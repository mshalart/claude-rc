import json
d = json.load(open('durations.json'))
order = ["s1","s2","s3","s4","s5","s6","s7","s8"]
t = 4.0  # title card
scenes = [{"id":"s0","start":0.0,"dur":4.0,"vstart":None}]
for i,k in enumerate(order):
    lead = 1.0 if k not in ("s1",) else 0.7
    tail = 1.3 if k != "s8" else 5.0
    dur = lead + d[k] + tail
    scenes.append({"id":k,"start":round(t,3),"dur":round(dur,3),"vstart":round(t+lead,3),"vdur":d[k]})
    t += dur
json.dump({"total":round(t,3),"scenes":scenes}, open('timeline.json','w'), indent=1)
print(round(t,2)); [print(s) for s in scenes]
