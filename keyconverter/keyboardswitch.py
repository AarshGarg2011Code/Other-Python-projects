"""
- Requires: pip install keyboard pystray pillow
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import keyboard
import time
import sys
import random
import urllib.parse
import base64
from PIL import Image, ImageOps, ImageEnhance
import pystray

MORSE = {
    'A': '.- ', 'B': '-... ', 'C': '-.-. ', 'D': '-.. ', 'E': '. ',
    'F': '..-. ', 'G': '--. ', 'H': '.... ', 'I': '.. ', 'J': '.--- ',
    'K': '-.- ', 'L': '.-.. ', 'M': '-- ', 'N': '-. ', 'O': '--- ',
    'P': '.--. ', 'Q': '--.- ', 'R': '.-. ', 'S': '... ', 'T': '- ',
    'U': '..- ', 'V': '...- ', 'W': '.-- ', 'X': '-..- ', 'Y': '-.-- ',
    'Z': '--.. ', '0': '----- ', '1': '.---- ', '2': '..--- ', '3': '...-- ',
    '4': '....- ', '5': '..... ', '6': '-.... ', '7': '--... ', '8': '---.. ', '9': '----. '
}

NATO = {
    'A': 'Alpha','B':'Bravo','C':'Charlie','D':'Delta','E':'Echo','F':'Foxtrot','G':'Golf',
    'H':'Hotel','I':'India','J':'Juliett','K':'Kilo','L':'Lima','M':'Mike','N':'November',
    'O':'Oscar','P':'Papa','Q':'Quebec','R':'Romeo','S':'Sierra','T':'Tango','U':'Uniform',
    'V':'Victor','W':'Whiskey','X':'X-ray','Y':'Yankee','Z':'Zulu'
}

BRAILLE = {
    'a':'⠁','b':'⠃','c':'⠉','d':'⠙','e':'⠑','f':'⠋','g':'⠛','h':'⠓','i':'⠊','j':'⠚',
    'k':'⠅','l':'⠇','m':'⠍','n':'⠝','o':'⠕','p':'⠏','q':'⠟','r':'⠗','s':'⠎','t':'⠞',
    'u':'⠥','v':'⠧','w':'⠺','x':'⠭','y':'⠽','z':'⠵','0':'⠴','1':'⠂'
}

ZALGO_CHARS = [
    '͏', '͐', '͑', '͒', '͓', '͔', '͕', '͖', '͙', '͚', '͛', '͜', '͝', '͟',
    '͠', '͢', '͡', '̚', '̕', '̛', '̛', '̛', '̛', '̛', '̛', '̛', '̛', '̛',
    '̐', '̇', '̈', '̉', '̊', '̋', '̌', '̍', '̎', '̏', '̒', '̓', '̑', '̛',
    '̛', '̛', '̛', '̛', '̛', '̛', '̛', '̛', '̛', '̛', '̛', '̛', '̛', '̛',
    '̯', '̺', '̻', '̼', '̹', '̝', '̞', '̟', '̠', '̤', '̥', '̦', '̧', '̨',
    '̩', '̪', '̫', '̬', '̭', '̮', '̰', '̱', '̀', '́', '͂', '̓', '̈́', 'ͅ',
    '͆', '͇', '͈', '͉', '͊', '͋', '͌', '͍', '͐', '͑', '͒', '͓', '͔', '͕',
    '͖', '͙', '͚', '͛', '͜', '͝', '͟', '͠', '͢', '͡', '̚', '̕', '̛', '̛',
]

class EncodingKeyboardApp:
    def __init__(self, logo_path="logo.png"):
        self.logo_path = logo_path
        self.root = tk.Tk()
        self.root.title("Encoding Keyboard")
        self.root.geometry("800x800")
        self.root.configure(bg="#00008b")
        self.root.resizable(False, False)

        style = ttk.Style(self.root)
        style.theme_use("clam")

        self.encoding_mode = None
        self.running_hook = False
        self.injecting = False
        self.tray_icon = None
        self.tray_thread = None
        self.buttons = {}
        self.hook_id = None

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _build_ui(self):
        title = tk.Label(self.root, text="🔣 Encoding Keyboard — 35 modes", font=("Segoe UI", 20, "bold"),
                         bg="#eaf2ff", fg="#1d4f94")
        title.pack(pady=18)

        subtitle = tk.Label(self.root, text="Click an encoding to activate (tray shows only while active).",
                             font=("Segoe UI", 10), bg="#eaf2ff", fg="#2f5d9a")
        subtitle.pack(pady=6)

        grid_frame = tk.Frame(self.root, bg="#eaf2ff")
        grid_frame.pack(expand=True, padx=18, pady=10, fill="both")

        encodings = [
            "ascii","binary","binary16","octal","decimal","hex","unicode","unicodehex",
            "utf8","utf16","utf32","base32","base64","rot13","caesar3","atbash",
            "reverse","leet","morse","url","html","roman","bcd","binarymirror","piglatin",
            "emoji","nato","braille","hexmirror","revmorse","zalgo","base85",
            "binhexcombo","hexbincombo","encrypted"
        ]
        rows, cols = 7, 5
        for i, enc in enumerate(encodings):
            r, c = divmod(i, cols)
            btn = tk.Button(grid_frame, text=enc.upper(), font=("Segoe UI", 10, "bold"),
                             bg="#d9e8ff", fg="#0d3a78", relief="raised",
                             command=lambda e=enc: self._on_encoding_click(e))
            btn.grid(row=r, column=c, padx=8, pady=8, ipadx=6, ipady=10, sticky="nsew")
            self.buttons[enc] = btn

        for r in range(rows):
            grid_frame.rowconfigure(r, weight=1)
        for c in range(cols):
            grid_frame.columnconfigure(c, weight=1)

        bottom = tk.Frame(self.root, bg="#eaf2ff")
        bottom.pack(fill="x", pady=12)

        self.status_label = tk.Label(bottom, text="Mode: OFF", bg="#eaf2ff", fg="#1d4f94",
                                     font=("Segoe UI", 12, "italic"))
        self.status_label.pack(side="left", padx=18)

        stop_button = tk.Button(bottom, text="🛑 Stop Encoding", font=("Segoe UI", 11),
                                 bg="#ffdddd", fg="#8b2222", command=self.stop_encoding)
        stop_button.pack(side="right", padx=18)

        quit_button = tk.Button(bottom, text="Quit", font=("Segoe UI", 11),
                                 bg="#ffd9b3", fg="#7a3b00", command=self.quit)
        quit_button.pack(side="right", padx=6)

    def _is_printable_char(self, name: str) -> bool:
        if name is None:
            return False
        if name == "space":
            return True
        return len(name) == 1 and (32 <= ord(name) <= 126 or name.isprintable())

    def _encode_char(self, ch: str) -> str:
        try:
            c = ch
            if self.encoding_mode == "ascii": return str(ord(c))
            if self.encoding_mode == "binary": return format(ord(c), "08b")
            if self.encoding_mode == "binary16": return format(ord(c), "016b")
            if self.encoding_mode == "octal": return oct(ord(c))[2:]
            if self.encoding_mode == "decimal": return str(ord(c))
            if self.encoding_mode == "hex": return format(ord(c), "x")
            if self.encoding_mode == "unicode": return f"U+{ord(c):04X}"
            if self.encoding_mode == "unicodehex": return f"\\u{ord(c):04x}"
            if self.encoding_mode == "utf8": return " ".join(f"{b:02x}" for b in c.encode("utf-8", errors="replace"))
            if self.encoding_mode == "utf16": return " ".join(f"{b:02x}" for b in c.encode("utf-16", errors="replace"))
            if self.encoding_mode == "utf32": return " ".join(f"{b:02x}" for b in c.encode("utf-32", errors="replace"))
            if self.encoding_mode == "base32": return base64.b32encode(c.encode(errors="replace")).decode().strip('=')
            if self.encoding_mode == "base64": return base64.b64encode(c.encode(errors="replace")).decode().strip('=')
            if self.encoding_mode == "rot13":
                a = ord(c)
                if 'a' <= c <= 'z': return chr((a - 97 + 13) % 26 + 97)
                if 'A' <= c <= 'Z': return chr((a - 65 + 13) % 26 + 65)
                return c
            if self.encoding_mode == "caesar3":
                if c.isalpha():
                    base = ord('A') if c.isupper() else ord('a')
                    return chr((ord(c) - base + 3) % 26 + base)
                return c
            if self.encoding_mode == "atbash":
                if c.isalpha():
                    if c.isupper(): return chr(155 - ord(c))
                    else: return chr(219 - ord(c))
                return c
            if self.encoding_mode == "reverse": return c
            if self.encoding_mode == "leet":
                table = {'a':'4','e':'3','i':'1','o':'0','t':'7','s':'5','g':'9','A':'4','E':'3','I':'1','O':'0','T':'7','S':'5','G':'9'}
                return table.get(c, c)
            if self.encoding_mode == "morse": return MORSE.get(c.upper(), '/')
            if self.encoding_mode == "url": return urllib.parse.quote(c)
            if self.encoding_mode == "html": return f"&#{ord(c)};"
            if self.encoding_mode == "roman":
                n = ord(c)
                if n > 3999: return str(n)
                vals = [(1000,"M"),(900,"CM"),(500,"D"),(400,"CD"),(100,"C"),(90,"XC"),(50,"L"),(40,"XL"),(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")]
                res = []
                for v,s in vals:
                    while n >= v:
                        res.append(s)
                        n -= v
                return "".join(res)
            if self.encoding_mode == "bcd":
                dec = str(ord(c))
                return " ".join(format(int(d), "04b") for d in dec)
            if self.encoding_mode == "binarymirror": return format(ord(c) & 0xFF, "08b")[::-1]
            if self.encoding_mode == "piglatin": return c + "ay"
            if self.encoding_mode == "emoji": return random.choice(['😀','😎','😇','🤖','🅰️','🌀','🔠','🧠','🦊','🐱','🐶','🌟'])
            if self.encoding_mode == "nato": return NATO.get(c.upper(), c)
            if self.encoding_mode == "braille": return BRAILLE.get(c.lower(), chr(0x2800 + (ord(c) % 64)))
            if self.encoding_mode == "hexmirror": return format(ord(c), "x")[::-1]
            if self.encoding_mode == "revmorse":
                m = MORSE.get(c.upper(), None)
                return m[::-1] if isinstance(m, str) else c
            if self.encoding_mode == "zalgo": return c + "".join(random.choice(ZALGO_CHARS) for _ in range(3))
            if self.encoding_mode == "base85": return base64.a85encode(c.encode()).decode().strip()
            if self.encoding_mode == "binhexcombo": return "0x" + format(ord(c), "x")
            if self.encoding_mode == "hexbincombo": return format(ord(c) & 0xFF, "08b")
            if self.encoding_mode == "encrypted": return f"⟦{format(ord(c),'x')}⟧"
            return c
        except Exception:
            return c

    def _start_hook(self):
        def handler(ev):
            if ev.event_type != keyboard.KEY_DOWN:
                return True 
            if self.injecting:
                return True
            name = ev.name
            if not self._is_printable_char(name):
                return True 
            try:
                self.injecting = True
                char_to_encode = " " if name == "space" else name
                encoded = self._encode_char(char_to_encode)
                keyboard.write(encoded)
                return False 
            except Exception as e:
                print(f"Injection error: {e}")
                return True 
            finally:
                self.injecting = False
        try:
            self.hook_id = keyboard.hook(handler, suppress=True) 
            self.running_hook = True
            while self.encoding_mode:
                time.sleep(0.1)
        except Exception as e:
            print("Keyboard hook error (needs admin/sudo):", e)
            self.stop_encoding()


    def _start_tray(self):
        try:
            img_size = (64, 64)
            try:
                img = Image.open(self.logo_path).convert("RGBA")
            except Exception:
                img = Image.new("RGBA", img_size, (30, 100, 200, 255))
            icon_img = ImageOps.fit(img, img_size, Image.Resampling.LANCZOS)
            blue_tint = Image.new("RGBA", icon_img.size, (40, 140, 220, 90))
            icon_img = Image.alpha_composite(icon_img.convert("RGBA"), blue_tint)
        except Exception as e:
            icon_img = Image.new("RGBA", (64, 64), (40, 140, 220, 255))
        def on_quit(icon, item):
            self.stop_encoding()
            try:
                icon.stop()
            except Exception:
                pass
            self.quit()
        menu = (pystray.MenuItem('Quit', on_quit),)
        self.tray_icon = pystray.Icon("encoding_keyboard", icon_img, "Encoding active", menu=pystray.Menu(*menu))
        try:
            self.tray_icon.run()
        except Exception as e:
            self.tray_icon = None


    def _on_encoding_click(self, mode_name: str):
        if self.encoding_mode == mode_name:
            self.stop_encoding()
            return
        self.stop_encoding(do_gui_update=False) 
        self.encoding_mode = mode_name
        self.status_label.config(text=f"Mode: {mode_name.upper()}")
        for name, btn in self.buttons.items():
            if name == mode_name:
                btn.config(bg="#9dc9ff", relief="sunken")
            else:
                btn.config(bg="#d9e8ff", relief="raised")
        if not self.running_hook:
            t = threading.Thread(target=self._start_hook, daemon=True)
            t.start()
        if (self.tray_thread is None) or (not self.tray_thread.is_alive()):
            self.tray_thread = threading.Thread(target=self._start_tray, daemon=True)
            self.tray_thread.start()

    def stop_encoding(self, do_gui_update=True):
        if do_gui_update and self.encoding_mode:
            for name, btn in self.buttons.items():
                btn.config(bg="#d9e8ff", relief="raised")
            self.status_label.config(text="Mode: OFF")
        self.encoding_mode = None
        try:
            if self.hook_id:
                keyboard.unhook(self.hook_id)
            keyboard.unhook_all()
        except Exception:
            pass
        self.running_hook = False
        self.hook_id = None
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
    def quit(self):
        self.stop_encoding()
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)
    def _on_close(self):
        if messagebox.askyesno("Quit", "Quit Encoding Keyboard?"):
            self.quit()

if __name__ == "__main__":
    app = EncodingKeyboardApp("logo.png")

