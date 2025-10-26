import tkinter as tk
from tkinter import messagebox
import random

root = tk.Tk()
root.title("💀💀💀💀💀💀💀💀💀💀💀💀")
root.geometry("600x400")
root.resizable(False, False)

root.protocol("WM_DELETE_WINDOW", lambda: None)

confirm_count = 0

def randomize_colors():
    volume_label.config(fg=random.choice(["red","blue","green","purple","orange"]))
    slider_label.config(fg=random.choice(["red","blue","green","purple","orange"]))
    confirm_btn.config(bg=random.choice(["yellow","pink","cyan","lime","magenta"]))
    teleport_btn.config(bg=random.choice(["yellow","pink","cyan","lime","magenta"]))

def extreme_teleport():
    new_x1 = random.randint(0, 500)
    new_y1 = random.randint(0, 350)
    teleport_btn.place(x=new_x1, y=new_y1)

    new_x2 = random.randint(0, 500)
    new_y2 = random.randint(0, 350)
    confirm_btn.place(x=new_x2, y=new_y2)

    randomize_colors()
    root.after(10, extreme_teleport)  

def slider_trick(event=None):
    slider.set(random.randint(0, 100))
    randomize_colors()
    if random.random() < 0.3:
        messagebox.showinfo("Chaos!", f"Slider jumped! Current value: {slider.get()}")

def confirm_action():
    global confirm_count
    confirm_count += 1
    required = random.randint(50, 100)  
    if confirm_count < required:
        messagebox.showwarning("Not yet!", f"You must confirm {required} times! ({confirm_count}/{required})")
    else:
        messagebox.showinfo("Finally!", "You survived the IMPOSSIBLE GUI 😈")
        root.destroy()

def random_popup():
    if random.random() < 0.5:
        messagebox.showinfo("Annoying!", f"Slider: {slider.get()} Volume\nTry clicking something!")
    root.after(random.randint(10, 20), random_popup)

def auto_slider_move():
    slider.set(random.randint(0, 100))
    randomize_colors()
    root.after(5, auto_slider_move)

def chaos_window():
    choice = random.choice(["minimize", "maximize", "small"])
    if choice == "minimize":
        root.iconify()
    elif choice == "maximize":
        root.state("zoomed")
    elif choice == "small":
        root.geometry(f"{random.randint(200, 600)}x{random.randint(150, 400)}")
    root.after(100, chaos_window) 

volume_label = tk.Label(root, text="Lorem ipsum dolor sit amet, consectetur", font=("Arial", 16))
volume_label.pack(pady=10)

slider_label = tk.Label(root, text="Doom", font=("Arial", 14))
slider_label.pack()

slider = tk.Scale(root, from_=0, to=100, orient="horizontal", length=400)
slider.pack(pady=10)
slider.bind("<ButtonRelease-1>", slider_trick)

confirm_btn = tk.Button(root, text="Lorem ipsum", font=("Arial", 14), command=confirm_action)
confirm_btn.place(x=250, y=150)

teleport_btn = tk.Button(root, text="Lorem ipsum", font=("Arial", 14))
teleport_btn.place(x=250, y=200)

extreme_teleport()

root.after(100, random_popup)
root.after(50, auto_slider_move)
root.after(100, chaos_window)

root.mainloop()
