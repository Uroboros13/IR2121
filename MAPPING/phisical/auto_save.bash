#!/bin/bash
INTERVALO="${1:-45}"
MODO="$2"
SAVE="$(cd "$(dirname "$0")" && pwd)/save.bash"
if ! [[ "$INTERVALO" =~ ^[1-9][0-9]*$ ]] || { [ -n "$MODO" ] && [ "$MODO" != "new_save" ]; }; then
    echo "Uso: $0 [segundos] [new_save]"
    exit 1
fi
terminar() {
    trap - INT TERM
    echo "Guardando el ultimo mapa antes de salir"
    "$SAVE"
    exit 0
}
trap terminar INT TERM
echo "Guardando un mapa cada $INTERVALO s. Ctrl+C para terminar"
"$SAVE" $MODO || echo "AVISO: no se pudo guardar; se reintenta en $INTERVALO s"
while true; do
    sleep "$INTERVALO"
    "$SAVE" || echo "AVISO: no se pudo guardar; se reintenta en $INTERVALO s"
done
