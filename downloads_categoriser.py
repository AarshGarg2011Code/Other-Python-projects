import os
import shutil
import keyboard
import time
'''
Downloaded Files Categoriser code by Aarsh Garg.
Categorises files into 9 categories - images, videos, documents, archives, text, programming, executables and other.
Except for other extensions, this code has a diversity of 81 extensions in total.
'''

TARGET_PATH = r'C:\Users\yourname\Downloads'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, "move_log.txt")

DIRECTORIES = {
    "IMAGES": [".jpeg", ".jpg", ".tiff", ".gif", ".bmp", ".png", ".bpg", "svg", ".heif", ".psd"],
    "VIDEOS": [".avi", ".flv", ".wmv", ".mov", ".mp4", ".webm", ".vob", ".mng", ".qt", ".mpg", ".mpeg", ".3gp"],
    "DOCUMENTS": [".oxps", ".epub", ".pages", ".docx", ".doc", ".fdf", ".ods", ".odt", ".pwn", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx"],
    "ARCHIVES": [".a", ".ar", ".cpio", ".iso", ".tar", ".gz", ".rz", ".7z", ".dmg", ".rar", ".xar", ".zip"],
    "AUDIO": [".aac", ".aa", ".aac", ".dvf", ".m4a", ".m4b", ".m4p", ".mp3", ".msv", "ogg", "oga", ".raw", ".vox", ".wav", ".wma"],
    "TEXT": [".txt", ".in", ".out", ".log"],
    "PROGRAMMING": [".py", ".cpp", ".c", ".h", ".java", ".js", ".html", ".css", ".sh", ".swift"],
    "EXECUTABLES": [".exe", ".msi", ".bin", ".app"]
}

def organize():
    print("\n[Action] Organizing folder...")
    extension_lookup = {ext: dest for dest, exts in DIRECTORIES.items() for ext in exts}
    this_script = os.path.basename(__file__)

    if not os.path.exists(TARGET_PATH):
        print(f"Error: Path {TARGET_PATH} not found.")
        return

    with open(LOG_FILE_PATH, "a", encoding="utf-8") as log:
        count = 0
        for filename in os.listdir(TARGET_PATH):
            file_path = os.path.join(TARGET_PATH, filename)
            if os.path.isdir(file_path) or filename == this_script or filename == "move_log.txt":
                continue

            ext = os.path.splitext(filename)[1].lower()
            category = extension_lookup.get(ext, "OTHER")
            target_folder = os.path.join(TARGET_PATH, category)
            
            os.makedirs(target_folder, exist_ok=True)
            dest_path = os.path.join(target_folder, filename)
            
            try:
                shutil.move(file_path, dest_path)
                log.write(f"{dest_path}|{file_path}\n")
                count += 1
            except Exception as e:
                print(f"Error moving {filename}: {e}")
        
        print(f"Done! Organized {count} files.")

def undo():
    print("\n[Action] Undoing last organization...")
    if not os.path.exists(LOG_FILE_PATH):
        print("No log file found. Nothing to undo.")
        return

    with open(LOG_FILE_PATH, "r", encoding="utf-8") as log:
        lines = log.readlines()

    if not lines:
        print("Log is empty.")
        return

    for line in reversed(lines):
        line = line.strip()
        if "|" not in line: continue
        current_path, original_path = line.split("|")
        
        if os.path.exists(current_path):
            try:
                shutil.move(current_path, original_path)
            except Exception as e:
                print(f"Error restoring {current_path}: {e}")

    os.remove(LOG_FILE_PATH)
    print("Done! Files restored and log cleared.")

print("Running Background Manager...")
print("Press CTRL+ALT+D to Organize")
print("Press CTRL+ALT+U to Undo")
print("Press ESC to stop the script")

keyboard.add_hotkey('ctrl+alt+d', organize)
keyboard.add_hotkey('ctrl+alt+u', undo)

keyboard.wait('esc')
