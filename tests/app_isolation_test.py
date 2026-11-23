"""PR-1: ephemeral same-origin databases and synthetic records only."""
import copy
import json
from pathlib import Path
import unittest
import plush_test as plush


# Reuse helpers without inheriting the original tests.
class AppIsolationTest(unittest.TestCase):
    setUpClass = classmethod(plush.PlushTest.setUpClass.__func__)
    tearDownClass = classmethod(plush.PlushTest.tearDownClass.__func__)
    ready = plush.PlushTest.ready
    def setUp(self):
        self.context=self.browser.new_context()
        self.page=self.context.new_page()
        self.errors=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.accept_dialog=lambda d:d.accept()
        self.page.on('dialog',self.accept_dialog)
        self.page.goto(self.url)
        self.ready()

    tearDown = plush.PlushTest.tearDown

    def test_same_origin_isolation_reload_and_new_database_only(self):
        old_name = 'history-master-sample-v1'
        self.page.evaluate('db.close()')
        self.page.evaluate('''async name => {
          await new Promise((ok,no)=>{const r=indexedDB.open(name,10);
            r.onupgradeneeded=()=>r.result.createObjectStore('sentinel');
            r.onsuccess=()=>{const d=r.result,t=d.transaction('sentinel','readwrite');
              t.objectStore('sentinel').put({coins:123,history:['synthetic'],runner:{active:true}},'old');
              t.oncomplete=()=>{d.close();ok();};};r.onerror=()=>no(r.error);});
        }''',old_name)
        self.context.add_init_script('''window.openedDatabases=[];
          const originalOpen=IDBFactory.prototype.open;
          IDBFactory.prototype.open=function(name,...args){window.openedDatabases.push(name);return originalOpen.call(this,name,...args);};''')
        self.page.reload();self.page.wait_for_function('appReady')
        self.assertEqual(self.page.evaluate('openedDatabases'), ['kakezan-master-v1'])
        self.assertEqual(self.page.evaluate('[DB_VERSION,BACKUP_VERSION,APP_VERSION,db.objectStoreNames.length]'),[12,12,'v0.4.4',17])
        self.assertTrue(self.page.evaluate("async()=>Object.entries(await snapshotAllStores()).every(([k,v])=>['coinMeta','arcadeBoards'].includes(k)||v.length===0)"))
        self.page.evaluate(plush.FIXTURE_HELPERS)
        self.page.evaluate("async()=>plushInstall(plushFixture(['shiba'],'student'))")
        before=self.page.evaluate('snapshotAllStores()')
        self.page.reload();self.page.wait_for_function('appReady')
        self.assertEqual(self.page.evaluate('snapshotAllStores()'), before)
        self.assertEqual(self.page.evaluate('openedDatabases'), ['kakezan-master-v1'])
        sentinel=self.page.evaluate('''name=>new Promise(ok=>{const r=indexedDB.open(name,10);r.onsuccess=()=>{
          const d=r.result,t=d.transaction('sentinel'),q=t.objectStore('sentinel').get('old');
          t.oncomplete=()=>{d.close();ok(q.result);};};})''',old_name)
        self.assertEqual(sentinel,dict(coins=123,history=['synthetic'],runner=dict(active=True)))
        self.assertEqual(self.page.evaluate('history.state.app'),'kakezan-master')

    def test_formats_versions_missing_stores_and_confirmation_preserve_data(self):
        self.page.evaluate("async()=>plushInstall(plushFixture(['shiba'],'student'))")
        before=self.page.evaluate('snapshotAllStores()')
        with self.page.expect_download() as event:self.page.evaluate('exportBackup()')
        backup=json.loads(Path(event.value.path()).read_text())
        self.assertTrue(event.value.suggested_filename.startswith('kakezan-master-backup-'))
        self.assertEqual(backup['backupFormat'],'kakezan-master-backup')
        self.assertEqual(backup['data'],before)
        invalid=[]
        for version in range(1,11):invalid.append(dict(backup,backupFormat='history-master-backup',backupVersion=version))
        for version in [0,*range(1,10),13]:invalid.append(dict(backup,backupVersion=version))
        for store in before:
            broken=copy.deepcopy(backup);del broken['data'][store];invalid.append(broken)
        for obj in invalid:
            self.assertTrue(self.page.evaluate('''obj=>{try{validateBackup(obj);return false;}catch{return true;}}''',obj))
        self.page.evaluate("navigate('admin','student')")
        self.page.locator('#backup-file').set_input_files(dict(name='synthetic.json',mimeType='application/json',buffer=json.dumps(backup).encode()))
        self.page.wait_for_function('pendingRestore!==null')
        self.page.remove_listener('dialog',self.accept_dialog)
        messages=[]
        dismiss_dialog=lambda d:(messages.append(d.message),d.dismiss())
        self.page.on('dialog',dismiss_dialog)
        self.page.evaluate('applyRestore()')
        self.assertTrue(messages)
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
        self.page.remove_listener('dialog',dismiss_dialog);self.page.on('dialog',self.accept_dialog)
        self.page.evaluate('applyRestore()');self.page.wait_for_function('!backingUp&&pendingRestore===null')
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
        self.assertEqual(self.page.evaluate("getAvailableCoins('student')"),705)
        self.assertEqual(self.page.evaluate("getAvailableCoins('test')"),9)

    def test_all_delivered_images_decode(self):
        root=Path(__file__).resolve().parents[1]
        paths=[str(p.relative_to(root)) for folder in ['assets','runner/assets'] for p in (root/folder).rglob('*.webp')]
        failed=self.page.evaluate("""async paths=>{
          const bad=[];
          for(const src of paths){const i=new Image();i.src=src;try{await i.decode();if(!i.naturalWidth)bad.push(src);}catch{bad.push(src);}}
          return bad;
        }""",paths)
        self.assertGreater(len(paths),100)
        self.assertEqual(failed,[])
