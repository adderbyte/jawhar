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

ICONS = {   # social links: set whatsapp / telegram / facebook in content/site/info.txt (full URL, or number / username / page name)
 'whatsapp': ('واتساب', '#25D366', 'https://wa.me/', 'M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z'),
 'telegram': ('تيليجرام', '#229ED9', 'https://t.me/', 'M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z'),
 'facebook': ('فيسبوك', '#1877F2', 'https://facebook.com/', 'M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z'),
}
def social_link(name, base):
    v = str(site.get(name, '')).strip()
    if not v: return ''
    if v.startswith('http'): return v
    v = v.lstrip('@').strip('/')
    return base + (re.sub(r'\D', '', v) if name == 'whatsapp' else v)
SOCIAL = ''.join(f'<a href="{esc(u)}" target="_blank" rel="noopener" aria-label="{lab}" style="background:{col}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="{path}"/></svg></a>'
                 for n, (lab, col, base, path) in ICONS.items() for u in [social_link(n, base)] if u)
SOCIAL = f'<div class="social">{SOCIAL}</div>' if SOCIAL else ''
tpl = tpl.replace('<!--SOCIAL-->', SOCIAL)
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
