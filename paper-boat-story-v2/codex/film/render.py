"""Render the 30.5-second watercolor film with the book's own painted assets."""
from pathlib import Path
import inspect
import math
import random
import re
import runpy
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ACTOR = runpy.run_path(str(ROOT / "side-profile" / "paint_keyframe.py"))
BOOK = runpy.run_path(str(ROOT / "revision" / "paint_keyframes.py"))
W, H = 1200, 675
FPS, DURATION = 24, 30.5
TRANSPARENT = (0, 0, 0, 0)
PAPER = (249, 240, 217)


def clamp(v):
    return min(1., max(0., v))


def smooth(v):
    x = clamp(v)
    return x*x*(3-2*x)


def lerp(a, b, t):
    return a + (b-a)*t


def arc(t, start, end):
    return smooth((t-start)/(end-start))


def bump(t, start, end):
    x = clamp((t-start)/(end-start))
    return math.sin(math.pi*x)**2


def clean_plate(name):
    """Reuse the original washes, with movable subjects painted separately."""
    scope = BOOK.copy()
    src = inspect.getsource(BOOK[name])
    src = re.sub(r"^    (?:duck|boat)\(p,[^\n]+\)\n", "", src, flags=re.MULTILINE)
    src = re.sub(r'^    p\.save\("[^"]+"\)$', "    return p", src, flags=re.MULTILINE)
    exec(src, scope)
    p = scope[name]()
    ink = np.clip(p.paint, 0, 255).astype(np.uint8)
    return Image.fromarray(ink).convert("RGBA")


def isolated(painting, mark, box):
    """Recover pigment and alpha from paired black and white substrates."""
    l, t, r, b = box
    painting.paint.fill(0.)
    mark(painting)
    dark = painting.paint[t:b, l:r].copy()
    painting.paint.fill(255.)
    mark(painting)
    white = painting.paint[t:b, l:r]
    alpha = np.clip(1 - np.mean(white-dark, axis=2)/255., 0., 1.)
    rgb = np.divide(dark, alpha[:, :, None], out=np.zeros_like(dark),
                    where=alpha[:, :, None] > .0001)
    pixels = np.dstack((np.clip(rgb, 0, 255), alpha*255)).round().astype(np.uint8)
    return Image.fromarray(pixels)


def artwork_fn(name, unwanted):
    env = BOOK.copy()
    source = inspect.getsource(BOOK[name])
    env_lines = source.splitlines()
    keep = []
    reject = False
    for row in env_lines:
        if row.startswith("    fill(") or row.startswith("    line("):
            reject = any(part in row for part in unwanted)
        elif not row.startswith("         "):
            reject = False
        if not reject:
            keep.append(row)
    exec("\n".join(keep), env)
    return env[name]


DRAW_BOAT = artwork_fn("boat", ("M -6 69", "M 14 76"))
DRAW_DUCK = artwork_fn("duck", ("M -42 112", "M -21 110", "M 28 107"))


def paste(im, sprite, x, y):
    im.alpha_composite(sprite, (round(x), round(y)))


def scaled(sprite, sx, sy=None):
    if sy is None:
        sy = sx
    return sprite.resize((max(1, round(sprite.width*sx)),max(1,round(sprite.height*sy))),
                         Image.Resampling.BICUBIC)


def draw_sprite(im, sprite, anchor, x, y, scale, rotation=0., sy=None):
    sy = scale if sy is None else sy
    sw, sh = round(sprite.width*scale), round(sprite.height*sy)
    pic = sprite.resize((max(1,sw), max(1,sh)), Image.Resampling.BICUBIC)
    ax, ay = anchor[0]*scale, anchor[1]*sy
    if abs(rotation) < .03:
        paste(im,pic,x-ax,y-ay)
        return
    # Rotate around the painted anchor, surrounded by clear paper.
    pad = max(sw,sh)+2
    canvas = Image.new("RGBA", (2*pad,2*pad),TRANSPARENT)
    paste(canvas,pic,pad-ax,pad-ay)
    canvas = canvas.rotate(rotation,resample=Image.Resampling.BICUBIC)
    paste(im,canvas,x-pad,y-pad)


def shadow(im, x, y, rx, ry, a):
    l,t = round(x-rx-9),round(y-ry-8)
    overlay = Image.new("RGBA",(round(rx*2+18),round(ry*2+16)),TRANSPARENT)
    ImageDraw.Draw(overlay).ellipse((9,8,9+2*rx,8+2*ry),fill=(43,103,115,round(a*255)))
    paste(im,overlay.filter(ImageFilter.GaussianBlur(3)),l,t)


def stroke(draw, points, rgb, a, width):
    draw.line([(round(x),round(y)) for x,y in points],fill=(*rgb,round(clamp(a)*255)),
              width=max(1,round(width)),joint="curve")


def ripple(draw,x,y,rx,ry,a,part=0.,warm=False):
    col=(255,241,194) if warm else (246,238,214)
    for start,end,weight in [(0.15,math.pi*.83,1.),(math.pi*1.03,math.pi*1.58,.36)]:
        pts = []
        for i in range(21):
            ang=lerp(start,end,i/20)+part
            pts.append((x+rx*math.cos(ang),y+ry*math.sin(ang)))
        stroke(draw,pts,col,a*weight,1.5 if rx<80 else 2)


class Flow:
    def __init__(self, seed, level):
        gen=random.Random(seed)
        self.level=level
        self.lines=[]
        for _ in range(43):
            y=gen.uniform(level,665)
            x=gen.uniform(-200,1240)
            length=gen.uniform(14,92)*(y-level+300)/570
            speed=gen.uniform(15,34)*(y-level+240)/490
            self.lines.append((x,y,length,speed,gen.uniform(0,math.tau),gen.uniform(.08,.38)))

    def paint(self, draw, t, gold=False):
        for ix,(x,y,l,v,phi,a) in enumerate(self.lines):
            x=(x+v*t+260)%1480-260
            y=y+math.sin(phi+t*.51)*1.4
            strength=.29+.71*(.5+.5*math.sin(t*(.65+(ix%6)*.12)+phi))**1.8
            if gold:
                strength*= .62+.9*math.exp(-((x-(1005-.37*(y-280)))/185)**2)
            direction = -.065 if gold else -.017
            points=[(x+l*i/9,y+l*i/9*direction+math.sin(phi+i/3+t*.8)*.65) for i in range(10)]
            stroke(draw,points,(255,237,179) if gold else (242,239,207),
                   a*strength,1 if l<46 else 2)


def drawn_layer():
    layer=Image.new("RGBA",(W,H),TRANSPARENT)
    return layer,ImageDraw.Draw(layer)


def reflection(im, child, t, x, y):
    src=child.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    src=scaled(src,1.,.53).filter(ImageFilter.GaussianBlur(.85))
    px=np.asarray(src).copy()
    mask=px[:,:,3].astype(float)
    for j in range(px.shape[0]):
        offset=round(5.8*math.sin(j*.182+t*2.8)+2.5*math.sin(j*.39-t*3.5))
        px[j]=np.roll(px[j],offset,axis=0)
        mask[j]=np.roll(mask[j],offset)
    row=np.arange(len(mask))
    bars=(.15+.85*(.5+.5*np.sin(row*.31+t*1.62))**.85)*np.exp(-row/192)
    col=np.arange(px.shape[1])
    cutoff=np.clip((px.shape[1]*.68-col)/85.,0,1)
    px[:,:,:3] = (px[:,:,:3]*.69 + np.array([81,130,135])*.31).astype(np.uint8)
    px[:,:,3] = (mask*bars[:,None]*cutoff[None,:]*.49).astype(np.uint8)
    paste(im,Image.fromarray(px),x,y)


def lens(im, width=1200., left=0., top=0.):
    left=max(0.,min(W-width,left))
    height=width*(H/W)
    top=max(0.,min(H-height,top))
    return im.transform((W,H),Image.Transform.EXTENT,(left,top,left+width,top+height),
                        Image.Resampling.BICUBIC)


def title_layer():
    font=ImageFont.truetype("C:/Windows/Fonts/simkai.ttf",64)
    mask=Image.new("L",(W,H))
    pen=ImageDraw.Draw(mask)
    x=738
    for c in "纸船的故事":
        pen.text((x,82),c,anchor="lt",font=font,fill=255)
        x+=71
    rgb=Image.new("RGBA",(W,H),(56,91,87,0))
    rgb.putalpha(mask)
    return rgb


def paper_fade(frame, alpha):
    if alpha <= 0.:
        return frame
    return Image.blend(frame,Image.new("RGBA",(W,H),(*PAPER,255)),clamp(alpha))


class Film:
    def __init__(self):
        self.child_ink=ACTOR["Painting"](42)
        self.cut_ink=BOOK["Painting"](315)
        self.launch_plate=ACTOR["background"]().to_image().convert("RGBA")
        self.creek=clean_plate("nudge")
        self.sun=clean_plate("sunlight")
        self.boat=isolated(self.cut_ink,lambda p: DRAW_BOAT(p,60,60,1.6),(52,65,334,197))
        self.boat_anchor=(8,110)
        self.ducks=[]
        for i in range(11):
            amount=i/10
            self.ducks.append(self.duck_sheet(amount))
        self.title=title_layer()
        self.flows=[Flow(655,303),Flow(785,305),Flow(631,282)]
        self.fixed_child={}
        scope=ACTOR.copy()
        blink=inspect.getsource(ACTOR["child"])
        blink=blink.replace('    p.dot(762.01,224.40,2.46,3.85,"634e47",.93,.24)',
                            '    p.stroke("M 756 222 C 759 226 765 226 769 223","694c45",1.4,.85)')
        blink=blink.replace('    p.dot(760.88,223.00,0.74,0.98,"f9dfc2",.87)','')
        exec(blink,scope)
        self.blink_child=scope["child"]

    def duck_sheet(self, amount):
        x0,y0,s=95.,75.,1.60
        def draw(p):
            original=p.path
            def warp(x,y):
                gate=smooth((x-106)/84.)*smooth((86-y)/48.)
                return x+17*amount*gate,y+8*amount*gate
            def placed(data, color, opacity=.8, **kw):
                if kw.get("x") == x0:
                    tokens=BOOK["CODES"].findall(data)
                    shift=[]
                    coords=[]
                    for at,k in enumerate(tokens):
                        if k in BOOK["POINTS"]:
                            shift.append(k)
                        else:
                            coords.append(float(k))
                            if len(coords)==2:
                                shift.extend(f"{v:.4f}" for v in warp(*coords))
                                coords.clear()
                    data=" ".join(shift)
                return original(data,color,opacity,**kw)
            orig_dot=p.dot
            def placed_dot(x,y,*v,**kw):
                ax,ay=warp((x-x0)/s,(y-y0)/s)
                return orig_dot(x0+ax*s,y0+ay*s,*v,**kw)
            p.path,p.dot=placed,placed_dot
            try:
                DRAW_DUCK(p,x0,y0,s)
            finally:
                p.path,p.dot=original,orig_dot
        return isolated(self.cut_ink,draw,(82,58,490,281))

    def child(self,wrist,opening,blink=False):
        key=tuple(np.round(np.r_[wrist,opening,blink],5))
        if key not in self.fixed_child:
            def mark(p):
                actor=self.blink_child if blink else ACTOR["child"]
                actor(p,np.asarray(wrist),opening)
            self.fixed_child[key]=isolated(self.child_ink,mark,(644,87,1041,488))
        return self.fixed_child[key]

    def boat_on(self,im,x,y,s,angle,afloat=True):
        if afloat:
            shadow(im,x+82*s,y+3*s,80*s,9*s,.24)
        draw_sprite(im,self.boat,self.boat_anchor,x,y,s/1.6,angle)

    def duck_on(self, im, x,y,s,t,reach=0.,stillness=0.):
        breath=(1.-stillness)*1.25*math.sin(t*8.2)+.37*math.sin(t*2.8)
        shadow(im,x+103*s,y+115*s,98*s,12*s,.17)
        draw_sprite(im,self.ducks[int(round(reach*10))],(13,17),x,y,s/1.6,
                    sy=s/1.6*(1.+breath/90.))
        waterline=y+116*s
        glaze,pen=drawn_layer()
        # A few broken arcs follow the belly and separate it from its reflection.
        for left,right,width,a in [(25,103,1.5,.65),(116,150,1.3,.59),(38,72,1.1,.31)]:
            points=[]
            for i in range(18):
                u=i/17
                lx=lerp(left,right,u)
                dy=(-.0022*(lx-88)**2+4.2)
                if left==38:
                    dy+=4
                points.append((x+lx*s,waterline+dy*s))
            stroke(pen,points,(248,235,204),a,width*s)
        im.alpha_composite(glaze)

    def launch(self,t):
        im=self.launch_plate.copy()
        if t<3.45:
            lift=1-arc(t,.58,2.78)
            wrist=np.array([734+6*lift,370-24*lift])
            openness=0.
        else:
            wrist,openness=ACTOR["pose_at"](arc(t,3.45,5.83))
            lift=0.
        child=self.child(wrist,openness,3.03<t<3.13 or 6.17<t<6.29)
        reflection(im,child,t,646,459)
        layer,d=drawn_layer()
        self.flows[0].paint(d,t)
        slide=arc(t,3.9,7.22)
        boat_x=658+6*lift-115*slide
        boat_y=438-24*lift+5*slide
        bob=0. if t<2.78 else math.sin((t-2.78)*6.5)*1.1*math.exp(-.21*(t-2.78))
        for delay in [0.,.24,.56]:
            age=t-2.78-delay
            if 0.<age<1.83:
                ripple(d,boat_x+68,boat_y+1,46+34*age,3+6*age,.46*(1-age/1.83),delay)
        if t>3.96:
            ripple(d,boat_x+62,boat_y+3,66,4,.52)
            ripple(d,boat_x+118,boat_y+6,32,2.8,.34,.16)
        im.alpha_composite(layer)
        self.boat_on(im,boat_x,boat_y+bob,.85,math.sin(t*4.1)*1.3*slide,t>2.62)
        paste(im,child,644,87)
        zoom=arc(t,.43,3.02)
        im=lens(im,lerp(803,1183,zoom),lerp(391,11,zoom),lerp(209,0,zoom))
        # View the launch from the opposite bank to carry the downstream
        # movement left-to-right through the cuts and into the sunlight.
        im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        title_alpha=arc(t,.48,1.40)*(1-arc(t,2.78,3.68))
        if title_alpha>0:
            text=self.title.copy()
            text.putalpha(text.getchannel("A").point(lambda a: round(a*title_alpha)))
            im.alpha_composite(text)
        return paper_fade(im,1-arc(t,0.,.52))

    def middle(self,t):
        im=self.creek.copy()
        layer,d=drawn_layer()
        self.flows[1].paint(d,t)
        approach=arc(t,7.10,11.38)
        pause=clamp((t-11.18)/2.3)
        drift=arc(t,18.88,22.35)
        oscillation=math.sin(3.3*(t-11.18))*math.sin(math.pi*pause/2)*math.exp(-max(0,t-13.48)*.46)
        x=lerp(264,654,approach)+3.9*oscillation+192*drift
        y=lerp(484,442,approach)+2.1*oscillation-73*drift
        strength=bump(t,10.8,13.8)
        angle= -4*(1-approach)+8.4*oscillation+strength*3.6+9.5*drift
        angle+= bump(t,18.82,19.37)*-5.8
        ripple(d,x+73,y+5,80,5,.42)
        if approach<.99:
            ripple(d,x-9,y+4,45,3,.37,.2)
        if 11.2<t<14.:
            ripple(d,x+117,y+2,56+16*pause,5,.31+strength*.2,.32)
        # The duck comes in on a separate path, slows to look, and reaches its bill.
        if t>=13.3:
            u=arc(t,13.34,17.97)
            reach=arc(t,18.16,18.88)*(1-arc(t,18.94,19.52))
            duck_x=lerp(-280,329,u)+52*arc(t,19.10,21.9)
            duck_y=lerp(378,342,u)-4.2*reach-13*arc(t,19.1,21.9)
            wake_alpha=(1-.65*arc(t,17.23,18.09))
            for i in range(4):
                wphase=(t*1.64+i*.24)%1
                dx=duck_x+30-125*wphase
                yy=duck_y+151+11*wphase
                ripple(d,dx,yy,34+39*wphase,3+6*wphase,.54*(1-wphase)*wake_alpha,.22*i)
            im.alpha_composite(layer)
            self.duck_on(im,duck_x,duck_y,1.43,t,reach,arc(t,17.1,18.1)*.84)
            layer,d=drawn_layer()
            impulse=clamp((t-18.86)/.88)
            if 0<impulse<1:
                ripple(d,x+14,y-4,15+58*impulse,2+5*impulse,.62*(1-impulse))
        im.alpha_composite(layer)
        self.boat_on(im,x,y,1.09-.17*drift,angle)
        # A shallow follow shot opens into a held composition for the contact.
        close=1-arc(t,11.3,14.0)
        push=.09*bump(t,15.92,22.36)
        return lens(im,lerp(1184,978,close)-W*push,
                    lerp(6,95,approach)*close+W*push*.54,91*close+H*push*.63)

    def finale(self,t):
        im=self.sun.copy()
        layer,d=drawn_layer()
        self.flows[2].paint(d,t,True)
        travel=arc(t,22.36,29.64)
        x=lerp(709,902,travel)
        y=lerp(371,290,travel)+math.sin((t-22.4)*3.3)*.61*(1-travel)
        size=lerp(.58,.37,travel)
        ripple(d, x+67*size,y+3,45*size+19,3,.54,.1,True)
        ripple(d, x+30*size,y+5,25*size+11,2,.32,.22,True)
        dx=397+36*arc(t,22.38,24.35)
        dy=420-8*arc(t,22.38,24.35)
        wake=(1-arc(t,23.1,25.4))
        ripple(d,dx-9,dy+69,42+21*(1-wake),5,.36*wake+.11,.06)
        im.alpha_composite(layer)
        self.duck_on(im,dx,dy,.56,t,bump(t,22.7,23.31)*.25,arc(t,23.1,25.3))
        self.boat_on(im,x,y,size,6+3.7*travel)
        pull=arc(t,22.35,28.85)
        im=lens(im,lerp(1030,1200,pull),lerp(118,0,pull),lerp(61,0,pull))
        return paper_fade(im,arc(t,29.76,30.48))

    def frame(self,t):
        if t<7.16:
            return self.launch(t)
        if t<22.38:
            return self.middle(t)
        return self.finale(t)


def render():
    film=Film()
    if "--stills" in sys.argv:
        for t in [1.3,3.4,5.1,8.5,12.15,15.2,17.9,18.60,18.91,19.3,22.,24.,27.1,29.4]:
            film.frame(t).convert("RGB").save(HERE/f"check-{t:05.2f}.png")
        return
    command = ["ffmpeg","-y","-hide_banner","-loglevel","warning",
               "-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}",
               "-framerate",str(FPS),"-i","pipe:0","-i",str(HERE/"mix.wav"),
               "-vf","scale=1280:720:flags=lanczos,format=yuv420p",
               "-c:v","libx264","-preset","medium","-crf","17",
               "-c:a","aac","-b:a","256k","-movflags","+faststart",
               "-metadata","title=纸船的故事","-shortest",str(HERE/"The-Paper-Boat.mp4")]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as ff:
        for i in range(round(FPS*DURATION)):
            t=i/FPS
            land=film.frame(t).convert("RGB")
            ff.stdin.write(land.tobytes())
            if i%96==0:
                print(f"{t:.0f}s / {DURATION}s",flush=True)
        ff.stdin.close()
        if ff.wait():
            raise RuntimeError("Video encoding failed")


if __name__=="__main__":
    render()


