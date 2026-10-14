#!/usr/bin/env python3
"""生成「三十七道品」思维导图卡（还原 XMind 原图），写入 cards.html 的 MINDMAP37 标记之间。
坐标按原图 756×602 像素量取，SVG viewBox 与原图一致。"""
import pathlib, re

import sys; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import xmind
from xmind import FILL, LINE as C, TIER1, TIER2, defs, box as _box, toggle, inject
LEAF, GROUP = [], []
def leaves(items, x0=None, x1=None, ys=None):
    for (txt, col, a, b), y in zip(items, ys):
        LEAF.append((a, y, b, y + 20, txt, col))

# 八正道（子节点在左，右缘 193）
for txt, col, x0, y in [('正見','c',156,11),('正思惟','w',143,36),('正語','w',156,61),('正業','w',156,86),
                        ('正命','w',156,111),('正精進','o',143,136),('正念','y',156,161),('正定','g',156,186)]:
    LEAF.append((x0, y, 193, y + 20, txt, col))
# 四念住
for txt, y in [('身念住',59),('受念住',84),('心念住',109),('法念住',134)]:
    LEAF.append((543, y, 592, y + 20, txt, 'y'))
# 四正勤
for txt, x1, y in [('已起惡不善法斷',698,188),('未起惡不善法不起',712,213),('未起善法令起',685,238),('已起善法增益修習',712,263)]:
    LEAF.append((597, y, x1, y + 20, txt, 'o'))
# 四神足
for txt, col, x1, y in [('欲神足','w',648,317),('精進神足','o',661,342),('心神足','y',648,367),('觀神足','y',648,392)]:
    LEAF.append((599, y, x1, y + 20, txt, col))
# 五根
for txt, col, x1, y in [('信根','r',562,446),('精進根','o',576,471),('念根','y',562,496),('定根','g',562,521),('慧根','c',562,546)]:
    LEAF.append((526, y, x1, y + 20, txt, col))
# 五力（子节点在左，右缘 210）
for txt, col, x0, y in [('信力','r',174,443),('精進力','o',161,468),('念力','y',174,493),('定力','g',174,518),('慧力','c',174,543)]:
    LEAF.append((x0, y, 210, y + 20, txt, col))
# 七觉支（子节点在左，右缘 135）
for txt, col, x0, y in [('念覺支','y',86,239),('擇法覺支','w',73,264),('精進覺支','o',73,289),('猗覺支','w',86,314),
                        ('喜覺支','w',86,339),('定覺支','g',86,364),('捨覺支','w',86,389)]:
    LEAF.append((x0, y, 135, y + 20, txt, col))

# 分组节点：(框, 颜色, ⊖位置, 括号线 x, 子节点范围, 子在左/右)
GROUPS = [
    ('八正道', (216,90,281,126), 'w', (208,108), 202, (21,196), 'L', (193,)),
    ('四念住', (454,87,520,124), 'y', (527,106), 534, (69,144), 'R', (543,)),
    ('四正勤', (509,217,574,253), 'o', (581,235), 588, (198,273), 'R', (597,)),
    ('四神足', (510,345,576,382), 'w', (583,364), 590, (327,402), 'R', (599,)),
    ('五根',   (454,488,503,524), 'w', (509,506), 516, (456,556), 'R', (526,)),
    ('五力',   (233,485,281,521), 'w', (226,503), 219, (453,553), 'L', (210,)),
    ('七覺支', (158,306,223,342), 'w', (150,324), 145, (249,399), 'L', (135,)),
]
CENTER = (286, 274, 452, 336)
SOLID = [((282,110),(355,274)), ((456,110),(384,274)), ((430,274),(509,244)), ((446,334),(510,363)),
         ((383,336),(455,503)), ((356,336),(282,503)), ((286,318),(224,324))]

# (颜色, 路径, 是否箭头, [(标签, x, y)])
DOTS = [
    ('y','M454,104 C390,108 262,126 194,166',0,[('=',323,124)]),
    ('y','M454,112 C380,132 232,220 136,247',0,[('=',301,178)]),
    ('y','M521,105 C600,110 692,150 736,230 C764,292 722,362 649,377',0,[]),
    ('y','M521,110 C612,124 702,170 744,252 C772,322 716,396 649,402',0,[]),
    ('y','M484,124 C470,200 454,300 461,392 C467,462 500,496 526,503',0,[('=',457,339)]),
    ('y','M476,124 C462,212 446,312 456,402 C464,472 498,506 526,509',0,[]),
    ('y','M526,509 C470,536 290,540 214,505',1,[]),
    ('b','M194,146 C300,150 442,190 509,228',0,[('=',376,166)]),
    ('b','M136,298 C250,262 402,226 509,237',0,[('=',323,240)]),
    ('b','M517,253 C482,300 464,380 476,430 C486,466 506,476 526,480',0,[('=',478,345)]),
    ('b','M550,254 C560,300 576,332 599,350',0,[]),
    ('b','M526,482 C430,470 300,474 214,478',1,[]),
    ('r','M526,457 C420,444 300,449 214,453',1,[]),
    ('g','M156,196 C92,206 40,260 50,320 C58,360 80,372 86,374',0,[]),
    ('g','M86,378 C55,386 50,440 80,490 C110,526 150,530 174,528',0,[]),
    ('g','M526,532 C430,552 300,546 214,528',1,[]),
    ('n','M156,21 C60,40 10,200 20,380 C30,530 150,590 330,592 C430,592 490,580 526,558',0,[]),
    ('n','M526,556 C430,576 300,571 214,553',1,[]),
    ('k','M455,117 C400,150 272,238 222,301',1,[('滿足',334,203)]),
]

def box(x0, y0, x1, y1, col, r, fs, txt, **kw):
    return _box(x0, y0, x1, y1, col, r, fs, txt, **kw)

S2T = str.maketrans('', '')
SIMP = str.maketrans({'見':'见','語':'语','業':'业','進':'进','覺':'觉','擇':'择','捨':'舍','惡':'恶','斷':'断',
                      '習':'习','觀':'观','聖':'圣','諦':'谛','滿':'满','勤':'勤','益':'益'})

def body(simplified=False, emph=False):
    """emph=True：嵌入总图时用，八正道按第一层强调、三十七道品按第二层强调；单独那张原图不强调。"""
    tr = SIMP if simplified else S2T
    o = []
    # 实线：中心到各组
    for (a, b) in SOLID:
        if emph and a == (282, 110): a = (296, 112)
        o.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#222" stroke-width="0.9"/>')
    # 树形括号
    for name, (x0,y0,x1,y1), col, (mx,my), bx, (ya,yb), side, (edge,) in GROUPS:
        o.append(f'<line x1="{bx}" y1="{ya}" x2="{bx}" y2="{yb}" stroke="#333" stroke-width="0.9"/>')
        for lx0, ly0, lx1, ly1, *_ in LEAF:
            cy = (ly0 + ly1) / 2
            if ya - 1 <= cy <= yb + 1 and ((side == 'L' and lx1 == edge) or (side == 'R' and lx0 == edge)):
                o.append(f'<line x1="{bx}" y1="{cy}" x2="{edge}" y2="{cy}" stroke="#333" stroke-width="0.9"/>')
        gx = x1 if side == 'L' else x0
        o.append(f'<line x1="{bx}" y1="{my}" x2="{gx}" y2="{my}" stroke="#333" stroke-width="0.9"/>')
    # 虚线（点线）关系
    for col, d, arrow, labels in DOTS:
        mk = f' marker-end="url(#{xmind.PFX}a{col})"' if arrow else ''
        o.append(f'<path d="{d}" fill="none" stroke="{C[col]}" stroke-width="2" stroke-dasharray="0 3.1" stroke-linecap="round"{mk}/>')
    # 节点
    for x0, y0, x1, y1, txt, col in LEAF:
        o.append(box(x0, y0, x1, y1, col, 3, 11.5, txt))
    for name, (x0,y0,x1,y1), col, (mx,my), *_ in GROUPS:
        if emph and name == '八正道':
            o.append(box(212, 84, 296, 132, col, 7, 22, name, **TIER1))
        else:
            o.append(box(x0, y0, x1, y1, col, 6, 16.5, name))
        o.append(toggle(mx, my))
    o.append(box(*CENTER, 'w', 10, 21, '三十七道品', **TIER2) if emph else box(*CENTER, 'w', 10, 25, '三十七道品'))
    # 标签（放在节点之后、带底色，避免被线穿过）
    for col, d, arrow, labels in DOTS:
        for t, x, y in labels:
            o.append(f'<text x="{x}" y="{y}" font-size="{11 if t!="=" else 11}" text-anchor="middle" fill="#555" class="lb">{t}</text>')
    o.append('<text x="24" y="371" font-size="11" text-anchor="middle" fill="#555" class="lb">四聖諦</text>')
    return [x.translate(tr) for x in o]

def svg():
    return '\n'.join(['<svg class="mm" viewBox="0 0 756 602" xmlns="http://www.w3.org/2000/svg">'] + defs() + body() + ['</svg>'])

if __name__ == '__main__':
    inject('MINDMAP37', svg())
    print('ok')
