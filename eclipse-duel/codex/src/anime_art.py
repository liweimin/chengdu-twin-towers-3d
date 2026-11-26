from math import hypot, sin, cos, pi
from PIL import Image, ImageDraw
import random

INK=(17,17,35)

def add(a,b): return (a[0]+b[0],a[1]+b[1])
def sub(a,b): return (a[0]-b[0],a[1]-b[1])
def mul(p,s): return (p[0]*s,p[1]*s)
def between(a,b,s): return add(a,mul(sub(b,a),s))
def unit(a):
    d=max(.01,hypot(*a))
    return mul(a,1/d)
def normal(v): return (-v[1],v[0])
def paint(a,b,s): return tuple(round(x+(y-x)*s) for x,y in zip(a,b))
def offset(origin,vec,r): return add(origin,mul(vec,r))

# Separate colors for each plane make the folds follow the body during the action.
JEDI={
'cloth':(206,222,222),'bright':(247,248,228),'shade':(111,151,169),
'dark':(48,68,97),'trouser':(56,79,112),'trouser_light':(98,137,157),
'boot':(37,47,68),'trim':(82,210,227),'trim_dark':(30,95,139),
'face':(251,211,176),'skin_shade':(184,127,120),'face_light':(255,230,193),
'hair':(32,52,84),'hair_dark':(24,30,56),'hair_light':(75,125,153),
'eye':(15,134,182)
}
SITH={
'cloth':(78,61,83),'bright':(128,84,108),'shade':(42,33,56),
'dark':(33,26,47),'trouser':(45,37,60),'trouser_light':(87,64,91),
'boot':(35,29,48),'trim':(251,106,117),'trim_dark':(117,44,71),
'face':(228,199,192),'skin_shade':(160,103,125),'face_light':(251,226,214),
'hair':(222,213,219),'hair_dark':(123,105,139),'hair_light':(253,228,231),
'eye':(197,34,72)
}

def draw_head(hd,sh,face,sith,t,poly,line,scale=1,eye_open=1):
    p=SITH if sith else JEDI
    drift=(hd[0]-sh[0])*face
    lean=max(-.33,min(.36,drift*.025))
    def xy(q):
        a,b=q
        return add(hd,(face*(a-b*lean)*scale,(b+a*lean)*scale))
    def shape(pts,col,stroke=1.15):
        actual=[xy(v) for v in pts]
        poly(actual,col)
        if stroke: line(actual+actual[:1],INK,stroke*scale)
    def detail(pts,col,width=1):
        line([xy(v) for v in pts],col,width*scale)
    if sith:
        shape([(-17,1),(-18,-9),(-11,-19),(5,-22),(14,-17),(21,-10),(16,-8),(19,-2),
               (11,-1),(15,5),(4,5),(7,19),(-7,15),(-15,19),(-13,12),(-22,15)],
              p['hair_dark'])
    else:
        shape([(-20,5),(-16,-2),(-19,-13),(-11,-18),(-15,-21),(-3,-20),(1,-23),
               (12,-20),(19,-13),(16,-5),(20,3),(12,3),(12,11),(4,15),(-7,13),(-18,15)],
              p['hair_dark'])
    shape([(-11,-7),(-6,-15),(7,-14),(13,-9),(13,-4),(18,2),(14,4),(14,8),(13,12),
           (8,17),(2,18),(-3,15),(-10,12),(-15,5),(-14,-1)],p['face'])
    shape([(-12,-6),(-5,-13),(-2,-7),(-4,0),(-3,5),(2,11),(7,14),(12,13),(8,17),
           (2,18),(-3,15),(-10,12),(-15,5),(-14,-1)],p['skin_shade'],0)
    shape([(-5,1),(0,-4),(6,-8),(12,-8),(12,-3),(15,2),(12,2),(11,0),
           (7,-1),(4,1),(2,5)],p['face_light'],0)
    shape([(-11,0),(-7,-1),(-6,1),(-7,6),(-10,7),(-12,4)],p['face'],.63)
    detail([(-10,1),(-8,1),(-9,4)],p['skin_shade'],.8)
    blink=any(abs(t-t0)<.038 for t0 in ([.19,6.61,13.80] if sith else [.54,4.99,13.76]))
    if not blink and eye_open>.35:
        shape([(1,-1),(7,-3),(12,-2),(10,0),(7,2),(4,1)],(254,241,225),.61)
        shape([(7,-2.9),(10,-2.4),(10,.3),(8,1.6),(7.1,.6)],p['eye'],0)
        detail([(9,-2.4),(9,0.55)],INK,.83)
        detail([(9.9,-1.9),(10.2,-1.4)],(255,251,234),.64)
    else:
        detail([(1,0),(7,-1),(12,-1)],INK,.89)
    detail([(1,-4),(5,-5),(11,-4.9)],INK,1.25)
    detail([(10,8),(13,7.9)],(105,68,90),.87)
    if sith:
        detail([(6,2.9),(4.2,4.7),(3.6,7.2)],(151,71,107),.72)
        shape([(-22,15),(-18,4),(-17,-7),(-14,-16),(-8,-18),(-2,-24),(5,-21),(14,-19),
               (21,-12),(17,-11),(22,-4),(16,-5),(15,-2),(10,-8),(7,-9),(4,-5),(6,-13),
               (-2,-7),(-8,-2),(-8,-8),(-11,1),(-12,-2),(-16,6),(-17,12)],p['hair'])
        shape([(-15,-9),(-10,-17),(-3,-19),(-1,-22),(4,-20),(13,-18),(18,-13),
               (12,-15),(3,-15),(-3,-11),(-7,-11),(-13,-5)],p['hair_light'],0)
        detail([(-14,0),(-12,-10),(-6,-15)],p['hair_dark'],1)
        detail([(1,-16),(-2,-11),(-7,-7)],p['hair_dark'],.85)
    else:
        shape([(-19,4),(-17,-4),(-20,-12),(-11,-15),(-14,-21),(-1,-19),(2,-23),
               (9,-20),(14,-19),(21,-12),(18,-11),(23,-7),(16,-6),(16,-1),(12,-4),
               (11,-10),(8,-12),(7,-7),(0,-1),(1,-9),(-5,-6),(-8,0),(-9,-5),
               (-13,3),(-17,9)],p['hair'])
        shape([(-18,-11),(-10,-14),(-11,-17),(-2,-15),(3,-20),(9,-18),(15,-16),
               (18,-13),(10,-14),(3,-15),(-2,-11),(-8,-11),(-13,-8)],p['hair_light'],0)
        detail([(-11,-4),(-8,-10),(-3,-14)],p['hair_light'],.9)
        detail([(5,-14),(4,-10),(1,-6)],p['hair_dark'],.9)
        detail([(-14,-10),(-9,-11)],p['trim_dark'],.8)

def draw_fighter(f,c,sith,t,poly,line,ellipse,bloom):
    points,vec,(x,y),speed,face,size=f
    hd,sh,hip,e,h,eb,hb,k,ft,kb,fb=points
    p=SITH if sith else JEDI
    trim=p['trim']
    stroke=INK
    light=paint(p['bright'],c,.35 if size>4 else .09)
    def shape(pts,col,width=1.45,edge=stroke):
        poly(pts,col)
        if width: line(pts+[pts[0]],edge,width)
    def side(a,b,dist): return offset(a,normal(unit(sub(b,a))),dist)
    def strip(a,b,aw,bw):
        return [side(a,b,aw),side(b,a,-bw),side(b,a,bw),side(a,b,-aw)]
    ground=max(0,min(1,1-(420-y)/174))
    ellipse((x+speed*.011,422),43+abs(speed)*.024,5.8,(4,8,19,round(129*ground)))
    if size>7:
        ellipse((x,420),69,8,(*c,round(23*ground)))
        bloom([(x-51,423),(x+47,423)],tuple(round(v*.16*ground) for v in c),4)
    axis=unit(sub(hip,sh))
    across=normal(axis)
    if face*across[0]<0: across=mul(across,-1)
    def torso(v):
        a,b=v
        return add(sh,add(mul(across,a),mul(axis,b)))
    body_len=hypot(*sub(hip,sh))
    def cloth(pts,col,s=1.45): shape([torso(v) for v in pts],col,s)
    def crease(pts,col,s=1): line([torso(v) for v in pts],col,s)

    # The cape and sash follow the trajectory a fraction of a beat behind the fighter.
    if sith:
        v=sin(t*12)
        dst=(hip[0]-face*(66+5*v)-speed*.09,hip[1]+56+v*7-min(58,abs(speed)*.10))
        a=torso((-14,-5)); b=torso((9,7))
        mid1=add(between(a,dst,.47),(-face*22,-7))
        mid2=add(between(a,dst,.68),(face*20,17))
        tip=add(dst,(face*39,9+sin(t*8)*7))
        crease_pt=between(mid2,tip,.48)
        shape([a,mid1,dst,add(dst,(face*18,-8)),tip,crease_pt,add(hip,(-face*7,14)),b],(62,33,64),1.7)
        shape([a,mid1,dst,add(dst,(face*18,-8)),between(dst,tip,.56),between(a,tip,.65)],(103,49,77),0)
        shape([a,mid1,between(mid1,dst,.88),between(mid1,dst,.55),between(a,dst,.23)],(157,66,91),0)
        line([a,mid1,dst],paint(trim,p['cloth'],.39),.74)
    else:
        root=torso((-17,body_len-4))
        flap=(hip[0]-face*45-speed*.08,hip[1]+24-min(39,abs(speed)*.054)+sin(t*9)*6)
        tip=(flap[0]-face*25-speed*.035,flap[1]+12+sin(t*12)*6)
        shape([root,offset(flap,(-1,-.15),6),tip,add(tip,(face*8,9)),add(flap,(face*3,10)),add(root,(0,7))],p['trim_dark'],1.2)
        line([root,flap,tip],trim,1.35)

    def leg(joint,ankle,near):
        trouser=p['trouser'] if near else paint(p['trouser'],INK,.34)
        lit=p['trouser_light'] if near else paint(p['trouser_light'],INK,.47)
        knee_axis=normal(unit(sub(ankle,joint)))
        legroot=add(hip,offset((0,0),across,6 if near else -7))
        a=side(legroot,joint,12.4)
        b=offset(joint,knee_axis,9.0)
        c=offset(ankle,knee_axis,6.85)
        d=offset(ankle,knee_axis,-7.2)
        ee=offset(joint,knee_axis,-8.8)
        ff=side(legroot,joint,-10.7)
        shape([a,b,c,d,ee,ff],trouser)
        shape([a,between(b,joint,.24),between(c,ankle,.68),c,d,between(ee,joint,.30),
               between(joint,legroot,.28),between(a,legroot,.46)],lit,0)
        line([between(a,legroot,.22),between(b,joint,.28),between(c,ankle,.28)],paint(lit,p['bright'],.25),.8)
        line([between(a,joint,.78),between(ee,joint,.34),between(ee,ankle,.28)],p['dark'],1.14)
        boot_top=between(joint,ankle,.63)
        ta,tb,tc,td=strip(boot_top,ankle,7.7,7.9)
        toe=add(ankle,(face*14,-2.5))
        sole=add(ankle,(face*12,3.7))
        heel=add(ankle,(-face*6,3.5))
        shape([ta,tb,tc,td],p['boot'])
        shape([tb,add(ankle,(face*3,-6)),toe,sole,heel,tc],p['boot'])
        shape([ta,between(ta,td,.46),between(tb,tc,.38),add(ankle,(face*7,-3)),toe,
               add(ankle,(face*4,0)),between(tb,tc,.75)],paint(p['boot'],p['trouser_light'],.49),0)
        line([heel,sole],paint(p['boot'],p['bright'],.29),1.1)
        for u in [.69,.79]:
            aa=between(joint,ankle,u)
            line([offset(aa,knee_axis,5.9),offset(aa,knee_axis,-5.6)],p['shade'],.95)

    def arm(elbow,hand,near):
        root=torso((10 if near else -9,3))
        n1=normal(unit(sub(elbow,root)))
        n2=normal(unit(sub(hand,elbow)))
        sleeve=p['cloth'] if near else paint(p['cloth'],p['shade'],.53)
        hl=p['bright'] if near else paint(p['bright'],p['shade'],.55)
        handstart=between(elbow,hand,.78)
        a,b=offset(root,n1,10.5),offset(root,n1,-10.2)
        aa,bb=offset(elbow,n2,8),offset(elbow,n2,-7.3)
        end1,end2=offset(handstart,n2,6.6),offset(handstart,n2,-5.9)
        shape([a,aa,end1,end2,bb,b],sleeve)
        shape([a,between(a,b,.39),between(aa,bb,.55),between(end1,end2,.31),end1,aa],hl,0)
        shape([b,bb,end2,between(end1,end2,.66),between(aa,bb,.71),between(a,b,.78)],p['shade'],0)
        line([between(a,b,.15),between(aa,bb,.16),between(end1,end2,.13)],light,.82)
        line([between(aa,bb,.14),between(aa,bb,.65),between(bb,end2,.38)],p['shade'],.83)
        glove_a=offset(handstart,n2,6.1); glove_b=offset(handstart,n2,-6.4)
        wrist=between(elbow,hand,.90)
        r=unit(sub(hand,elbow))
        q1=offset(wrist,n2,4.6)
        q2=offset(wrist,n2,-4.7)
        q3=offset(offset(hand,n2,4.6),r,3.8)
        q4=offset(offset(hand,n2,-4.6),r,3.7)
        shape([glove_a,glove_b,q2,q1],p['boot'])
        line([glove_a,glove_b],trim,.81 if near else .47)
        shape([q1,q2,q4,offset(hand,r,6.7),q3],p['boot'] if sith else (193,172,155),1)
        line([q1,offset(q3,r,-.9)],p['trouser_light'] if sith else p['face_light'],1.05)
        if sith and not near and 6.7<t<8.19:
            for i in range(3):
                a0=offset(q4,n2,(i-1)*3.1)
                tip=add(a0,(face*(8+i*.9),(i-1)*3.4))
                shape([a0,add(tip,(-face*2,-1.3)),tip,add(a0,(0,2))],p['skin_shade'],.6)

    leg(kb,fb,False)
    arm(eb,hb,False)
    leg(k,ft,True)
    neck=between(hd,sh,.68)
    shape([add(neck,(-6,-7)),add(neck,(6,-6)),torso((8,6)),torso((-7,7))],p['skin_shade'],.86)
    cloth([(-8,-7),(-20,-2),(-22,12),(-15,29),(-14,body_len+4),
           (13,body_len+6),(17,27),(24,13),(19,0),(9,-7)],p['cloth'],1.7)
    cloth([(-8,-6),(-19,-1),(-18,14),(-12,30),(-11,body_len),
           (-1,body_len-5),(-3,22),(2,13)],p['shade'],0)
    cloth([(4,-4),(15,-3),(22,6),(16,17),(12,25),(9,body_len-7),
           (2,body_len-10),(3,22),(8,10)],p['bright'],0)
    cloth([(-15,body_len-11),(-16,body_len+9),(-10,body_len+19),(-5,body_len+14),
           (0,body_len+2),(13,body_len+17),(22,body_len+16),(16,body_len-11)],p['shade'],1.3)
    cloth([(0,body_len-4),(14,body_len-7),(18,body_len+13),(15,body_len+13),
           (6,body_len+4)],p['cloth'],0)
    if sith:
        cloth([(-21,4),(-17,-6),(-8,-13),(-4,-2),(7,1),(11,-11),(18,-7),
               (24,6),(16,15),(8,11),(2,16),(-10,13),(-14,18)],(54,40,63),1.4)
        crease([(-16,-5),(-9,-10),(-5,-1),(4,4),(12,-9),(17,-6)],paint(trim,p['cloth'],.27),1.24)
        cloth([(-8,13),(-2,16),(7,13),(9,21),(0,29),(-1,body_len-6),(-7,body_len-5)],(91,56,80),.93)
        crease([(-7,20),(-1,25),(5,21)],p['trim_dark'],1.3)
    else:
        cloth([(-12,-6),(-7,-8),(4,9),(12,25),(9,33),(2,22),(-5,10)],p['dark'],.9)
        cloth([(11,-7),(17,-3),(12,9),(5,20),(-2,35),(-7,body_len-8),
               (-12,body_len-11),(-7,30),(-2,18)],(232,240,225),1)
        crease([(15,-4),(9,10),(3,18),(-4,32)],p['trim_dark'],1.46)
        crease([(16,21),(11,29),(9,body_len-11)],p['shade'],1.15)
    cloth([(-16,body_len-9),(15,body_len-8),(16,body_len-1),(-15,body_len+1)],p['dark'],1.2)
    crease([(-15,body_len-7),(15,body_len-6)],trim,1.1)
    cloth([(6,body_len-9),(12,body_len-9),(12,body_len+1),(6,body_len+1)],paint(trim,p['bright'],.35),.62)
    arm(e,h,True)
    draw_head(hd,sh,face,sith,t,poly,line)
    glow=(.12 if size>4 else .035)
    bloom([torso((13,-1)),torso((18,8)),torso((14,19))],tuple(int(component*glow) for component in c),3)
    bloom([add(hd,(face*3,-4)),add(hd,(face*12,-4))],tuple(int(component*.15) for component in c),2)
    return h

def portrait_insert(im,t,W,H):
    # A two-panel close-up drawn with the same heads used in the fight.
    left=Image.new('RGB',(W,H),(16,31,58))
    right=Image.new('RGB',(W,H),(68,21,44))
    start=11.99
    progress=(t-start)/.38
    for out,sith in ((left,False),(right,True)):
        d=ImageDraw.Draw(out,'RGBA')
        side=-1 if sith else 1
        p=SITH if sith else JEDI
        px=W*(.71 if sith else .29)+side*21*progress
        py=H*.53+sin(progress*pi)*3
        scale=17.4+progress*1.1
        anch=(px,py)
        rng=random.Random(212 if sith else 622)
        grad=p['trim_dark']
        for n in range(145):
            row=int(rng.uniform(0,H)); yy=row+int(rng.uniform(-74,74))
            x1=rng.randrange(-100,W+100)+int((-progress*150 if sith else progress*150))
            lng=rng.randrange(16,465)
            d.line([(x1,row),(x1+side*lng,yy)],fill=(*grad,rng.randrange(20,154)),width=rng.randrange(1,8))
        def poly(pts,c): d.polygon(pts,fill=c)
        def line(pts,c,w=1): d.line(pts,fill=c,width=max(1,round(w)),joint='curve')
        d.polygon([(px-383,H),(px-254,py+214),(px-106,py+137),(px+153,py+126),
                   (px+249,py+224),(px+332,H)],fill=p['cloth'])
        d.line([(px-383,H),(px-254,py+214),(px-106,py+137)],fill=p['trim'],width=5)
        d.polygon([(px-132,py+126),(px+98,py+121),(px+91,H),(px-89,H)],fill=p['skin_shade'])
        draw_head(anch,(px-side*(12+progress*6),py+170),side,sith,t,poly,line,scale=scale)
        edge=(*p['trim'],53)
        glint=py+scale*(-2+side*.1)
        d.line([(px-280,glint+side*22),(px+320,glint-side*30)],fill=edge,width=4)
        for n in range(52):
            x0=rng.randrange(0,W)
            y0=rng.randrange(0,H)
            d.line([(x0,y0),(x0-7,y0+20)],fill=(190,219,241,54),width=1)
    mask=Image.new('L',(W,H))
    d=ImageDraw.Draw(mask)
    d.polygon([(0,0),(W*.62,0),(W*.39,H),(0,H)],fill=255)
    composed=Image.composite(left,right,mask)
    d=ImageDraw.Draw(composed,'RGBA')
    d.line([(W*.62,0),(W*.39,H)],fill=(12,14,28),width=16)
    d.line([(W*.62+6,0),(W*.39+6,H)],fill=(242,227,239,198),width=2)
    if t<12.05 or t>12.31:
        u=min(1,max(0,min(t-start,12.383-t)/.054))
        return Image.blend(im,composed,u)
    return composed
