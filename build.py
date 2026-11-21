#!/usr/bin/env python3
"""Rebuild the site into public/ from the content/ folder.
Usage:  python build.py            (public/index.html + a page per article/book/journal + images and PDFs)
        python build.py --embed    (images inlined into public/index.html)
Only public/ is published: build.py, template.html, detail.html, style.css sources and info.txt/text.txt stay private
(style.css is copied into public/)."""
import json, base64, sys, mimetypes, shutil, re, html
from pathlib import Path
ROOT = Path(__file__).parent; C = ROOT / 'content'; OUT = ROOT / 'public'; EMBED = '--embed' in sys.argv
EXT = ('.jpg', '.jpeg', '.png', '.webp')
MONTHS = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
esc = lambda s: html.escape(str(s or ''))

KEY = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:(.*)$')
def parse(p):                                   # info.txt: "key: value", "- item" lines, "#" comments;
    d, key, brk = {}, None, False               # lines after a "key:" line continue its value (blank line = new paragraph)
    for line in p.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if s.startswith('#'): continue
        m = KEY.match(s)
        if m:
            key, brk = m[1], False; v = m[2].split('  #')[0].strip(); d[key] = v if v else []
        elif not s: brk = True
        elif key and isinstance(d[key], list):
            if s.startswith('-') and s[1:].strip(): d[key].append(s[1:].strip())
        elif key:
            d[key] = (d[key] + ('\n' if brk else ' ') + s) if d[key] else s; brk = False
    return d

def find(folder, stem):
    for e in EXT:
        if (folder / (stem + e)).exists(): return folder / (stem + e)
def rel(f): return f.relative_to(ROOT).as_posix() if f else ''
def src(f):
    if not f: return ''
    if EMBED: return f'data:{mimetypes.guess_type(f.name)[0]};base64,' + base64.b64encode(f.read_bytes()).decode()
    return rel(f)

def items(sub, stem, urlbase='', pdf=False):
    out, base = [], C / sub
    for f in sorted(base.iterdir()) if base.exists() else []:
        if f.is_dir() and (f / 'info.txt').exists():
            r = parse(f / 'info.txt'); r['dir'] = f.relative_to(C).as_posix()
            im = find(f, stem); r['img'] = src(im); r['imgpath'] = rel(im)
            if urlbase: r['url'] = urlbase + f.name + '/'
            if pdf:
                p = sorted(f.glob('*.pdf')); r['pdf'] = rel(p[0]) if p else ''
            out.append(r)
    return out

def fmt(d):                                     # 2026-10-17 -> 17 أكتوبر 2026 ; 2025-10 -> أكتوبر 2025 ; 2025 -> 2025
    m = re.match(r'(\d{4})(?:-(\d\d))?(?:-(\d\d))?', (d or '').strip())
    if not m: return d or ''
    y, mo, da = m.groups()
    if not mo: return y
    s = f'{MONTHS[int(mo) - 1]} {y}'
    return f'{int(da)} {s}' if da else s
def when(r): return fmt(r['date']) if r.get('date') else r.get('year', '')
def key(r):
    m = re.search(r'\d{4}', str(r.get('year', '')))
    return r.get('date') or (m[0] if m else '')

site = parse(C / 'site' / 'info.txt'); lg = find(C / 'site', 'logo'); site['logo'] = src(lg); site['logopath'] = rel(lg); site['banner'] = src(find(C / 'site', 'banner'))
site['banners'] = [src(f) for f in (find(C / 'site', s) for s in ['banner'] + [f'banner-{i}' for i in range(2, 10)]) if f]   # banner, banner-2, banner-3 ... rotate automatically
arts = sorted(items('maqalat', 'image', 'maqalat/', True), key=lambda r: r.get('date', ''), reverse=True)
books = items('isdarat/kutub', 'cover', 'isdarat/kutub/', True); journals = items('isdarat/majallat', 'cover', 'isdarat/majallat/', True)
for b in books: b['type'] = 'book'
for j in journals: j['type'] = 'journal'
pubs = sorted(books + journals, key=key, reverse=True)
data = {'site': site, 'articles': arts, 'books': books, 'journals': journals,
        'programs': items('baramij', 'image'), 'authors': items('ashkhas/kuttab-wa-bahithun', 'photo'), 'team': items('ashkhas/fariq-al-amal', 'photo')}

tpl = (ROOT / 'template.html').read_text(encoding='utf-8'); detail = (ROOT / 'detail.html').read_text(encoding='utf-8')
html_out = tpl.replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
HEADER = re.search(r'<header>.*?</header>', tpl, re.S)[0]; FOOTER = re.search(r'<footer>.*?</footer>', tpl, re.S)[0]

BLANK = r'\n\s*\n'; NL = r'\n'
def paras(text, sep):
    return ''.join(f'<p>{esc(" ".join(x.split()))}</p>' for x in re.split(sep, text.strip()) if x.strip())
def image(r, p, cls, label):
    return (f'<div class="ph {cls}"><img src="{p}{r["imgpath"]}" alt=""></div>' if r['imgpath']
            else f'<div class="ph {cls}"><span>{label}</span></div>')
def page(r, title, desc, body):
    p = '../' * r['url'].count('/')
    fix = lambda s: re.sub(r'href="#([^"]*)"', lambda m: f'href="{p}index.html#{m[1]}"', s)
    mark = f'<span class="ph mark"><img src="{p}{site["logopath"]}" alt=""></span>' if site['logopath'] else '<span class="ph mark"></span>'
    h = fix(HEADER).replace('<span class="ph mark" data-img="logo"></span>', mark)
    o = (detail.replace('{{PREFIX}}', p).replace('{{TITLE}}', esc(title)).replace('{{DESC}}', esc(desc))
         .replace('{{HEADER}}', h).replace('{{FOOTER}}', fix(FOOTER)).replace('{{BODY}}', body.replace('{{P}}', p)))
    d = OUT / r['url']; d.mkdir(parents=True, exist_ok=True); (d / 'index.html').write_text(o, encoding='utf-8')

def article_page(r):
    t = C / r['dir'] / 'text.txt'; text = t.read_text(encoding='utf-8') if t.exists() else ''
    others = [a for a in arts if a is not r]; same = [a for a in others if a.get('topic') == r.get('topic')]
    rel3 = (same + [a for a in others if a not in same])[:3]
    cards = ''.join(f'<a href="{{{{P}}}}{a["url"]}">{image(a, "{{P}}", "", "")}<span class="tag">{esc(a.get("topic"))}</span><h3>{esc(a.get("title"))}</h3></a>' for a in rel3)
    pdf = f'<p><a class="btn" href="{{{{P}}}}{r["pdf"]}" download>تحميل PDF</a></p>' if r.get('pdf') else ''
    body = (f'<p class="crumbs"><a href="{{{{P}}}}index.html">الرئيسية</a> › <a href="{{{{P}}}}index.html#articles">المقالات</a></p>'
            f'<article><span class="tag">{esc(r.get("topic"))}</span><h1>{esc(r.get("title"))}</h1>'
            f'<div class="meta">{esc(r.get("author"))} · {fmt(r.get("date"))}</div>'
            + (image(r, '{{P}}', 'hero-img', '') if r['imgpath'] else '') + f'<div class="prose">{paras(text, BLANK) or paras(r.get("summary", ""), NL)}</div>{pdf}</article>'
            + (f'<h2 class="rel-h">مقالات ذات صلة</h2><div class="rel">{cards}</div>' if cards else ''))
    page(r, r.get('title'), r.get('summary'), body)

def pub_page(r):
    kind = 'كتاب' if r['type'] == 'book' else 'مجلة'
    others = [x for x in pubs if x is not r][:4]
    cards = ''.join(f'<a class="pub" href="{{{{P}}}}{x["url"]}">{image(x, "{{P}}", "", "")}<div><span class="tag">{"كتاب" if x["type"] == "book" else "مجلة"} · {esc(when(x))}</span><h3>{esc(x.get("title"))}</h3></div></a>' for x in others)
    btns = (f'<a class="btn p" href="{{{{P}}}}{r["pdf"]}" target="_blank" rel="noopener">قراءة</a> <a class="btn" href="{{{{P}}}}{r["pdf"]}" download>تحميل</a>'
            if r.get('pdf') else '<span class="muted sm">ملف الإصدار غير متوفر بعد.</span>')
    body = (f'<p class="crumbs"><a href="{{{{P}}}}index.html">الرئيسية</a> › <a href="{{{{P}}}}index.html#publications">الإصدارات</a></p>'
            f'<div class="bookpage">{image(r, "{{P}}", "", "غلاف")}<div><span class="tag">{kind} · {esc(when(r))}</span><h1>{esc(r.get("title"))}</h1>'
            f'<div class="meta">{esc(r.get("author"))}</div><p class="lead2">{esc(r.get("summary"))}</p>'
            f'<div class="prose">{paras(r.get("description", ""), NL)}</div><p>{btns}</p></div></div>'
            + (f'<h2 class="rel-h">إصدارات أخرى</h2><div class="grid">{cards}</div>' if cards else ''))
    page(r, r.get('title'), r.get('summary'), body)

shutil.rmtree(OUT, ignore_errors=True)
KEEP = EXT + ('.pdf',)
def skip(d, names):   # publish images and PDFs only; skip info.txt, text.txt and _namadhij
    return [n for n in names if ((Path(d) / n).is_file() and not n.lower().endswith(KEEP)) or ((Path(d) / n).is_dir() and n.startswith('_'))]
shutil.copytree(C, OUT / 'content', ignore=skip)
shutil.copy(ROOT / 'style.css', OUT / 'style.css')
(OUT / 'index.html').write_text(html_out, encoding='utf-8')
for a in arts: article_page(a)
for x in pubs: pub_page(x)
print('built public/: index.html +', len(arts), 'article pages +', len(pubs), 'publication pages')
