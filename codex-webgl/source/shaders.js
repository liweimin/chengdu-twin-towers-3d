const fullscreenVertex = `#version 300 es
layout(location=0) in vec2 aPosition;
out vec2 vScreen;
void main() {
  vScreen = aPosition * .5 + .5;
  gl_Position = vec4(aPosition, 0., 1.);
}`;

const surfaceVertex = `#version 300 es
layout(location=0) in vec3 aPosition;
layout(location=1) in vec3 aNormal;
layout(location=2) in vec2 aUV;
uniform mat4 uViewProjection;
out vec3 vWorld;
out vec3 vNormal;
out vec2 vUV;
void main() {
  vWorld = aPosition;
  vNormal = aNormal;
  vUV = aUV;
  gl_Position = uViewProjection * vec4(aPosition, 1.);
}`;

const noiseGL = `
float sat(float x) { return clamp(x, 0., 1.); }
float hash(vec2 p) {
  vec3 q = fract(vec3(p.xyx) * .1031);
  q += dot(q, q.yzx + 33.33);
  return fract((q.x + q.y) * q.z);
}
vec2 hash2(vec2 p) {
  return vec2(hash(p), hash(p + vec2(41.72, 17.17)));
}
float noise(vec2 p) {
  vec2 cell = floor(p), f = fract(p);
  vec2 w = f*f*(3.-2.*f);
  return mix(mix(hash(cell), hash(cell+vec2(1,0)), w.x),
             mix(hash(cell+vec2(0,1)), hash(cell+vec2(1,1)), w.x), w.y);
}
float clouds(vec2 p) {
  mat2 spin = mat2(.84,.54,-.54,.84);
  float n = .50*noise(p);
  p = spin*p*2.04 + 9.2;
  n += .25*noise(p);
  p = spin*p*2.07 - 4.7;
  n += .125*noise(p);
  p = spin*p*2.04 + 12.6;
  n += .063*noise(p) + .035*noise(p*2.07-2.1) + .017*noise(p*4.1);
  return n;
}
const vec3 sunDir = normalize(vec3(-.57, .82, .047));
const vec3 sunKey = normalize(vec3(-.87, -.34, .30));
vec3 airColor(vec3 ray) {
  float w = pow(sat(dot(normalize(vec3(ray.xy,0.)), normalize(vec3(sunDir.xy,0.)))), 6.);
  return mix(vec3(.215,.274,.356),vec3(.67,.352,.223),w);
}
vec3 aerial(vec3 c, vec3 point, vec3 eye) {
  vec3 v = point - eye;
  float haze = 1.-exp(-length(v)*.00029*exp(-max(point.z,0.)*.0036));
  return mix(c, airColor(v), haze*.79);
}
vec3 clearSky(vec3 ray) {
  float altitude = max(ray.z, 0.);
  float w = pow(sat(dot(normalize(vec3(ray.xy,0.)), normalize(vec3(sunDir.xy,0.)))), 5.);
  vec3 horizon = mix(vec3(.48,.53,.63), vec3(1.25,.598,.30), w);
  vec3 blue = mix(vec3(.195,.311,.472),vec3(.083,.179,.312),smoothstep(.22,.72,altitude));
  float band = 1.-exp(-altitude*6.9);
  float angle = max(0., 1.-dot(ray,sunDir));
  vec3 c = mix(horizon, blue, band);
  c += vec3(.63,.246,.062)*exp(-angle*32.)*exp(-altitude*1.9);
  c += vec3(.43,.142,.029)*exp(-angle*650.);
  return c;
}
`;

const skyFragment = `#version 300 es
precision highp float;
in vec2 vScreen;
out vec4 frag;
uniform vec3 uForward, uRight, uUp;
uniform vec2 uLens;
uniform float uLensShift;
uniform bool uMirror;
${noiseGL}
void main() {
  vec2 xy = (vScreen*2.-1.)*uLens;
  xy.y += uLensShift;
  vec3 ray = normalize(uForward + xy.x*uRight + xy.y*uUp);
  if (uMirror) ray.z = -ray.z;
  vec3 c = clearSky(ray);
  float z = max(.015, ray.z);
  vec2 p = ray.xy/(z+.09);
  vec2 upper = p*vec2(2.9,2.2) + vec2(-6.3,11.1);
  upper += vec2(noise(upper*.54), noise(upper*.48+7.3))*1.45;
  float high = clouds(upper*vec2(1.0,1.65));
  float veil = smoothstep(.43,.71,high)*smoothstep(.014,.10,z);
  c = mix(c, c*vec3(1.13,.99,1.00)+vec3(.079,.030,.016), veil*.42);

  vec2 lower = p * vec2(1.15,1.85) + vec2(22.2,5.3);
  lower += .98*vec2(noise(lower*.80+7.3), noise(lower*.61-4.));
  float density = clouds(lower)*.89 + .11*clouds(lower*vec2(1.85,3.9)+vec2(8.5,1.2));
  float cover = .515 + .064*sin(p.x*.78-1.1) + .025*sin(p.y*.72+1.5);
  float cloud = smoothstep(cover-.054,cover+.155,density);
  float depth = smoothstep(cover-.008,cover+.18,density);
  float side = clouds(lower+vec2(-.12,.22))-density;
  float light = sat(.38+.45*exp(-depth*2.4)+side*4.8);
  float warm = pow(sat(dot(ray,sunDir)),13.)*(.6+.4*exp(-z*4.));
  vec3 shadow = mix(vec3(.108,.154,.236),vec3(.305,.157,.161),warm);
  vec3 lit = mix(vec3(.36,.401,.49),vec3(.91,.498,.322),warm);
  vec3 cloudColor = mix(shadow,lit,light);
  cloudColor += vec3(.20,.084,.047)*warm*max(0.,side*3.)*(1.-depth);
  c = mix(c, cloudColor, cloud * .84 * smoothstep(.002,.062,z));
  float smallBand = smoothstep(.49,.72,clouds(vec2(p.x*.9,p.y*3.9)+vec2(7.6,3.1)));
  c = mix(c, vec3(.39,.325,.350), smallBand*.24*exp(-pow((z-.056)*14.,2.)));
  frag = vec4(c,1.);
}`;

const iceFragment = `#version 300 es
precision highp float;
in vec2 vScreen;
out vec4 frag;
${noiseGL}
vec2 seed(vec2 cell) {
  vec2 id = mod(cell, vec2(24,18));
  return cell + vec2(.23*mod(cell.y,2.),0.) + .19 + .61*hash2(id);
}
void main() {
  vec2 p = vScreen*vec2(24,18), cell = floor(p), first = vec2(0), firstCell = vec2(0);
  float distanceSquared = 100.;
  for (int y=-1; y<=1; y++) for (int x=-1; x<=1; x++) {
    vec2 g = cell+vec2(x,y), delta = seed(g)-p;
    float d = dot(delta,delta);
    if (d<distanceSquared) { distanceSquared=d; first=delta; firstCell=g; }
  }
  float edge = 10.;
  vec2 axis = vec2(0);
  for (int y=-2; y<=2; y++) for (int x=-2; x<=2; x++) {
    vec2 g = cell+vec2(x,y), delta = seed(g)-p, diff = delta-first;
    if (dot(diff,diff)>.00001) {
      vec2 n = normalize(diff);
      float d = dot(.5*(delta+first),n);
      if (d<edge) { edge=d; axis=n; }
    }
  }
  float angle = dot(axis, vec2(-.63,.77));
  float bend = (noise(p*1.18)-.5)*.058;
  float width = .066 + .021*hash(mod(firstCell,vec2(24,18))) + bend*.42;
  float mesh = 1.-smoothstep(width-.018,width+.018,edge+bend);
  float bevel = smoothstep(.005,.067,edge)*mesh;
  frag = vec4(mesh,.5+.45*angle*bevel,hash(mod(firstCell,vec2(24,18))),1.);
}`;

const surfaceFragment = `#version 300 es
precision highp float;
in vec3 vWorld, vNormal;
in vec2 vUV;
out vec4 frag;
uniform vec3 uEye, uColor;
uniform vec4 uInfo;
uniform int uMaterial;
uniform sampler2D uIce, uLeaves;
${noiseGL}

float joint(float q, float width) {
  float fw = max(fwidth(q)*.76,.001);
  return (1.-smoothstep(max(0.,width-fw),width+fw,abs(fract(q+.5)-.5)))*min(1.,width*1.75/fw);
}

vec3 windowWall(vec2 st, vec3 n, vec3 view, bool tower) {
  float paneWidth = tower ? 1.29 : uInfo.y;
  float floorHeight = uInfo.x;
  vec2 pane = vec2(st.x/paneWidth+uInfo.w, st.y/floorHeight);
  vec2 id = floor(pane), f = fract(pane);
  float seed = uInfo.z;
  float rough = hash(id+vec2(6.1,seed));
  float row = hash(vec2(id.y*1.37,seed+5.));
  float tenant = hash(vec2(floor(id.x/4.3)+seed, id.y));
  float exposure = .64+.53*hash(vec2(id.x*2.,seed-12.));
  float reflectance = pow(1.-sat(dot(view,n)),2.1);
  vec3 reflectRay = reflect(-view, n);
  reflectRay.z += (hash(id+seed+41.)-.5)*.033;
  vec3 sunset = clearSky(normalize(reflectRay));
  float band = noise(vec2(st.x*.043+seed, st.y*.041));
  float brushedSky = noise(vec2(reflectRay.x*13.7,reflectRay.z*41.8)+8.4);
  sunset *= .84+.38*brushedSky;
  float skirt = exp(-pow((st.y-38.)*.023,2.));
  vec3 reflected = mix(sunset, vec3(.054,.069,.095),(.36*band+.24)*skirt);
  float cityMask = (1.-smoothstep(14.,112.,st.y))*(.19+.81*noise(vec2(st.x*.14,seed)));
  reflected = mix(reflected,vec3(.045,.059,.064),cityMask*.51);
  float faceSun = pow(sat(dot(n,sunKey)),1.75);
  float facadeLight = .58+.55*faceSun;
  vec3 glass = uColor*(.42+.53*rough+.23*row)*facadeLight;
  glass += reflected*(.093+.38*reflectance)*exposure;
  if (tower) glass += vec3(.150,.065,.024)*faceSun*(.65+.35*band);
  float bigWindow = float(tenant*.68+rough*.32 > (tower ? .751 : .76));
  float subdued = hash(id+vec2(36.7,seed-17.23));
  float lit = bigWindow * (.21 + 1.23*pow(subdued,2.4));
  if (tower && (mod(id.y+2.,15.)<.5 || st.y>206.)) lit *= .055;
  float trim = smoothstep(.10,.18,f.y)*(1.-smoothstep(.73,.81,f.y));
  float aafade = 1.-smoothstep(.14,1.2,fwidth(pane.x)+fwidth(pane.y));
  trim = mix(.60,trim,aafade);
  float ceiling = smoothstep(.65,.735,f.y)*(1.-smoothstep(.75,.80,f.y))*aafade;
  float blinds = 1.-smoothstep(.16,.28,f.x)*.20;
  float stripes = (1.-joint(pane.y*16.,.16)*.28);
  float stripesMask = smoothstep(.61,.83,hash(vec2(id.x+seed,id.y+4.)));
  float colorTemperature = hash(vec2(floor(id.x/4.3)+seed*.15,id.y+12.7));
  vec3 warm = mix(vec3(1.65,.67,.21),vec3(.55,.88,1.01),smoothstep(.61,.97,colorTemperature));
  warm *= mix(.76,1.31,row);
  float curtainGlow = smoothstep(.18,.75,noise(vec2(f.x*4.0,id.y+id.x*13.0)));
  glass += warm*lit*(trim*blinds*(.48+.36*f.y+.18*curtainGlow)*mix(1.,stripes,stripesMask)+ceiling*.62);
  float slab = max(joint(pane.y,.092), joint(pane.y+.23,.036)*.48);
  float mullion = joint(pane.x,.051);
  glass = mix(glass, glass*.30 + vec3(.012,.016,.021), max(slab*.77,mullion*.88));
  glass += .016*joint(pane.x-.060,.023)*max(0.,-n.x+.3);
  return glass;
}

void main() {
  vec3 n = normalize(vNormal), view = normalize(uEye-vWorld);
  float diffuse = .54+.46*sat(dot(n,sunKey));
  vec3 c;
  if (uMaterial == 8) {
    vec2 st = vUV*2.-1.;
    float r = dot(st,st);
    float halo = exp(-r*7.6)*.31 + exp(-r*49.)*.92 + exp(-r*365.)*2.9;
    halo *= 1.-smoothstep(.59,1.,r);
    frag = vec4(halo*uColor,1.);
    return;
  }
  if (uMaterial == 0 || uMaterial == 1) {
    bool tower = uMaterial == 1;
    vec2 st = vUV;
    if (tower) {
      vec3 tangent = normalize(cross(vec3(0,0,1),n));
      float vn = .38 + .62*abs(dot(view,n));
      st.x += dot(view,tangent)*.76/vn;
      st.y -= view.z*.64/vn;
    }
    c = windowWall(st,n,view,tower);
    if (tower) {
      vec2 q = vec2(vUV.x/(24.*.68),vUV.y/(18.*.65));
      vec3 ice = texture(uIce,q).rgb;
      float f = pow(1.-sat(dot(n,view)),3.4);
      float skyward = sat(n.z*.7+.55);
      float local = noise(vUV*.105+uInfo.z);
      float b = noise(vec2(vUV.x*.023,vUV.y*.039)+2.1);
      vec3 silver = mix(vec3(.071,.120,.185),vec3(.19,.259,.329),skyward);
      silver *= (.88+.17*local+.15*ice.g)*(.49+.72*diffuse);
      silver += vec3(.46,.219,.079)*pow(sat(dot(n,sunKey)),2.3)*(.55+.61*b);
      silver += vec3(.10,.17,.25)*f;
      float maintenance = joint(vUV.y/16.5,.014)*.54;
      float horizontal = joint(vUV.y/1.82,.025)*.30;
      c = mix(c, silver, min(1.,ice.r*(.78+.20*f)+horizontal+maintenance));
      c *= 1.-.12*joint(vUV.y/16.5-.019,.015);
      float crown = smoothstep(211.2,217.1,vWorld.z);
      c = mix(c, silver*.74, crown*.56);
    }
  } else if (uMaterial == 2) {
    float rough = noise(vWorld.xy*3.1+vWorld.z) * .135 + .11*noise(vWorld.xz*.31);
    float tiles = joint(vUV.x/1.6,.014)*.14 + joint(vUV.y/.48,.016)*.21;
    c = uColor*(diffuse + rough-tiles);
  } else if (uMaterial == 3) {
    c = uColor;
  } else if (uMaterial == 4) {
    vec4 leaf = texture(uLeaves,vUV);
    if (leaf.a < .45) discard;
    c = leaf.rgb * leaf.rgb * uColor;
  } else if (uMaterial == 5) {
    float earth = noise(vWorld.xy*.071);
    float mixGrass = noise(vWorld.xy*.47)*.30 + earth*.38 + noise(vWorld.xy*3.9)*.18;
    c = uColor*(.46+mixGrass*.78);
  } else if (uMaterial == 6) {
    float th = joint(vUV.x/.38,.11);
    float tier = .48+.44*noise(vUV*.25);
    c = uColor*(.62+diffuse*.42+th*.64)*tier;
    c += vec3(.095,.065,.043)*th*pow(diffuse,4.);
  } else if (uMaterial == 9) {
    float standingSeam = joint(vUV.x/1.50,.050);
    float lapSeam = joint(vUV.y/.71+mod(floor(vUV.x/1.50),2.)*.5,.018);
    float tile = hash(vec2(floor(vUV.x/1.50),floor(vUV.y/.71)));
    vec3 sunset = vec3(.86,.34,.108)*pow(sat(dot(n,sunKey)),2.4);
    vec3 roof = uColor*(.43 + .41*sat(n.z) + .18*tile) + sunset*.26;
    c = roof*(1.-.43*standingSeam-.27*lapSeam) + .062*standingSeam*diffuse;
  } else {
    float line = joint(vUV.x/.33,.057);
    float tier = smoothstep(.08,.47,noise(vUV*.091));
    c = uColor*(.48+.51*diffuse+.12*line+.13*tier);
  }
  frag = vec4(aerial(c,vWorld,uEye),1.);
}`;

const waterFragment = `#version 300 es
precision highp float;
in vec3 vWorld;
out vec4 frag;
uniform vec3 uEye;
uniform vec2 uResolution;
uniform sampler2D uReflection;
${noiseGL}
void main() {
  vec2 p = vWorld.xy;
  vec3 view = normalize(uEye-vWorld);
  float broad = noise(p*vec2(.026,.072));
  float cadence = noise(p*vec2(.095,.51)+3.17);
  vec2 a = p*vec2(.15,.63);
  float wave = sin(p.y*2.27+p.x*.11+broad*6.6) + .46*sin(p.y*3.97-p.x*.16+cadence*3.9);
  float chop = noise(a*2.4+23.)-.5;
  float xp = .48*sin(p.y*.95+p.x*.12+cadence*2.)+.44*chop+.18*wave;
  float yp = .43*wave+.47*chop+.25*sin(p.y*.38+p.x*.07+broad*4.3);
  float rippleFade = 1.-smoothstep(.20,1.75,length(fwidth(p)));
  xp *= mix(.45,1.,rippleFade);
  yp *= mix(.42,1.,rippleFade);
  vec2 uv = gl_FragCoord.xy/uResolution;
  float concentration = .42+.95*pow(broad,1.7);
  vec2 offset = vec2(xp*.0056,yp*.0018)*concentration*(.64+view.z*1.2);
  vec2 w = vec2(.0019,.0014)*concentration*(.83+abs(yp)*1.4);
  vec2 q = uv+offset;
  vec3 mirror = texture(uReflection,q).rgb*.44;
  mirror += (texture(uReflection,q+vec2(w.x,w.y)).rgb + texture(uReflection,q-vec2(w.x,w.y)).rgb)*.17;
  mirror += (texture(uReflection,q+vec2(-w.x,w.y*.45)).rgb + texture(uReflection,q+vec2(w.x,-w.y*1.55)).rgb)*.11;
  float fresnel = .026+.974*pow(1.-sat(view.z+.010*yp),5.);
  vec3 bed = mix(vec3(.027,.041,.046),vec3(.041,.054,.055), broad);
  vec3 c = mix(bed,mirror*vec3(.84,.88,.96),fresnel*.88);
  float streak = sat((sin(p.y*8.6+p.x*.29+cadence*5.1)-.42)*.64);
  c += vec3(.038,.043,.048)*streak*rippleFade*smoothstep(.25,.7,broad)*(.32+.68*view.z);
  c *= .97 + chop*.049 + .017*yp;
  frag = vec4(c,1.);
}`;

const bloomFragment = `#version 300 es
precision highp float;
in vec2 vScreen;
out vec4 frag;
uniform sampler2D uTexture;
uniform vec2 uStep;
uniform bool uExtract;
vec3 fetch(vec2 p) {
  vec3 c = texture(uTexture,p).rgb;
  return uExtract ? c*max(0.,(max(c.r,max(c.g,c.b))-.63)/(max(c.r,max(c.g,c.b))+.36)) : c;
}
void main() {
  vec3 c = fetch(vScreen)*.227;
  c += (fetch(vScreen+uStep*1.385)+fetch(vScreen-uStep*1.385))*.316;
  c += (fetch(vScreen+uStep*3.231)+fetch(vScreen-uStep*3.231))*.070;
  frag = vec4(c,1.);
}`;

const finishFragment = `#version 300 es
precision highp float;
in vec2 vScreen;
out vec4 frag;
uniform sampler2D uTexture, uBloom;
${noiseGL}
void main() {
  vec3 linear = texture(uTexture,vScreen).rgb;
  vec3 bloom = texture(uBloom,vScreen).rgb;
  linear += bloom*vec3(.28,.22,.22);
  vec2 v = vScreen*2.-1.;
  float vig = 1.-.15*pow(dot(v*vec2(.79,.61),v*vec2(.79,.61)),1.37);
  linear *= vig*1.09;
  float lum = dot(linear,vec3(.2126,.7152,.0722));
  linear = mix(vec3(lum),linear,.97);
  vec3 film = linear * (1.+linear/5.0)/(1.+linear*.90);
  film = pow(max(film,vec3(0.)),vec3(.48)) - .015;
  float pixelGrain = hash(gl_FragCoord.xy*vec2(.741,1.15))-.5;
  float grain = pixelGrain + .41*(hash(floor(gl_FragCoord.xy/2.)+8.)-.5);
  film += grain*.010*(.4+.6*exp(-lum*.9));
  frag = vec4(clamp(film,0.,1.),1.);
}`;
