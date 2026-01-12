# YouTube Stream Cutter

Application de découpage et téléchargement de vidéos YouTube avec interface graphique.

## Fonctionnalités

- Téléchargement de segments spécifiques de vidéos YouTube
- Choix de la résolution (360p à 1080p)
- Extraction audio en MP3
- Interface graphique simple et intuitive
- Barre de progression en temps réel

## Installation

### Prérequis

- Python 3.12+
- ffmpeg (peut être fourni dans le dossier `bin/` ou installé système)

### Installation

```bash
# Cloner le dépôt
git clone <votre-repo-url>
cd yt

# Créer un environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install yt-dlp
```

## Utilisation

```bash
python src/gui.py
```

### Interface

1. **URL YouTube** : Coller l'URL de la vidéo
2. **Début (s)** : Temps de début en secondes
3. **Fin (s)** : Temps de fin en secondes
4. **Résolution max** : Choisir la qualité vidéo
5. **Audio seulement** : Extraire uniquement l'audio en MP3
6. **Dossier de sortie** : Choisir où sauvegarder le fichier

## Structure du projet

```
yt/
├── bin/                  # Binaires (ffmpeg, ffprobe, yt-dlp)
├── src/
│   └── gui.py           # Interface graphique
├── build_youtube_cutter_usb.sh  # Script de build
└── README.md
```

## Licence

MIT
