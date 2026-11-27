"""Original instrumental score and Foley for The Paper Boat."""
from pathlib import Path
import math
import wave

import numpy as np

HERE = Path(__file__).resolve().parent
DURATION = 30.5
SR = 48000
COUNT = round(SR * DURATION)
rng = np.random.default_rng(271129)
score = np.zeros((COUNT, 2), dtype=np.float64)
world = np.zeros_like(score)


def time(n):
    return np.arange(n) / SR


def pitch(note):
    return 440 * 2 ** ((note - 69) / 12)


def stereo(mix, tone, start, level, pan=0., room=0.):
    at = round(start * SR)
    theta = (pan + 1) * math.pi / 4
    for delay, gain, lr in [(0, 1., (math.cos(theta), math.sin(theta))),
                             (.044, room, (.31,.83)),(.083, room*.7, (.78,.28)),
                             (.149, room*.35, (.43,.69))]:
        off = at + round(SR*delay)
        n = min(len(tone), COUNT-off)
        if n > 0 and gain:
            mix[off:off+n] += (tone[:n]*level*gain)[:, None] * lr


def band(n, low, high):
    length = 2**math.ceil(math.log2(max(n, 2)))
    frequencies = np.fft.rfftfreq(length, 1/SR)
    noise = rng.normal(size=length)
    response = (1-np.exp(-(frequencies/max(low, 1))**2)) * np.exp(-(frequencies/high)**2)
    tone = np.fft.irfft(np.fft.rfft(noise)*response, length)[:n]
    return tone / max(np.std(tone),1e-9)


def felt(note, when, level, pan=0., dwell=1.4):
    n = round(SR*(dwell+1.8))
    t = time(n)
    f = pitch(note)
    env = (1-np.exp(-t/.012))*np.exp(-t/(.40+440/f*.14))
    env *= np.exp(-np.maximum(0,t-dwell)/.18)
    sound = np.sin(2*np.pi*f*t) + .085*np.sin(2*np.pi*f*1.0009*t)
    for partial, weight in [(2,.26),(3,.105),(4,.037),(5,.022),(7,.009)]:
        decay = np.exp(-t*(partial-1)*1.64)
        sound += weight*decay*np.sin(2*np.pi*(f*partial*(1+.00014*partial**2))*t+.4)
    hammer = .034*band(n,320,2360)*np.exp(-t/.039)
    stereo(score, env*(sound+hammer), when, level, pan, .17)


def bell(note, when, level, pan=.25):
    t = time(3*SR)
    f = pitch(note)
    attack = 1-np.exp(-t/.016)
    sig = sum(v*np.sin(2*np.pi*f*h*t)*np.exp(-t*d)
              for h,v,d in [(1,1,1.8),(2.01,.24,3.9),(3.01,.07,8.4),(4.19,.045,8)])
    stereo(score,attack*sig,when,level,pan,.27)


def bow(note, when, length, level, pan):
    t = time(round(SR*length))
    f = pitch(note)
    flutter = .0019*np.sin(2*np.pi*(4.5*t+.02*t*t))
    phase = 2*np.pi*f*(t+flutter*t/(7+t))
    body = (.75*np.sin(phase)+.16*np.sin(2*phase+.4)+.07*np.sin(3*phase))
    env = np.clip(t/.75,0,1)**1.4 * np.clip((length-t)/1.0,0,1)**1.3
    stereo(score,env*body*(.95+.05*np.sin(2*np.pi*2.3*t)),when,level,pan,.12)


# The four-note motif starts when the child lets go. The duck introduces a
# brief answering phrase, and the opening harmony returns under the sun.
melody = [
    (3.96,69,.074), (4.73,74,.076), (5.51,78,.071), (6.63,76,.060),
    (7.84,74,.067), (8.61,71,.061), (9.38,69,.056),
    (10.63,67,.053), (11.39,71,.056), (12.59,73,.047),
    (14.32,69,.056), (14.91,71,.055), (15.49,74,.057), (16.63,76,.058),
    (17.40,74,.044), (19.41,78,.076), (20.24,81,.063), (21.38,76,.057),
    (22.67,74,.072), (23.47,78,.067), (24.26,81,.061), (25.38,83,.058),
    (26.52,81,.058), (27.29,78,.046), (28.14,74,.056)
]
for when,note,level in melody:
    felt(note,when,level,.11,.75 if when<22 else 1.25)

harmonies = [
    (4.02,[50,57,62,66]), (7.80,[47,54,62,66]), (10.64,[43,55,59,62]),
    (12.94,[45,52,57,61]), (15.31,[47,54,62,66]), (17.29,[43,55,62,67]),
    (19.42,[45,52,61,64]), (22.66,[50,57,62,66]), (25.40,[43,55,59,62]),
    (27.97,[38,50,57,66])
]
for when,chord in harmonies:
    for i,note in enumerate(chord):
        felt(note,when+[0.,.10,.25,.43][i],.046 if i==0 else .029,-.28+i*.09,2.0)

for when,note,level in [(4.78,86,.014),(9.41,81,.012),(15.56,86,.014),
                        (19.35,90,.030),(22.75,86,.017),(25.41,95,.014),(28.24,86,.021)]:
    bell(note,when,level)

for when,note,length,level,pan in [(7.82,54,2.4,.018,-.34),(10.63,55,2.7,.018,.29),
    (14.48,59,2.8,.017,-.32),(16.98,55,2.3,.018,.37),(19.34,57,3.0,.025,-.28),
    (22.52,62,3.6,.023,-.31),(22.73,66,3.0,.015,.30),(25.21,59,2.9,.016,.22),
    (27.78,62,2.64,.023,-.11)]:
    bow(note,when,length,level,pan)

# Creek. Several independent layers feed both stereo channels.
t = time(COUNT)
broad = band(COUNT,240,2900)
airy = band(COUNT,1350,5700)
slow = band(COUNT,28,400)
space = band(COUNT,350,4600)
curve = (1-.22*np.exp(-((t-18.9)/1.2)**2))*(1+.084*np.sin(t*2.9)+.047*np.sin(t*9.13))
for side,sign in enumerate((-1,1)):
    world[:,side] = curve*(.016*broad+.0065*airy+.007*slow+sign*.006*space)
world *= np.clip(t/.39,0,1)[:,None] * np.clip((DURATION-t)/.80,0,1)[:,None]

def splash(start, amp, pan=0., bright=1.):
    length=.56
    n=round(SR*length)
    t=time(n)
    q=band(n,630,4450)
    burst = q*(1-np.exp(-t/.009))*np.exp(-t/(.091*bright))
    for i in range(4):
        onset=.015+i*.027
        tau=np.maximum(t-onset,0.)
        hz=rng.uniform(470,1150)*bright
        bubble=np.sin(2*np.pi*(hz*tau-320*tau*tau))*(tau>0)*(1-np.exp(-tau/.003))*np.exp(-tau/.027)
        burst+=bubble*.32
    stereo(world,burst,start,amp,pan,.09)

def peep(start, level, low, hi, length=.20, pan=.24):
    t=time(round(SR*length))
    f=low+(hi-low)*np.sin(np.pi*t/length)**1.1
    phase=2*np.pi*np.cumsum(f)/SR
    tone=(np.sin(phase)+.24*np.sin(2*phase+.4)+.08*np.sin(3*phase))
    env=np.sin(np.pi*t/length)**1.4 * (1-.24*t/length)
    stereo(world,tone*env,start,level,pan,.19)

for a in [(2.78,.062,.21), (4.05,.027,.13), (8.34,.024,-.24), (10.75,.024,.11),
          (11.92,.032,.21),(13.75,.037,-.53),(14.39,.034,-.39),(15.01,.027,-.24),
          (15.66,.025,-.15),(16.34,.024,-.04),(18.85,.063,.18),(19.21,.033,.22),
          (20.42,.023,.26),(23.37,.020,-.12),(25.31,.015,.25)]:
    splash(*a)
for args in [(1.06,.010,1840,2370,.105,-.63),(1.22,.008,2020,2530,.101,-.59),
             (14.05,.022,609,783,.16,-.44),(14.24,.020,648,840,.145,-.38),
             (16.70,.015,621,721,.19,-.10),(22.88,.011,625,752,.18,-.14),
             (26.18,.008,1910,2410,.095,.5)]:
    peep(*args)

rustle = band(round(SR*.27),1400,5500)
tr = time(len(rustle))
stereo(world,rustle*np.sin(np.pi*tr/.27)**2,3.83,.025,.25,.06)

def write_wav(path, signal):
    peak=np.max(np.abs(signal))
    signal=signal*(.85/max(peak,.85))
    with wave.open(str(path),"wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(SR)
        out.writeframes((signal*32767).astype("<i2").tobytes())

end=np.clip((DURATION-t)/1.1,0,1)**1.35
score*=end[:,None]
mix=world+score
# Preserve headroom, with the instrument transients defining the master level.
mix*= .76 / np.max(np.abs(mix))
write_wav(HERE/"mix.wav", mix)

