from pathlib import Path
import math as m
import numpy as np
from scipy import signal
from scipy.io import wavfile
from duel import HITS

RATE=48000
DURATION=15
N=RATE*DURATION
rng=np.random.default_rng(57761)
mix=np.zeros((N,2))
tau=2*np.pi

def times(duration):
    return np.arange(round(duration*RATE))/RATE

def sweep(t,f0,f1,k):
    phi=f1*t+(f0-f1)*(1-np.exp(-k*t))/k
    return np.sin(tau*phi)

def noise(t,lo=0,hi=0):
    raw=rng.standard_normal(len(t))
    if lo and hi:
        normalized=(lo,hi); mode='bandpass'
    else:
        normalized=lo or hi; mode='highpass' if lo else 'lowpass'
    if normalized: raw=signal.sosfilt(signal.butter(2,normalized,btype=mode,fs=RATE,output='sos'),raw)
    return raw

def add(at,data,level,pan=0,echo=0):
    index=round(at*RATE)
    if index<0:
        data=data[-index:]; index=0
    if index>=N: return
    end=min(N,index+len(data))
    gains=np.sqrt((1+np.array([-pan,pan]))*.5)
    mix[index:end]+=data[:end-index,None]*gains[None,:]*level
    if echo:
        for dt,amount,spread in ((.064,.26,-.62),(.112,.16,.58),(.204,.085,-.40),(.311,.051,.30)):
            add(at+dt,data,level*echo*amount,spread)

def env(t,attack,decay):
    return (1-np.exp(-(t/attack)**2))*np.exp(-t*decay)

def tone(t,f):
    return np.sin(tau*f*t)

def boom(at,vol=.5,pan=0,short=False):
    t=times(.7)
    d=(sweep(t,99,37,22)+.27*sweep(t,137,50,29)+noise(t,0,200)*1.13)*env(t,.0018,12 if short else 8)
    add(at,d,vol,pan,.48)

def clank(at,power,pan):
    t=times(.57)
    strike=noise(t,1200,9800)*env(t,.0006,54)*.78
    spark=noise(t,3100,13800)*(1+.53*tone(t,62))*env(t,.002,17)*.43
    metal=np.zeros_like(t)
    for f,v,a in [(492,.17,21),(787,.21,17),(1142,.22,22),(1551,.20,12),(2147,.15,20),(2874,.11,23),(4110,.05,31)]:
        metal+=sweep(t,f*1.073,f,71)*v*env(t,.0009,a)
    add(at,strike+spark+metal,.45*power,pan,1.35)
    boom(at,.44*power,pan*.52)
    if power>.9:
        for i in range(4):
            dt=.035+i*.032+rng.uniform(0,.016)
            tt=times(.16)
            f=rng.uniform(2100,5200)
            b=(sweep(tt,f,f*.67,25)+.7*noise(tt,880,6200))*env(tt,.001,39)
            add(at+dt,b,.094*power*(1-i*.12),pan+rng.uniform(-.29,.29),.6)

def whoosh(at,dur,vol,pan1,pan2,low=False):
    t=times(dur)
    u=t/dur
    profile=(np.sin(np.pi*u)**1.6)*(1+u*.34)
    f0,f1=(72,29) if low else (159,61)
    fly=(sweep(t,f0,f1,10)*.58+sweep(t,f0*1.41,f1*1.58,13)*.26)
    rush=(noise(t,230 if low else 460,3000)*.77+noise(t,1300,7900)*.28)*(.67+u*.51)
    wave=(fly+rush)*profile
    pan=pan1+(pan2-pan1)*u
    for i in range(2):
        gains=np.sqrt((1+(i*2-1)*pan)*.5)
        index=max(0,round(at*RATE))
        m=min(len(t),N-index)
        mix[index:index+m,i]+=wave[:m]*gains[:m]*vol
    add(at+.053,wave,vol*.138,-pan2)

def ignite(at,pan,color):
    t=times(.52)
    anchor=111 if color=='blue' else 77
    g=sweep(t,anchor*.47,anchor,13)
    g+=.42*sweep(t,anchor*1.24,anchor*2.01,11)
    rev=noise(t,480,8500)*(1+.34*tone(t,39))*env(t,.004,18)
    zirp=sweep(t,889,222,6)*env(t,.009,17)
    add(at,g*env(t,.020,9)*.63+rev*.89+zirp*.44,.57,pan,.98)

# Original synthetic score. The pulse follows a four-bar phrase and briefly drops before the finish.
t=times(15)
fade=np.clip(t/.38,0,1)*np.clip((15-t)/.45,0,1)
beds=[(36.71,.25),(55,.12),(73.42,.075),(87.31,.057),(110,.045),(130.81,.039)]
air=noise(t,140,4000)
pause=1-.82*np.exp(-((t-12.13)/.48)**6)
storm=.44+.56*(.5+.5*tone(t,.085))
add(0,air*fade*storm,.048,-.34)
add(0,noise(t,110,3900)*fade*storm,.042,.42)
for i,(f,v) in enumerate(beds):
    slowly=(.5+.5*tone(t,.17+i*.06))
    a=np.sin(tau*f*t+(.31+i*.07)*tone(t,.42+i*.034))
    b=np.sin(tau*f*1.006*t+.43*tone(t,.31+i*.041))
    swells=(.79+.21*tone(t,.18+i*.036))*fade*pause
    add(0,(a*.63+b*.37)*swells*slowly,v,(i%3-1)*.46)

beat=.42857
patterns=[[36.71,36.71,43.65,32.70],[36.71,43.65,36.71,34.65],[36.71,49,43.65,34.65]]
for i,start in enumerate(np.arange(.57,11.94,beat)):
    root=patterns[(i//8)%3][(i//2)%4]
    if i%4 in (0,2):
        boom(start,.23 if i>1 else .17,0,True)
    for j in range(4):
        at=start+j*beat/4
        tt=times(.17)
        f=root*(2 if j!=2 else 3)
        bass=(tone(tt,f)+.36*tone(tt,f*2+.5)+.08*tone(tt,f*3))*env(tt,.005,17)
        add(at,bass,.128 if j in (0,2) else .075,(-1)**j*.12)
        if i>4 and ((j+i)%3==0 or j==2):
            hi=noise(tt,2900,11400)*env(tt,.0015,37)+.34*tone(tt,1500)*env(tt,.001,55)
            add(at,hi,.062 if j==2 else .043,(-1)**i*.43,.34)
    if i%4 in (1,3) and i>2:
        tt=times(.28)
        snare=noise(tt,540,6800)*env(tt,.001,19)+.49*sweep(tt,190,125,27)*env(tt,.001,24)
        add(start,snare,.15,(-1)**i*.19,.84)
    if i in (7,11,15,19,23,25):
        tt=times(.45)
        note=root*4*(1.5 if i%3 else 1)
        chime=(tone(tt,note)+.44*tone(tt,note*2.01)+.24*tone(tt,note*2.99))*env(tt,.006,9)
        add(start+.075,chime,.083,(-1)**i*.36,1.1)

ignite(.12,.52,'red')
ignite(.28,-.49,'blue')
for a in [.91,1.09,1.24,3.10,3.86,3.99,4.11,6.28,6.38,7.52,7.67,7.82,8.74,9.84,10.49,10.66,10.79,13.20]:
    tt=times(.17)
    foot=sweep(tt,122,51,38)*.80+noise(tt,270,5400)*.43
    add(a,foot*env(tt,.0015,28),.11,m.sin(a*2.2)*.48,.32)

for at,dur,vol,left,right,low in [
(.71,.46,.27,-.65,.52,True),(1.16,.29,.32,.67,-.37,False),(1.62,.27,.25,.61,-.27,False),
(2.04,.27,.25,-.53,.43,False),(2.40,.24,.30,.48,-.33,False),(2.91,.49,.40,-.75,.52,True),
(3.34,.46,.36,-.35,.78,False),(3.98,.30,.28,.54,-.23,False),(4.47,.29,.29,.6,-.41,True),
(5.11,.30,.28,-.45,.25,False),(5.80,.55,.58,0,.35,True),(6.17,.52,.32,-.35,.55,True),
(7.49,.31,.31,.60,-.2,True),(7.87,.32,.30,.65,-.4,False),(8.64,.51,.41,-.53,.49,True),
(9.34,.53,.52,.26,.71,False),(9.43,.54,.29,.56,-.65,True),(10.47,.39,.39,-.52,.43,True),
(11.15,.20,.26,.60,-.38,False),(11.41,.22,.26,-.52,.37,False),(11.68,.25,.25,.37,-.53,False),
(12.28,.45,.46,-.47,.49,True),(12.64,.43,.48,-.38,.69,False),(12.87,.42,.23,.42,.71,False),
]:
    whoosh(at,dur,vol,left,right,low)
for at,x,y,power in HITS:
    clank(at,power,(x-480)/375)
boom(5.81,.33)
boom(9.852,.22,.36)
boom(12.71,.38,.14)
tt=times(.49)
lock=(noise(tt,800,8900)*.83+sweep(tt,168,140,4)*.53)*(1+.62*tone(tt,46))*env(tt,.02,.7)*np.clip((.49-tt)*26,0,1)
add(5.36,lock,.29,.02,.77)
tt=times(1.53)
arc=(noise(tt,700,10600)*(.61+.47*tone(tt,61))+.50*sweep(tt,92,142,5)*(1+.65*tone(tt,29)))*np.clip(tt*12,0,1)*np.clip((1.53-tt)*12,0,1)
add(6.70,arc,.395,-.07,.49)
for i in range(22):
    dt=rng.uniform(.05,1.4)
    tt=times(.16)
    f=rng.uniform(210,500)
    crack=(sweep(tt,f,f*.66,22)*.48+noise(tt,760,11000))*env(tt,.001,40)
    add(6.72+dt,crack,rng.uniform(.055,.2),rng.uniform(-.48,.61),.42)

# Drop to the near-field blade hum before the decisive pass.
tt=times(1.00)
heartbeat=sweep(tt,65,42,8)*env(tt,.008,8)
add(11.93,heartbeat,.23,0)
add(12.29,heartbeat,.23,0)
tt=times(.43)
off=(sweep(tt,156,36,17)*.99+noise(tt,460,6600)*.57)*env(tt,.002,15)
add(13.03,off,.25,.65,.69)
add(14.37,off,.32,-.21,.48)

for i,f in enumerate([55,82.41,110,130.81,164.81,220]):
    tt=times(2.15)
    chord=(tone(tt,f)+.22*tone(tt,f*2.004))*env(tt,.43,1.29)
    add(12.89+i*.026,chord,.12-i*.012,(i%3-1)*.37,.4)
final_fade=np.clip((15-t)/.19,0,1)
mix*=final_fade[:,None]
mix=np.tanh(mix*.84)
mix*=.933/max(np.abs(mix).max(),.001)
wavfile.write(str(Path(__file__).with_name("sound.wav")),RATE,np.round(mix*32767).astype(np.int16))
