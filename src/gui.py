import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import shutil
import os
import re
import json
from datetime import datetime

# Vérifier si rclone est disponible
RCLONE_AVAILABLE = shutil.which("rclone") is not None

# --- Paths ---
BASE_DIR = Path(__file__).parent.parent
BIN_DIR = BASE_DIR / "bin"
CONFIG_FILE = BASE_DIR / "config.json"
LOG_FILE = BASE_DIR / f"youtube_cutter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

YTDLP = BIN_DIR / ("yt-dlp.exe" if sys.platform.startswith("win") else "yt-dlp")

# Utiliser ffmpeg système s'il est disponible, sinon utiliser le binaire local
FFMPEG_LOCATION = BIN_DIR if not shutil.which("ffmpeg") else None

# Flag de pause
paused = False
download_running = False

# --- UI helpers ---
def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    
    # Afficher dans l'UI
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)
    
    # Écrire dans le fichier de log
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(full_msg + "\n")
            f.flush()
    except Exception as e:
        print(f"Erreur écriture log: {e}")

def set_progress(value):
    progress_var.set(value)
    root.update_idletasks()

# --- Configuration ---
def load_config():
    """Charge la dernière configuration utilisée"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        log(f"⚠️ Erreur lors du chargement de la config: {e}")
    return {}

def save_config():
    """Sauvegarde la configuration actuelle"""
    try:
        config = {
            'url': url_var.get(),
            'start': start_var.get(),
            'end': end_var.get(),
            'res': res_var.get(),
            'audio_only': audio_var.get(),
            'output': output_var.get(),
            'mode': mode_var.get(),
            'max_videos': max_videos_var.get(),
            'gdrive_enabled': gdrive_var.get(),
            'rclone_remote': rclone_remote_var.get(),
            'gdrive_folder': gdrive_folder_var.get(),
            'delete_local': gdrive_delete_local_var.get(),
            'skip_check': skip_check_var.get()
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        log(f"⚠️ Erreur lors de la sauvegarde de la config: {e}")

# --- Rclone pour Google Drive ---
def get_rclone_remotes():
    """Liste les remotes rclone configurés"""
    try:
        result = subprocess.run(
            ["rclone", "listremotes"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return [r.strip().rstrip(':') for r in result.stdout.strip().split('\n') if r]
        return []
    except:
        return []

def check_rclone_file_exists(remote, remote_path, filename):
    """Vérifie si un fichier existe déjà sur le remote"""
    try:
        full_path = f"{remote}:{remote_path}/" if remote_path else f"{remote}:"
        result = subprocess.run(
            ["rclone", "lsf", full_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            files_list = result.stdout.strip().split('\n')
            return filename in files_list
        return False
    except:
        return False

def get_video_filenames(url, format_selector, max_videos=0):
    """Récupère les noms de fichiers qui seraient téléchargés sans les télécharger"""
    try:
        log("   Récupération de la liste des vidéos...")
        cmd = [str(YTDLP)]
        
        if FFMPEG_LOCATION:
            cmd += ["--ffmpeg-location", str(FFMPEG_LOCATION)]
        
        cmd += [
            "-f", format_selector,
            "--print", "%(playlist_index)03d - %(title)s.%(ext)s",
            "--no-download",
            "--quiet",
        ]
        
        if max_videos > 0:
            cmd += ["--playlist-end", str(max_videos)]
        
        cmd.append(url)
        
        log(f"   Commande: {' '.join(cmd[:5])}...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180  # Timeout de 180 secondes (3 minutes)
        )
        
        if result.returncode == 0:
            filenames = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            log(f"   ✅ {len(filenames)} fichier(s) détecté(s)")
            return filenames
        else:
            log(f"   ⚠️ Erreur lors de la récupération (code {result.returncode})")
            log(f"   {result.stderr[:200]}")
            return []
    except subprocess.TimeoutExpired:
        log("   ⚠️ Timeout - la récupération a pris trop de temps")
        return []
    except Exception as e:
        log(f"❌ Erreur lors de la récupération des noms: {e}")
        return []

def upload_to_rclone(file_path, remote, remote_path):
    """Upload un fichier vers un remote rclone"""
    try:
        file_name = Path(file_path).name
        
        # Vérifier si le fichier existe déjà
        if check_rclone_file_exists(remote, remote_path, file_name):
            log(f"⏭️ Fichier déjà présent, skip: {file_name}")
            return True
        
        log(f"☁️ Upload vers {remote}: {file_name}")
        log(f"   Taille: {Path(file_path).stat().st_size / (1024*1024):.2f} MB")
        
        # Construire le chemin de destination
        dest_path = f"{remote}:{remote_path}" if remote_path else f"{remote}:"
        
        # Upload avec rclone
        process = subprocess.run(
            ["rclone", "copy", str(file_path), dest_path, "-P"],
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            log(f"✅ Upload terminé: {file_name}")
            return True
        else:
            log(f"❌ Échec de l'upload: {file_name}")
            log(f"   Erreur: {process.stderr}")
            return False
            
    except Exception as e:
        log(f"❌ Erreur d'upload: {e}")
        return False

# --- Download logic ---
def download():
    global download_running, paused
    download_running = True
    paused = False
    
    # Activer le bouton pause, désactiver le bouton télécharger
    pause_btn.configure(state="normal")
    download_btn.configure(state="disabled")
    
    url = url_var.get().strip()
    start = start_var.get()
    end = end_var.get()
    res = res_var.get()
    audio_only = audio_var.get()
    out_dir = Path(output_var.get())
    mode = mode_var.get()
    max_videos = max_videos_var.get()

    if not url:
        messagebox.showwarning("Erreur", "URL manquante")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    format_selector = (
        "bestaudio/best"
        if audio_only else
        f"bestvideo[height<={res}][ext=mp4]+bestaudio[ext=m4a]/best"
    )
    
    # Vérifier les fichiers existants sur le Drive avant de télécharger (par batch)
    files_to_skip = []
    # Skip automatique pour les chaînes complètes (trop de vidéos = timeout)
    should_skip = skip_check_var.get() or (mode == "channel" and max_videos == 0)
    
    if gdrive_var.get() and RCLONE_AVAILABLE and not should_skip:
        remote = rclone_remote_var.get().strip()
        remote_path = gdrive_folder_var.get().strip()
        
        if remote:
            log("🔍 Vérification des fichiers existants sur le Drive (par batch de 10)...")
            
            # Construire l'URL pour la vérification
            check_url = url
            if mode == "channel" and "@" in url and "/videos" not in url:
                check_url = url.rstrip("/") + "/videos"
            
            # Récupérer les noms de fichiers qui seraient téléchargés
            log("   Récupération rapide de la liste...")
            potential_files = get_video_filenames(check_url, format_selector, max_videos)
            
            if not potential_files:
                log("⚠️ Impossible de récupérer la liste des fichiers, téléchargement normal")
            elif potential_files:
                log(f"📋 {len(potential_files)} vidéo(s) à vérifier")
                
                # Vérifier par batch de 10
                batch_size = 10
                for i in range(0, len(potential_files), batch_size):
                    batch = potential_files[i:i + batch_size]
                    log(f"   Vérification batch {i//batch_size + 1}/{(len(potential_files) + batch_size - 1)//batch_size}")
                    
                    for filename in batch:
                        if check_rclone_file_exists(remote, remote_path, filename):
                            files_to_skip.append(filename)
                            log(f"      ⏭️ Déjà sur Drive: {filename}")
                
                if files_to_skip:
                    log(f"\n✅ {len(files_to_skip)} fichier(s) déjà présent(s), {len(potential_files) - len(files_to_skip)} à télécharger")
                    
                    # Si tous les fichiers existent déjà, arrêter
                    if len(files_to_skip) == len(potential_files):
                        log("\n🎉 Tous les fichiers existent déjà sur le Drive !")
                        return
                else:
                    log("✅ Aucun fichier existant, téléchargement complet")

    cmd = [str(YTDLP)]
    
    # Ajouter --ffmpeg-location seulement si on utilise le binaire local
    if FFMPEG_LOCATION:
        cmd += ["--ffmpeg-location", str(FFMPEG_LOCATION)]
    
    # Découpage temporel (appliqué à chaque vidéo)
    cmd += [
        "--download-sections", f"*{start}-{end}",
    ]
    
    # Mode playlist ou chaîne
    if mode != "video":
        # Limiter le nombre de vidéos si spécifié
        if max_videos > 0:
            cmd += ["--playlist-end", str(max_videos)]
        
        # Pour les chaînes, ajouter /videos pour avoir toutes les vidéos
        if mode == "channel" and "@" in url and "/videos" not in url:
            url = url.rstrip("/") + "/videos"
    
    cmd += [
        "-f", format_selector,
        "--newline",
        "-o", str(out_dir / "%(playlist_index)03d - %(title)s.%(ext)s"),
        url
    ]

    if audio_only:
        cmd += ["-x", "--audio-format", "mp3"]

    try:
        log("▶ Démarrage...")
        set_progress(0)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            # Vérifier si on doit mettre en pause
            if paused:
                log("⏸️ Pause demandée, arrêt du processus...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                log("⏸️ Téléchargement mis en pause")
                download_running = False
                pause_btn.configure(state="disabled")
                download_btn.configure(state="normal")
                return
            
            if "[download]" in line and "%" in line:
                try:
                    pct = float(line.split("%")[0].split()[-1])
                    set_progress(pct)
                except:
                    pass
            log(line.strip())

        process.wait()
        set_progress(100)
        log("✅ Téléchargement terminé")
        
        # Upload vers rclone si activé (par batch de 10 vidéos)
        if gdrive_var.get() and RCLONE_AVAILABLE:
            remote = rclone_remote_var.get().strip()
            remote_path = gdrive_folder_var.get().strip()
            
            if not remote:
                log("❌ Aucun remote rclone sélectionné")
            else:
                log(f"\n📤 Début de l'upload vers {remote}...")
                
                # Rechercher tous les fichiers téléchargés
                all_files = [f for f in out_dir.iterdir() 
                            if f.is_file() and f.suffix in ['.mp4', '.mp3', '.webm', '.mkv']]
                
                if not all_files:
                    log("❌ Aucun fichier à uploader")
                else:
                    uploaded_files = []
                    batch_size = 10
                    
                    # Uploader par batch de 10
                    for i in range(0, len(all_files), batch_size):
                        batch = all_files[i:i + batch_size]
                        log(f"\n📦 Batch {i//batch_size + 1}/{(len(all_files) + batch_size - 1)//batch_size} ({len(batch)} fichiers)")
                        
                        for file in batch:
                            if upload_to_rclone(file, remote, remote_path):
                                uploaded_files.append(file)
                        
                        # Supprimer les fichiers du batch si l'option est activée
                        if gdrive_delete_local_var.get() and uploaded_files:
                            log(f"🗑️ Suppression des fichiers du batch...")
                            for file in uploaded_files:
                                try:
                                    file.unlink()
                                    log(f"✅ Supprimé: {file.name}")
                                except Exception as e:
                                    log(f"❌ Erreur de suppression {file.name}: {e}")
                            uploaded_files = []  # Reset pour le prochain batch
        
        log("\n🎉 Traitement terminé")
        
        # Sauvegarder la configuration
        save_config()

    except Exception as e:
        messagebox.showerror("Erreur", str(e))
    finally:
        download_running = False
        pause_btn.configure(state="disabled")
        download_btn.configure(state="normal")

def start_download():
    threading.Thread(target=download, daemon=True).start()

def toggle_pause():
    global paused
    if not download_running:
        return
    
    paused = not paused
    if paused:
        pause_btn.configure(text="⏸️ En pause...")
        log("⏸️ Pause demandée (s'arrêtera entre deux vidéos)...")
    else:
        pause_btn.configure(text="⏸️ Pause")
        log("▶ Reprise du téléchargement...")

def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        output_var.set(folder)

def toggle_time_controls():
    """Active/désactive les contrôles selon le mode"""
    if mode_var.get() == "video":
        max_videos_spin.configure(state="disabled")
    else:
        max_videos_spin.configure(state="normal")

# --- UI ---
root = tk.Tk()
root.title("YouTube Stream Cutter")
root.geometry("600x600")
root.configure(bg="#2b2b2b")

# Écrire l'en-tête du log
try:
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"=== YouTube Stream Cutter Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        f.write(f"Log file: {LOG_FILE}\n")
        f.write(f"Rclone available: {RCLONE_AVAILABLE}\n")
        f.write("=" * 80 + "\n\n")
except:
    pass

style = ttk.Style()
style.theme_use("clam")
style.configure(".", background="#2b2b2b", foreground="white")
style.configure("TEntry", fieldbackground="#3c3f41", foreground="white")
style.configure("TSpinbox", fieldbackground="#3c3f41", foreground="white", selectbackground="#4a90d9", selectforeground="white")
style.configure("TButton", background="#3c3f41")
style.configure("TLabel", background="#2b2b2b")

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

# Charger la configuration sauvegardée
saved_config = load_config()

url_var = tk.StringVar(value=saved_config.get('url', ''))
start_var = tk.IntVar(value=saved_config.get('start', 0))
end_var = tk.IntVar(value=saved_config.get('end', 30))
res_var = tk.IntVar(value=saved_config.get('res', 720))
audio_var = tk.BooleanVar(value=saved_config.get('audio_only', False))
output_var = tk.StringVar(value=saved_config.get('output', str(BASE_DIR)))
mode_var = tk.StringVar(value=saved_config.get('mode', 'video'))
max_videos_var = tk.IntVar(value=saved_config.get('max_videos', 0))
gdrive_var = tk.BooleanVar(value=saved_config.get('gdrive_enabled', False))
rclone_remote_var = tk.StringVar(value=saved_config.get('rclone_remote', ''))
gdrive_folder_var = tk.StringVar(value=saved_config.get('gdrive_folder', ''))
gdrive_delete_local_var = tk.BooleanVar(value=saved_config.get('delete_local', False))
skip_check_var = tk.BooleanVar(value=saved_config.get('skip_check', False))

progress_var = tk.DoubleVar()

# Mode de téléchargement
mode_frame = ttk.Frame(frame)
mode_frame.pack(fill="x", pady=5)

ttk.Label(mode_frame, text="Mode:").pack(side="left", padx=(0, 10))
ttk.Radiobutton(
    mode_frame,
    text="Vidéo unique",
    variable=mode_var,
    value="video",
    command=toggle_time_controls
).pack(side="left", padx=5)
ttk.Radiobutton(
    mode_frame,
    text="Playlist",
    variable=mode_var,
    value="playlist",
    command=toggle_time_controls
).pack(side="left", padx=5)
ttk.Radiobutton(
    mode_frame,
    text="Chaîne",
    variable=mode_var,
    value="channel",
    command=toggle_time_controls
).pack(side="left", padx=5)

ttk.Label(frame, text="URL YouTube").pack(anchor="w")
ttk.Entry(frame, textvariable=url_var).pack(fill="x", pady=5)

time_frame = ttk.Frame(frame)
time_frame.pack(fill="x", pady=5)

ttk.Label(time_frame, text="Début (s)").grid(row=0, column=0)
ttk.Spinbox(time_frame, from_=0, to=9999, textvariable=start_var, width=6).grid(row=0, column=1, padx=5)

ttk.Label(time_frame, text="Fin (s)").grid(row=0, column=2)
ttk.Spinbox(time_frame, from_=1, to=9999, textvariable=end_var, width=6).grid(row=0, column=3, padx=5)

ttk.Label(time_frame, text="Max vidéos (0=toutes)").grid(row=0, column=4, padx=(20, 0))
max_videos_spin = ttk.Spinbox(time_frame, from_=0, to=999, textvariable=max_videos_var, width=6, state="disabled")
max_videos_spin.grid(row=0, column=5, padx=5)

opt_frame = ttk.Frame(frame)
opt_frame.pack(fill="x", pady=5)

ttk.Label(opt_frame, text="Résolution max").grid(row=0, column=0)
ttk.Combobox(
    opt_frame,
    values=[360, 480, 720, 1080],
    textvariable=res_var,
    state="readonly",
    width=8
).grid(row=0, column=1, padx=5)

ttk.Checkbutton(
    opt_frame,
    text="Audio seulement (MP3)",
    variable=audio_var
).grid(row=0, column=2, padx=10)

if RCLONE_AVAILABLE:
    ttk.Checkbutton(
        opt_frame,
        text="Upload vers cloud (rclone)",
        variable=gdrive_var
    ).grid(row=0, column=3, padx=10)
    
    ttk.Checkbutton(
        opt_frame,
        text="Supprimer local après upload",
        variable=gdrive_delete_local_var
    ).grid(row=1, column=0, padx=10, pady=5)
    
    ttk.Checkbutton(
        opt_frame,
        text="Skip vérification Drive",
        variable=skip_check_var
    ).grid(row=1, column=1, padx=10, pady=5)

# Remote rclone et chemin
if RCLONE_AVAILABLE:
    rclone_frame = ttk.Frame(frame)
    rclone_frame.pack(fill="x", pady=5)
    
    ttk.Label(rclone_frame, text="Remote rclone:").pack(side="left", padx=(0, 5))
    
    # Liste des remotes disponibles
    remotes = get_rclone_remotes()
    if remotes:
        rclone_remote_combo = ttk.Combobox(
            rclone_frame,
            textvariable=rclone_remote_var,
            values=remotes,
            state="readonly",
            width=20
        )
        rclone_remote_combo.pack(side="left", padx=5)
        # Initialiser avec la valeur sauvegardée ou le premier remote
        if not rclone_remote_var.get() and remotes:
            rclone_remote_var.set(remotes[0])
    else:
        ttk.Label(rclone_frame, text="Aucun remote - Exécutez 'rclone config' d'abord", foreground="orange").pack(side="left")
    
    ttk.Label(rclone_frame, text="Chemin (ex: Videos/YouTube):").pack(side="left", padx=(20, 5))
    ttk.Entry(rclone_frame, textvariable=gdrive_folder_var, width=30).pack(side="left", fill="x", expand=True)

out_frame = ttk.Frame(frame)
out_frame.pack(fill="x", pady=5)

ttk.Entry(out_frame, textvariable=output_var).pack(side="left", fill="x", expand=True)
ttk.Button(out_frame, text="Parcourir", command=choose_folder).pack(side="right", padx=5)

# Frame pour les boutons de contrôle
btn_frame = ttk.Frame(frame)
btn_frame.pack(pady=10)

download_btn = ttk.Button(btn_frame, text="Télécharger", command=start_download)
download_btn.pack(side="left", padx=5)

pause_btn = ttk.Button(btn_frame, text="⏸️ Pause", command=toggle_pause, state="disabled")
pause_btn.pack(side="left", padx=5)

ttk.Progressbar(
    frame,
    variable=progress_var,
    maximum=100
).pack(fill="x")

log_box = tk.Text(frame, height=10, bg="#1e1e1e", fg="white")
log_box.pack(fill="both", expand=True, pady=5)

root.mainloop()
