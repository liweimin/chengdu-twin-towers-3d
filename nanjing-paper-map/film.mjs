import * as THREE from './node_modules/three/build/three.module.js';
import {uv,width as W,height as H} from './projection.mjs';

const query=new URLSearchParams(location.search);
const width=+(query.get('w')||1080);
const height=+(query.get('h')||1920);
const fast=query.has('fast');
const PI=Math.PI;
const V=(x,y,z)=>new THREE.Vector3(x,y,z);
const clamp=x=>Math.min(1,Math.max(0,x));
const lerp=(a,b,x)=>a+(b-a)*x;
const smooth=x=>{x=clamp(x);return x*x*(3-2*x);};
const phase=(t,a,b)=>smooth((t-a)/(b-a));
const seeded=seed=>()=>{seed=(1664525*seed+1013904223)|0;return (seed>>>0)/4294967296;};
const surface=.052;
const world=(u,v,y=surface)=>V((u-.5)*W,y,(v-.5)*H);
const texLoader=new THREE.TextureLoader();
const source=async file=>fetch(file).then(r=>{if(!r.ok)throw Error(file);return r.json();});
const [stops,silhouettes,routes]=await Promise.all([source('landmarks.json'),source('assets/silhouettes.json'),source('assets/routes.json')]);
for(const s of stops) s.location=world(...uv(s.lon,s.lat));
const byId=Object.fromEntries(stops.map(s=>[s.id,s]));
const artNames=Object.keys(silhouettes);
const litNames=['tower','gate','temple','hall','lake','boat','skyline','guard','houses'];

const renderer=new THREE.WebGLRenderer({antialias:!fast,alpha:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.setSize(width,height,false);
const physicalUnfoldShadows=!query.has('noshadow');
renderer.shadowMap.enabled=physicalUnfoldShadows;
renderer.shadowMap.type=THREE.PCFShadowMap;
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.06;
const scene=new THREE.Scene();
scene.background=new THREE.Color('#2d221a');
scene.fog=new THREE.Fog('#2d221a',9,40);
const camera=new THREE.PerspectiveCamera(39,width/height,.075,85);

async function texture(name,linear=false){
  const t=await texLoader.loadAsync('assets/'+name);
  t.colorSpace=linear?THREE.NoColorSpace:THREE.SRGBColorSpace;
  t.anisotropy=8;
  return t;
}
const loadList=['map.jpg','walnut.jpg',...artNames.map(n=>n+'.png'),...litNames.map(n=>n+'-light.png')];
const textures=Object.fromEntries(await Promise.all(loadList.map(async n=>[n,await texture(n)])));

const ambient=new THREE.HemisphereLight('#ffead2','#6c503d',1.67);
scene.add(ambient);
const sun=new THREE.DirectionalLight('#ffe3bf',2.12);
sun.position.set(-7,12,5);
sun.castShadow=true;
sun.shadow.mapSize.set(fast?768:1536,fast?768:1536);
Object.assign(sun.shadow.camera,{left:-8,right:8,top:8,bottom:-8,near:1,far:32});
sun.shadow.normalBias=.010;
sun.shadow.bias=-.00022;
sun.shadow.radius=2.3;
scene.add(sun,sun.target);
const fill=new THREE.DirectionalLight('#e3ebee',.48);
fill.position.set(6,4,-8);
scene.add(fill);

function mesh(g,m,parent=scene,casts=false,receives=true){
  const o=new THREE.Mesh(g,m);
  o.castShadow=casts;o.receiveShadow=receives;parent.add(o);return o;
}
const table=mesh(new THREE.PlaneGeometry(160,160),new THREE.MeshBasicMaterial({map:textures['walnut.jpg']}));
table.rotation.x=-PI/2;
const wood=textures['walnut.jpg'];
wood.wrapS=wood.wrapT=THREE.RepeatWrapping;
wood.repeat.set(4.9,6.6);

function radialTexture(){
  const c=document.createElement('canvas');c.width=c.height=128;
  const g=c.getContext('2d'), r=g.createRadialGradient(64,64,0,64,64,63);
  r.addColorStop(0,'rgba(255,255,255,1)');r.addColorStop(.39,'rgba(255,255,255,.64)');r.addColorStop(.75,'rgba(255,255,255,.17)');r.addColorStop(1,'rgba(255,255,255,0)');
  g.fillStyle=r;g.fillRect(0,0,128,128);
  return new THREE.CanvasTexture(c);
}
const soft=radialTexture();
function decal(mat,w,d,position){
  const o=mesh(new THREE.PlaneGeometry(w,d),mat,scene,false,false);
  o.rotation.x=-PI/2;o.position.copy(position);return o;
}
const tableShadow=mesh(new THREE.PlaneGeometry(17,17),new THREE.ShadowMaterial({color:'#251c1c',opacity:.38,depthWrite:false}),scene,false,true);
tableShadow.rotation.x=-PI/2;tableShadow.position.y=.005;
const under=decal(new THREE.MeshBasicMaterial({map:soft,transparent:true,color:'#130f0d',opacity:.36,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1}),W*1.38,H*1.40,V(0,.008,0));

const mapMat=new THREE.MeshStandardMaterial({map:textures['map.jpg'],roughness:.91});
const mapFlat=new THREE.MeshBasicMaterial({map:textures['map.jpg']});
const backing=new THREE.MeshStandardMaterial({map:textures['map.jpg'],color:'#e0ce9f',roughness:.93,side:THREE.BackSide});
const frontPanels=[];
const focus={value:5};
function softenPrint(material,strength){
  material.onBeforeCompile=shader=>{
    shader.uniforms.focusDistance=focus;
    shader.vertexShader='varying vec3 focusView;\n'+shader.vertexShader.replace('#include <project_vertex>', '#include <project_vertex>\nfocusView=mvPosition.xyz;');
    shader.fragmentShader='varying vec3 focusView; uniform float focusDistance;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',
      THREE.ShaderChunk.map_fragment.replace('texture2D( map, vMapUv )',
        `texture2D( map, vMapUv, clamp(abs(length(focusView)-focusDistance)*${strength.toFixed(2)}-0.38, 0.0, 3.6) )`));
  };
  material.customProgramCacheKey=()=>String(strength);
}
softenPrint(table.material,.36);
softenPrint(mapMat,.43);
softenPrint(mapFlat,.47);
const cutEdge=new THREE.MeshStandardMaterial({color:'#cfb991',roughness:.9,side:THREE.DoubleSide});
const hingeMat=new THREE.MeshStandardMaterial({color:'#c4ad83',roughness:1,side:THREE.DoubleSide});
const board=new THREE.Group();
board.position.y=surface;
scene.add(board);
const col=W/3,row=H/3,thick=.022;
const rows=[];
function flap(ix,iz,g){
  const geom=new THREE.PlaneGeometry(col+.002,row+.002,8,8);
  geom.rotateX(-PI/2);
  const p=geom.attributes.position,t=geom.attributes.uv;
  for(let i=0;i<p.count;i++){
    const x=p.getX(i),z=p.getZ(i);
    p.setY(i,.006*Math.sin((x/col+.5)*PI)*Math.sin((z/row+.5)*PI));
    t.setXY(i,(ix+(x/col+.5))/3,1-(iz+(z/row+.5))/3);
  }
  geom.computeVertexNormals();
  frontPanels.push(mesh(geom,mapMat,g,true));
  const b=mesh(geom,backing,g,false);
  b.position.y=-thick;
  const ed=new THREE.BufferGeometry();
  const xs=col/2,zs=row/2;
  const pp=[];
  for(const [a,b] of [[[-xs,-zs],[xs,-zs]],[[xs,-zs],[xs,zs]],[[xs,zs],[-xs,zs]],[[-xs,zs],[-xs,-zs]]]){
    pp.push(a[0],0,a[1], b[0],0,b[1], b[0],-thick,b[1], a[0],0,a[1], b[0],-thick,b[1], a[0],-thick,a[1]);
  }
  ed.setAttribute('position',new THREE.Float32BufferAttribute(pp,3));ed.computeVertexNormals();
  mesh(ed,cutEdge,g,false);
}
for(let iz=0;iz<3;iz++){
  const dz=iz-1;
  const fold=new THREE.Group();board.add(fold);fold.position.z=dz*row/2;
  const strip=new THREE.Group();fold.add(strip);strip.position.z=dz*row/2;
  const wings=[];
  for(let ix=0;ix<3;ix++){
    const dx=ix-1;
    const hinge=new THREE.Group();hinge.position.x=dx*col/2;
    strip.add(hinge);
    const panel=new THREE.Group();panel.position.x=dx*col/2;
    hinge.add(panel);flap(ix,iz,panel);
    wings.push(hinge);
  }
  rows.push({fold,wings});
}
const creaseG=new THREE.Group();board.add(creaseG);
for(const offset of [-1,1]){
  const x=mesh(new THREE.BoxGeometry(.014,.006,H-.015),hingeMat,creaseG,false);
  x.position.set(offset*col*.5,.003,0);
  const z=mesh(new THREE.BoxGeometry(W-.015,.006,.014),hingeMat,creaseG,false);
  z.position.set(0,.004,offset*row*.5);
}

const art=new Map();
const depth=.013;
for(const name of artNames){
  const spec=silhouettes[name],w=spec.ratio;
  const geometry=new THREE.PlaneGeometry(w,1);
  geometry.translate(0,.5,depth/2);
  const face=new THREE.MeshStandardMaterial({map:textures[name+'.png'],alphaTest:.50,roughness:.88,emissive:litNames.includes(name)?'#fff3d6':'#000000',emissiveMap:textures[name+'-light.png']||null,emissiveIntensity:0});
  const back=new THREE.MeshStandardMaterial({map:textures[name+'.png'],color:'#c6b78f',alphaTest:.50,roughness:1,side:THREE.BackSide,emissive:'#000000'});
  const edge=new THREE.BufferGeometry(), p=[];
  for(const outline of spec.paths){
    for(let i=0;i<outline.length;i++){
      const a=outline[i], b=outline[(i+1)%outline.length];
      const x=(a[0]-.5)*w, y=1-a[1], u=(b[0]-.5)*w, v=1-b[1];
      p.push(x,y,-depth/2,u,v,-depth/2,u,v,depth/2,x,y,-depth/2,u,v,depth/2,x,y,depth/2);
    }
  }
  edge.setAttribute('position',new THREE.Float32BufferAttribute(p,3));edge.computeVertexNormals();
  art.set(name,{geometry,face,back,edge,w});
}
const tabMat=new THREE.MeshStandardMaterial({color:'#cdbb90',roughness:1,side:THREE.DoubleSide});
const glueMat=new THREE.MeshStandardMaterial({color:'#ad9264',roughness:1,side:THREE.DoubleSide});
const cards=[];
const sunRay={value:V(.45,-1,-.34)};
function shadowFrom(data,texture,leaf){
  const material=new THREE.ShaderMaterial({
    side:THREE.DoubleSide,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1,
    uniforms:{ink:{value:texture},leafMatrix:{value:leaf.matrixWorld},sunRay,strength:{value:0}},
    vertexShader:`
      uniform mat4 leafMatrix;
      uniform vec3 sunRay;
      varying vec2 paperUV;
      varying float rise;
      void main() {
        vec4 p=leafMatrix*vec4(position,1.0);
        rise=max(p.y-0.061,0.0);
        p.xyz+=sunRay*rise;
        p.y=0.061;
        paperUV=uv;
        gl_Position=projectionMatrix*viewMatrix*p;
      }`,
    fragmentShader:`
      uniform sampler2D ink;
      uniform float strength;
      varying vec2 paperUV;
      varying float rise;
      void main() {
        float mask=smoothstep(0.10,0.82,texture2D(ink,paperUV,1.4+rise*.54).a);
        gl_FragColor=vec4(0.10,0.077,0.078,mask*strength/(1.0+0.18*rise));
        #include <colorspace_fragment>
      }`
  });
  const shadow=mesh(data.geometry,material,scene,false,false);
  shadow.frustumCulled=false;
  return shadow;
}
const drawLayer=new THREE.Group();scene.add(drawLayer);
function card(id,name,dx,dz,h,delay=0,yaw=0,props={}){
  const data=art.get(name),anch=byId[id].location;
  const base=new THREE.Group();base.position.copy(anch).add(V(dx,.010,dz));
  base.rotation.y=yaw;drawLayer.add(base);
  const leaf=new THREE.Group();base.add(leaf);
  leaf.scale.set(h,h,1);
  mesh(data.geometry,data.face,leaf,true,true);
  const b=mesh(data.geometry,data.back,leaf,false,true);b.position.z=-depth;
  mesh(data.edge,cutEdge,leaf,false,true);
  const glues=[];
  for(const sign of [-1,1]){
    const lx=sign*data.w*h*.225;
    const ww=Math.min(.22,data.w*h*.19), dd=Math.min(.25,h*.27);
    const foot=mesh(new THREE.BoxGeometry(ww,.012,dd),glueMat,base,false,true);
    foot.position.set(lx,-.006,-dd*.43);
    const g=new THREE.PlaneGeometry(ww,1);
    const support=mesh(g,tabMat,base,false,true);
    glues.push({support,lx,ww,dd});
  }
  const shade=decal(new THREE.MeshBasicMaterial({map:soft,color:'#292018',opacity:.24,transparent:true,depthWrite:false}),Math.max(.16,data.w*h*.96),Math.min(.47,h*.65),base.position.clone().add(V(0,-.006,-.08)));
  shade.rotation.z=yaw;
  const duration=props.duration??2.35;
  const silhouetteShadow=shadowFrom(data,textures[name+'.png'],leaf);
  cards.push({base,leaf,glues,shade,silhouetteShadow,h,delay:byId[id].visit+delay,duration,shadeStrength:props.shade??.30});
}

// The front, middle and back cards have independent fold hinges and stay at their map anchors.
card('center','skyline', .03,.12,.49,0,.12);
card('center','skyline',-.16,-.39,.70,.34,-.16);
card('center','willow',-.61,.24,.32,.55,.24);
card('gate','gate',0,0,.57,0,.10);
card('gate','guard',.12,-.52,.70,.24,.13);
card('gate','cypress',-.63,-.69,.66,.45,-.09);
card('gate','willow',.65,-.25,.57,.70,.26);
card('temple','temple',0,0,1.00,.08,-.10,{duration:2.65});
card('temple','houses',.21,-.70,.70,.46,.12);
card('temple','willow',.68,-.31,.68,.66,-.31);
card('temple','willow',-.69,-.40,.58,.75,.15);
card('temple','boat',.01,.45,.29,.95,-.22);
card('mausoleum','ridge',-.30,-.87,.81,-.19,.02);
card('mausoleum','ridge',.18,-1.46,.69,.19,.23);
card('mausoleum','hall',0,0,1.34,.36,.06,{duration:3});
card('mausoleum','cypress',-.71,-.28,.69,.65,.14);
card('mausoleum','cypress',.81,-.42,.76,.81,-.1);
card('lake','lake',0,0,.54,.04,-.12,{duration:2.7});
card('lake','lake',.44,-.62,.39,.28,.10);
card('lake','willow',-.48,.075,.53,.65,.17);
card('lake','boat',.48,.49,.22,1.05,-.10);
card('tower','tower',0,0,2.00,.05,.10,{duration:2.7});
card('tower','skyline',-.39,-.48,.67,.46,-.12);
card('tower','skyline',.25,-.72,.80,.30,.25);
card('tower','willow',.33,.27,.49,.68,-.13);

const lights=[];
for(const s of stops){
  const p=s.location;
  const aura=decal(new THREE.MeshBasicMaterial({map:soft,transparent:true,color:'#faae55',opacity:0,depthWrite:false,blending:THREE.AdditiveBlending}),s.id==='temple'?2.45:1.9,1.6,V(p.x,.063,p.z-.04));
  lights.push(aura);
}
const lineGroup=new THREE.Group();scene.add(lineGroup);
const lineMat=new THREE.MeshBasicMaterial({color:'#aa3a24',side:THREE.DoubleSide});
const lineEdge=new THREE.MeshBasicMaterial({color:'#edcf8b',side:THREE.DoubleSide});
const routeMeshes=[];
function pathRibbon(points,span,band){
  const p=[];
  let dist=0;
  const pt=[{p:points[0],at:0}];
  for(let j=1;j<points.length;j++){
    dist+=points[j].distanceTo(points[j-1]);
    pt.push({p:points[j],at:dist});
  }
  function at(d){
    let j=pt.findIndex(k=>k.at>=d);
    if(j<=0) return (j===0?pt[0]:pt[pt.length-1]).p.clone();
    return pt[j-1].p.clone().lerp(pt[j].p,(d-pt[j-1].at)/(pt[j].at-pt[j-1].at));
  }
  for(let d=.008;d<dist;d+=span){
    const a=at(d),b=at(Math.min(dist,d+span*.70));
    const delta=b.clone().sub(a).normalize();
    const v=V(-delta.z*band,0,delta.x*band);
    const s=a.clone().add(v),t=a.clone().sub(v),u=b.clone().add(v),w=b.clone().sub(v);
    p.push(...s,...t,...u,...u,...t,...w);
  }
  return {p,at,dist};
}
routes.forEach(data=>{
  const points=data.map(([u,v])=>world(u,v,.068));
  const red=pathRibbon(points,.104,.021);
  const edge=pathRibbon(points,.104,.034);
  const layers=[[edge.p,lineEdge,0],[red.p,lineMat,.002]].map(([p,mat,y])=>{
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));
    const o=mesh(g,mat,lineGroup,false,false);o.position.y=y;return o;
  });
  routeMeshes.push({...red,layers});
});
function horizontalCircle(radius,mat,y,x,z){
  const o=mesh(new THREE.CircleGeometry(radius,32),mat,lineGroup,false,false);
  o.rotation.x=-PI/2;o.position.set(x,y,z);return o;
}
const marks=stops.map(s=>{
  const p=s.location;
  return [horizontalCircle(.116,lineEdge,.073,p.x,p.z+.12),horizontalCircle(.081,lineMat,.075,p.x,p.z+.12),horizontalCircle(.029,new THREE.MeshBasicMaterial({color:'#f7e2ae'}),.077,p.x,p.z+.12)];
});
const activeDot=horizontalCircle(.051,new THREE.MeshBasicMaterial({color:'#ffc672'}),.077,0,0);
const activeGlow=decal(new THREE.MeshBasicMaterial({map:soft,transparent:true,depthWrite:false,color:'#ed6d24',opacity:.68,blending:THREE.AdditiveBlending}),.44,.36,V(0,.078,0));

const shots=[];
function key(t,anchor,look,eye,fov){
  const at=anchor?byId[anchor].location:V(0,0,0);
  shots.push({t,values:[at.x+look[0],look[1],at.z+look[2],at.x+eye[0],eye[1],at.z+eye[2],fov]});
}
key(0,null,[.06,.12,-.68],[1.62,8.95,9.45],42);
key(1.4,null,[.07,.22,-.40],[1.09,9.1,9.1],43);
key(3.4,null,[.07,.52,-.40],[1.2,11.05,11.7],44);
key(5.65,null,[.10,.25,-.21],[.50,21.0,17.3],50);
key(6.45,null,[-.59,.16,.10],[.00,16.9,12.70],47);
key(7.75,'center',[.02,.34,-.02],[.32,3.28,4.42],43);
key(8.6,'center',[.03,.24,.25],[-.30,1.95,3.99],42);
key(9.8,'gate',[.00,.22,-.05],[-1.35,1.57,4.58],43);
key(11.7,'gate',[.00,.37,-.18],[-1.47,1.35,4.18],43);
key(13.4,'gate',[.04,.37,-.16],[-.68,1.59,3.87],43);
key(14.55,'gate',[.26,.31,-.27],[1.19,1.86,4.52],43);
key(16,'temple',[.07,.39,-.10],[3.16,2.21,4.22],43);
key(18.4,'temple',[.10,.48,.04],[3.44,1.68,3.27],43);
key(20.7,'temple',[.08,.48,-.04],[2.86,1.37,3.28],43);
key(22.2,'temple',[.29,.43,-.38],[2.64,2.48,4.47],43);
key(23.3,null,[1.00,.12,1.23],[2.0,4.34,6.74],43);
key(24.45,'mausoleum',[-.20,.40,-.06],[1.92,2.75,5.29],43);
key(26.1,'mausoleum',[-.10,.49,-.28],[1.52,1.94,4.49],43);
key(28.2,'mausoleum',[-.05,.67,-.24],[.80,1.87,4.23],43);
key(30.3,'mausoleum',[.02,.64,-.25],[-.64,2.03,4.17],43);
key(32.0,'mausoleum',[-.33,.56,-.34],[-1.72,2.77,4.87],43);
key(33.1,null,[.95,.13,-1.84],[.31,4.22,3.75],43);
key(34.5,'lake',[.11,.25,-.05],[1.20,2.37,4.60],43);
key(36.4,'lake',[.13,.30,-.16],[.55,1.59,3.88],43);
key(38.3,'lake',[.14,.35,-.10],[-.63,1.26,4.10],43);
key(39.6,'lake',[-.39,.42,-.22],[-1.59,1.81,4.55],43);
key(41.3,'tower',[.03,.84,-.10],[-1.85,2.10,4.55],43);
key(43.2,'tower',[.05,.92,-.12],[-1.35,1.77,3.98],41);
key(44.7,'tower',[.10,.96,-.18],[-.56,1.91,3.88],41);
key(46.3,'tower',[.38,.92,-.12],[.48,3.28,5.45],42);
key(48.25,null,[.10,1.48,-.53],[1.25,8.12,10.43],43);
key(50.4,null,[.01,1.74,-.80],[1.37,12.8,14.67],43);
key(52.4,null,[.02,1.37,-.48],[.55,21.3,18.6],48);
key(55,null,[0,1.22,-.42],[.16,23.0,19.8],49);

function evaluate(t){
  const n=shots.length;
  let i=shots.findIndex(k=>k.t>t)-1;
  if(i<0)i=t<=0?0:n-2;
  const a=shots[i],b=shots[i+1],c=shots[Math.max(0,i-1)],d=shots[Math.min(n-1,i+2)];
  const dt=b.t-a.t, s=clamp((t-a.t)/dt), s2=s*s, s3=s2*s;
  const tangent=(l,r,dl,dr)=>l*r>0?((dl+dr)/(dl/l+dr/r))*.92:0;
  return a.values.map((va,j)=>{
    const vb=b.values[j],vc=c.values[j],vd=d.values[j];
    const sec=(vb-va)/dt,dc=a.t-c.t,dd=d.t-b.t;
    const m0=dc===0?sec*.25:tangent((va-vc)/dc,sec,dc,dt);
    const m1=dd===0?0:tangent(sec,(vd-vb)/dd,dt,dd);
    return (2*s3-3*s2+1)*va+(s3-2*s2+s)*dt*m0+(-2*s3+3*s2)*vb+(s3-s2)*dt*m1;
  });
}

const capTimes=[
  [7.30,9.27],[9.76,14.28],[15.70,22.35],[25.02,32.49],[34.59,39.60],[41.38,46.64]
];
const travelTimes=[[8.20,10.5],[14.0,16.4],[21.7,25.7],[31.6,35.2],[38.8,42.4],[45.9,48.4]];
const live=query.has('preview');
const out=live?document.createElement('canvas'):new OffscreenCanvas(width,height);
out.width=width;out.height=height;
if(live)document.body.append(out);
const ctx=out.getContext('2d',{alpha:false,willReadFrequently:!live});
const normalized=width/1080;
const vignette=document.createElement('canvas');vignette.width=540;vignette.height=960;
{
  const c=vignette.getContext('2d');
  c.save();c.translate(270,458);c.scale(1,1.72);
  const g=c.createRadialGradient(0,0,115,0,0,339);
  g.addColorStop(0,'rgba(23,14,17,0)');g.addColorStop(.63,'rgba(25,17,17,.035)');g.addColorStop(1,'rgba(14,10,16,.47)');
  c.fillStyle=g;c.fillRect(-270,-280,540,570);c.restore();
}
function tracking(text,x,y,spacing){
  const glyphs=[...text];
  const measures=glyphs.map(c=>ctx.measureText(c).width);
  const tw=measures.reduce((a,b)=>a+b,0)+(glyphs.length-1)*spacing;
  let p=x-tw/2;
  for(let i=0;i<glyphs.length;i++){ctx.fillText(glyphs[i],p,y);p+=measures[i]+spacing;}
}
function title(t){
  const opacity=phase(t,.36,1.45)*(1-phase(t,4.53,6.2));
  if(opacity===0)return;
  ctx.save();
  ctx.globalAlpha=opacity;
  ctx.fillStyle='#fff0d0';ctx.textAlign='left';ctx.textBaseline='alphabetic';
  ctx.font='106px Georgia, "Noto Serif", serif';
  ctx.shadowColor='rgba(39,20,12,.48)';ctx.shadowBlur=21;ctx.shadowOffsetY=5;
  tracking('NANJING',540,327,13.4);
  ctx.restore();
}
function caption(t){
  const i=capTimes.findIndex(([a,b])=>a<t&&t<b);
  if(i<0)return;
  const [a,b]=capTimes[i],opacity=phase(t,a,a+.40)*(1-phase(t,b-.44,b));
  const s=stops[i];
  ctx.save();ctx.globalAlpha=opacity;
  const bg=ctx.createLinearGradient(0,1465,0,1905);
  bg.addColorStop(0,'rgba(20,16,16,0)');bg.addColorStop(.48,'rgba(21,17,18,.43)');bg.addColorStop(1,'rgba(17,15,18,.51)');
  ctx.fillStyle=bg;ctx.fillRect(0,1450,1080,470);
  ctx.translate(89,1566+8*(1-opacity));
  ctx.shadowColor='rgba(17,12,10,.55)';ctx.shadowBlur=8;ctx.shadowOffsetY=2;
  ctx.fillStyle='#efcf95';ctx.fillRect(2,8,29,2);
  ctx.font='22px "DejaVu Sans", sans-serif';ctx.fillText(s.number,43,16);
  ctx.fillStyle='#fff2d8';ctx.font='62px "Noto Serif CJK SC", serif';ctx.fillText(s.zh,0,92);
  ctx.font='31px Georgia, serif';ctx.fillStyle='#f7ddae';ctx.fillText(s.en,3,144);
  ctx.restore();
}
function project(p){
  const q=p.clone().project(camera);
  return [(q.x*.5+.5)*1080,(.5-q.y*.5)*1920,q.z];
}
const bursts=[];
const burstRandom=seeded(8823);
function explosion(t,position,sz,colors,count){
  const sparks=[];
  for(let i=0;i<count;i++){
    const u=(i+.5)/count, y=1-2*u, a=i*2.399963+burstRandom()*.25;
    const shell=Math.sqrt(1-y*y);
    const dir=V(Math.cos(a)*shell,y,Math.sin(a)*shell);
    sparks.push({dir,speed:(.69+burstRandom()*.41)*sz,life:1.72+burstRandom()*1.32,phase:burstRandom()*PI*2,color:colors[Math.floor(burstRandom()*colors.length)],tail:.11+burstRandom()*.21});
  }
  bursts.push({t,position,sparks});
}
explosion(49.14,V(-2.35,5.24,-3.7),2.40,['255,206,121','255,229,169','255,153,97'],126);
explosion(50.23,V(2.37,5.65,-4.20),2.12,['255,130,121','251,181,154','255,221,180'],112);
explosion(51.71,V(.10,6.66,-5.0),2.60,['255,210,117','255,242,188','255,154,81'],160);
explosion(52.86,V(-3.11,5.96,-5.55),1.60,['143,203,227','235,233,204','137,223,195'],90);
explosion(53.30,V(3.03,6.59,-5.32),2.11,['255,160,131','255,219,148','238,116,153'],128);
explosion(54.26,V(.66,5.66,-2.60),1.27,['255,211,125','255,164,98','255,235,177'],76);
function fireworks(t){
  if(t<48.3)return;
  ctx.save();ctx.globalCompositeOperation='screen';
  for(const burst of bursts){
    const time=t-burst.t,center=burst.position;
    if(time<-.75||time>3.1)continue;
    if(time<0){
      const p=center.clone();p.y=lerp(.18,center.y,Math.pow(clamp((time+.75)/.75),.80));
      const q=p.clone();q.y-=.49;
      const [x,y]=project(p),[a,b]=project(q);
      const grad=ctx.createLinearGradient(x,y,a,b);
      grad.addColorStop(0,'rgba(255,222,149,.8)');grad.addColorStop(1,'rgba(238,121,63,0)');
      ctx.strokeStyle=grad;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(a,b);ctx.stroke();
      continue;
    }
    const tailPoint=(s,d)=>{
      const speed=(1-Math.exp(-1.15*d))*s.speed;
      const p=center.clone().addScaledVector(s.dir,speed);
      p.y-=.205*d*d;
      return project(p);
    };
    const [cx,cy]=project(center);
    if(time<.35){
      const d=45+time*120,g=ctx.createRadialGradient(cx,cy,0,cx,cy,d);
      g.addColorStop(0,'rgba(255,222,150,'+(.38*(1-time/.35))+')');g.addColorStop(1,'rgba(255,171,85,0)');
      ctx.fillStyle=g;ctx.fillRect(cx-d,cy-d,d*2,d*2);
    }
    for(const s of burst.sparks){
      if(time>s.life)continue;
      const bright=Math.pow(1-time/s.life,1.38)*(.70+.3*Math.sin(time*27+s.phase));
      const [x,y,z]=tailPoint(s,time);
      if(z<0||z>1||x< -100||x>1180||y< -100||y>2020)continue;
      const [a,b]=tailPoint(s,Math.max(0,time-s.tail));
      if(Math.hypot(a-x,b-y)<.1)continue;
      ctx.strokeStyle='rgba('+s.color+','+(bright*.28)+')';ctx.lineWidth=6.8;
      ctx.beginPath();ctx.moveTo(a,b);ctx.lineTo(x,y);ctx.stroke();
      const g=ctx.createLinearGradient(a,b,x,y);
      g.addColorStop(0,'rgba('+s.color+',0)');g.addColorStop(1,'rgba('+s.color+','+(bright*.93)+')');
      ctx.strokeStyle=g;ctx.lineWidth=2.05;ctx.stroke();
      ctx.fillStyle='rgba(255,243,213,'+(bright*.86)+')';ctx.fillRect(x-.88,y-.88,1.76,1.76);
    }
  }
  ctx.restore();
}

const dsun=new THREE.Color('#ffe4c2'),nsun=new THREE.Color('#91a9e6');
const damb=new THREE.Color('#fff1dc'),namb=new THREE.Color('#829ac8');
const dground=new THREE.Color('#7b624c'),nground=new THREE.Color('#473955');
const dfog=new THREE.Color('#4c3125'),nfog=new THREE.Color('#211b26');
const dfill=new THREE.Color('#e5edf0'),nfill=new THREE.Color('#d49b5d');

function render(t){
  t=Math.max(0,Math.min(55,t));
  const [tx,ty,tz,x,y,z,fov]=evaluate(t);
  camera.position.set(x,y,z);camera.fov=fov;camera.updateProjectionMatrix();
  camera.lookAt(tx,ty,tz);
  camera.updateMatrixWorld();
  focus.value=camera.position.distanceTo(V(tx,ty,tz));

  const dusk=phase(t,41.9,49.6), night=phase(t,45.2,51.0);
  ambient.color.copy(damb).lerp(namb,dusk);
  ambient.groundColor.copy(dground).lerp(nground,dusk);
  ambient.intensity=lerp(1.63,.94,dusk);
  sun.color.copy(dsun).lerp(nsun,dusk);
  sun.intensity=lerp(2.05,.74,dusk);
  sun.position.set(lerp(-7,-4,dusk),lerp(12,8,dusk),lerp(5,3.5,dusk));
  fill.color.copy(dfill).lerp(nfill,dusk);
  fill.intensity=lerp(.43,1.07,dusk);
  fill.position.set(lerp(6,2.5,dusk),lerp(4,5,dusk),lerp(-8,8,dusk));
  const paperBlend=phase(t,6.02,6.57);
  mapFlat.color.setRGB(lerp(1.30,.195,dusk),lerp(1.25,.26,dusk),lerp(1.13,.44,dusk));
  table.material.color.setRGB(lerp(1.16,.18,dusk),lerp(1.06,.20,dusk),lerp(1.00,.36,dusk));
  sunRay.value.set(lerp(.55,.50,dusk),-1,lerp(-.44,.23,dusk));
  scene.fog.color.copy(dfog).lerp(nfog,dusk);
  scene.background.copy(scene.fog.color);
  scene.fog.near=9+Math.max(0,y-4)*1.6;
  scene.fog.far=scene.fog.near+27;
  for(const [name,a] of art){
    const click=phase(t,44.4+(name.length%4)*.53,49.0+(name.length%3)*.45);
    a.face.emissiveIntensity=click*(name==='temple'?2.65:1.94);
  }
  for(let i=0;i<lights.length;i++)lights[i].material.opacity=phase(t,44.4+i*.39,48+i*.41)*.53;
  lineMat.color.setRGB(lerp(.402,.80,night),lerp(.057,.27,night),lerp(.019,.042,night));
  under.material.opacity=lerp(.20,.53,phase(t,2,5.8));
  const openingZ=[1.1,0,.50];
  const openingX=[3.05,0,2.58];
  rows.forEach(({fold,wings},i)=>{
    const s=i-1;
    const amount=1-phase(t,openingZ[i],openingZ[i]+2.51);
    fold.rotation.x=-s*(PI-.085)*amount;
    fold.position.y=(i===0?.072:i===2?.035:0)*amount;
    wings.forEach((hinge,j)=>{
      const sign=j-1;
      const f=1-phase(t,openingX[j]+(i===1?0:.14*i),openingX[j]+2.57+(i===1?0:.14*i));
      hinge.rotation.z=sign*(PI-.145)*f;
      hinge.position.y=(j===0?.041:j===2?.020:0)*f;
    });
  });
  creaseG.visible=t>5.95;
  for(const c of cards){
    const p=phase(t,c.delay,c.delay+c.duration);
    c.base.visible=t>6.23 && t>c.delay-.38;
    c.shade.visible=c.silhouetteShadow.visible=c.base.visible;
    if(!c.base.visible)continue;
    const flex=Math.sin(p*PI*2)*Math.sin(p*PI)*.025;
    const a=lerp(-PI/2+.012,0,p)+flex;
    c.leaf.rotation.x=a;
    c.shade.material.opacity=c.shadeStrength*(.40+.60*p);
    c.silhouetteShadow.material.uniforms.strength.value=lerp(.32,.18,dusk)*(.29+.71*p);
    for(const {support,lx,dd} of c.glues){
      const y=c.h*.176*Math.cos(a),z=c.h*.176*Math.sin(a);
      const end=-Math.max(dd*.72,.075);
      support.position.set(lx,y*.5,(z+end)*.5-.015);
      support.scale.y=Math.hypot(y,z-end);
      support.rotation.x=Math.atan2(z-end,y);
    }
  }
  marks.forEach((m,i)=>m.forEach(o=>o.visible=t>Math.max(6.6,stops[i].visit-.65)));
  let there=null;
  routeMeshes.forEach((r,i)=>{
    const [a,b]=travelTimes[i],q=phase(t,a,b);
    for(const layer of r.layers){
      layer.visible=q>0;
      const count=Math.floor(layer.geometry.attributes.position.count*q/6)*6;
      layer.geometry.setDrawRange(0,count);
    }
    if(q>0&&q<1)there=r.at(r.dist*q);
  });
  activeDot.visible=activeGlow.visible=Boolean(there);
  if(there){activeDot.position.set(there.x,.079,there.z);activeGlow.position.set(there.x,.080,there.z);}
  ctx.setTransform(1,0,0,1,0,0);
  function exposePaper(flat,opacity){
    renderer.shadowMap.enabled=physicalUnfoldShadows&&!flat;
    tableShadow.visible=renderer.shadowMap.enabled;
    for(const panel of frontPanels)panel.material=flat?mapFlat:mapMat;
    renderer.render(scene,camera);
    ctx.globalAlpha=opacity;
    ctx.drawImage(renderer.domElement,0,0);
  }
  if(paperBlend<1)exposePaper(false,1);
  if(paperBlend>0)exposePaper(true,paperBlend);
  ctx.globalAlpha=1;
  ctx.setTransform(normalized,0,0,normalized,0,0);
  ctx.drawImage(vignette,0,0,1080,1920);
  fireworks(t);
  title(t);caption(t);
  if(t<.23){
    ctx.fillStyle='rgba(12,9,10,'+(1-phase(t,0,.23))+')';ctx.fillRect(0,0,1080,1920);
  }
}
window.film={
  render,
  async jpeg(t,quality=.92){
    render(t);
    if(!live) return out.convertToBlob({type:'image/jpeg',quality});
    return new Promise((resolve,reject)=>out.toBlob(b=>b?resolve(b):reject(new Error('Canvas encoding failed')),'image/jpeg',quality));
  },
  duration:55,
  routes:routeMeshes.map(r=>r.dist)
};
if(live){
  const start=performance.now();
  function tick(now){render(((now-start)/1000)%55);requestAnimationFrame(tick);}
  requestAnimationFrame(tick);
}else render(2);
