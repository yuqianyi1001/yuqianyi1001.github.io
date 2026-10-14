"""XMind 风格思维导图的公用画法：玻璃质感节点、点线、箭头、⊖ 折叠钮。坐标单位与 SVG viewBox 一致。"""
import re, pathlib

FILL = {  # 上浅、下深、描边
    'w': ('#ffffff', '#f1f1f1', '#3a3a3a'),
    'c': ('#b6f3f3', '#4fc9cf', '#2b7f86'),   # 慧：青
    'y': ('#ffff9a', '#f3e61e', '#8f8a12'),   # 念：黄
    'o': ('#ffd38a', '#f0981e', '#9a5a0c'),   # 精进：橙
    'g': ('#a8f5a0', '#3cc43a', '#24772a'),   # 定：绿
    'r': ('#ffc2c2', '#e46e6e', '#9a3434'),   # 信 / 惑：红
    'b': ('#d6e2ff', '#86a0dc', '#3d5592'),   # 业：蓝
    'm': ('#e9fbe6', '#b9e8b0', '#4f8a4a'),   # 灭：浅绿
}
LINE = {'y': '#c4cb34', 'b': '#a2520e', 'r': '#b02a2a', 'g': '#1d6e1d', 'n': '#16166e',
        'k': '#111111', 'u': '#3d5592', 's': '#555555'}

PFX = ''  # 同一页面有多张 SVG 时，渐变和箭头的 id 加前缀，避免互相引用

def defs():
    o = ['<defs>']
    for k, (top, bot, _) in FILL.items():
        o.append(f'<linearGradient id="{PFX}g{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>')
    for k, c in LINE.items():
        o.append(f'<marker id="{PFX}a{k}" viewBox="0 0 8 8" refX="7.4" refY="4" markerWidth="8" markerHeight="8" orient="auto" markerUnits="userSpaceOnUse"><path d="M1,0.6 L7.4,4 L1,7.4" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker>')
    o.append('</defs>')
    return o

def box(x0, y0, x1, y1, col, r, fs, txt, weight=None):
    top, bot, stroke = FILL[col]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    fw = f' font-weight="{weight}"' if weight else ''
    return (f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" rx="{r}" fill="url(#{PFX}g{col})" stroke="{stroke}" stroke-width="0.9"/>'
            f'<rect x="{x0+1.2}" y="{y0+1.2}" width="{x1-x0-2.4}" height="{(y1-y0)*0.42}" rx="{max(r-1,1)}" fill="#fff" opacity="{0.35 if col!="w" else 0}"/>'
            f'<text x="{cx}" y="{cy+fs*0.36}" font-size="{fs}" text-anchor="middle"{fw}>{txt}</text>')

def toggle(mx, my):
    return (f'<circle cx="{mx}" cy="{my}" r="4" fill="#e3ebf7" stroke="#8aa3c8" stroke-width="0.8"/>'
            f'<line x1="{mx-2.2}" y1="{my}" x2="{mx+2.2}" y2="{my}" stroke="#5a78a8" stroke-width="0.9"/>')

def dotted(col, d, arrow=False):
    mk = f' marker-end="url(#{PFX}a{col})"' if arrow else ''
    return f'<path d="{d}" fill="none" stroke="{LINE[col]}" stroke-width="2" stroke-dasharray="0 3.1" stroke-linecap="round"{mk}/>'

def solid(a, b):
    return f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#222" stroke-width="0.9"/>'

def label(t, x, y, fs=11):
    return f'<text x="{x}" y="{y}" font-size="{fs}" text-anchor="middle" class="lb">{t}</text>'

def inject(marker, svg_text):
    p = pathlib.Path(__file__).resolve().parent.parent / 'cards.html'
    s = p.read_text()
    s, n = re.subn(rf'(<!-- {marker} -->).*?(<!-- /{marker} -->)', lambda m: m.group(1) + '\n' + svg_text + '\n' + m.group(2), s, flags=re.S)
    assert n == 1, marker
    p.write_text(s)
