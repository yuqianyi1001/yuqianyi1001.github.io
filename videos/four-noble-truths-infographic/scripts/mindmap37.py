#!/usr/bin/env python3
"""生成「三十七道品」思维导图卡（还原 XMind 原图），写入 cards.html 的 MINDMAP37 标记之间。
坐标按原图 756×602 像素量取，SVG viewBox 与原图一致。"""
import pathlib, re

FILL = {  # 原图的玻璃质感配色：上浅下深
    'w': ('#ffffff', '#f1f1f1', '#3a3a3a'),
    'c': ('#b6f3f3', '#4fc9cf', '#2b7f86'),   # 慧：青
    'y': ('#ffff9a', '#f3e61e', '#8f8a12'),   # 念：黄
    'o': ('#ffd38a', '#f0981e', '#9a5a0c'),   # 精进：橙
    'g': ('#a8f5a0', '#3cc43a', '#24772a'),   # 定：绿
    'r': ('#ffc2c2', '#e46e6e', '#9a3434'),   # 信：红
}
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

C = {'y':'#c4cb34','b':'#a2520e','r':'#b02a2a','g':'#1d6e1d','n':'#16166e','k':'#111111'}
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

def box(x0, y0, x1, y1, col, r, fs, txt, bold=False):
    top, bot, stroke = FILL[col]
    gid = f'g{col}'
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" rx="{r}" fill="url(#{gid})" stroke="{stroke}" stroke-width="0.9"/>'
            f'<rect x="{x0+1.2}" y="{y0+1.2}" width="{x1-x0-2.4}" height="{(y1-y0)*0.42}" rx="{max(r-1,1)}" fill="#fff" opacity="{0.35 if col!="w" else 0}"/>'
            f'<text x="{cx}" y="{cy+fs*0.36}" font-size="{fs}" text-anchor="middle"{" font-weight=\"600\"" if bold else ""}>{txt}</text>')

def svg():
    o = ['<svg class="mm" viewBox="0 0 756 602" xmlns="http://www.w3.org/2000/svg">', '<defs>']
    for k, (top, bot, _) in FILL.items():
        o.append(f'<linearGradient id="g{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>')
    for k, c in C.items():
        o.append(f'<marker id="a{k}" viewBox="0 0 8 8" refX="7.4" refY="4" markerWidth="8" markerHeight="8" orient="auto" markerUnits="userSpaceOnUse"><path d="M1,0.6 L7.4,4 L1,7.4" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker>')
    o.append('</defs>')
    # 实线：中心到各组
    for (a, b) in SOLID:
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
        mk = f' marker-start="url(#a{col})"' if False else ''
        mk = f' marker-end="url(#a{col})"' if arrow else ''
        o.append(f'<path d="{d}" fill="none" stroke="{C[col]}" stroke-width="2" stroke-dasharray="0 3.1" stroke-linecap="round"{mk}/>')
    # 节点
    for x0, y0, x1, y1, txt, col in LEAF:
        o.append(box(x0, y0, x1, y1, col, 3, 11.5, txt))
    for name, (x0,y0,x1,y1), col, (mx,my), *_ in GROUPS:
        o.append(box(x0, y0, x1, y1, col, 6, 16.5, name))
        o.append(f'<circle cx="{mx}" cy="{my}" r="4" fill="#e3ebf7" stroke="#8aa3c8" stroke-width="0.8"/><line x1="{mx-2.2}" y1="{my}" x2="{mx+2.2}" y2="{my}" stroke="#5a78a8" stroke-width="0.9"/>')
    o.append(box(*CENTER, 'w', 10, 25, '三十七道品'))
    # 标签（放在节点之后、带底色，避免被线穿过）
    for col, d, arrow, labels in DOTS:
        for t, x, y in labels:
            o.append(f'<text x="{x}" y="{y}" font-size="{11 if t!="=" else 11}" text-anchor="middle" fill="#555" class="lb">{t}</text>')
    o.append('<text x="24" y="371" font-size="11" text-anchor="middle" fill="#555" class="lb">四聖諦</text>')
    o.append('</svg>')
    return '\n'.join(o)

p = pathlib.Path(__file__).resolve().parent.parent / 'cards.html'
s = p.read_text()
s = re.sub(r'(<!-- MINDMAP37 -->).*?(<!-- /MINDMAP37 -->)', lambda m: m.group(1) + '\n' + svg() + '\n' + m.group(2), s, flags=re.S)
p.write_text(s)
print('ok')
