"""Deterministic stereo score and Foley for the 55-second print."""
import math
import numpy as np
from scipy.io import wavfile
from scipy.signal import sosfilt, butter, fftconvolve

rate=48000
duration=55
mix=np.zeros((rate*duration,2),dtype=np.float32)
rng=np.random.default_rng(1832)
def hz(midi): return 440*2**((midi-69)/12)
def clock(seconds): return np.arange(round(seconds*rate))/rate
def add(at,a,pan=0):
    start=round(at*rate)
    n=min(len(a),len(mix)-start)
    if n<=0:return
    p=(pan+1)*math.pi/4
    mix[start:start+n,0]+=a[:n]*math.cos(p)
    mix[start:start+n,1]+=a[:n]*math.sin(p)
def envelope(t,attack,decay):
    return np.minimum(1,t/attack)**1.6*np.exp(-t/decay)
def string(at,midi,amp,pan=0,long=False):
    t=clock(3.6 if long else 2.2)
    f=hz(midi)
    a=np.zeros_like(t)
    for i,amp0 in enumerate([1,.42,.34,.18,.11,.060,.045,.018,.014],1):
        offset=rng.uniform(0,2*np.pi)
        tail=(1.03 if long else .72)/(i**.77)
        a+=amp0*np.sin(2*np.pi*f*i*(1+i*.00024)*t+offset)*envelope(t,.010,tail)
    click=sosfilt(butter(2,[700,3100],fs=rate,btype='bandpass',output='sos'),rng.normal(0,1,len(t)))
    a+=.16*click*envelope(t,.002,.035)
    add(at,amp*a,pan)
def bell(at,midi,amp,pan):
    t=clock(4.5);f=hz(midi);a=np.zeros_like(t)
    for ratio,a0,d in [(1,1,1.31),(2,.17,.97),(2.72,.12,.39),(3.71,.075,.19),(5.31,.021,.13)]:
        a+=a0*np.sin(2*np.pi*f*ratio*t+.18)*envelope(t,.018,d)
    add(at,amp*a,pan)
def bed(at,seconds,notes,amp):
    t=clock(seconds)
    swell=np.sin(np.pi*np.minimum(1,t/seconds))**1.45
    for k,midi in enumerate(notes):
        f=hz(midi)
        for i in range(3):
            v=.83+.17*np.cos(t*(1.1+i*.36)+k)
            phase=f*2*np.pi*t*(.997+i*.0028)+(.20+i*.08)*np.sin(t*(2.5+i*.72)+k*2)
            p=(np.sin(phase)+.27*np.sin(phase*2+.8)+.06*np.sin(phase*3+.28))*swell*v
            add(at,p*amp/(len(notes)*2.4),(-.7+i*.7)*(-1 if k%2 else 1))
def noise(t,low,high):
    return sosfilt(butter(2,[low,high],fs=rate,btype='bandpass',output='sos'),rng.normal(0,1,len(t)))
def fold(at,length,amp,pan):
    t=clock(length)
    x=(np.sin(np.pi*t/length)**1.65)
    x*=.38+.62*np.sin(t*11.5+.4)**2
    add(at,(noise(t,210,5400)*.78+noise(t,90,800)*.80)*x*amp,pan)
def fire(at,pan,amp):
    t=clock(2.8)
    low=(np.sin(2*np.pi*(56*t-7*t*t))*.54+noise(t,25,148)*1.42)*envelope(t,.025,.33)
    treb=noise(t,500,4400)*envelope(t,.009,.41)*(.48+.52*np.sin(t*37)**2)
    add(at,(low*.65+treb*.31)*amp,pan)
    for i in range(8):
        p=clock(.17)
        add(at+.20+i*.094+rng.random()*.21,noise(p,980,6200)*envelope(p,.003,.037)*amp*.13,pan+rng.uniform(-.16,.16))
def whoosh(at,pan):
    t=clock(.67)
    add(at,noise(t,480,3200)*np.sin(np.pi*t/.67)**1.5*.016,pan)

bed(.23,11,[38,45,50,57],.11)
bed(6.0,13,[35,42,50,57],.105)
bed(13,12,[43,50,55,62],.11)
bed(21.5,15,[38,45,54,62],.13)
bed(29,15,[35,42,50,59],.11)
bed(36.5,13,[43,50,57,62],.12)
bed(43.6,11.4,[38,45,54,57,62],.16)
for at,ln,a,p in [(.54,1.90,.046,.11),(1.44,2.39,.057,-.22),(2.65,2.64,.061,.44),(3.28,2.64,.052,-.43)]:
    fold(at,ln,a,p)
themes=[
    (1.07,[(0,62),(1.18,69),(2.35,71),(3.40,66),(4.13,62)]),
    (6.63,[(0,54),(.65,62),(1.14,64),(1.89,69),(3.2,66),(4.45,62),(5.15,57),(6.12,62)]),
    (13.56,[(0,55),(1.03,62),(1.78,69),(2.55,74),(3.10,71),(3.73,69),(4.95,66),(5.62,64),(6.82,62),(7.72,69)]),
    (22.14,[(0,57),(.73,62),(1.53,64),(2.61,66),(3.36,69),(4.20,74),(5.48,76),(6.26,78),(7.28,74),(8.95,69)]),
    (32.06,[(0,59),(1.00,64),(2.16,66),(2.86,69),(3.66,71),(4.50,69),(5.47,66),(6.32,64),(7.03,62)]),
    (40.1,[(0,55),(.83,62),(1.76,66),(2.66,69),(3.42,74),(4.48,71),(5.18,69),(6.41,66),(7.16,69)]),
    (48.71,[(0,62),(.94,66),(1.82,69),(2.44,74),(3.11,76),(3.93,78),(4.75,74),(5.40,69)])
]
for bank,(start,notes) in enumerate(themes):
    for i,(offset,midi) in enumerate(notes):
        strength=(.068 if i%3==0 else .047)*rng.uniform(.83,1.15)
        string(start+offset,midi,strength,(-1)**i*.26,long=i%3==0)
    string(start-.12,notes[0][1]-12,.043,-.23,True)
for at,midi,pan in [(7.4,76,-.20),(9.76,74,-.27),(16.46,81,.28),(25.04,78,.24),(34.26,76,-.18),(42.09,81,-.29),(49.13,86,-.26),(51.74,90,.2),(53.3,86,.27)]:
    bell(at,midi,.031,pan)
for k,at in enumerate([7.29,9.47,15.27,24.50,34.02,41.06]):
    fold(at,2.05,.034,(-1)**k*.31)
for at,p,amp in [(49.14,-.47,.150),(50.23,.45,.137),(51.71,0,.182),(52.86,-.60,.110),(53.30,.62,.155),(54.26,.14,.089)]:
    whoosh(at-.72,p)
    fire(at,p,amp)

# A restrained short room impulse integrates the score with the wooden-table sounds.
imp_time=clock(.91)
for channel in range(2):
    ir=rng.normal(0,1,len(imp_time))*np.exp(-5.7*imp_time)*.00051
    for d,a in [(.039,.095),(.077,.051),(.143,.046),(.207,.030)]:
        ir[round(rate*(d+channel*.006))]+=a
    mix[:,channel]+=fftconvolve(mix[:,channel],ir)[:len(mix)]*.72
f=np.ones(len(mix))
f[:12000]=np.linspace(0,1,12000)
f[-24000:]=np.linspace(1,0,24000)**.75
mix*=f[:,None]
peak=np.max(np.abs(mix))
mix*=min(4.0,.76/peak)
wavfile.write('assets/score.wav',rate,np.int16(np.clip(mix,-1,1)*32767))
