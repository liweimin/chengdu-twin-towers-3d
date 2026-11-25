from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter, binary_fill_holes, label
from matplotlib.figure import Figure

rng=np.random.default_rng(794)
assets=Path('assets')
thumbs={}
fig=Figure()
ax=fig.subplots()
for source, names in [('atlas',('tower','gate','temple','hall','lake','ridge')),
                      ('props',('boat','willow','skyline','guard','cypress','houses'))]:
    a=np.array(Image.open(assets/f'{source}.png').convert('RGB')).astype(float)
    for k,name in enumerate(names):
        b=a[(k//3)*512:(k//3+1)*512,(k%3)*512:(k%3+1)*512].copy()
        delta=np.minimum(b[:,:,0],b[:,:,2])-b[:,:,1]
        alpha=np.clip((164-delta)/108,0,1)
        strong=alpha>.59
        labels,n=label(strong)
        sizes=np.bincount(labels.ravel())
        keep=np.where((sizes>=26)&(np.arange(len(sizes))>0))[0]
        mask=binary_fill_holes(np.isin(labels,keep))
        alpha*=gaussian_filter(mask.astype(float),.8)>.04
        rows,cols=np.where(alpha>.40)
        y0,y1=rows.min(),rows.max()+1
        x0,x1=cols.min(),cols.max()+1
        # Remove magenta spill from the cut edge and restore a matte ink response.
        weak=(alpha>.005)&(alpha<.99)
        b[:,:,0][weak]=np.minimum(b[:,:,0][weak],b[:,:,1][weak]+52)
        b[:,:,2][weak]=np.minimum(b[:,:,2][weak],b[:,:,1][weak]+36)
        b=(b*.94+np.array([12,8,4])).clip(0,255)
        b+=rng.normal(0,.9,b.shape[:2])[:,:,None]
        alpha=alpha[y0:y1,x0:x1]
        b=b[y0:y1,x0:x1]
        h,w=alpha.shape
        rgba=np.uint8(np.dstack((b.clip(0,255),alpha*255)))
        Image.fromarray(rgba).save(assets/f'{name}.png',optimize=True)

        # Half-millimeter card stock wraps the perimeter of the printed face.
        ax.clear()
        z=np.pad(alpha,1)
        con=ax.contour(z,levels=[.56])
        paths=[]
        for seg in con.allsegs[0]:
            if len(seg)<27: continue
            seg=seg[::3]
            paths.append([[round((x-1+.5)/w,5),round((y-1+.5)/h,5)] for x,y in seg])
        thumbs[name]={'ratio':round(w/h,6),'paths':paths}

        # Emissive ink masks align with windows, lanterns and step lighting.
        lamp=Image.new('RGB',(w,h))
        draw=ImageDraw.Draw(lamp)
        def dot(u,v,r,c,elong=1):
            x,y=u*w,v*h
            if (0<x<w and 0<y<h and alpha[round(y)-1,round(x)-1]>.7):
                draw.ellipse((x-r*elong,y-r,x+r*elong,y+r),fill=c)
        if name=='tower':
            for v in np.arange(.22,.97,.018):
                for u in np.arange(.165,.85,.07):
                    if rng.random()<.47: dot(u+rng.normal(0,.005),v,rng.uniform(.53,1.3),(247,176,83),1.35)
            dot(.52,.032,1,(255,101,58))
        if name=='skyline':
            for v in np.arange(.13,.97,.053):
                for u in np.arange(.035,.99,.032):
                    if rng.random()<.49: dot(u,v,rng.uniform(.65,1.5),(247,192,108),1.4)
        if name=='temple':
            for u,v in [(.017,.708),(.083,.683),(.139,.666),(.227,.667),(.299,.648),(.411,.684),(.479,.692),(.557,.696),(.664,.676),(.798,.705),(.856,.695),(.916,.696),(.977,.699),(.388,.369),(.408,.369),(.436,.369)]:
                dot(u,v,2.25,(255,118,27),.92)
            for u in np.arange(.04,.96,.041): dot(u,.798,1.3,(237,143,55),1.8)
        if name in ('hall','gate','guard','houses','lake','boat'):
            pts={'hall':[(.354,.54),(.5,.532),(.65,.54),(.345,.68),(.655,.68),(.308,.78),(.697,.78),(.252,.9),(.749,.9)],
                'gate':[(.29,.86),(.473,.82),(.512,.83),(.72,.86)],
                'guard':[(.35,.54),(.50,.54),(.65,.54)],
                'houses':[(.19,.75),(.32,.72),(.60,.75),(.65,.69),(.79,.77),(.90,.76)],
                'lake':[(.78,.73),(.85,.73)],
                'boat':[(.33,.59),(.53,.57),(.68,.63)]}[name]
            for u,v in pts: dot(u,v,2.3,(255,167,59),1.2)
        if lamp.getbbox():
            soft=lamp.filter(ImageFilter.GaussianBlur(3))
            mix=np.asarray(lamp).astype(float)*.85+np.asarray(soft)*1.45
            Image.fromarray(np.uint8(np.clip(mix,0,255))).save(assets/f'{name}-light.png',optimize=True)
(assets/'silhouettes.json').write_text(json.dumps(thumbs,separators=(',',':')))

# Planed walnut with long anisotropic grain, medullary rays and board seams.
w,h=1600,1600
y,x=np.mgrid[0:h,0:w].astype(np.float32)
x/=w; y/=h
base=np.zeros((h,w),dtype=np.float32)
warp=.028*np.sin(x*7.4+y*5.2)+.012*np.sin(x*18.2-y*13.4)+.004*np.sin(x*45+y*13)
for cx,cy,strength in [(.33,.24,.044),(.69,.71,-.036),(.77,.52,.025),(.16,.82,-.027)]:
    dx=x-cx; dy=y-cy
    warp+=strength*np.exp(-dx*dx*24-dy*dy*95)*np.tanh(dy*40)
t=y+warp
for freq,power in [(23,4.4),(55,4.1),(91,2.05),(191,1.75),(382,1.42),(672,.75)]:
    base+=power*np.sin(t*freq*2*np.pi+2.5*np.sin(x*7+freq*.2)+np.sin(x*22)*.68)
for bw,power in [(14,4.9),(70,2.3),(310,1.3)]:
    tex=Image.fromarray(rng.integers(0,255,(bw,19),dtype=np.uint8)).resize((w,h),Image.Resampling.BICUBIC)
    base+=(np.asarray(tex,dtype=np.float32)-128)*power/54
base+=rng.normal(0,1.45,(h,w))
for ys in [.283,.563,.839]:
    base-=14*np.exp(-((y-ys)/.0016)**2)
    base+=4*np.exp(-((y-ys-.0022)/.0012)**2)
for k,(a,b) in enumerate(zip([0,.283,.563,.839],[.283,.563,.839,1])):
    base+=np.where((y>=a)&(y<b),[1.3,-4,2,-3][k],0)
wood=np.array([111,72,47])+base[:,:,None]*np.array([1.55,1.09,.73])
Image.fromarray(np.uint8(np.clip(wood,0,255))).save(assets/'walnut.jpg',quality=92,subsampling=0,optimize=True)
