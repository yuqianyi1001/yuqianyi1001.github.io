// 《为什么佛教说人生是苦》— 手绘白板讲解视频场景定义
// 流程：改这里 → wb stills "人生是苦" 看 frames/ 排版 → wb build "人生是苦" 出片
// 经文出处见同目录 README.md「资料来源」，全部可在 CBETA 检索。
// 本期未出贴纸（环境里没有 codex CLI），人物与物件都用 Excalidraw 图形画。
const { Scene, C, CX, build } = require(require('path').join(__dirname, '../../lib/scene-dsl')).use(__dirname);
const scenes = [];
function heading(s, t) { s.text(120, 65, t, { size: 80, color: C.brand }); }
function card(s, x, y, w, h, t, color = C.ink, fill = C.fYellow, size = 48) {
  s.rect(x, y, w, h, { round: true, fill, fillStyle: 'solid' });
  s.text(x + w / 2, y + (h - size * 1.25) / 2, t, { size, align: 'center', color });
}
// 经名标签：灰框 + 经名
function source(s, x, y, t, size = 34) {
  const w = [...t].length * size + 40;
  s.rect(x, y, w, size + 36, { round: true, stroke: C.gray, strokeStyle: 'dashed' });
  s.text(x + w / 2, y + 16, t, { size, align: 'center', color: C.gray });
}
// 一支箭：从 (x1,y1) 射向 (x2,y2)，带尾羽
function dart(s, x1, y1, x2, y2, color = C.red) {
  s.arrow([[x1, y1], [x2, y2]], { stroke: color, strokeWidth: 5 });
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L;
  for (const k of [0, 22]) {
    const bx = x1 + ux * k, by = y1 + uy * k;
    s.line([[bx, by], [bx - ux * 24 - uy * 18, by - uy * 24 + ux * 18]], { stroke: color, strokeWidth: 3 });
  }
}

{
  const s = new Scene('01-hook', `佛教说，人生是苦。不少人一听就皱眉：这也太悲观了吧？人生明明也有开心的时候。|可佛经里的这个苦字，原词的意思不只是疼、难受，还包括不圆满、靠不住。今天用几部阿含经，一条一条看佛陀和弟子们怎么说。`);
  s.nextBeat();
  s.text(CX, 90, '人生是苦？', { size: 150, align: 'center', color: C.brand });
  s.person(360, 420, 1.6);
  s.text(430, 780, '太悲观了吧', { size: 44, align: 'center', color: C.gray });
  s.ellipse(1150, 300, 520, 220, { stroke: C.orange, fill: C.fYellow, fillStyle: 'solid' });
  s.text(1410, 385, '明明也有开心的时候', { size: 40, align: 'center', color: C.orange });
  s.nextBeat();
  s.arrow([[1410, 530], [1410, 590]], { stroke: C.gray, strokeWidth: 3 });
  card(s, 780, 600, 960, 150, '苦 = 疼、难受 + 不圆满、靠不住', C.brand, C.fGreen, 48);
  s.text(1260, 800, '巴利语 dukkha', { size: 40, align: 'center', color: C.gray });
  s.text(1260, 870, '今天只看阿含经原文', { size: 36, align: 'center', color: C.gray });
  scenes.push(s);
}
{
  const s = new Scene('02-eight', `先看苦有哪些。《中阿含经》的《分别圣谛经》里，舍梨子给比丘们解说苦圣谛，一共列了八种。头四种是生苦、老苦、病苦、死苦，落在身体上，谁都躲不开。|接着三种落在人和事上：怨憎会苦，是和讨厌的人凑在一起；爱别离苦，是和爱的人分开；所求不得苦，是想要的得不到。|最后一种叫五盛阴苦。色、受、想、行、识这五阴，被当成“我”抓住不放，前面七种苦，都压在这上面。`);
  s.nextBeat();
  heading(s, '八种苦');
  source(s, 1120, 80, '中阿含·分别圣谛经');
  ['生', '老', '病', '死'].forEach((t, i) => {
    const x = 160 + i * 230;
    s.rect(x, 240, 190, 150, { round: true, fill: C.fBlue, fillStyle: 'solid' });
    s.text(x + 95, 270, t + '苦', { size: 56, align: 'center', color: C.blue });
  });
  s.text(560, 420, '身体上，谁都躲不开', { size: 36, align: 'center', color: C.gray });
  s.nextBeat();
  [['怨憎会苦', '和讨厌的人凑一起'], ['爱别离苦', '和爱的人分开'], ['所求不得苦', '想要的得不到']].forEach(([t, n], i) => {
    const y = 240 + i * 150;
    s.rect(1120, y, 620, 120, { round: true, fill: C.fRed, fillStyle: 'solid' });
    s.text(1150, y + 12, t, { size: 48, color: C.red });
    s.text(1150, y + 72, n, { size: 30, color: C.gray });
  });
  s.nextBeat();
  card(s, 360, 700, 1200, 150, '五盛阴苦：五阴被当成“我”抓住', C.brand, C.fGreen, 52);
  s.arrow([[560, 480], [700, 690]], { stroke: C.gray, strokeWidth: 3 });
  s.arrow([[1430, 665], [1330, 695]], { stroke: C.gray, strokeWidth: 3 });
  s.text(CX, 875, '前七种苦都压在这上面', { size: 36, align: 'center', color: C.gray });
  scenes.push(s);
}
{
  const s = new Scene('03-three', `那快乐呢？快乐总不是苦吧？《长阿含经》的《众集经》把苦分成三类：苦苦、变易苦、行苦。|苦苦，就是疼和难受本身。变易苦，是快乐会变。《中阿含经》里，法乐比丘尼回答毗舍佉的提问，说乐受是生乐、住乐，变易苦：快乐生起时是乐，停留时是乐，一变就成了苦。|行苦，是一切因缘造作的东西，都在迁流不停。连不苦不乐的平常日子，也停不住。`);
  s.nextBeat();
  heading(s, '三种苦');
  source(s, 1120, 80, '长阿含·众集经');
  const colW = 540, gap = 60, top = 230;
  const xs = [CX - colW - gap, CX, CX + colW + gap];
  s.rect(xs[0] - colW / 2, top, colW, 700, { round: true, fill: C.fRed, fillStyle: 'hachure', roughness: 1.2 });
  s.text(xs[0], top + 20, '① 苦苦', { size: 56, align: 'center', color: C.red });
  s.rect(xs[1] - colW / 2, top, colW, 700, { round: true, fill: C.fYellow, fillStyle: 'hachure', roughness: 1.2 });
  s.text(xs[1], top + 20, '② 变易苦', { size: 56, align: 'center', color: C.orange });
  s.rect(xs[2] - colW / 2, top, colW, 700, { round: true, fill: C.fBlue, fillStyle: 'hachure', roughness: 1.2 });
  s.text(xs[2], top + 20, '③ 行苦', { size: 56, align: 'center', color: C.blue });
  s.nextBeat();
  s.text(xs[0], top + 200, '疼、难受', { size: 48, align: 'center' });
  s.text(xs[0], top + 280, '本身就是苦', { size: 40, align: 'center', color: C.gray });
  // 苦苦：一道锯齿
  s.line([[xs[0] - 200, top + 480], [xs[0] - 120, top + 400], [xs[0] - 40, top + 520], [xs[0] + 40, top + 400], [xs[0] + 120, top + 520], [xs[0] + 200, top + 440]], { stroke: C.red, strokeWidth: 5 });
  s.text(xs[0], top + 610, '这一层谁都认', { size: 48, align: 'center' });
  // 变易苦：一条先升后落的曲线
  s.line([[xs[1] - 200, top + 330], [xs[1] - 80, top + 170], [xs[1] + 40, top + 160], [xs[1] + 200, top + 340]], { round: true, stroke: C.orange, strokeWidth: 5 });
  s.text(xs[1] - 130, top + 360, '生乐 住乐', { size: 36, align: 'center', color: C.orange });
  s.text(xs[1] + 150, top + 360, '变易苦', { size: 36, align: 'center', color: C.red });
  s.text(xs[1], top + 470, '法乐比丘尼', { size: 36, align: 'center', color: C.gray });
  s.text(xs[1], top + 520, '答毗舍佉', { size: 36, align: 'center', color: C.gray });
  s.text(xs[1], top + 610, '快乐会变', { size: 48, align: 'center' });
  s.nextBeat();
  s.line([[xs[2] - 200, top + 250], [xs[2] - 100, top + 210], [xs[2], top + 250], [xs[2] + 100, top + 210], [xs[2] + 200, top + 250]], { round: true, stroke: C.blue, strokeWidth: 4 });
  s.arrow([[xs[2] - 200, top + 320], [xs[2] + 200, top + 320]], { stroke: C.blue, strokeWidth: 3 });
  s.text(xs[2], top + 400, '因缘造作', { size: 48, align: 'center' });
  s.text(xs[2], top + 470, '迁流不停', { size: 48, align: 'center' });
  s.text(xs[2], top + 580, '平常日子', { size: 36, align: 'center', color: C.gray });
  s.text(xs[2], top + 630, '也停不住', { size: 36, align: 'center', color: C.gray });
  scenes.push(s);
}
{
  const s = new Scene('04-impermanence', `为什么快乐也算苦？《杂阿含经》第九经，佛陀对比丘们说：色无常，无常即苦，苦即非我。受、想、行、识，也是这样。|第四七三经里，有位比丘独自禅思，想不通：世尊说有乐受、苦受、不苦不乐受，又说所有的受都是苦，这是什么意思？佛陀回答：因为一切行无常，一切行都是变易法，所以说，所有的受都是苦。|所以这个苦，不是说每一刻都在疼，是说没有一样东西抓得住、靠得住。`);
  s.nextBeat();
  heading(s, '为什么快乐也算苦');
  source(s, 1150, 80, '杂阿含经 第9经');
  card(s, 160, 250, 380, 130, '色无常', C.blue, C.fBlue, 56);
  s.arrow([[550, 315], [640, 315]], { stroke: C.gray, strokeWidth: 3 });
  card(s, 650, 250, 380, 130, '无常即苦', C.red, C.fRed, 56);
  s.arrow([[1040, 315], [1130, 315]], { stroke: C.gray, strokeWidth: 3 });
  card(s, 1140, 250, 380, 130, '苦即非我', C.brand, C.fGreen, 56);
  s.text(1560, 290, '受想行识\n亦如是', { size: 34, color: C.gray });
  s.nextBeat();
  source(s, 160, 450, '杂阿含经 第473经');
  s.person(260, 560, 1.1);
  s.text(290, 800, '比丘', { size: 36, align: 'center', color: C.gray });
  s.text(460, 560, '三种受，为何都是苦？', { size: 44, color: C.orange });
  s.rect(450, 660, 1260, 140, { round: true, fill: C.fYellow, fillStyle: 'solid' });
  s.text(1080, 675, '“以一切行无常故，一切诸行变易法故，', { size: 40, align: 'center' });
  s.text(1080, 735, '说诸所有受悉皆是苦。”', { size: 40, align: 'center' });
  s.nextBeat();
  s.text(1080, 850, '不是每刻都在疼，是抓不住、靠不住', { size: 44, align: 'center', color: C.brand });
  scenes.push(s);
}
{
  const s = new Scene('05-arrow', `知道了苦，是不是只能认命？《杂阿含经》第四七零经里，佛陀打了个比方。没听过佛法的凡夫，身体受了苦，心里又跟着忧愁、埋怨、哭喊，像一个人身上中了两支毒箭。|第一支是身受：病痛、衰老，躲不开。第二支是心受，是自己又补射的一箭。|多闻的圣弟子，身体一样会疼，但不起忧悲，不哭喊。经里说，他只中一支箭，只有身受，不生心受。`);
  s.nextBeat();
  heading(s, '两支毒箭');
  source(s, 1150, 80, '杂阿含经 第470经');
  s.line([[CX, 200], [CX, 940]], { strokeStyle: 'dashed', stroke: C.gray });
  s.text(480, 210, '凡夫', { size: 56, align: 'center', color: C.red });
  s.person(430, 360, 2.0);
  s.nextBeat();
  dart(s, 180, 380, 430, 500);
  s.text(180, 300, '① 身受', { size: 40, align: 'center', color: C.red });
  dart(s, 780, 420, 570, 540, C.purple);
  s.text(790, 340, '② 心受', { size: 40, align: 'center', color: C.purple });
  s.text(480, 800, '忧愁 · 埋怨 · 哭喊', { size: 40, align: 'center', color: C.gray });
  s.nextBeat();
  s.text(1440, 210, '多闻圣弟子', { size: 56, align: 'center', color: C.brand });
  s.person(1390, 360, 2.0);
  dart(s, 1140, 380, 1390, 500);
  s.text(1140, 300, '只有身受', { size: 40, align: 'center', color: C.red });
  s.text(1440, 800, '不起忧悲，不生心受', { size: 40, align: 'center', color: C.brand });
  scenes.push(s);
}
{
  const s = new Scene('06-doctor', `所以佛陀讲苦，是在看病。《杂阿含经》第三八九经，佛陀在鹿野苑说，好医生要懂四件事：知道是什么病，知道病从哪来，知道怎么对治，治好以后不再复发。|佛陀接着说，如来是大医王，也成就四德，就是如实知道苦、苦的集起、苦的息灭、灭苦的道路。对照良医四事来看：知病是苦，知病源是集，知对治是道，治好不再复发是灭。说苦是诊断，后面还有治法。`);
  s.nextBeat();
  heading(s, '说苦，是在看病');
  source(s, 1150, 80, '杂阿含经 第389经');
  const rows = [['知病', '苦'], ['知病源', '集'], ['知对治', '道'], ['不再复发', '灭']];
  s.text(420, 210, '良医四事', { size: 48, align: 'center', color: C.gray });
  rows.forEach(([a], i) => card(s, 170, 290 + i * 150, 500, 110, a, C.ink, C.fBlue, 44));
  s.nextBeat();
  s.text(1400, 210, '如来 · 大医王', { size: 48, align: 'center', color: C.brand });
  rows.forEach(([, b], i) => {
    s.arrow([[690, 345 + i * 150], [1090, 345 + i * 150]], { stroke: C.gray, strokeWidth: 3 });
    card(s, 1110, 290 + i * 150, 580, 110, b + '圣谛', C.brand, C.fGreen, 44);
  });
  s.text(CX, 890, '苦是诊断，后面还有治法', { size: 44, align: 'center', color: C.red });
  scenes.push(s);
}
{
  const s = new Scene('07-close', `所以，人生是苦，不是叫人悲观。是叫人看清：快乐会变，身体会老，抓不住的东西，就别死死抓着。看清了病，才找得到治的路。|你最近给自己补射的那第二支箭，是什么？评论区聊聊。`);
  s.nextBeat();
  heading(s, '人生是苦，不是悲观');
  s.checkbox(200, 260, '快乐会变', { size: 52 });
  s.checkbox(200, 380, '身体会老', { size: 52 });
  s.checkbox(200, 500, '抓不住的，别死抓', { size: 52 });
  s.text(1300, 300, '看清病', { size: 72, align: 'center' });
  s.arrow([[1300, 410], [1300, 500]], { stroke: C.brand, strokeWidth: 4 });
  s.text(1300, 520, '才有治的路', { size: 72, align: 'center', color: C.brand });
  s.nextBeat();
  card(s, 200, 700, 1100, 160, '你给自己补射的第二支箭是什么？', C.ink, C.fYellow, 48);
  s.ellipse(1400, 720, 300, 120, { stroke: C.orange, fill: C.fYellow, fillStyle: 'solid' });
  s.text(1550, 752, '评论区聊聊', { size: 40, align: 'center', color: C.orange });
  scenes.push(s);
}
const cover = (s, ratio) => {
  s.coverLayout({
    ratio,
    title: '佛教为什么\n说人生是苦？',
    sub: '阿含经里的八苦、三苦和两支箭',
    tag: '白板讲佛法',
  });
  // 没有贴纸，右下 / 下方画一个中两支箭的人
  if (ratio === '3:4') {
    s.person(480, 820, 2.2);
    dart(s, 230, 860, 490, 990);
    dart(s, 880, 900, 640, 1030, C.purple);
  } else {
    s.person(1150, 650, 1.8);
    dart(s, 900, 730, 1150, 820);
    dart(s, 1390, 720, 1275, 830, C.purple);
  }
};
build(__dirname, scenes, { cover });
