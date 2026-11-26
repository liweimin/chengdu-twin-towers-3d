import math as m
import random
import sys
from bisect import bisect_right
from pathlib import Path

import numpy as np
from anime_art import draw_fighter, portrait_insert
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

W,H=1440,810
FPS=30
BLUE=(27,204,255)
RED=(255,49,101)
GOLD=(255,170,107)
TAU=m.tau
rng=random.Random(2056)

def lerp(a,b,u): return a+(b-a)*u
def clamp(v): return max(0,min(1,v))
def smooth(v):
    v=clamp(v)
    return v*v*(3-2*v)
def blend(a,b,u): return tuple(lerp(x,y,u) for x,y in zip(a,b))
def shade(c,k): return tuple(int(a*k) for a in c)
def mix(a,b,k): return tuple(int(v) for v in blend(a,b,k))
def pos(a,b): return (a[0]+b[0],a[1]+b[1])

def make_stage():
    w,h=1800,1012
    y,x=np.mgrid[:h,:w].astype(np.float32)
    x=x*(960/w); y=y*(540/h)
    horizon=np.exp(-((y-332)/127)**2)
    mist=np.exp(-((x-535)/380)**2-((y-305)/159)**2)
    ember=np.exp(-((x-821)/265)**2-((y-323)/125)**2)
    moon=np.exp(-((x-349)/180)**2-((y-187)/142)**2)
    grain=np.random.default_rng(2).normal(0,.85,(h,w))
    rgb=np.stack([20+29*horizon+21*mist+74*ember+24*moon+grain,20+17*horizon+29*mist+12*ember+20*moon+grain,40+37*horizon+44*mist+35*ember+38*moon+grain],-1)
    stage=Image.fromarray(np.clip(rgb,0,255).astype('uint8'))
    d=ImageDraw.Draw(stage,'RGBA')
    def tr(p): return [(round(a*w/960),round(b*h/540)) for a,b in p]
    def poly(p,c): d.polygon(tr(p), fill=c)
    def line(p,c,wd=1): d.line(tr(p),fill=c,width=max(1,round(wd*w/960)),joint='curve')
    def ellipse(x,y,rx,ry,c,outline=None,width=1): d.ellipse(tr([(x-rx,y-ry),(x+rx,y+ry)]),fill=c,outline=outline,width=width)
    for i in range(850):
        sx=rng.uniform(0,960); sy=rng.uniform(0,335)
        radius=rng.choices([.32,.54,.82],[66,31,3])[0]
        ellipse(sx,sy,radius,radius,(180,209,244,rng.randrange(18,115)))
    # The bright crescent is backed by several translucent atmospheric rings.
    crescent=Image.new('RGB',stage.size); cd=ImageDraw.Draw(crescent)
    for r,col in [(130,(14,19,29)),(109,(31,38,52)),(99,(51,57,68)),(94,(80,80,87)),(91,(127,112,105))]:
        cd.ellipse(tr([(357-r,165-r),(357+r,165+r)]),fill=col)
    stage=ImageChops.add(stage,crescent.filter(ImageFilter.GaussianBlur(21)))
    d=ImageDraw.Draw(stage,'RGBA')
    ellipse(357,165,91,91,(216,206,192,248))
    ellipse(360.5,161.5,90,90,(24,23,46,255))
    ellipse(360.5,161.5,89.5,89.5,None,(102,124,152,110),1)
    # Long painted cloud bands pick up dusk color on their lower edges.
    cr=random.Random(1927)
    for layer in range(3):
        for i in range(19):
            x0=cr.uniform(-155,961)
            y0=cr.uniform(178,336)-layer*31
            if 270<x0<440 and y0<239:
                continue
            lng=cr.uniform(18,182)
            depth=cr.uniform(1.6,12)
            outline=[(x0,y0+depth*.44),(x0+lng*.17,y0-depth*.26),
                (x0+lng*.34,y0-depth*.19),(x0+lng*.53,y0-depth*.85),
                (x0+lng*.65,y0-depth*.75),(x0+lng*.72,y0-depth*.26),
                (x0+lng*.86,y0-depth*.11),(x0+lng,y0+depth*.18),
                (x0+lng*.76,y0+depth*.45),(x0+lng*.56,y0+depth*.5),
                (x0+lng*.29,y0+depth*.66)]
            if x0>558:
                col=(225,147,187,35-layer*4)
                shine=(233,171,182,43-layer*8)
            else:
                col=(110,145,202,29-layer*5)
                shine=(135,187,219,39-layer*8)
            poly(outline,col)
            line(outline[7:11],shine,max(.44,depth*.085))
    for i in range(38):
        n=rng.uniform(0,960); alt=rng.uniform(218,346); l=rng.uniform(5,95)
        line([(n,alt),(n+l,alt)],(139,178,205,rng.randrange(4,31)),rng.uniform(.35,1.2))
    # Layered city silhouettes frame the dueling platform.
    for layer in range(3):
        for _ in range(48-layer*9):
            a=rng.uniform(-55,1000); z=rng.uniform(6,58-layer*7)
            taper=abs(a-487)/487
            ht=rng.uniform(14,64)+(19+33*layer)*taper**1.4
            bot=365+layer*9+rng.uniform(-5,8); top=bot-ht
            col=[(28,41,64),(21,31,52),(13,22,39)][layer]
            pal=tuple(int(v+rng.uniform(-4,5)) for v in col)
            poly([(a,bot),(a,top+10),(a+z*.34,top),(a+z*.83,top),(a+z,top+8),(a+z,bot)],pal)
            line([(a+z*.34,top),(a+z*.83,top)],(112,139,165,45))
            if rng.random()<.47:
                pole=a+z*.52
                line([(pole,top),(pole,top-17)],(70,87,115,170))
                ellipse(pole,top-17,.9,.9,(255,120,109,178))
            for row in range(int(ht//10)):
                if rng.random()<.65:
                    xx=a+rng.uniform(2,z); yy=top+12+row*10
                    line([(xx,yy),(min(xx+rng.uniform(1,9),a+z),yy)],(111,187,218,rng.randrange(14,72)))
    for p in [
        [(-50,382),(-32,88),(21,60),(49,90),(49,197),(76,219),(78,297),(143,367)],
        [(33,377),(52,192),(83,184),(104,217),(107,272),(147,318),(179,380)],
        [(1000,379),(994,76),(938,91),(921,141),(907,149),(907,234),(865,267),(866,310),(812,369)],
        [(950,406),(942,197),(892,207),(881,259),(847,262),(829,308),(798,327),(778,392)],
    ]:
        poly(p,(10,17,30))
        line(p[:-1],(83,107,135,116),.8)
    for side in (-1,1):
        for i in range(14):
            x0=(i*9-7) if side==-1 else (967-i*8)
            y0=185+i*12+rng.uniform(-19,18)
            line([(x0,y0),(x0+side*rng.uniform(5,27),y0-2)],(131,184,206,rng.randrange(35,100)),.7)
    # Suspended deck, panel seams, and warning lights.
    for i in range(13):
        rx=45+i*73
        line([(rx,376),(rx+7,353)],(56,77,102,220),2)
        line([(rx+7,353),(rx+7,344)],(75,99,125,155),1)
    line([(21,356),(949,356)],(73,96,123,160),1.6)
    line([(38,363),(936,363)],(32,51,78,230),2)
    poly([(-70,493),(64,367),(896,367),(1030,493),(1000,540),(-50,540)],(15,23,40))
    poly([(-70,477),(64,367),(896,367),(1030,477)],(43,55,75))
    poly([(-70,477),(64,375),(896,375),(1030,477)],(38,49,68))
    poly([(-70,477),(102,410),(859,410),(1030,477)],(35,45,63))
    poly([(-70,477),(1030,477),(1030,492),(-70,492)],(18,29,49))
    line([(-40,478),(1000,478)],(119,149,169,155),1.5)
    line([(65,368),(896,368)],(123,160,185,187),1.1)
    for base in [87,164,240,320,398,480,562,640,720,796,873]:
        high=480+(base-480)*.84; low=480+(base-480)*1.41
        line([(high,370),(low,476)],(11,20,36,190),1.4)
        line([(high+1,370),(low+2,476)],(151,176,196,50),.7)
    for row in [384,409,448,466]:
        ext=(row-368)*1.2
        line([(64-ext,row),(896+ext,row)],(8,17,32,160),1.4)
        line([(65-ext,row+1),(896+ext,row+1)],(120,155,177,61),.7)
    for i in range(1600):
        yy=rng.uniform(371,476); ext=(yy-367)*1.13
        xx=rng.uniform(64-ext,896+ext)
        line([(xx,yy),(xx+rng.uniform(.6,4),yy)],(176,191,208,rng.randrange(4,24)),.55)
    for i in range(18):
        x0=i*61-23
        line([(x0,481),(x0+22,481)],(69,204,247,169),1.6)
        line([(x0,485),(x0+29,485)],(44,93,142,95),1)
    for i in range(19):
        xx=51+i*48
        ellipse(xx,374,1.3,.65,(216,221,198,150))
        line([(xx-9,460),(xx+13,460)],(199,163,108,68),1.1)
    for k in range(12):
        a=k*95-15
        poly([(a,540),(a+8,496),(a+73,496),(a+63,540)],(20,31,51))
        line([(a+8,496),(a+73,496)],(100,130,155,106),1)
    return stage

# Every pose specifies the head, shoulders, hips, elbows, hands, knees and feet.
# Coordinates are measured from the point on the deck underneath each figure.
POSES={
'guard':[(0,-127),(-4,-105),(-13,-55),(15,-83),(40,-86),(-5,-81),(32,-80),(17,-26),(29,0),(-34,-26),(-47,0)],
'ready':[(11,-115),(3,-94),(-14,-48),(24,-65),(50,-74),(-16,-71),(41,-70),(24,-24),(50,0),(-40,-27),(-64,0)],
'run1':[(30,-112),(19,-92),(-5,-49),(32,-75),(60,-67),(-8,-68),(-38,-79),(39,-37),(44,0),(-46,-47),(-73,-22)],
'run2':[(26,-116),(16,-96),(-9,-49),(40,-88),(29,-114),(-9,-67),(-32,-56),(25,-13),(19,0),(-41,-28),(-51,-43)],
'run3':[(31,-114),(20,-93),(-7,-47),(45,-107),(66,-119),(2,-72),(-28,-84),(39,-27),(73,-14),(-42,-8),(-58,-3)],
'strike':[(33,-112),(19,-91),(-14,-47),(38,-76),(70,-84),(19,-70),(62,-78),(31,-25),(48,0),(-41,-26),(-70,0)],
'high':[(12,-122),(5,-101),(-13,-50),(38,-91),(51,-117),(21,-78),(43,-114),(25,-23),(48,0),(-34,-24),(-61,0)],
'over':[(12,-114),(0,-95),(-19,-49),(-16,-121),(2,-144),(20,-114),(10,-140),(29,-24),(52,0),(-39,-22),(-66,0)],
'low':[(40,-77),(24,-63),(-16,-34),(46,-58),(73,-46),(7,-49),(64,-43),(25,-10),(60,0),(-42,-13),(-79,0)],
'slide':[(47,-62),(29,-50),(-18,-24),(48,-28),(67,-36),(14,-37),(-10,-60),(29,-7),(80,0),(-46,-3),(-80,0)],
'block':[(4,-116),(-2,-93),(-23,-48),(20,-77),(37,-98),(17,-70),(30,-90),(14,-23),(36,0),(-47,-20),(-69,0)],
'recoil':[(-24,-115),(-14,-95),(-9,-48),(7,-69),(44,-71),(-35,-71),(-55,-85),(19,-24),(46,-8),(-32,-24),(-55,0)],
'float':[(23,-122),(12,-102),(-10,-51),(44,-98),(61,-117),(5,-79),(-25,-60),(33,-32),(51,-58),(-44,-21),(-66,-39)],
'tuck':[(40,-105),(26,-87),(-11,-64),(38,-63),(18,-33),(51,-72),(35,-35),(34,-54),(48,-23),(-26,-34),(3,-17)],
'dive':[(41,-91),(24,-84),(-24,-60),(45,-59),(76,-47),(30,-64),(67,-49),(2,-31),(-12,-7),(-60,-58),(-83,-74)],
'force':[(12,-121),(2,-100),(-13,-49),(0,-74),(-26,-58),(35,-93),(69,-98),(21,-24),(40,0),(-39,-22),(-66,0)],
'crouch':[(12,-79),(2,-63),(-22,-31),(26,-43),(41,-61),(-9,-44),(33,-56),(14,-10),(42,0),(-46,-10),(-69,0)],
'kneel':[(24,-77),(14,-58),(-11,-38),(31,-36),(47,-32),(0,-37),(-16,-16),(24,-25),(46,0),(-36,-5),(-64,0)],
'end':[(0,-132),(-3,-110),(-10,-57),(10,-81),(26,-66),(-20,-77),(-23,-57),(9,-26),(25,0),(-26,-26),(-38,0)],
}

# time, x, floor y, pose, facing, blade angle in local space; optional body roll.
J=[
(0,240,420,'guard',1,-60),(.27,240,420,'ready',1,-57),(.55,241,420,'ready',1,-49),(.78,238,420,'low',1,-31),
(.96,270,420,'run1',1,-54),(1.09,315,420,'run2',1,-83),(1.23,360,420,'run3',1,-99),
(1.42,405,420,'over',1,18),(1.55,409,420,'recoil',1,-53),(1.68,400,420,'high',1,-111),
(1.83,407,420,'block',1,-25),(1.97,412,420,'ready',1,-72),(2.13,408,420,'low',1,-28),
(2.27,422,420,'strike',1,-43),(2.39,426,420,'high',1,-108),(2.49,427,420,'over',1,-100),
(2.63,409,420,'block',1,10),(2.76,397,420,'recoil',1,85),(2.94,391,420,'crouch',1,-64),
(3.12,411,416,'float',1,-93),(3.33,468,334,'float',1,-113,-15),(3.52,520,298,'tuck',1,32,38),
(3.67,557,322,'tuck',-1,-22,-20),(3.85,603,388,'dive',-1,39,-15),
(4.11,604,420,'high',-1,-132),(4.26,591,420,'strike',-1,-51),(4.41,587,420,'block',-1,25),
(4.56,598,420,'over',-1,-105),(4.73,572,420,'low',-1,13),(4.92,560,420,'ready',-1,-35),
(5.13,553,420,'high',-1,-94),(5.38,540,420,'block',-1,2),(5.61,545,420,'ready',-1,-9),
(5.76,541,420,'block',-1,-10),(5.92,574,406,'recoil',-1,-72),
(6.19,668,405,'recoil',-1,34),(6.37,702,420,'slide',-1,10),(6.61,705,420,'crouch',-1,-61),
(6.84,692,420,'block',-1,-68),(7.17,686,420,'block',-1,-66),(7.42,669,420,'low',-1,-72),
(7.61,628,420,'run3',-1,-53),(7.79,591,420,'run1',-1,-33),(7.99,554,420,'run2',-1,-78),
(8.17,522,420,'strike',-1,-13),(8.38,550,420,'recoil',-1,-75),(8.62,564,420,'ready',-1,-30),
(8.84,562,420,'high',-1,-93),(9.05,561,420,'block',-1,-74),(9.25,536,420,'low',-1,-111),
(9.49,486,420,'slide',-1,-132),(9.73,431,420,'slide',-1,145),(9.91,386,420,'crouch',-1,85),
(10.12,360,420,'low',1,153),(10.34,347,420,'ready',1,-134),
(10.55,369,420,'run1',1,-108),(10.75,402,420,'run3',1,-94),(10.93,417,420,'strike',1,-40),
(11.05,422,420,'low',1,24),(11.20,425,420,'high',1,-91),(11.34,413,420,'block',1,-9),
(11.47,422,420,'over',1,-120),(11.61,416,420,'low',1,-5),(11.74,416,420,'strike',1,51),
(11.93,397,420,'ready',1,-10),(12.32,387,420,'ready',1,-24),(12.53,404,420,'over',1,-124),
(12.69,437,420,'strike',1,-25),(12.81,459,420,'low',1,49),(13.02,477,420,'low',1,66),
(13.36,458,420,'crouch',1,46),(13.73,436,420,'end',1,48),(14.14,431,420,'end',1,54),(15,431,420,'end',1,55),
]
S=[
(0,723,420,'end',-1,40),(.20,723,420,'end',-1,25),(.47,724,420,'ready',-1,-18),(.77,725,420,'low',-1,-23),
(.95,693,420,'run3',-1,-59),(1.11,645,420,'run1',-1,-71),(1.24,605,420,'run2',-1,-107),
(1.42,555,420,'high',-1,-6),(1.55,555,420,'recoil',-1,-60),(1.67,551,420,'over',-1,-117),
(1.83,547,420,'strike',-1,-38),(1.97,546,420,'low',-1,52),(2.13,555,420,'high',-1,-93),
(2.27,555,420,'block',-1,-40),(2.39,556,420,'recoil',-1,-66),(2.49,555,420,'over',-1,-86),
(2.63,547,420,'strike',-1,14),(2.76,534,420,'low',-1,55),(2.94,527,420,'ready',-1,-15),
(3.12,507,420,'strike',-1,21),(3.33,484,420,'low',-1,60),(3.52,456,420,'crouch',-1,-66),
(3.69,456,420,'high',1,-138),(3.88,464,395,'float',1,-69),(4.07,448,380,'float',1,-39),
(4.26,454,400,'dive',1,-13),(4.41,436,420,'recoil',1,53),(4.56,430,420,'ready',1,-79),
(4.73,443,420,'crouch',1,-4),(4.92,422,420,'recoil',1,-67),(5.13,423,420,'run3',1,-79),
(5.38,431,420,'block',1,-12),(5.61,426,420,'ready',1,3),(5.76,430,420,'block',1,5),
(5.92,384,413,'recoil',1,-126),(6.19,296,408,'recoil',1,-176),(6.37,252,420,'crouch',1,39),
(6.64,270,420,'force',1,35),(6.85,290,420,'force',1,47),(7.16,299,420,'force',1,56),
(7.42,308,420,'force',1,64),(7.68,331,420,'force',1,68),(7.91,351,420,'force',1,56),
(8.17,382,420,'block',1,-18),(8.38,393,420,'recoil',1,-122),(8.62,395,420,'ready',1,-36),
(8.84,408,409,'float',1,-100),(9.08,455,338,'float',1,-123),(9.30,505,297,'tuck',1,-82,29),
(9.50,556,324,'dive',1,48,22),(9.71,604,378,'dive',1,100,29),(9.84,622,420,'low',1,108),
(9.99,646,420,'crouch',1,113),(10.17,642,420,'recoil',-1,-135),(10.36,628,420,'ready',-1,-59),
(10.55,604,420,'run3',-1,-111),(10.75,574,420,'run2',-1,-85),(10.93,554,420,'block',-1,-45),
(11.05,553,420,'recoil',-1,-96),(11.20,554,420,'over',-1,-99),(11.34,551,420,'strike',-1,-25),
(11.47,552,420,'high',-1,-107),(11.61,544,420,'block',-1,5),(11.74,550,420,'low',-1,50),
(11.93,572,420,'ready',-1,20),(12.32,578,420,'ready',-1,13),(12.53,565,420,'high',-1,-115),
(12.69,552,420,'block',-1,-33),(12.81,570,419,'recoil',-1,-153),(13.02,601,420,'recoil',-1,-164),
(13.33,618,420,'kneel',-1,-45),(13.68,620,420,'kneel',-1,-30),(15,620,420,'kneel',-1,-28),
]

# Impacts drive the characters, score, camera shake, and debris from a shared clock.
HITS=[
(1.42,489,286,1.00),(1.83,487,307,.71),(2.27,490,303,.70),(2.63,491,323,.92),
(4.26,525,312,.86),(4.73,519,371,1.0),(5.38,486,309,.68),(5.80,485,311,1.38),
(8.17,466,312,1.05),(9.84,676,416,1.13),(10.93,490,298,.88),
(11.34,483,308,.72),(11.61,488,331,.77),(12.69,518,307,1.6),
]
LOCK=(5.38,5.80)
CAM=[
(0,.73,476,278,1.02,480,278,1.13),(.73,1.37,470,301,1.17,490,302,1.32),
(1.37,2.05,486,309,1.75,483,312,1.59),(2.05,2.81,482,319,1.38,489,315,1.57),
(2.81,3.98,494,284,1.13,511,251,1.29),(3.98,4.93,515,299,1.50,506,331,1.54),
(4.93,5.87,483,314,1.38,486,309,2.30),(5.87,6.62,482,289,1.07,485,289,1.07),
(6.62,7.50,488,316,1.21,493,308,1.30),(7.50,8.37,522,323,1.61,474,317,1.79),
(8.37,9.02,479,307,1.35,480,306,1.34),(9.02,9.83,502,261,1.36,523,293,1.49),
(9.83,10.49,484,328,1.20,489,315,1.14),(10.49,11.05,490,315,1.19,489,312,1.45),
(11.05,11.78,485,315,1.77,488,317,1.87),(11.78,12.56,487,316,1.32,486,315,1.70),
(12.56,12.89,502,310,1.89,510,314,1.73),(12.89,13.65,536,307,1.44,536,303,1.34),
(13.65,15.01,528,292,1.14,519,286,1.08),
]

def timeline(keys,t):
    ix=max(0,min(len(keys)-2,bisect_right([k[0] for k in keys],t)-1))
    a,b=keys[ix:ix+2]
    u=clamp((t-a[0])/(b[0]-a[0]))
    v=lerp(u,smooth(u),.62)
    x,y=blend(a[1:3],b[1:3],v)
    facing=a[4] if a[4]==b[4] or u<.56 else b[4]
    fo=lerp(a[4],b[4],smooth(u)) if a[4]!=b[4] else facing
    tilt=m.radians(lerp(a[6] if len(a)>6 else 0,b[6] if len(b)>6 else 0,v))
    si,co=m.sin(tilt),m.cos(tilt)
    pts=[]
    for aa,bb in zip(POSES[a[3]],POSES[b[3]]):
        q,r=blend(aa,bb,v)
        q*=fo if abs(fo)>.19 else .19*facing
        if tilt:
            d=r+59
            q,r=q*co-d*si,q*si+d*co-59
        pts.append((x+q,y+r))
    ang=a[5]+((b[5]-a[5]+180)%360-180)*v
    angle=m.radians(ang)
    vec=m.cos(angle)*facing,m.sin(angle)
    speed=(b[1]-a[1])/(b[0]-a[0])*(.62+.38*m.sin(m.pi*u))
    return pts,vec,(x,y),speed,facing

def fighter(keys,t):
    points,direction,base,speed,facing=timeline(keys,t)
    hand=points[4]
    for at,px,py,power in HITS:
        if at==9.84 and keys is J: continue
        sustain=.36 if at==5.38 else .075
        dt=t-at
        if -.067<dt<sustain:
            u=smooth(1+dt/.067) if dt<0 else 1-smooth(dt/sustain)
            aim=(px-hand[0],py-hand[1])
            dist=m.hypot(*aim)
            if dist>1:
                ax=m.atan2(aim[1],aim[0]); ba=m.atan2(direction[1],direction[0])
                angle=ba+((ax-ba+m.pi)%TAU-m.pi)*u
                direction=(m.cos(angle),m.sin(angle))
    if keys is J:
        size=125*smooth((t-.28)/.19)*(1-smooth((t-14.29)/.18))
    else:
        size=125*smooth((t-.12)/.17)
        if 9.61<t<10.02 and direction[1]>.13:
            ground_limit=max(24,(419-hand[1])/direction[1]-10)
            strength=smooth((t-9.61)/.08)*(1-smooth((t-9.92)/.10))
            size=lerp(size,min(size,ground_limit),strength)
    return points,direction,base,speed,facing,size

def blade(f):
    hand=f[0][4]; vx,vy=f[1]
    return (hand[0]+vx*10,hand[1]+vy*10),(hand[0]+vx*(10+f[5]),hand[1]+vy*(10+f[5]))

STAGE=make_stage()
rain=[(rng.uniform(-300,1360),rng.uniform(-200,680),rng.uniform(40,177),rng.uniform(3,16),rng.uniform(.24,1),rng.randint(30,117)) for _ in range(240)]
sparks=[]
for oi,(at,x,y,power) in enumerate(HITS):
    for i in range(int(56+36*power)):
        direction=rng.uniform(-m.pi,m.pi)
        speed=rng.uniform(42,575)*(.55+.45*power)
        sparks.append((at,x,y,power,direction,speed,rng.uniform(.15,.63),rng.uniform(.58,2.3),rng.random()))
rock=[(rng.uniform(-m.pi,0),rng.uniform(85,360),rng.uniform(.6,1.9),rng.uniform(1,6),rng.uniform(0,6.3)) for _ in range(48)]
embers=[(rng.uniform(50,860),rng.uniform(295,460),rng.uniform(6,27),rng.uniform(.4,2),rng.uniform(0,TAU)) for _ in range(56)]

yy,xx=np.mgrid[-1:1:H*1j,-1:1:W*1j]
vignette=Image.fromarray(np.uint8(255*np.clip(1-.18*(xx*xx+yy*yy)**1.6,0.55,1)),'L').convert('RGB')
del xx,yy

def draw_frame(frame):
    t=frame/FPS
    _,_,x0,y0,z0,x1,y1,z1=cam=next(c for c in CAM if c[0]<=t<c[1])
    u=smooth((t-cam[0])/(cam[1]-cam[0]))
    cx,cy=blend((x0,y0),(x1,y1),u)
    zoom=lerp(z0,z1,u)
    hit_glow=0
    for at,x,y,power in HITS:
        dt=t-at
        if 0<=dt<.28:
            j=power*m.exp(-dt*17)
            cx+=m.sin(dt*147+at*5)*j*10
            cy+=m.cos(dt*114+at*7)*j*6
            zoom+=j*.030
            hit_glow=max(hit_glow,j)
    base=zoom*W/960
    u0=W/2-cx*base; v0=H/2-cy*base
    stage_w,stage_h=STAGE.size
    im=STAGE.transform((W,H),Image.Transform.AFFINE,(stage_w/960/base,0,-u0*stage_w/960/base,0,stage_h/540/base,-v0*stage_h/540/base),Image.Resampling.BILINEAR,fillcolor=(9,14,25))
    d=ImageDraw.Draw(im,'RGBA')
    blur=Image.new('RGB',(W//3,H//3))
    g=ImageDraw.Draw(blur)
    def screen(p): return (p[0]*base+u0,p[1]*base+v0)
    def coords(pts): return [screen(p) for p in pts]
    def line(pts,c,w=1,draw=d):
        draw.line(coords(pts),fill=c,width=max(1,round(w*base)),joint='curve')
    def poly(pts,c,draw=d): draw.polygon(coords(pts),fill=c)
    def ellipse(p,rx,ry,c,draw=d):
        a,b=p
        draw.ellipse(coords([(a-rx,b-ry),(a+rx,b+ry)]),fill=c)
    def capsule(a,b,c,w,draw=d):
        line([a,b],c,w,draw)
        ellipse(a,w/2,w/2,c,draw)
        ellipse(b,w/2,w/2,c,draw)
    def bloom(pts,c,w=3):
        g.line([(a/3,b/3) for a,b in coords(pts)],fill=c,width=max(1,round(w*base/3)),joint='curve')
    def bdot(p,r,c,ry=None):
        a,b=screen(p)
        rx=r*base; ry=(r if ry is None else ry)*base
        g.ellipse(((a-rx)/3,(b-ry)/3,(a+rx)/3,(b+ry)/3),fill=c)
    def arc(p,r,ya,from_a,to_a,c,w):
        x,y=p
        d.arc(coords([(x-r,y-r*ya),(x+r,y+r*ya)]),from_a,to_a,fill=c,width=max(1,round(w*base)))
    def rain_layer(front):
        for x,y,v,l,depth,alpha in rain:
            if (depth>=.62)!=front: continue
            dy=((y+t*v+200)%771)-200
            dx=((x-t*v*.21+300)%1380)-230
            line([(dx,dy),(dx-l*.29,dy+l)],(159,196,222,int(alpha*(.79 if front else .53))),depth*.95)
    rain_layer(False)

    jt=fighter(J,t)
    st=fighter(S,t)
    def figure(f,c,sith):
        return draw_fighter(f,c,sith,t,poly,line,ellipse,bloom)

    def saber(f,c,history=None,throw=False):
        hand,vec=f[0][4],f[1]
        a,b=blade(f)
        if f[5]>2 and history:
            blade_edges=[(a,b)]
            for delta in [.024,.049,.079,.112,.145]:
                prior=fighter(history,max(0,t-delta))
                if prior[5]>3 and abs(prior[0][4][0]-hand[0])<102:
                    blade_edges.append(blade(prior))
            for i in range(len(blade_edges)-1,0,-1):
                a0,b0=blade_edges[i]; a1,b1=blade_edges[i-1]
                if m.dist(b0,b1)>3:
                    density=1-i/7
                    q0=blend(a0,b0,.27+i*.079); q1=blend(a1,b1,.27+i*.079)
                    poly([q0,b0,b1,q1],(*c,int(96*density)))
                    line([b0,b1],(*c,int(145*density)),1.1)
                    bloom([b0,b1],shade(c,.74*density),4)
        gripA=pos(hand,(-vec[0]*14,-vec[1]*14))
        gripB=pos(hand,(vec[0]*9,vec[1]*9))
        capsule(gripA,gripB,(108,130,150),5.5 if not throw else 6.2)
        capsule(gripA,gripB,(37,47,65),3.3)
        line([pos(gripB,(-vec[0]*2,-vec[1]*2)),gripB],(193,213,228),3.4)
        if f[5]>1:
            bloom([a,b],c,10)
            line([a,b],(*c,78),16)
            capsule(a,b,(*c,132),10.1)
            capsule(a,b,mix(c,(230,250,255),.35),6.0)
            capsule(a,b,mix(c,(252,253,255),.89),3.4)
            bdot(a,6,shade(c,.85))

    # Light trails and debris inside the scene.
    for x,y,basev,r,phase in embers:
        px=x+m.sin(t*1.3+phase)*13-t*basev*.36
        py=455-((455-y+t*basev)%164)
        av=int(23+70*(.5+.5*m.sin(t*3.8+phase)))
        ellipse((px,py),r*.68,r*.64,(*GOLD,av))
    if 5.80<=t<6.46:
        dt=t-5.80
        for i in range(4):
            tau=dt-i*.026
            if tau<=0: continue
            av=int(141*m.exp(-tau*6.3))
            arc((485,313),tau*(491+i*30)+7,.69,0,359,(155,220,253,av),max(.3,2.1-tau*2))
        arc((485,420),dt*565+10,.13,0,359,(128,207,248,int(190*m.exp(-dt*4))),1.7)
    if 9.84<=t<10.45:
        dt=t-9.84
        arc((676,418),dt*335+4,.14,0,359,(*RED,int(210*m.exp(-dt*5.8))),1.4)
        for angle,speed,life,sz,spin in rock:
            px=676+m.cos(angle)*speed*dt
            py=min(422,418+m.sin(angle)*speed*dt+350*dt*dt)
            rr=sz*(1-.78*dt)
            poly([(px+m.cos(dt*spin+j*TAU/4)*rr,py+m.sin(dt*spin+j*TAU/4)*rr) for j in range(4)],(102,70,84))
            ellipse((px,py),rr*.30,rr*.30,(*GOLD,111))

    if t>=9.84:
        frac=clamp((t-9.84)/.58)
        crack=([(676,417),(665,427),(673,436),(651,445),(654,453),(633,462)],[(676,417),(691,412),(700,418),(725,409),(739,415)],[(676,417),(664,410),(663,401),(650,397),(648,389)])
        for pts in crack:
            if frac>.06:
                qty=1+int(frac*(len(pts)-1))
                shown=pts[:qty]
                if len(shown)>1:
                    line(shown,(12,13,23,235),2.6)
                    line([pos(p,(0,.9)) for p in shown],(*RED,int(140*m.exp(-(t-9.84)*.52))),.9)
                    if t<10.32: bloom(shown,shade(RED,.37),2.3)
    for at,x,y,side in [(3.87,608,419,1),(6.24,683,419,1),(6.26,272,420,-1),(9.46,456,420,-1),(9.84,644,418,1)]:
        dt=t-at
        if 0<dt<.64:
            dr=random.Random(int(at*100))
            for i in range(36):
                delay=dr.uniform(0,.22)
                life=dr.uniform(.22,.64)
                size=dr.uniform(1,9)
                vx=dr.uniform(40,190)*side
                vy=dr.uniform(-68,-12)
                a=dt-delay
                if not 0<a<life: continue
                px=x+vx*a+dr.uniform(-21,21)
                py=y+vy*a+34*a*a
                alpha=int((1-a/life)*15)
                ellipse((px,py),size*(.6+a*3.2),size*(.32+a*1.0),(119,146,165,alpha))
                if i%7==0:
                    line([(px,py),(px-vx*.032,py+2)],(248,178,116,min(174,alpha*9)),.86)

    figure(st,RED,True)
    figure(jt,BLUE,False)
    if t<12.72: saber(st,RED,S)
    saber(jt,BLUE,J)

    if 12.72<=t<13.30:
        dt=t-12.72
        h=(st[0][4] if dt<.036 else (514+675*dt,305-434*dt+279*dt*dt))
        a=-.25+dt*26
        saber(([None,None,None,None,h],(m.cos(a),m.sin(a)),None,0,1,125*(1-smooth((dt-.27)/.15))),RED,throw=True)
        bloom([h,pos(h,(-36,14))],shade(RED,.44*(1-dt/.58)),2.6)

    if 6.73<=t<8.17:
        light=clamp((t-6.73)/.12)*clamp((8.17-t)/.18)
        start=st[0][6]
        aa,bb=blade(jt)
        for beam in range(7):
            rb=random.Random(frame*699+beam*2634+33)
            end=blend(aa,bb,rb.uniform(.22,.79))
            pts=[start]; segment=14
            phase=rb.randrange(6)
            for i in range(1,segment):
                u=i/segment
                wiggle=m.sin(u*m.pi)*(rb.uniform(-1,1)*(12+beam*3)+m.sin(u*36+phase)*10)
                px,py=blend(start,end,u)
                pts.append((px+rb.uniform(-7,7),py+wiggle))
            pts.append(end)
            line(pts,(*RED,int(light*(142 if beam<3 else 83))),1.8 if beam<3 else .82)
            if beam<3:
                line(pts,(255,191,219,int(225*light)),.66)
                bloom(pts,shade(RED,light*.67),3.6)
            if rb.random()<.83:
                root=pts[rb.randrange(3,segment-2)]
                fork=[root,pos(root,(rb.uniform(-11,27),rb.uniform(-20,19))),pos(root,(rb.uniform(24,49),rb.uniform(-32,29)))]
                line(fork,(*RED,int(143*light)),.9)
        ellipse(start,3.2,3.2,(255,224,231,int(230*light)))
        bdot(start,12,shade(RED,light))
        bdot(aa,11,shade(BLUE,light*.7))

    # Continuous spraying sparks while the blades are locked.
    if LOCK[0]<=t<=LOCK[1]+.05:
        rb=random.Random(78)
        for i in range(93):
            time=5.36+rb.random()*.48
            a=rb.random()*TAU
            speed=rb.uniform(42,271)
            dt=t-time
            if 0<dt<.23:
                px,py=485+m.cos(a)*speed*dt,309+m.sin(a)*speed*dt+110*dt*dt
                length=rb.uniform(1,6)
                line([(px,py),(px-m.cos(a)*length,py-m.sin(a)*length)],(255,214,161,int(227*(1-dt/.23))),1.3)
        bdot((485,309),8+3*m.sin(t*63),GOLD)

    for at,x,y,power,angle,speed,life,width,color in sparks:
        age=t-at
        if not 0<=age<life: continue
        si,co=m.sin(angle),m.cos(angle)
        dist=speed*age*(1-age*.60)
        px,py=x+co*dist,y+si*dist+280*age*age
        if py>423: py=423-(py-423)*.30
        length=min(28,speed*(.027+width*.010))*(1-age/life)**.5
        col=(255,202,144) if color<.59 else ((124,224,255) if color<.82 else (255,106,140))
        pts=[(px,py),(px-co*length,py-si*length-90*age*age)]
        line(pts,(*col,int(255*(1-age/life)**.45)),width)
        if age<.20 and width>1: bloom(pts,shade(col,.62*(1-age/.22)),width*1.7)

    for at,x,y,power in HITS:
        age=t-at
        if -.012<=age<.135:
            p=power*m.exp(-max(age,0)*25)
            bdot((x,y),max(4,12*p),shade(GOLD,min(1,p)))
            r=max(1,14*p)
            ellipse((x,y),r,r,(255,236,207,int(184*min(p,1))))
            ellipse((x,y),r*.59,r*.56,(255,248,230,int(248*min(p,1))))
            line([(x-85*p,y),(x+85*p,y)],(255,231,206,int(180*min(p,1))),max(.5,2*p))
            bloom([(x-85*p,y),(x+85*p,y)],shade(GOLD,min(1,p)),4)
            if at==12.69:
                a=(x-140*p,y+35*p); b=(x+119*p,y-29*p)
                line([a,b],(209,240,255,int(180*min(p,1))),2.8)
                bloom([a,b],shade(BLUE,min(1,p)),8)
    # Draw directional speed lines only during acceleration and frame the impact around the contact point.
    rush=max((max(0,1-abs(t-at)/duration)*amount for at,duration,amount in [
      (1.14,.26,.75),(3.37,.31,.80),(5.96,.22,.63),(7.85,.33,.78),
      (9.56,.27,.85),(10.70,.23,.78),(12.60,.16,1.0)]),default=0)
    if rush>.025:
        rr=random.Random(2217)
        center=(cx+12,cy+7)
        for i in range(56):
            angle=rr.uniform(0,TAU)
            distance=rr.uniform(135,385)/zoom+((t*210+i*17)%72)/zoom
            direction=(m.cos(angle),m.sin(angle))
            ln=rr.uniform(8,88)*rush/zoom
            near=pos(center,(direction[0]*distance,direction[1]*distance))
            tip=pos(near,(direction[0]*ln,direction[1]*ln))
            color=(216,216,252) if i%4 else (252,179,211)
            line([near,tip],(*color,int(rr.uniform(22,108)*rush)),rr.uniform(.44,1.45))
    rain_layer(True)
    hot=blur.filter(ImageFilter.GaussianBlur(2.8)).resize((W,H),Image.Resampling.BILINEAR)
    low=blur.filter(ImageFilter.GaussianBlur(10.5)).resize((W,H),Image.Resampling.BILINEAR)
    im=ImageChops.add(ImageChops.add(im,hot,scale=1),ImageEnhance.Brightness(low).enhance(1.38))
    im=ImageChops.multiply(im,vignette)
    if hit_glow>.25:
        tint=(185,221,248) if t<5.98 or t>=12.69 else (241,194,207)
        im=Image.blend(im,Image.new('RGB',(W,H),tint),min(.16,hit_glow*hit_glow*.051))
    if frame in (43,174,381):
        # Single-frame ink accents are keyed to the three biggest contacts.
        latest=min(HITS,key=lambda h:abs(t-h[0]))
        focal=screen(latest[1:3])
        overlay=Image.new('RGB',(W,H),(231,237,245))
        k=ImageDraw.Draw(overlay)
        x,y=focal
        rr=random.Random(1005+frame)
        for n in range(58):
            a=(n+rr.random()*.45)*TAU/58
            r=rr.uniform(48,475)
            e=rr.uniform(640,1140)
            theta=rr.uniform(.0015,.015)
            pts=[(x+m.cos(a)*r,y+m.sin(a)*r),
                 (x+m.cos(a-theta)*e,y+m.sin(a-theta)*e),
                 (x+m.cos(a+theta)*e,y+m.sin(a+theta)*e)]
            k.polygon(pts,fill=(12,14,32) if n%5 else (84,96,139))
        k.ellipse((x-37,y-26,x+37,y+26),fill=(255,250,227))
        im=Image.blend(im,overlay,.44 if frame!=381 else .59)
    if 11.99<=t<12.383:
        im=portrait_insert(im,t,W,H)
    if t<.18: im=ImageEnhance.Brightness(im).enhance(lerp(.45,1,smooth(t/.18)))
    if t>13.89:
        d=ImageDraw.Draw(im,'RGBA')
        alpha=int(249*smooth((t-13.89)/.32))
        f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-ExtraLight.ttf',50)
        s=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',14)
        def spaced(word,font,space,cy,col):
            sizes=[d.textlength(char,font=font) for char in word]
            left=(W-sum(sizes)-space*(len(word)-1))/2
            for char,size in zip(word,sizes):
                d.text((left,cy),char,font=font,fill=col,anchor='lt')
                left+=size+space
        spaced('ECLIPSE',f,13,88,(231,245,254,alpha))
        d.line([(W/2-15,157),(W/2+15,157)],fill=(162,206,226,alpha),width=1)
        spaced('SITH  /  JEDI',s,4,177,(190,217,238,int(alpha*.91)))
    if t>14.76:
        im=ImageEnhance.Brightness(im).enhance(1-.76*smooth((t-14.76)/.24))
    return im

if __name__=='__main__':
    if sys.argv[1]=='preview':
        ts=[.38,1.42,2.27,3.46,4.26,4.73,5.53,5.87,7.16,8.17,9.49,9.87,10.93,11.61,12.16,12.69,13.02,14.43]
        sheet=Image.new('RGB',(1080,6*203+6),(7,10,18))
        for i,t in enumerate(ts):
            piece=draw_frame(round(t*FPS)); piece.thumbnail((354,198))
            sheet.paste(piece,(6+i%3*358,6+i//3*203))
        sheet.save(Path(__file__).with_name("anime_preview.jpg"),quality=92)
    else:
        from multiprocessing import Pool
        from subprocess import Popen, PIPE
        target=sys.argv[1]
        def render(n):
            return draw_frame(n).tobytes()
        cmd=['ffmpeg','-loglevel','warning','-nostdin','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(Path(__file__).with_name("sound.wav")),'-c:v','libx264','-preset','fast','-crf','17','-threads','3','-vf','scale=1920:1080:flags=lanczos,format=yuv420p','-c:a','aac','-b:a','256k','-movflags','+faststart','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',target]
        with Pool(4) as workers, Popen(cmd,stdin=PIPE) as encoder:
            for i,data in enumerate(workers.imap(render,range(15*FPS),chunksize=2)):
                encoder.stdin.write(data)
                if i%75==0:
                    print(f'{i}/{15*FPS} frames',flush=True)
            encoder.stdin.close()
            if encoder.wait()!=0:
                raise SystemExit('Encoding failed')
