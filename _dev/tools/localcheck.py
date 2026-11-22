import re, json, sys, os, collections, urllib.parse, html as H
import urllib.request
sys.path.insert(0,'/home/claude/scripts')
import pymysql
c=pymysql.connect(unix_socket='/run/mysqld/mysqld.sock',user='root',database='lbif_local',charset='utf8mb4').cursor()
c.execute("select id,context_key,uri from Impulse_Digital_X_site_content where deleted=0 and published=1 and template>0 and uri not in ('sitemap.xml','dostup-zapreshhen')")
pages=[]
for i,ctx,uri in c.fetchall():
    base='http://localhost:8080/'+('ru/' if ctx=='web' else '')
    pages.append((i,ctx, base if i in (1,193) else base+uri))
man={x['dest'] for x in json.load(open('/home/claude/work/img_manifest.json'))}
ROOT='/var/www/lbif/'
def get(u):
    try:
        r=urllib.request.urlopen(u,timeout=60); return r.status, r.read().decode('utf-8','replace')
    except urllib.error.HTTPError as e: return e.code, ''
    except Exception as e: return 'ERR '+str(e), ''
res={}; missing=collections.defaultdict(set); badlinks=collections.defaultdict(set); words=collections.defaultdict(set)
linkcache={}
for i,ctx,u in pages:
    st,h=get(u)
    t=re.search(r'<title>(.*?)</title>',h,re.S); h1=re.search(r'<h1[^>]*>(.*?)</h1>',h,re.S)
    d=re.search(r'<meta name="description" content="([^"]*)"',h)
    res[i]={'ctx':ctx,'url':u,'status':st,'title':t.group(1).strip() if t else None,'h1':re.sub('<[^>]+>',' ',h1.group(1)).strip() if h1 else None,'desc':d.group(1) if d else None}
    base=re.search(r'<base href="([^"]+)"',h); base=base.group(1) if base else u
    hb=re.sub(r'<!--.*?-->','',h,flags=re.S)
    for m in re.finditer(r'''(?:src|data-src|poster)\s*=\s*["']([^"']+)["']|url\(\s*["']?([^)"']+)["']?\s*\)''',hb):
        v=H.unescape(m.group(1) or m.group(2))
        if v.startswith(('data:','http')) and 'localhost' not in v: continue
        a=urllib.parse.urljoin(base,v); p=urllib.parse.urlparse(a).path
        p=urllib.parse.unquote(p).lstrip('/')
        if p.startswith('ru/'): p=p[3:]
        if not re.search(r'\.(jpe?g|png|gif|svg|webp|mp4|JPE?G|PNG)$',p): continue
        if os.path.exists(ROOT+p) or p in man: continue
        missing[p].add(i)
    for m in re.finditer(r'''<a[^>]+href\s*=\s*["']([^"'#]+)["']''',hb):
        v=H.unescape(m.group(1))
        if v.startswith(('mailto','tel','viber','whatsapp','javascript','https://www.','https://t','https://lbar.ro','https://impulse','https://google','https://lbar.com.ua/dnipro')): continue
        a=urllib.parse.urljoin(base,v)
        pp=urllib.parse.unquote(urllib.parse.urlparse(a).path).lstrip('/')
        pp=pp[3:] if pp.startswith('ru/') else pp
        if re.search(r'\.(jpe?g|png|gif|svg|webp|mp4|JPE?G|PNG)$',pp) and (os.path.exists(ROOT+pp) or pp in man): continue
        if 'localhost' not in a:
            badlinks[a].add(i) if 'lbar.com.ua' in a else None; continue
        if a not in linkcache: linkcache[a]=get(a)[0]
        if linkcache[a]!=200: badlinks[f'{a} -> {linkcache[a]}'].add(i)
    txt=re.sub(r'<script.*?</script>|<style.*?</style>','',hb,flags=re.S)
    for w in re.findall(r'\w*(?:Днеп|Дніп|Днип|dnipro|Dnipro|Киев|Києв|Київ|Ольг|Анастас)\w*',txt):
        words[w].add(i)
json.dump(res,open('/home/claude/work/local_pages.json','w'),ensure_ascii=False,indent=1)
print('status != 200:',[ (i,r['url'],r['status']) for i,r in res.items() if r['status']!=200])
print('missing images:',len(missing)); [print('  ',k,sorted(v)[:8]) for k,v in sorted(missing.items())]
print('bad links:',len(badlinks)); [print('  ',k,sorted(v)[:8]) for k,v in sorted(badlinks.items())]
print('city/name words:'); [print('  ',k,sorted(v)[:12]) for k,v in sorted(words.items())]
