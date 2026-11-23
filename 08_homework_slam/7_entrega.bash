#!/bin/bash
BAG="${1%/}"
if [ ! -f "$BAG/metadata.yaml" ]; then
    echo "Uso: ./7_entrega.bash carpeta_del_bag"
    exit 1
fi
mkdir -p entrega
rm -f "entrega/$(basename "$BAG").zip"
zip -r "entrega/$(basename "$BAG").zip" "$BAG"
python3 6_pdf.py "$BAG" entrega/comparacion_SLAM_gazebo.pdf
ls -lh entrega
