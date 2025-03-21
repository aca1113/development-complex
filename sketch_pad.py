import os
import json
import tkinter as tk
from tkinter import ttk, colorchooser, simpledialog

# Standard A4 dimensions in landscape mode (in pixels)
PAGE_WIDTH = 900
PAGE_HEIGHT = 595

class SketchPad:
    def __init__(self, master):
        self.master = master
        self.master.title("Sketch Pad")

        # Default tool settings
        self.current_tool = "pencil"
        self.pen_color = "#000000"    # black
        self.fill_color = ""          # no fill
        self.pen_width = 2

        # For object IDs and undo/redo stacks
        self.object_counter = 0
        # Each page holds a list of drawn objects
        self.pages = [[]]  # start with one blank page
        self.current_page = 0
        # Undo/redo stacks; each element is a dict with keys: action ("add" or "delete"), object, index
        self.undo_stack = [[]]  # per page
        self.redo_stack = [[]]  # per page

        # Drawing state variables
        self.current_object = None  # for pencil, line preview, etc.
        self.preview_id = None      # for shape preview
        self.start_x = None
        self.start_y = None

        # For inline text editing, we no longer restrict to one at a time.
        # Temporary storage for a text box in creation:
        self.current_text_entry = None
        self.current_text_frame = None

        # the sketch folder
        self.sketch_dir = "sketch_folder"
        if not os.path.exists(self.sketch_dir):
            os.makedirs(self.sketch_dir)

        # Layout: left frame: file explorer, right frame: toolbar + pages
        self.left_frame = tk.Frame(master, width=200)
        self.left_frame.pack(side="left", fill="y")
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side="right", fill="both", expand=True)

        # File explorer (Treeview)
        self.tree = ttk.Treeview(self.left_frame, columns=("Name"), show="tree")
        self.tree.pack(fill="both", expand=True)
        self.update_tree()
        self.tree.bind("<Button-3>", self.show_file_context_menu)

        # context menu 
        self.file_menu = tk.Menu(master, tearoff=0)
        self.file_menu.add_command(label="New Drawing", command=self.new_drawing)
        self.file_menu.add_command(label="Save Drawing", command=self.save_drawing)
        self.file_menu.add_command(label="Load Drawing", command=self.load_drawing)
        self.file_menu.add_command(label="Delete Drawing", command=self.delete_drawing)
        self.file_menu.add_command(label="Rename Drawing", command=self.rename_drawing)

        # Toolbar
        self.toolbar = tk.Frame(self.right_frame, bd=1, relief="raised")
        self.toolbar.pack(side="top", fill="x")

        # Tool selection buttons
        self.pencil_btn = tk.Button(self.toolbar, text="Pencil", command=lambda: self.select_tool("pencil"))
        self.pencil_btn.pack(side="left", padx=2, pady=2)
        self.line_btn = tk.Button(self.toolbar, text="Line", command=lambda: self.select_tool("line"))
        self.line_btn.pack(side="left", padx=2, pady=2)
        self.rect_btn = tk.Button(self.toolbar, text="Rectangle", command=lambda: self.select_tool("rectangle"))
        self.rect_btn.pack(side="left", padx=2, pady=2)
        self.oval_btn = tk.Button(self.toolbar, text="Oval", command=lambda: self.select_tool("oval"))
        self.oval_btn.pack(side="left", padx=2, pady=2)
        self.text_btn = tk.Button(self.toolbar, text="Text", command=lambda: self.select_tool("text"))
        self.text_btn.pack(side="left", padx=2, pady=2)
        self.delete_btn = tk.Button(self.toolbar, text="Delete", command=lambda: self.select_tool("delete"))
        self.delete_btn.pack(side="left", padx=2, pady=2)

        # Color selection buttons
        self.pen_color_btn = tk.Button(self.toolbar, text="Pen Color", command=self.choose_pen_color)
        self.pen_color_btn.pack(side="left", padx=2, pady=2)
        self.fill_color_btn = tk.Button(self.toolbar, text="Fill Color", command=self.choose_fill_color)
        self.fill_color_btn.pack(side="left", padx=2, pady=2)

        # Pen width slider
        self.width_slider = tk.Scale(self.toolbar, from_=1, to=10, orient="horizontal",
                                     label="Width", command=self.change_width)
        self.width_slider.set(self.pen_width)
        self.width_slider.pack(side="left", padx=2, pady=2)

        # Undo / Redo buttons
        self.undo_btn = tk.Button(self.toolbar, text="Undo", command=self.undo)
        self.undo_btn.pack(side="left", padx=2, pady=2)
        self.redo_btn = tk.Button(self.toolbar, text="Redo", command=self.redo)
        self.redo_btn.pack(side="left", padx=2, pady=2)

        # Page navigation
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

        # Sketch pad with vertical scrollbar
        self.canvas_frame = tk.Frame(self.right_frame)
        self.canvas_frame.pack(fill="both", expand=True)

        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical")
        self.v_scrollbar.pack(side="right", fill="y")

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", width=PAGE_WIDTH, height=PAGE_HEIGHT,
                                yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.v_scrollbar.config(command=self.canvas.yview)

        # Set scroll region to match the page size
        self.canvas.config(scrollregion=(0, 0, PAGE_WIDTH, PAGE_HEIGHT))

        # Draw a border representing the page boundary
        self.canvas.create_rectangle(0, 0, PAGE_WIDTH, PAGE_HEIGHT, outline="gray", tags="page_border")

        # Bind canvas events
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        # For deletion (when delete tool is active)
        self.canvas.bind("<Button-1>", self.on_canvas_click, add="+")

    # --------------------------
    # Tool & Color Functions
    # --------------------------
    def select_tool(self, tool):
        self.current_tool = tool

    def choose_pen_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.pen_color = color

    def choose_fill_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.fill_color = color

    def change_width(self, val):
        self.pen_width = int(val)

    # --------------------------
    # Page Management Functions
    # --------------------------
    def update_page_label(self):
        self.page_label.config(text=f"Page: {self.current_page+1}/{len(self.pages)}")

    def redraw_page_border(self):
        self.canvas.delete("page_border")
        self.canvas.create_rectangle(0, 0, PAGE_WIDTH, PAGE_HEIGHT, outline="gray", tags="page_border")

    def load_current_page(self):
        self.canvas.delete("all")
        self.redraw_page_border()
        self.canvas.config(scrollregion=(0, 0, PAGE_WIDTH, PAGE_HEIGHT))
        self.redraw_objects()

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
        self.pages.append([])
        self.undo_stack.append([])
        self.redo_stack.append([])
        self.current_page = len(self.pages) - 1
        self.load_current_page()
        self.update_page_label()

    def delete_page(self):
        if len(self.pages) > 1:
            del self.pages[self.current_page]
            del self.undo_stack[self.current_page]
            del self.redo_stack[self.current_page]
            if self.current_page >= len(self.pages):
                self.current_page = len(self.pages) - 1
            self.load_current_page()
            self.update_page_label()

    # --------------------------
    # Drawing Helpers
    # --------------------------
    def get_new_object_id(self):
        oid = self.object_counter
        self.object_counter += 1
        return oid

    def add_action(self, action_type, obj, index=None):
        # Record an action for undo/redo.
        if index is None:
            index = len(self.pages[self.current_page])
        self.undo_stack[self.current_page].append({"action": action_type, "object": obj, "index": index})
        self.redo_stack[self.current_page].clear()

    def draw_object(self, obj):
        # Draw an object based on its type and store its canvas item ids.
        cid_list = []
        tag = f"obj_{obj['id']}"
        if obj["type"] == "pencil":
            cid = self.canvas.create_line(*sum(obj["points"], []),
                                          fill=obj["color"], width=obj["width"],
                                          capstyle="round", smooth=True, tags=("drawable", tag))
            cid_list.append(cid)
        elif obj["type"] in ("rectangle", "oval"):
            if obj["type"] == "rectangle":
                cid = self.canvas.create_rectangle(
                    *obj["start"], *obj["end"],
                    outline=obj["outline"], width=obj["width"], fill=obj["fill"],
                    tags=("drawable", tag))
            else:
                cid = self.canvas.create_oval(
                    *obj["start"], *obj["end"],
                    outline=obj["outline"], width=obj["width"], fill=obj["fill"],
                    tags=("drawable", tag))
            cid_list.append(cid)
        elif obj["type"] == "line":
            cid = self.canvas.create_line(
                *obj["start"], *obj["end"],
                fill=obj["color"], width=obj["width"], tags=("drawable", tag))
            cid_list.append(cid)
        elif obj["type"] == "text":
            # For text objects, we create a resizable frame with a Text widget and a resize handle.
            frame = tk.Frame(self.canvas, bd=1, relief="solid")
            text_widget = tk.Text(frame, width=obj.get("width_chars", 20), height=obj.get("height_lines", 2),
                                  font=("Arial", 16), wrap="word", fg=obj["fill"])
            text_widget.insert("1.0", obj["text"])
            text_widget.pack(fill="both", expand=True)
            # Create a resize handle (a small label in the bottom-right)
            handle = tk.Label(frame, text="⇲", cursor="size_nw_se")
            handle.place(relx=1.0, rely=1.0, anchor="se")
            # Bind mouse events to resize the frame.
            handle.bind("<ButtonPress-1>", lambda e, fr=frame: self.start_resize(e, fr))
            handle.bind("<B1-Motion>", lambda e, fr=frame: self.perform_resize(e, fr))
            win_id = self.canvas.create_window(obj["position"][0], obj["position"][1],
                                               window=frame, anchor="nw", tags=("drawable", tag))
            cid_list.append(win_id)
            # Save reference to the widget in the object for later editing if needed.
            obj["widget"] = frame
        obj["canvas_ids"] = cid_list

    def redraw_objects(self):
        for obj in self.pages[self.current_page]:
            self.draw_object(obj)

    def clear_canvas(self):
        self.canvas.delete("all")
        self.redraw_page_border()

    # --------------------------
    # Resize Text Box Handlers
    # --------------------------
    def start_resize(self, event, frame):
        frame._resize_start_width = frame.winfo_width()
        frame._resize_start_height = frame.winfo_height()
        frame._resize_start_x = event.x_root
        frame._resize_start_y = event.y_root

    def perform_resize(self, event, frame):
        dx = event.x_root - frame._resize_start_x
        dy = event.y_root - frame._resize_start_y
        new_width = max(50, frame._resize_start_width + dx)
        new_height = max(20, frame._resize_start_height + dy)
        frame.config(width=new_width, height=new_height)

    # --------------------------
    # Canvas Event Handlers
    # --------------------------
    def on_canvas_press(self, event):
        self.start_x, self.start_y = event.x, event.y

        if self.current_tool == "pencil":
            # Start a new pencil stroke: record starting point and create an item for preview.
            obj = {
                "id": self.get_new_object_id(),
                "type": "pencil",
                "points": [[event.x, event.y]],
                "color": self.pen_color,
                "width": self.pen_width
            }
            self.current_object = obj
            # Create a temporary line item:
            cid = self.canvas.create_line(event.x, event.y, event.x, event.y,
                                          fill=self.pen_color, width=self.pen_width,
                                          capstyle="round", smooth=True, tags="preview")
            self.current_object["canvas_ids"] = [cid]

        elif self.current_tool == "line":
            # For straight line tool
            obj = {
                "id": self.get_new_object_id(),
                "type": "line",
                "start": [event.x, event.y],
                "end": [event.x, event.y],
                "color": self.pen_color,
                "width": self.pen_width
            }
            self.current_object = obj
            cid = self.canvas.create_line(event.x, event.y, event.x, event.y,
                                          fill=self.pen_color, width=self.pen_width,
                                          tags="preview")
            self.current_object["canvas_ids"] = [cid]

        elif self.current_tool in ("rectangle", "oval"):
            # Prepare for shape preview
            self.preview_id = None

        elif self.current_tool == "text":
            # Immediately create a text entry (resizable) at the clicked position.
            self.create_text_entry(event.x, event.y)

    def on_canvas_drag(self, event):
        if self.current_tool == "pencil" and self.current_object:
            # Update pencil stroke: add new point and update the preview line.
            self.current_object["points"].append([event.x, event.y])
            # Update preview: remove old preview and create a new one.
            for cid in self.current_object.get("canvas_ids", []):
                self.canvas.delete(cid)
            cid = self.canvas.create_line(*sum(self.current_object["points"], []),
                                          fill=self.pen_color, width=self.pen_width,
                                          capstyle="round", smooth=True, tags="preview")
            self.current_object["canvas_ids"] = [cid]

        elif self.current_tool == "line" and self.current_object:
            # Update line preview
            self.current_object["end"] = [event.x, event.y]
            for cid in self.current_object.get("canvas_ids", []):
                self.canvas.delete(cid)
            cid = self.canvas.create_line(self.start_x, self.start_y, event.x, event.y,
                                          fill=self.pen_color, width=self.pen_width,
                                          tags="preview")
            self.current_object["canvas_ids"] = [cid]

        elif self.current_tool in ("rectangle", "oval"):
            if self.preview_id:
                self.canvas.delete(self.preview_id)
            if self.current_tool == "rectangle":
                self.preview_id = self.canvas.create_rectangle(
                    self.start_x, self.start_y, event.x, event.y,
                    outline=self.pen_color, width=self.pen_width, fill=self.fill_color, tags="preview")
            elif self.current_tool == "oval":
                self.preview_id = self.canvas.create_oval(
                    self.start_x, self.start_y, event.x, event.y,
                    outline=self.pen_color, width=self.pen_width, fill=self.fill_color, tags="preview")

    def on_canvas_release(self, event):
        if self.current_tool == "pencil" and self.current_object:
            # Finalize pencil stroke: remove preview tag and add object to page.
            for cid in self.current_object.get("canvas_ids", []):
                self.canvas.delete(cid)
            self.add_object(self.current_object)
            self.current_object = None
            self.canvas.delete("preview")

        elif self.current_tool == "line" and self.current_object:
            for cid in self.current_object.get("canvas_ids", []):
                self.canvas.delete(cid)
            self.current_object["end"] = [event.x, event.y]
            self.add_object(self.current_object)
            self.current_object = None
            self.canvas.delete("preview")

        elif self.current_tool in ("rectangle", "oval"):
            if self.preview_id:
                self.canvas.delete(self.preview_id)
                self.preview_id = None
            if self.current_tool == "rectangle":
                obj = {
                    "id": self.get_new_object_id(),
                    "type": "rectangle",
                    "start": [self.start_x, self.start_y],
                    "end": [event.x, event.y],
                    "outline": self.pen_color,
                    "width": self.pen_width,
                    "fill": self.fill_color
                }
            else:
                obj = {
                    "id": self.get_new_object_id(),
                    "type": "oval",
                    "start": [self.start_x, self.start_y],
                    "end": [event.x, event.y],
                    "outline": self.pen_color,
                    "width": self.pen_width,
                    "fill": self.fill_color
                }
            self.add_object(obj)

    def on_canvas_click(self, event):
        # If delete tool is active, try to delete the clicked object.
        if self.current_tool == "delete":
            items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            for item in items:
                tags = self.canvas.gettags(item)
                # Look for a tag that starts with "obj_"
                obj_tags = [t for t in tags if t.startswith("obj_")]
                if obj_tags:
                    obj_tag = obj_tags[0]
                    # Find and remove the corresponding object from the page.
                    for idx, obj in enumerate(self.pages[self.current_page]):
                        if f"obj_{obj['id']}" == obj_tag:
                            self.remove_object(idx)
                            return

    # --------------------------
    # Object Management, Undo/Redo
    # --------------------------
    def add_object(self, obj):
        self.pages[self.current_page].append(obj)
        self.add_action("add", obj)
        self.draw_object(obj)

    def remove_object(self, idx):
        # Remove object from canvas and record deletion for undo.
        obj = self.pages[self.current_page].pop(idx)
        # Delete its canvas items.
        if "canvas_ids" in obj:
            for cid in obj["canvas_ids"]:
                self.canvas.delete(cid)
        # If it is a text widget, also destroy its frame.
        if obj["type"] == "text" and "widget" in obj:
            obj["widget"].destroy()
        self.add_action("delete", obj, index=idx)

    def undo(self):
        if not self.undo_stack[self.current_page]:
            return
        action = self.undo_stack[self.current_page].pop()
        if action["action"] == "add":
            # Undo addition: remove object.
            # Find object in pages list.
            for idx, obj in enumerate(self.pages[self.current_page]):
                if obj["id"] == action["object"]["id"]:
                    self.pages[self.current_page].pop(idx)
                    if "canvas_ids" in obj:
                        for cid in obj["canvas_ids"]:
                            self.canvas.delete(cid)
                    if obj["type"] == "text" and "widget" in obj:
                        obj["widget"].destroy()
                    break
            # Record in redo stack.
            self.redo_stack[self.current_page].append(action)
        elif action["action"] == "delete":
            # Undo deletion: re-add the object at the recorded index.
            self.pages[self.current_page].insert(action["index"], action["object"])
            self.draw_object(action["object"])
            self.redo_stack[self.current_page].append(action)

    def redo(self):
        if not self.redo_stack[self.current_page]:
            return
        action = self.redo_stack[self.current_page].pop()
        if action["action"] == "add":
            # Redo addition: re-add the object.
            self.pages[self.current_page].append(action["object"])
            self.draw_object(action["object"])
            self.undo_stack[self.current_page].append(action)
        elif action["action"] == "delete":
            # Redo deletion: remove the object.
            for idx, obj in enumerate(self.pages[self.current_page]):
                if obj["id"] == action["object"]["id"]:
                    self.pages[self.current_page].pop(idx)
                    if "canvas_ids" in obj:
                        for cid in obj["canvas_ids"]:
                            self.canvas.delete(cid)
                    if obj["type"] == "text" and "widget" in obj:
                        obj["widget"].destroy()
                    break
            self.undo_stack[self.current_page].append(action)

    # --------------------------
    # Inline Text Editing with Resizable Text Box
    # --------------------------
    def create_text_entry(self, x, y):
        # Create a small frame that holds a Text widget and a resize handle.
        frame = tk.Frame(self.canvas, bd=1, relief="solid")
        text_widget = tk.Text(frame, width=20, height=2, font=("Arial", 16), wrap="word", fg=self.pen_color)
        text_widget.pack(fill="both", expand=True)
        handle = tk.Label(frame, text="⇲", cursor="size_nw_se")
        handle.place(relx=1.0, rely=1.0, anchor="se")
        handle.bind("<ButtonPress-1>", lambda e, fr=frame: self.start_resize(e, fr))
        handle.bind("<B1-Motion>", lambda e, fr=frame: self.perform_resize(e, fr))
        # Create a canvas window for the text frame.
        win_id = self.canvas.create_window(x, y, window=frame, anchor="nw", tags="preview")
        # Focus on the text widget.
        text_widget.focus_set()
        # When the user presses Return or the widget loses focus, finalize the text box.
        text_widget.bind("<Return>", lambda e: self.finish_text_entry(frame, text_widget, win_id))
        text_widget.bind("<FocusOut>", lambda e: self.finish_text_entry(frame, text_widget, win_id))
        # We do not restrict multiple text entries.
    
    def finish_text_entry(self, frame, text_widget, win_id):
        # Finalize the text entry: if text is entered, create a permanent text object.
        text = text_widget.get("1.0", "end-1c")
        # Remove the preview widget.
        self.canvas.delete(win_id)
        frame.destroy()
        if text.strip():
            obj = {
                "id": self.get_new_object_id(),
                "type": "text",
                "position": [self.start_x, self.start_y],
                "text": text,
                "fill": self.pen_color,
                "width_chars": 20,
                "height_lines": 2
            }
            self.add_object(obj)

    # --------------------------
    # File Explorer and Operations
    # --------------------------
    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        # List files ending with .sketch
        for f in os.listdir(self.sketch_dir):
            if f.endswith(".sketch"):
                self.tree.insert("", "end", iid=f, text=f)

    def show_file_context_menu(self, event):
        try:
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
            self.file_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.file_menu.grab_release()

    def new_drawing(self):
        self.canvas.delete("all")
        self.pages = [[]]
        self.undo_stack = [[]]
        self.redo_stack = [[]]
        self.current_page = 0
        self.load_current_page()
        self.update_page_label()

    def save_drawing(self):
        # If no filename is set, ask for one.
        if not hasattr(self, "current_file") or not self.current_file:
            filename = simpledialog.askstring("Save Drawing", "Enter file name (without extension):")
            if not filename:
                return
            if not filename.endswith(".sketch"):
                filename += ".sketch"
            self.current_file = filename
        path = os.path.join(self.sketch_dir, self.current_file)
        # We only save the raw object data (without canvas ids or widget references).
        def clean_obj(obj):
            new_obj = obj.copy()
            new_obj.pop("canvas_ids", None)
            new_obj.pop("widget", None)
            return new_obj
        data = {"pages": [[clean_obj(o) for o in page] for page in self.pages]}
        with open(path, "w") as f:
            json.dump(data, f)
        self.update_tree()

    def load_drawing(self):
        selection = self.tree.selection()
        if not selection:
            return
        filename = selection[0]
        path = os.path.join(self.sketch_dir, filename)
        with open(path, "r") as f:
            data = json.load(f)
        self.canvas.delete("all")
        self.pages = data.get("pages", [[]])
        # Reset undo/redo stacks
        self.undo_stack = [[] for _ in self.pages]
        self.redo_stack = [[] for _ in self.pages]
        self.current_page = 0
        self.load_current_page()
        self.update_page_label()
        self.current_file = filename

    def delete_drawing(self):
        selection = self.tree.selection()
        if not selection:
            return
        filename = selection[0]
        path = os.path.join(self.sketch_dir, filename)
        os.remove(path)
        self.update_tree()

    def rename_drawing(self):
        selection = self.tree.selection()
        if not selection:
            return
        old_filename = selection[0]
        new_name = simpledialog.askstring("Rename Drawing", "Enter new file name (without extension):")
        if not new_name:
            return
        if not new_name.endswith(".sketch"):
            new_name += ".sketch"
        old_path = os.path.join(self.sketch_dir, old_filename)
        new_path = os.path.join(self.sketch_dir, new_name)
        try:
            os.rename(old_path, new_path)
            if hasattr(self, "current_file") and self.current_file == old_filename:
                self.current_file = new_name
            self.update_tree()
        except Exception as e:
            print("Rename error:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = SketchPad(root)
    root.mainloop()
