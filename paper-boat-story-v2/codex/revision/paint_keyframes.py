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

    def save(self, name):
        # Restore individual paper fibers above all paint layers.
        fibers = np.maximum(0, self.pulp + self.grain * .30 - .23) * .18
        image = self.paint + (self.paper - self.paint) * fibers[:, :, None]
        Image.fromarray(np.clip(image, 0, 255).astype(np.uint8)).save(HERE / name)


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


def duck(p, x, y, s):
    def fill(d, col, opacity=.9, **kw):
        p.path(d,col,opacity,x=x,y=y,scale=s,**kw)
    fill("M -42 112 C 7 102 89 104 169 100 C 254 106 191 126 119 134 "
         "C 53 142 6 131 -42 112 Z","4e8690",.43,blur=4*s)
    fill("M -21 110 C 23 116 37 117 76 115 M -43 120 C 7 129 41 126 56 125 "
         "M 154 113 C 174 113 190 112 208 106","f4edd1",.68,pen=2.4,edge=.04)
    fill("M 13 65 C 31 72 40 56 62 51 C 82 45 98 51 111 64 C 120 60 125 51 125 43 "
         "C 114 34 115 13 127 4 C 138 -5 161 -4 174 6 C 182 12 187 21 186 33 "
         "C 187 45 181 57 174 66 C 175 87 159 112 127 116 "
         "C 93 125 49 119 32 103 C 20 91 17 84 13 65 Z","f5d38a",1,bottom="d49a59")
    fill("M 32 69 C 62 56 89 51 108 66 C 119 74 125 85 148 79 "
         "C 141 97 124 109 97 110 C 64 111 45 98 32 69 Z","ffe7a8",.69,bottom="e0ac66",edge=.15)
    fill("M 41 75 C 62 66 91 67 106 80 C 103 100 69 103 51 91 "
         "C 43 88 42 82 35 81 Z","f4cb81",.90,bottom="d5a160",edge=.27)
    fill("M 51 76 C 72 69 91 72 98 80 C 85 86 66 84 51 76 Z","ffe9ac",.60,blur=1*s)
    fill("M 174 31 C 189 30 195 30 203 34 C 208 34 212 37 212 40 "
         "C 210 46 195 51 179 49 C 174 46 171 39 174 31 Z","ecaa60",.98,bottom="c4784e")
    fill("M 178 40 C 190 42 201 42 211 39","9b694e",.63,pen=1.15,edge=.05)
    fill("M 128 23 C 130 9 145 3 155 5 C 145 10 142 20 128 23 Z",
         "fff0b8",.84,blur=.55*s,edge=.04)
    fill("M 141 36 C 145 31 155 34 159 39 C 164 46 149 48 142 43 Z",
         "e6a16f",.48,blur=1.3*s)
    p.dot(x+163*s,y+23*s,3.3*s,4.0*s,"4e4940",.99,-.10)
    p.dot(x+164*s,y+21.5*s,1.14*s,1.13*s,"fff0cf",.96)
    fill("M 136 3 C 140 -3 146 -5 149 -6 M 142 3 C 147 -3 151 -4 154 -3",
         "c49858",.67,pen=1.55,edge=.05)
    fill("M 28 107 C 65 123 111 125 140 116 M 75 127 C 104 130 122 126 137 124",
         "f9eed1",.72,pen=1.9,edge=.04)

def child(p):
    def arm_x(x):
        return x + 56 * min(1, max(0, (770 - x) / 273))

    def arm_path(path):
        coordinate = 0
        result = []
        for token in CODES.findall(path):
            if token in POINTS:
                coordinate = 0
            else:
                if coordinate % 2 == 0:
                    token = f"{arm_x(float(token)):.2f}"
                coordinate += 1
            result.append(token)
        return " ".join(result)

    # The hips are over the heels. Draw the farther foot and shin first.
    p.path("M 943 350 C 956 339 979 345 989 361 C 999 378 996 402 1013 418 "
           "C 1011 429 998 434 983 431 C 964 412 954 388 939 374 Z",
           "889077",1,bottom="647c6e")
    p.path("M 983 416 C 993 421 1007 421 1013 415 C 1020 416 1027 428 1027 436 "
           "C 1027 444 1019 447 1006 447 L 963 447 C 952 447 946 443 949 436 "
           "C 953 428 966 429 976 426 Z","7c6552",1,bottom="535d54")
    p.stroke("M 949 441 C 967 445 1001 445 1026 439","c1ad8c",2.4,.76)
    # The near thigh points toward the raised knee and the shin folds back down.
    p.path("M 936 332 C 951 332 969 343 970 359 C 971 378 958 391 941 399 "
           "C 948 413 964 427 974 440 L 948 456 "
           "C 922 443 907 421 892 408 C 861 406 840 387 844 363 "
           "C 848 344 868 328 890 334 C 906 338 918 337 936 332 Z",
           "a9a174",1,bottom="697f6b")
    p.path("M 852 365 C 852 349 869 340 886 340 C 902 347 916 353 929 358 "
           "C 920 373 894 386 870 377 Z","c9ba85",.54,blur=1.3)
    p.path("M 862 379 C 870 393 883 396 898 393 C 919 388 928 381 935 371 "
           "C 932 393 914 405 892 405 C 880 403 869 392 862 379 Z",
           "71866a",.50,blur=1.5)
    p.stroke("M 855 358 C 859 349 869 345 875 345","e3c990",1.8,.64)
    p.stroke("M 895 396 C 910 398 923 395 933 386 M 937 409 C 940 419 953 426 956 433",
             "536e63",2.6,.65)
    p.path("M 945 440 C 952 442 966 436 972 432 L 979 442 "
           "C 973 449 961 454 948 455 Z","c8b786",1,bottom="a59b77")
    p.path("M 950 449 C 958 450 969 444 978 442 C 982 447 990 455 988 463 "
           "C 987 470 978 474 962 474 L 908 472 C 895 471 892 466 899 460 "
           "C 905 452 920 453 930 454 C 937 454 945 452 950 449 Z",
           "ad7d5f",1,bottom="735c50")
    p.path("M 899 463 C 922 469 958 469 987 461 L 987 469 "
           "C 969 475 916 476 899 470 Z","cfbb94",.97)
    p.stroke("M 926 455 L 935 460 M 934 453 L 944 460 M 942 451 L 952 458",
             "f0d6a3",1.8,.88)
    p.path("M 856 225 C 885 213 919 223 939 244 C 966 272 973 302 978 325 "
           "C 958 347 928 359 901 351 C 876 352 850 337 832 315 "
           "C 818 300 837 245 856 225 Z",
           "a0bcbc",1,bottom="537985")
    p.path("M 901 235 C 928 248 944 266 953 292 C 959 314 949 334 927 350 "
           "C 955 347 969 336 978 325 C 973 302 966 273 939 244 "
           "C 928 232 911 227 901 235 Z","417481",.44,edge=.11)
    # A weight-bearing hand, with fingers spread on the bank.
    p.path("M 918 308 C 929 303 945 306 949 316 C 938 341 917 358 902 375 "
           "C 884 395 874 413 857 422 C 853 429 850 432 845 435 "
           "C 838 435 843 428 846 423 C 839 425 838 437 830 438 "
           "C 825 438 827 430 833 424 C 827 428 826 436 819 436 "
           "C 814 434 824 423 827 419 C 820 425 817 429 812 427 "
           "C 808 425 817 417 824 414 C 832 409 844 409 849 406 "
           "C 867 385 876 363 892 347 C 904 332 907 322 918 308 Z",
           "e5b28c",1,bottom="bf7f64")
    p.stroke("M 830 426 C 834 420 838 417 845 415 M 839 429 C 843 422 849 418 853 417",
             "a46a5a",1.35,.65)
    p.path("M 916 271 C 931 267 953 278 961 292 C 960 309 953 326 943 338 "
           "C 932 344 910 336 905 321 C 904 304 906 283 916 271 Z",
           "83a5a8",1,bottom="567a87")
    p.path("M 902 318 C 909 328 930 337 944 332 L 941 344 "
           "C 929 350 905 339 899 331 Z","c8a671",.98,bottom="a88760")
    p.path("M 842 199 C 862 204 887 217 887 233 C 880 250 851 260 825 249 "
           "C 805 240 817 208 842 199 Z","d18c70",1,bottom="a96856")
    p.path("M 736 119 C 762 91 817 91 851 116 C 887 142 892 185 875 214 "
           "C 851 253 821 275 781 267 C 760 262 746 248 737 235 "
           "C 730 231 721 227 720 220 C 719 214 727 208 729 203 "
           "C 718 178 715 145 736 119 Z","f5caa7",1,bottom="dfa083")
    p.path("M 733 220 C 754 226 771 246 798 248 C 822 244 838 233 850 225 "
           "C 839 253 812 274 781 267 C 756 261 741 241 733 220 Z","bd715f",.32,blur=2)
    p.dot(766,227,22,12,"e59581",.53,.18,3.6)
    p.path("M 728 195 C 713 184 701 168 706 151 L 694 153 C 691 140 701 127 714 119 "
           "C 702 121 695 118 690 114 C 708 105 722 83 739 77 "
           "C 749 73 758 72 774 73 C 775 65 772 61 767 55 "
           "C 784 50 807 57 820 67 C 861 65 888 88 897 118 "
           "C 911 145 908 187 884 217 C 871 234 857 239 846 229 "
           "C 853 211 852 188 845 176 C 823 192 797 195 779 189 "
           "C 802 177 808 162 809 153 C 784 177 750 185 733 177 "
           "C 729 182 728 190 728 195 Z","745747",1,bottom="4c4942")
    p.path("M 708 137 C 732 106 757 87 798 84 C 840 80 876 106 881 135 "
           "C 856 111 832 108 809 112 C 784 116 760 146 729 148 Z",
           "b07d52",.56,bottom="91644a",blur=2.7)
    p.path("M 731 151 C 756 142 776 131 792 113 C 782 141 760 161 736 166 Z",
           "cf9b65",.47,blur=1.6)
    p.stroke("M 710 141 C 728 113 751 103 766 102 M 774 145 C 791 136 798 127 807 116 "
             "M 833 89 C 864 92 887 118 893 149 M 847 146 C 851 159 843 177 836 180",
             "bb8e5f",1.45,.52)
    p.path("M 838 186 C 841 172 852 167 864 174 C 877 182 870 202 861 209 "
           "C 851 216 842 210 837 202 Z","eab18e",.98,bottom="cc8b72")
    p.stroke("M 855 202 C 862 198 863 187 857 185 C 853 184 851 187 850 190",
             "b67362",2.2,.69)
    p.stroke("M 738 203 C 745 200 752 203 758 208 M 742 191 C 750 188 759 191 766 196",
             "634e47",2.0,.85)
    p.dot(746,207,3.0,4.7,"634e47",.93,.24)
    p.dot(744.9,205.1,.9,1.2,"f9dfc2",.87)
    p.stroke("M 738 240 C 745 242 752 241 757 238","9a6358",1.9,.81)
    p.path(arm_path("M 795 302 C 780 323 754 342 721 353 C 675 370 613 376 564 381 "
           "C 550 381 546 380 534 385 L 507 401 C 499 406 494 415 497 421 "
           "C 504 425 511 416 517 412 C 523 408 529 408 533 406 "
           "C 531 412 521 413 521 421 C 523 427 530 424 536 421 "
           "C 548 414 559 410 566 402 C 624 401 687 395 730 381 "
           "C 781 365 807 347 825 322 Z"),"efbf9b",1,bottom="cd886e")
    p.stroke(arm_path("M 554 401 C 545 408 535 412 529 417 M 511 402 C 518 397 528 394 536 391"),
             "b77762",1.75,.57)
    p.path("M 867 253 C 898 255 900 281 884 308 C 871 331 830 354 803 351 "
           "C 783 345 769 319 779 306 C 806 292 815 281 832 266 C 845 255 853 252 867 253 Z",
           "8cacaa",1,bottom="567c85")
    p.path("M 797 307 C 815 294 831 277 848 267 C 856 263 864 263 873 267 "
           "C 855 280 834 294 822 311 C 815 319 804 321 797 307 Z",
           "a5c8bf",.53,blur=2.1,edge=.1)
    p.path("M 785 305 C 780 321 793 339 808 348 C 800 358 786 361 778 355 "
           "C 765 347 760 334 761 324 C 761 319 771 311 785 305 Z",
           "d7b67b",.99,bottom="aa895e")
    p.stroke("M 799 340 C 832 334 849 322 870 300 M 889 283 C 891 270 886 263 876 257",
             "496f77",2.0,.58)


def launch():
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
        ("M 579 494 C 590 493 607 503 624 512 C 609 516 588 507 570 505 Z","e3b395"),
        ("M 745 580 C 799 568 866 570 895 599 C 905 623 876 641 830 639 C 789 639 754 612 745 580 Z","687e7b"),
        ("M 729 603 C 792 599 832 607 874 621 C 831 627 762 618 729 603 Z","a59e7e"),
    ]
    for d, c in reflection:
        p.path(d,c,.45,blur=3.2,edge=.02)
    for d in ["M 519 497 C 550 489 598 491 626 494",
              "M 545 507 C 581 510 617 510 653 505",
              "M 449 491 C 476 486 496 485 513 487",
              "M 604 537 C 653 536 702 538 761 548",
              "M 751 608 C 779 609 814 613 833 617"]:
        p.stroke(d,"f1ecd0",2.5,.63)
    p.path("M 810 447 C 825 426 843 424 851 436 C 865 425 899 409 937 410 C 978 411 999 430 1021 450 C 991 477 925 486 873 471 C 846 469 823 460 810 447 Z",
           "978975",.98,bottom="767d70")
    p.path("M 824 447 C 843 437 850 440 857 451 C 887 432 912 429 937 433 C 958 435 969 440 977 450 "
           "C 949 457 907 461 857 451 Z","c1b397",.65,blur=1.1)
    p.dot(936,468,104,9,"5e7564",.35,-.09,3.5)
    p.dot(837,434,33,5,"6c7162",.49,.12,2.2)
    child(p)
    p.path("M 496 498 C 534 494 595 495 647 497 C 620 502 586 513 555 516 "
           "C 526 512 515 505 496 498 Z","f5dfb5",.33,blur=2.1,edge=.02)
    boat(p,481,410,1.15)
    # Let the visible fingertip overlap the paper at the fold.
    p.path("M 561 408 C 559 412 558 418 554 421 C 551 422 551 418 554 413 Z",
           "e1a787",.93)
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
    p.save("01-launch.png")


def nudge():
    p = Painting(215)
    wash(p)
    for x,y,s,h in [(0,302,235,130),(175,311,176,123),(375,316,143,78),
                    (1084,249,135,60),(1197,262,137,96)]:
        shrubs(p,x,y,s,h,42,True)
    p.path("M -20 292 C 79 269 169 284 242 302 C 270 311 301 320 337 327 "
           "C 290 346 224 359 151 355 L -20 369 Z","9b9f73",.69,bottom="788f7b",blur=2)
    p.path("M -20 319 C 72 315 106 302 178 315 C 231 326 269 329 334 327 "
           "C 290 347 219 357 132 358 L -20 362 Z","b5b180",.73,bottom="8e9579",blur=1)
    for x,y,s,h in [(18,331,40,72),(124,318,62,57),(213,328,60,43),
                    (872,401,42,82),(932,397,28,70),(970,382,33,52)]:
        reeds(p,x,y,s,h,25,x<260)
    p.path("M 785 417 C 862 402 936 403 1016 383 C 1094 360 1152 360 1220 368 "
           "C 1060 394 1105 434 940 444 C 853 450 805 444 785 417 Z",
           "a5b797",.53,blur=4)
    p.path("M 821 304 C 926 278 1034 274 1220 270 L 1220 316 "
           "C 1079 311 1052 342 899 355 C 852 357 821 333 821 304 Z",
           "f8e4a7",.62,blur=8)
    glints(p,315,82,lambda y: 1085 - (y-325)*.45)
    current(p,[(72,494,162,-6,5,.51),(140,533,131,-2,3,.57),(465,472,185,-22,5,.37),
               (620,542,166,-6,4,.48),(731,505,181,-17,6,.63),(844,415,184,-23,5,.47),
               (920,476,185,-14,5,.56),(789,601,253,-17,6,.51)],"f3e5b7")
    current(p,[(98,506,218,-1,4,.44),(208,574,202,4,5,.44),(498,553,158,-7,5,.38),
               (631,503,116,-13,4,.52),(870,505,214,-23,5,.43)],"49878d")
    for d in ["M 245 506 C 298 505 341 521 390 519",
              "M 271 525 C 306 528 339 534 369 533",
              "M 647 454 C 671 464 711 469 744 462",
              "M 788 458 C 821 454 857 442 878 437",
              "M 810 467 C 840 462 855 454 880 453"]:
        p.stroke(d,"fbedd0",2.2,.65)
    duck(p,348,345,1.46)
    boat(p,654,357,1.23)
    for d in ["M 649 454 C 656 454 662 455 670 456","M 663 462 C 675 464 687 465 700 465"]:
        p.stroke(d,"f9ecd0",1.9,.73)
    for x,y,s,h in [(1161,669,47,129),(1190,630,26,111),(30,680,60,111)]:
        reeds(p,x,y,s,h,22,True)
    willow(p,19,637,.84,colorway="shade")
    willow(p,1155,668,1.02,colorway="sun")
    p.save("02-nudge.png")


def sunlight():
    p = Painting(119)
    p.path("M -30 -30 L 1230 -30 L 1230 380 L -30 380 Z",
           "e9d6a3",.61,bottom="fff1c6",blur=9,edge=0)
    p.dot(854,107,272,129,"fff8d9",.86,-.07,42)
    p.dot(898,110,86,79,"fff6d1",.81,0,17)
    for x,y,s,h in [(55,295,260,240),(245,291,190,191),(403,273,140,143),
                    (536,268,177,105),(1085,253,176,162),(1181,236,150,164)]:
        shrubs(p,x,y,s,h,66,True)
    for x,y,lean,col in [(36,306,32,"7c8d70"),(130,293,43,"8a9978"),
                         (188,297,17,"a6a379"),(1113,240,18,"a5a480"),(1177,264,-16,"829579")]:
        p.path(f"M {x-8} {y} C {x-8} {y-106} {x+lean-9} 18 {x+lean} -20 "
               f"L {x+lean+12} -20 C {x+lean+8} 63 {x+10} {y-80} {x+7} {y} Z",
               col,.45,blur=2.3)
    p.path("M -25 274 C 158 270 278 316 443 294 C 616 273 687 237 782 229 "
           "C 861 215 958 226 1027 207 C 1098 187 1161 183 1225 196 L 1225 699 L -25 700 Z",
           "d6ddbd",1,bottom="629b9f",edge=.06)
    p.path("M 1231 210 C 1060 189 999 225 920 243 C 802 269 733 263 641 292 "
           "C 514 338 452 375 336 402 C 463 410 598 386 724 344 "
           "C 856 304 939 281 1012 273 C 1086 263 1156 263 1230 252 Z",
           "8db4a3",.56,bottom="83aaa2",blur=7,edge=.02)
    p.path("M -24 501 C 165 432 393 511 590 473 C 772 439 882 390 1021 382 "
           "C 1094 376 1157 387 1226 375 L 1226 472 C 1124 501 1061 478 947 518 "
           "C 777 578 592 616 435 605 C 255 592 184 555 -24 617 Z",
           "547e8c",.44,bottom="5b9698",blur=10,edge=.01)
    p.path("M 865 205 C 928 217 992 208 1030 204 C 935 243 932 268 966 281 "
           "C 1033 307 1010 331 929 374 C 841 420 909 446 1015 460 "
           "C 1073 469 1075 511 1024 543 C 959 579 884 621 881 696 "
           "L 530 700 C 499 635 698 527 684 490 C 665 456 583 450 670 408 "
           "C 755 366 828 337 847 315 C 859 308 802 285 808 275 C 828 247 912 221 865 205 Z",
           "f2dfa0",.76,bottom="f7e3ac",blur=19,edge=.02)
    p.path("M 893 223 C 949 211 983 211 1029 210 C 950 229 887 263 882 276 "
           "C 869 293 923 298 924 308 C 915 330 868 351 800 380 "
           "C 744 403 732 420 747 428 C 772 441 844 447 857 469 "
           "C 895 534 725 550 694 634 L 589 675 C 632 579 796 516 787 480 "
           "C 787 461 688 461 683 433 C 677 409 803 360 847 332 C 876 314 869 311 850 301 "
           "C 814 278 830 266 893 223 Z","fff2bd",.60,blur=9,edge=.01)
    p.path("M -20 258 C 179 265 218 313 380 297 C 537 278 591 243 720 239 "
           "C 628 262 527 322 414 347 C 264 381 120 323 -20 342 Z",
           "aab48a",.86,bottom="829b82",blur=2)
    p.path("M 1224 188 C 1154 166 1063 180 987 214 C 1076 193 1136 214 1224 232 Z",
           "a9ab7a",.68,blur=3)
    for x,y,s,h in [(45,310,99,78),(246,329,73,58),(425,317,45,48),(552,289,68,35),
                    (1110,208,64,37),(1198,222,73,52)]:
        reeds(p,x,y,s,h,30,True)
    glints(p,281,98,lambda y: 965 - (y-270)*.58)
    current(p,[(402,386,178,-24,5,.53),(542,438,199,-22,4,.70),(665,394,126,-16,4,.60),
               (776,331,150,-21,3,.63),(842,317,106,-12,2,.64),(665,508,231,-26,6,.66),
               (516,567,183,-16,5,.53),(677,572,262,-26,8,.72),(811,601,151,-15,5,.52)],"fff0bf")
    current(p,[(38,438,245,13,7,.41),(166,506,182,12,4,.55),(302,559,187,6,5,.44),
               (478,522,172,-3,4,.53),(911,524,151,-18,4,.52),(1012,553,159,-11,4,.42)],"498089")
    for d in ["M 756 353 C 784 349 818 342 850 340",
              "M 724 367 C 777 368 819 356 862 357",
              "M 695 378 C 744 380 783 373 810 372",
              "M 814 379 C 839 376 867 368 893 368",
              "M 708 416 C 747 416 773 401 803 399",
              "M 593 543 C 667 544 702 522 756 522"]:
        p.stroke(d,"fff2c9",2.0,.79)
    duck(p,392,424,.55)
    boat(p,724,323,.54)
    p.path("M -30 556 C 63 537 111 551 181 570 C 270 587 390 631 425 701 L -30 701 Z",
           "7c9a7a",.96,bottom="50756a")
    p.path("M -30 617 C 51 580 164 605 242 631 C 302 646 342 668 376 701 L -30 701 Z",
           "759069",.78,bottom="426a60",blur=1)
    for x,y,s,h in [(25,622,62,142),(135,648,68,108),(244,695,68,124),(1161,702,65,83)]:
        reeds(p,x,y,s,h,31,True)
    for _ in range(35):
        x = p.r.uniform(-10,302)
        y = p.r.uniform(612,684)+x*.16
        p.dot(x,y,p.r.uniform(3,17),p.r.uniform(2,5),
              p.r.choice(["a1aa77","b6ad73","50786a","648365"]),.59,-.3,.4)
    willow(p,29,613,1.02,colorway="shade")
    willow(p,96,655,1.17,colorway="shade")
    willow(p,232,675,.78,colorway="sun")
    p.path("M -15 -15 C 63 14 124 4 171 13 C 227 24 265 43 304 54 "
           "C 239 45 204 31 160 26 C 92 20 52 28 -15 6 Z","617f6a",.58,blur=.72)
    willow(p,71,17,1.29,True,"shade")
    willow(p,153,19,1.11,True,"sun")
    p.save("03-sunlight.png")


if __name__ == "__main__":
    launch()
    nudge()
    sunlight()

