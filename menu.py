import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import subprocess
import threading
import json
import os
import time
from PIL import Image, ImageTk
import tkinter.font as tkFont
import psutil

# ------------- Global Configuration -------------
# Overarching folder for all start menus
START_MENUS_DIR = "start_menus"

# Color scheme (Windows Start Menu–inspired)
MAIN_BG = "#2D2D30"          # dark grey background for main window
TILE_BG = "#0078D7"          # blue for app tiles
TILE_HOVER_BG = "#005A9E"    # darker blue on hover
DETAIL_BG = "#3C3C3C"        # dark grey for detail panel
BUTTON_BG = "#0078D7"
BUTTON_HOVER_BG = "#005A9E"
BUTTON_FG = "white"
TEXT_FG = "white"

# Fonts (using Segoe UI style)
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_NORMAL = ("Segoe UI", 14)
FONT_SMALL = ("Segoe UI", 12)

# Icon and tile sizes
ICON_SIZE = (128, 128)       # resize icons to 128x128
TILE_WIDTH = 200             # approximate width of each tile
TILE_HEIGHT = 220            # approximate height of each tile

# ------------- Persistence Helpers -------------
def get_apps_file_path(base_dir):
    return os.path.join(base_dir, "apps.json")

def get_usage_file_path(base_dir):
    return os.path.join(base_dir, "usage.json")

def load_apps(base_dir):
    path = get_apps_file_path(base_dir)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading apps:", e)
    return []

def save_apps(apps, base_dir):
    path = get_apps_file_path(base_dir)
    try:
        with open(path, "w") as f:
            json.dump(apps, f)
    except Exception as e:
        print("Error saving apps:", e)

def load_usage(base_dir):
    path = get_usage_file_path(base_dir)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading usage:", e)
    return {}

def save_usage(usage, base_dir):
    path = get_usage_file_path(base_dir)
    try:
        with open(path, "w") as f:
            json.dump(usage, f)
    except Exception as e:
        print("Error saving usage:", e)

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# ------------- Scrollable Frame for App Tiles -------------
class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.configure(bg=MAIN_BG)
        canvas = tk.Canvas(self, bg=MAIN_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=MAIN_BG)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

# ------------- Helper: Check if Process Tree is Running -------------
def is_process_tree_running(process):
    if psutil:
        try:
            proc = psutil.Process(process.pid)
            if proc.is_running():
                children = proc.children(recursive=True)
                # If either the main process or any child is running, return True.
                if proc.is_running() or any(child.is_running() for child in children):
                    return True
            return False
        except psutil.NoSuchProcess:
            return False
    else:
        # Fallback: use the original process.poll()
        return process.poll() is None

# ------------- Main App Launcher -------------
class Menu(tk.Tk):
    def __init__(self, start_menu_dir):
        super().__init__()
        self.start_menu_dir = start_menu_dir
        self.title(f"Apps Launcher - {os.path.basename(start_menu_dir)}")
        self.configure(bg=MAIN_BG)
        self.geometry("1000x600")
        
        # Load persisted data for this start menu
        self.apps = load_apps(self.start_menu_dir)  # Each app: {"name": str, "path": str, "icon": str}
        self.usage = load_usage(self.start_menu_dir)  # Mapping: app path -> total usage time (in seconds)
        
        self.icon_images = {}    # keep references to PhotoImage objects
        self.tile_frames = {}    # map index -> tile container (for highlighting)
        self.selected_index = None  # currently selected app index
        
        self.create_toolbar()
        self.create_main_frames()
        
        self.populate_tiles()
        self.create_detail_panel()
    
    def create_toolbar(self):
        toolbar = tk.Frame(self, bg=MAIN_BG)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        add_btn = tk.Button(toolbar, text="Add App", bg=BUTTON_BG, fg=BUTTON_FG,
                            font=FONT_NORMAL, padx=10, pady=5, command=self.add_app)
        add_btn.pack(side=tk.LEFT, padx=10, pady=10)
    
    def create_main_frames(self):
        self.left_frame = ScrollableFrame(self)
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.detail_frame = tk.Frame(self, bg=DETAIL_BG, bd=2, relief=tk.RIDGE)
        self.detail_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def populate_tiles(self):
        for widget in self.left_frame.scrollable_frame.winfo_children():
            widget.destroy()
        self.icon_images.clear()
        self.tile_frames.clear()
        
        columns = 3
        for idx, app in enumerate(self.apps):
            tile_container = tk.Frame(self.left_frame.scrollable_frame, bg=TILE_BG, width=TILE_WIDTH, height=TILE_HEIGHT, bd=2, relief=tk.RIDGE)
            tile_container.grid_propagate(False)
            tile_container.grid(row=idx//columns, column=idx % columns, padx=10, pady=10)
            self.tile_frames[idx] = tile_container
            
            icon_path = app.get("icon", "")
            if icon_path and os.path.exists(icon_path):
                try:
                    img = Image.open(icon_path)
                    img = img.resize(ICON_SIZE, Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                except Exception as e:
                    print("Error loading icon:", e)
                    photo = None
            else:
                photo = None
            if not photo:
                photo = ImageTk.PhotoImage(Image.new("RGB", ICON_SIZE, color="gray"))
            self.icon_images[idx] = photo
            
            app_path = app.get("path", "")
            total_time = self.usage.get(app_path, 0)
            usage_str = f"Usage: {format_time(total_time)}"
            
            btn = tk.Button(tile_container, image=photo,
                            text=f"{app.get('name', 'Unnamed')}\n{usage_str}",
                            compound="top", wraplength=180, justify="center",
                            font=FONT_NORMAL, bg=TILE_BG, fg=TEXT_FG, bd=0,
                            command=lambda idx=idx: self.select_tile(idx))
            btn.pack(expand=True, fill="both")
            
            tile_container.bind("<Enter>", lambda e, idx=idx: self.on_tile_hover(idx, True))
            tile_container.bind("<Leave>", lambda e, idx=idx: self.on_tile_hover(idx, False))
            btn.bind("<Enter>", lambda e, idx=idx: self.on_tile_hover(idx, True))
            btn.bind("<Leave>", lambda e, idx=idx: self.on_tile_hover(idx, False))
    
    def on_tile_hover(self, idx, hover):
        tile = self.tile_frames.get(idx)
        if tile:
            tile.configure(bg=TILE_HOVER_BG if hover else TILE_BG)
    
    def create_detail_panel(self):
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
        
        title = tk.Label(self.detail_frame, text="App Details", bg=DETAIL_BG, fg=TEXT_FG, font=FONT_TITLE)
        title.pack(pady=10)
        
        self.detail_container = tk.Frame(self.detail_frame, bg=DETAIL_BG)
        self.detail_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.update_detail_panel()
    
    def update_detail_panel(self):
        for widget in self.detail_container.winfo_children():
            widget.destroy()
        
        if self.selected_index is None:
            msg = tk.Label(self.detail_container, text="Select an app tile to manage", bg=DETAIL_BG, fg=TEXT_FG, font=FONT_NORMAL)
            msg.pack(pady=20)
        else:
            app = self.apps[self.selected_index]
            app_path = app.get("path", "")
            total_time = self.usage.get(app_path, 0)
            
            name_frame = tk.Frame(self.detail_container, bg=DETAIL_BG)
            name_frame.pack(fill="x", pady=5)
            tk.Label(name_frame, text="Name:", bg=DETAIL_BG, fg=TEXT_FG, font=FONT_NORMAL).pack(side="left")
            self.name_var = tk.StringVar(value=app.get("name", ""))
            name_entry = tk.Entry(name_frame, textvariable=self.name_var, font=FONT_NORMAL)
            name_entry.pack(side="left", fill="x", expand=True, padx=5)
            update_btn = tk.Button(name_frame, text="Update", bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL,
                                   command=self.update_name)
            update_btn.pack(side="left", padx=5)
            
            path_frame = tk.Frame(self.detail_container, bg=DETAIL_BG)
            path_frame.pack(fill="x", pady=5)
            tk.Label(path_frame, text="Path:", bg=DETAIL_BG, fg=TEXT_FG, font=FONT_NORMAL).pack(side="left")
            path_label = tk.Label(path_frame, text=app_path, bg=DETAIL_BG, fg=TEXT_FG, font=FONT_SMALL, wraplength=250)
            path_label.pack(side="left", padx=5)
            
            usage_frame = tk.Frame(self.detail_container, bg=DETAIL_BG)
            usage_frame.pack(fill="x", pady=5)
            tk.Label(usage_frame, text="Total Usage:", bg=DETAIL_BG, fg=TEXT_FG, font=FONT_NORMAL).pack(side="left")
            usage_label = tk.Label(usage_frame, text=f"{format_time(total_time)}", bg=DETAIL_BG, fg=TEXT_FG, font=FONT_NORMAL)
            usage_label.pack(side="left", padx=5)
            
            btn_frame = tk.Frame(self.detail_container, bg=DETAIL_BG)
            btn_frame.pack(pady=15)
            
            launch_btn = tk.Button(btn_frame, text="Launch App", bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL,
                                   padx=10, pady=5, command=self.launch_selected_app)
            launch_btn.pack(side="left", padx=5)
            
            icon_btn = tk.Button(btn_frame, text="Set Icon", bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL,
                                 padx=10, pady=5, command=self.set_icon)
            icon_btn.pack(side="left", padx=5)
            
            remove_btn = tk.Button(btn_frame, text="Remove App", bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL,
                                   padx=10, pady=5, command=self.remove_app)
            remove_btn.pack(side="left", padx=5)
    
    def clear_tile_highlights(self):
        for tile in self.tile_frames.values():
            tile.config(bd=2)
    
    def select_tile(self, idx):
        self.selected_index = idx
        self.clear_tile_highlights()
        tile = self.tile_frames.get(idx)
        if tile:
            tile.config(bd=4)
        self.update_detail_panel()
    
    def update_name(self):
        if self.selected_index is not None:
            new_name = self.name_var.get().strip()
            if new_name:
                self.apps[self.selected_index]["name"] = new_name
                save_apps(self.apps, self.start_menu_dir)
                self.populate_tiles()
                self.update_detail_panel()
    
    def set_icon(self):
        if self.selected_index is not None:
            icon_path = filedialog.askopenfilename(title="Select Icon",
                                                   filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.ico"), ("All Files", "*.*")])
            if icon_path:
                self.apps[self.selected_index]["icon"] = icon_path
                save_apps(self.apps, self.start_menu_dir)
                self.populate_tiles()
                self.update_detail_panel()
    
    def remove_app(self):
        if self.selected_index is not None:
            del self.apps[self.selected_index]
            save_apps(self.apps, self.start_menu_dir)
            self.selected_index = None
            self.populate_tiles()
            self.update_detail_panel()
    
    def launch_selected_app(self):
        if self.selected_index is not None:
            self.launch_app(self.selected_index)
    
    def launch_app(self, idx):
        app = self.apps[idx]
        app_path = app.get("path", "")
        if not os.path.exists(app_path):
            messagebox.showerror("Error", f"Application not found:\n{app_path}")
            return
        try:
            start_time = time.time()
            process = subprocess.Popen([app_path])
            # Update UI immediately
            self.populate_tiles()
            self.update_detail_panel()
            # Start continuous usage tracking in a separate thread.
            threading.Thread(target=self.track_session, args=(app_path, process, start_time), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch app:\n{e}")
    
    def track_session(self, app_path, process, start_time):
        last_time = start_time
        # Use psutil (if available) to check if the process tree is still running.
        while is_process_tree_running(process):
            time.sleep(1)
            now = time.time()
            elapsed = now - last_time
            last_time = now
            self.usage[app_path] = self.usage.get(app_path, 0) + elapsed
            save_usage(self.usage, self.start_menu_dir)
            self.after(0, lambda: [self.populate_tiles(), self.update_detail_panel()])
        # Final update after process (and its children) have terminated.
        now = time.time()
        elapsed = now - last_time
        self.usage[app_path] = self.usage.get(app_path, 0) + elapsed
        save_usage(self.usage, self.start_menu_dir)
        self.after(0, lambda: [self.populate_tiles(), self.update_detail_panel()])
    
    def add_app(self):
        app_path = filedialog.askopenfilename(title="Select Application")
        if app_path:
            default_name = os.path.basename(app_path)
            new_app = {"name": default_name, "path": app_path, "icon": ""}
            self.apps.append(new_app)
            save_apps(self.apps, self.start_menu_dir)
            self.populate_tiles()

# ------------- Start Menu Selector -------------
class StartMenuSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Start Menu Selector")
        self.configure(bg=MAIN_BG)
        self.geometry("500x400")
        
        # Ensure the overarching folder exists
        if not os.path.exists(START_MENUS_DIR):
            os.makedirs(START_MENUS_DIR)
        
        header = tk.Label(self, text="Choose Your Start Menu", bg=MAIN_BG, fg=TEXT_FG, font=FONT_TITLE)
        header.pack(pady=20)
        
        self.container = tk.Frame(self, bg=MAIN_BG)
        self.container.pack(fill="both", expand=True, padx=20)
        
        self.refresh_start_menu_buttons()
        
        create_btn = tk.Button(self, text="Create New Start Menu", bg=BUTTON_BG, fg=BUTTON_FG,
                               font=FONT_NORMAL, padx=10, pady=5, command=self.create_start_menu)
        create_btn.pack(pady=10)
    
    def refresh_start_menu_buttons(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        
        # List folders in START_MENUS_DIR and display as buttons
        menus = [name for name in os.listdir(START_MENUS_DIR)
                 if os.path.isdir(os.path.join(START_MENUS_DIR, name))]
        if not menus:
            msg = tk.Label(self.container, text="No Start Menus found. Create one!", bg=MAIN_BG, fg=TEXT_FG, font=FONT_NORMAL)
            msg.pack(pady=20)
        else:
            columns = 2
            for idx, name in enumerate(menus):
                btn = tk.Button(self.container, text=name, bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL,
                                width=15, height=2, relief="flat",
                                command=lambda name=name: self.open_start_menu(name))
                btn.grid(row=idx//columns, column=idx % columns, padx=10, pady=10)
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BUTTON_HOVER_BG))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BUTTON_BG))
    
    def create_start_menu(self):
        name = simpledialog.askstring("New Start Menu", "Enter name for new Start Menu:")
        if name:
            new_dir = os.path.join(START_MENUS_DIR, name)
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)
                with open(os.path.join(new_dir, "apps.json"), "w") as f:
                    json.dump([], f)
                with open(os.path.join(new_dir, "usage.json"), "w") as f:
                    json.dump({}, f)
                self.refresh_start_menu_buttons()
            else:
                messagebox.showerror("Error", "A Start Menu with that name already exists.")
    
    def open_start_menu(self, name):
        menu_dir = os.path.join(START_MENUS_DIR, name)
        self.destroy()
        launcher = Menu(menu_dir)
        launcher.mainloop()

if __name__ == "__main__":
    selector = StartMenuSelector()
    selector.mainloop()