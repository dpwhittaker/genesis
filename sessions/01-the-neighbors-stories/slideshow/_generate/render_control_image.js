const path=require('path');
function pp(){for(const t of [()=>require('puppeteer'),()=>require(path.resolve('../systematic-theology/node_modules/puppeteer'))]){try{return t()}catch(e){}}throw new Error('no pp')}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const url="http://127.0.0.1:4000/genesis/sessions/01-the-neighbors-stories/slideshow/";
  const b=await pp().launch({headless:'new',args:['--no-sandbox','--disable-setuid-sandbox']});
  const p=await b.newPage(); await p.setViewport({width:1344,height:756,deviceScaleFactor:1});
  await p.goto(url,{waitUntil:'networkidle0'}); await wait(600);
  await p.evaluate(()=>{ for(const s of ['#overlay','.topbar','.controls','#hint']){const e=document.querySelector(s); if(e) e.style.display='none';} });
  await wait(200);
  const stage=await p.$('#stage'); await stage.screenshot({path:'pdf/control.png'});
  await b.close(); console.log('control.png written');
})().catch(e=>{console.error(e.message);process.exit(1)});
