#!/usr/bin/env python3
"""总图的思维导图版：四圣谛 → 苦、集、灭、道，道下挂三十七道品。十二因缘只画一列：
框和 ↓ 是顺转，框右边「X灭 ↓」是逆转。点线：集＝惑＋业，苦果落在生、老死，灭＝还灭那一列，正见生明而无明灭。
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
JI = Group('集', (300, 270, 352, 304), 'w', 'L', [('惑 · 无明 爱 取', 'r'), ('业 · 行 有', 'b')], fs=19)
MIE = Group('灭', (648, 70, 700, 104), 'm', 'R',
            [('贪欲永尽', 'm'), ('瞋恚永尽', 'm'), ('愚痴永尽', 'm'), ('一切烦恼永尽', 'm')], fs=19)
DAO = Group('道', (648, 300, 700, 334), 'm', 'R',
            [('正见', 'c'), ('正思惟', 'w'), ('正语', 'w'), ('正业', 'w'), ('正命', 'w'), ('正精进', 'o'), ('正念', 'y'), ('正定', 'g')], fs=19)
DP = Group('三十七道品', (648, 470, 744, 504), 'w', 'R',
           [('四念处', 'y'), ('四正勤', 'o'), ('四如意足', 'w'), ('五根', 'w'), ('五力', 'w'), ('七觉支', 'w'), ('八正道', 'w')], fs=14)
GROUPS = [KU, JI, MIE, DAO, DP]
CENTER = (420, 8, 580, 64)
YIN = (424, 90, 512, 120)  # 「十二因缘」

# 十二因缘只画一列：框和 ↓ 是顺转；框右边的「X灭 ↓」是逆转
TYPE = {'无明': 'r', '爱': 'r', '取': 'r', '行': 'b', '有': 'b'}
LINKS = ['无明', '行', '识', '名色', '六入', '触', '受', '爱', '取', '有', '生', '老死']
BX0, BX1, NX, ROW0, PITCH, BH = 432, 492, 540, 154, 32, 20
def row(t): i = LINKS.index(t); return ROW0 + i * PITCH
def lft(t): return (BX0, row(t) + BH / 2)

def svg():
    o = ['<svg class="mm" viewBox="0 0 1000 580" xmlns="http://www.w3.org/2000/svg">'] + defs()
    for a, b in [((420, 36), (352, 87)), ((420, 56), (352, 287)), ((580, 36), (648, 87)), ((580, 56), (648, 312)),
                 ((468, 64), (468, 90)), ((674, 334), (696, 470))]:
        o.append(solid(a, b))
    for g in GROUPS: o += g.draw()
    # 集＝惑＋业 → 对应的支
    for t in ['无明', '爱', '取']:
        tx, ty = lft(t)
        o.append(dotted('r', f'M352,284 C398,284 {tx-48},{ty} {tx-3},{ty}', True))
    for t in ['行', '有']:
        tx, ty = lft(t)
        o.append(dotted('u', f'M352,292 C392,296 {tx-44},{ty} {tx-3},{ty}', True))
    # 苦果落在生、老死
    for t, d in [('生', 0), ('老死', 8)]:
        tx, ty = lft(t)
        o.append(dotted('s', f'M352,98 C{392+d},120 {372+d},{ty-60} {tx-3},{ty}', True))
    # 集 → 苦，道 → 灭：因 → 果
    o.append(dotted('k', 'M326,270 L326,107', True)); o.append(label('因 → 果', 352, 190))
    o.append(dotted('k', 'M674,300 L674,107', True)); o.append(label('因 → 果', 646, 205))
    # 灭 ＝ 还灭那一列；正见 → 无明灭（生明）
    o.append(dotted('g', f'M648,100 C618,104 600,118 {NX+14},{ROW0-16}', True)); o.append(label('＝', 622, 116))
    nx_end = NX + 22
    o.append(dotted('n', f'M648,312 C606,300 616,{ROW0+40} {nx_end+3},{ROW0+BH/2}', True)); o.append(label('生明', 604, 230))
    # 节点
    for g in GROUPS: o += g.nodes()
    o.append(box(*CENTER, 'w', 10, 30, '四圣谛'))
    o.append(box(*YIN, 'w', 6, 15, '十二因缘'))
    cx = (BX0 + BX1) / 2
    o.append(f'<text x="{cx}" y="{ROW0-8}" font-size="10.5" text-anchor="middle" class="lg">顺转</text>')
    o.append(f'<text x="{NX}" y="{ROW0-8}" font-size="10.5" text-anchor="middle" class="ni">逆转</text>')
    for i, t in enumerate(LINKS):
        y = row(t)
        o.append(box(BX0, y, BX1, y + BH, TYPE.get(t, 'w'), 3, FS, t))
        o.append(f'<text x="{NX}" y="{y+14}" font-size="11.5" text-anchor="middle" class="ni">{t}灭</text>')
        ay = y + BH + (PITCH - BH) / 2 + 4
        o.append(f'<text x="{cx}" y="{ay}" font-size="10" text-anchor="middle" class="ar">↓</text>')
        o.append(f'<text x="{NX}" y="{ay}" font-size="10" text-anchor="middle" class="ni">↓</text>')
    yend = row('老死') + PITCH + 12
    o.append(f'<text x="{cx}" y="{yend}" font-size="11.5" text-anchor="middle" class="ar">纯大苦聚集</text>')
    o.append(f'<text x="{NX}" y="{yend}" font-size="11.5" text-anchor="middle" class="ni">纯大苦聚灭</text>')
    # 图例
    for (x0, y0, c, t) in [(40, 520, 'r', '惑'), (96, 520, 'b', '业'), (40, 540, 'w', '事·苦果'), (120, 540, 'm', '还灭')]:
        o.append(box(x0, y0, x0 + 20, y0 + 13, c, 2, 9, ''))
        o.append(f'<text x="{x0+25}" y="{y0+11}" font-size="11" class="lg">{t}</text>')
    o.append('</svg>')
    return '\n'.join(o)

inject('MINDMAP_OVERVIEW', svg())
print('ok')
