// Participant-style local regression. No production network access or data writes.
// PLAYWRIGHT_MODULE may point to a separately installed Playwright package.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const out = process.env.TEST_OUTPUT_DIR;
const conditions = require('../web/conditions.json');
const report = [];

(async()=>{
 const browser = await chromium.launch({headless:true});
 try {
  for(let rotation=0;rotation<3;rotation++) {
   const width=[1280,390,320][rotation];
   const context=await browser.newContext({viewport:{width,height:900},colorScheme:rotation===1?'dark':'light'});
   const page=await context.newPage();const posts=[];const errors=[];let attempts=0;
   page.on('pageerror',e=>errors.push(e.message));
   await page.addInitScript(rotation=>{
    let first=true, seed=rotation+98231;
    Math.random=()=>{if(first){first=false;return (rotation+.1)/3;} seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return (seed>>>0)/4294967296;};
   },rotation);
   await page.route('**/*',async route=>{
    const req=route.request();
    if(req.url()==='https://test.invalid/submit') {
     const payload=JSON.parse(req.postData()); posts.push(payload);
     if(payload.type==='complete' && ++attempts===1) return route.abort();
     return route.fulfill({contentType:'application/json',body:'{"ok":true}'});
    }
    if(!req.url().startsWith('http://127.0.0.1:8765/')||req.method()!=='GET') return route.abort();
    if(req.url().endsWith('/web/config.js')) return route.fulfill({contentType:'application/javascript',body:'window.STICKER_CONFIG={ENDPOINT_URL:"https://test.invalid/submit",SECRET:"test-only",N_BONUS:3};'});
    return route.continue();
   });
   await page.goto('http://127.0.0.1:8765/web/');
   await page.locator('#btn-start').click();
   await page.locator('#survey-form button').click();
   assert(await page.locator('#survey-error').isVisible());
   for(const [name,value] of Object.entries({fam_turkish:'none',fam_chinese:'native',fam_american:'some',meme_fluency:'4',sticker_use_frequency:'daily',bilingual:'yes'}))
    await page.locator(`label:has(input[name="${name}"][value="${value}"])`).click();
   await page.locator('#native_language').fill('Chinese');
   await page.locator('#age').fill('17');
   await page.locator('#survey-form button').click();
   assert(await page.locator('#screen-survey').isVisible());
   await page.locator('#age').fill('25');
   await page.locator('#other_languages').fill('English');
   await page.locator('#survey-form button').click();
   await page.locator('#btn-begin').click();
   const observations=[];const photographed=new Set();
   for(let i=0;i<37;i++){
    await page.waitForFunction(()=>!document.querySelector('.choice').disabled);
    assert.equal((await page.locator('#progress').innerText()).trim(),`${i+1} / 37`);
    const img=page.locator('#stimulus img');
    const hidden=await page.locator('#stimulus .hidden-sticker').count()>0;
    const mode=hidden?'text_only':await page.locator('#stimulus .chat').count()?'chat':'alone';
    let id=null;
    if(hidden){assert.equal(await img.count(),0);assert((await page.locator('#stimulus .bubble.them').innerText()).trim().length>5);}
    else {
     assert(await img.evaluate(i=>i.complete&&i.naturalWidth>0&&i.naturalHeight>0));
     id=path.basename(await img.getAttribute('src')).replace(/\.[^.]+$/,'');
    }
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`horizontal overflow at ${width}px trial ${i+1}`);
    if(out&&!photographed.has(mode)){
     await page.screenshot({path:path.join(out,`participant-${rotation}-${mode}.png`),fullPage:true});photographed.add(mode);
    }
    const answer=id==='ATTN_01'?(rotation===1?'negative':'positive'):['positive','negative','sarcastic'][i%3];
    await page.locator(`.choice[data-response="${answer}"]`).click();
    if(i===0){await page.locator('#btn-change').click();await page.locator(`.choice[data-response="${answer}"]`).click();}
    const confidence=i%5+1;
    await page.locator(`.conf[data-confidence="${confidence}"]`).click();
    observations.push({id,mode,answer,confidence});
   }
   await page.locator('#bonus-text').fill('Test only: what a wonderful surprise!');
   await page.locator('#btn-bonus-next').click();
   await page.locator('#btn-bonus-skip').click();
   await page.locator('#btn-bonus-skip').click();
   await page.locator('#btn-retry').waitFor({state:'visible'});
   assert((await page.locator('#save-status').innerText()).includes('Could not reach'));
   assert.equal(await page.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('sticker_pending_')).length),1);
   await page.locator('#btn-retry').click();
   await page.locator('#giveaway-form').waitFor({state:'visible'});
   assert.equal(await page.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('sticker_pending_')).length),0);
   const complete=posts.filter(p=>p.type==='complete');assert.equal(complete.length,2);assert.deepEqual(complete[0],complete[1]);
   const payload=complete[1];assert.equal(payload.participant.rotation,rotation);assert.equal(payload.trials.length,37);
   assert.equal(new Set(payload.trials.map(t=>t.sticker_id)).size,37);
   assert.equal(payload.participant.passed_attention_check,rotation===1?0:1);
   assert.equal(payload.trials.filter(t=>t.is_attention_check).length,1);
   assert.equal(payload.trials.filter(t=>t.context==='text_only').length,12);
   assert.equal(payload.freetext.length,1);assert.equal(payload.trials[0].changed_answer,1);
   for(let i=0;i<37;i++){
    const t=payload.trials[i], seen=observations[i], s=conditions.stickers.find(s=>s.sticker_id===t.sticker_id);
    assert(s);assert.equal(t.participant_id,payload.participant.participant_id);assert.equal(t.trial_order,i+1);
    assert.equal(t.context,seen.mode);assert.equal(t.response,seen.answer);assert.equal(t.confidence,seen.confidence);
    assert(Number.isFinite(t.rt_ms)&&t.rt_ms>=0);
    if(seen.id)assert.equal(t.sticker_id,seen.id);
    if(s.culture!=='ATTN')assert.equal(conditions.rotations[rotation][t.context],s.set);
   }
   await page.locator('#gw-name').fill('Synthetic Test');await page.locator('#gw-contact').fill('test@example.invalid');
   await page.locator('#giveaway-form button').click();
   await page.locator('label:has(input[name="aipi_cohort"][value="no"])').click();
   await page.locator('#secret-form button[type=submit]').click();
   await page.waitForFunction(()=>document.querySelector('#secret-status').textContent.includes('thanks'));
   assert(posts.some(p=>p.type==='giveaway'));assert(posts.some(p=>p.type==='extra'));assert.deepEqual(errors,[]);
   if(out)fs.writeFileSync(path.join(out,`participant-${rotation}.json`),JSON.stringify(payload,null,2));
   report.push({rotation,width,trials:37,visible:25,hidden:12,attentionPassed:payload.participant.passed_attention_check,retryIdentical:true,allAnswersAndConfidenceVerified:true});
   await context.close();
  }
  if(out)fs.writeFileSync(path.join(out,'participant-audit.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
