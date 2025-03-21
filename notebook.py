# note app thingamabob.
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog, messagebox, simpledialog, colorchooser
import re
from tkinter import ttk
import os
import shutil
import json

class Notebook(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # Global starter style
        self.font_size = 12  
        self.global_text_color = "black"
        self.global_bg_color = "white"
        # Counters for unique tag names 
        self.bg_color_tag_count = 0
        self.text_color_tag_count = 0
        self.sel_font_tag_count = 0
        self.init_ui()

    def init_ui(self):

        self.text_frame = tk.Frame(self)
        self.text_frame.pack(fill='both', expand=True)

        # Line number widget. (it exists)
        self.line_numbers = tk.Text(
            self.text_frame, width=4, padx=5, wrap='none',
            font=("Courier", self.font_size), state='disabled',
            bg='#f0f0f0', fg='gray', relief='flat'
        )
        self.line_numbers.pack(side='left', fill='y')

        # Main text widget (ScrolledText) with global colors
        self.text_widget = ScrolledText(
            self.text_frame, wrap='word', font=("Courier", self.font_size),
            foreground=self.global_text_color, background=self.global_bg_color
        )
        self.text_widget.pack(side='right', fill='both', expand=True)

        # Toolbar with file, formatting, font size, and color buttons
        toolbar = tk.Frame(self)
        toolbar.pack(fill='x')

        # File buttons
        tk.Button(toolbar, text="Save", command=self.save_to_file).pack(side='left')
        tk.Button(toolbar, text="Load", command=self.load_from_file).pack(side='left')
        # Markdown formatting buttons
        tk.Button(toolbar, text="B", command=lambda: self.apply_tag("**")).pack(side='left')
        tk.Button(toolbar, text="I", command=lambda: self.apply_tag("*")).pack(side='left')
        tk.Button(toolbar, text="S", command=lambda: self.apply_tag("~~")).pack(side='left')
        tk.Button(toolbar, text="Code", command=lambda: self.apply_tag("`")).pack(side='left')
        tk.Button(toolbar, text="H", command=lambda: self.apply_heading("#")).pack(side='left')
        # Global persistent font size buttons (affect entire editor)
        tk.Button(toolbar, text="A+ Global", command=self.increase_font_size).pack(side='left')
        tk.Button(toolbar, text="A- Global", command=self.decrease_font_size).pack(side='left')
        # Local (selected text) font size buttons
        tk.Button(toolbar, text="A+ local", command=self.increase_selection_font_size).pack(side='left')
        tk.Button(toolbar, text="A- local", command=self.decrease_selection_font_size).pack(side='left')
        # Local color buttons (affect only selected text)
        tk.Button(toolbar, text="local Text Color", command=self.choose_text_color).pack(side='left')
        tk.Button(toolbar, text="local BG Color", command=self.choose_bg_color).pack(side='left')
        # Global color buttons (persistently update default style)
        tk.Button(toolbar, text="Global Text Color", command=self.global_choose_text_color).pack(side='left')
        tk.Button(toolbar, text="Global BG Color", command=self.global_choose_bg_color).pack(side='left')

        # Bind events 
        self.text_widget.bind('<KeyRelease>', self.on_key_release)
        self.text_widget.bind('<MouseWheel>', self.sync_scroll)
        self.text_widget.bind('<Shift-MouseWheel>', self.sync_scroll)

        # tutorial cuz ppl be stupid
        sample_content = (
            "## Features\n"
            "- **Bold Text**\n"
            "- *Italic Text*\n"
            "- ~~Strikethrough~~\n"
            "- `Inline Code`\n"
            "```\n"
            "Code Block\n"
            "```\n"
            "> Quotes are supported too.\n"
            "[Link](https://www.example.com)\n"
            "~~Deleted Text~~\n"
            "[Email](mailto:example@example.com)\n"
        )
        self.text_widget.insert("1.0", sample_content)
        self.highlight_syntax()
        self.update_line_numbers()

    def on_key_release(self, event=None):
        self.highlight_syntax()
        self.update_line_numbers()

    def apply_tag(self, tag):
        try:
            start = self.text_widget.index(tk.SEL_FIRST)
            end = self.text_widget.index(tk.SEL_LAST)
            text = self.text_widget.get(start, end)
            self.text_widget.delete(start, end)
            self.text_widget.insert(start, f"{tag}{text}{tag}")
            self.highlight_syntax()
            self.update_line_numbers()
        except tk.TclError:
            pass

    def apply_heading(self, prefix):
        try:
            line_start = self.text_widget.index(tk.SEL_FIRST).split('.')[0]
            self.text_widget.insert(f"{line_start}.0", f"{prefix} ")
            self.highlight_syntax()
            self.update_line_numbers()
        except tk.TclError:
            pass

    def highlight_syntax(self, event=None):
        # Remove tags related to stuff like bold 
        for tag in ["heading", "bold", "italic", "strikethrough", "bullet",
                    "quote", "inline_code", "code_block", "link", "email"]:
            self.text_widget.tag_remove(tag, "1.0", tk.END)

        # these are tags probs i dunno ask greg
        self.text_widget.tag_configure("heading", foreground="blue", font=("Courier", self.font_size+2, "bold"))
        self.text_widget.tag_configure("bold", foreground="darkred", font=("Courier", self.font_size, "bold"))
        self.text_widget.tag_configure("italic", foreground="darkgreen", font=("Courier", self.font_size, "italic"))
        self.text_widget.tag_configure("strikethrough", font=("Courier", self.font_size, "overstrike"))
        self.text_widget.tag_configure("bullet", foreground="black", font=("Courier", self.font_size))
        self.text_widget.tag_configure("quote", foreground="gray", font=("Courier", self.font_size, "italic"))
        self.text_widget.tag_configure("inline_code", foreground="purple", font=("Courier", self.font_size, "italic"))
        self.text_widget.tag_configure("code_block", background="#f0f0f0", foreground="black", font=("Courier", self.font_size))
        self.text_widget.tag_configure("link", foreground="blue", underline=True, font=("Courier", self.font_size))
        self.text_widget.tag_configure("email", foreground="blue", underline=True, font=("Courier", self.font_size))

        # computer magic
        text = self.text_widget.get("1.0", tk.END)
        patterns = {
            "heading": r"^(#{1,6})\s+.*$",
            "bold": r"\*\*(.+?)\*\*",
            "italic": r"\*(.+?)\*",
            "strikethrough": r"~~(.+?)~~",
            "bullet": r"^- .*$",
            "quote": r"^> .*$",
            "code_block": r"```[\s\S]+?```",
            "inline_code": r"`(.+?)`",
            "link": r"\[([^\]]+)\]\((https?://[^\)]+)\)",
            "email": r"\[([^\]]+)\]\((mailto:[^)]+)\)",
        }
        for tag, pattern in patterns.items():
            for match in re.finditer(pattern, text, re.MULTILINE):
                start_index = f"1.0+{match.start()}c"
                end_index = f"1.0+{match.end()}c"
                self.text_widget.tag_add(tag, start_index, end_index)

    def update_line_numbers(self, event=None):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        line_count = int(self.text_widget.index('end-1c').split('.')[0])
        self.line_numbers.insert('1.0', "\n".join(str(i) for i in range(1, line_count + 1)))
        self.line_numbers.config(state='disabled')

    def sync_scroll(self, event):
        self.line_numbers.yview_moveto(self.text_widget.yview()[0])
        return "break"

    def update_fonts(self):
        """Update global font and colors for the text widget and refresh syntax tags."""
        self.text_widget.config(font=("Courier", self.font_size), 
                                foreground=self.global_text_color, background=self.global_bg_color)
        self.line_numbers.config(font=("Courier", self.font_size))
        self.highlight_syntax()

    def increase_font_size(self):
        self.font_size += 1
        self.update_fonts()
        self.update_line_numbers()

    def decrease_font_size(self):
        if self.font_size > 6:
            self.font_size -= 1
            self.update_fonts()
            self.update_line_numbers()

    def choose_text_color(self):
        try:
            start = self.text_widget.index(tk.SEL_FIRST)
            end = self.text_widget.index(tk.SEL_LAST)
        except tk.TclError:
            messagebox.showinfo("Selection Required")
            return
        color = colorchooser.askcolor(title="Choose text color")[1]
        if color:
            tag_name = f"custom_text_color_{self.text_color_tag_count}"
            self.text_color_tag_count += 1
            self.text_widget.tag_add(tag_name, start, end)
            self.text_widget.tag_configure(tag_name, foreground=color)

    def choose_bg_color(self):
        try:
            start = self.text_widget.index(tk.SEL_FIRST)
            end = self.text_widget.index(tk.SEL_LAST)
        except tk.TclError:
            messagebox.showinfo("Selection Required")
            return
        color = colorchooser.askcolor(title="Choose background color")[1]
        if color:
            tag_name = f"custom_bg_color_{self.bg_color_tag_count}"
            self.bg_color_tag_count += 1
            self.text_widget.tag_add(tag_name, start, end)
            self.text_widget.tag_configure(tag_name, background=color)

    def increase_selection_font_size(self):
        try:
            start = self.text_widget.index(tk.SEL_FIRST)
            end = self.text_widget.index(tk.SEL_LAST)
        except tk.TclError:
            messagebox.showinfo("Selection Required")
            return
        current_tags = self.text_widget.tag_names(start)
        current_size = None
        for tag in current_tags:
            if tag.startswith("sel_font_"):
                font_str = self.text_widget.tag_cget(tag, "font")
                parts = font_str.split()
                if len(parts) >= 2:
                    try:
                        current_size = int(parts[1])
                        break
                    except ValueError:
                        pass
        if current_size is None:
            current_size = self.font_size
        new_size = current_size + 2
        for tag in self.text_widget.tag_names():
            if tag.startswith("sel_font_"):
                self.text_widget.tag_remove(tag, start, end)
        tag_name = f"sel_font_{self.sel_font_tag_count}"
        self.sel_font_tag_count += 1
        self.text_widget.tag_add(tag_name, start, end)
        self.text_widget.tag_configure(tag_name, font=("Courier", new_size))

    def decrease_selection_font_size(self):
        try:
            start = self.text_widget.index(tk.SEL_FIRST)
            end = self.text_widget.index(tk.SEL_LAST)
        except tk.TclError:
            messagebox.showinfo("Selection Required")
            return
        current_tags = self.text_widget.tag_names(start)
        current_size = None
        for tag in current_tags:
            if tag.startswith("sel_font_"):
                font_str = self.text_widget.tag_cget(tag, "font")
                parts = font_str.split()
                if len(parts) >= 2:
                    try:
                        current_size = int(parts[1])
                        break
                    except ValueError:
                        pass
        if current_size is None:
            current_size = self.font_size
        new_size = current_size - 2 if current_size > 6 else current_size
        for tag in self.text_widget.tag_names():
            if tag.startswith("sel_font_"):
                self.text_widget.tag_remove(tag, start, end)
        tag_name = f"sel_font_{self.sel_font_tag_count}"
        self.sel_font_tag_count += 1
        self.text_widget.tag_add(tag_name, start, end)
        self.text_widget.tag_configure(tag_name, font=("Courier", new_size))

    def global_choose_text_color(self):
        color = colorchooser.askcolor(title="Choose Global Text Color")[1]
        if color:
            self.global_text_color = color
            self.update_fonts()

    def global_choose_bg_color(self):
        color = colorchooser.askcolor(title="Choose Global BG Color")[1]
        if color:
            self.global_bg_color = color
            self.update_fonts()

    def get_content(self):
        return self.text_widget.get("1.0", tk.END)

    def save_to_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".mk", filetypes=[("MK Files", "*.mk"), ("All Files", "*.*")]
        )
        if file_path:
            content = self.text_widget.get("1.0", "end-1c")
            # Collect tags data
            persistent_tags = []
            for tag in self.text_widget.tag_names():
                if (tag.startswith("custom_text_color_") or 
                    tag.startswith("custom_bg_color_") or 
                    tag.startswith("sel_font_")):
                    ranges = []
                    tag_ranges = self.text_widget.tag_ranges(tag)
                    for i in range(0, len(tag_ranges), 2):
                        start = str(tag_ranges[i])
                        end = str(tag_ranges[i+1])
                        ranges.append((start, end))
                    # Get configuration for options we care about
                    config = {}
                    for opt in ["foreground", "background", "font"]:
                        value = self.text_widget.tag_cget(tag, opt)
                        if value:
                            config[opt] = value
                    persistent_tags.append({"tag": tag, "ranges": ranges, "config": config})
            data = {
                "global": {
                    "font_size": self.font_size,
                    "global_text_color": self.global_text_color,
                    "global_bg_color": self.global_bg_color,
                },
                "content": content,
                "persistent_tags": persistent_tags,
            }
            try:
                with open(file_path, "w") as f:
                    json.dump(data, f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def load_from_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("MK Files", "*.mk"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                global_data = data.get("global", {})
                self.font_size = global_data.get("font_size", 12)
                self.global_text_color = global_data.get("global_text_color", "black")
                self.global_bg_color = global_data.get("global_bg_color", "white")
                self.update_fonts()
                self.text_widget.delete("1.0", tk.END)
                self.text_widget.insert("1.0", data.get("content", ""))
                self.highlight_syntax()
                self.update_line_numbers()
                # Reapply persistent tags
                for tag_data in data.get("persistent_tags", []):
                    tag = tag_data["tag"]
                    config = tag_data.get("config", {})
                    ranges = tag_data.get("ranges", [])
                    self.text_widget.tag_configure(tag, **config)
                    for (start, end) in ranges:
                        self.text_widget.tag_add(tag, start, end)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def open_file(self, file_path):
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
            global_data = data.get("global", {})
            self.font_size = global_data.get("font_size", 12)
            self.global_text_color = global_data.get("global_text_color", "black")
            self.global_bg_color = global_data.get("global_bg_color", "white")
            self.update_fonts()
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", data.get("content", ""))
            self.highlight_syntax()
            self.update_line_numbers()
            for tag_data in data.get("persistent_tags", []):
                tag = tag_data["tag"]
                config = tag_data.get("config", {})
                ranges = tag_data.get("ranges", [])
                self.text_widget.tag_configure(tag, **config)
                for (start, end) in ranges:
                    self.text_widget.tag_add(tag, start, end)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")

class Files(tk.Frame):
    def __init__(self, parent, root_dir=None, editor_callback=None):
        super().__init__(parent)
        self.root_dir = root_dir if root_dir else os.path.abspath(".")
        self.editor_callback = editor_callback  # callback to open file in editor
        self.init_ui()

    def init_ui(self):
        self.tree = ttk.Treeview(self)
        ysb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=ysb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        ysb.pack(side='right', fill='y')
        self.tree.heading("#0", text="SideBar - (sidebar)", anchor='w')
        abspath = os.path.abspath(self.root_dir)
        root_node = self.tree.insert('', 'end', text=abspath, open=True, values=[abspath])
        self.populate_tree(root_node, abspath)
        self.tree.bind('<<TreeviewOpen>>', self.on_open)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="New File", command=self.new_file)
        self.context_menu.add_command(label="New Folder", command=self.new_folder)
        self.context_menu.add_command(label="Rename", command=self.rename_item)
        self.context_menu.add_command(label="Delete", command=self.delete_item)

    def populate_tree(self, parent, fullpath):
        self.tree.delete(*self.tree.get_children(parent))
        try:
            for item in os.listdir(fullpath):
                item_fullpath = os.path.join(fullpath, item)
                isdir = os.path.isdir(item_fullpath)
                node = self.tree.insert(parent, 'end', text=item, values=[item_fullpath])
                if isdir:
                    self.tree.insert(node, 'end')
        except PermissionError:
            pass

    def on_open(self, event):
        node = self.tree.focus()
        fullpath = self.tree.item(node, "values")[0]
        if os.path.isdir(fullpath):
            self.populate_tree(node, fullpath)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def new_file(self):
        item = self.tree.focus()
        if not item:
            return
        fullpath = self.tree.item(item, "values")[0]
        if not os.path.isdir(fullpath):
            fullpath = os.path.dirname(fullpath)
        filename = simpledialog.askstring("New File")
        if filename:
            new_file_path = os.path.join(fullpath, filename)
            if os.path.exists(new_file_path):
                messagebox.showerror("Error", "File already exists!")
                return
            try:
                open(new_file_path, 'w').close()
                parent_item = self.tree.focus()
                if not os.path.isdir(self.tree.item(parent_item, "values")[0]):
                    parent_item = self.tree.parent(parent_item)
                self.populate_tree(parent_item, self.tree.item(parent_item, "values")[0])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create file: {e}")

    def new_folder(self):
        item = self.tree.focus()
        if not item:
            return
        fullpath = self.tree.item(item, "values")[0]
        if not os.path.isdir(fullpath):
            fullpath = os.path.dirname(fullpath)
        foldername = simpledialog.askstring("New Folder", "Enter new folder name:")
        if foldername:
            new_folder_path = os.path.join(fullpath, foldername)
            if os.path.exists(new_folder_path):
                messagebox.showerror("Error", "Folder already exists!")
                return
            try:
                os.mkdir(new_folder_path)
                parent_item = self.tree.focus()
                if not os.path.isdir(self.tree.item(parent_item, "values")[0]):
                    parent_item = self.tree.parent(parent_item)
                self.populate_tree(parent_item, self.tree.item(parent_item, "values")[0])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create folder: {e}")

    def rename_item(self):
        item = self.tree.focus()
        if not item:
            return
        fullpath = self.tree.item(item, "values")[0]
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=os.path.basename(fullpath))
        if new_name:
            new_path = os.path.join(os.path.dirname(fullpath), new_name)
            try:
                os.rename(fullpath, new_path)
                self.tree.item(item, text=new_name, values=[new_path])
                parent = self.tree.parent(item)
                if parent:
                    self.populate_tree(parent, self.tree.item(parent, "values")[0])
                else:
                    self.populate_tree(item, new_path)
            except Exception as e:
                messagebox.showerror("Error", f"Rename failed: {e}")

    def delete_item(self):
        item = self.tree.focus()
        if not item:
            return
        fullpath = self.tree.item(item, "values")[0]
        confirm = messagebox.askyesno("Delete", f"Are you sure you want to delete '{os.path.basename(fullpath)}'?")
        if confirm:
            try:
                if os.path.isdir(fullpath):
                    shutil.rmtree(fullpath)
                else:
                    os.remove(fullpath)
                parent = self.tree.parent(item)
                if parent:
                    self.populate_tree(parent, self.tree.item(parent, "values")[0])
            except Exception as e:
                messagebox.showerror("Error", f"Delete failed: {e}")

    def on_double_click(self, event):
        item = self.tree.focus()
        if not item:
            return
        fullpath = self.tree.item(item, "values")[0]
        if os.path.isfile(fullpath) and self.editor_callback:
            self.editor_callback(fullpath)
        elif os.path.isfile(fullpath):
            messagebox.showinfo("Open File", f"Open file: {fullpath}")

class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Notebook")
        self.geometry("1200x700")
        self.paned = tk.PanedWindow(self, orient='horizontal')
        self.paned.pack(fill='both', expand=True)
        self.file_explorer = Files(self.paned, root_dir=os.path.abspath("."), editor_callback=self.open_file_in_editor)
        self.paned.add(self.file_explorer, minsize=250)
        self.editor = Notebook(self.paned)
        self.paned.add(self.editor, minsize=500)

    def open_file_in_editor(self, file_path):
        self.editor.open_file(file_path)
# let's start this thing up (not my fault if ur computer blows up)
if __name__ == '__main__':
    app = Main()
    app.mainloop()
