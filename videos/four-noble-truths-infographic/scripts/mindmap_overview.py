#!/usr/bin/env python3
"""总图的思维导图版：四圣谛 → 苦、集、灭、道；集下挂十二因缘顺转，灭下挂逆转，道下挂三十七道品。
点线表示跨分支的对应：集＝惑＋业，苦果落在生、老死，灭＝无明灭、爱灭，正见生明而无明灭。
写入 cards.html 的 MINDMAP_OVERVIEW 标记之间。viewBox 1000×580。"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import xmind
xmind.PFX = 'ov'
from xmind import defs, box, toggle, dotted, solid, label, inject

STEP, H, FS = 21, 17, 11.5
def w(txt): return max(round(FS * len(txt) + 14), 46)

class Group:
    def __init__(self, name, rect, col, side, leaves, fs=16):
        self.name, self.rect, self.col, self.side, self.fs = name, rect, col, side, fs
        x0, y0, x1, y1 = rect
        self.cy = (y0 + y1) / 2
        n = len(leaves)
        first = self.cy - (n - 1) * STEP / 2
        if side == 'L':
            self.tog, self.br, self.edge = x0 - 8, x0 - 14, x0 - 23
        else:
            self.tog, self.br, self.edge = x1 + 7, x1 + 14, x1 + 23
        self.leaves = {}
        for i, (txt, c) in enumerate(leaves):
            cy = first + i * STEP
            lw = w(txt)
            lx0, lx1 = (self.edge - lw, self.edge) if side == 'L' else (self.edge, self.edge + lw)
            self.leaves[txt] = (lx0, cy - H / 2, lx1, cy + H / 2, c)
    def left(self, t):  l = self.leaves[t]; return (l[0], (l[1] + l[3]) / 2)
    def right(self, t): l = self.leaves[t]; return (l[2], (l[1] + l[3]) / 2)
    def draw(self):
        o = []
        ys = [(l[1] + l[3]) / 2 for l in self.leaves.values()]
        o.append(f'<line x1="{self.br}" y1="{min(ys)}" x2="{self.br}" y2="{max(ys)}" stroke="#333" stroke-width="0.9"/>')
        for l in self.leaves.values():
            cy = (l[1] + l[3]) / 2
            o.append(f'<line x1="{self.br}" y1="{cy}" x2="{self.edge}" y2="{cy}" stroke="#333" stroke-width="0.9"/>')
        gx = self.rect[0] if self.side == 'L' else self.rect[2]
        o.append(f'<line x1="{self.br}" y1="{self.cy}" x2="{gx}" y2="{self.cy}" stroke="#333" stroke-width="0.9"/>')
        return o
    def nodes(self):
        o = [box(*l[:4], l[4], 3, FS, t) for t, l in self.leaves.items()]
        o.append(box(*self.rect, self.col, 6, self.fs, self.name))
        o.append(toggle(self.tog, self.cy))
        return o

KU = Group('苦', (300, 70, 352, 104), 'w', 'L',
           [(t, 'w') for t in ['生苦', '老苦', '病苦', '死苦', '怨憎会苦', '爱别离苦', '所求不得苦', '五盛阴苦']], fs=19)
JI = Group('集', (300, 212, 352, 246), 'w', 'L', [('惑 · 无明 爱 取', 'r'), ('业 · 行 有', 'b')], fs=19)
TYPE = {'无明': 'r', '爱': 'r', '取': 'r', '行': 'b', '有': 'b'}
LINKS = ['无明', '行', '识', '名色', '六入', '触', '受', '爱', '取', '有', '生', '老死']
SHUN = Group('十二因缘 · 顺转', (186, 391, 300, 425), 'w', 'L', [(x, TYPE.get(x, 'w')) for x in LINKS], fs=14)
MIE = Group('灭', (648, 59, 700, 93), 'm', 'R',
            [('贪欲永尽', 'm'), ('瞋恚永尽', 'm'), ('愚痴永尽', 'm'), ('一切烦恼永尽', 'm')], fs=19)
NI = Group('十二因缘 · 逆转', (712, 261, 826, 295), 'm', 'R', [(x + '灭', 'm') for x in LINKS], fs=14)
DAO = Group('道', (648, 473, 700, 507), 'm', 'R',
            [('正见', 'c'), ('正思惟', 'w'), ('正语', 'w'), ('正业', 'w'), ('正命', 'w'), ('正精进', 'o'), ('正念', 'y'), ('正定', 'g')], fs=19)
DP = Group('三十七道品', (520, 485, 616, 519), 'w', 'L',
           [('四念处', 'y'), ('四正勤', 'o'), ('四如意足', 'w'), ('五根', 'w'), ('五力', 'w'), ('七觉支', 'w'), ('八正道', 'w')], fs=14)
GROUPS = [KU, JI, SHUN, MIE, NI, DAO, DP]
CENTER = (420, 248, 580, 312)

def svg():
    o = ['<svg class="mm" viewBox="0 0 1000 580" xmlns="http://www.w3.org/2000/svg">'] + defs()
    # 树干：中心 → 四谛；集 → 顺转；灭 → 逆转；道 → 三十七道品
    for a, b in [((436, 248), (352, 87)), ((420, 266), (352, 229)), ((580, 260), (648, 76)), ((566, 312), (648, 490)),
                 ((326, 246), (290, 391)), ((684, 93), (740, 261)), ((648, 496), (616, 502))]:
        o.append(solid(a, b))
    for g in GROUPS: o += g.draw()
    # 点线：跨分支的对应
    ax, ay = JI.left('惑 · 无明 爱 取'); bx, by = JI.left('业 · 行 有')
    for t in ['无明', '爱', '取']:
        tx, ty = SHUN.right(t)
        lx, ly = SHUN.left(t)
        o.append(dotted('r', f'M{ax},{ay} C{ax-70},{ay+6} {lx-34},{ly-60} {lx-3},{ly}', True))
    for t in ['行', '有']:
        tx, ty = SHUN.right(t)
        lx, ly = SHUN.left(t)
        o.append(dotted('u', f'M{bx},{by} C{bx-80},{by+10} {lx-52},{ly-70} {lx-3},{ly}', True))
    for t, tgt, dx in [('生苦', '生', 0), ('老苦', '老死', 10), ('死苦', '老死', 20)]:
        sx, sy = KU.left(t); tx, ty = SHUN.left(tgt)
        o.append(dotted('s', f'M{sx},{sy} C{sx-150-dx},{sy+20} {20+dx},{ty-220} {30+dx},{ty-60} C{36+dx},{ty-10} {tx-30},{ty} {tx-3},{ty}', True))
    o.append(label('＝', 34, 330))
    # 集 → 苦，道 → 灭：因 → 果
    o.append(dotted('k', 'M326,212 L326,107', True)); o.append(label('因 → 果', 352, 165))
    o.append(dotted('k', 'M674,473 C672,350 672,200 674,96', True)); o.append(label('因 → 果', 646, 400))
    # 灭 ＝ 逆转
    sx, sy = MIE.right('愚痴永尽'); tx, ty = NI.left('无明灭')
    o.append(dotted('g', f'M{sx},{sy} C{sx+40},{sy+10} {tx-40},{ty-20} {tx-3},{ty}', True)); o.append(label('＝', (sx+tx)/2+8, (sy+ty)/2-4))
    sx, sy = MIE.right('贪欲永尽'); tx, ty = NI.right('爱灭')
    o.append(dotted('g', f'M{sx},{sy} C{sx+120},{sy-10} 1000,120 975,230 C960,290 930,{ty} {tx+3},{ty}', True)); o.append(label('＝', 978, 200))
    # 正见 → 无明灭：无明离欲而生明
    sx, sy = DAO.right('正见'); tx, ty = NI.right('无明灭')
    o.append(dotted('n', f'M{sx},{sy} C{sx+120},{sy+30} 962,440 952,320 C944,220 930,{ty} {tx+3},{ty}', True)); o.append(label('生明', 952, 340))
    # 节点
    for g in GROUPS: o += g.nodes()
    o.append(box(*CENTER, 'w', 10, 30, '四圣谛'))
    # 图例
    for x, c, t in [(176, 'r', '惑'), (226, 'b', '业'), (276, 'w', '事·苦果'), (356, 'm', '还灭')]:
        o.append(box(x, 556, x + 20, 569, c, 2, 9, ''))
        o.append(f'<text x="{x+25}" y="567" font-size="11" class="lg">{t}</text>')
    o.append('</svg>')
    return '\n'.join(o)

inject('MINDMAP_OVERVIEW', svg())
print('ok')
