"""Prepare Inna's photos: portraits, banners, SEO images, ms2Gallery sets (+medium/small thumbs).
Writes files to /home/claude/out/site/... and a JSON manifest of gallery rows for the SQL step."""
import os, json, hashlib
from PIL import Image, ImageOps
import pillow_heif; pillow_heif.register_heif_opener()
SRC='/home/claude/src/img'; OUT='/home/claude/out/site'
FLIP={'IMG_0936','IMG_1817','IMG_2167','IMG_2530','IMG_3209','IMG_4493','IMG_5462','IMG_6009','IMG_8021'}
def load(n):
    for ext in ('.JPG','.HEIC','.PNG','.jpg'):
        p=os.path.join(SRC,n+ext)
        if os.path.exists(p):
            im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
            if n in FLIP: im=im.rotate(180)
            return im
    raise FileNotFoundError(n)
def save(im,rel,q=84):
    p=os.path.join(OUT,rel); os.makedirs(os.path.dirname(p),exist_ok=True)
    im.save(p,'JPEG',quality=q,optimize=True,progressive=True)  # no exif -> metadata stripped
    return p
def fit_long(im,L):
    im=im.copy(); im.thumbnail((L,L),Image.LANCZOS); return im
def cover(im,w,h,cy=0.5,cx=0.5):
    """crop to aspect w:h around (cx,cy) then resize"""
    W,H=im.size; r=w/h
    if W/H>r: nw=int(H*r); x=int((W-nw)*cx); box=(x,0,x+nw,H)
    else: nh=int(W/r); y=int((H-nh)*cy); box=(0,y,W,y+nh)
    return im.crop(box).resize((w,h),Image.LANCZOS)
# ---------- portraits ----------
p=load('IMG_7905'); save(p.crop((0,120,941,1296)).resize((800,1000),Image.LANCZOS),'images/design/inna-master.jpg')
pl=load('IMG_7922'); save(pl.crop((0,0,560,640)),'images/design/inna-2.jpg',q=88)
# ---------- banners (650x700) & seo (images/all) & album covers ----------
BANNER={'brows':('IMG_7809',0.45),'powder':('IMG_7611',0.35),'lips':('IMG_3838',0.5),'strilky':('IMG_7574',0.5),'mizhviyka':('IMG_9542',0.5)}
for k,(n,cy) in BANNER.items(): save(cover(load(n),650,700,cy),f'images/design/inna-banner-{k}.jpg')
SEO={'home':'IMG_6454','brows':'IMG_4439','powder':'IMG_7105','lips':'IMG_6849','strilky':'IMG_2079','mizhviyka':'IMG_9476','korekciya':'IMG_9183'}
for k,n in SEO.items(): save(fit_long(load(n),1000),f'images/all/inna-{k}.jpg')
ALB={'brows':'IMG_7809','eyes':'IMG_7574','lips':'IMG_3838'}
for k,n in ALB.items(): save(cover(load(n),600,600),f'images/design/inna-album-{k}.jpg')
# ---------- galleries ----------
BROWS=['IMG_7809','IMG_7611','IMG_4439','IMG_7105','IMG_6014','IMG_5463','IMG_9183','IMG_6667','IMG_7058','IMG_1781','IMG_5267','IMG_9641',
       'IMG_0936','IMG_1817','IMG_2167','IMG_2530','IMG_3209','IMG_4493','IMG_5462','IMG_6009','IMG_8021','IMG_6764','IMG_7055','IMG_5986','IMG_9969']
LIPS=['IMG_3838','IMG_6454','IMG_6849','IMG_0140','IMG_9574','IMG_0063','IMG_0526','IMG_0540','IMG_0813','IMG_2111','IMG_5588','IMG_6376',
      'IMG_6879','IMG_8621','IMG_8649','IMG_8657','IMG_9742','IMG_9751','IMG_9962','IMG_0244']
STRILKY=['IMG_7574','IMG_7570','IMG_2079']
MIZH=['IMG_9542','IMG_9476']
SETS={
 'home':   ['IMG_7809','IMG_3838','IMG_7611','IMG_6454','IMG_7574','IMG_4439','IMG_6849','IMG_7105','IMG_0140','IMG_9542','IMG_6014','IMG_9574'],
 'brows':  BROWS[:12],
 'powder': BROWS[12:24],
 'lips':   LIPS[:19],
 'strilky':STRILKY+['IMG_9542'],
 'mizhviyka':MIZH+['IMG_2079'],
 'korekciya':['IMG_9969','IMG_9183','IMG_6667','IMG_8649','IMG_8621','IMG_9742','IMG_5463','IMG_7058'],
 'album-brows':BROWS,
 'album-eyes':STRILKY+MIZH,
 'album-lips':LIPS,
}
KIND={**{n:'brows' for n in BROWS},**{n:'lips' for n in LIPS},**{n:'strilky' for n in STRILKY},**{n:'mizhviyka' for n in MIZH}}
SLUG={'brows':'permanent-briv','lips':'permanent-gub','strilky':'tatuazh-strilok','mizhviyka':'mizhviykovyi-tatuazh'}
# resource ids (ru web, ua) per set
RES={'home':(1,193),'brows':(2,303),'powder':(51,304),'lips':(167,319),'strilky':(162,317),'mizhviyka':(163,318),'korekciya':(119,316),
     'album-brows':(123,202),'album-eyes':(124,203),'album-lips':(125,204)}
cache={}
def prepared(n):
    if n not in cache: cache[n]=fit_long(load(n),1200)
    return cache[n]
num={}
fname={}
for n in KIND:
    k=KIND[n]; num[k]=num.get(k,0)+1; fname[n]=f"{SLUG[k]}-ivano-frankivsk-{num[k]:02d}.jpg"
rows=[]
def props(path):
    im=Image.open(path); return {"size":os.path.getsize(path),"width":im.size[0],"height":im.size[1],"bits":8,"mime":"image/jpeg"}
for setname,photos in SETS.items():
    for rid in RES[setname]:
        for rank,n in enumerate(photos):
            f=fname[n]; im=prepared(n)
            base=f'assets/images/resources/{rid}/'
            p0=save(im,base+f,q=84)
            pm=save(cover(im,400,400),base+'medium/'+f,q=88)
            ps=save(cover(im,120,90),base+'small/'+f,q=80)
            rows.append({'resource_id':rid,'rank':rank,'file':f,'name':f[:-4],'kind':KIND[n],'src':n,
                         'path':f'{rid}/','props':props(p0),'hash':hashlib.sha1(open(p0,'rb').read()).hexdigest(),
                         'thumbs':{'medium':props(pm),'small':props(ps)},
                         'thumb_hash':{'medium':hashlib.sha1(open(pm,'rb').read()).hexdigest(),'small':hashlib.sha1(open(ps,'rb').read()).hexdigest()}})
json.dump(rows,open('/home/claude/work/gallery_rows.json','w'),ensure_ascii=False,indent=0)
print('gallery rows',len(rows))
