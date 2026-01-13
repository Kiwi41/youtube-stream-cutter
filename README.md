# YouTube Stream Cutter

Application de découpage et téléchargement de vidéos YouTube avec interface graphique et upload vers le cloud.

## Fonctionnalités

### Téléchargement
- **Téléchargement de segments spécifiques** de vidéos YouTube (début/fin en secondes)
- **Choix de la résolution** (360p, 480p, 720p, 1080p)
- **Extraction audio en MP3** uniquement
- **3 modes de téléchargement** :
  - Vidéo unique
  - Playlist complète
  - Chaîne YouTube (tous les vidéos)
- **Limitation du nombre de vidéos** pour les playlists et chaînes
- **Bouton Pause** pour arrêter/reprendre le téléchargement entre deux vidéos

### Upload Cloud (rclone)
- **Upload automatique vers Google Drive** (ou tout remote rclone)
- **Upload par batch de 10 vidéos** pour optimiser les performances
- **Détection des doublons** : skip automatique des fichiers déjà présents
- **Vérification pré-téléchargement** : évite de télécharger des vidéos déjà sur le cloud
- **Option "Skip vérification"** pour les grandes chaînes (évite les timeouts)
- **Suppression locale optionnelle** après upload pour économiser l'espace

### Interface
- **Interface graphique simple et intuitive**
- **Barre de progression en temps réel**
- **Logs détaillés** avec horodatage
- **Fichiers de log** automatiques pour débogage
- **Sauvegarde de la configuration** entre les sessions

## Installation

### Prérequis

- Python 3.12+
- ffmpeg (peut être fourni dans le dossier `bin/` ou installé système)
- rclone (optionnel, pour l'upload cloud)

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/Kiwi41/youtube-stream-cutter.git
cd youtube-stream-cutter

# Créer un environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install yt-dlp
```

### Configuration rclone (optionnel)

Pour utiliser l'upload vers Google Drive :

```bash
# Installer rclone
# Linux
sudo apt install rclone
# Mac
brew install rclone

# Configurer un remote
rclone config
# Suivre les instructions pour créer un remote "gdrive" ou autre nom
```

## Utilisation

```bash
python src/gui.py
```

### Interface

#### Paramètres de base
1. **Mode** : Vidéo unique / Playlist / Chaîne
2. **URL YouTube** : Coller l'URL de la vidéo, playlist ou chaîne
3. **Début (s)** : Temps de début en secondes
4. **Fin (s)** : Temps de fin en secondes
5. **Limite vidéos** : Nombre max de vidéos à télécharger (0 = toutes)
6. **Résolution max** : Choisir la qualité vidéo (360p à 1080p)
7. **Audio seulement** : Extraire uniquement l'audio en MP3

#### Paramètres Cloud (si rclone disponible)
8. **Upload vers cloud** : Activer l'upload automatique
9. **Supprimer local après upload** : Libérer l'espace disque
10. **Skip vérification Drive** : Désactiver la vérification pré-téléchargement (utile pour les grandes chaînes)
11. **Remote rclone** : Choisir le remote configuré
12. **Chemin** : Dossier de destination (ex: `JDR/AnimatedBattleMaps`)

#### Contrôles
- **Bouton Télécharger** : Lancer le téléchargement
- **Bouton Pause** : Mettre en pause (s'arrête proprement entre deux vidéos)
- **Dossier de sortie** : Choisir où sauvegarder les fichiers

### Exemples d'utilisation

#### Télécharger une vidéo unique (extrait 30s)
- Mode: Vidéo unique
- URL: `https://www.youtube.com/watch?v=...`
- Début: 10, Fin: 40

#### Télécharger les 50 premières vidéos d'une chaîne vers Google Drive
- Mode: Chaîne
- URL: `https://www.youtube.com/@NomDeLaChaine`
- Limite vidéos: 50
- Upload vers cloud: ✓
- Skip vérification Drive: ✓ (recommandé pour éviter les timeouts)

#### Télécharger une playlist complète en audio MP3
- Mode: Playlist
- URL: `https://www.youtube.com/playlist?list=...`
- Limite vidéos: 0 (toutes)
- Audio seulement: ✓

## Structure du projet

```
youtube-stream-cutter/
├── bin/                  # Binaires (ffmpeg, ffprobe, yt-dlp)
├── src/
│   └── gui.py           # Interface graphique
├── config.json          # Configuration sauvegardée (auto-généré)
├── youtube_cutter_*.log # Fichiers de log (auto-générés)
├── build_youtube_cutter_usb.sh
└── README.md
```

## Conseils d'utilisation

### Pour les grandes chaînes
- Cocher **"Skip vérification Drive"** pour éviter les timeouts
- Utiliser **"Limite vidéos"** pour télécharger par lots
- Activer **"Supprimer local après upload"** pour économiser l'espace

### Reprise après pause
- Les fichiers déjà téléchargés sont détectés automatiquement
- Relancer le téléchargement avec la même configuration
- Les doublons sont skippés (localement et sur le cloud)

### Logs
- Tous les téléchargements génèrent un fichier `.log` avec horodatage
- Utile pour déboguer ou suivre l'historique des téléchargements

## Licence

MIT
