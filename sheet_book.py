import os
import json
import tkinter as tk
from tkinter import ttk, simpledialog

# Standard A4 dimensions in landscape mode (in pixels)
PAGE_WIDTH = 900
PAGE_HEIGHT = 595

class sheet_book:
    def __init__(self, master):
        self.master = master
        self.master.title("sheet_book")
        
        # Table dimensions (number of rows and columns)
        self.rows = 15
        self.columns = 10
        
        # Pages: each page is a 2D list (table) of cell strings
        self.pages = [self.create_empty_table()]
        self.current_page = 0
        
        self.current_file = None  # Currently loaded file
        
        # For inline cell editing
        self.current_cell_entry = None
        self.current_cell_position = None  # (row, col)
        self.current_cell_window = None
        
        # The folder for saving files
        self.sheet_folder = "sheet_folder"
        if not os.path.exists(self.sheet_folder):
            os.makedirs(self.sheet_folder)
        
        # Layout: left frame (file explorer), right frame (toolbar + pages)
        self.left_frame = tk.Frame(master, width=200)
        self.left_frame.pack(side="left", fill="y")
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side="right", fill="both", expand=True)
        
        # File explorer (Treeview)
        self.tree = ttk.Treeview(self.left_frame, columns=("Name"), show="tree")
        self.tree.pack(fill="both", expand=True)
        self.update_tree()
        self.tree.bind("<Button-3>", self.show_file_context_menu)
        
        # Context menu for file operations
        self.file_menu = tk.Menu(master, tearoff=0)
        self.file_menu.add_command(label="New Table", command=self.new_table)
        self.file_menu.add_command(label="Save Table", command=self.save_table)
        self.file_menu.add_command(label="Load Table", command=self.load_table)
        self.file_menu.add_command(label="Delete Table", command=self.delete_table)
        self.file_menu.add_command(label="Rename Table", command=self.rename_table)
        
        # Toolbar (page navigation buttons)
        self.toolbar = tk.Frame(self.right_frame, bd=1, relief="raised")
        self.toolbar.pack(side="top", fill="x")
        
        self.prev_page_btn = tk.Button(self.toolbar, text="Previous Page", command=self.prev_page)
        self.prev_page_btn.pack(side="left", padx=2, pady=2)
        self.page_label = tk.Label(self.toolbar, text=f"Page: {self.current_page+1}/{len(self.pages)}")
        self.page_label.pack(side="left", padx=2, pady=2)
        self.next_page_btn = tk.Button(self.toolbar, text="Next Page", command=self.next_page)
        self.next_page_btn.pack(side="left", padx=2, pady=2)
        self.add_page_btn = tk.Button(self.toolbar, text="Add Page", command=self.add_page)
        self.add_page_btn.pack(side="left", padx=2, pady=2)
        self.delete_page_btn = tk.Button(self.toolbar, text="Delete Page", command=self.delete_page)
        self.delete_page_btn.pack(side="left", padx=2, pady=2)
        
        # Canvas with vertical scrollbar for table pages
        self.canvas_frame = tk.Frame(self.right_frame)
        self.canvas_frame.pack(fill="both", expand=True)
        
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical")
        self.v_scrollbar.pack(side="right", fill="y")
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", width=PAGE_WIDTH, height=PAGE_HEIGHT,
                                yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.v_scrollbar.config(command=self.canvas.yview)
        
        self.canvas.config(scrollregion=(0, 0, PAGE_WIDTH, PAGE_HEIGHT))
        
        # Bind a click event on the canvas to enable cell editing.
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Draw the current page (table)
        self.load_current_page()
    
    def create_empty_table(self):
        """Creates an empty table (2D list) with self.rows rows and self.columns columns."""
        return [["" for _ in range(self.columns)] for _ in range(self.rows)]
    
    def draw_table(self):
        """Clears the canvas and draws the grid and cell contents for the current page."""
        self.canvas.delete("all")
        cell_width = PAGE_WIDTH / self.columns
        cell_height = PAGE_HEIGHT / self.rows
        
        # Draw vertical grid lines
        for i in range(self.columns + 1):
            x = i * cell_width
            self.canvas.create_line(x, 0, x, PAGE_HEIGHT, fill="black")
        # Draw horizontal grid lines
        for j in range(self.rows + 1):
            y = j * cell_height
            self.canvas.create_line(0, y, PAGE_WIDTH, y, fill="black")
        
        # Draw cell contents (if any)
        table = self.pages[self.current_page]
        for r in range(self.rows):
            for c in range(self.columns):
                text = table[r][c]
                if text:
                    self.canvas.create_text(c * cell_width + 5, r * cell_height + 5,
                                            text=text, anchor="nw", font=("Arial", 12))
    
    def on_canvas_click(self, event):
        """Handles canvas clicks by opening an entry widget for the clicked cell.
           If an entry is already open, it is committed first."""
        if self.current_cell_entry:
            self.commit_cell_edit()
        cell_width = PAGE_WIDTH / self.columns
        cell_height = PAGE_HEIGHT / self.rows
        col = int(event.x / cell_width)
        row = int(event.y / cell_height)
        if row < self.rows and col < self.columns:
            self.edit_cell(row, col, col * cell_width, row * cell_height, cell_width, cell_height)
    
    def edit_cell(self, row, col, x, y, cell_width, cell_height):
        """Creates an Entry widget overlay for editing a cell."""
        self.current_cell_position = (row, col)
        current_text = self.pages[self.current_page][row][col]
        self.current_cell_entry = tk.Entry(self.canvas, font=("Arial", 12))
        self.current_cell_entry.insert(0, current_text)
        self.current_cell_entry.focus_set()
        self.current_cell_window = self.canvas.create_window(x, y, anchor="nw",
                                                             window=self.current_cell_entry,
                                                             width=cell_width, height=cell_height)
        self.current_cell_entry.bind("<Return>", self.on_cell_edit)
        # Removed the <FocusOut> binding to prevent the entry from disappearing immediately.
    
    def on_cell_edit(self, event):
        self.commit_cell_edit()
    
    def commit_cell_edit(self):
        """Stores the edited cell data and redraws the table."""
        if not self.current_cell_entry:
            return
        row, col = self.current_cell_position
        new_text = self.current_cell_entry.get()
        self.pages[self.current_page][row][col] = new_text
        self.canvas.delete(self.current_cell_window)
        self.current_cell_entry = None
        self.current_cell_position = None
        self.current_cell_window = None
        self.draw_table()
    
    def load_current_page(self):
        """Loads and draws the current page."""
        self.draw_table()
        self.canvas.config(scrollregion=(0, 0, PAGE_WIDTH, PAGE_HEIGHT))
    
    def update_page_label(self):
        self.page_label.config(text=f"Page: {self.current_page+1}/{len(self.pages)}")
    
    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.load_current_page()
            self.update_page_label()
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_current_page()
            self.update_page_label()
    
    def add_page(self):
        self.pages.append(self.create_empty_table())
        self.current_page = len(self.pages) - 1
        self.load_current_page()
        self.update_page_label()
    
    def delete_page(self):
        if len(self.pages) > 1:
            del self.pages[self.current_page]
            if self.current_page >= len(self.pages):
                self.current_page = len(self.pages) - 1
            self.load_current_page()
            self.update_page_label()
    
    # --------------------------
    # File Explorer and Operations
    # --------------------------
    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        # List files ending with .sheet_book
        for f in os.listdir(self.sheet_folder):
            if f.endswith(".sheet_book"):
                self.tree.insert("", "end", iid=f, text=f)
    
    def show_file_context_menu(self, event):
        try:
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
            self.file_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.file_menu.grab_release()
    
    def new_table(self):
        self.pages = [self.create_empty_table()]
        self.current_page = 0
        self.load_current_page()
        self.update_page_label()
        self.current_file = None
    
    def save_table(self):
        # If no filename is set, ask for one.
        if not self.current_file:
            filename = simpledialog.askstring("Save Table", "Enter file name (without extension):")
            if not filename:
                return
            if not filename.endswith(".sheet_book"):
                filename += ".sheet_book"
            self.current_file = filename
        path = os.path.join(self.sheet_folder, self.current_file)
        data = {"pages": self.pages, "rows": self.rows, "columns": self.columns}
        with open(path, "w") as f:
            json.dump(data, f)
        self.update_tree()
    
    def load_table(self):
        selection = self.tree.selection()
        if not selection:
            return
        filename = selection[0]
        path = os.path.join(self.sheet_folder, filename)
        with open(path, "r") as f:
            data = json.load(f)
        self.pages = data.get("pages", [self.create_empty_table()])
        self.rows = data.get("rows", self.rows)
        self.columns = data.get("columns", self.columns)
        self.current_page = 0
        self.load_current_page()
        self.update_page_label()
        self.current_file = filename
    
    def delete_table(self):
        selection = self.tree.selection()
        if not selection:
            return
        filename = selection[0]
        path = os.path.join(self.sheet_folder, filename)
        os.remove(path)
        self.update_tree()
    
    def rename_table(self):
        selection = self.tree.selection()
        if not selection:
            return
        old_filename = selection[0]
        new_name = simpledialog.askstring("Rename Table", "Enter new file name (without extension):")
        if not new_name:
            return
        if not new_name.endswith(".sheet_book"):
            new_name += ".sheet_book"
        old_path = os.path.join(self.sheet_folder, old_filename)
        new_path = os.path.join(self.sheet_folder, new_name)
        try:
            os.rename(old_path, new_path)
            if self.current_file == old_filename:
                self.current_file = new_name
            self.update_tree()
        except Exception as e:
            print("Rename error:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = sheet_book(root)
    root.mainloop()
