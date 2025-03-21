import os
import string
import shutil
import ctypes
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class USB_reader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("USB reader")
        self.geometry("1000x600")
        self.configure(bg="#393e46")
        
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview",
                        background="#393e46",
                        foreground="#03fff6",
                        fieldbackground="#393e46",
                        font=("MS Sans Serif", 10))
        style.configure("Treeview.Heading",
                        background="#00CFC8",
                        foreground="#393e46",
                        font=("MS Sans Serif", 10, "bold"))
        
        toolbar = tk.Frame(self, bg="#00CFC8")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Label(toolbar, text="Search:", bg="#00CFC8", fg="#393e46").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(toolbar, textvariable=self.search_var, bg="#393e46", fg="#03fff6")
        search_entry.pack(side=tk.LEFT, padx=5)
        search_btn = tk.Button(toolbar, text="Search", command=self.search, bg="#393e46", fg="#03fff6")
        search_btn.pack(side=tk.LEFT, padx=5)

        up_btn = tk.Button(toolbar, text="Up", command=self.go_up, bg="#393e46", fg="#03fff6")
        up_btn.pack(side=tk.LEFT, padx=5)

        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#393e46")
        paned.pack(fill=tk.BOTH, expand=True)

        explorer_frame = tk.Frame(paned, bg="#393e46")
        paned.add(explorer_frame, stretch="always")

        sidebar_frame = tk.Frame(paned, width=300, bg="#393e46")
        paned.add(sidebar_frame)

        self.tree = ttk.Treeview(explorer_frame, columns=("fullpath",), displaycolumns=())
        self.tree.heading("#0", text="Name", anchor='w')
        self.tree.column("#0", anchor='w')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewOpen>>", self.on_open)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Create Folder", command=self.create_folder)
        self.context_menu.add_command(label="Create File", command=self.create_file)
        self.context_menu.add_command(label="Rename", command=self.rename_item)
        self.context_menu.add_command(label="Delete", command=self.delete_item)
        self.context_menu.add_command(label="attributes", command=self.show_metadata)

        tk.Label(sidebar_frame, text="Search Results", bg="#393e46", fg="#03fff6").pack(anchor="nw", padx=5, pady=5)
        self.search_results = tk.Listbox(sidebar_frame, bg="#393e46", fg="#03fff6",
                                         selectbackground="#00CFC8", selectforeground="#393e46")
        self.search_results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.init_tree()

    def init_tree(self):
        drives = self.get_usb_drives()
        if not drives:
            messagebox.showinfo("Info", "No USB drives found.")
        for drive in drives:
            node = self.tree.insert("", "end", text=drive, values=(drive,))
            self.tree.insert(node, "end", text="dummy")

    def get_usb_drives(self):
        drives = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive = letter + ":\\"
                # DRIVE_REMOVABLE = 2
                if ctypes.windll.kernel32.GetDriveTypeW(drive) == 2:
                    drives.append(drive)
            bitmask >>= 1
        return drives

    def on_open(self, event):
        node = self.tree.focus()
        path = self.get_full_path(node)
        children = self.tree.get_children(node)
        if children:
            first_child = children[0]
            if self.tree.item(first_child, "text") == "dummy":
                self.tree.delete(first_child)
        self.populate_tree(node, path)

    def populate_tree(self, parent, path):
        try:
            for item in os.listdir(path):
                abspath = os.path.join(path, item)
                node = self.tree.insert(parent, "end", text=item, values=(abspath,))
                if os.path.isdir(abspath):
                    self.tree.insert(node, "end", text="dummy")
        except Exception as e:
            print(f"Error reading {path}: {e}")

    def get_full_path(self, node):
        return self.tree.set(node, "fullpath")

    def show_context_menu(self, event):
        node = self.tree.identify_row(event.y)
        if node:
            self.tree.selection_set(node)
            self.context_menu.post(event.x_root, event.y_root)

    def create_folder(self):
        node = self.tree.focus()
        parent_path = self.get_full_path(node)
        folder_name = simpledialog.askstring("Create Folder", "Folder name:")
        if folder_name:
            new_path = os.path.join(parent_path, folder_name)
            try:
                os.mkdir(new_path)
                new_node = self.tree.insert(node, "end", text=folder_name, values=(new_path,))
                self.tree.insert(new_node, "end", text="dummy")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def create_file(self):
        node = self.tree.focus()
        parent_path = self.get_full_path(node)
        file_name = simpledialog.askstring("Create File", "File name:")
        if file_name:
            new_path = os.path.join(parent_path, file_name)
            try:
                with open(new_path, 'w') as f:
                    f.write("")
                self.tree.insert(node, "end", text=file_name, values=(new_path,))
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def rename_item(self):
        node = self.tree.focus()
        old_path = self.get_full_path(node)
        new_name = simpledialog.askstring("Rename", "New name:")
        if new_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.tree.item(node, text=new_name, values=(new_path,))
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_item(self):
        node = self.tree.focus()
        path = self.get_full_path(node)
        confirm = messagebox.askyesno("Delete", f"Are you sure you want to delete:\n{path}?")
        if confirm:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.tree.delete(node)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def human_readable_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def get_folder_size(self, folder):
        """Recursively calculates folder size using os.scandir with error handling."""
        total_size = 0
        try:
            with os.scandir(folder) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total_size += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            total_size += self.get_folder_size(entry.path)
                    except Exception:
                        continue
        except Exception:
            pass
        return total_size

    def show_metadata(self):
        node = self.tree.focus()
        path = self.get_full_path(node)

        # Check that the path exists and isn't a placeholder.
        if not os.path.exists(path):
            messagebox.showerror("Error", "The selected path does not exist or is invalid.")
            return

        try:
            # Use os.path.isfile and os.path.isdir to decide how to calculate size.
            if os.path.isfile(path):
                try:
                    size = os.path.getsize(path)
                except Exception:
                    size = 0
            elif os.path.isdir(path):
                size = self.get_folder_size(path)
            else:
                size = 0

            hr_size = self.human_readable_size(size)
            stat_info = os.stat(path)
            last_modified = time.ctime(stat_info.st_mtime)
            created = time.ctime(stat_info.st_ctime)
            metadata = (
                f"Path: {path}\n"
                f"Size: {hr_size}\n"
                f"Last Modified: {last_modified}\n"
                f"Created: {created}"
            )
            messagebox.showinfo("Metadata", metadata)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search(self):
        search_term = self.search_var.get().lower()
        self.search_results.delete(0, tk.END)
        if not search_term:
            return

        node = self.tree.focus()
        if not node:
            messagebox.showinfo("Info", "Please select a directory to search within.")
            return

        start_path = self.get_full_path(node)
        matches = []
        for root, dirs, files in os.walk(start_path):
            for name in dirs + files:
                if search_term in name.lower():
                    matches.append(os.path.join(root, name))
        if matches:
            for match in matches:
                self.search_results.insert(tk.END, match)
        else:
            self.search_results.insert(tk.END, "No matching files or folders found.")

    def go_up(self):
        node = self.tree.focus()
        parent = self.tree.parent(node)
        if parent:
            self.tree.selection_set(parent)
            self.tree.focus(parent)
        else:
            messagebox.showinfo("Info", "No parent directory.")

if __name__ == "__main__":
    app = USB_reader()
    app.mainloop()
