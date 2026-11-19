#!/usr/bin/env python3
"""Rebuild index.html from the content/ folder.
Usage:  python build.py            (images stay in content/, for hosting the folder)
        python build.py --embed    (images inlined into one self-contained index.html)"""
import json, base64, sys, mimetypes
from pathlib import Path
ROOT = Path(__file__).parent; C = ROOT / 'content'; EMBED = '--embed' in sys.argv
EXT = ('.jpg', '.jpeg', '.png', '.webp')

def parse(p):                                   # info.txt: "key: value", "- item" lines, "#" comments
    d, key = {}, None
    for line in p.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if not s or s.startswith('#'): continue
        if s.startswith('-') and key and isinstance(d[key], list):
            if s[1:].strip(): d[key].append(s[1:].strip())
        elif ':' in s:
            key, v = s.split(':', 1); key = key.strip(); v = v.split('  #')[0].strip(); d[key] = v if v else []
    return d

def src(f):
    if EMBED: return f'data:{mimetypes.guess_type(f.name)[0]};base64,' + base64.b64encode(f.read_bytes()).decode()
    return f.relative_to(ROOT).as_posix()

def img(folder, stem):
    for e in EXT:
        if (folder / (stem + e)).exists(): return src(folder / (stem + e))
    return ''

def items(sub, stem, pdf=False):
    out, base = [], C / sub
    for f in sorted(base.iterdir()) if base.exists() else []:
        if f.is_dir() and (f / 'info.txt').exists():
            r = parse(f / 'info.txt'); r['dir'] = f.relative_to(C).as_posix(); r['img'] = img(f, stem)
            if pdf:
                p = sorted(f.glob('*.pdf')); r['pdf'] = p[0].relative_to(ROOT).as_posix() if p else ''
            out.append(r)
    return out

site = parse(C / 'site' / 'info.txt'); site['logo'] = img(C / 'site', 'logo'); site['banner'] = img(C / 'site', 'banner')
data = {'site': site,
        'articles': sorted(items('maqalat', 'image'), key=lambda r: r.get('date', ''), reverse=True),
        'books': items('isdarat/kutub', 'cover', True), 'journals': items('isdarat/majallat', 'cover', True),
        'programs': items('baramij', 'image'), 'authors': items('ashkhas/kuttab-wa-bahithun', 'photo'), 'team': items('ashkhas/fariq-al-amal', 'photo')}
html = (ROOT / 'template.html').read_text(encoding='utf-8').replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
(ROOT / 'index.html').write_text(html, encoding='utf-8')
print('index.html built:', {k: len(v) for k, v in data.items() if isinstance(v, list)})
