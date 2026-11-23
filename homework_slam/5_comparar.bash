#!/bin/bash
BAG="${1%/}"
RATE="${2:-1.0}"
EVERY="${3:-20}"
if [ ! -f "$BAG/metadata.yaml" ]; then
    echo "Uso: ./5_comparar.bash carpeta_del_bag [velocidad] [segundos_entre_mapas]"
    exit 1
fi
for ALG in cartographer toolbox rtabmap; do
    ./4_slam.bash "$ALG" "$BAG" "$RATE" "$EVERY"
    sleep 5
done
ls mapas_*/map_*.pgm | sed 's|/.*||' | sort | uniq -c
