# -*- coding: utf-8 -*-
"""Build the list of images the Ivano-Frankivsk site needs from the Dnipro site.
Output: /home/claude/work/img_manifest.json  [{dest, primary, fallback, kind, where}]"""
import sys, re, os, json, glob, html, collections
from urllib.parse import quote, unquote
import pymysql
sys.path.insert(0, '/home/claude/scripts')
P = 'Impulse_Digital_X_'
ARCH = '/home/claude/src/files/lbarif/'
OUT = '/home/claude/out/site/'
def db(name):
    return pymysql.connect(unix_socket='/run/mysqld/mysqld.sock', user='root', database=name, charset='utf8mb4').cursor()
new, old = db('lbif'), db('lb')
IMG = r'(?:jpe?g|png|gif|svg|webp|mp4|ico|JPE?G|PNG)'
need = collections.OrderedDict()   # dest -> dict
def add(dest, kind, where, primary=None):
    dest = unquote(html.unescape(dest.strip())).lstrip('/')
    dest = dest.split('?')[0].split('#')[0]
    if not dest or '[[' in dest or '{' in dest or dest.startswith(('http', 'data:')):
        return
    if dest.startswith('dnipro/'):
        dest = dest[len('dnipro/'):]
    if not re.search(r'\.' + IMG + r'$', dest):
        return
    e = need.setdefault(dest, {'dest': dest, 'kind': kind, 'where': set(), 'primary': primary})
    e['where'].add(where)
    if primary and not e['primary']:
        e['primary'] = primary

new.execute(f"select id,context_key from {P}site_content where deleted=0 and published=1"); live = dict(new.fetchall())

# a. chunks / templates
for tbl, col, key in (('site_htmlsnippets', 'snippet', 'name'), ('site_templates', 'content', 'templatename')):
    new.execute(f"select {key},{col} from {P}{tbl}")
    for n, s in new.fetchall():
        s = s or ''
        if s.lstrip().startswith('<!--') and s.rstrip().endswith('-->'):
            continue
        for m in re.finditer(r'''(?:src|href|data-src|poster|content)\s*=\s*["'](?:\[\[\+\+site_url\]\]|\[\[!\+\+site_url\]\])?(images/[^"'\[\]]+)''', s):
            add(m.group(1), 'design', f'chunk:{n}')
        for m in re.finditer(r'''url\(\s*["']?(images/[^)"']+)''', s):
            add(m.group(1), 'design', f'chunk:{n}')
        for m in re.finditer(r'''"(?:\[\[!?\+\+site_url\]\])(images/[^"]+)"''', s):
            add(m.group(1), 'design', f'chunk:{n}')
# b. CSS
for f in glob.glob(ARCH + 'assets/templates/css/*.css'):
    p = OUT + 'assets/templates/css/' + os.path.basename(f)
    s = open(p if os.path.exists(p) else f, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'''url\(\s*["']?\.\./\.\./\.\./(images/[^)"']+)''', s):
        add(m.group(1), 'design', 'css:' + os.path.basename(f))
# c. JS
s = open(ARCH + 'assets/templates/js/custom.js', encoding='utf-8', errors='replace').read()
for m in re.finditer(r"""['"]/?(images/[^'"]+)['"]""", s):
    add(m.group(1), 'design', 'js:custom.js')
# d. TV image values (rendered through the media source of the TV for that context)
new.execute(f"select id,properties from {P}media_sources")
SRC = {}
for sid, props in new.fetchall():
    m = re.search(r's:8:"basePath";a:\d+:\{.*?s:5:"value";s:\d+:"([^"]*)"', props or '', re.S)
    SRC[sid] = m.group(1) if m else ''
new.execute(f"select source,object,context_key from {P}media_sources_elements where object_class='modTemplateVar'")
TVSRC = {(o, c): s for s, o, c in new.fetchall()}
new.execute(f"select id,name,type from {P}site_tmplvars"); TV = {i: (n, t) for i, n, t in new.fetchall()}
new.execute(f"select tmplvarid,contentid,value from {P}site_tmplvar_contentvalues")
for tid, cid, val in new.fetchall():
    if cid not in live or not val:
        continue
    name, typ = TV.get(tid, ('', ''))
    ctx = live[cid]
    base = SRC.get(TVSRC.get((tid, ctx), 1), '')
    if typ == 'image':
        v = val if (val.startswith(('images/', 'assets/', '/')) or not base) else base + val
        add(v, 'tv', f'{cid}:{name}')
    elif typ == 'migx':
        try:
            arr = json.loads(val)
        except Exception:
            arr = []
        for it in arr:
            for k, x in it.items():
                if isinstance(x, str) and re.search(r'\.' + IMG + r'$', x) and not x.startswith('http'):
                    add(x, 'tv', f'{cid}:{name}')
    if typ in ('richtext', 'textarea', 'text', 'migx'):
        for m in re.finditer(r'''<img[^>]+src\s*=\s*\\?["']([^"'\\]+)''', val):
            u = m.group(1)
            if u.startswith('http') and 'lbar.com.ua' not in u:
                continue
            add(re.sub(r'^https?://lbar\.com\.ua/', '', u), 'content', f'{cid}:{name}')
new.execute(f"select id,content from {P}site_content where deleted=0 and published=1")
for cid, s in new.fetchall():
    for m in re.finditer(r'''<img[^>]+src\s*=\s*["']([^"']+)''', s or ''):
        u = m.group(1)
        if u.startswith('http') and 'lbar.com.ua' not in u:
            continue
        add(re.sub(r'^https?://lbar\.com\.ua/', '', u), 'content', f'{cid}:content')
# g. ClientConfig
new.execute(f"select `key`,value from {P}clientconfig_setting")
for k, v in new.fetchall():
    if v and re.search(r'\.' + IMG + r'$', v) and not v.startswith('http'):
        add(v, 'design', f'clientconfig:{k}')
# h. ms2Gallery files of live resources that were kept
new.execute(f"select id,resource_id,url from {P}ms2_resource_files where resource_id in ({','.join(map(str, live))}) and active=1")
rows = new.fetchall()
old.execute(f"select id,url from {P}ms2_resource_files"); oldurl = dict(old.fetchall())
for fid, rid, url in rows:
    if fid not in oldurl:
        continue  # new (Inna) files are shipped with the package
    add(url, 'gallery', f'ms2:{rid}', primary='https://lbar.com.ua' + oldurl[fid])

# exclude what we ship / what is already in the archive
ship = set()
for root, d, fs in os.walk(OUT):
    for f in fs:
        ship.add(os.path.relpath(os.path.join(root, f), OUT))
res = []
for dest, e in need.items():
    if dest in ship or os.path.exists(ARCH + dest):
        continue
    prim = e['primary'] or 'https://lbar.com.ua/dnipro/' + quote(dest)
    fb = 'https://lbar.com.ua/' + quote(dest)
    res.append({'dest': dest, 'kind': e['kind'], 'primary': prim, 'fallback': fb if fb != prim else 'https://lbar.com.ua/dnipro/' + quote(dest), 'where': sorted(e['where'])[:6]})
json.dump(res, open('/home/claude/work/img_manifest.json', 'w'), ensure_ascii=False, indent=1)
c = collections.Counter(r['kind'] for r in res)
print(len(res), dict(c))
