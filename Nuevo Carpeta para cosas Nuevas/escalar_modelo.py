#!/usr/bin/env python3
import argparse
import os
import shutil
import sys
import xml.etree.ElementTree as ET

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, 'Worlds', 'models')


def fmt(v):
    return f'{v:.6g}'


def scale_pose(elem, k):
    v = [float(x) for x in elem.text.split()]
    v[0] *= k
    v[1] *= k
    elem.text = ' '.join(fmt(x) for x in v)


def scale_size(elem, k, k_thickness, k_height):
    v = [float(x) for x in elem.text.split()]
    elem.text = ' '.join(fmt(x) for x in (v[0] * k, v[1] * k_thickness, v[2] * k_height))


def write_xml(tree, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write("<?xml version='1.0'?>\n")
        f.write(ET.tostring(tree.getroot(), encoding='unicode'))
        f.write('\n')


def rename_model(model_dir, new_name):
    config = os.path.join(model_dir, 'model.config')
    tree = ET.parse(config)
    tree.getroot().find('name').text = new_name
    write_xml(tree, config)
    sdf = os.path.join(model_dir, 'model.sdf')
    tree = ET.parse(sdf)
    tree.getroot().find('model').set('name', new_name)
    write_xml(tree, sdf)


def main():
    parser = argparse.ArgumentParser(
        description='Crea Worlds/models/<nombre> escalando en planta el modelo <nombre>_original.')
    parser.add_argument('factor', type=float, help='multiplicador de escala en X e Y (p. ej. 1.15)')
    parser.add_argument('--nombre', default='TD_n1', help='nombre del modelo (por defecto TD_n1)')
    parser.add_argument('--escalar-grosor', action='store_true', help='escalar también el grosor de las paredes')
    parser.add_argument('--escalar-altura', action='store_true', help='escalar también la altura de las paredes')
    args = parser.parse_args()

    if args.factor <= 0:
        sys.exit('El factor debe ser mayor que 0')

    model_dir = os.path.join(MODELS_DIR, args.nombre)
    original_name = args.nombre + '_original'
    original_dir = os.path.join(MODELS_DIR, original_name)

    if not os.path.isdir(original_dir):
        if not os.path.isfile(os.path.join(model_dir, 'model.sdf')):
            sys.exit(f'No existe {model_dir}/model.sdf')
        os.rename(model_dir, original_dir)
        rename_model(original_dir, original_name)
        print(f'Original movido a {original_dir}')

    tree = ET.parse(os.path.join(original_dir, 'model.sdf'))
    model = tree.getroot().find('model')
    model.set('name', args.nombre)

    k = args.factor
    k_thickness = k if args.escalar_grosor else 1.0
    k_height = k if args.escalar_altura else 1.0

    model_pose = model.find('pose')
    if model_pose is not None:
        scale_pose(model_pose, k)

    for link in model.findall('link'):
        link_pose = link.find('pose')
        if link_pose is not None:
            scale_pose(link_pose, k)
        for part in link.findall('collision') + link.findall('visual'):
            local_pose = part.find('pose')
            if local_pose is not None and k_height != 1.0:
                v = [float(x) for x in local_pose.text.split()]
                v[2] *= k_height
                local_pose.text = ' '.join(fmt(x) for x in v)
            size = part.find('geometry/box/size')
            if size is not None:
                scale_size(size, k, k_thickness, k_height)

    if os.path.isdir(model_dir):
        shutil.rmtree(model_dir)
    os.makedirs(model_dir)
    write_xml(tree, os.path.join(model_dir, 'model.sdf'))
    shutil.copy(os.path.join(original_dir, 'model.config'), model_dir)
    config = os.path.join(model_dir, 'model.config')
    ctree = ET.parse(config)
    ctree.getroot().find('name').text = args.nombre
    write_xml(ctree, config)

    print(f'Creado {model_dir} con factor {k} '
          f'(grosor x{k_thickness}, altura x{k_height}) a partir de {original_name}')


if __name__ == '__main__':
    main()
