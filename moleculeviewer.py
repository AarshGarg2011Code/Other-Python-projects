'''
    ChemGeek3D VERSION 1 SRC
'''

import customtkinter as ctk
import pubchempy as pcp
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import time
import requests
from scipy.interpolate import interp1d

class ChemGeekApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ChemGeek 3D: Research Edition")
        self.geometry("1450x900")
        ctk.set_appearance_mode("dark")
        
        self.is_rotating = False
        self.show_surface = False
        self.is_loading = False
        self.current_mol = None
        self.canvas_lock = threading.Lock() # Fix for the 'M' attribute error

        self.vdw_radii = {'H': 1.2, 'C': 1.7, 'N': 1.55, 'O': 1.52, 'F': 1.47, 'P': 1.8, 'S': 1.8, 'Cl': 1.75, 'Fe': 1.8, 'Na': 2.27, 'Sb': 2.0, 'Mg': 1.73}
        self.cpk_colors = {'H': '#FFFFFF', 'C': '#444444', 'N': '#3050F8', 'O': '#FF0D0D', 'F': '#90E050', 'Cl': '#1FF01F', 'Sb': '#FFD700', 'S': '#FFFF30', 'Fe': '#E06633'}
        self.en_scale = {'H': 2.20, 'C': 2.55, 'N': 3.04, 'O': 3.44, 'F': 3.98, 'Na': 0.93, 'Cl': 3.16}

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=320)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.sidebar, text="MOLECULAR ENGINE", font=("Arial", 22, "bold")).pack(pady=20)
        self.search_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Name (e.g. C60, DNA, TNT)", width=250)
        self.search_entry.pack(pady=10)
        self.btn_search = ctk.CTkButton(self.sidebar, text="RENDER MODEL", fg_color="#27ae60", command=self.start_search)
        self.btn_search.pack(pady=10)

        self.rotate_switch = ctk.CTkSwitch(self.sidebar, text="Auto-Rotate", command=self.toggle_rotation)
        self.rotate_switch.pack(pady=10)
        self.surface_switch = ctk.CTkSwitch(self.sidebar, text="VdW Surface (Small Mols)", command=self.toggle_surface)
        self.surface_switch.pack(pady=10)

        self.info_box = ctk.CTkTextbox(self.sidebar, height=350, width=280, font=("Consolas", 12))
        self.info_box.pack(pady=20, padx=20)

        self.main_panel = ctk.CTkFrame(self, fg_color="#2B2B2B")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.fig = plt.figure(facecolor='#2B2B2B', figsize=(8,8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('#2B2B2B')
        self.ax.set_axis_off()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def toggle_surface(self):
        self.show_surface = self.surface_switch.get()
        if self.current_mol:
            if self.current_mol.GetNumAtoms() < 400:
                self.render_final(self.current_mol, "Refreshing...", "Live")
            else:
                self.surface_switch.deselect()

    def toggle_rotation(self):
        self.is_rotating = self.rotate_switch.get()
        if self.is_rotating: threading.Thread(target=self.rotation_loop, daemon=True).start()

    def rotation_loop(self):
        angle = 0
        while self.is_rotating:
            with self.canvas_lock:
                try:
                    angle = (angle + 2) % 360
                    self.ax.view_init(elev=20, azim=angle)
                    self.canvas.draw_idle()
                except: break
            time.sleep(0.05)

    def start_search(self):
        query = self.search_entry.get().strip()
        if not query: return
        self.is_loading = True
        self.btn_search.configure(state="disabled")
        threading.Thread(target=self.animate_loading, daemon=True).start()
        threading.Thread(target=self.universal_logic, args=(query,), daemon=True).start()

    def animate_loading(self):
        t = 0
        n_points = 12
        base_coords = np.random.uniform(-1, 1, (n_points, 3))
        while self.is_loading:
            with self.canvas_lock:
                self.ax.clear()
                self.ax.set_axis_off()
                pulse = 1.0 + 0.2 * np.sin(t * 4)
                current = base_coords * pulse + np.random.normal(0, 0.03, (n_points, 3))
                self.ax.scatter(current[:,0], current[:,1], current[:,2], s=150, color='#27ae60', alpha=0.6)
                for i in range(n_points-1):
                    self.ax.plot(current[i:i+2,0], current[i:i+2,1], current[i:i+2,2], color='#27ae60', alpha=0.3)
                self.ax.view_init(elev=20, azim=t*50)
                self.ax.set_xlim(-2,2); self.ax.set_ylim(-2,2); self.ax.set_zlim(-2,2)
                self.canvas.draw_idle()
            t += 0.05
            time.sleep(0.04)

    def universal_logic(self, query):
        try:
            res = pcp.get_compounds(query, 'name')
            if res:
                smi = res[0].smiles
                mol = Chem.MolFromSmiles(smi)
                if mol:
                    mol = Chem.AddHs(mol)
                    params = AllChem.ETKDGv3()
                    params.useSmallRingTorsions = True
                    AllChem.EmbedMolecule(mol, params)
                    AllChem.MMFFOptimizeMolecule(mol)
                    self.current_mol = mol
                    self.is_loading = False
                    self.after(100, lambda: self.render_final(mol, query, "Chemical"))
                    return

            api = f"https://search.rcsb.org/rcsbsearch/v2/query?json=%7B%22query%22%3A%7B%22type%22%3A%22terminal%22%2C%22service%22%3A%22full_text%22%2C%22parameters%22%3A%7B%22value%22%3A%22{query}%22%7D%7D%2C%22return_type%22%3A%22entry%22%7D"
            pdb_id = requests.get(api).json()['result_set'][0]['identifier']
            pdb_data = requests.get(f"https://files.rcsb.org/download/{pdb_id}.pdb").text
            mol = Chem.MolFromPDBBlock(pdb_data)
            if mol:
                self.current_mol = mol
                self.is_loading = False
                self.after(100, lambda: self.render_final(mol, query, "Protein"))
        except:
            self.is_loading = False
            self.after(0, lambda: self.btn_search.configure(text="ERROR", state="normal"))

    def render_final(self, mol, name, m_type):
        with self.canvas_lock:
            self.ax.clear()
            self.ax.set_axis_off()
            conf = mol.GetConformer()
            coords = conf.GetPositions()
            atoms = mol.GetAtoms()
            
            if self.show_surface and len(atoms) < 400:
                for a in atoms:
                    p = coords[a.GetIdx()]
                    r = self.vdw_radii.get(a.GetSymbol(), 1.5)
                    self.ax.scatter(p[0], p[1], p[2], s=r**2*1400, color=self.cpk_colors.get(a.GetSymbol(), 'gray'), alpha=0.1)

            if len(atoms) > 400:
                t = np.linspace(0, 1, len(coords))
                ts = np.linspace(0, 1, 1000)
                xs = interp1d(t, coords[:,0])(ts)
                ys = interp1d(t, coords[:,1])(ts)
                zs = interp1d(t, coords[:,2])(ts)
                for i in range(len(xs)-1):
                    self.ax.plot(xs[i:i+2], ys[i:i+2], zs[i:i+2], color=plt.cm.jet(i/1000), linewidth=3)
            else:
                for bond in mol.GetBonds():
                    p1, p2 = coords[bond.GetBeginAtomIdx()], coords[bond.GetEndAtomIdx()]
                    self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], color='#888888', linewidth=2)
                for a in atoms:
                    p = coords[a.GetIdx()]
                    r = self.vdw_radii.get(a.GetSymbol(), 1.5)
                    self.ax.scatter(p[0], p[1], p[2], s=r**2*400, color=self.cpk_colors.get(a.GetSymbol(), 'gray'), edgecolors='black')

            self.canvas.draw_idle()
            self.btn_search.configure(text="RENDER MODEL", state="normal")

if __name__ == "__main__":
    app = ChemGeekApp()
    app.mainloop()
