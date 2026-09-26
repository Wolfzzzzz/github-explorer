const puppeteer = require('puppeteer-core');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const FILE = process.argv[2] || 'file:///Users/zzn/Desktop/github-explorer/_site/index.html';

(async () => {
  const b = await puppeteer.launch({ executablePath: CHROME, headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] });
  const page = await b.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));

  const t0 = Date.now();
  await page.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 300000 });
  await page.waitForSelector('.card', { timeout: 180000 });
  const loadMs = Date.now() - t0;

  const info = await page.evaluate(() => ({
    repos: (window.DATA && DATA.repos.length) || 0,
    cards: document.querySelectorAll('.card').length,
    dirs: (window.DATA && DATA.dirNames.length) || 0,
  }));

  // 搜索响应
  const s0 = Date.now();
  await page.type('#q', 'photo');
  await page.waitForFunction(() => document.querySelectorAll('.card').length > 0, { timeout: 60000 });
  await new Promise(r => setTimeout(r, 400));
  const searchMs = Date.now() - s0;
  const hit = await page.$$eval('.card', e => e.length);

  // 翻页响应
  const p0 = Date.now();
  await page.evaluate(() => document.getElementById('pgNext').click());
  await new Promise(r => setTimeout(r, 500));
  const pageMs = Date.now() - p0;

  // 切页签
  const tab0 = Date.now();
  await page.evaluate(() => document.querySelector('.tab[data-tab="stats"]').click());
  await new Promise(r => setTimeout(r, 700));
  const tabMs = Date.now() - tab0;

  await b.close();
  console.log('===== 性能测试 =====');
  console.log(`仓库总数: ${info.repos.toLocaleString()} | 方向: ${info.dirs} | 首页卡片: ${info.cards}`);
  console.log(`⏱ 首屏加载: ${(loadMs/1000).toFixed(2)} 秒`);
  console.log(`⏱ 搜索响应(输入→结果): ${searchMs} 毫秒（命中 ${hit} 张卡）`);
  console.log(`⏱ 翻页响应: ${pageMs} 毫秒`);
  console.log(`⏱ 切页签渲染: ${tabMs} 毫秒`);
  console.log(errs.length ? `\n⚠️ JS 错误: ${errs.slice(0,3).join(' | ')}` : '\n✅ 无 JS 错误');
  const ok = loadMs < 20000 && searchMs < 4000;
  console.log(ok ? '\n✅ 性能达标' : '\n⚠️ 性能需优化');
})().catch(e => { console.error('异常:', e.message); process.exit(1); });
