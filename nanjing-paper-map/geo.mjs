import { VectorTile } from '@mapbox/vector-tile';
import { PbfReader } from 'pbf';
import fs from 'node:fs';
import { gunzipSync } from 'node:zlib';

import { bounds, tileXY, width, height } from './projection.mjs';
const [west,south,east,north]=bounds;
const [left,top]=tileXY(west,north);
const [right,bottom]=tileXY(east,south);
if (typeof window === 'undefined') {
  const groups = {};
  for(const file of fs.readdirSync('map-cache').filter(p=>p.endsWith('.mvt'))) {
    const [tx,ty] = file.slice(0,-4).split('-').map(Number);
    let data = fs.readFileSync('map-cache/'+file);
    if(data[0]===31) data=gunzipSync(data);
    const tile = new VectorTile(new PbfReader(data));
    for(const layerName of ['land','water_polygons','water_lines','streets','railways','bridges','sites']) {
      const layer=tile.layers[layerName];
      if(!layer) continue;
      for(let i=0;i<layer.length;i++) {
        const f=layer.feature(i);
        if(f.properties.tunnel || (layerName==='streets' && f.properties.rail)) continue;
        const k=layerName+'/'+f.properties.kind;
        const paths=f.loadGeometry().map(path=>path.map(p=>[
          +((tx+p.x/layer.extent-left)/(right-left)).toFixed(6),
          +((ty+p.y/layer.extent-top)/(bottom-top)).toFixed(6)
        ]));
        (groups[k]??=[]).push(paths);
      }
    }
  }
  fs.writeFileSync('map-vectors.json',JSON.stringify({bounds,tileBounds:[left,top,right,bottom],width,height,groups}));
}
