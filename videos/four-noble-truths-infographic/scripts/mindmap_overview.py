#!/usr/bin/env python3
"""总图的思维导图版。四圣谛 → 苦、集、灭、道。
苦、集只用十二因缘说：十二支一列，左边按三世两重因果分四段（集＝过去因、现在因；苦＝现在果、未来果）。
框和 ↓ 是顺转，框右边绿色「X灭 ↓」是逆转（灭）。道下面直接嵌入三十七道品导图（简体）。
写入 cards.html 的 MINDMAP_OVERVIEW 标记之间。viewBox 1680×920，单位约等于像素。"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import xmind
xmind.PFX = 'ov'
from xmind import defs, box, toggle, dotted, solid, label, inject
import mindmap37

FS = 19
TYPE = {'无明': 'r', '爱': 'r', '取': 'r', '行': 'b', '有': 'b'}
LINKS = ['无明', '行', '识', '名色', '六入', '触', '受', '爱', '取', '有', '生', '老死']
BX0, BX1, NX = 318, 398, 494          # 顺转框、逆转文字的位置
ROW0, PITCH, BH = 190, 56, 30
def ry(i): return ROW0 + i * PITCH
def mid(i, j): return (ry(i) + ry(j) + BH) / 2

CENTER = (236, 16, 436, 92)
YIN = (306, 112, 410, 146)
JI, KU = (40, 300, 120, 344), (40, 600, 120, 644)
MIE, DAO = (690, 20, 770, 60), (1124, 20, 1204, 60)
# 三十七道品导图：原图 756×602，缩放后放在右侧
MX, MY, MS = 680, 128, 1.312
def mp(x, y): return (MX + x * MS, MY + y * MS)

# 三世两重因果：(起, 止, 标签, 属于)
SEGS = [(0, 1, '过去因', 'ji'), (2, 6, '现在果', 'ku'), (7, 9, '现在因', 'ji'), (10, 11, '未来果', 'ku')]
BRX = 300

def svg():
    o = [f'<svg class="mm" viewBox="0 0 1680 920" xmlns="http://www.w3.org/2000/svg">'] + defs()
    # 嵌入的三十七道品导图
    o.append(f'<g transform="translate({MX},{MY}) scale({MS})">')
    o += mindmap37.body(simplified=True)
    o.append('</g>')
    # 树干
    cx = (BX0 + BX1) / 2
    for a, b in [((236, 60), (80, 300)), ((250, 92), (80, 600)), ((436, 40), (690, 40)),
                 ((436, 76), (1124, 50)), ((cx, 92), (cx, 112)), ((1164, 60), mp(369, 274))]:
        o.append(solid(a, b))
    # 三世两重因果的括号
    for i, j, t, who in SEGS:
        y0, y1 = ry(i) + 4, ry(j) + BH - 4
        o.append(f'<path d="M{BRX+8},{y0} L{BRX},{y0} L{BRX},{y1} L{BRX+8},{y1}" fill="none" stroke="#777" stroke-width="1.4"/>')
        o.append(f'<text x="{BRX-8}" y="{(y0+y1)/2+7}" font-size="18" text-anchor="end" class="lg">{t}</text>')
    # 集 → 两段「因」，苦 → 两段「果」
    for i, j, t, who in SEGS:
        sx, sy = (JI[2], (JI[1] + JI[3]) / 2) if who == 'ji' else (KU[2], (KU[1] + KU[3]) / 2)
        ty = mid(i, j)
        col = 'r' if who == 'ji' else 's'
        o.append(dotted(col, f'M{sx},{sy} C{sx+60},{sy} {BRX-130},{ty} {BRX-76},{ty}', True))
    o.append(dotted('k', f'M80,{JI[3]} L80,{KU[1]-3}', True)); o.append(label('因 → 果', 80, 480, 17))
    # 灭 ＝ 逆转那一列；道 → 灭：因 → 果
    o.append(dotted('g', f'M{MIE[0]},{MIE[3]-6} C{MIE[0]-80},{MIE[3]+30} {NX+40},{ROW0-60} {NX+6},{ROW0-38}', True))
    o.append(label('＝', 600, 112, 17))
    o.append(dotted('k', f'M{DAO[0]},{DAO[1]+6} C{DAO[0]-120},{DAO[1]-14} {MIE[2]+110},{MIE[1]-14} {MIE[2]+3},{MIE[1]+8}', True))
    o.append(label('因 → 果', 950, 14, 17))
    # 节点
    o.append(box(*CENTER, 'w', 12, 44, '四圣谛'))
    for r, t, c in [(JI, '集', 'w'), (KU, '苦', 'w'), (MIE, '灭', 'm'), (DAO, '道', 'm')]:
        o.append(box(*r, c, 8, 28, t))
    o.append(box(*YIN, 'w', 7, 21, '十二因缘'))
    o.append(f'<text x="{cx}" y="{ROW0-14}" font-size="17" text-anchor="middle" class="lg">顺转</text>')
    o.append(f'<text x="{NX}" y="{ROW0-14}" font-size="17" text-anchor="middle" class="ni">逆转</text>')
    for i, t in enumerate(LINKS):
        y = ry(i)
        o.append(box(BX0, y, BX1, y + BH, TYPE.get(t, 'w'), 4, FS, t))
        o.append(f'<text x="{NX}" y="{y+21}" font-size="19" text-anchor="middle" class="ni">{t}灭</text>')
        ay = y + BH + (PITCH - BH) / 2 + 6
        o.append(f'<text x="{cx}" y="{ay}" font-size="16" text-anchor="middle" class="ar">↓</text>')
        o.append(f'<text x="{NX}" y="{ay}" font-size="16" text-anchor="middle" class="ni">↓</text>')
    yend = ry(11) + PITCH + 20
    o.append(f'<text x="{cx}" y="{yend}" font-size="19" text-anchor="middle" class="ar">纯大苦聚集</text>')
    o.append(f'<text x="{NX}" y="{yend}" font-size="19" text-anchor="middle" class="ni">纯大苦聚灭</text>')
    # 图例
    for (x0, y0, c, t) in [(30, 780, 'r', '惑'), (130, 780, 'b', '业'), (30, 814, 'w', '事'), (130, 814, 'm', '还灭')]:
        o.append(box(x0, y0, x0 + 30, y0 + 20, c, 3, 9, ''))
        o.append(f'<text x="{x0+38}" y="{y0+17}" font-size="18" class="lg">{t}</text>')
    o.append('</svg>')
    return '\n'.join(o)

if __name__ == '__main__':
    inject('MINDMAP_OVERVIEW', svg())
    print('ok')
