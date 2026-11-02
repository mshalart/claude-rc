const { chromium } = require('playwright');
const fs=require('fs'); const {spawn}=require('child_process');
(async()=>{
  const dir=process.argv[2], out=process.argv[3], only=process.argv[4];
  const TL=JSON.parse(fs.readFileSync(dir+'/timeline.json'));
  const CAPS=JSON.parse(fs.readFileSync(dir+'/script.json')).map(s=>({id:s.id,cap:s.cap}));
  const b=await chromium.launch(); const pg=await b.newPage({viewport:{width:1920,height:1080}});
  pg.on('console',m=>console.log('PAGE',m.text())); pg.on('pageerror',e=>console.log('ERR',e.message));
  await pg.addInitScript(`window.TL=${JSON.stringify(TL)};window.CAPS=${JSON.stringify(CAPS)};`);
  await pg.goto('file://'+dir+'/index.html'); await pg.waitForFunction(()=>window.isReady&&window.isReady());
  if(only){ for(const t of only.split(',')){await pg.evaluate(t=>seek(+t),t); await pg.screenshot({path:`${out}/shot_${t}.png`});} await b.close(); return; }
  const fps=12, N=Math.ceil(TL.total*fps);
  const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-vf','fps=24','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',out]);
  ff.stderr.on('data',d=>process.stderr.write(d));
  for(let i=0;i<N;i++){ await pg.evaluate(t=>seek(t),i/fps); const buf=await pg.screenshot({type:'jpeg',quality:92}); if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r)); if(i%120===0) console.log('frame',i,'/',N); }
  ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await b.close();
})();
