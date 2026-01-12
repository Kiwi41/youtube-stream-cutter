import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import shutil

# --- Paths ---
BASE_DIR = Path(__file__).parent.parent
BIN_DIR = BASE_DIR / "bin"

YTDLP = BIN_DIR / ("yt-dlp.exe" if sys.platform.startswith("win") else "yt-dlp")

# Utiliser ffmpeg système s'il est disponible, sinon utiliser le binaire local
FFMPEG_LOCATION = BIN_DIR if not shutil.which("ffmpeg") else None

# --- UI helpers ---
def log(msg):
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)

def set_progress(value):
    progress_var.set(value)
    root.update_idletasks()

# --- Download logic ---
def download():
    url = url_var.get().strip()
    start = start_var.get()
    end = end_var.get()
    res = res_var.get()
    audio_only = audio_var.get()
    out_dir = Path(output_var.get())

    if not url:
        messagebox.showwarning("Erreur", "URL manquante")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    format_selector = (
        "bestaudio/best"
        if audio_only else
        f"bestvideo[height<={res}][ext=mp4]+bestaudio[ext=m4a]/best"
    )

    cmd = [str(YTDLP)]
    
    # Ajouter --ffmpeg-location seulement si on utilise le binaire local
    if FFMPEG_LOCATION:
        cmd += ["--ffmpeg-location", str(FFMPEG_LOCATION)]
    
    cmd += [
        "--download-sections", f"*{start}-{end}",
        "-f", format_selector,
        "--newline",
        "-o", str(out_dir / "%(title)s.%(ext)s"),
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
            if "[download]" in line and "%" in line:
                try:
                    pct = float(line.split("%")[0].split()[-1])
                    set_progress(pct)
                except:
                    pass
            log(line.strip())

        process.wait()
        set_progress(100)
        log("✅ Terminé")

    except Exception as e:
        messagebox.showerror("Erreur", str(e))

def start_download():
    threading.Thread(target=download, daemon=True).start()

def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        output_var.set(folder)

# --- UI ---
root = tk.Tk()
root.title("YouTube Stream Cutter")
root.geometry("600x520")
root.configure(bg="#2b2b2b")

style = ttk.Style()
style.theme_use("clam")
style.configure(".", background="#2b2b2b", foreground="white")
style.configure("TEntry", fieldbackground="#3c3f41", foreground="white")
style.configure("TSpinbox", fieldbackground="#3c3f41", foreground="white", selectbackground="#4a90d9", selectforeground="white")
style.configure("TButton", background="#3c3f41")
style.configure("TLabel", background="#2b2b2b")

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

url_var = tk.StringVar()
start_var = tk.IntVar(value=0)
end_var = tk.IntVar(value=30)
res_var = tk.IntVar(value=720)
audio_var = tk.BooleanVar(value=False)
output_var = tk.StringVar(value=str(BASE_DIR))

progress_var = tk.DoubleVar()

ttk.Label(frame, text="URL YouTube").pack(anchor="w")
ttk.Entry(frame, textvariable=url_var).pack(fill="x", pady=5)

time_frame = ttk.Frame(frame)
time_frame.pack(fill="x", pady=5)

ttk.Label(time_frame, text="Début (s)").grid(row=0, column=0)
ttk.Spinbox(time_frame, from_=0, to=9999, textvariable=start_var, width=6).grid(row=0, column=1, padx=5)

ttk.Label(time_frame, text="Fin (s)").grid(row=0, column=2)
ttk.Spinbox(time_frame, from_=1, to=9999, textvariable=end_var, width=6).grid(row=0, column=3, padx=5)

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

out_frame = ttk.Frame(frame)
out_frame.pack(fill="x", pady=5)

ttk.Entry(out_frame, textvariable=output_var).pack(side="left", fill="x", expand=True)
ttk.Button(out_frame, text="📁", command=choose_folder).pack(side="right", padx=5)

ttk.Button(frame, text="⬇ Télécharger", command=start_download).pack(pady=10)

ttk.Progressbar(
    frame,
    variable=progress_var,
    maximum=100
).pack(fill="x")

log_box = tk.Text(frame, height=10, bg="#1e1e1e", fg="white")
log_box.pack(fill="both", expand=True, pady=5)

root.mainloop()
