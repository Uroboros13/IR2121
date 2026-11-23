#!/usr/bin/env python3
import glob
import os
import re
import sys
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ALGS = [('cartographer', 'Cartographer'), ('toolbox', 'SLAM Toolbox'), ('rtabmap', 'RTAB-Map')]
W, H = 1754, 1240
BAG = sys.argv[1] if len(sys.argv) > 1 else ''
OUTPDF = sys.argv[2] if len(sys.argv) > 2 else 'comparacion_SLAM.pdf'


def font(size, bold=False):
    for f in ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf',):
        for d in ('/usr/share/fonts/truetype/dejavu/', ''):
            try:
                return ImageFont.truetype(d + f, size)
            except OSError:
                pass
    return ImageFont.load_default()


TF, SF, NF = font(44, True), font(26), font(22)


def crop(path, pad=15):
    a = np.array(Image.open(path).convert('L'))
    ys, xs = np.nonzero(a != 205)
    if len(ys) == 0:
        return Image.fromarray(a)
    return Image.fromarray(a[max(ys.min() - pad, 0):ys.max() + pad, max(xs.min() - pad, 0):xs.max() + pad])


def fit(img, w, h):
    s = min(w / img.width, h / img.height)
    return img.convert('RGB').resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.NEAREST if s >= 1 else Image.LANCZOS)


def new_page(title, sub=''):
    p = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(p)
    d.text((70, 45), title, fill=(0, 0, 0), font=TF)
    if sub:
        d.text((70, 105), sub, fill=(90, 90, 90), font=SF)
    return p, d


def comments():
    txt = open('comentarios.txt', encoding='utf-8').read() if os.path.exists('comentarios.txt') else ''
    out = {}
    for key, body in re.findall(r'\[(\w+)\][ \t]*\n(.*?)(?=\n\[\w+\]|\Z)', txt, re.S):
        out[key] = body.strip()
    return out


def text_block(d, text, x, y, width_chars, f=SF, step=36):
    for para in text.split('\n'):
        for line in textwrap.wrap(para, width_chars) or ['']:
            d.text((x, y), line, fill=(0, 0, 0), font=f)
            y += step
    return y


com = comments()
pages = []
p, d = new_page('Comparación de métodos SLAM en Gazebo', 'Modelo Gazebo del edificio TD (planta 1) · TurtleBot3 burger · ROS 2 Humble')
y = 200
y = text_block(d, 'Bag: ' + (os.path.basename(BAG.rstrip('/')) or '(sin indicar)'), 70, y, 100)
y = text_block(d, 'Topics grabados: /clock /odom /robot_description /scan /tf /tf_static', 70, y + 10, 100)
y = text_block(d, 'Algoritmos: Cartographer, SLAM Toolbox y RTAB-Map', 70, y + 10, 100)
if com.get('general'):
    y = text_block(d, com['general'], 70, y + 30, 100)
pages.append(p)
finals = []
for key, name in ALGS:
    maps = sorted(glob.glob(f'mapas_{key}/map_*.pgm'))
    if not maps:
        p, d = new_page(name, 'Sin mapas: no se ha ejecutado o ha fallado (mira mapas_%s/slam.log)' % key)
        pages.append(p)
        continue
    finals.append((name, maps[-1]))
    for i in range(0, len(maps), 9):
        chunk = maps[i:i + 9]
        p, d = new_page(f'{name}: secuencia de mapas', f'{len(maps)} mapas · página {i // 9 + 1} de {(len(maps) + 8) // 9}')
        cw, ch = (W - 140 - 40) // 3, (H - 190 - 40) // 3
        for j, m in enumerate(chunk):
            cx, cy = 70 + (j % 3) * (cw + 20), 170 + (j // 3) * (ch + 20)
            im = fit(crop(m), cw, ch - 30)
            p.paste(im, (cx + (cw - im.width) // 2, cy + 30 + (ch - 30 - im.height) // 2))
            d.rectangle([cx, cy + 28, cx + cw, cy + ch], outline=(200, 200, 200))
            d.text((cx, cy), os.path.basename(m)[:-4], fill=(0, 0, 0), font=NF)
        pages.append(p)
    p, d = new_page(f'{name}: mapa final', os.path.basename(maps[-1]))
    if com.get(key):
        im = fit(crop(maps[-1]), 1000, H - 220)
        p.paste(im, (70, 170))
        text_block(d, com[key], 1110, 180, 38, NF, 30)
    else:
        im = fit(crop(maps[-1]), W - 140, H - 220)
        p.paste(im, ((W - im.width) // 2, 170))
    pages.append(p)
if finals:
    p, d = new_page('Comparación de los mapas finales')
    cw = (W - 140 - 40) // len(finals)
    for j, (name, m) in enumerate(finals):
        im = fit(crop(m), cw, 650)
        x = 70 + j * (cw + 20)
        d.text((x, 160), name, fill=(0, 0, 0), font=SF)
        p.paste(im, (x + (cw - im.width) // 2, 210))
    if com.get('conclusion'):
        text_block(d, com['conclusion'], 70, 900, 105, NF, 30)
    pages.append(p)
orden = [k for k, _ in ALGS] + ['todos']
for sp in sorted(glob.glob('superposicion_*.png'), key=lambda x: orden.index(os.path.basename(x)[14:-4]) if os.path.basename(x)[14:-4] in orden else 99):
    nombre = os.path.basename(sp)[len('superposicion_'):-4]
    titulo = dict(ALGS).get(nombre, 'Los tres algoritmos' if nombre == 'todos' else nombre)
    p, d = new_page(f'{titulo} sobre el plano real', 'Plano TD-02, planta nivel 1, escala 1:200 · rojo: paredes del mapa · azul: espacio libre')
    im = fit(Image.open(sp), W - 140, H - 220)
    p.paste(im, ((W - im.width) // 2, 170))
    pages.append(p)
pages[0].save(OUTPDF, save_all=True, append_images=pages[1:], resolution=150)
print(f'{OUTPDF}: {len(pages)} páginas')
