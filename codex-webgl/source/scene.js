const TAU = 2 * Math.PI;
const clamp01 = n => Math.min(1, Math.max(0, n));
const lerp = (a, b, t) => a + (b - a) * t;
const sub = (a, b) => a.map((n, i) => n - b[i]);
const dot = (a, b) => a.reduce((sum, n, i) => sum + n * b[i], 0);
const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const unit = a => a.map(n => n / (Math.hypot(...a) || 1));

function random(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let n = Math.imul(state ^ (state >>> 15), state | 1);
    n ^= n + Math.imul(n ^ (n >>> 7), n | 61);
    return ((n ^ (n >>> 14)) >>> 0) / 4294967296;
  };
}

class Mesh {
  vertices = [];
  indices = [];

  vertex(point, normal, uv = [0, 0]) {
    const i = this.vertices.length / 8;
    this.vertices.push(...point, ...normal, ...uv);
    return i;
  }

  triangle(a, b, c) { this.indices.push(a, b, c); }

  face(points, normal, uv = [[0,0],[1,0],[1,1],[0,1]]) {
    const i = this.vertices.length / 8;
    for (let j = 0; j < 4; j++) this.vertex(points[j], normal, uv[j]);
    this.indices.push(i,i+1,i+2,i,i+2,i+3);
  }

  grid(columns, rows, sample) {
    const start = this.vertices.length / 8;
    const stride = columns + 1;
    for (let y = 0; y <= rows; y++) for (let x = 0; x <= columns; x++) {
      const [p,n,uv] = sample(x/columns,y/rows);
      this.vertex(p,n,uv);
    }
    for (let y = 0; y < rows; y++) for (let x = 0; x < columns; x++) {
      const i = start+y*stride+x;
      this.indices.push(i,i+1,i+stride+1,i,i+stride+1,i+stride);
    }
  }
}

function box(mesh,x,y,z,w,d,h, angle = 0) {
  const cs = Math.cos(angle), sn = Math.sin(angle);
  const rotate = (px,py) => [px*cs-py*sn,px*sn+py*cs];
  const point = (px,py,pz) => { const p = rotate(px,py); return [p[0]+x,p[1]+y,pz+z]; };
  const ring = [[-w/2,-d/2],[w/2,-d/2],[w/2,d/2],[-w/2,d/2]];
  const ns = [[0,-1],[1,0],[0,1],[-1,0]];
  for (let j = 0; j < 4; j++) {
    const [a,b] = ring[j], [e,f] = ring[(j+1)%4];
    const span = j%2 === 0 ? w : d;
    const shift = j*128;
    const n = rotate(...ns[j]);
    mesh.face([point(a,b,0),point(e,f,0),point(e,f,h),point(a,b,h)], [...n,0],
      [[shift,z],[shift+span,z],[shift+span,z+h],[shift,z+h]]);
  }
  mesh.face(ring.map(([a,b])=>point(a,b,h)),[0,0,1],[[0,0],[w,0],[w,d],[0,d]]);
}

function tube(mesh,a,b,ra,rb,sides=8) {
  const axis = unit(sub(b,a));
  const u = unit(cross(axis,Math.abs(axis[2])>.71 ? [1,0,0] : [0,0,1]));
  const v = cross(axis,u);
  mesh.grid(sides,1,(s,t) => {
    const angle = s*TAU;
    const n = u.map((c,i)=>c*Math.cos(angle)+v[i]*Math.sin(angle));
    return [a.map((c,i)=>lerp(c,b[i],t)+n[i]*lerp(ra,rb,t)),n,[s,t]];
  });
}

function revolve(mesh, center, profile, options={}) {
  const { columns=120, rows=44, power=1, length=140, rotation=0, phase=0 } = options;
  const signedPow = n => Math.sign(n)*Math.pow(Math.abs(n),power);
  const cs = Math.cos(rotation), sn = Math.sin(rotation);
  function position(u,t) {
    const [rx,ry,z,shift=0] = profile(clamp01(t));
    const theta = TAU*u+phase;
    const x = rx*signedPow(Math.cos(theta)) + shift;
    const y = ry*signedPow(Math.sin(theta));
    return [center[0]+x*cs-y*sn,center[1]+x*sn+y*cs,z];
  }
  const arc = [0];
  for (let i = 1; i <= columns; i++) {
    const a = position((i-1)/columns,.5), b = position(i/columns,.5);
    arc.push(arc[i-1]+Math.hypot(b[0]-a[0],b[1]-a[1]));
  }
  mesh.grid(columns,rows,(u,t)=>{
    const p = position(u,t);
    const tangent = sub(position(u+.00085,t), position(u-.00085,t));
    const vertical = sub(position(u,t+.001), position(u,t-.001));
    const n = unit(cross(tangent,vertical));
    return [p,n,[arc[Math.round(u*columns)]*length/arc[columns],p[2]]];
  });
}

function disk(mesh,x,y,z,rx,ry,colorAngle=0) {
  const mid = mesh.vertex([x,y,z],[0,0,1],[0,0]);
  const c = Math.cos(colorAngle), s = Math.sin(colorAngle);
  for (let i=0;i<=96;i++) {
    const a=i/96*TAU, dx=rx*Math.cos(a), dy=ry*Math.sin(a);
    const id = mesh.vertex([x+dx*c-dy*s,y+dy*c+dx*s,z],[0,0,1],[dx,dy]);
    if(i>0) mesh.triangle(mid,id-1,id);
  }
}

function foliageAtlas() {
  const canvas = document.createElement('canvas');
  const tile = 256;
  canvas.width = tile*4;
  canvas.height = tile*2;
  const ctx = canvas.getContext('2d');
  for (let variant=0; variant<8; variant++) {
    const rng = random(901+variant*73);
    const between = (a,b) => lerp(a,b,rng());
    const ox = variant%4*tile, oy = Math.floor(variant/4)*tile;
    ctx.save();
    ctx.translate(ox,oy);
    ctx.beginPath(); ctx.rect(2,2,252,252); ctx.clip();
    const ends = [];
    const shrub = variant >= 6;
    function branch(x,y,len,angle,width,level) {
      const x1=x+Math.sin(angle)*len, y1=y-Math.cos(angle)*len;
      const bend = between(-.25,.25)*len;
      ctx.lineWidth=width;
      ctx.lineCap='round';
      ctx.strokeStyle=level>1 ? '#433e31':'#514635';
      ctx.beginPath(); ctx.moveTo(x,y); ctx.quadraticCurveTo((x+x1)/2+bend,(y+y1)/2,x1,y1); ctx.stroke();
      if (level===0 || len<8) {
        ends.push([x1,y1,between(9,24),between(6,17),rng()]);
        return;
      }
      const split = between(.35,.78);
      branch(lerp(x,x1,split),lerp(y,y1,split),len*between(.48,.81),angle+between(.42,1.11),width*.56,level-1);
      branch(lerp(x,x1,split*.79),lerp(y,y1,split*.79),len*between(.45,.79),angle-between(.37,1.13),width*.53,level-1);
      branch(x1,y1,len*between(.58,.86),angle+between(-.43,.39),width*.63,level-1);
    }
    branch(128,251,shrub?65:between(88,106),between(-.12,.12),shrub?5:7,4);
    for (let i=0;i<40;i++) {
      const a=between(0,TAU), radius=Math.sqrt(rng());
      const x=127+Math.cos(a)*radius*between(61,100);
      const y=(shrub?123:103)+Math.sin(a)*radius*between(51,75);
      ends.push([x,y,between(9,27),between(8,24),rng()]);
    }
    ends.sort((a,b)=>a[4]-b[4]);
    for (const [x,y,rx,ry,illumination] of ends) {
      const n = Math.round(between(95,210));
      for (let i=0;i<n;i++) {
        const a=between(0,TAU), radius=Math.sqrt(rng());
        const dx=Math.cos(a)*rx*radius, dy=Math.sin(a)*ry*radius;
        const lit = .37*illumination+.36*rng()+.27*(1-(dy/ry+1)/2);
        const green = 37+64*lit;
        const brown = variant===5 ? 1.08 : .72+variant*.014;
        ctx.fillStyle=`rgb(${Math.round(green*brown)},${Math.round(green)},${Math.round(green*(.58+illumination*.08))})`;
        ctx.beginPath(); ctx.ellipse(x+dx,y+dy,between(.62,2.65),between(.5,1.46),a,0,TAU); ctx.fill();
      }
    }
    ctx.restore();
  }
  return canvas;
}

function buildScene(eye) {
  const rng = random(2751823);
  const between = (a,b) => lerp(a,b,rng());
  const entries = [];
  function add(material,color,info=[4,1.42,0,0]) {
    const mesh = new Mesh();
    entries.push({mesh,material,color,info});
    return mesh;
  }
  const metal = add(7,[.123,.141,.159]);
  const darkMetal = add(2,[.047,.055,.063]);
  const paleMetal = add(2,[.210,.215,.208]);
  const rooftops = add(2,[.115,.117,.120]);
  const warmLamp = add(3,[6.5,3.45,1.27]);
  const whiteLamp = add(3,[4.5,3.91,2.4]);
  const redLamp = add(3,[2.7,.105,.035]);
  const bronze = add(9,[.203,.167,.136]);
  const amberHalo = add(8,[.80,.367,.117]);
  const whiteHalo = add(8,[.65,.55,.37]);

  // Both envelopes derive from a truncated ellipsoid. The rotated superellipse
  // introduces the broad faces and rounded shoulders visible from the park.
  const towers = [[-48.8,6.0,58,3.3,-.115], [50.1,-1.0,48,4.125,.078]];
  for (const [x,y,seed,floor,rotation] of towers) {
    const shell = add(1,seed===58?[.063,.095,.133]:[.055,.086,.124],[floor,1.29,seed,.13*seed]);
    const body = t => {
      const z=t*218;
      const scale=Math.sqrt(1-Math.pow((z-99)/173,2));
      return [26.3*scale,23.7*scale,z,-2.2*t+1.4*Math.sin(Math.PI*t)];
    };
    revolve(shell,[x,y],body,{rows:140,columns:192,power:.77,length:156.2,rotation,phase:.18});
    const [rx,ry] = body(1);
    disk(rooftops,x-2.2,y,217.9,rx*.97,ry*.98,rotation);
    revolve(metal,[x,y],t=>[rx*(1.005-.012*t),ry*(1.01-.012*t),217.75+.27*t,-2.2],
      {rows:1,power:.77,rotation,phase:.18});
    box(darkMetal,x-3.8,y+6.4,216.4,20.5,11.2,2.45,rotation);
    box(rooftops,x+2.1,y+5.8,218.85,6.1,7.2,.26,rotation);
    for (const s of [-1,1]) {
      tube(darkMetal,[x+s*(rx-4),y+7,217],[x+s*(rx-4),y+7,218.5],.11,.09,5);
      tube(redLamp,[x+s*(rx-4),y+7,218.50],[x+s*(rx-4),y+7,218.68],.115,.095,6);
    }
    const lobby = add(0,[.105,.153,.167],[5.0,1.6,seed+45,.1]);
    revolve(lobby,[x,y-1.2],t=>[22.3+1.9*t,17.2+1.8*t,2+12.5*t],{rows:3,power:.72,length:123,rotation});
  }

  // Stepped, oval volumes of the ground-level financial centre.
  function petal(x,y,rx,ry,h,rotation) {
    const glass = add(0,[.079,.114,.137],[3.85,1.69,between(8,80),between(0,1)]);
    const tiers = Math.max(4,Math.round(h/4));
    for (let i=0;i<tiers;i++) {
      const s = Math.sqrt(1-.68*Math.pow((i+.60)/tiers,1.91));
      const z = 1.6+(h-1.6)*i/tiers, level = (h-1.6)/tiers;
      const profile = t=>[rx*s*(1-.025*t),ry*s*(1-.025*t),z+level*t];
      revolve(glass,[x+i*.20,y],profile,{rows:2,length:TAU*Math.sqrt((rx*rx+ry*ry)/2)*s,rotation,power:.93});
      revolve(metal,[x+i*.20,y],t=>[rx*s*(1.012-.028*t),ry*s*(1.012-.028*t),z+level-.34+t*.60],
        {rows:1,length:TAU*rx*s,rotation,power:.93});
      disk(rooftops,x+i*.20,y,z+level,rx*s*.985,ry*s*.985,rotation);
    }
  }
  petal(-109,-21,39,25,35,-.3);
  petal(107,-14,42,27,40,.21);
  petal(-166,35,36,22,51,-.57);
  petal(166,42,36,23,54,.38);
  petal(-122,63,36,24,56,-.3);
  petal(99,68,34,26,51,.3);

  // The low conference hall sits in front of the two towers.
  const hallGlass = add(0,[.13,.149,.154],[4.18,1.84,23.6,.4]);
  const hall = [-.5,-60.8];
  revolve(hallGlass,hall,t=>[34.3+1.9*Math.sin(t*Math.PI),21.2+1.3*Math.sin(t*Math.PI),3.0+12.4*t],
    {rows:24,power:.89,length:178,rotation:-.03});
  revolve(bronze,hall,t=>[36.0*Math.cos(1.560*t)+.03,22.4*Math.cos(1.560*t)+.03,14.8+13.2*Math.sin(1.560*t)],
    {rows:38,columns:160,power:.95,length:192,rotation:-.03});
  revolve(paleMetal,hall,t=>[36.1-.10*t,22.5-.12*t,14.46+.39*t],{rows:1,length:185,rotation:-.03});
  revolve(darkMetal,hall,t=>[35.0+.30*t,22.65-.16*t,2.5+.45*t],{rows:1,length:179,rotation:-.03});
  for (let i=0;i<28;i++) {
    const a = .78*Math.PI + i/27*1.41*Math.PI;
    const x = hall[0]+34.9*Math.cos(a), y = hall[1]+21.91*Math.sin(a);
    tube(metal,[x,y,2.8],[x,y,14.5],.155,.135,6);
  }

  // Background skyline, including service floors, mechanical roofs and parapets.
  const skyline = [
    [-242,101,45,27,89,4.1,-.03],[-209,112,23,26,73,3.4,-.14],[-180,108,34,32,109,4.1,-.06],
    [-150,188,26,29,118,3.7,.05],[-127,169,22,26,82,3.3,0],[-105,171,19,25,59,3.25,.03],
    [-85,244,36,35,115,3.1,-.04],[-55,242,25,28,69,3.5,-.06],[-31,293,20,23,74,3.4,.02],
    [-14,254,21,27,62,3.3,-.08],[6,256,27,27,89,3.67,.02],[33,260,26,27,104,3.6,.09],
    [72,253,30,31,107,3.4,-.06],[116,146,29,26,84,4.25,-.07],[139,153,27,30,105,4.0,.03],
    [168,126,30,28,124,4.1,-.17],[193,166,27,31,94,3.7,-.10],[218,124,32,25,88,4.0,.06],
    [244,105,35,39,140,4.2,.02],[269,216,27,35,108,3.3,-.07],[307,183,37,33,111,3.7,.04],
    [328,105,24,34,137,4.1,-.11],[-279,137,33,35,125,4.12,.08],[-285,211,32,31,91,3.6,.08],
  ];
  for (const [x,y,w,d,h,f,a] of skyline) {
    const tint = between(.61,1.29);
    const warm = between(0,1);
    const glass = add(0,[lerp(.053,.144,warm)*tint,lerp(.085,.115,warm)*tint,lerp(.145,.100,warm)*tint],
      [f,between(1.19,2.1),between(0,90),between(0,1)]);
    const z = 2.2;
    const podium = h*between(.17,.27);
    box(glass,x,y,z,w+3.4,d+3.1,podium,a);
    box(glass,x,y,z+podium,w,d,h-podium-6,a);
    box(darkMetal,x,y,h-4.6,w+.5,d+.5,1.07,a);
    box(glass,x-w*.045,y+d*.033,h-3.8,w*.89,d*.87,5.8,a);
    box(metal,x-w*.045,y+d*.033,h+2.0,w*.92,d*.91,.64,a);
    box(rooftops,x+w*.16,y+d*.16,h+2.63,w*.34,d*.38,2.25,a);
    if(rng()>.58) box(paleMetal,x+w*.25,y+d*.13,h+4.8,.35,.38,5.3,a);
    if(rng()>.42) {
      const louver=add(6,[.087,.108,.135]);
      box(louver,x,y,podium+z-.7,w+3.45,d+3.2,1.55,a);
      box(louver,x,y,f*19.0,w+.24,d+.24,1.25,a);
    }
    const ribs = add(7,[.127*tint,.142*tint,.151*tint]);
    const count=Math.round(w/between(3.1,5.2));
    const ca=Math.cos(a), sa=Math.sin(a);
    for (let j=0;j<=count;j++) {
      const dx=lerp(-w/2,w/2,j/count), dy=-d/2;
      box(ribs,x+dx*ca-dy*sa,y+dx*sa+dy*ca,z+podium,.14,.40,h-podium-6,a);
    }
  }

  const park = add(5,[.055,.084,.041]);
  const walk = add(2,[.186,.168,.137]);
  const retaining = add(2,[.090,.083,.070]);
  const cap = add(2,[.178,.166,.143]);
  const rail = add(2,[.085,.087,.074]);
  const shore = x => -115.4 - .00288*x*x + 2.2*Math.sin(x*.051) + 3.7*Math.sin(x*.018+.3);
  function band(mesh,near,far) {
    mesh.grid(260,1,(u,t)=>{
      const x=lerp(-367,367,u);
      const [y0,z0]=near(x), [y1,z1]=far(x);
      return [[x,lerp(y0,y1,t),lerp(z0,z1,t)],[0,(z0-z1)*.1,1],[x,lerp(y0,y1,t)]];
    });
  }
  band(retaining,x=>[shore(x),-.13],x=>[shore(x)+.45,1.02]);
  band(cap,x=>[shore(x)-.07,1.02],x=>[shore(x)+.88,1.10]);
  band(walk,x=>[shore(x)+.88,1.04],x=>[shore(x)+5.20,1.27]);
  band(park,x=>[shore(x)+5.19,1.22],x=>[shore(x)+28.8,3.5]);
  band(park,x=>[shore(x)+28.8,3.5],x=>[520,3.2]);
  for(let i=0;i<170;i++) {
    const x=lerp(-276,277,i/169), y=shore(x)+.86;
    tube(rail,[x,y,1.06],[x,y,1.83],.024,.022,5);
    if(i<169) {
      const xNext=lerp(-276,277,(i+1)/169), yNext=shore(xNext)+.86;
      tube(rail,[x,y,1.81],[xNext,yNext,1.81],.022,.022,5);
    }
  }

  function glow(mesh,x,y,z,radius) {
    const dx=x-eye[0],dy=y-eye[1],length=Math.hypot(dx,dy);
    const bx=dy*radius/length,by=-dx*radius/length;
    x-=dx*.34/length;
    y-=dy*.34/length;
    mesh.face([[x-bx,y-by,z-radius],[x+bx,y+by,z-radius],[x+bx,y+by,z+radius],[x-bx,y-by,z+radius]],[0,-1,0]);
  }
  function lamp(x,y,z,h,white=false) {
    tube(darkMetal,[x,y,z],[x,y,z+h],.075,.040,7);
    tube(metal,[x,y,z+h-.12],[x,y-.65,z+h-.12],.033,.033,6);
    box(darkMetal,x,y-.64,z+h-.15,.31,.37,.15);
    box(white ? whiteLamp : warmLamp,x,y-.64,z+h-.17,.25,.31,.06);
    glow(white ? whiteHalo : amberHalo,x,y-.67,z+h-.145,white?1.5:1.35);
  }
  for(let i=0;i<27;i++) {
    const x=lerp(-240,241,i/26)+between(-1,1), y=shore(x)+2.8;
    lamp(x,y,1.23,between(3.7,4.6),i%7===3);
  }
  for(let i=0;i<27;i++) {
    const x=lerp(-229,224,i/26), y=between(-60,-36);
    lamp(x,y,2.8,between(4.2,5.1),i%3===0);
  }
  for(let i=0;i<29;i++) {
    const x=hall[0]+(i-14)*1.72;
    box(warmLamp,x,-82+Math.pow(x-hall[0],2)*.0061,3.18,.74,.20,.13);
  }

  const leaves = add(4,[.74,.84,.65]);
  const shrubs = add(4,[.55,.68,.46]);
  function plant(mesh,x,y,z,w,h,variant) {
    const dx=x-eye[0],dy=y-eye[1];
    const inv=w*.5/Math.hypot(dx,dy), bx=dy*inv, by=-dx*inv;
    const u=variant%4/4, v=(1-Math.floor(variant/4))/2;
    mesh.face([[x-bx,y-by,z],[x+bx,y+by,z],[x+bx,y+by,z+h],[x-bx,y-by,z+h]],
      [0,-1,0],[[u,v],[u+.25,v],[u+.25,v+.5],[u,v+.5]]);
  }
  for(let i=0;i<221;i++) {
    const x=between(-289,279), y=shore(x)+between(6,33);
    const h=between(3.3,10.8) * (Math.abs(x)<39 ? .72 : 1);
    const z=1.4 + (y-shore(x)-6)*.078;
    plant(leaves,x,y,z,h*between(.78,1.16),h,Math.floor(between(0,6)));
  }
  for(let i=0;i<203;i++) {
    const x=between(-285,285), y=between(-71,22);
    if(Math.abs(x)<40 && y>-85 && y<-35) continue;
    const h=between(3.9,11.1);
    plant(leaves,x,y,3.1,h*between(.84,1.25),h,Math.floor(between(0,6)));
  }
  for(let i=0;i<216;i++) {
    const x=between(-267,264), y=shore(x)+between(.6,14);
    const h=between(.56,2.5);
    plant(shrubs,x,y,1.1,h*between(1.1,2.5),h,6+Math.floor(between(0,2)));
  }

  const people = [[-45,-111,1.28,1],[-46.9,-112.2,1.25,2],[34,-110.5,1.27,1],[36,-110.4,1.26,0],
    [112,-143,1.25,1],[114,-143,1.25,2],[-118,-152,1.25,0],[-116,-152,1.25,2],[-122,-148,1.25,1]];
  const coats = [[.082,.086,.088],[.21,.16,.113],[.118,.064,.063]].map(c=>add(2,c));
  const skin = add(2,[.193,.127,.092]);
  for(const [x,y,z,index] of people) {
    const h=between(1.57,1.85), lean=between(-.12,.1), stride=between(.19,.41);
    for(const side of [-1,1]) {
      const foot=[x+side*stride,y+side*.17,z+.07];
      tube(darkMetal,foot,[x+side*.105,y,z+h*.50],.061,.088,6);
      const hand=[x+side*.24,y-side*.13,z+h*.46];
      tube(coats[index],hand,[x+lean+side*.20,y,z+h*.77],.055,.078,6);
    }
    tube(coats[index],[x,y,z+h*.47],[x+lean,y,z+h*.83],.16,.195,9);
    tube(skin,[x+lean,y,z+h*.83],[x+lean,y,z+h*.98],.091,.09,8);
    tube(darkMetal,[x+lean,y,z+h*.97],[x+lean,y,z+h*1.015],.092,.056,8);
  }

  // Reeds near the corners give the open water a foreground depth cue.
  const reed = add(2,[.043,.060,.036]);
  function blade(x,y,z,h,w,dx,dy) {
    reed.grid(1,5,(u,t)=>[[x+dx*t*t+w*(u-.5)*(1-t),y+dy*t*t,z+h*t*(1-.13*t)],[.18,-.94,.29],[u,t]]);
  }
  for(const [cx,cy,count] of [[2,-365,250],[.5,-361,130],[40,-358,140]]) {
    for(let i=0;i<count;i++) {
      const a=between(0,TAU), radius=Math.sqrt(rng());
      const x=cx+Math.cos(a)*radius*between(1.7,7.6), y=cy+Math.sin(a)*radius*between(1.8,5.5);
      blade(x,y,-.12,between(.25,1.33),between(.027,.16),between(-.66,.66),between(-.25,.5));
    }
  }
  const water = new Mesh();
  water.face([[-1120,-1100,0],[1120,-1100,0],[1120,490,0],[-1120,490,0]],[0,0,1]);
  return {entries,water};
}
