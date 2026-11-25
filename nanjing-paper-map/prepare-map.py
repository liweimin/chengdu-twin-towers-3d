from pathlib import Path
import json, math, heapq
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from matplotlib.figure import Figure
from scipy.spatial import cKDTree

data=json.loads(Path('map-vectors.json').read_text())
groups=data['groups']
landmarks=json.loads(Path('landmarks.json').read_text())
left,top,right,bottom=data['tileBounds']
W,H=3300,round(3300*data['height']/data['width'])
rng=np.random.default_rng(84)
SC='/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
SANS='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
SERIF='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
def font(path,size): return ImageFont.truetype(path,size,index=2 if 'ttc' in path else 0)
def pix(path): return [(round(x*W),round(y*H)) for x,y in path]
def uv(lon,lat):
    x,y=(lon+180)/360*8192,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)*4096
    return (x-left)/(right-left),(y-top)/(bottom-top)

# Cartographic printing, using the layers in the source vector tiles.
im=Image.new('RGB',(W,H),'#e9dfc3')
d=ImageDraw.Draw(im)
def polygons(layers,color,target=d):
    for name in layers:
        for feature in groups.get(name,[]):
            for ring in feature:
                points=pix(ring)
                if len(points)>2: target.polygon(points,fill=color)
def lines(layers,color,weight,target=d):
    for name in layers:
        for feature in groups.get(name,[]):
            for line in feature:
                points=pix(line)
                if len(points)>1: target.line(points,fill=color,width=weight,joint='curve')
polygons(['land/'+n for n in ('residential','retail','commercial','industrial')],'#ded2b0')
polygons(['land/'+n for n in ('farmland','forest','meadow','grass','grassland','park','garden','recreation_ground','scrub','heath')],'#c4c9a5')
polygons(['land/forest'],'#a9bb93')
polygons(['land/sand'],'#e0d1a2')

# Terrarium elevation tiles provide the printed contours of Zijin Shan.
x0,y0,x1,y1=map(math.floor,(left,top,right,bottom))
terr=Image.new('RGB',((x1-x0+1)*256,(y1-y0+1)*256),(128,0,0))
for x in range(x0,x1+1):
    for y in range(y0,y1+1):
        p=Path(f'map-cache/{x}-{y}.png')
        if p.exists(): terr.paste(Image.open(p),(256*(x-x0),256*(y-y0)))
box=((left-x0)*256,(top-y0)*256,(right-x0)*256,(bottom-y0)*256)
rgb=np.asarray(terr,dtype=np.float32)
elev=rgb[:,:,0]*256+rgb[:,:,1]+rgb[:,:,2]/256-32768
z=np.asarray(Image.fromarray(elev).transform((580,530),Image.Transform.EXTENT,box,Image.Resampling.BILINEAR))
sx=(W-1)/(z.shape[1]-1); sy=(H-1)/(z.shape[0]-1)
fig=Figure()
ax=fig.subplots()
levels=list(range(40,461,20))
contours=ax.contour(z,levels=levels)
for level,segs in zip(levels,contours.allsegs):
    for seg in segs:
        if len(seg)>12:
            d.line([(round(x*sx),round(y*sy)) for x,y in seg],fill='#80926d' if level%100==0 else '#9fa37c',width=3 if level%100==0 else 2)

water=Image.new('L',(W,H))
wd=ImageDraw.Draw(water)
for key in [n for n in groups if n.startswith('water_polygons/')]:
    for feature in groups[key]:
        for i,ring in enumerate(feature):
            points=pix(ring)
            if len(points)>2: wd.polygon(points,fill=255 if i==0 else 0)
im.paste('#527e7a',mask=water.filter(ImageFilter.MaxFilter(7)))
im.paste('#769f9a',mask=water)
d=ImageDraw.Draw(im)
lines(['water_lines/river','water_lines/canal'],'#749d99',6)
for color,weight,kinds in [
    ('#ece1c4',3,('service','footway','path','steps','cycleway','track')),
    ('#f5e9c9',5,('residential','living_street','pedestrian','unclassified')),
    ('#bcad89',11,('tertiary','secondary')),
    ('#e8d6a3',7,('tertiary','secondary')),
    ('#ae9571',15,('primary','trunk','motorway')),
    ('#f1d7a0',10,('primary','trunk','motorway')),
]:
    lines(['streets/'+k for k in kinds],color,weight)
lines(['bridges/bridge'],'#f4dfb4',6)

def label(lon,lat,text,english='',size=34,color='#4d6256'):
    u,v=uv(lon,lat)
    x,y=u*W,v*H
    d.text((x,y),text,font=font(SC,size),fill=color,anchor='mm',stroke_width=2,stroke_fill='#dfd7b5')
    if english:
        d.text((x,y+size*.78),english,font=font(SERIF,round(size*.49)),fill=color,anchor='mm',stroke_width=1,stroke_fill='#dfd7b5')

label(118.739,32.091,'长 江','Y A N G T Z E   R I V E R',51,'#3e645e')
label(118.839,32.085,'紫 金 山','P U R P L E   M O U N T A I N',41)
label(118.795,32.085,'玄 武 湖','X U A N W U   L A K E',28,'#3d625d')
label(118.811,32.031,'秦淮河','Qinhuai River',24,'#4f6d69')
label(118.753,32.047,'鼓楼区','GULOU',25)
label(118.819,32.048,'玄武区','XUANWU',26)
label(118.799,32.009,'秦淮区','QINHUAI',28)
label(118.746,32.005,'建邺区','JIANYE',24)

# The neatline and scale are printed on the same sheet.
margin=55
d.rectangle((margin,margin,W-margin,H-margin),outline='#8b8867',width=2)
d.rectangle((margin+11,margin+11,W-margin-11,H-margin-11),outline='#b1a58a',width=1)
x,y=165,H-208
d.ellipse((x-53,y-53,x+53,y+53),outline='#6d7259',width=2)
for theta in np.arange(0,2*np.pi,np.pi/4):
    p=(x+48*np.sin(theta),y+48*np.cos(theta))
    d.line([p,(x+57*np.sin(theta),y+57*np.cos(theta))],fill='#6d7259',width=2)
d.polygon([(x,y-42),(x-15,y+28),(x,y+16),(x+15,y+28)],fill='#954829')
d.text((x,y-72),'N',font=font(SERIF,27),fill='#67563f',anchor='mm')
scale=(1000/(111320*math.cos(math.radians(32.05))))/(data['bounds'][2]-data['bounds'][0])*W
x,y=291,H-177
for k in range(2):
    d.rectangle((x+k*scale,y,x+(k+1)*scale,y+8),outline='#686952',fill='#686952' if k==0 else '#d8cbaa',width=2)
for k,txt in enumerate(['0','1','2 km']):
    d.text((x+k*scale,y-5),txt,font=font(SANS,15),fill='#605a46',anchor='ms')
d.text((W-85,H-82),'© OpenStreetMap contributors',font=font(SANS,19),fill='#5e5e4c',anchor='rs')
d.text((86,81),'32° N   ·   118° E',font=font(SANS,19),fill='#615943',anchor='lt')
for i in (1,2):
    for q in (-5,0,4):
        c='#f1e6ca' if q<0 else '#b8ab8b' if q==4 else '#d0c09b'
        d.line((W*i/3+q,0,W*i/3+q,H),fill=c,width=1)
        d.line((0,H*i/3+q,W,H*i/3+q),fill=c,width=1)

a=np.asarray(im,dtype=np.float32).copy()
yy,xx=np.mgrid[0:H,0:W]
grain=rng.normal(0,1.65,(H,W)).astype(np.float32)
grain+=0.85*np.sin(xx*1.82+yy*.055)+.65*np.sin(yy*1.7)
coarse=np.asarray(Image.fromarray(rng.integers(0,255,(64,70),dtype=np.uint8)).resize((W,H),Image.Resampling.BICUBIC),dtype=np.float32)
grain+=(coarse-128)*.023
a+=grain[:,:,None]
Image.fromarray(np.uint8(np.clip(a,0,255))).save('assets/map.jpg',quality=94,subsampling=0,optimize=True)

# Routes follow the connected OSM pedestrian/road graph, with a short connector at each point of interest.
graph={}
def length(p,q):
    return math.hypot((p[0]-q[0])*data['width'],(p[1]-q[1])*data['height'])
for name in ('primary','secondary','tertiary','residential','unclassified','living_street','pedestrian','service','footway','path','steps','track','cycleway','trunk'):
    cost=1.0 if name in ('primary','secondary','tertiary','residential','unclassified','living_street','pedestrian') else 1.29
    for feature in groups.get('streets/'+name,[]):
        for p in feature:
            for a,b in zip(p,p[1:]):
                a,b=tuple(round(k,5) for k in a),tuple(round(k,5) for k in b)
                if a==b: continue
                weight=length(a,b)*cost
                graph.setdefault(a,[]).append((b,weight))
                graph.setdefault(b,[]).append((a,weight))
# Nearby cut ends at tile boundaries can be separated by vector-tile quantization.
# Link neighboring endpoints within approximately 18 m before routing.
nodes=list(graph)
positions=np.asarray(nodes)*np.array([data['width'],data['height']])
for i,j in cKDTree(positions).query_pairs(.013,output_type='ndarray'):
    a,b=nodes[i],nodes[j]
    d=length(a,b)*1.57
    graph[a].append((b,d)); graph[b].append((a,d))
remaining=set(graph)
main_component=set()
while remaining:
    first=remaining.pop()
    group={first}
    queue=[first]
    while queue:
        for neighbor,_ in graph[queue.pop()]:
            if neighbor in remaining:
                remaining.remove(neighbor)
                group.add(neighbor)
                queue.append(neighbor)
    if len(group)>len(main_component): main_component=group
anchors=[uv(s['lon'],s['lat']) for s in landmarks]
def route(a,b):
    start=min(main_component,key=lambda p:length(a,p))
    end=min(main_component,key=lambda p:length(b,p))
    seen={start:(0,None)}
    queue=[(length(start,end),0,start)]
    while queue:
        _,cost,node=heapq.heappop(queue)
        if node==end:
            path=[b,end]
            while seen[node][1] is not None:
                node=seen[node][1]
                path.append(node)
            return [a,*reversed(path)]
        if cost>seen[node][0]: continue
        for dst,weight in graph[node]:
            new=cost+weight
            if new<seen.get(dst,(float('inf'),None))[0]:
                seen[dst]=(new,node)
                heapq.heappush(queue,(new+length(dst,end),new,dst))
    raise ValueError('Disconnected map route')
routes=[route(a,b) for a,b in zip(anchors,anchors[1:]+anchors[:1])]
Path('assets/routes.json').write_text(json.dumps(routes,separators=(',',':')))
print('Landmark anchors',[[s['name'] if 'name' in s else s['id'],*[round(k,4) for k in l]] for s,l in zip(landmarks,anchors)])
print('Route vertex counts',[len(x) for x in routes])
