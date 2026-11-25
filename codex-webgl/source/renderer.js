function matrixProduct(a,b) {
  const c = new Float32Array(16);
  for(let column=0;column<4;column++) for(let row=0;row<4;row++) {
    c[column*4+row] = a[row]*b[column*4] + a[4+row]*b[column*4+1]
      + a[8+row]*b[column*4+2] + a[12+row]*b[column*4+3];
  }
  return c;
}

function camera(width,height) {
  const eye = [19.5,-391,8.5];
  const target = [-8,-4,52];
  const forward = unit(sub(target,eye));
  const right = unit(cross(forward,[0,0,1]));
  const up = cross(right,forward);
  const lensY = Math.tan(23.7*Math.PI/180);
  const lens = [lensY*width/height,lensY];
  const lensShift = .065;
  const view = new Float32Array([
    right[0],up[0],-forward[0],0,
    right[1],up[1],-forward[1],0,
    right[2],up[2],-forward[2],0,
    -dot(right,eye),-dot(up,eye),dot(forward,eye),1,
  ]);
  const near=.45, far=2200;
  const projection = new Float32Array([
    1/lens[0],0,0,0,0,1/lens[1],0,0,
    0,lensShift/lensY,-(far+near)/(far-near),-1,0,0,-2*far*near/(far-near),0,
  ]);
  const viewProjection = matrixProduct(projection,view);
  const reflection = new Float32Array(viewProjection);
  for(let i=8;i<12;i++) reflection[i] *= -1;
  return {eye,forward,right,up,lens,lensShift,viewProjection,reflection};
}

function renderFrame(width,height) {
  const canvas = document.getElementById('frame');
  canvas.width=width;
  canvas.height=height;
  const gl = canvas.getContext('webgl2',{alpha:false,antialias:false,preserveDrawingBuffer:true});
  if(!gl) throw new Error('WebGL 2 is unavailable. Use a WebGL 2 capable Chromium build.');
  if (Math.max(width,height) > Math.min(gl.getParameter(gl.MAX_TEXTURE_SIZE),gl.getParameter(gl.MAX_RENDERBUFFER_SIZE))) {
    throw new Error('This WebGL renderer cannot allocate a framebuffer at the requested size.');
  }
  if(!gl.getExtension('EXT_color_buffer_float')) throw new Error('WebGL floating-point framebuffers are unavailable.');
  gl.disable(gl.CULL_FACE);
  gl.disable(gl.DITHER);

  function shader(type,source,label) {
    const object=gl.createShader(type);
    gl.shaderSource(object,source);
    gl.compileShader(object);
    if(!gl.getShaderParameter(object,gl.COMPILE_STATUS)) {
      throw new Error(`${label}: ${gl.getShaderInfoLog(object)}`);
    }
    return object;
  }
  function program(label,vertex,fragment) {
    const object=gl.createProgram();
    gl.attachShader(object,shader(gl.VERTEX_SHADER,vertex,label));
    gl.attachShader(object,shader(gl.FRAGMENT_SHADER,fragment,label));
    gl.linkProgram(object);
    if(!gl.getProgramParameter(object,gl.LINK_STATUS)) throw new Error(`${label}: ${gl.getProgramInfoLog(object)}`);
    const locations=new Map();
    const uniform=name=>{
      if (!locations.has(name)) locations.set(name,gl.getUniformLocation(object,name));
      return locations.get(name);
    };
    return {object,uniform};
  }
  function framebuffer(w,h,{ depth=false, bytes=false, mipmap=false }={}) {
    const texture=gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D,texture);
    gl.texImage2D(gl.TEXTURE_2D,0,bytes?gl.RGBA8:gl.RGBA16F,w,h,0,gl.RGBA,bytes?gl.UNSIGNED_BYTE:gl.HALF_FLOAT,null);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,mipmap?gl.LINEAR_MIPMAP_LINEAR:gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,mipmap?gl.REPEAT:gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,mipmap?gl.REPEAT:gl.CLAMP_TO_EDGE);
    const target=gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER,target);
    gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,texture,0);
    if(depth) {
      const buffer=gl.createRenderbuffer();
      gl.bindRenderbuffer(gl.RENDERBUFFER,buffer);
      gl.renderbufferStorage(gl.RENDERBUFFER,gl.DEPTH_COMPONENT24,w,h);
      gl.framebufferRenderbuffer(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.RENDERBUFFER,buffer);
    }
    if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE) throw new Error(`Incomplete framebuffer ${w} × ${h}.`);
    return {target,texture,w,h};
  }
  function renderTo(target) {
    gl.bindFramebuffer(gl.FRAMEBUFFER,target?.target ?? null);
    gl.viewport(0,0,target?.w ?? width,target?.h ?? height);
  }
  function bindTexture(p,name,unit,texture) {
    gl.activeTexture(gl.TEXTURE0+unit);
    gl.bindTexture(gl.TEXTURE_2D,texture);
    gl.uniform1i(p.uniform(name),unit);
  }
  function uploadSurface(mesh) {
    const vao=gl.createVertexArray();
    gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(mesh.vertices),gl.STATIC_DRAW);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,gl.createBuffer());
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint32Array(mesh.indices),gl.STATIC_DRAW);
    for(const [index,count,offset] of [[0,3,0],[1,3,12],[2,2,24]]) {
      gl.enableVertexAttribArray(index);
      gl.vertexAttribPointer(index,count,gl.FLOAT,false,32,offset);
    }
    return {vao,count:mesh.indices.length};
  }
  const screen=gl.createVertexArray();
  gl.bindVertexArray(screen);
  gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0);
  gl.vertexAttribPointer(0,2,gl.FLOAT,false,8,0);
  function fullscreen() {
    gl.bindVertexArray(screen);
    gl.drawArrays(gl.TRIANGLES,0,3);
  }

  const sky=program('sky',fullscreenVertex,skyFragment);
  const ice=program('ice lattice',fullscreenVertex,iceFragment);
  const surface=program('surface',surfaceVertex,surfaceFragment);
  const water=program('water',surfaceVertex,waterFragment);
  const bloom=program('bloom',fullscreenVertex,bloomFragment);
  const finish=program('finish',fullscreenVertex,finishFragment);
  const lattice=framebuffer(768,576,{bytes:true,mipmap:true});
  renderTo(lattice);
  gl.useProgram(ice.object);
  fullscreen();
  gl.bindTexture(gl.TEXTURE_2D,lattice.texture);
  gl.generateMipmap(gl.TEXTURE_2D);

  const foliage=gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D,foliage);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);
  gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,foliageAtlas());
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  gl.generateMipmap(gl.TEXTURE_2D);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);

  const cam=camera(width,height);
  const scene=buildScene(cam.eye);
  const objects=scene.entries.map(({mesh,...entry})=>({...uploadSurface(mesh),...entry}));
  const lake=uploadSurface(scene.water);
  function drawSurface(object) {
    gl.bindVertexArray(object.vao);
    gl.drawElements(gl.TRIANGLES,object.count,gl.UNSIGNED_INT,0);
  }
  function drawScene(target,mirror) {
    renderTo(target);
    gl.disable(gl.DEPTH_TEST);
    gl.useProgram(sky.object);
    gl.uniform3fv(sky.uniform('uForward'),cam.forward);
    gl.uniform3fv(sky.uniform('uRight'),cam.right);
    gl.uniform3fv(sky.uniform('uUp'),cam.up);
    gl.uniform2fv(sky.uniform('uLens'),cam.lens);
    gl.uniform1f(sky.uniform('uLensShift'),cam.lensShift);
    gl.uniform1i(sky.uniform('uMirror'),mirror);
    fullscreen();
    gl.enable(gl.DEPTH_TEST);
    gl.clear(gl.DEPTH_BUFFER_BIT);
    gl.useProgram(surface.object);
    const eye = mirror ? [cam.eye[0],cam.eye[1],-cam.eye[2]] : cam.eye;
    gl.uniform3fv(surface.uniform('uEye'),eye);
    gl.uniformMatrix4fv(surface.uniform('uViewProjection'),false,mirror?cam.reflection:cam.viewProjection);
    bindTexture(surface,'uIce',0,lattice.texture);
    bindTexture(surface,'uLeaves',1,foliage);
    function drawMaterial(object) {
      gl.uniform3fv(surface.uniform('uColor'),object.color);
      gl.uniform4fv(surface.uniform('uInfo'),object.info);
      gl.uniform1i(surface.uniform('uMaterial'),object.material);
      drawSurface(object);
    }
    for(const object of objects) if(object.material!==8) drawMaterial(object);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE,gl.ONE);
    gl.depthMask(false);
    for(const object of objects) if(object.material===8) drawMaterial(object);
    gl.depthMask(true);
    gl.disable(gl.BLEND);
  }

  const reflected=framebuffer(Math.round(width*.52),Math.round(height*.52),{depth:true});
  const frame=framebuffer(width,height,{depth:true});
  drawScene(reflected,true);
  drawScene(frame,false);
  gl.useProgram(water.object);
  gl.uniform3fv(water.uniform('uEye'),cam.eye);
  gl.uniform2f(water.uniform('uResolution'),width,height);
  gl.uniformMatrix4fv(water.uniform('uViewProjection'),false,cam.viewProjection);
  bindTexture(water,'uReflection',2,reflected.texture);
  drawSurface(lake);

  gl.disable(gl.DEPTH_TEST);
  const bloomWidth=Math.ceil(width/5),bloomHeight=Math.ceil(height/5);
  const glowX=framebuffer(bloomWidth,bloomHeight);
  const glowY=framebuffer(bloomWidth,bloomHeight);
  function blur(target,input,dx,dy,extract) {
    renderTo(target);
    gl.useProgram(bloom.object);
    bindTexture(bloom,'uTexture',0,input.texture);
    gl.uniform2f(bloom.uniform('uStep'),dx,dy);
    gl.uniform1i(bloom.uniform('uExtract'),extract);
    fullscreen();
  }
  blur(glowX,frame,.53/bloomWidth,0,true);
  blur(glowY,glowX,0,1/bloomHeight,false);
  renderTo(null);
  gl.useProgram(finish.object);
  bindTexture(finish,'uTexture',0,frame.texture);
  bindTexture(finish,'uBloom',1,glowY.texture);
  fullscreen();
  gl.finish();
  const error=gl.getError();
  if(error!==gl.NO_ERROR) throw new Error(`WebGL error ${error}.`);
  return canvas.toDataURL('image/png');
}
