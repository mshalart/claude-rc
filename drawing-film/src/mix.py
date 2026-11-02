import json, wave, numpy as np
SR=44100; TL=json.load(open('timeline.json')); T=TL['total']; N=int(T*SR)+SR
rng=np.random.default_rng(1)
def env(n,a=0.005,d=0.3):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
def pluck(f,dur=0.6,amp=.3):
    n=int(dur*SR); p=int(SR/f); buf=rng.uniform(-1,1,p); out=np.zeros(n)
    for i in range(n):
        out[i]=buf[i%p]; buf[i%p]=0.5*(buf[i%p]+buf[(i+1)%p])*0.996
    return out*amp
cache={}
def pl(f,dur=.55,amp=.3):
    key=(round(f,2),dur,amp)
    if key not in cache: cache[key]=pluck(f,dur,amp)
    return cache[key]
def add(buf,sig,t):
    i=int(t*SR); j=min(len(buf),i+len(sig))
    if i<len(buf) and j>i: buf[i:j]+=sig[:j-i]
def nf(m): return 440*2**((m-69)/12)
music=np.zeros(N)
bpm=104; beat=60/bpm; bar=4*beat
chords=[[60,64,67],[57,60,64],[53,57,60],[55,59,62]]  # C Am F G
roots=[48,45,41,43]
mel=[[76,None,79,76,74,None,72,None],[72,None,74,76,None,72,69,None],[69,None,72,74,72,None,69,None],[71,None,74,None,79,77,74,None]]
nbars=int(T/bar)+1
for b in range(nbars):
    c=b%4; t0=b*bar
    pat=[0,1,2,1,0,2,1,2]
    for e in range(8):
        add(music,pl(nf(chords[c][pat[e]]+12*(e%4==3)),.5,.18),t0+e*beat/2)
    for e in (0,2,2.5):
        n=int(.5*SR); tt=np.arange(n)/SR
        f=nf(roots[c]); add(music,(np.sin(2*np.pi*f*tt)+.3*np.sin(4*np.pi*f*tt))*env(n,.01,.25)*.28,t0+e*beat)
    # kick + shaker + clap
    for e in range(4):
        n=int(.25*SR); tt=np.arange(n)/SR; fk=50+90*np.exp(-tt*30)
        if e in (0,2): add(music,np.sin(2*np.pi*np.cumsum(fk)/SR)*env(n,.002,.09)*.45,t0+e*beat)
        if e in (1,3):
            cl=rng.uniform(-1,1,int(.15*SR))*env(int(.15*SR),.001,.04)*.12; add(music,cl,t0+e*beat)
    for e in range(8):
        sh=np.diff(rng.uniform(-1,1,int(.07*SR)+1))*env(int(.07*SR),.003,.02)*(.07 if e%2 else .04); add(music,sh,t0+e*beat/2)
    if b>=4 and (b//4)%2==1 or b>=24:
        for e,m in enumerate(mel[c]):
            if m is None: continue
            n=int(.7*SR); tt=np.arange(n)/SR; f=nf(m+12)
            add(music,(np.sin(2*np.pi*f*tt)+.25*np.sin(2*np.pi*f*2.76*tt)*np.exp(-tt*8))*env(n,.002,.35)*.09,t0+e*beat/2)
# voice
voice=np.zeros(N); vmask=np.zeros(N)
for s in TL['scenes']:
    if s['vstart'] is None: continue
    w=wave.open(f"audio/{s['id']}.wav"); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
    x=np.interp(np.arange(int(len(x)*SR/sr))*sr/SR,np.arange(len(x)),x)
    x=x/np.max(np.abs(x))*0.9
    add(voice,x,s['vstart']); i=int((s['vstart']-.3)*SR); vmask[i:i+len(x)+int(.6*SR)]=1
# duck envelope smoothing
kern=np.ones(int(.25*SR))/int(.25*SR); duck=np.convolve(vmask,kern,'same')
mg=0.85-0.62*duck
fade=np.ones(N); fe=int((T-2.5)*SR); fade[fe:]=np.linspace(1,0,N-fe).clip(0,1)
fade[:int(.3*SR)]=np.linspace(0,1,int(.3*SR))
mus=music/np.max(np.abs(music))*mg*fade
# sfx
sfx=np.zeros(N)
def whoosh(t):
    n=int(.9*SR); x=rng.normal(0,1,n); tt=np.arange(n)/SR
    f=np.cumsum(np.linspace(.02,.25,n)); 
    y=np.convolve(x,np.ones(6)/6,'same')*np.sin(np.pi*tt/.9)**2*.22
    # crinkle
    y+=(rng.uniform(0,1,n)>.985)*rng.uniform(-1,1,n)*.25*np.sin(np.pi*tt/.9)
    add(sfx,y,t-.45)
def ding(t,base=1046,a=.22):
    for i,f in enumerate([base,base*1.5]):
        n=int(.9*SR); tt=np.arange(n)/SR; add(sfx,np.sin(2*np.pi*f*tt)*env(n,.002,.3)*a,t+i*.09)
def popsnd(t,a=.35):
    n=int(.12*SR); tt=np.arange(n)/SR; f=300+900*np.exp(-tt*40); add(sfx,np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,.002,.04)*a,t)
sc={s['id']:s for s in TL['scenes']}
for s in TL['scenes'][1:]: whoosh(s['start'])
ding(.7,880,.25); popsnd(1.4)
for k in ['s2','s3','s4','s5','s6']: popsnd(sc[k]['start']+.15)
xp={'s2':.86,'s3':.8,'s4':.88,'s6':.9}
for k,f in xp.items(): s=sc[k]; ding(s['vstart']+s['vdur']*f,1318,.16)
s=sc['s5']; ding(s['vstart']+s['vdur']*.8+.9,1318,.16)
for i,f in enumerate([.25,.36,.46,.57]): s=sc['s6']; popsnd(s['vstart']+s['vdur']*f)
s=sc['s8']; ding(s['start']+.2,784,.25); ding(s['vstart']+s['vdur']*.55,1046,.2)
s=sc['s1']; ding(s['vstart']+s['vdur']*.42,988,.2)
mix=voice*1.0+mus*0.55+sfx
mix=np.tanh(mix*1.1)/np.tanh(1.1)
mix=mix[:int(T*SR)]
st=np.stack([mix,mix],1)
with wave.open('mix.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32000).astype(np.int16).tobytes())
print('ok',len(mix)/SR, np.abs(mix).max())
