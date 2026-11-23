#!/bin/bash
set -e
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
SDK=/usr/lib/android-sdk/platforms/android-23/android.jar
B="$DIR/build"
rm -rf "$B"
mkdir -p "$B/gen" "$B/obj" "$B/apk"
aapt package -f -m -J "$B/gen" -M "$DIR/AndroidManifest.xml" -S "$DIR/res" -I "$SDK"
javac -nowarn -source 8 -target 8 -bootclasspath "$SDK" -classpath "$SDK" -d "$B/obj" $(find "$DIR/src" "$B/gen" -name "*.java")
dalvik-exchange --dex --min-sdk-version=21 --output="$B/apk/classes.dex" "$B/obj"
aapt package -f -0 arsc -M "$DIR/AndroidManifest.xml" -S "$DIR/res" -A "$DIR/assets" -I "$SDK" -F "$B/unsigned.apk"
(cd "$B/apk" && aapt add "$B/unsigned.apk" classes.dex)
zipalign -f 4 "$B/unsigned.apk" "$B/aligned.apk"
if [ ! -f "$DIR/tb3mando.keystore" ]; then
    keytool -genkeypair -keystore "$DIR/tb3mando.keystore" -storepass ir2121 -keypass ir2121 -alias tb3mando -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Mando TB3, O=IR2121"
fi
apksigner sign --ks "$DIR/tb3mando.keystore" --ks-pass pass:ir2121 --key-pass pass:ir2121 --ks-key-alias tb3mando --out "$DIR/MandoTB3.apk" "$B/aligned.apk"
apksigner verify --print-certs "$DIR/MandoTB3.apk" | head -2
echo "APK: $DIR/MandoTB3.apk"
