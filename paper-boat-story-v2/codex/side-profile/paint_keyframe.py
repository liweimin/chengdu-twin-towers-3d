"""Hand-drawn paths and procedural pigment washes for The Paper Boat."""
import math

from functools import lru_cache
import random
import re
from pathlib import Path

import aggdraw
import numpy as np
from PIL import Image, ImageFilter

W, H = 1200, 675
HERE = Path(__file__).resolve().parent
PAPER = (250, 242, 223)
CODES = re.compile(r"[MLCZ]|-?\d+(?:\.\d+)?")
POINTS = {"M": 2, "L": 2, "C": 6, "Z": 0}


@lru_cache(maxsize=128)
def rgb(hex_color):
    return np.array([
        int(hex_color[i:i+2], 16) for i in (0, 2, 4)
    ], dtype=np.float32)


def noise(rng, width, height):
    original = Image.fromarray(rng.integers(0, 256, (height, width), dtype=np.uint8))
    return np.asarray(original.resize((W, H), Image.Resampling.BICUBIC), dtype=np.float32) / 255 - .5


class Painting:
    def __init__(self, seed):
        gen = np.random.default_rng(seed)
        self.r = random.Random(seed)
        self.cloud = noise(gen, 23, 14)
        self.bloom = noise(gen, 104, 60)
        self.pulp = noise(gen, 628, 336)
        self.grain = gen.normal(0, .18, (H, W)).astype(np.float32)
        self.drift_x = noise(gen, 316, 177) * 2.15 + self.bloom * .84
        self.drift_y = noise(gen, 302, 196) * 2.30 - self.bloom * .64
        self.texture = self.cloud * .38 + self.bloom * .26 + self.pulp * .12 + self.grain * .10
        paper_tone = self.pulp * 11 + self.grain * 9 + self.cloud * 5
        self.paper = np.asarray(PAPER, dtype=np.float32) + paper_tone[:, :, None]
        self.paint = self.paper.copy()

    def path(self, data, color, opacity=.8, *, bottom=None, blur=0, edge=.25,
             pen=None, scale=1, x=0, y=0, drift=.58):
        tokens = iter(CODES.findall(data))
        segments = []
        xx, yy = [], []
        for command in tokens:
            points = [float(next(tokens)) * scale + (x if i % 2 == 0 else y)
                      for i in range(POINTS[command])]
            xx.extend(points[::2])
            yy.extend(points[1::2])
            segments.append((command, points))
        padding = 5 + int(blur * 3 + (pen or 0) * scale)
        l = max(0, math.floor(min(xx) - padding))
        t = max(0, math.floor(min(yy) - padding))
        r = min(W, math.ceil(max(xx) + padding))
        b = min(H, math.ceil(max(yy) + padding))
        if r <= l or b <= t:
            return
        mask = Image.new("L", (r-l, b-t))
        drawer = aggdraw.Draw(mask)
        outline = aggdraw.Path()
        methods = {"M": outline.moveto, "L": outline.lineto, "C": outline.curveto, "Z": outline.close}
        for command, points in segments:
            methods[command](*(point - (l if i % 2 == 0 else t) for i, point in enumerate(points)))
        if pen is None:
            drawer.path(outline, aggdraw.Brush(255))
        else:
            drawer.path(outline, aggdraw.Pen(255, pen * scale))
        drawer.flush()
        sl = np.s_[t:b, l:r]
        if blur:
            mask = mask.filter(ImageFilter.GaussianBlur(blur))
        dry = np.asarray(mask, dtype=np.float32) / 255
        if blur < 1.6 and pen is None and r-l > 12 and b-t > 9:
            # Sample the mask at subtly displaced points to show the absorbent edge of the paper.
            cols = np.arange(r-l, dtype=np.float32)[None, :] + self.drift_x[sl] * drift
            rows = np.arange(b-t, dtype=np.float32)[:, None] + self.drift_y[sl] * drift
            cols = np.clip(cols, 0, r-l-1.001)
            rows = np.clip(rows, 0, b-t-1.001)
            left = cols.astype(np.int32)
            top = rows.astype(np.int32)
            fx = cols-left
            fy = rows-top
            dry = (
                (1-fy) * ((1-fx)*dry[top,left] + fx*dry[top,left+1])
                + fy * ((1-fx)*dry[top+1,left] + fx*dry[top+1,left+1])
            )
        colored = dry * opacity * (1 + self.texture[sl] * 1.10)
        if edge:
            inside = np.asarray(mask.filter(ImageFilter.MinFilter(5)), dtype=np.float32) / 255
            pool = np.maximum(0, dry - inside) * edge * opacity
            colored *= 1 - np.minimum(pool, .29) * .35
            colored += pool * .64
        alpha = np.clip(colored, 0, 1)[:, :, None]
        ink = rgb(color)
        if bottom:
            progress = np.clip((np.arange(t, b, dtype=np.float32) - min(yy)) /
                               max(max(yy)-min(yy), 1), 0, 1)[:, None, None]
            ink = ink + (rgb(bottom) - ink) * progress
        ink = ink + self.texture[sl][:, :, None] * 18
        self.paint[sl] += (ink - self.paint[sl]) * alpha

    def dot(self, x, y, rx, ry, color, opacity=.7, tilt=0, blur=0):
        skew = rx * tilt
        self.path(f"M {x-rx:.2f} {y-skew:.2f} C {x-rx:.2f} {y-ry-skew:.2f} "
                  f"{x+rx*.62:.2f} {y-ry+skew:.2f} {x+rx:.2f} {y+skew:.2f} "
                  f"C {x+rx:.2f} {y+ry+skew:.2f} {x-rx*.72:.2f} {y+ry-skew:.2f} "
                  f"{x-rx:.2f} {y-skew:.2f} Z", color, opacity, blur=blur, edge=.09)

    def stroke(self, data, color, width, opacity=.65):
        self.path(data, color, opacity, pen=width, edge=.08)

    def brush(self, points, color, width, opacity=.7, wetness=.4):
        """Lay a single variable-width wash along a cubic brush gesture.

        Each control point gives x, y, and pressure. Deposits within one
        gesture merge on the paper before this layer meets preceding washes.
        """
        controls = np.asarray(points, dtype=np.float32)
        length = np.linalg.norm(np.diff(controls[:, :2], axis=0), axis=1).sum()
        step = np.linspace(0, 1, max(8, math.ceil(length * 2)))[:, None]
        curve = ((1-step)**3 * controls[0] + 3*(1-step)**2*step * controls[1]
                 + 3*(1-step)*step**2 * controls[2] + step**3 * controls[3])
        padding = width + 4
        l, t = np.maximum(0, np.floor(curve[:, :2].min(axis=0) - padding)).astype(int)
        r, b = np.minimum((W, H), np.ceil(curve[:, :2].max(axis=0) + padding)).astype(int)
        if r <= l or b <= t:
            return
        x_grid, y_grid = np.meshgrid(np.arange(l, r, dtype=np.float32),
                                    np.arange(t, b, dtype=np.float32))
        deposit = np.zeros_like(x_grid)
        feather = .45 + wetness * .8
        for x, y, pressure in curve:
            radius = max(.2, width * pressure * .5)
            distance = np.sqrt((x_grid - x)**2 + (y_grid - y)**2)
            dab = np.clip((radius + feather*.5 - distance) / feather, 0, 1)
            deposit = np.maximum(deposit, dab * (.55 + .45*pressure))
        area = np.s_[t:b, l:r]
        grain = self.pulp[area] * .28 + self.bloom[area] * .14
        pigment = (1 + grain * (1-wetness*.7)) * deposit
        alpha = np.clip(pigment * opacity, 0, 1)[:, :, None]
        self.paint[area] += (rgb(color) - self.paint[area]) * alpha

    def to_image(self):
        # Restore individual paper fibers above all paint layers.
        fibers = np.maximum(0, self.pulp + self.grain * .30 - .23) * .18
        image = self.paint + (self.paper - self.paint) * fibers[:, :, None]
        return Image.fromarray(np.clip(image, 0, 255).astype(np.uint8))


def wash(p, close=False):
    p.path("M -20 -20 L 1220 -20 L 1220 406 L -20 406 Z", "e6e6cb", .54,
           bottom="f5e7bd", blur=8, edge=0)
    for _ in range(21):
        x = p.r.uniform(-30, 1230)
        y = p.r.uniform(14, 220)
        if (x > 720 and x < 1065 and not close):
            continue
        size = p.r.uniform(30, 145)
        p.dot(x,y,size,p.r.uniform(31,101),p.r.choice(["a7ad79","c8ca89","b3bc8c","e5ce86"]), .25, .12, 10)
    p.path("M -20 185 C 171 196 270 151 417 173 C 535 188 625 231 754 231 "
           "C 889 236 1052 143 1220 151 L 1220 390 L -20 411 Z",
           "b6bf8b", .56, bottom="8eaf95", blur=4, edge=.09)
    p.path("M -20 256 C 143 217 291 212 411 241 C 586 290 707 291 833 245 "
           "C 983 199 1065 210 1220 207 L 1220 390 L -20 399 Z",
           "e5dcaa", .59, bottom="cbd3a1", blur=3, edge=.11)
    water = ("M -20 308 C 128 294 263 315 409 318 C 569 329 684 302 812 270 "
             "C 965 227 1089 232 1220 243 L 1220 700 L -20 700 Z")
    p.path(water, "d5dcc0", .94, bottom="6fa3a7", edge=.0)
    p.path("M -18 341 C 154 324 232 367 453 339 C 677 318 774 278 920 269 "
           "C 1042 264 1120 268 1220 248 L 1220 355 C 1003 362 1007 310 799 350 "
           "C 670 379 550 407 403 412 C 273 420 102 398 -18 422 Z",
           "82aba4", .41, bottom="739f9c", blur=5, edge=.03)
    p.path("M -25 494 C 103 446 297 464 432 439 C 650 402 784 416 908 378 "
           "C 1017 345 1126 346 1224 327 L 1224 439 C 1107 488 974 448 859 500 "
           "C 658 560 531 519 389 551 C 249 583 127 548 -25 599 Z",
           "528f96", .40, bottom="88b6ac", blur=6, edge=.02)


def glints(p, start, count=106, light=None):
    colors = ["ecedcf","f8eac0","f8efda","4a8687","77978e","a7c3b1"]
    for _ in range(count):
        y = p.r.uniform(start, H+5)
        x = p.r.uniform(-60, W)
        depth = (y-start)/(H-start)
        length = p.r.uniform(10, 105) * (.4 + depth*.7)
        bump = p.r.uniform(-6, 4) * (.4+depth)
        color = p.r.choice(colors)
        alpha = p.r.uniform(.16, .56)
        if light and abs(x-light(y)) < 160:
            color = p.r.choice(["fff2c6","f8e7ab","fff7d8"])
            alpha *= 1.33
        p.path(f"M {x:.1f} {y:.1f} C {x+length*.28:.1f} {y+bump:.1f} "
               f"{x+length*.69:.1f} {y+bump:.1f} {x+length:.1f} {y-.3:.1f} "
               f"C {x+length*.7:.1f} {y+bump+(depth+1)*1.5:.1f} "
               f"{x+length*.29:.1f} {y+bump+(depth+1)*2.2:.1f} {x:.1f} {y:.1f} Z",
               color, alpha, edge=.04)


def reeds(p, x, y, spread, height, count, soft=False):
    palette = ["5d8875", "75936d", "adb275", "416f62", "a9975d", "c2bd80"]
    for _ in range(count):
        x0 = x + p.r.uniform(-spread, spread)
        y0 = y + p.r.uniform(-spread*.19, spread*.19)
        size = height * p.r.uniform(.25, 1)
        curve = size * p.r.uniform(-.63,.64)
        w = p.r.uniform(2, 6) * (height/99)**.62
        tip = x0 + curve
        top = y0 - size
        p.path(f"M {x0:.1f} {y0:.1f} C {x0-w*2:.1f} {y0-size*.43:.1f} "
               f"{tip-curve*.33-w:.1f} {top+size*.15:.1f} {tip:.1f} {top:.1f} "
               f"C {tip-curve*.34+w:.1f} {top+size*.26:.1f} "
               f"{x0+w*.3:.1f} {y0-size*.34:.1f} {x0+w:.1f} {y0:.1f} Z",
               p.r.choice(palette), p.r.uniform(.32, .76), blur=1 if soft else .15)
        if p.r.random() < .15:
            p.dot(tip,top,3.9,6,"b59964",.62,.5,1 if soft else .1)


def shrubs(p, x, y, spread, tall, count, far=False):
    colors = ["759274","a1ac75","b3b57a","c6c38b","4e7a69","839664","c7ae76"]
    for _ in range(count):
        dx = p.r.uniform(-1, 1)
        dy = p.r.uniform(0, 1) * (1-.46*abs(dx))
        size = p.r.uniform(.045,.23) * tall
        p.dot(x + spread*dx, y - tall*dy, size*p.r.uniform(.75,1.8), size,
              p.r.choice(colors), p.r.uniform(.26,.62), p.r.uniform(-.5,.5), 2.6 if far else .5)


def willow(p, x, y, scale=1, hanging=False, colorway="green"):
    palette = {
        "green": ("658574", "a4ad70", "849661", "c0bb77"),
        "sun": ("8a9a6a", "c6b66e", "a1aa73", "cec48b"),
        "shade": ("3f7268", "739366", "557f6d", "a1aa6a"),
    }[colorway]
    direction = 1 if hanging else -1
    for shoot in range(5):
        reach = p.r.uniform(45, 119) * scale
        curl = p.r.uniform(-53, 88) * scale
        foot = x + p.r.uniform(-18, 17)*scale
        slope = p.r.uniform(-.28,.27)
        def point(t):
            return foot+curl*t*t, y+(reach*t + reach*slope*t*t)*direction
        bx, by = point(.44)
        tx, ty = point(1)
        p.stroke(f"M {foot:.2f} {y:.2f} C {foot:.2f} {by:.2f} "
                 f"{bx:.2f} {by:.2f} {tx:.2f} {ty:.2f}", palette[0], 1.15*scale, .64)
        for leaf in range(7):
            t = (leaf+2)/9.5
            ax, ay = point(t)
            side = -1 if leaf%2 else 1
            length = p.r.uniform(13,36)*scale*(1-.42*t)
            width = p.r.uniform(2.3,7.7)*scale*(1-.31*t)
            lx = ax + length*side
            ly = ay + (length*.48 + p.r.uniform(-7,3)*scale)*direction
            outline = (f"M {ax:.2f} {ay:.2f} C {ax+length*.21*side:.2f} {ay+width*direction:.2f} "
                       f"{lx-length*.3*side:.2f} {ly+width*direction:.2f} {lx:.2f} {ly:.2f} "
                       f"C {lx-length*.3*side:.2f} {ly-width*direction:.2f} "
                       f"{ax+length*.49*side:.2f} {ay-width*.62*direction:.2f} {ax:.2f} {ay:.2f} Z")
            p.path(outline,p.r.choice(palette),p.r.uniform(.46,.83),edge=.26,blur=.24)
            if leaf%3==0 and scale>.75:
                p.stroke(f"M {ax:.2f} {ay:.2f} L {lx:.2f} {ly:.2f}",palette[2],.65*scale,.56)


def current(p, strokes, tint):
    for x, y, length, bend, width, opacity in strokes:
        p.path(f"M {x} {y} C {x+length*.25} {y+bend*.32} {x+length*.72} {y+bend} "
               f"{x+length} {y+bend*.70} C {x+length*.74} {y+bend+width} "
               f"{x+length*.27} {y+bend*.32+width*.68} {x} {y} Z",
               tint,opacity,edge=.08,blur=.52,drift=.34)

def boat(p, x, y, s):
    def fill(d, col, opacity=.92, **kw):
        p.path(d,col,opacity,x=x,y=y,scale=s,drift=.19,**kw)
    def line(d, col, w, a):
        fill(d,col,a,pen=w,edge=.05)
    fill("M -6 69 C 23 59 140 58 167 67 C 204 75 101 89 19 81 C 2 79 -9 75 -6 69 Z",
         "427d83", .36, blur=3.0*s)
    fill("M 20 57 L 63 10 L 81 30 L 110 58 L 70 68 Z", "fcf2d5", 1,
         bottom="d6c4ab", edge=.13)
    fill("M 63 10 L 104 39 L 117 62 L 81 52 Z", "c9bca5", .91,bottom="aeb2a8")
    fill("M 63 10 L 81 31 L 90 50 L 74 42 Z", "ffefcc", .64, edge=.1)
    fill("M 0 39 L 66 53 L 163 31 L 137 69 L 44 75 L 16 65 Z", "fbefd3", 1,
         bottom="c6c9b7", edge=.17)
    fill("M 66 53 L 163 31 L 137 69 L 78 73 Z", "e2d8bc", .76, bottom="a9b4a7", edge=.14)
    fill("M 0 39 L 66 53 L 163 31 L 83 60 L 54 61 Z", "fff3d9", .93, edge=.01)
    line("M 1 39 L 17 65 L 44 75 L 137 69 L 162 32", "717e77", 1.15, .60)
    line("M 63 11 C 69 24 77 39 82 50 M 66 54 L 77 71", "8e887d", 1.03,.50)
    line("M 14 76 C 49 82 95 78 120 76 M 106 80 C 130 79 151 75 164 72",
         "fff1cf", 1.7, .62)


# The character stays on the right bank, seen from the side.
# Screen-space joints are shared by the pose study and finished artwork.
SHOULDER = np.array([855., 266.])
UPPER_ARM = 86.
FOREARM = 76.


def elbow_for(wrist):
    delta = wrist - SHOULDER
    distance = np.linalg.norm(delta)
    axis = delta / distance
    along = (distance**2 + UPPER_ARM**2 - FOREARM**2) / (2 * distance)
    height = math.sqrt(UPPER_ARM**2 - along**2)
    return SHOULDER + along * axis + height * np.array([axis[1], -axis[0]])


def xys(*points):
    return " ".join(f"{x:.2f} {y:.2f}" for x, y in points)


def normal(vector):
    return np.array([vector[1], -vector[0]]) / np.linalg.norm(vector)


def pose_at(t):
    # Hold, open the fingers, then bend the elbow and let the hand come back.
    if t < .42:
        k = t / .42
        k = k*k*(3-2*k)
        wrist = [734+6*k, 370-7*k]
        openness = k
    else:
        k = (t-.42)/.58
        ease = k*k*(3-2*k)
        wrist = [740+45*ease, 363+20*ease]
        openness = 1-.37*ease
    return np.array(wrist,dtype=float), openness


def near_arm(p, wrist, openness):
    elbow = elbow_for(wrist)
    u = normal(elbow-SHOULDER)
    fore_normal = normal(wrist-elbow)
    sleeve_mid = SHOULDER + .60*(elbow-SHOULDER)
    cuff_near = sleeve_mid + u*16
    cuff_far = sleeve_mid - u*15
    wrist_up = wrist - fore_normal*6.2
    wrist_dn = wrist + fore_normal*6.8
    body(p, cuff_near, cuff_far, u, elbow)
    # Outlined as an overlapping side view of the fingers, with a short thumb.
    # During release the knuckles open toward the boat and lift clear of it.
    def h(x,y):
        return wrist+np.array([x,y])
    curl = 1-openness
    arm_and_hand = (
        f"M {xys(cuff_far)} C "
        f"{xys(cuff_far+(elbow-sleeve_mid)*.40, elbow-u*10.8, elbow-fore_normal*10)} "
        f"C {xys(elbow+.44*(wrist-elbow)-fore_normal*8.4, wrist_up+.25*(elbow-wrist), wrist_up)} "
        f"C {xys(h(-7,-4), h(-16,0), h(-21,3))} "
        f"C {xys(h(-26,6), h(-30+2*curl,8+5*curl), h(-30+4*curl,11+6*curl))} "
        f"C {xys(h(-28+5*curl,13+8*curl),h(-23+8*curl,11+8*curl),h(-19+7*curl,9+6*curl))} "
        f"C {xys(h(-19+4*curl,12+4*curl),h(-21+5*curl,14+5*curl),h(-18+4*curl,15+4*curl))} "
        f"C {xys(h(-14,16),h(-10,12),h(-7,10))} "
        f"C {xys(h(-3,9),h(0,7),wrist_dn)} "
        f"C {xys(wrist_dn+.27*(elbow-wrist),elbow+.47*(wrist-elbow)+fore_normal*9.5,elbow+fore_normal*10)} "
        f"C {xys(elbow+u*12,cuff_near+(elbow-sleeve_mid)*.70,cuff_near)} Z"
    )
    p.path(arm_and_hand,"f0c39f",1,bottom="cb8e73",edge=.13)
    p.brush([(*v, w) for v,w in zip(
        (cuff_near, elbow+fore_normal*8, .49*(elbow+wrist)+fore_normal*6.0, wrist_dn),
        (.13,.73,.62,.13))], "ae7565", 4, .30, .76)
    p.brush([(*h(-18+5*curl,11+4*curl),.22),(*h(-15,9),.64),
             (*h(-11,8),.65),(*h(-9,7),.11)],"a66b5a",1.53,.56,.37)
    sleeve_trim(p,cuff_near,cuff_far,u,elbow-SHOULDER)


def body(p, cuff_near, cuff_far, u, elbow):
    # The torso and sleeve are two closed subpaths with the same winding.
    # They cover one shared wash, so the shoulder has no painted overlap seam.
    inward = elbow-SHOULDER
    neck = "M 833 239 C 843 246 852 247 865 239 "
    shell = (
        "C 875 239 888 248 895 261 C 906 283 910 306 915 327 "
        "C 921 347 933 363 937 377 C 921 393 891 395 863 385 "
        "C 854 371 844 355 837 339 C 829 322 820 305 819 287 "
        "C 814 267 821 246 833 239 Z"
    )
    shoulder_left = np.array([831.,250.])
    sleeve = (
        f"M {xys(shoulder_left)} C {xys((841,241),(863,245),(873,256))} "
        f"C {xys((882,271),cuff_near-inward*.30+u*5,cuff_near)} "
        f"C {xys(cuff_near-u*8+inward*.09,cuff_far+inward*.09,cuff_far)} "
        f"C {xys(cuff_far-inward*.38,shoulder_left+np.array([-11,23]),shoulder_left)} Z"
    )
    p.path(neck+shell+" "+sleeve,"a1bcb7",1,bottom="65858a",edge=.12)
    # A glaze follows the back rather than drawing a separate shoulder cap.
    p.path("M 869 242 C 883 248 890 259 895 278 C 903 306 901 329 915 347 "
           "C 923 358 928 369 931 377 C 914 387 899 388 882 381 "
           "C 888 360 873 349 870 325 C 868 304 878 280 873 259 Z",
           "527d86",.36,blur=2.0,edge=.02)
    p.path("M 835 251 C 843 253 850 251 861 247 C 869 261 861 280 847 289 "
           "C 837 297 829 301 817 305 C 815 285 825 270 835 251 Z",
           "c5d1bc",.38,blur=2.1,edge=.02)
    p.brush([(850,283,.11),(862,291,.60),(860,306,.75),(842,323,.18)],
            "547984",3.0,.43,.70)
    p.brush([(876,339,.09),(881,349,.57),(898,355,.85),(911,365,.19)],
            "496d77",2.2,.50,.65)
    p.brush([(861,374,.19),(877,387,.64),(907,388,.77),(926,381,.16)],
            "cad4bc",2.2,.43,.63)
    p.brush([(832,240,.33),(841,250,.83),(856,247,.85),(866,239,.27)],
            "caba8d",3.7,.83,.47)


def sleeve_trim(p,cuff_near,cuff_far,u,inward):
    # Let the sleeve trim wrap around the arm in the same plane as its opening.
    towards_elbow = inward / UPPER_ARM
    outer, inner = cuff_near+towards_elbow*5, cuff_far+towards_elbow*5
    p.path(
        f"M {xys(cuff_near-towards_elbow*3)} "
        f"C {xys(cuff_near-u*4,cuff_far+u*7+inward*.09,cuff_far-towards_elbow*3)} "
        f"L {xys(inner)} C {xys(inner+u*11+inward*.08,outer-u*8,outer)} Z",
        "d1b283",.97,bottom="aa8a64",edge=.10)


def child(p, wrist, openness):
    # Far knee and foot tuck under the hip. The nearer knee carries the weight.
    p.path("M 908 360 C 929 364 936 379 924 391 C 906 404 867 412 851 417 "
           "C 863 422 891 429 919 435 L 918 452 C 877 448 841 446 822 438 "
           "C 803 431 793 420 799 408 C 805 395 824 386 843 380 Z",
           "a4a77a",1,bottom="657762")
    p.path("M 908 433 C 922 428 934 433 940 438 C 951 441 961 447 960 454 "
           "C 957 461 943 461 931 458 L 907 451 Z","7d624e",1,bottom="5c574b")
    p.stroke("M 911 451 C 928 454 945 461 959 454","bba786",1.7,.67)
    p.path("M 891 365 C 908 363 934 371 937 388 C 940 408 917 420 889 426 "
           "C 876 430 867 433 861 439 C 886 445 922 444 957 445 L 966 464 "
           "C 938 473 911 470 880 468 C 845 467 819 460 816 444 "
           "C 813 425 834 410 851 398 C 865 384 875 371 891 365 Z",
           "b7ac7c",1,bottom="778467")
    p.path("M 824 437 C 829 422 847 412 860 405 C 850 420 847 431 852 440 "
           "C 875 451 896 452 919 451 C 898 457 863 459 843 451 Z",
           "dbcb93",.46,blur=1.4,edge=.03)
    p.path("M 819 446 C 837 459 871 461 900 462 L 958 462 "
           "C 945 469 920 470 894 468 C 854 466 824 460 819 446 Z",
           "506e5c",.32,blur=1.7)
    p.brush([(854,437,.21),(860,431,.71),(878,429,.73),(895,425,.13)],
            "637762",2.3,.57,.37)
    p.path("M 953 444 C 967 444 973 444 978 447 L 975 462 "
           "C 967 469 962 466 952 466 Z","cbbc8f",.98,bottom="a49670")
    p.path("M 975 446 C 982 445 986 448 989 451 C 1003 450 1018 456 1023 465 "
           "C 1028 473 1017 478 1004 476 L 977 471 C 968 468 967 461 969 456 Z",
           "a5785a",1,bottom="6d5748")
    p.path("M 969 462 C 982 467 1000 473 1022 468 L 1024 473 "
           "C 1019 479 1009 479 999 477 L 976 472 Z","d9c398",.98)
    p.stroke("M 991 452 L 998 457 M 999 454 L 1006 459","ebd5ab",1.5,.82)

    # The far arm drops beside the chest and rests across the far knee.
    p.path("M 822 274 C 827 278 833 286 833 293 "
           "C 829 315 817 337 807 354 C 802 368 803 380 806 389 "
           "C 812 392 823 392 828 397 C 832 400 833 404 830 406 "
           "C 828 407 825 404 823 403 C 825 408 823 411 820 410 "
           "C 817 410 816 407 814 405 C 814 409 811 411 808 409 "
           "C 806 406 806 404 803 405 C 797 409 790 405 790 399 "
           "C 790 393 792 389 794 387 "
           "C 789 374 790 361 793 349 C 797 330 802 306 809 290 Z",
           "e4b092",1,bottom="be826c",edge=.12)
    p.path("M 825 251 C 835 252 842 263 840 278 C 837 297 833 312 829 318 "
           "C 820 319 806 313 802 307 C 802 293 807 272 816 258 Z",
           "73979a",1,bottom="597d85",edge=.12)
    p.path("M 804 302 C 813 309 821 311 831 310 L 828 319 "
           "C 819 322 810 317 801 312 Z","bd9d6f",.97,bottom="9a7b57")
    p.brush([(797,398,.09),(803,395,.54),(810,398,.59),(817,403,.11)],
            "ad7663",2.0,.52,.49)
    p.brush([(804,405,.10),(812,408,.68),(822,411,.64),(833,408,.14)],
            "587767",2.7,.38,.77)
    p.path("M 837 219 C 847 211 858 215 865 227 C 868 233 872 236 873 240 "
           "C 866 251 850 252 838 247 C 835 241 832 235 827 232 Z",
           "da9b7d",1,bottom="b47762")
    near_arm(p,wrist,openness)
    p.path("M 742.62 154.41 C 760.09 128.40 804.63 121.34 835.38 137.23 C 867.87 153.67 877.44 187.85 867.39 213.52 "
           "C 852.95 248.19 831.48 269.85 798.05 268.51 C 780.41 267.15 767.27 257.61 758.31 248.23 "
           "C 752.13 245.89 744.33 243.81 742.62 238.26 C 741.04 233.53 746.75 227.65 747.73 223.34 "
           "C 735.61 204.51 728.95 178.16 742.62 154.41 Z","f5caa7",1,bottom="dfa083")
    p.path("M 753.15 236.60 C 770.93 238.76 787.26 252.78 809.39 250.94 C 828.31 244.62 839.86 233.66 848.55 225.64 "
           "C 843.23 249.73 824.06 270.20 798.05 268.51 C 777.04 266.85 762.32 252.58 753.15 236.60 Z","bd715f",.32,blur=2)
    p.dot(780.77,238.03,18.04,9.84,"e59581",.53,.18,3.6)
    p.path("M 745.89 216.99 C 732.33 210.01 720.56 198.59 722.43 184.18 L 712.97 187.34 C 708.87 177.19 715.30 165.38 724.81 157.23 "
           "C 715.34 160.39 709.29 158.86 704.73 156.26 C 718.15 146.67 726.67 127.05 739.67 120.01 "
           "C 747.25 115.49 754.41 113.52 767.50 112.28 C 767.28 105.67 764.34 102.82 759.52 98.60 "
           "C 772.65 92.37 792.17 95.09 803.99 101.52 C 836.94 94.64 861.75 109.81 872.89 132.95 "
           "C 887.69 153.02 890.65 187.42 875.06 214.80 C 866.71 230.23 856.02 236.08 845.82 229.39 "
           "C 849.18 213.91 845.42 195.42 838.22 186.59 C 822.45 202.38 801.78 208.14 786.43 205.59 "
           "C 803.52 192.92 806.45 180.00 806.11 172.58 C 788.94 195.23 762.43 206.07 747.63 201.77 "
           "C 745.04 206.33 745.25 212.94 745.89 216.99 Z","745747",1,bottom="4c4942")
    p.path("M 722.26 172.58 C 737.72 144.40 755.53 125.80 788.35 118.11 C 821.85 109.49 854.34 125.92 862.11 148.77 "
           "C 838.79 132.54 818.96 133.19 800.85 139.38 C 781.11 145.83 765.53 173.20 740.67 178.80 Z",
           "b07d52",.56,bottom="91644a",blur=2.7)
    p.path("M 742.68 180.97 C 761.77 170.47 776.56 159.00 787.21 142.37 C 782.70 166.33 767.45 185.35 748.65 192.48 Z",
           "cf9b65",.47,blur=1.6)
    p.stroke("M 724.39 175.57 C 735.38 150.58 752.72 139.53 764.74 136.80 M 776.74 170.60 C 789.35 161.13 793.86 152.94 799.74 142.87 "
             "M 817.34 117.67 C 842.83 116.13 864.79 134.23 873.63 158.57 M 835.99 162.04 C 840.89 172.06 836.72 187.66 831.44 190.99",
             "bb8e5f",1.45,.52)
    p.path("M 833.83 195.59 C 834.46 183.87 842.73 178.41 853.35 182.54 C 864.90 187.35 861.80 204.45 855.41 211.27 "
           "C 848.21 218.22 840.15 214.52 835.07 208.68 Z","eab18e",.98,bottom="cc8b72")
    p.stroke("M 849.65 206.37 C 854.81 202.23 854.20 193.19 849.09 192.34 C 845.72 192.05 844.49 194.73 844.06 197.29",
             "b67362",2.2,.69)
    p.stroke("M 755.02 222.19 C 760.30 218.86 766.36 220.39 771.86 223.67 M 756.72 211.96 C 762.81 208.50 770.49 209.77 776.80 212.93",
             "634e47",2.0,.85)
    p.dot(762.01,224.40,2.46,3.85,"634e47",.93,.24)
    p.dot(760.88,223.00,0.74,0.98,"f9dfc2",.87)
    p.stroke("M 759.77 252.15 C 765.69 252.88 771.23 251.17 774.90 248.10","9a6358",1.9,.81)


def background():
    p = Painting(42)
    wash(p, True)
    for x, y, spread, tall in [(0,320,216,173),(220,305,176,86),(397,319,134,70),(1150,258,190,145)]:
        shrubs(p,x,y,spread,tall,40,True)
    for x,y,size in [(61,300,.64),(194,302,.48),(312,311,.44),(1154,273,.60)]:
        willow(p,x,y,size,colorway="sun")
    for x in range(0, 545, 68):
        reeds(p,x,315+p.r.uniform(-12,8),36,p.r.uniform(17,44),14,True)
    p.path("M 779 500 C 861 454 940 440 987 419 C 1061 368 1090 300 1220 287 "
           "L 1220 700 L 701 700 C 740 630 778 573 779 500 Z",
           "b5a779",.48,bottom="5d8784",blur=10,edge=.03)
    p.path("M 795 457 C 886 442 950 421 982 382 C 1059 316 1106 303 1220 282 "
           "L 1220 700 L 963 700 C 969 652 999 628 995 588 C 1000 548 960 514 889 507 "
           "C 848 505 811 493 795 457 Z","ac9d72",.96,bottom="7e8a6e")
    p.path("M 817 454 C 880 440 941 407 999 369 C 1061 321 1154 299 1221 300 "
           "L 1221 588 C 1165 571 1104 518 1018 497 C 943 483 867 506 817 454 Z",
           "8a9b73",.86,bottom="9e9b66")
    p.path("M 858 475 C 907 498 1005 477 1086 516 C 1128 538 1155 571 1222 565 "
           "L 1222 595 C 1154 585 1124 557 1076 538 C 1012 511 932 514 858 475 Z",
           "b99969",.56,bottom="b4ac76",blur=1.8,edge=.15)
    glints(p,325,61)
    current(p,[(167,454,164,-7,7,.34),(301,470,115,-3,3,.56),(91,585,159,-14,5,.51),
               (220,592,150,-12,3,.43),(374,553,156,-10,4,.59),(579,494,107,-2,3,.60),
               (322,636,255,-14,7,.47),(645,516,107,8,3,.64)],"ece5bb")
    current(p,[(162,502,103,-6,4,.31),(329,515,134,-6,3,.45),(145,602,99,-7,3,.43),
               (444,603,200,2,6,.41),(669,570,121,11,5,.42)],"458286")
    reflection = [
        ("M 698 505 C 751 506 818 534 892 557 C 853 562 797 556 753 545 C 727 531 722 525 698 505 Z","537c80"),
        ("M 569 520 C 619 526 681 519 735 534 C 779 550 823 566 851 579 C 795 574 761 557 706 552 C 659 550 598 540 569 520 Z","cead92"),
        ("M 672 496 C 687 499 703 507 715 514 C 699 518 679 511 665 505 Z","e3b395"),
        ("M 745 580 C 799 568 866 570 895 599 C 905 623 876 641 830 639 C 789 639 754 612 745 580 Z","687e7b"),
        ("M 729 603 C 792 599 832 607 874 621 C 831 627 762 618 729 603 Z","a59e7e"),
    ]
    for d, c in reflection:
        p.path(d,c,.45,blur=3.2,edge=.02)
    for d in ["M 533 497 C 563 491 585 491 609 494",
              "M 545 507 C 581 510 617 510 653 505",
              "M 449 491 C 476 486 496 485 513 487",
              "M 604 537 C 653 536 702 538 761 548",
              "M 751 608 C 779 609 814 613 833 617"]:
        p.stroke(d,"f1ecd0",2.5,.63)
    p.path("M 792 450 C 805 432 825 425 846 426 C 862 423 883 420 907 424 "
           "C 940 421 986 427 1017 420 C 1050 413 1082 409 1108 421 "
           "C 1085 450 1021 470 975 467 C 932 473 850 475 815 459 Z",
           "9b967c",.98,bottom="697b6e")
    p.path("M 797 448 C 818 432 847 431 872 434 C 910 430 944 432 975 441 "
           "C 950 455 906 459 854 456 C 829 458 807 455 797 448 Z",
           "c5b698",.72,blur=.85)
    p.stroke("M 804 452 C 817 454 828 454 843 453 M 912 461 C 934 460 960 457 974 451",
             "777b67",1.3,.57)
    p.dot(882,444,51,7,"445f58",.40,.08,2.3)
    p.dot(1001,456,46,6,"455e55",.48,.12,2.1)
    p.dot(1045,437,25,5,"455e55",.39,-.08,1.5)
    p.dot(820,438,24,5,"605f55",.54,.04,1.1)
    p.path("M 614 499 C 652 497 700 497 747 499 C 729 506 697 513 673 518 "
           "C 650 514 633 506 614 499 Z","f4ddb0",.40,blur=1.8,edge=.03)
    for x,y,w,h in [(1082,483,54,89),(1178,414,55,114),(1143,564,70,118),(1006,655,65,89)]:
        reeds(p,x,y,w,h,26)
    for x,y,rx,ry in [(1090,494,23,10),(1142,507,18,7),(1059,530,13,7),(1128,571,23,8),(1026,538,12,6)]:
        p.dot(x,y,rx,ry,"b5a582",.86,-.2)
    reeds(p,54,701,71,160,27,True)
    willow(p,24,676,1.12,colorway="shade")
    willow(p,1142,542,.65,colorway="sun")
    willow(p,1053,631,.82,colorway="green")
    p.path("M -12 -17 C 56 28 108 51 190 66 C 102 60 53 47 -11 15 Z",
           "899475",.51,blur=.7)
    willow(p,62,40,1.00,True,"sun")
    willow(p,144,57,.65,True,"green")
    return p




def draw_still(scene, t):
    wrist, openness = pose_at(t)
    shift = max(0., (t-.23)/.77)
    boat(scene,658-15*shift,379+7*shift,.85)
    child(scene,wrist,openness)


def render():
    scene=background()
    base=scene.paint.copy()
    times=(0.,.42,1.)
    contact=Image.new("RGB",(1188,300),(246,237,216))
    for index,t in enumerate(times):
        scene.paint=base.copy()
        draw_still(scene,t)
        preview=scene.to_image()
        panel=preview.crop((558,74,1086,474)).resize((396,300),Image.Resampling.LANCZOS)
        contact.paste(panel,(396*index,0))
        if index==1:
            preview.save(HERE / "01-launch.png")
    contact.save(HERE / "poses.png")

    frames=[]
    for t in np.linspace(0,1,17):
        scene.paint=base.copy()
        wrist,_=pose_at(t)
        elbow=elbow_for(wrist)
        assert np.isclose(np.linalg.norm(elbow-SHOULDER),UPPER_ARM)
        assert np.isclose(np.linalg.norm(elbow-wrist),FOREARM)
        draw_still(scene,t)
        frames.append(scene.to_image().resize((768,432),Image.Resampling.LANCZOS))
    frames[0].save(HERE / "release-study.webp",save_all=True,append_images=frames[1:],
                   duration=[180]+[80]*15+[350],loop=0,quality=87,method=4)
    frames[0].save(HERE / "release-study.gif",save_all=True,append_images=frames[1:],
                   duration=[180]+[80]*15+[350],loop=0,disposal=1)


if __name__ == "__main__":
    render()

