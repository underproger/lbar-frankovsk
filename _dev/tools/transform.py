# -*- coding: utf-8 -*-
"""Build the Ivano-Frankivsk DB from the Dnipro dump.
usage: python3 transform.py            -> rebuild DB `lbif` from slim.sql and apply everything (test env settings)
"""
import sys, os, re, json, html, hashlib, datetime, collections
sys.path.insert(0, '/home/claude/scripts')
import pymysql
P = 'Impulse_Digital_X_'
DB = 'lbif'
SLIM = '/home/claude/src/sql/slim.sql'
REPORT = collections.defaultdict(list)

def rebuild():
    os.system(f"mysql -e 'DROP DATABASE IF EXISTS {DB}; CREATE DATABASE {DB} CHARACTER SET utf8mb4;'")
    assert os.system(f"mysql {DB} < {SLIM}") == 0

def conn():
    return pymysql.connect(unix_socket='/run/mysqld/mysqld.sock', user='root', database=DB, charset='utf8mb4', autocommit=True)

# ------------------------------------------------------------------ city morphology
def city_ru(s):
    s = re.sub(r'Днепропетровск(ая|ой|ую|е|а|у|ом)?\b', lambda m: 'Ивано-Франковск' + (m.group(1) or ''), s)
    s = re.sub(r'Днепр(е|а|у|ом)?\b', lambda m: 'Ивано-Франковск' + (m.group(1) or ''), s)
    return s

def city_ua(s):
    s = re.sub(r'Дніпропетровськ(а|ій|у|ом|ої)?\b', lambda m: 'Івано-Франківськ' + (m.group(1) or ''), s)
    UA = {'і': 'у', 'а': 'а', 'у': 'у', 'ом': 'ом', '': ''}
    s = re.sub(r'Дніпр(о|і|а|у|ом)\b', lambda m: 'Івано-Франківськ' + UA['' if m.group(1) == 'о' else m.group(1)], s)
    # "у Івано-Франківську" -> "в Івано-Франківську" (before a vowel)
    s = re.sub(r'(^|[\s>(«"])у (Івано-Франківськ)', r'\1в \2', s)
    s = re.sub(r'(^|[\s>(«"])У (Івано-Франківськ)', r'\1В \2', s)
    return s

def city(s, lang):
    if not s or not isinstance(s, str):
        return s
    return city_ru(s) if lang == 'ru' else city_ua(s)

LANG = {'web': 'ru', 'ua': 'ua'}

# ------------------------------------------------------------------ helpers
class Site:
    def __init__(self, c):
        self.c = c
        cur = c.cursor()
        cur.execute(f"select id,name,type from {P}site_tmplvars")
        self.tv = {n: (i, t) for i, n, t in cur.fetchall()}
        self.tvname = {i: n for n, (i, t) in self.tv.items()}
        cur.execute(f"select id,context_key,uri,template from {P}site_content where deleted=0 and published=1")
        self.live = {i: (ctx, uri, tpl) for i, ctx, uri, tpl in cur.fetchall()}
        self.byuri = {(ctx, uri): i for i, (ctx, uri, tpl) in self.live.items()}

    def q(self, sql, args=None):
        cur = self.c.cursor(); cur.execute(sql, args); return cur.fetchall()

    def tv_get(self, rid, name):
        r = self.q(f"select value from {P}site_tmplvar_contentvalues where tmplvarid=%s and contentid=%s", (self.tv[name][0], rid))
        return r[0][0] if r else None

    def tv_set(self, rid, name, value):
        tid = self.tv[name][0]
        r = self.q(f"select id from {P}site_tmplvar_contentvalues where tmplvarid=%s and contentid=%s", (tid, rid))
        if r:
            self.q(f"update {P}site_tmplvar_contentvalues set value=%s where id=%s", (value, r[0][0]))
        else:
            self.q(f"insert into {P}site_tmplvar_contentvalues (tmplvarid,contentid,value) values (%s,%s,%s)", (tid, rid, value))

    def field_set(self, rid, field, value):
        assert field in ('pagetitle', 'longtitle', 'description', 'introtext', 'menutitle', 'content', 'alias', 'uri')
        self.q(f"update {P}site_content set `{field}`=%s where id=%s", (value, rid))

    def set(self, rid, key, value):
        if key.startswith('tv:'):
            self.tv_set(rid, key[3:], value)
        else:
            self.field_set(rid, key, value)

TEXT_FIELDS = ['pagetitle', 'longtitle', 'description', 'introtext', 'menutitle', 'content']
TEXT_TV_TYPES = ('text', 'textarea', 'richtext', 'migx')

def map_text_fields(site, rid, fn):
    """apply fn(str)->str to all text fields + text TVs (incl. MIGX leaves) of a resource"""
    ctx = site.live[rid][0]
    row = site.q(f"select {','.join('`'+f+'`' for f in TEXT_FIELDS)} from {P}site_content where id=%s", (rid,))[0]
    for f, v in zip(TEXT_FIELDS, row):
        if v:
            nv = fn(v)
            if nv != v:
                site.field_set(rid, f, nv)
    for tid, val, vid in site.q(f"select tmplvarid,value,id from {P}site_tmplvar_contentvalues where contentid=%s", (rid,)):
        name = site.tvname.get(tid)
        if not name or site.tv[name][1] not in TEXT_TV_TYPES or not val:
            continue
        if site.tv[name][1] == 'migx':
            try:
                arr = json.loads(val)
            except Exception:
                nv = fn(val)
            else:
                for it in arr:
                    for k, x in list(it.items()):
                        if isinstance(x, str) and k != 'MIGX_id':
                            it[k] = fn(x)
                nv = json.dumps(arr, ensure_ascii=('\\u04' in val))
                if nv == val or json.loads(nv) == json.loads(val):
                    nv = val if json.loads(nv) == json.loads(val) else nv
        else:
            nv = fn(val)
        if nv != val:
            site.q(f"update {P}site_tmplvar_contentvalues set value=%s where id=%s", (nv, vid))

# ------------------------------------------------------------------ 1. city + claims + overrides
def content_pass(site):
    import rew_a, rew_b, rew_c
    R = {}
    for mod in (rew_a, rew_b, rew_c):
        for k, v in mod.R.items():
            R.setdefault(k, {}).update(v)
    for rid, (ctx, uri, tpl) in site.live.items():
        lang = LANG[ctx]
        gen = rew_c.GENERIC[lang]
        def fn(s, lang=lang, gen=gen):
            s = city(s, lang)
            for a, b in gen:
                s = s.replace(a, b)
            return s
        map_text_fields(site, rid, fn)
        for a, b in rew_c.SUBS.get(rid, []):
            map_text_fields(site, rid, lambda s, a=a, b=b: s.replace(a, b))
    for rid, fields in R.items():
        assert rid in site.live, rid
        for k, v in fields.items():
            site.set(rid, k, v)
    # master block
    for rid, kind in rew_a.MASTER_KIND.items():
        lang = LANG[site.live[rid][0]]
        site.tv_set(rid, 'title_bl5_about', rew_a.MASTER_TITLE[lang])
        site.tv_set(rid, 'sub-title_bl5_about', rew_a.MASTER_SUB[lang])
        txt = rew_a.MASTER_FULL[lang] if kind == 'full' else rew_a.MASTER_SHORT[kind][lang]
        site.tv_set(rid, 'text_bl5_about', txt)
        if rid not in (1, 193):
            site.tv_set(rid, 'image_bl5_about', 'images/design/inna-master.jpg')
    # home aliases (site_start is served at the root anyway)
    site.q(f"update {P}site_content set alias=%s, uri=%s where id=1", ('permanentnyj-makiyazh-v-ivano-frankovske-ot-lbar',) * 2)
    site.q(f"update {P}site_content set alias=%s, uri=%s where id=193", ('permanentnij-makiyazh-v-ivano-frankivsku-vid-lbar',) * 2)

# ------------------------------------------------------------------ 2. prices (Inna's price list)
PRICE = {
    'brows': 3500, 'brows_k': 1700, 'lips': 3500, 'lips_k': 1700,
    'mizh': 2000, 'mizh_k': 1000, 'strilka': 3000, 'strilka_k': 1500,
    'remover': 1000, 'renew': 2000,
}
def g(n): return f"{n} грн"
def price_pass(site):
    def mk(rows):
        return json.dumps([{'MIGX_id': str(i + 1), 'col-1': a, 'col-2': b, 'col-3': c, 'col-4': ''} for i, (a, b, c) in enumerate(rows)], ensure_ascii=False)
    ru_k = 'Коррекция (в течение 3 месяцев)'; ua_k = 'Корекція (протягом 3 місяців)'
    ru_cover = ('Перекрытие старого татуажа', '1,5 часа', '+500 грн к процедуре')
    ua_cover = ('Перекриття старого татуажу', '1,5 години', '+500 грн до процедури')
    ru_renew = ('Обновление моих работ (спустя 3+ месяца)', '1,5 часа', g(PRICE['renew']))
    ua_renew = ('Оновлення моїх робіт (через 3+ місяці)', '1,5 години', g(PRICE['renew']))
    T = {
        # home
        1: [('Перманентный макияж бровей', '1,5–2 часа', g(PRICE['brows'])), ('Перманентный макияж губ', '1,5–2 часа', g(PRICE['lips'])),
            ('Татуаж стрелок', '1,5 часа', g(PRICE['strilka'])), ('Межресничный татуаж', '1–1,5 часа', g(PRICE['mizh'])),
            ('Коррекция', '1 час', 'от 1000 грн'), ('Удаление старого перманента ремувером', '30 мин', g(PRICE['remover'])),
            ('Мини-тату', '1,5 часа', '10 см - 1000 грн , 15 см - 1300, до 20 см - обсуждается'), ru_cover],
        193: [('Перманентний макіяж брів', '1,5–2 години', g(PRICE['brows'])), ('Перманентний макіяж губ', '1,5–2 години', g(PRICE['lips'])),
              ('Татуаж стрілок', '1,5 години', g(PRICE['strilka'])), ('Міжвійковий татуаж', '1–1,5 години', g(PRICE['mizh'])),
              ('Корекція', '1 година', 'від 1000 грн'), ('Видалення старого перманенту ремувером', '30 хв', g(PRICE['remover'])),
              ('Міні-тату', '1,5 години', '10 см - 1000 грн , 15 см - 1300, до 20 см - обговорюється'), ua_cover],
        2: [('Перманентный макияж бровей', '1,5–2 часа', g(PRICE['brows'])), (ru_k, '1–1,5 часа', g(PRICE['brows_k'])), ru_renew, ru_cover],
        303: [('Перманентний макіяж брів', '1,5–2 години', g(PRICE['brows'])), (ua_k, '1–1,5 години', g(PRICE['brows_k'])), ua_renew, ua_cover],
        51: [('Пудровые брови (классика, омбре)', '1,5 часа', g(PRICE['brows'])), (ru_k, '1 час', g(PRICE['brows_k'])), ru_renew, ru_cover],
        304: [('Пудрові брови (класика, омбре)', '1,5 години', g(PRICE['brows'])), (ua_k, '1 година', g(PRICE['brows_k'])), ua_renew, ua_cover],
        167: [('Акварельный татуаж губ', '1,5–2 часа', g(PRICE['lips'])), (ru_k, '0,5–1 час', g(PRICE['lips_k'])), ru_renew, ru_cover],
        319: [('Акварельний татуаж губ', '1,5–2 години', g(PRICE['lips'])), (ua_k, '0,5–1 година', g(PRICE['lips_k'])), ua_renew, ua_cover],
        162: [('Татуаж стрелок', '1,5–2 часа', g(PRICE['strilka'])), ('Стрелка с растушевкой', '1,5–2 часа', g(PRICE['strilka'])),
              ('Межресничное пространство', '1–1,5 часа', g(PRICE['mizh'])), ('Коррекция стрелки (в течение 3 месяцев)', '0,5–1 час', g(PRICE['strilka_k'])),
              ('Коррекция межреснички (в течение 3 месяцев)', '0,5–1 час', g(PRICE['mizh_k'])), ru_cover],
        317: [('Татуаж стрілок', '1,5–2 години', g(PRICE['strilka'])), ('Стрілка з розтушовкою', '1,5–2 години', g(PRICE['strilka'])),
              ('Міжвійковий простір', '1–1,5 години', g(PRICE['mizh'])), ('Корекція стрілки (протягом 3 місяців)', '0,5–1 година', g(PRICE['strilka_k'])),
              ('Корекція міжвійки (протягом 3 місяців)', '0,5–1 година', g(PRICE['mizh_k'])), ua_cover],
        163: [('Межресничный татуаж', '1–1,5 часа', g(PRICE['mizh'])), (ru_k, '0,5–1 час', g(PRICE['mizh_k'])), ru_cover],
        318: [('Міжвійковий татуаж', '1–1,5 години', g(PRICE['mizh'])), (ua_k, '0,5–1 година', g(PRICE['mizh_k'])), ua_cover],
        119: [('Коррекция бровей', '1–1,5 часа', g(PRICE['brows_k'])), ('Коррекция губ', '1–1,5 часа', g(PRICE['lips_k'])),
              ('Коррекция стрелки', '1–1,5 часа', g(PRICE['strilka_k'])), ('Коррекция межреснички', '1–1,5 часа', g(PRICE['mizh_k'])),
              ('Обновление моих работ (спустя 3+ месяца)', '1,5 часа', g(PRICE['renew'])), ('Перекрытие старого татуажа', '1–1,5 часа', '+500 грн к стоимости процедуры')],
        316: [('Корекція брів', '1–1,5 години', g(PRICE['brows_k'])), ('Корекція губ', '1–1,5 години', g(PRICE['lips_k'])),
              ('Корекція стрілки', '1–1,5 години', g(PRICE['strilka_k'])), ('Корекція міжвійки', '1–1,5 години', g(PRICE['mizh_k'])),
              ('Оновлення моїх робіт (через 3+ місяці)', '1,5 години', g(PRICE['renew'])), ('Перекриття старого татуажу', '1–1,5 години', '+500 грн до вартості процедури')],
        170: [('Удаление старого перманента ремувером (1 сеанс)', '30 мин', g(PRICE['remover']))],
        322: [('Видалення старого перманенту ремувером (1 сеанс)', '30 хв', g(PRICE['remover']))],
    }
    for rid, rows in T.items():
        site.tv_set(rid, 'table-res-bl7', mk(rows))
    # prices page tables
    site.tv_set(44, 'table-price-1', mk([('Пудровые брови', '1,5 часа', g(PRICE['brows'])), (ru_k, '1 час', g(PRICE['brows_k'])), ru_renew, ru_cover]))
    site.tv_set(44, 'table-price-2', mk([('Акварельный татуаж губ', '1,5 часа', g(PRICE['lips'])), (ru_k, '1,5 часа', g(PRICE['lips_k'])), ru_renew, ru_cover]))
    site.tv_set(44, 'table-price-3', mk([('Межресничное пространство', '1 час', g(PRICE['mizh'])), ('Классическая стрелка', '1,5 часа', g(PRICE['strilka'])),
                                         ('Стрелка с растушевкой', '1,5 часа', g(PRICE['strilka'])), ('Коррекция стрелки (в течение 3 месяцев)', '1 час', g(PRICE['strilka_k'])),
                                         ('Коррекция межреснички (в течение 3 месяцев)', '1 час', g(PRICE['mizh_k'])), ru_cover]))
    site.tv_set(270, 'table-price-1', mk([('Пудрові брови', '1,5 години', g(PRICE['brows'])), (ua_k, '1 година', g(PRICE['brows_k'])), ua_renew, ua_cover]))
    site.tv_set(270, 'table-price-2', mk([('Акварельний татуаж губ', '1,5 години', g(PRICE['lips'])), (ua_k, '1,5 години', g(PRICE['lips_k'])), ua_renew, ua_cover]))
    site.tv_set(270, 'table-price-3', mk([('Міжвійковий простір', '1 година', g(PRICE['mizh'])), ('Класична стрілка', '1,5 години', g(PRICE['strilka'])),
                                          ('Стрілка з розтушовкою', '1,5 години', g(PRICE['strilka'])), ('Корекція стрілки (протягом 3 місяців)', '1 година', g(PRICE['strilka_k'])),
                                          ('Корекція міжвійки (протягом 3 місяців)', '1 година', g(PRICE['mizh_k'])), ua_cover]))
    for rid in (44, 270):
        if site.tv_get(rid, 'table-price-4'):
            REPORT['prices'].append(f"{rid}: table-price-4 left as in Dnipro: {site.tv_get(rid, 'title-price-4')}")
    RANGE = {1: '1000-3500', 193: '1000-3500', 2: '1700-3500', 303: '1700-3500', 51: '1700-3500', 304: '1700-3500', 167: '1700-3500', 319: '1700-3500',
             162: '1000-3000', 317: '1000-3000', 163: '1000-2000', 318: '1000-2000', 119: '1000-2000', 316: '1000-2000', 44: '1000-3500', 270: '1000-3500'}
    for rid, rg in RANGE.items():
        site.tv_set(rid, 'seo-price-range', rg + ' UAH')

# ------------------------------------------------------------------ 3. images in TVs
def image_pass(site):
    # trainer photo + about photo (home)
    site.tv_set(1, 'img_bl5_about', 'inna-master.jpg')                 # web: media source "Design" (images/design/)
    site.tv_set(193, 'img_bl5_about', 'images/design/inna-master.jpg')  # ua: media source Filesystem
    site.tv_set(1, 'img_bl1_about', 'inna-2.jpg')
    site.tv_set(193, 'img_bl1_about', 'images/design/inna-2.jpg')
    for rid in (315, 336, 337, 1, 193):
        site.tv_set(rid, 'image_bl1_about', 'images/design/inna-2.jpg')
    for rid in (1, 193):
        site.tv_set(rid, 'image_bl5_about', 'images/design/inna-master.jpg')
    # banners (source Design both ctx)
    for (ru, ua), k in {(2, 303): 'brows', (51, 304): 'powder', (167, 319): 'lips', (162, 317): 'strilky', (163, 318): 'mizhviyka'}.items():
        for rid in (ru, ua):
            site.tv_set(rid, 'img_banner_main', f'inna-banner-{k}.jpg')
    # SEO block pictures (source All = images/all/)
    for (ru, ua), k in {(1, 193): 'home', (2, 303): 'brows', (51, 304): 'powder', (167, 319): 'lips', (162, 317): 'strilky',
                        (163, 318): 'mizhviyka', (119, 316): 'korekciya'}.items():
        for rid in (ru, ua):
            site.tv_set(rid, 'img-bl-seo', f'inna-{k}.jpg')
    # portfolio album covers (source Design)
    for rid in (100, 198):
        site.tv_set(rid, 'img-p-1', 'inna-album-brows.jpg')
        site.tv_set(rid, 'img-p-2', 'inna-album-eyes.jpg')
        site.tv_set(rid, 'img-p-3', 'inna-album-lips.jpg')
    # leading slash in Filesystem-source values would break relative URLs
    for tid, cid, val in site.q(f"select cv.tmplvarid,cv.contentid,cv.value from {P}site_tmplvar_contentvalues cv join {P}site_tmplvars v on v.id=cv.tmplvarid where v.type='image' and cv.value like '/images/%%'"):
        site.q(f"update {P}site_tmplvar_contentvalues set value=%s where tmplvarid=%s and contentid=%s", (val.lstrip('/'), tid, cid))

# ------------------------------------------------------------------ 4. links
KYIV_ALIAS = {  # old Kyiv aliases used in content -> (ru uri, ua uri)
    'permanentnyy-makiyazh-brovey': ('tatuazh-brovey', 'tatuazh-briv'),
    'lazernoye-udaleniye-tatuazha-i-tatu': ('udalenie-tatuazha-remuverom', 'vydalennya-tatuazhu-remuverom'),
    'tatuazh-gub': ('akvarelnayi-gubu', 'akvarelnayi-gubu'),
    'permanentnyy-makiyazh-glaz': ('tatuazh-strelok', 'tatuazh-strilok'),
    'pudrovi-brovi': ('pudrovyye-brovi', 'pudrovi-brovi'),
    'pudrovyye-brovi': ('pudrovyye-brovi', 'pudrovi-brovi'),
    'tatuazh-brovey': ('tatuazh-brovey', 'tatuazh-briv'),
    'tatuazh-briv': ('tatuazh-brovey', 'tatuazh-briv'),
    'tatuazh-strilok': ('tatuazh-strelok', 'tatuazh-strilok'),
    'tatuazh-strelok': ('tatuazh-strelok', 'tatuazh-strilok'),
    'uslugi': ('uslugi', 'poslugi'), 'poslugi': ('uslugi', 'poslugi'),
    'mini-tatu': ('mini-tatu', 'mini-tatu-ua'), 'mini-tatu-ua': ('mini-tatu', 'mini-tatu-ua'),
    'udalenie-tatuazha-remuverom': ('udalenie-tatuazha-remuverom', 'vydalennya-tatuazhu-remuverom'),
    'vydalennya-tatuazhu-remuverom': ('udalenie-tatuazha-remuverom', 'vydalennya-tatuazhu-remuverom'),
}
def resolve(site, ctx, href):
    """return [[~id]] for an internal link or None"""
    h = html.unescape(href.strip())
    m = re.match(r'^(?:https?://(?:www\.)?lbar\.com\.ua)?/?(dnipro/)?(ua/)?([^?#]*)(.*)$', h)
    if not m or h.startswith(('#', 'mailto:', 'tel:', 'viber:', 'whatsapp:', '[[')):
        return None
    absolute = h.startswith('http')
    if absolute and 'lbar.com.ua' not in h:
        return None
    is_dnipro, is_ua, path, tail = m.group(1), m.group(2), m.group(3).strip('/'), m.group(4)
    if absolute and not is_dnipro and path.startswith(('ua/', 'blog')):
        pass
    tctx = 'ua' if is_ua else ('web' if (is_dnipro or absolute) else ctx)
    if absolute and not is_dnipro:
        # link into the Kyiv site: only keep local if a page with this uri exists here
        if (tctx, path) not in site.byuri and path not in ('portfolio', 'otzyvy', 'tseny', 'kontakty', 'o-nas'):
            return None
    if path == '':
        rid = 1 if tctx == 'web' else 193
    elif (tctx, path) in site.byuri:
        rid = site.byuri[(tctx, path)]
    elif path in KYIV_ALIAS:
        u = KYIV_ALIAS[path][0 if tctx == 'web' else 1]
        rid = site.byuri.get((tctx, u))
    else:
        rid = None
    if rid is None:
        return 'BROKEN'
    return f'[[~{rid}]]' + (tail if tail.startswith('#') else '')

def link_pass(site):
    hrefrx = re.compile(r'''(href\s*=\s*)(["'])(.*?)\2''', re.I)
    LINK_TVS = ['link-bl6', 'link-p-1', 'link-p-2', 'link-p-3', 'link-p-4', 'link-p-5', 'link_bl5_about']
    for rid, (ctx, uri, tpl) in site.live.items():
        def fn(s, ctx=ctx, rid=rid):
            def rep(m):
                r = resolve(site, ctx, m.group(3))
                if r is None:
                    return m.group(0)
                if r == 'BROKEN':
                    REPORT['broken_links'].append(f"{rid}/{ctx}: {m.group(3)}")
                    return m.group(0)
                return m.group(1) + m.group(2) + r + m.group(2)
            return hrefrx.sub(rep, s)
        map_text_fields(site, rid, fn)
        for name in LINK_TVS:
            v = site.tv_get(rid, name)
            if v and not v.startswith('[['):
                r = resolve(site, ctx, v)
                if r and r != 'BROKEN':
                    site.tv_set(rid, name, r)
                elif r == 'BROKEN':
                    REPORT['broken_links'].append(f"{rid}/{ctx} tv {name}: {v}")
    # remove <a> around links to pages that don't exist here (keep the text)
    for rid, (ctx, uri, tpl) in site.live.items():
        def unlink(s, rid=rid, ctx=ctx):
            def rep(m):
                r = resolve(site, ctx, m.group(2))
                if r == 'BROKEN':
                    return m.group(3)
                return m.group(0)
            return re.sub(r'<a\s[^>]*href\s*=\s*(["\'])(.*?)\1[^>]*>(.*?)</a>', rep, s, flags=re.S | re.I)
        map_text_fields(site, rid, unlink)

def footer_fix(site):
    for rid in (1, 193):
        for name in ('foot-link-l', 'foot-link-r'):
            v = site.tv_get(rid, name)
            if not v: continue
            v = v.replace('<p>Главная</p>', '<p><a href="[[++site_url]]">Главная</a></p>')
            v = re.sub(r'\s*<p>(Блог|Другие цены|Інші ціни)(<br />)?</p>', '', v)
            site.tv_set(rid, name, v)

# ------------------------------------------------------------------ 5. ms2Gallery
def gallery_pass(site):
    rows = json.load(open('/home/claude/work/gallery_rows.json'))
    rids = sorted({r['resource_id'] for r in rows})
    # drop old rows of replaced galleries
    site.q(f"delete from {P}ms2_resource_files where resource_id in ({','.join(map(str, rids))})")
    nid = site.q(f"select max(id) from {P}ms2_resource_files")[0][0] + 1000
    now = '2026-11-22 12:00:00'
    DESC = {
        'ru': {'brows': 'Перманентный макияж бровей — работа мастера Инны, LBar Ивано-Франковск',
               'lips': 'Перманентный макияж губ — работа мастера Инны, LBar Ивано-Франковск',
               'strilky': 'Татуаж стрелок — работа мастера Инны, LBar Ивано-Франковск',
               'mizhviyka': 'Межресничный татуаж — работа мастера Инны, LBar Ивано-Франковск'},
        'ua': {'brows': 'Перманентний макіяж брів — робота майстра Інни, LBar Івано-Франківськ',
               'lips': 'Перманентний макіяж губ — робота майстра Інни, LBar Івано-Франківськ',
               'strilky': 'Татуаж стрілок — робота майстра Інни, LBar Івано-Франківськ',
               'mizhviyka': 'Міжвійковий татуаж — робота майстра Інни, LBar Івано-Франківськ'},
    }
    for r in rows:
        rid = r['resource_id']; lang = LANG[site.live[rid][0]]
        pid = nid; nid += 1
        url = f"assets/images/resources/{rid}/{r['file']}"
        site.q(f"""insert into {P}ms2_resource_files (id,resource_id,source,parent,name,alt,description,path,file,type,createdon,createdby,`rank`,url,properties,hash,active)
                   values (%s,%s,2,0,%s,%s,%s,%s,%s,'image',%s,1,%s,%s,%s,%s,1)""",
               (pid, rid, r['name'], '', DESC[lang][r['kind']], r['path'], r['file'], now, r['rank'], url, json.dumps(r['props']), r['hash']))
        for th in ('small', 'medium'):
            tid = nid; nid += 1
            site.q(f"""insert into {P}ms2_resource_files (id,resource_id,source,parent,name,alt,description,path,file,type,createdon,createdby,`rank`,url,properties,hash,active)
                       values (%s,%s,2,%s,%s,%s,%s,%s,%s,'image',%s,1,%s,%s,%s,%s,1)""",
                   (tid, rid, pid, r['name'], '', None, f"{rid}/{th}/", r['file'], now, r['rank'],
                    f"assets/images/resources/{rid}/{th}/{r['file']}", json.dumps(r['thumbs'][th]), r['thumb_hash'][th]))
    # remaining galleries: make URLs relative to the site (they used /assets/... of Kyiv root or /dnipro/assets/...)
    site.q(f"update {P}ms2_resource_files set url=substring(url, 9) where url like '/dnipro/assets/%%'")
    site.q(f"update {P}ms2_resource_files set url=substring(url, 2) where url like '/assets/%%'")
    # review screenshots (171/299) belong to other cities -> hide
    site.q(f"update {P}ms2_resource_files set active=0 where resource_id in (171,299)")
    REPORT['gallery'].append('review screenshots on otzyvy (171/299) set active=0')

# ------------------------------------------------------------------ 6. chunks & templates
def element_pass(site):
    def fix_paths(s):
        s = s.replace('[[++cultureKey:is=`uk`:then=`/dnipro/`]]', '').replace('[[++cultureKey:is=`uk`:then=`/dnipro`]]', '')
        s = s.replace('/dnipro/[[*img-bl-seo]]', '[[*img-bl-seo]]')
        s = s.replace('/dnipro/[[*img_banner_main:empty=`/dnipro/images/design/IMG_5877-min.jpg`]]', '[[*img_banner_main:empty=`images/design/inna-banner-brows.jpg`]]')
        s = s.replace('/dnipro/assets/', '[[++assets_url]]')
        s = s.replace('/dnipro/images/', 'images/')
        s = re.sub(r'''((?:src|href|data-src|poster)\s*=\s*["'])/assets/''', r'\1[[++assets_url]]', s)
        s = re.sub(r'''((?:src|href|data-src|poster)\s*=\s*["'])/images/''', r'\1images/', s)
        s = re.sub(r'''url\(\s*(["']?)/images/''', r'url(\1images/', s)
        s = s.replace('href="/[[*link-bl6]]"', 'href="[[*link-bl6]]"')
        s = re.sub(r'''((?:src|data-src)\s*=\s*["'])/(\[\[)''', r'\1\2', s)
        s = s.replace('src="/[[*img_banner_main]]"', 'src="[[*img_banner_main]]"')
        s = s.replace('"https://lbar.com.ua/images/design/logo-schema.jpg"', '"[[++site_url]]images/design/logo-schema.jpg"')
        return s
    for tbl, col, key in ((f'{P}site_htmlsnippets', 'snippet', 'name'), (f'{P}site_templates', 'content', 'templatename')):
        for i, name, val in site.q(f"select id,{key},{col} from {tbl}"):
            if not val:
                continue
            nv = fix_paths(val)
            if nv != val:
                site.q(f"update {tbl} set {col}=%s where id=%s", (nv, i))
                REPORT['elements'].append(f"{tbl.split('_X_')[1]}: {name}")
    ch = lambda n: site.q(f"select snippet from {P}site_htmlsnippets where name=%s", (n,))[0][0]
    def put(n, v): site.q(f"update {P}site_htmlsnippets set snippet=%s where name=%s", (v, n))
    # header: city switcher + popup city
    h = ch('header')
    h = h.replace('<div class="custom-select__trigger"><span>[[++cultureKey:is=`ru`:then=`Днепр`:else=`Дніпро`]]</span>',
                  '<div class="custom-select__trigger"><span>[[++cultureKey:is=`ru`:then=`Ивано-Франковск`:else=`Івано-Франківськ`]]</span>')
    h = h.replace('<a href="#" class="custom-option selected" data-value="Dnipro">[[++cultureKey:is=`ru`:then=`Днепр`:else=`Дніпро`]]</a>',
                  '<a href="#" class="custom-option selected" data-value="Ivano-Frankivsk">[[++cultureKey:is=`ru`:then=`Ивано-Франковск`:else=`Івано-Франківськ`]]</a>\n'
                  '                <a href="https://lbar.com.ua/dnipro/" target="_blank" rel="dofollow" class="custom-option" data-value="Dnipro">[[++cultureKey:is=`ru`:then=`Днепр`:else=`Дніпро`]]</a>')
    h = h.replace('[[++cultureKey:is=`ru`:then=`Ваш город: <span>Киев</span>`:else=`Ваше місто: <span>Київ</span>`]]',
                  '[[++cultureKey:is=`ru`:then=`Ваш город: <span>Ивано-Франковск</span>`:else=`Ваше місто: <span>Івано-Франківськ</span>`]]')
    assert 'Ivano-Frankivsk' in h and 'Ваш город: <span>Ивано' in h
    put('header', h)
    # schema.org: address from ClientConfig, city, no Kyiv geo
    s = ch('script')
    s = re.sub(r'"address": \{.*?\},\s*"geo": \{.*?\},', '''"address": {
                "@type": "PostalAddress",
                "streetAddress": "[[++cultureKey:is=`ru`:then=`[[++adress]]`:else=`[[++adress-ua]]`]]",
                "addressLocality": "[[++cultureKey:is=`ru`:then=`Ивано-Франковск`:else=`Івано-Франківськ`]]",
                "addressRegion": "[[++cultureKey:is=`ru`:then=`Ивано-Франковская обл.`:else=`Івано-Франківська обл.`]]",
                "addressCountry": "UA"
				},''', s, flags=re.S)
    s = s.replace('"description": "Студия перманентного макияжа Lbar"', '"description": "[[++cultureKey:is=`ru`:then=`Студия перманентного макияжа LBar в Ивано-Франковске`:else=`Студія перманентного макіяжу LBar в Івано-Франківську`]]"')
    assert 'Киев' not in s
    s = s.replace('window.location.href = "[[~40]]"', 'window.location.href = "[[~[[++cultureKey:is=`ru`:then=`40`:else=`269`]]]]"')
    put('script', s)
    for n in ('tpl.ecMessages.Row.Micro', 'bl5 - copy seo star'):
        v = ch(n).replace('content="Киев, Шевченковский район, ул. Шолуденка 5 (метро Лукьяновская/Политех)"',
                          'content="[[++cultureKey:is=`ru`:then=`[[++adress]]`:else=`[[++adress-ua]]`]]"')
        put(n, v)
    # price table headers were RU-only in the UA version
    for n in ('table-three-col-bl7', 'table-two-col-bl7'):
        v = ch(n).replace('<th>Время</th>', '<th>[[++cultureKey:is=`ru`:then=`Время`:else=`Час`]]</th>')
        v = v.replace('<th>Цена</th>', '<th>[[++cultureKey:is=`ru`:then=`Цена`:else=`Ціна`]]</th>')
        put(n, v)
    # reviews block: Google Maps link of the Dnipro studio -> off
    v = ch('bl9-reviews')
    v = v.replace('[[*id:is=`51`:or:is=`304`:then=`', '[[*id:is=`-1`:then=`')
    put('bl9-reviews', v)

# ------------------------------------------------------------------ 7. contexts, plugin, settings
def env_pass(site, host, base):
    """host like https://lbar-frankovsk.touchit.vinnica.ua ; base like / or /ivano-frankivsk/"""
    S = {('ua', 'base_url'): base, ('ua', 'site_url'): host + base,
         ('web', 'base_url'): base + 'ru/', ('web', 'site_url'): host + base + 'ru/',
         ('ua', 'site_name'): 'Студія ПМ LBar Івано-Франківськ', ('web', 'site_name'): 'Студия ПМ LBar Ивано-Франковск'}
    for (ctx, k), v in S.items():
        site.q(f"update {P}context_setting set value=%s where context_key=%s and `key`=%s", (v, ctx, k))
    for ctx in ('web', 'ua'):
        site.q(f"insert into {P}context_setting (context_key,`key`,value,xtype,namespace,area,editedon) values (%s,'session_cookie_path',%s,'textfield','core','session',NOW()) on duplicate key update value=values(value)", (ctx, base))
    site.q(f"update {P}context set name='Русский (RU)', description='Русская версия (/ru/)' where `key`='web'")
    site.q(f"update {P}context set name='Українська (UA, основна)', description='Основна українська версія (корінь сайту)' where `key`='ua'")

def settings_pass(site):
    code = site.q(f"select plugincode from {P}site_plugins where name='switchContext'")[0][0]
    new = re.sub(r"case 'ua':\s*\n\$modx->switchContext\('ua'\);",
                 "case 'ru':\n$modx->switchContext('web');", code)
    new = re.sub(r"default:(\s*)\$modx->switchContext\('web'\);", r"default:\1$modx->switchContext('ua');", new)
    new = new.replace('/* Устанавливаем контекст по умолчанию */', '/* Контекст по умолчанию: украинский (ua) в корне сайта, русский (web) в /ru/ */')
    assert "case 'ru':" in new and "switchContext('ua');" in new.split('default:')[1], new
    site.q(f"update {P}site_plugins set plugincode=%s where name='switchContext'", (new,))
    site.q(f"update {P}system_settings set value='ua,web' where `key`='babel.contextKeys'")
    site.q(f"update {P}system_settings set value=%s where `key`='site_name'", ('Студія ПМ LBar Івано-Франківськ',))
    # ClientConfig: city-specific values. Address/map/phone: placeholders until the client sends them
    CC = {
        'adress': 'Ивано-Франковск (адрес уточняется)',
        'adress-ua': 'Івано-Франківськ (адреса уточнюється)',
        'google-map': '<iframe src="https://www.google.com/maps?q=%D0%86%D0%B2%D0%B0%D0%BD%D0%BE-%D0%A4%D1%80%D0%B0%D0%BD%D0%BA%D1%96%D0%B2%D1%81%D1%8C%D0%BA&amp;z=13&amp;output=embed" width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>',
        'autor': 'LBar Ивано-Франковск', 'autor-ua': 'LBar Івано-Франківськ',
    }
    for k, v in CC.items():
        site.q(f"update {P}clientconfig_setting set value=%s where `key`=%s", (v, k))
    # reviews of other cities/masters -> hidden (published=0, kept in DB)
    n = site.q(f"""select count(*) from {P}ec_messages m join {P}ec_threads t on t.id=m.thread
                   where m.published=1 and t.resource in ({','.join(map(str, site.live))})""")[0][0]
    site.q(f"""update {P}ec_messages m join {P}ec_threads t on t.id=m.thread set m.published=0
               where m.published=1 and t.resource in ({','.join(map(str, site.live))})""")
    site.q(f"update {P}ec_threads set rating_simple=0, rating_wilson=0, count=0 where resource in ({','.join(map(str, site.live))})")
    REPORT['reviews'].append(f'{n} published reviews (Dnipro/Kyiv) set published=0')
    # logs / stats / sessions start clean (tables already empty in slim dump)
    for t in ('session', 'manager_log', 'stat_online_users', 'stat_page_statistics', 'register_messages', 'active_users'):
        site.q(f"truncate table {P}{t}")

def check(site):
    bad = collections.Counter()
    for rid, (ctx, uri, tpl) in site.live.items():
        def fn(s, rid=rid):
            for w in re.findall(r'\w*(?:Днеп|Дніп|Днип|dnipro|Киев|Києв|Київ|Ольг|Анастас|Ксюн)\w*', s):
                bad[(rid, w)] += 1
            return s
        map_text_fields(site, rid, fn)
    return bad

if __name__ == '__main__':
    rebuild()
    site = Site(conn())
    content_pass(site); print('content ok')
    price_pass(site); print('prices ok')
    image_pass(site); print('images ok')
    link_pass(site); footer_fix(site); print('links ok')
    gallery_pass(site); print('gallery ok')
    element_pass(site); print('elements ok')
    env_pass(site, 'https://lbar-frankovsk.touchit.vinnica.ua', '/')
    settings_pass(site); print('settings ok')
    for k, v in check(site).items():
        REPORT['leftovers'].append(f'{k[0]}: {k[1]} x{v}')
    json.dump(REPORT, open('/home/claude/work/report.json', 'w'), ensure_ascii=False, indent=1)
    for k, v in REPORT.items():
        print('==', k, len(v))
        for x in v[:80]:
            print('  ', x)
