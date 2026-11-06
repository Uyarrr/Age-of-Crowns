"""Build a province index (--index), or render the frozen ownership manifest.

Uses the installed map, numpy, and Pillow. No raster art is generated or edited.
"""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from economy_audit import BASE, ROOT, parse

def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding='utf-8')

def pixels():
    a = np.asarray(Image.open(BASE/'map_data/provinces.png').convert('RGB'))
    return (a[:, :, 0].astype(np.uint32) << 16) | (a[:, :, 1].astype(np.uint32) << 8) | a[:, :, 2]

def index():
    wanted = set()
    for p in (BASE/'common/strategic_regions').glob('*.txt'):
        for n in parse(p.read_text(encoding='utf-8-sig')):
            if n.key in {'region_brazil','region_la_plata','region_andes','region_gran_colombia'}:
                wanted.update(n.words('states'))
    states = {}
    for p in (BASE/'map_data/state_regions').glob('*.txt'):
        for n in parse(p.read_text(encoding='utf-8-sig')):
            if n.key in wanted:
                states[n.key] = {'provinces': [s.strip('"') for s in n.words('provinces')],
                                 'city': n.scalar('city','').strip('"'), 'port':n.scalar('port','').strip('"')}
    codes = pixels()
    sample = codes[::2, ::2]
    colors, inv = np.unique(sample, return_inverse=True)
    inv = inv.ravel()
    y, x = np.indices(sample.shape)
    counts = np.bincount(inv)
    cx = np.bincount(inv, weights=x.ravel()) / counts * 2
    cy = np.bincount(inv, weights=y.ravel()) / counts * 2
    centres = {f'x{c:06X}':[round(float(x),2),round(float(y),2)] for c,x,y in zip(colors,cx,cy)}
    valid = {int(p[1:],16) for s in states.values() for p in s['provinces']}
    adjacency = {f'x{v:06X}':set() for v in valid}
    # Includes the mainland, Tierra del Fuego, and Falklands; remote islands
    # remain in the ownership manifest but are never playable-core candidates.
    crop = codes[1800:3520,2000:3340]
    for a,b in [(crop[:,1:],crop[:,:-1]),(crop[1:,:],crop[:-1,:])]:
        mask=a!=b
        for x,y in np.unique(np.stack((a[mask],b[mask]),axis=1),axis=0):
            if int(x) in valid and int(y) in valid:
                adjacency[f'x{x:06X}'].add(f'x{y:06X}')
                adjacency[f'x{y:06X}'].add(f'x{x:06X}')
    for name,data in [('states',states),('centres',centres),('adjacency',{k:sorted(v) for k,v in adjacency.items()})]:
        dump(ROOT/f'tools/south_america_{name}.tmp.json',data)
    print(f'Indexed {len(valid)} provinces in {len(states)} state regions.')

def preview():
    data=json.loads((ROOT/'docs/south_america_1444.json').read_text(encoding='utf-8'))
    profiles=data['profiles']
    codes=pixels()[1800:3520,2250:3340]
    lookup=np.full((16777216,3),[19,35,47],dtype=np.uint8)
    state_ids=np.zeros(16777216,dtype=np.uint8)
    for i,(state,owners) in enumerate(data['finalOwners'].items(),1):
        for tag,provs in owners.items():
            color=profiles[tag]['color'] if tag in profiles else ([83,103,81] if tag=='AMZ' else [186,162,109])
            for p in provs:
                lookup[int(p[1:],16)]=color
                state_ids[int(p[1:],16)]=i
    arr=lookup[codes]
    states=state_ids[codes]
    border=np.zeros(codes.shape,dtype=bool)
    border[:,1:]|=states[:,1:]!=states[:,:-1]
    border[1:,:]|=states[1:,:]!=states[:-1,:]
    arr[border & (states>0)]=[27,43,42]
    im=Image.fromarray(arr).resize((763,1204))
    out=Image.new('RGB',(1100,1300),(240,237,228))
    out.paste(im,(15,75))
    fontpath='C:/Windows/Fonts/arial.ttf'
    font=ImageFont.truetype(fontpath,17)
    title=ImageFont.truetype(fontpath,26)
    draw=ImageDraw.Draw(out)
    draw.text((20,18),'South America · 1444 starting ownership',font=title,fill=(30,47,46))
    draw.text((20,50),'Compact playable cores; existing Andean states retained',font=font,fill=(50,65,60))
    for i,(tag,f) in enumerate(profiles.items()):
        x,y=f['anchor']; x=15+(x-2250)*.7; y=75+(y-1800)*.7
        draw.ellipse((x-3,y-3,x+3,y+3),fill='white',outline='black')
        draw.text((x+7,y-10),tag,font=font,fill='white',stroke_width=2,stroke_fill=(20,30,30))
        ly=95+i*61
        draw.rectangle((800,ly,818,ly+18),fill=tuple(f['color']))
        draw.text((830,ly-2),tag+' · '+f['name'],font=font,fill=(30,45,40))
        n=sum(len(o.get(tag,[])) for o in data['finalOwners'].values())
        draw.text((830,ly+22),f'{n} connected provinces',font=font,fill=(75,85,75))
    for j,(color,label) in enumerate([((83,103,81),'South American Peoples'),((186,162,109),'Existing Andean states')]):
        y=820+j*38
        draw.rectangle((800,y,818,y+18),fill=color)
        draw.text((830,y-2),label,font=font,fill=(30,45,40))
    draw.multiline_text((800,930),'Research-informed game cores.\nNot exact historical borders.\nSee the research notes for\nregional evidence and limits.',font=font,fill=(65,75,65),spacing=8)
    output=ROOT/'docs/south_america_1444_map.png'
    out.save(output)
    print(output)

if __name__=='__main__':
    index() if '--index' in sys.argv else preview()
