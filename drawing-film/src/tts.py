import json, wave, sys
from piper import PiperVoice, SynthesisConfig
v = PiperVoice.load(sys.argv[1])
cfg = SynthesisConfig(length_scale=1.08, noise_scale=0.6, noise_w_scale=0.8)
out = {}
for s in json.load(open('script.json')):
    p = f"audio/{s['id']}.wav"
    with wave.open(p, 'wb') as w:
        v.synthesize_wav(s['say'], w, syn_config=cfg)
    with wave.open(p) as w: d = w.getnframes()/w.getframerate()
    out[s['id']] = round(d, 3); print(s['id'], d)
json.dump(out, open('durations.json','w'))
