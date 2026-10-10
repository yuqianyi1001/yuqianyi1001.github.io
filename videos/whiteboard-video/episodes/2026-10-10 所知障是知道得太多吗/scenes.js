// 《所知障是知道得太多吗》— 手绘白板讲解视频场景定义（佛教最容易被误解的概念）
// 流程：改这里 → wb stills "所知障" 看 frames/ 排版 → wb build "所知障" 出片
// 经文出处见同目录 README.md「资料来源」，全部可在 CBETA 检索。
// 本期未出贴纸（环境里没有 codex CLI），人物与物件都用 Excalidraw 图形画。
const { Scene, C, CX, build } = require(require('path').join(process.env.WB_ROOT, 'lib/scene-dsl')).use(__dirname);
const scenes = [];
function heading(s, t) { s.text(120, 65, t, { size: 80, color: C.brand }); }
function card(s, x, y, w, h, t, color = C.ink, fill = C.fYellow, size = 48) {
  s.rect(x, y, w, h, { round: true, fill, fillStyle: 'solid' });
  s.text(x + w / 2, y + (h - size * 1.25 * t.split('\n').length) / 2, t, { size, align: 'center', color });
}
// 经名标签：灰框 + 经名
function source(s, x, y, t, size = 34) {
  const w = [...t].length * size + 40;
  s.rect(x, y, w, size + 36, { round: true, stroke: C.gray, strokeStyle: 'dashed' });
  s.text(x + w / 2, y + 16, t, { size, align: 'center', color: C.gray });
}
// 一摞书：左下角 (x,y)，n 本
function books(s, x, y, n = 3, w = 260) {
  const fills = [C.fBlue, C.fRed, C.fGreen, C.fYellow];
  for (let i = 0; i < n; i++) {
    const off = (i % 2) * 18;
    s.rect(x + off, y - (i + 1) * 46, w - 36, 42, { round: true, fill: fills[i % 4], fillStyle: 'solid' });
  }
}
// 一堵墙：砖块
function wall(s, x, y, w, h) {
  s.rect(x, y, w, h, { fill: C.fRed, fillStyle: 'hachure', stroke: C.red, strokeWidth: 3 });
  for (let yy = y + h / 4; yy < y + h - 5; yy += h / 4) s.line([[x, yy], [x + w, yy]], { stroke: C.red, strokeWidth: 2 });
}
// 叉
function cross(s, cx, cy, r = 40) {
  s.line([[cx - r, cy - r], [cx + r, cy + r]], { stroke: C.red, strokeWidth: 6 });
  s.line([[cx + r, cy - r], [cx - r, cy + r]], { stroke: C.red, strokeWidth: 6 });
}

{
  const s = new Scene('01-hook', `常听人说：书读多了，有所知障。知道得越多，障碍越大，学佛还是少读点书好。|这是对所知障最常见的误解。所知障是唯识学的名词，今天用《瑜伽师地论》和《成唯识论》的原文，看它到底指什么。`);
  s.nextBeat();
  s.text(CX, 80, '所知障？', { size: 150, align: 'center', color: C.brand });
  s.person(330, 400, 1.6);
  books(s, 230, 900, 4);
  s.ellipse(620, 300, 640, 200, { stroke: C.orange, fill: C.fYellow, fillStyle: 'solid' });
  s.text(940, 375, '书读多了，有所知障', { size: 44, align: 'center', color: C.orange });
  card(s, 680, 580, 520, 120, '知道越多', C.blue, C.fBlue, 52);
  s.arrow([[1215, 640], [1325, 640]], { stroke: C.gray, strokeWidth: 4 });
  card(s, 1340, 580, 440, 120, '障碍越大', C.red, C.fRed, 52);
  s.nextBeat();
  cross(s, 1230, 640, 70);
  s.text(1230, 740, '最常见的误解', { size: 44, align: 'center', color: C.red });
  source(s, 700, 830, '瑜伽师地论');
  source(s, 1150, 830, '成唯识论');
  scenes.push(s);
}
{
  const s = new Scene('02-word', `先拆字。所知，不是“我知道的那些东西”，是被认识的对象，也就是一切该知道的法。|《瑜伽师地论》卷三十六给了定义：于所知能碍智故，名所知障。对着该认识的境界，障住了智慧，所以叫所知障。|所以它是障住所知的障，不是所知变成了障。`);
  s.nextBeat();
  heading(s, '先拆字');
  source(s, 1100, 80, '瑜伽师地论 卷36');
  s.ellipse(1300, 230, 460, 260, { fill: C.fGreen, fillStyle: 'solid', stroke: C.brand });
  s.text(1530, 290, '所知', { size: 64, align: 'center', color: C.brand });
  s.text(1530, 380, '被认识的一切法', { size: 36, align: 'center', color: C.gray });
  s.nextBeat();
  s.ellipse(160, 250, 300, 220, { fill: C.fBlue, fillStyle: 'solid', stroke: C.blue });
  s.text(310, 320, '智', { size: 72, align: 'center', color: C.blue });
  s.arrow([[470, 360], [760, 360]], { stroke: C.blue, strokeWidth: 4 });
  wall(s, 790, 210, 130, 300);
  s.text(855, 525, '障', { size: 60, align: 'center', color: C.red });
  s.arrow([[940, 360], [1280, 360]], { stroke: C.gray, strokeWidth: 3, strokeStyle: 'dashed' });
  s.rect(220, 640, 1480, 110, { round: true, fill: C.fYellow, fillStyle: 'solid' });
  s.text(CX, 665, '“于所知能碍智故，名所知障”', { size: 48, align: 'center' });
  s.nextBeat();
  s.text(320, 815, '✗ 所知变成了障', { size: 48, color: C.red });
  s.text(1060, 815, '✓ 障住所知的障', { size: 48, color: C.brand });
  scenes.push(s);
}
{
  const s = new Scene('03-two', `所知障是跟烦恼障配对讲的。《成唯识论》卷九说，烦恼障，是执着有一个实在的我，扰乱身心，障碍涅槃。|所知障，是执着有实在的法，跟着生起见、疑、无明、爱、恚、慢这些心所，遮住所知境界不颠倒的真相，障碍菩提。|一个执我，一个执法；一个障涅槃，一个障菩提。`);
  s.nextBeat();
  heading(s, '两种障');
  source(s, 1150, 80, '成唯识论 卷9');
  const colW = 760, top = 220, xs = [CX - colW / 2 - 40, CX + colW / 2 + 40];
  s.rect(xs[0] - colW / 2, top, colW, 700, { round: true, fill: C.fRed, fillStyle: 'hachure', roughness: 1.2 });
  s.text(xs[0], top + 25, '烦恼障', { size: 60, align: 'center', color: C.red });
  card(s, xs[0] - 300, top + 140, 600, 110, '执实我', C.red, '#fff5f5', 52);
  s.text(xs[0], top + 300, '扰恼有情身心', { size: 42, align: 'center' });
  s.arrow([[xs[0], top + 380], [xs[0], top + 470]], { stroke: C.gray, strokeWidth: 3 });
  card(s, xs[0] - 230, top + 490, 460, 110, '障涅槃', C.ink, C.fYellow, 52);
  s.nextBeat();
  s.rect(xs[1] - colW / 2, top, colW, 700, { round: true, fill: C.fBlue, fillStyle: 'hachure', roughness: 1.2 });
  s.text(xs[1], top + 25, '所知障', { size: 60, align: 'center', color: C.blue });
  card(s, xs[1] - 300, top + 140, 600, 110, '执实法', C.blue, '#f1f7ff', 52);
  s.text(xs[1], top + 280, '见 疑 无明 爱 恚 慢', { size: 40, align: 'center', color: C.gray });
  s.text(xs[1], top + 340, '覆所知境无颠倒性', { size: 42, align: 'center' });
  s.arrow([[xs[1], top + 410], [xs[1], top + 470]], { stroke: C.gray, strokeWidth: 3 });
  card(s, xs[1] - 230, top + 490, 460, 110, '障菩提', C.ink, C.fYellow, 52);
  s.nextBeat();
  s.text(xs[0], top + 630, '执我', { size: 48, align: 'center', color: C.red });
  s.text(xs[1], top + 630, '执法', { size: 48, align: 'center', color: C.blue });
  scenes.push(s);
}
{
  const s = new Scene('04-result', `两种障断了，得到的果不一样。《成唯识论》卷一说：断烦恼障，证真解脱；断所知障，得大菩提。|《瑜伽师地论》卷三十五说，声闻、独觉的种性，只能证烦恼障净，不能证所知障净；菩萨种性，两种都能证。|所以阿罗汉已经解脱生死，所知障还在，还没有成佛。`);
  s.nextBeat();
  heading(s, '断了得什么');
  source(s, 1150, 80, '成唯识论 卷1');
  card(s, 160, 240, 560, 120, '断烦恼障', C.red, C.fRed, 52);
  s.arrow([[740, 300], [880, 300]], { stroke: C.gray, strokeWidth: 4 });
  card(s, 900, 240, 460, 120, '证真解脱', C.ink, C.fYellow, 52);
  card(s, 160, 410, 560, 120, '断所知障', C.blue, C.fBlue, 52);
  s.arrow([[740, 470], [880, 470]], { stroke: C.gray, strokeWidth: 4 });
  card(s, 900, 410, 460, 120, '得大菩提', C.brand, C.fGreen, 52);
  s.nextBeat();
  source(s, 160, 590, '瑜伽师地论 卷35');
  s.text(160, 690, '声闻、独觉种性：只证烦恼障净', { size: 44 });
  s.text(160, 770, '菩萨种性：两种障净都能证', { size: 44, color: C.brand });
  s.nextBeat();
  s.rect(1440, 240, 340, 290, { round: true, stroke: C.orange, strokeStyle: 'dashed' });
  s.text(1610, 270, '阿罗汉', { size: 52, align: 'center', color: C.orange });
  s.text(1610, 360, '已解脱生死', { size: 36, align: 'center' });
  s.text(1610, 420, '所知障还在', { size: 36, align: 'center', color: C.red });
  s.text(1610, 560, '还没有成佛', { size: 48, align: 'center', color: C.red });
  scenes.push(s);
}
{
  const s = new Scene('05-attach', `那执着实法，是什么样子？就是把认识到的东西，当成有它自己固定不变的实体：把名字当成事物本身，把一个概念、一个道理，当成实实在在的东西。|《成唯识论》还说，这两种障，有分别起的，也有任运起的。分别起，是听了错误的教导、自己推想出来的；任运起，是生来就带着的。一个字不认识的人，照样有所知障。|读书生出傲慢、死守成见，确实是毛病，但毛病在慢和执，不在读书。问题出在执，不在知。`);
  s.nextBeat();
  heading(s, '执着实法');
  card(s, 160, 230, 440, 120, '名字', C.ink, C.fGray, 52);
  s.text(700, 245, '≠', { size: 90, color: C.red });
  card(s, 820, 230, 440, 120, '事物本身', C.ink, C.fGray, 52);
  card(s, 160, 400, 440, 120, '概念 · 道理', C.blue, C.fBlue, 48);
  s.arrow([[620, 460], [800, 460]], { stroke: C.gray, strokeWidth: 3 });
  card(s, 820, 400, 440, 120, '当成实体', C.red, C.fRed, 48);
  s.nextBeat();
  source(s, 1340, 230, '成唯识论 卷9');
  s.text(1340, 330, '分别起', { size: 48, color: C.orange });
  s.text(1340, 395, '邪教、邪分别引生', { size: 32, color: C.gray });
  s.text(1340, 460, '任运起', { size: 48, color: C.orange });
  s.text(1340, 525, '生来就带着', { size: 32, color: C.gray });
  s.person(1480, 590, 1.0);
  s.text(1560, 820, '不识字也有', { size: 36, align: 'center', color: C.gray });
  s.nextBeat();
  books(s, 200, 860, 3, 240);
  s.text(500, 640, '傲慢、成见：', { size: 40, color: C.gray });
  s.text(500, 700, '毛病在慢和执，不在读书', { size: 40, color: C.gray });
  s.text(500, 790, '问题出在执，不在知', { size: 64, color: C.brand });
  scenes.push(s);
}
{
  const s = new Scene('06-cure', `那所知障怎么断？《成唯识论》卷一说：若证二空，彼障随断。证得法空，所知障才断，不是靠少知道一点。|《瑜伽师地论》卷三十八反而要求菩萨学五明：内明、因明、声明、医方明、工业明。论里说，不在这些明处次第修学，得不到无障一切智智。`);
  s.nextBeat();
  heading(s, '怎么断');
  source(s, 1150, 80, '成唯识论 卷1');
  card(s, 160, 230, 500, 120, '证法空', C.brand, C.fGreen, 56);
  s.arrow([[680, 290], [840, 290]], { stroke: C.brand, strokeWidth: 4 });
  card(s, 860, 230, 500, 120, '所知障断', C.blue, C.fBlue, 56);
  s.text(1420, 260, '✗ 少读书', { size: 48, color: C.red });
  s.nextBeat();
  source(s, 160, 420, '瑜伽师地论 卷38');
  ['内明', '因明', '声明', '医方明', '工业明'].forEach((t, i) => {
    card(s, 160 + i * 325, 520, 290, 120, t, C.ink, C.fYellow, 46);
  });
  s.rect(160, 700, 1590, 110, { round: true, fill: C.fGreen, fillStyle: 'solid' });
  s.text(955, 725, '“非不于此一切明处次第修学，能得无障一切智智”', { size: 40, align: 'center', color: C.brand });
  scenes.push(s);
}
{
  const s = new Scene('07-close', `所以，所知障不是知道得太多，是把所知的东西执为实有。对治它，不是少学，是在学的路上破除法执，证得法空。|你以前听过的所知障，是哪种说法？评论区聊聊。`);
  s.nextBeat();
  heading(s, '所知障，不是知道太多');
  s.text(200, 260, '✗ 知道得太多', { size: 60, color: C.red });
  s.text(200, 380, '✓ 把所知执为实有', { size: 60, color: C.brand });
  s.text(1100, 260, '✗ 少学', { size: 60, color: C.red });
  s.text(1100, 380, '✓ 破法执，证法空', { size: 60, color: C.brand });
  s.squiggle(200, 1700, 500);
  s.nextBeat();
  card(s, 200, 640, 1100, 160, '你听过的所知障，是哪种说法？', C.ink, C.fYellow, 48);
  s.ellipse(1400, 660, 300, 120, { stroke: C.orange, fill: C.fYellow, fillStyle: 'solid' });
  s.text(1550, 692, '评论区聊聊', { size: 40, align: 'center', color: C.orange });
  scenes.push(s);
}
const cover = (s, ratio) => {
  s.coverLayout({
    ratio,
    title: '所知障，\n是知道太多？',
    sub: '佛教最容易被误解的概念',
    tag: '白板讲佛法',
  });
  // 没有贴纸：画一摞书 + 一堵墙
  if (ratio === '3:4') {
    books(s, 260, 1180, 4, 300);
    wall(s, 640, 900, 140, 280);
  } else {
    books(s, 900, 960, 4, 260);
    wall(s, 1220, 700, 120, 260);
  }
};
build(__dirname, scenes, { cover });
