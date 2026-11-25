from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen
from math import pi, radians, asinh, tan, floor
from time import sleep
z = 13
def tile(lon, lat):
    return ((lon+180)/360*2**z,(1-asinh(tan(radians(lat)))/pi)/2*2**z)
lo, top = tile(118.713,32.131)
hi, bottom = tile(118.894,31.982)
cache = Path('map-cache')
cache.mkdir(exist_ok=True)
jobs = [(x,y,k) for x in range(floor(lo),floor(hi)+1) for y in range(floor(top),floor(bottom)+1) for k in ('mvt','png')]
def save(job):
    x,y,k = job
    path = cache / f'{x}-{y}.{k}'
    if path.exists():
        return
    url = (f'https://vector.openstreetmap.org/shortbread_v1/{z}/{x}/{y}.mvt' if k=='mvt'
           else f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png')
    for i in range(3):
        try:
            with urlopen(url, timeout=15) as response:
                path.write_bytes(response.read())
            return
        except Exception as err:
            if i == 2: print(path,err)
            sleep(0.5)
with ThreadPoolExecutor(10) as executor:
    list(executor.map(save,jobs))
print(len(list(cache.iterdir())), 'tiles')
