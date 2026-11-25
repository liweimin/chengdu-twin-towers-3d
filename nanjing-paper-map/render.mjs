import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright-core';

const mode=process.argv[2]||'video';
const output=process.argv[3]||(mode==='video'?'Nanjing.mp4':'previews');
const root=path.dirname(fileURLToPath(import.meta.url));
const w=+(process.env.FILM_WIDTH|| (mode==='stills'?432:1080));
const h=Math.round(w*16/9);
const fps=+(process.env.FILM_FPS||24);
const duration=mode==='benchmark'?2:55;
const first=+(process.env.FILM_START||0);
const frames=+(process.env.FILM_FRAMES||duration*fps);
const threads=+(process.env.FILM_ENCODER_THREADS||2);
const start=performance.now();
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg'};
let encoder,encDone,received=0;
let browser;
if(mode==='video'||mode==='benchmark'){
  const args=['-hide_banner','-loglevel','warning','-y','-thread_queue_size','8','-f','image2pipe','-c:v','mjpeg','-framerate',String(fps),'-i','pipe:0'];
  const soundtrack=path.join(root,'assets','score.wav');
  const hasAudio=mode==='video'&&fs.existsSync(soundtrack);
  if(hasAudio) args.push('-i',soundtrack,'-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','256k','-shortest');
  const target=mode==='video'&&w!==1080?'1080:1920:flags=lanczos:':'';
  args.push('-vf','scale='+target+'in_range=pc:out_range=tv,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','17','-threads',String(threads),
    '-color_primaries','bt709','-colorspace','bt709','-color_trc','bt709','-movflags','+faststart','-metadata','title=Nanjing',output);
  encoder=spawn('ffmpeg',args,{stdio:['pipe','ignore','inherit']});
  encoder.stdin.on('error',err=>console.error(err.message));
  encDone=once(encoder,'exit');
}else fs.mkdirSync(output,{recursive:true});
const server=http.createServer(async(req,res)=>{
  const url=new URL(req.url,'http://localhost');
  try{
    if(req.method==='POST'&&url.pathname==='/frame'){
      const n=+url.searchParams.get('n');
      if(n!==received) throw new Error('Frame order error at '+n+' expected '+received);
      const bufs=[];
      for await(const b of req) bufs.push(b);
      const frame=Buffer.concat(bufs);
      if(encoder){
        if(!encoder.stdin.write(frame))await once(encoder.stdin,'drain');
      }else {
        const t=+url.searchParams.get('t');
        fs.writeFileSync(path.join(output,String(t.toFixed(2)).padStart(5,'0')+'.jpg'),frame);
      }
      received++;
      if(received%96===0) console.log(received+'/'+frames, ((performance.now()-start)/1000).toFixed(1)+'s');
      res.writeHead(204).end();return;
    }
    const full=path.resolve(root,'.'+url.pathname);
    if(!full.startsWith(root+path.sep)){res.writeHead(403).end();return;}
    if(!fs.existsSync(full)||!fs.statSync(full).isFile()){res.writeHead(404).end();return;}
    res.setHeader('Content-Type',types[path.extname(full)]||'application/octet-stream');
    fs.createReadStream(full).pipe(res);
  }catch(err){console.error(err);res.writeHead(500).end(err.message);}
});
await new Promise((resolve,reject)=>server.listen(0,'127.0.0.1',resolve).on('error',reject));
try{
  browser=await chromium.launch({
    executablePath:process.env.CHROMIUM||'/usr/bin/chromium',
    headless:true,
    args:['--no-sandbox','--disable-dev-shm-usage','--enable-webgl','--enable-unsafe-swiftshader','--use-angle='+(process.env.FILM_ANGLE||'swiftshader'),'--disable-background-networking','--mute-audio']
  });
  const page=await browser.newPage({viewport:{width:128,height:128},deviceScaleFactor:1});
  page.on('pageerror',err=>console.error('Page:',err.message));
  page.on('console',msg=>{if(msg.type()==='error')console.error('Chromium:',msg.text());});
  const options=new URLSearchParams({w,h});
  if(process.env.FILM_FAST==='1')options.set('fast','');
  if(process.env.FILM_SHADOWS==='0')options.set('noshadow','');
  await page.goto('http://127.0.0.1:'+server.address().port+'/index.html?'+options,{waitUntil:'load'});
  await page.waitForFunction(()=>Boolean(window.film),{timeout:30000});
  console.log('Route lengths',await page.evaluate(()=>window.film.routes.map(v=>v.toFixed(2))));
  const times=mode==='stills'?(process.env.FILM_TIMES||'1.5,2.7,3.9,5.6,7.9,10.7,12.9,16.7,19,21,24.3,26.8,29.7,35.5,37.5,43,46,48.7,50.4,52.2,54.6').split(',').map(Number):null;
  await page.evaluate(async({times,fps,frames,first})=>{
    const count=times?.length??frames;
    for(let n=0;n<count;n++){
      const t=times?.[n]??first+n/fps;
      const image=await window.film.jpeg(t,.94);
      const res=await fetch('/frame?n='+n+'&t='+t,{method:'POST',body:image});
      if(!res.ok) throw Error(await res.text());
    }
  },{times,fps,frames,first});
  if(encoder){
    encoder.stdin.end();
    const [status]=await encDone;
    if(status!==0)throw new Error('FFmpeg exited with status '+status);
    if(received!==frames)throw new Error('Invalid frame count '+received);
  }
  console.log(received+' frames in '+((performance.now()-start)/1000).toFixed(1)+'s');
}finally{
  if(encoder&&!encoder.stdin.destroyed)encoder.stdin.end();
  if(browser)await browser.close();
  server.close();
}
