// npm install playwright separately; set PLAYWRIGHT_MODULE if outside this repo.
// Run a local server on 8765. No production submissions are permitted.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    let failImages = true;
    await page.route('**/*', route => {
      const req = route.request();
      if (!req.url().startsWith('http://127.0.0.1:8765/') || req.method() !== 'GET') return route.abort();
      if (req.url().endsWith('/web/config.js')) return route.fulfill({contentType:'application/javascript',body:'window.STICKER_CONFIG={ENDPOINT_URL:"",N_BONUS:0};'});
      if (failImages && req.url().includes('/stimuli/')) return route.abort();
      return route.continue();
    });
    await page.goto('http://127.0.0.1:8765/web/');
    await page.locator('#btn-start').click();
    for (const [name, value] of Object.entries({fam_turkish:'none',fam_chinese:'native',fam_american:'some',meme_fluency:'3',sticker_use_frequency:'daily',bilingual:'no'})) {
      await page.locator(`label:has(input[name="${name}"][value="${value}"])`).click();
    }
    await page.locator('#age').fill('25');
    await page.locator('#native_language').fill('Chinese');
    await page.locator('#survey-form button').click();
    await page.locator('#btn-begin').click();
    // Randomized text_only trials remain answerable, with the intended hidden box.
    for (let i=0; i<13 && await page.locator('#stimulus .hidden-sticker').count(); i++) {
      assert.equal(await page.locator('#stimulus img').count(),0);
      await page.locator('.choice[data-response="negative"]').click();
      await page.locator('.conf[data-confidence="2"]').click();
    }
    await page.locator('#stimulus-error').waitFor({state:'visible'});
    assert(await page.locator('.choice').first().isDisabled());
    const progress = await page.locator('#progress').innerText();
    failImages = false;
    await page.locator('#btn-stimulus-retry').click();
    await page.waitForFunction(()=>!document.querySelector('.choice').disabled);
    assert.equal(await page.locator('#progress').innerText(),progress);
    assert(await page.locator('#stimulus img').evaluate(i=>i.complete&&i.naturalWidth>0));
    assert(await page.locator('#stimulus-error').isHidden());
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.locator('.choice[data-response="sarcastic"]').click();
    await page.locator('#btn-change').click();
    await page.locator('.choice[data-response="positive"]').click();
    await page.locator('.conf[data-confidence="5"]').click();
    console.log('PASS: real radio-label clicks; failed image blocks answers; retry retains trial; decoded image enables answers; change-answer works; no mobile horizontal overflow.');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1);});
