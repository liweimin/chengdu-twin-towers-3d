from bisect import bisect_right
from functools import lru_cache
import math
from pathlib import Path
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = 30
BEAT = .4
BEATS = 132
ROOT = Path(__file__).resolve().parent
FONT_DIR = Path('C:/Windows/Fonts')
PAPER = '#f8f0df'
INK = '#161421'
AMBER = '#ffc26c'
MINT = '#a8f7d1'
LILAC = '#d7c1ff'
ORANGE = '#a63721'
SKY = '#91d5ff'
TAU = math.tau

# Timings are written in beats and shared with the score.
SCENES = [
    (0,   '2022—2026', '一场对话，四年', '', '', 'open'),
    (8,   '2022.11.30', 'ChatGPT', '基于 GPT-3.5 的公开研究预览', '一段可以追问的对话', 'chat'),
    (16,  '2022.12.05', '100 万+', '注册用户', '公开发布后第 5 天', 'million'),
    (24,  '2023.03.14', 'GPT-4', '进入 ChatGPT Plus', '模型支持图像与文字输入', 'vision'),
    (32,  '2023.11.06', 'GPTs', '自定义版本的 ChatGPT', '指令、知识、技能可以组合', 'tiles'),
    (40,  '2024.05.13', 'GPT-4o', '实时处理文字、图像与音频', '同一个模型，处理不同模态', 'voice'),
    (50,  '2024.09.12', 'o1-preview', '推理模型登场', '花更多时间思考复杂问题', 'reason'),
    (58,  '2025.02.02', 'Deep research', '深度研究进入 ChatGPT', '检索、综合资料并生成带引用的报告', 'research'),
    (66,  '2025.08.07', 'GPT-5', '快速回答与深度推理统一', '系统自动选择何时深入思考', 'merge'),
    (76,  '2025.10  /  DEVDAY', '8 亿+', 'ChatGPT 每周用户', 'OpenAI DevDay 2025 公布', 'growth'),
    (84,  '2026.09.03', 'GPT-6 Astra', '发布并开始分批开放', '面向编程、研究与多步骤工作', 'astra'),
    (92,  '2026.10.05', '12 亿', 'ChatGPT 每周触达人数', 'OpenAI 于 2026 年 10 月披露', 'world'),
    (100, '2026.10.07', 'GPT-6', 'Intelligent UI 进入对话', '答案可包含图表和可操作的工具', 'ui'),
    (108, '2026.11.17 → 11.23', 'GPT-6.2', 'Astra 与 Sol 发布', '随后，面向聊天标签页的版本开始推送', 'duo'),
    (120, '2022.11.30 — 2026.11.30', '对话继续', '', '', 'end'),
]
STARTS = [row[0] for row in SCENES]
PALETTES = {
    'open': ('#21112d', '#59344d', PAPER, AMBER),
    'chat': ('#ebd8bc', '#fff0d7', INK, ORANGE),
    'million': ('#29132d', '#743b56', PAPER, AMBER),
    'vision': ('#24274a', '#473b78', PAPER, LILAC),
    'tiles': ('#e1e9cc', '#fff1d5', INK, '#225a49'),
    'voice': ('#18152e', '#503566', PAPER, MINT),
    'reason': ('#152929', '#21594d', PAPER, MINT),
    'research': ('#f6d5b5', '#fff0da', INK, ORANGE),
    'merge': ('#29264b', '#63408a', PAPER, LILAC),
    'growth': ('#2b172c', '#7a4556', PAPER, AMBER),
    'astra': ('#11192c', '#284770', PAPER, SKY),
    'world': ('#102a2c', '#23665e', PAPER, MINT),
    'ui': ('#e2d8fa', '#f9eed8', INK, '#53309b'),
    'duo': ('#261938', '#5a3b69', PAPER, LILAC),
    'end': ('#271331', '#6f3d61', PAPER, AMBER),
}


@lru_cache(maxsize=128)
def rgb(hex_color):
    return tuple(bytes.fromhex(hex_color[1:]))


def blend(a, b, mix):
    mix = max(0, min(mix, 1))
    return tuple(round(x+(y-x)*mix) for x, y in zip(rgb(a) if isinstance(a, str) else a, rgb(b) if isinstance(b, str) else b))


@lru_cache(maxsize=256)
def font(size, family):
    file = {'title':'ARIALNB.TTF', 'zh':'msyhbd.ttc', 'regular':'msyh.ttc', 'mono':'consola.ttf'}[family]
    return ImageFont.truetype(str(FONT_DIR / file), size)


def label(draw, x, y, value, size, color, family='mono', anchor='lt', max_width=None):
    f = font(size, family)
    if max_width and f.getlength(value) > max_width:
        f = font(max(12, int(size*max_width/f.getlength(value))), family)
    draw.text((x,y), value, font=f, fill=color, anchor=anchor)


def ease(x):
    return 1-(1-max(0, min(x, 1)))**3


def dot(draw, x, y, radius, color):
    draw.ellipse((x-radius,y-radius,x+radius,y+radius), fill=color)


def path(draw, points, color, width=1):
    draw.line(points, fill=color, width=width, joint='curve')


def card(draw, box, color, edge, radius=18):
    x0,y0,x1,y1 = box
    draw.rounded_rectangle((x0+7,y0+10,x1+7,y1+10),radius,fill=blend(color, INK,.72))
    draw.rounded_rectangle(box, radius, fill=color, outline=edge, width=1)


@lru_cache(maxsize=16)
def backdrop(kind):
    base, glow, _, _ = PALETTES[kind]
    rng = np.random.default_rng(19)
    ys, xs = np.mgrid[0:360,0:640]
    lobe = np.exp(-(((xs-495)/310)**2+((ys-154)/176)**2))
    texture = rng.normal(0,1.7,lobe.shape) + .8*np.sin(ys*2.6)
    lo, hi = np.array(rgb(base)), np.array(rgb(glow))
    data = lo + (hi-lo)*lobe[:,:,None] + texture[:,:,None]
    return Image.fromarray(np.clip(data,0,255).astype(np.uint8)).resize((W,H),Image.Resampling.BILINEAR)


rng = random.Random(612)
SPECKS = [(rng.uniform(0,W),rng.uniform(0,H),rng.uniform(.5,1.9),rng.random()) for _ in range(140)]


def landscape(d, x, y, w, h, t, c):
    d.rounded_rectangle((x,y,x+w,y+h),12,fill='#3b3d75')
    dot(d,x+w*.72,y+h*.32, min(w,h)*.18,'#ffd38b')
    for i,(col, base) in enumerate([('#a17cd3',.73),('#6e59a9',.83),('#483d7b',.99)]):
        points = [(x+w*j/16,y+h*(base-.28*(.5+.5*math.sin(j*.81+i*2+t*.6))**2)) for j in range(17)]
        d.polygon(points+[(x+w,y+h),(x,y+h)],fill=col)
    d.rounded_rectangle((x,y,x+w,y+h),12,outline=c,width=1)


def orbit(d, cx, cy, rx, ry, t, accent, base, rings=12, tilt=.25):
    for ring in range(rings):
        p = ring/max(1,rings-1)
        r = .45+p*.55
        pts = []
        for j in range(84):
            a = j*TAU/83
            x = math.cos(a)*r*rx
            y = math.sin(a)*r*ry + 7*math.sin(a*4+t*3+ring*.4)
            pts.append((cx+x*math.cos(tilt)-y*math.sin(tilt),cy+x*math.sin(tilt)+y*math.cos(tilt)))
        path(d,pts,blend(base,accent,.22+p*.47),1)
        k = int((ring*13+t*(13+ring%3))%83)
        if ring%2==0:
            dot(d,*pts[k],2+ring%3,accent)


def wire(d, cx, cy, radius, angle, accent, base, box=False):
    ca,sa = math.cos(angle),math.sin(angle)
    cb,sb = math.cos(.40),math.sin(.40)
    def project(v):
        x,y,z=v
        x,z=x*ca+z*sa,-x*sa+z*ca
        y,z=y*cb-z*sb,y*sb+z*cb
        perspective=1/(1-z*.24)
        return cx+x*radius*perspective,cy+y*radius*perspective,z
    lines = []
    if box:
        for h in (-1,-.65,-.3,.05,.4,.75,1):
            lines.append([(x,h,z) for x,z in [(-1,-1),(1,-1),(1,1),(-1,1),(-1,-1)]])
            lines.extend([[(h,-1,z),(h,1,z)] for z in [-1,1]])
            lines.extend([[(x,-1,h),(x,1,h)] for x in [-1,1]])
    else:
        for lat in np.linspace(-1.4,1.4,12):
            lines.append([(math.cos(lat)*math.cos(j*TAU/56),math.sin(lat),math.cos(lat)*math.sin(j*TAU/56)) for j in range(57)])
        for lon in np.linspace(0,TAU,19)[:-1]:
            lines.append([(math.sin(j*math.pi/40)*math.cos(lon),math.cos(j*math.pi/40),math.sin(j*math.pi/40)*math.sin(lon)) for j in range(41)])
    for line in lines:
        points = list(map(project,line))
        for (x,y,z),(xx,yy,zz) in zip(points,points[1:]):
            path(d,[(x,y),(xx,yy)],blend(base,accent,.29+.64*((z+zz)/4+.5)),1 if z<0 else 2)


def bars(d,x,y,count,width,height,t,accent,base,kind):
    for i in range(count):
        pos=i/(count-1)
        if kind=='audio':
            h=(.12+.8*abs(math.sin(i*.17-t*7)*math.cos(i*.105+t*4)))*math.sin(math.pi*pos)**.35
            d.rounded_rectangle((x+pos*width,y-h*height,x+pos*width+3,y+h*height),2,fill=blend(base,accent,.43+.57*h))
        else:
            h=(.12+.88*pos**1.7)*(.9+.1*math.sin(i*.8+t*7))
            if pos<=ease(t*.85):
                d.rounded_rectangle((x+pos*width,y-h*height,x+pos*width+max(2,width/count-5),y),3,fill=blend(base,accent,.28+.69*pos))


def visual(d, kind, t, kick, fg, accent):
    base, glow, _, _ = PALETTES[kind]
    cx, cy = 949, 351
    m = ease(t*2.8)
    sx = (1-m)*120
    cx += sx
    tint = blend(base,accent,.5)
    if kind=='chat':
        for i in range(3):
            x = 725+42*i+sx
            y = 195+81*i+(1-ease((t-.10*i)*3))*75
            bg = ('#fbefd9','#33253b','#a63721')[i]
            fore = (INK,PAPER,PAPER)[i]
            card(d,(x,y,x+332,y+112),bg,tint)
            k = max(0,int((t-.25*i)*17))
            label(d,x+24,y+23,('你好。','你好，有什么想问的？','我们从哪里开始？')[i][:k],22,fore,'regular')
            for j in range(3):
                d.rounded_rectangle((x+24+j*44,y+65,x+55+j*44,y+69),2,fill=blend(bg,fore,.4))
            if int(t*5)%2==0:
                d.rectangle((x+287,y+63,x+302,y+76),fill=fore)
    elif kind=='million':
        orbit(d,cx,cy,243,140,t,accent,base,16,-.37)
        for i in range(112):
            a=i*2.399963+t*.25
            r=(i/112)**.5*205
            x,y=cx+r*math.cos(a),cy+.77*r*math.sin(a)
            dot(d,x,y,1.2+2*(i%5==0)+kick*.7,blend(base,accent,.38+.55*(i%9)/8))
        dot(d,cx,cy,43+7*kick,accent)
        label(d,cx,cy,'+',47,INK,'title','mm')
    elif kind=='vision':
        for i in range(3):
            x,y=777+i*22+sx,202+i*32+math.sin(t*2+i)*8
            card(d,(x,y,x+355,y+235),blend(glow,LILAC,.14+i*.08),accent)
        x,y=822+sx,274+math.sin(t*2+2)*8
        landscape(d,x+17,y+11,319,172,t,accent)
        label(d,x+18,y+203,'图像输入  /  IMAGE',16,PAPER,'regular')
        scan = x+18+(t*.44%1)*303
        path(d,[(scan,y+12),(scan,y+178)],PAPER,2)
    elif kind=='tiles':
        for i,(name,color) in enumerate([('指令','#f9ead0'),('知识','#badac8'),('技能','#efbc96')]):
            x=756+i*135+sx
            y=239+math.sin(t*3+i)*26+(1-ease((t-i*.13)*3))*90
            card(d,(x,y,x+126,y+239),color,'#366355')
            label(d,x+63,y+25,name,26,INK,'zh','mt')
            for k in range(6):
                rr=9+k*7
                d.arc((x+63-rr,y+126-rr,x+63+rr,y+126+rr),int(t*80+i*38+k*13)%360,int(t*80+i*38+k*13)%360+222,fill='#225a49',width=2)
            path(d,[(x+21,y+198),(x+105,y+198)],'#225a49',1)
    elif kind=='voice':
        for i in range(6):
            r=57+31*i+2*kick
            d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=blend(base,accent,.12+i*.046),width=1)
        bars(d,716+sx,cy,100,462,151+15*kick,t,accent,base,'audio')
        for i,name in enumerate(['文字','图像','音频']):
            x=768+145*i+sx
            d.rounded_rectangle((x-42,526,x+42,561),17,fill=blend(base,accent,.17+i*.13),outline=tint)
            label(d,x,544,name,17,fg,'regular','mm')
    elif kind=='reason':
        for i in range(13):
            a=i*2.399963+t*.34
            r=52+int(i/2)*26
            x,y=cx+r*math.cos(a),cy+r*.90*math.sin(a)
            path(d,[(cx,cy),(cx+(x-cx)*.51,y),(x,y)],blend(base,accent,.31+i*.03),1+(i%4==0))
            dot(d,x,y,4+i%4+kick,accent if (int(t*4)+i)%4==0 else tint)
            d.ellipse((x-15,y-15,x+15,y+15),outline=tint)
        for i in range(4):
            rr=34+i*15+math.sin(t*5+i)*4
            d.arc((cx-rr,cy-rr,cx+rr,cy+rr),t*111+i*60,t*111+i*60+240,fill=accent,width=3)
        dot(d,cx,cy,12+6*kick,accent)
    elif kind=='research':
        for i in range(3):
            x,y=741+i*54+sx,202+i*53+math.sin(t*3+i)*6
            sheet=('#ca6948','#f8e4cb','#fff2e0')[i]
            card(d,(x,y,x+302,y+232),sheet,'#a63721')
            label(d,x+22,y+25,('检索','整理','带引用的报告')[i],23,PAPER if i==0 else INK,'zh')
            for j in range(6):
                if t*9>j+i*.4:
                    rowy=y+71+j*21
                    path(d,[(x+24,rowy),(x+97+(j*37)%154,rowy)],blend(sheet,INK,.41),3)
        xx=1081+sx
        label(d,xx,499,'[1] [2] [3]',18,ORANGE)
    elif kind=='merge':
        for i in range(14):
            start_y=174+i*27
            pts=[]
            for j in range(81):
                p=j/80
                pts.append((714+492*p+sx,cy+(start_y-cy)*(1-ease(p*1.38))+math.sin(p*11-t*5+i*.35)*(15+9*kick)))
            path(d,pts,blend(glow,accent,.39+(i%5)*.12),2)
            dot(d,*pts[int((t*38+7*i)%80)],3,accent)
        label(d,755+sx,130,'快速回答',20,LILAC,'regular')
        label(d,755+sx,567,'深度推理',20,LILAC,'regular')
    elif kind=='growth':
        for i in range(8):
            x=762+55*i+sx
            y=cy+83*math.sin(i*.68+t*2.9)
            for j in range(5,-1,-1):
                rr=14+j*3
                dot(d,x,y,rr,blend(base,accent,.13+(5-j)*.058))
            dot(d,x,y,10+5*kick,accent)
            path(d,[(x,y-49),(x,y+49)],blend(base,accent,.45),1)
        orbit(d,cx,cy,242,112,t,accent,base,10,-.42)
    elif kind=='astra':
        wire(d,cx,cy,134+8*kick,t*.48+.38,accent,base,True)
        orbit(d,cx,cy,233,110,t,accent,base,7,-.31)
        for i,(x,y) in enumerate([(769,193),(1127,203),(1119,530)]):
            label(d,x+sx,y,['编程','研究','多步骤工作'][i],18,accent,'regular')
    elif kind=='world':
        wire(d,cx,cy,183+5*kick,t*.55,accent,base)
        orbit(d,cx,cy,246,102,t,PAPER,base,7,.34)
        for i in range(42):
            a=i*2.399963+t*.2
            r=115+85*abs(math.sin(i*1.8))
            dot(d,cx+r*math.cos(a),cy+r*.82*math.sin(a),1.2+(i%6==0)*2,accent)
    elif kind=='ui':
        x,y=741+sx,181
        card(d,(x,y,x+427,y+339),'#fff7e5','#654b97')
        label(d,x+25,y+27,'比较两个方案',24,INK,'zh')
        for i,(name,col) in enumerate([('方案 A','#d8c7f5'),('方案 B','#b7dccc')]):
            xx=x+24+192*i
            d.rounded_rectangle((xx,y+76,xx+178,y+219),12,fill=col)
            label(d,xx+15,y+93,name,18,INK,'zh')
            for j in range(6):
                h=(15+j*9+8*math.sin(t*4+j+i))*ease(t*2)
                if h>0:
                    d.rounded_rectangle((xx+14+25*j,y+196-h,xx+31+25*j,y+196),3,fill='#694c9e' if i==0 else '#33755a')
        path(d,[(x+35,y+268),(x+386,y+268)],'#c5b4dc',5)
        r=x+35+350*(.54+.31*math.sin(t*2))
        dot(d,r,y+268,11,'#654b97')
        label(d,x+26,y+296,'交互示意',15,'#654b97','regular')
    elif kind=='duo':
        for i,(name,col) in enumerate([('Astra',LILAC),('Sol',AMBER)]):
            x,y=740+220*i+sx,211+math.sin(t*2+i*2)*15
            card(d,(x,y,x+203,y+281),'#302340' if i==0 else '#4b2b3a',col,19)
            orbit(d,x+102,y+132,76,48,t+i,col,base,8,.57 if i==0 else -.5)
            dot(d,x+102,y+132,12+4*kick,col)
            label(d,x+16,y+221,name,46,col,'title')


def full_title(d,kind,t,kick,fg,accent):
    base, _, _, _ = PALETTES[kind]
    if kind=='open':
        if t<.8:
            orbit(d,640,365,280+135*t,165,t,accent,base,18,-.28)
            d.rectangle((612,314,669,401),fill=accent)
            label(d,640,351,'›',63,INK,'title','mm')
        else:
            orbit(d,891,360,383,222,t,accent,base,16,-.34)
            label(d,82,158,'2022 → 2026',28,accent)
            label(d,73,201+22*(1-ease((t-.8)*3)),'ChatGPT',156,fg,'title')
            label(d,80,376,'一场对话，四年',69,fg,'zh')
            label(d,83,485,'四周年独立致敬短片',22,accent,'regular')
            label(d,1147,489,'04',154,blend(base,accent,.59),'title','rt')
    else:
        orbit(d,922,350,331,206,t,accent,base,20,-.30)
        label(d,1157,177,'04',255,blend(base,accent,.77),'title','rt')
        label(d,82,170,'ChatGPT 四周年',30,accent,'zh')
        label(d,76,230,'对话继续',112,fg,'zh')
        label(d,83,386,'2022.11.30 — 2026.11.30',30,fg)
        label(d,83,452,'独立致敬短片  ·  非 OpenAI 官方出品',22,accent,'regular')
        label(d,83,495,'史料核验截至 2026.11.25',17,fg,'regular')


def place_visual(pic, kind, t, kick, fg, accent, scale=1, shift=(0,0)):
    if scale==1 and shift==(0,0):
        visual(ImageDraw.Draw(pic),kind,t,kick,fg,accent)
        return
    layer=Image.new('RGBA',(W,H))
    visual(ImageDraw.Draw(layer),kind,t,kick,fg,accent)
    layer=layer.resize((round(W*scale),round(H*scale)),Image.Resampling.BICUBIC)
    pic.paste(layer,shift,layer)


def render_frame(t):
    beat=t/BEAT
    index=bisect_right(STARTS,beat+1e-8)-1
    start,date,title,sub,details,kind=SCENES[index]
    elapsed=t-start*BEAT
    phase=beat%1
    kick=math.exp(-phase*7)
    base, glow, fg, accent=PALETTES[kind]
    pic=backdrop(kind).copy()
    d=ImageDraw.Draw(pic)
    grid=blend(glow,fg,.13)
    for x in range(40,1250,48):
        for y in range(122,630,48):
            dot(d,x,y,1,grid)
    for x,y,size,brightness in SPECKS:
        x=(x+t*(7+brightness*16))%W
        if 675<x<1245 and 105<y<619:
            dot(d,x,y,size,blend(glow,accent,.12+brightness*.37))
    d.rectangle((38,35,1241,682),outline=blend(glow,fg,.30),width=1)
    for x,y,s in [(38,35,1),(1241,35,-1),(38,682,1),(1241,682,-1)]:
        path(d,[(x,y),(x+s*19,y)],accent,3)
    path(d,[(62,92),(1218,92)],blend(base,fg,.3),1)
    label(d,63,55,'INDEPENDENT TRIBUTE',16,fg)
    label(d,1216,55,'CHATGPT  /  4 YEARS',16,fg,anchor='rt')
    if kind in ('open','end'):
        full_title(d,kind,elapsed,kick,fg,accent)
    else:
        left_visual=kind in ('vision','research','ui')
        detail_start={'voice':2.8,'merge':2.8,'astra':2.4,'duo':3.2}.get(kind,99)
        detail=elapsed>=detail_start
        rise=(1-ease(elapsed*4.7))*28
        family='zh' if kind in ('growth','world','million') else 'title'
        if detail:
            # Cut to a closer view of the artwork, with a smaller editorial caption.
            scale=1.18+.10*ease(elapsed-detail_start)
            place_visual(pic,kind,elapsed,kick,fg,accent,scale,(round(807-949*scale),round(341-351*scale)))
            label(d,78,180,date,22,accent)
            label(d,75,241,title,70,fg,family,max_width=385)
            label(d,78,332,sub,22,fg,'zh',max_width=380)
            label(d,78,374,details,17,fg,'regular',max_width=380)
        elif kind in ('million','growth','world'):
            scale=1.12
            place_visual(pic,kind,elapsed,kick,fg,accent,scale,(-91,-36))
            label(d,80,152+rise,date,25,accent)
            label(d,73,214+rise,title,173,fg,family,max_width=700)
            label(d,82,442+rise,sub,33,fg,'zh')
            label(d,84,501+rise,details,20,blend(base,fg,.88),'regular')
        else:
            x=652 if left_visual else 78
            if left_visual:
                place_visual(pic,kind,elapsed,kick,fg,accent,1.07,(-729,-18))
                path(d,[(622,161),(622,528)],blend(base,fg,.30),1)
            else:
                place_visual(pic,kind,elapsed,kick,fg,accent)
            label(d,x,178+rise,date,25,accent)
            label(d,x-7,226+rise,title,128,fg,family,max_width=555 if left_visual else 620)
            d.rounded_rectangle((x,377,x+min(552,1217-x)*ease(elapsed*1.7),379),1,fill=blend(base,accent,.67))
            label(d,x,402+rise,sub,30,fg,'zh',max_width=560 if left_visual else 627)
            label(d,x+1,454+rise,details,21,blend(base,fg,.88),'regular',max_width=553 if left_visual else 619)
            for j in range(4):
                r=4+3*(int(beat)%4==j)*kick
                dot(d,x+5+j*21,553,r,accent if int(beat)%4==j else blend(base,accent,.45))
    d.rectangle((63,602,1217,604),fill=blend(base,fg,.25))
    d.rectangle((63,602,63+1154*beat/BEATS,605),fill=accent)
    for i in STARTS:
        x=63+1154*i/BEATS
        path(d,[(x,598),(x,610)],blend(base,fg,.62),1)
    for b,yr in [(0,'2022'),(24,'2023'),(40,'2024'),(58,'2025'),(84,'2026')]:
        label(d,63+1154*b/BEATS,631,yr,17,fg)
    if 0<elapsed<.14 and kind not in ('open','end'):
        w=int(1165*(1-ease(elapsed/.14)))
        if w:
            x=1240-w if index%2 else 39
            d.rectangle((x,94,x+w,101),fill=accent)
            d.rectangle((x,585,x+w,592),fill=accent)
    if t>52.43:
        pic=Image.blend(pic,Image.new('RGB',(W,H),INK),ease((t-52.43)/.37))
    return pic


def score():
    sr=48000
    duration=BEATS*BEAT
    stereo=np.zeros((round(sr*duration),2),dtype=np.float32)
    rng=np.random.default_rng(20261130)
    def timer(seconds):
        return np.arange(round(sr*seconds))/sr
    def hz(note):
        return 440*2**((note-69)/12)
    def add(at,signal,gain,pan=0):
        i=round(sr*at)
        signal=signal[:max(0,len(stereo)-i)]
        stereo[i:i+len(signal),0]+=signal*gain*math.sqrt((1-pan)*.5)
        stereo[i:i+len(signal),1]+=signal*gain*math.sqrt((1+pan)*.5)
    kt=timer(.36)
    kick=np.sin(TAU*(48*kt+52*.023*(1-np.exp(-kt/.023))))*np.exp(-kt*13)
    kick+=.18*np.sin(TAU*116*kt)*np.exp(-kt*55)
    ht=timer(.115)
    noise=rng.normal(0,.25,len(ht))
    hat=np.diff(noise,prepend=0)*np.exp(-ht*45)
    st=timer(.23)
    noise=rng.normal(0,.21,len(st))
    snare=(np.diff(noise,prepend=0)*np.exp(-st*21)+.25*np.sin(TAU*(171*st-19*st**2))*np.exp(-st*36))
    bt=timer(.34)
    pt=timer(.55)
    chords=[(45,57,60,64,71),(41,57,60,64,69),(48,55,60,64,67),(43,55,59,62,69)]
    for beat in range(BEATS-4):
        when=beat*BEAT
        root,*chord=chords[(beat//4)%4]
        full=8<=beat<120
        if beat%4 in (0,2) or (full and (beat%4==3 or beat in STARTS)):
            add(when,kick,.72 if full else .55)
        if full and beat%4 in (1,3):
            add(when,snare,.56,-.07)
        for off,vel in [(0,.19),(.5,.29),(.75,.11)]:
            if full or beat>=3:
                add(when+off*BEAT,hat,vel,.23 if off==.5 else -.21)
        for off,j in [(0,0),(.5,7)] if beat%4 in (0,2) else [(.5,0)]:
            f=hz(root-12+j)
            bass=(np.sin(TAU*f*bt)+.25*np.sin(TAU*f*2*bt)+.15*np.sin(TAU*f*3*bt))
            bass*=np.minimum(1,bt*115)*np.exp(-bt*(8 if off==0 else 13))
            if beat>=4:
                add(when+off*BEAT,bass,.29 if full else .16)
        for j in range(2 if beat<40 or beat>=120 else 4):
            note=chord[(beat+j*3)%4]+(12 if (beat+j)%3==0 else 0)
            p=TAU*hz(note)*pt
            pluck=(np.sin(p+.52*np.sin(p*2.002)*np.exp(-pt*8))+.13*np.sin(p*3))*np.minimum(1,pt*210)*np.exp(-pt*9)
            off=j*(.5 if beat<40 or beat>=120 else .25)
            add(when+BEAT*off,pluck,.10 if full else .19,(-1)**j*.48)
            add(when+BEAT*(off+.75),pluck,.034,(-1)**(j+1)*.60)
        if beat%4==0 and beat>=12:
            ct=timer(1.6)
            for j,note in enumerate(chord):
                p=TAU*hz(note)*ct
                sustain=(np.sin(p)+.26*np.sin(p*1.003)+.14*np.sin(2*p+np.sin(ct*3)))
                sustain*=np.minimum(1,ct*9)*np.exp(-ct*1.7)*(1-.23*np.cos(2*math.pi*ct/BEAT))
                add(when,sustain,.058,(j-1.5)*.4)
    for cut in STARTS[1:]:
        t=timer(.33)
        rise=rng.normal(0,.19,len(t))*.15+np.sin(TAU*(94*t+350*t**2))*.13
        add(cut*BEAT-.33,rise*(t/.33)**2,.60)
        bell=np.sin(TAU*hz(81)*pt)*np.exp(-pt*12)+.33*np.sin(TAU*hz(88)*pt)*np.exp(-pt*19)
        add(cut*BEAT,bell,.13,.35)
    et=timer(2.20)
    for i,note in enumerate((45,57,60,64,69,71,76)):
        p=TAU*hz(note)*et
        add(50.4+i*.025,(np.sin(p)+.18*np.sin(p*2))*np.minimum(1,et*12)*np.exp(-et*2.35),.105,(i-3)*.18)
    tail=round(sr*.55)
    stereo[-tail:]*=np.linspace(1,0,tail)[:,None]
    stereo=np.tanh(stereo*1.31)
    stereo*=.92/np.max(np.abs(stereo))
    out=ROOT/'score.wav'
    with wave.open(str(out),'wb') as wav:
        wav.setparams((2,2,sr,0,'NONE','not compressed'))
        wav.writeframes(np.round(stereo*32767).astype('<i2').tobytes())
    return out


def contact_sheet():
    sheet=Image.new('RGB',(1280,900),INK)
    for index,start in enumerate(STARTS):
        sample=render_frame(start*BEAT+1.45).resize((320,180),Image.Resampling.LANCZOS)
        sheet.paste(sample,((index%4)*320,(index//4)*180))
    sheet.save(ROOT/'contact.jpg',quality=95)


def export(output):
    soundtrack=score()
    args=['ffmpeg','-hide_banner','-y','-loglevel','warning','-f','rawvideo','-pix_fmt','rgb24',
          '-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(soundtrack),
          '-vf','scale=1920:1080:flags=lanczos,setsar=1','-c:v','libx264','-preset','fast','-crf','17',
          '-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-movflags','+faststart',
          '-color_primaries','bt709','-colorspace','bt709','-color_trc','bt709',str(output)]
    with subprocess.Popen(args,stdin=subprocess.PIPE) as encoder:
        for i in range(round(BEATS*BEAT*FPS)):
            encoder.stdin.write(render_frame(i/FPS).tobytes())
            if i%240==0:
                print(f'{i/FPS:04.1f}s rendered',flush=True)
        encoder.stdin.close()
        if encoder.wait()!=0:
            raise RuntimeError('FFmpeg could not encode the video')


if __name__=='__main__':
    if sys.argv[1]=='preview':
        contact_sheet()
    else:
        export(Path(sys.argv[1]))
