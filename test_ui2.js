const puppeteer = require('puppeteer-core');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const FILE = process.argv[2] || 'file:///Users/zzn/Desktop/github-explorer/_site/index.html';
const res = [], errs = [];
const t = (n, ok, e = '') => res.push({ n, ok, e });
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({ executablePath: CHROME, headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] });
  const page = await b.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  const click = s => page.evaluate(x => { const e = document.querySelector(x); if (!e) return false; e.click(); return true; }, s);
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });

  await page.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 180000 });
  await page.waitForSelector('.card', { timeout: 90000 }).catch(() => {});
  await sleep(800);

  const firstNames = () => page.$$eval('.card .rname', e => e.slice(0, 5).map(x => x.textContent));
  const a1 = await firstNames();

  // 随机排序
  await page.select('#sortSel', 'random'); await sleep(700);
  const a2 = await firstNames();
  t('① 随机排序改变顺序', JSON.stringify(a1) !== JSON.stringify(a2), '前5项已变化');

  // 换一批按钮出现 + 生效
  const rsVisible = await page.$eval('#reshuffleBtn', e => getComputedStyle(e).display !== 'none');
  t('② 换一批按钮出现', rsVisible);
  await click('#reshuffleBtn'); await sleep(700);
  const a3 = await firstNames();
  t('③ 换一批再次打乱', JSON.stringify(a2) !== JSON.stringify(a3));

  // 本页收藏
  const favsBefore = await page.evaluate(() => JSON.parse(localStorage.getItem('gh_favs') || '[]').length);
  await click('#selPageFav'); await sleep(800);
  const favsAfter = await page.evaluate(() => JSON.parse(localStorage.getItem('gh_favs') || '[]').length);
  t('④ 本页批量收藏', favsAfter > favsBefore, `${favsBefore} → ${favsAfter}`);

  // 本页对比
  await click('#selPageCmp'); await sleep(800);
  const cmpShown = await page.$eval('#cmpbar', e => e.classList.contains('show'));
  const cmpN = await page.$$eval('#cmplist .cmpitem', e => e.length).catch(() => 0);
  t('⑤ 本页批量加入对比篮', cmpShown && cmpN > 0, `对比项=${cmpN}`);

  // 对比弹窗
  await click('#cmpGo'); await sleep(700);
  const modalRows = await page.$$eval('.modal table.tbl tbody tr', e => e.length).catch(() => 0);
  t('⑥ 对比弹窗渲染', modalRows > 0, `行数=${modalRows}`);
  await page.evaluate(() => { document.querySelectorAll('.modal').forEach(m => m.remove()); document.getElementById('overlay').classList.remove('show'); });

  // 方向搜索
  await page.type('#dirSearch', '摄影'); await sleep(700);
  const nDir = await page.$$eval('#dirChips .chip', e => e.length).catch(() => 0);
  t('⑦ 方向搜索过滤', nDir > 0 && nDir < 12, '匹配方向=' + nDir);
  await page.evaluate(() => { const el = document.getElementById('dirSearch'); el.value = ''; el.dispatchEvent(new Event('input', { bubbles: true })); });
  await sleep(500);

  // 详情页导航
  await click('.card'); await sleep(700);
  const pos1 = await page.$eval('#dPos', e => e.textContent).catch(() => '');
  await click('#dNext'); await sleep(700);
  const pos2 = await page.$eval('#dPos', e => e.textContent).catch(() => '');
  t('⑧ 详情页上一个/下一个', pos1 && pos2 && pos1 !== pos2, `${pos1} → ${pos2}`);

  await b.close();
  console.log('\n===== 新功能测试 =====');
  let p = 0; res.forEach(r => { if (r.ok) p++; console.log(`${r.ok ? '✅' : '❌'} ${r.n}${r.e ? ' — ' + r.e : ''}`); });
  console.log(`\n通过: ${p}/${res.length}`);
  const u = [...new Set(errs)];
  console.log(u.length ? '\n⚠️ 错误:\n' + u.slice(0, 8).map(x => '  ' + x.slice(0, 150)).join('\n') : '\n✅ 无 JS 错误');
})().catch(e => { console.error('异常:', e.message); process.exit(1); });
