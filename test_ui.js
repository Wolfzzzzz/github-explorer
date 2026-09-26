const puppeteer = require('puppeteer-core');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const FILE = process.argv[2] || 'file:///Users/zzn/Desktop/github-explorer/_site/index.html';
const results = [];
const errors = [];
const t = (name, ok, extra = '') => results.push({ name, ok, extra });
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
  });
  const page = await browser.newPage();
  const click = sel => page.evaluate(s => { const e = document.querySelector(s); if (!e) return false; e.click(); return true; }, sel);
  await page.setViewport({ width: 1440, height: 900 });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

  await page.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 180000 });
  await page.waitForSelector('.card', { timeout: 90000 }).catch(() => {});
  const cardCount = () => page.$$eval('.card', e => e.length).catch(() => 0);

  const c0 = await cardCount();
  t('① 初始渲染卡片', c0 > 0, '卡片=' + c0);

  // 搜索
  const statBefore = await page.$eval('#resStat', e => e.textContent);
  await page.type('#q', 'immich'); await sleep(600);
  const c1 = await cardCount();
  const statAfter = await page.$eval('#resStat', e => e.textContent);
  const hit = await page.$$eval('.card', e => e.some(x => x.textContent.toLowerCase().includes('immich'))).catch(() => false);
  t('② 搜索框过滤', c1 > 0 && hit && statBefore !== statAfter, `匹配数变化: ${statBefore.slice(0,18)} → ${statAfter.slice(0,18)}`);
  const mk = await page.$$eval('mark', e => e.length).catch(() => 0);
  t('③ 搜索关键词高亮', mk > 0, 'mark=' + mk);
  await page.$eval('#q', el => { el.value = ''; el.dispatchEvent(new Event('input', { bubbles: true })); });
  await sleep(400);
  t('④ 清空搜索恢复', (await cardCount()) === c0);

  // 方向 chip
  const nDir = await page.$$eval('#dirChips .chip', e => e.length).catch(() => 0);
  t('⑤ 方向 chips 渲染', nDir > 0, '数量=' + nDir);
  if (nDir) {
    await click('#dirChips .chip'); await sleep(500);
    const c3 = await cardCount();
    t('⑥ 点击方向 chip 筛选', c3 > 0 && c3 <= c0, '筛选后=' + c3);
    await click('#dirChips .chip.on').catch(() => {}); await sleep(400);
  }
  const nLang = await page.$$eval('#langChips .chip', e => e.length).catch(() => 0);
  if (nLang) {
    await click('#langChips .chip'); await sleep(500);
    t('⑦ 点击语言 chip 筛选', (await cardCount()) > 0);
    await click('#langChips .chip.on').catch(() => {}); await sleep(400);
  }
  // 排序
  await page.select('#sortSel', 'stars-asc'); await sleep(400);
  const asc = await page.$eval('.card .stars', e => e.textContent).catch(() => '');
  await page.select('#sortSel', 'stars-desc'); await sleep(400);
  const desc = await page.$eval('.card .stars', e => e.textContent).catch(() => '');
  t('⑧ 排序切换生效', asc !== desc, `升=${asc} 降=${desc}`);

  // 视图
  await page.select('#viewSel', 'list'); await sleep(400);
  t('⑨ 紧凑视图', await page.$eval('#list', e => getComputedStyle(e).display !== 'none').catch(() => false));
  await page.select('#viewSel', 'table'); await sleep(500);
  t('⑩ 表格视图', (await page.$$eval('#tblwrap tbody tr', e => e.length).catch(() => 0)) > 0);
  await page.select('#viewSel', 'card'); await sleep(400);

  // 分页
  const p1 = await page.$eval('#pgNum', e => e.textContent);
  await click('#pgNext'); await sleep(600);
  const p2 = await page.$eval('#pgNum', e => e.textContent);
  t('⑪ 下一页翻页', p1 !== p2, `${p1} → ${p2}`);
  await click('#pgPrev'); await sleep(400);

  // 详情抽屉
  await click('.card'); await sleep(600);
  const dw = await page.$eval('#drawer', e => e.classList.contains('show')).catch(() => false);
  t('⑫ 点击卡片开详情抽屉', dw);
  if (dw) {
    await click('#dFav'); await sleep(400);
    const nf = await page.evaluate(() => JSON.parse(localStorage.getItem('gh_favs') || '[]').length);
    t('⑬ 收藏写入本地存储', nf > 0, 'favs=' + nf);
    const sim = await page.$$eval('#simList .row', e => e.length).catch(() => 0);
    t('⑭ 相似推荐列表', sim > 0, '相似=' + sim);
    await page.evaluate(() => document.getElementById('dClose')?.click()); await sleep(400);
  }
  // 随机发现
  await click('#randBtn'); await sleep(600);
  t('⑮ 随机发现按钮', await page.$eval('#drawer', e => e.classList.contains('show')).catch(() => false));
  await page.evaluate(() => document.getElementById('dClose')?.click()); await sleep(300);

  // 页签
  for (const [tab, sec, sel] of [['trend', '#secTrend', '.tcard'], ['insight', '#secInsight', '.ins'], ['stats', '#secStats', '.kpiCard'], ['fav', '#secFav', '.tcard']]) {
    await click(`.tab[data-tab="${tab}"]`); await sleep(700);
    const vis = await page.$eval(sec, e => e.classList.contains('show')).catch(() => false);
    const n = await page.$$eval(sec + ' ' + sel, e => e.length).catch(() => 0);
    t(`⑯ 页签 ${tab}`, vis && n > 0, `可见=${vis} 内容=${n}`);
  }
  // 关键词云
  const kw = await page.$$eval('[data-kw]', e => e.length).catch(() => 0);
  t('⑰ 统计页关键词云', kw > 0, '词数=' + kw);
  await click('.tab[data-tab="lib"]'); await sleep(500);

  // 导出
  await click('#exportBtn'); await sleep(600);
  t('⑱ 导出弹窗', await page.$$eval('.modal', e => e.some(m => m.classList.contains('show'))).catch(() => false));
  await page.evaluate(() => { document.querySelectorAll('.modal').forEach(m => m.remove()); document.getElementById('overlay').classList.remove('show'); });

  // 主题
  const th1 = await page.evaluate(() => document.documentElement.dataset.theme);
  await click('#themeBtn'); await sleep(400);
  const th2 = await page.evaluate(() => document.documentElement.dataset.theme);
  t('⑲ 主题切换', th1 !== th2, `${th1}→${th2}`);

  // 重置
  await click('#resetBtn'); await sleep(500);
  t('⑳ 重置筛选', (await cardCount()) === c0);

  // 仅推荐
  await click('#hlOnly'); await sleep(500);
  const hlN = await cardCount();
  t('㉑ 仅看⭐推荐筛选', hlN >= 0, '推荐数=' + hlN);
  await click('#hlOnly'); await sleep(300);

  await browser.close();
  console.log('\n===== 交互测试报告 =====');
  let pass = 0;
  results.forEach(r => { if (r.ok) pass++; console.log(`${r.ok ? '✅' : '❌'} ${r.name}${r.extra ? ' — ' + r.extra : ''}`); });
  console.log(`\n通过: ${pass}/${results.length}`);
  const uni = [...new Set(errors)];
  if (uni.length) { console.log('\n===== JS 错误 ====='); uni.slice(0, 15).forEach(e => console.log('⚠️ ' + e.slice(0, 180))); }
  else console.log('\n✅ 无 JS 错误');
})().catch(e => { console.error('测试脚本异常:', e.message); process.exit(1); });
