#!/bin/bash
set -e

# ------------------------
# CONFIG
# ------------------------
BASE_DIR="YouTube_Stream_Cutter_USB"
SRC_DIR="src"
DIST_DIR="dist"

WINDOWS_BIN="$BASE_DIR/windows/bin"
LINUX_BIN="$BASE_DIR/linux/bin"

GUI_FILE="$SRC_DIR/gui.py"

# Vérification gui.py
if [ ! -f "$GUI_FILE" ]; then
    echo "❌ ERREUR : $GUI_FILE introuvable. Place ton gui.py ici."
    exit 1
fi

# ------------------------
# CRÉATION DES DOSSIERS
# ------------------------
echo "📁 Création des dossiers..."
mkdir -p $WINDOWS_BIN $LINUX_BIN $DIST_DIR

# ------------------------
# TÉLÉCHARGEMENT BINAIRES WINDOWS
# ------------------------
if [ ! -f "$WINDOWS_BIN/yt-dlp.exe" ] || [ ! -s "$WINDOWS_BIN/yt-dlp.exe" ]; then
    echo "🪟 Téléchargement yt-dlp Windows..."
    curl -L -o $WINDOWS_BIN/yt-dlp.exe \
        https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe
else
    echo "✅ yt-dlp Windows déjà présent"
fi

if [ ! -f "$WINDOWS_BIN/ffmpeg.exe" ] || [ ! -s "$WINDOWS_BIN/ffmpeg.exe" ]; then
    echo "🪟 Téléchargement ffmpeg Windows..."
    curl -L -o ffmpeg_win.zip https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
    unzip -q ffmpeg_win.zip
    FFMPEG_DIR=$(find . -type d -name "ffmpeg-*-essentials_build" | head -n 1)
    cp $FFMPEG_DIR/bin/ffmpeg.exe $WINDOWS_BIN/
    cp $FFMPEG_DIR/bin/ffprobe.exe $WINDOWS_BIN/
    rm -rf ffmpeg_win.zip $FFMPEG_DIR
else
    echo "✅ ffmpeg Windows déjà présent"
fi

# ------------------------
# TÉLÉCHARGEMENT BINAIRES LINUX
# ------------------------
if [ ! -f "$LINUX_BIN/yt-dlp" ] || [ ! -s "$LINUX_BIN/yt-dlp" ]; then
    echo "🐧 Téléchargement yt-dlp Linux..."
    curl -L -o $LINUX_BIN/yt-dlp \
        https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp
    chmod +x $LINUX_BIN/yt-dlp
else
    echo "✅ yt-dlp Linux déjà présent"
fi

if [ ! -f "$LINUX_BIN/ffmpeg" ] || [ ! -s "$LINUX_BIN/ffmpeg" ]; then
    echo "🐧 Téléchargement ffmpeg Linux..."
    curl -L -o ffmpeg_linux.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    tar -xf ffmpeg_linux.tar.xz
    FFMPEG_LINUX_DIR=$(find . -type d -name "ffmpeg-*-amd64-static" | head -n 1)
    cp $FFMPEG_LINUX_DIR/ffmpeg $LINUX_BIN/
    cp $FFMPEG_LINUX_DIR/ffprobe $LINUX_BIN/
    chmod +x $LINUX_BIN/ffmpeg
    chmod +x $LINUX_BIN/ffprobe
    rm -rf ffmpeg_linux.tar.xz $FFMPEG_LINUX_DIR
else
    echo "✅ ffmpeg Linux déjà présent"
fi

# ------------------------
# CONFIG PAR DÉFAUT
# ------------------------
echo "⚙️ Création des config.json..."
mkdir -p $BASE_DIR/windows $BASE_DIR/linux
cat > $BASE_DIR/windows/config.json <<EOF
{
  "resolution": 720,
  "audio_only": false,
  "output_dir": ".",
  "start": 0,
  "end": 30
}
EOF
cp $BASE_DIR/windows/config.json $BASE_DIR/linux/config.json

# ------------------------
# README
# ------------------------
echo "📄 Création du README..."
cat > $BASE_DIR/README.txt <<EOF
YouTube Stream Cutter – Version portable USB

1) Ouvrez le dossier correspondant à votre OS
2) Lancez l'application
3) Collez l'URL YouTube
4) Choisissez durée et résolution
5) Télécharger

Aucune installation requise. Usage légal uniquement.
EOF

# ------------------------
# COPY GUI
# ------------------------
echo "📋 Copie gui.py..."
mkdir -p $BASE_DIR/src
cp $GUI_FILE $BASE_DIR/src/

# ------------------------
# BUILD WINDOWS
# ------------------------
echo "🪟 Préparation Windows (build .exe ignoré depuis Linux)..."
echo "⚠️  Pour builder l'exe Windows, exécute ce script depuis Windows"
# Copie du script Python brut pour Windows
cp $BASE_DIR/src/gui.py $BASE_DIR/windows/

# ------------------------
# BUILD LINUX
# ------------------------
echo "🐧 Build Linux..."
/home/a154355/git/perso/yt/.venv/bin/python -m PyInstaller \
  --onefile \
  --add-binary "$LINUX_BIN:bin" \
  $BASE_DIR/src/gui.py
cp dist/gui $BASE_DIR/linux/YouTubeCutter
chmod +x $BASE_DIR/linux/YouTubeCutter
rm -rf build dist __pycache__ gui.spec

# ------------------------
# ZIP FINAL
# ------------------------
echo "📦 Création du ZIP final..."
mkdir -p $DIST_DIR
cd $(dirname $BASE_DIR)
zip -r $DIST_DIR/YouTube_Stream_Cutter_USB.zip $(basename $BASE_DIR)

echo "✅ Build terminé !"
echo "ZIP final disponible dans $DIST_DIR/YouTube_Stream_Cutter_USB.zip"
