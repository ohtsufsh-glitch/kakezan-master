#!/usr/bin/env python3
"""Check delivered scripts, local HTML references and all image assets."""
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]


class References(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.page = page

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key not in ('src', 'href') or not value:
                continue
            url = urlsplit(value)
            if url.scheme or url.netloc or not url.path:
                continue
            path = self.page.parent / unquote(url.path)
            assert path.exists(), f'Missing reference: {self.page}: {value}'


def main():
    for page in [ROOT / 'index.html', ROOT / 'runner/index.html']:
        source = page.read_text()
        References(page).feed(source)
        for script in re.findall(r'<script>([\s\S]*?)</script>', source):
            with tempfile.NamedTemporaryFile(suffix='.js', mode='w') as f:
                f.write(script)
                f.flush()
                subprocess.run(['node', '--check', f.name], check=True)
    for script in (ROOT / 'runner').glob('*.js'):
        subprocess.run(['node', '--input-type=module', '--check'], input=script.read_bytes(), check=True)
    for script in (ROOT / 'runner').glob('*.js'):
        for target in re.findall(r'from\s+["\'](\.[^"\']+)', script.read_text()):
            assert (script.parent / urlsplit(target).path).is_file(), target
    code = (ROOT / 'index.html').read_text()
    assert 'history-master' not in code
    assert not re.search(r'localStorage|sessionStorage|caches\.', code)
    print('OK: HTML references, parent/runner JavaScript syntax, app identifiers')


if __name__ == '__main__':
    main()
