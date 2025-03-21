import tkinter as tk
from tkinter import ttk
import json
import os

class LedgerManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # Colors and font
        self.bg_color = "#393e46"
        self.accent_color = "#03fff6"
        self.custom_font = ("MS Sans Serif", 10)
        self.configure(bg=self.bg_color)

        self.title("Ledger Manager")
        self.geometry("900x700")

        # Directory for ledger files
        self.ledger_dir = "ledgers"
        self.ensure_ledger_directory()
        
        # Data: mapping ledger names to a list of strings.
        # Each ledger must have at least 16 entries and at most 4096.
        self.data = {}
        self.load_ledgers()

        self.current_ledger = None  # Name of the currently selected ledger.
        self.current_entry_index = None  # Index of the entry (when editing) that is focused.
        self.entry_fields = []  # List of current Entry widgets (for non-global mode).

        self.create_widgets()

    def ensure_ledger_directory(self):
        if not os.path.exists(self.ledger_dir):
            os.makedirs(self.ledger_dir)

    def load_ledgers(self):
        # Load every ".ledger" file as a JSON list.
        for filename in os.listdir(self.ledger_dir):
            if filename.endswith(".ledger"):
                ledger_name = os.path.splitext(filename)[0]
                filepath = os.path.join(self.ledger_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        entries = json.load(f)
                    if not isinstance(entries, list):
                        entries = []
                    # Enforce minimum size of 16.
                    if len(entries) < 16:
                        entries += [""] * (16 - len(entries))
                    self.data[ledger_name] = entries
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    self.data[ledger_name] = ["" for _ in range(16)]
        if not self.data:
            # Create a default ledger if none exist.
            self.data["Default"] = ["" for _ in range(16)]

    def create_widgets(self):
        # --- Left Panel: Ledger Treeview and New Ledger ---
        self.left_frame = tk.Frame(self, bg=self.bg_color)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.tree = ttk.Treeview(self.left_frame, height=20)
        self.tree.heading("#0", text="Ledgers")
        self.tree.pack(fill=tk.Y, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_ledger_select)
        for ledger in self.data.keys():
            self.tree.insert("", tk.END, iid=ledger, text=ledger)
        
        new_ledger_frame = tk.Frame(self.left_frame, bg=self.bg_color)
        new_ledger_frame.pack(fill=tk.X, pady=5)
        tk.Label(new_ledger_frame, text="New Ledger:", bg=self.bg_color,
                 fg=self.accent_color, font=self.custom_font).pack(side=tk.LEFT)
        self.new_ledger_entry = tk.Entry(new_ledger_frame, font=self.custom_font,
                                         bg=self.bg_color, fg=self.accent_color,
                                         insertbackground=self.accent_color)
        self.new_ledger_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(new_ledger_frame, text="Add Ledger", command=self.add_ledger,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).pack(side=tk.LEFT, padx=5)

        # --- Right Panel: Search and Ledger Entries ---
        self.right_frame = tk.Frame(self, bg=self.bg_color)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Search area
        search_frame = tk.Frame(self.right_frame, bg=self.bg_color)
        search_frame.pack(fill=tk.X, pady=5)
        tk.Label(search_frame, text="Search:", bg=self.bg_color,
                 fg=self.accent_color, font=self.custom_font).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=self.custom_font, bg=self.bg_color,
                                     fg=self.accent_color, insertbackground=self.accent_color)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        self.global_search_var = tk.IntVar()
        self.global_search_cb = tk.Checkbutton(search_frame, text="Global",
                                                variable=self.global_search_var,
                                                command=self.on_search, bg=self.bg_color,
                                                fg=self.accent_color, selectcolor=self.bg_color,
                                                font=self.custom_font)
        self.global_search_cb.pack(side=tk.LEFT, padx=5)

        # Scrollable ledger entries area using a Canvas.
        self.canvas = tk.Canvas(self.right_frame, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.scrollbar = tk.Scrollbar(self.right_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.entries_inner_frame = tk.Frame(self.canvas, bg=self.bg_color)
        self.canvas.create_window((0, 0), window=self.entries_inner_frame, anchor="nw")
        self.entries_inner_frame.bind("<Configure>",
                                      lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # --- Controls for Ledger-Level Operations ---
        controls_frame = tk.Frame(self.right_frame, bg=self.bg_color)
        controls_frame.pack(fill=tk.X, pady=5)

        # (a) Move Ledger – moves entire contents of current ledger to selected ledger.
        move_frame = tk.Frame(controls_frame, bg=self.bg_color)
        move_frame.pack(fill=tk.X, pady=2)
        tk.Label(move_frame, text="Move Ledger to:", bg=self.bg_color,
                 fg=self.accent_color, font=self.custom_font).grid(row=0, column=0, sticky=tk.W, padx=2)
        self.move_to_ledger_var = tk.StringVar()
        self.move_to_ledger_combobox = ttk.Combobox(move_frame, textvariable=self.move_to_ledger_var,
                                                    state="readonly", font=self.custom_font)
        self.move_to_ledger_combobox.grid(row=0, column=1, padx=2, sticky=tk.EW)
        tk.Button(move_frame, text="Move Ledger", command=self.move_ledger,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).grid(row=0, column=2, padx=2)
        move_frame.columnconfigure(1, weight=1)

        # (b) Swap Ledgers – swaps the entire contents of the current ledger with a selected ledger.
        swap_frame = tk.Frame(controls_frame, bg=self.bg_color)
        swap_frame.pack(fill=tk.X, pady=2)
        tk.Label(swap_frame, text="Swap with Ledger:", bg=self.bg_color,
                 fg=self.accent_color, font=self.custom_font).grid(row=0, column=0, sticky=tk.W, padx=2)
        self.swap_ledger_var = tk.StringVar()
        self.swap_ledger_combobox = ttk.Combobox(swap_frame, textvariable=self.swap_ledger_var,
                                                 state="readonly", font=self.custom_font)
        self.swap_ledger_combobox.grid(row=0, column=1, padx=2, sticky=tk.EW)
        tk.Button(swap_frame, text="Swap Ledgers", command=self.swap_ledgers,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).grid(row=0, column=2, padx=2)
        swap_frame.columnconfigure(1, weight=1)

        # (c) Merge Ledgers – merges current ledger with a selected ledger.
        merge_frame = tk.Frame(controls_frame, bg=self.bg_color)
        merge_frame.pack(fill=tk.X, pady=2)
        tk.Label(merge_frame, text="Merge with Ledger:", bg=self.bg_color,
                 fg=self.accent_color, font=self.custom_font).grid(row=0, column=0, sticky=tk.W, padx=2)
        self.merge_ledger_var = tk.StringVar()
        self.merge_ledger_combobox = ttk.Combobox(merge_frame, textvariable=self.merge_ledger_var,
                                                  state="readonly", font=self.custom_font)
        self.merge_ledger_combobox.grid(row=0, column=1, padx=2, sticky=tk.EW)
        tk.Button(merge_frame, text="Merge Ledgers", command=self.merge_ledgers,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).grid(row=0, column=2, padx=2)
        merge_frame.columnconfigure(1, weight=1)

        # Additional actions: Clear the currently focused entry, Save current ledger, Save all ledgers.
        actions_frame = tk.Frame(controls_frame, bg=self.bg_color)
        actions_frame.pack(fill=tk.X, pady=2)
        tk.Button(actions_frame, text="Clear Entry", command=self.clear_entry,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).pack(side=tk.LEFT, padx=2)
        tk.Button(actions_frame, text="Save Ledger", command=self.save_ledger,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).pack(side=tk.LEFT, padx=2)
        tk.Button(actions_frame, text="Save All", command=self.save_all,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).pack(side=tk.LEFT, padx=2)

        # --- Status Bar ---
        self.status_label = tk.Label(self, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                     bg=self.bg_color, fg=self.accent_color, font=self.custom_font)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Initially select the default ledger.
        if "Default" in self.data:
            self.tree.selection_set("Default")
            self.on_ledger_select(None)
        else:
            first = list(self.data.keys())[0]
            self.tree.selection_set(first)
            self.on_ledger_select(None)

    def set_status(self, message, error=False):
        self.status_label.config(text=message, fg="red" if error else self.accent_color)

    def on_ledger_select(self, event):
        selected = self.tree.selection()
        if selected:
            ledger = selected[0]
            self.current_ledger = ledger
            self.update_ledger_entries()
            self.update_dropdowns()
            self.set_status(f"Selected ledger: {ledger}")

    def update_dropdowns(self):
        # Update all ledger-level operation dropdowns to list all ledgers except the current one.
        available = [l for l in self.data.keys() if l != self.current_ledger]
        self.move_to_ledger_combobox['values'] = available
        self.swap_ledger_combobox['values'] = available
        self.merge_ledger_combobox['values'] = available
        if available:
            self.move_to_ledger_var.set(available[0])
            self.swap_ledger_var.set(available[0])
            self.merge_ledger_var.set(available[0])
        else:
            self.move_to_ledger_var.set("")
            self.swap_ledger_var.set("")
            self.merge_ledger_var.set("")

    def update_ledger_entries(self):
        # Clear existing entry widgets.
        for widget in self.entries_inner_frame.winfo_children():
            widget.destroy()
        self.entry_fields = []
        query = self.search_var.get().lower()
        if self.global_search_var.get():
            # Global search: look through all ledgers.
            results = []
            for ledger, entries in self.data.items():
                for idx, text in enumerate(entries):
                    if query in text.lower():
                        results.append(f"[{ledger}] {idx+1:03d}: {text}")
            for i, res in enumerate(results):
                row = tk.Frame(self.entries_inner_frame, bg=self.bg_color)
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=f"{i+1:03d}:", bg=self.bg_color,
                         fg=self.accent_color, font=self.custom_font, width=4).pack(side=tk.LEFT)
                entry = tk.Entry(row, font=self.custom_font, bg=self.bg_color,
                                 fg=self.accent_color, state="disabled")
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                entry.insert(0, res)
                self.entry_fields.append(entry)
            self.set_status("Global search active")
        else:
            # Non-global mode: display all entries from the current ledger.
            if self.current_ledger:
                entries = self.data.get(self.current_ledger, [])
                for i, text in enumerate(entries):
                    row = tk.Frame(self.entries_inner_frame, bg=self.bg_color)
                    row.pack(fill=tk.X, pady=1)
                    tk.Label(row, text=f"{i+1:03d}:", bg=self.bg_color,
                             fg=self.accent_color, font=self.custom_font, width=4).pack(side=tk.LEFT)
                    entry = tk.Entry(row, font=self.custom_font, bg=self.bg_color,
                                     fg=self.accent_color, insertbackground=self.accent_color)
                    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    entry.insert(0, text)
                    # When an entry gets focus, record its index.
                    entry.bind("<FocusIn>", lambda event, idx=i: self.set_current_entry(idx))
                    # If a search query is active and this line matches, highlight it.
                    if query and query in text.lower():
                        entry.config(bg=self.accent_color)
                    else:
                        entry.config(bg=self.bg_color)
                    self.entry_fields.append(entry)
                self.set_status(f"Viewing ledger: {self.current_ledger}")

    def set_current_entry(self, idx):
        if not self.global_search_var.get():
            self.current_entry_index = idx

    def on_search(self, event=None):
        self.update_ledger_entries()

    # --- Ledger-Level Operations ---

    def move_ledger(self):
        # Moves the entire current ledger to the destination ledger (overwriting it)
        # and clears the current ledger.
        if not self.current_ledger:
            self.set_status("Select a ledger first", error=True)
            return
        dest = self.move_to_ledger_var.get()
        if not dest:
            self.set_status("Select a destination ledger", error=True)
            return
        self.data[dest] = self.data[self.current_ledger].copy()
        self.data[self.current_ledger] = ["" for _ in self.data[self.current_ledger]]
        self.update_ledger_entries()
        self.set_status(f"Ledger '{self.current_ledger}' moved to '{dest}' (destination overwritten)")

    def swap_ledgers(self):
        # Swaps the entire contents of the current ledger with the selected ledger.
        if not self.current_ledger:
            self.set_status("Select a ledger first", error=True)
            return
        dest = self.swap_ledger_var.get()
        if not dest:
            self.set_status("Select a ledger to swap with", error=True)
            return
        self.data[self.current_ledger], self.data[dest] = self.data[dest], self.data[self.current_ledger]
        self.update_ledger_entries()
        self.set_status(f"Ledger '{self.current_ledger}' swapped with '{dest}'")

    def merge_ledgers(self):
        # Merges the current ledger with the selected ledger.
        # The merged ledger (concatenation of both lists) is stored in the current ledger.
        if not self.current_ledger:
            self.set_status("Select a ledger first", error=True)
            return
        dest = self.merge_ledger_var.get()
        if not dest:
            self.set_status("Select a ledger to merge with", error=True)
            return
        merged = self.data[self.current_ledger] + self.data[dest]
        if len(merged) > 4096:
            self.set_status("Merged ledger exceeds maximum size (4096)", error=True)
            return
        # No special rounding is done; the new ledger size is the sum.
        self.data[self.current_ledger] = merged
        self.update_ledger_entries()
        self.set_status(f"Ledger '{self.current_ledger}' merged with '{dest}' (new size: {len(merged)})")

    def clear_entry(self):
        # Clears the currently focused entry in the current ledger.
        if self.global_search_var.get():
            self.set_status("Clearing entries not allowed in global search mode", error=True)
            return
        if self.current_ledger is None:
            self.set_status("Select a ledger first", error=True)
            return
        if self.current_entry_index is None:
            self.set_status("Focus an entry field first", error=True)
            return
        self.data[self.current_ledger][self.current_entry_index] = ""
        self.update_ledger_entries()
        self.set_status("Entry cleared")

    def add_ledger(self):
        ledger_name = self.new_ledger_entry.get().strip()
        if not ledger_name:
            self.set_status("Ledger name cannot be empty", error=True)
            return
        if ledger_name in self.data:
            self.set_status("Ledger already exists", error=True)
            return
        # New ledgers start with 16 blank entries.
        self.data[ledger_name] = ["" for _ in range(16)]
        self.tree.insert("", tk.END, iid=ledger_name, text=ledger_name)
        self.new_ledger_entry.delete(0, tk.END)
        self.set_status(f"Ledger '{ledger_name}' added")

    def save_ledger(self):
        if not self.current_ledger:
            self.set_status("Select a ledger first", error=True)
            return
        # In non-global mode, update the data from the entry widgets.
        if not self.global_search_var.get():
            new_entries = [entry.get() for entry in self.entry_fields]
            self.data[self.current_ledger] = new_entries
        filepath = os.path.join(self.ledger_dir, f"{self.current_ledger}.ledger")
        try:
            with open(filepath, "w") as f:
                json.dump(self.data[self.current_ledger], f, indent=4)
            self.set_status(f"Ledger '{self.current_ledger}' saved successfully")
        except Exception as e:
            self.set_status(f"Error saving ledger: {e}", error=True)

    def save_all(self):
        if not self.global_search_var.get() and self.current_ledger:
            new_entries = [entry.get() for entry in self.entry_fields]
            self.data[self.current_ledger] = new_entries
        errors = []
        for ledger, entries in self.data.items():
            filepath = os.path.join(self.ledger_dir, f"{ledger}.ledger")
            try:
                with open(filepath, "w") as f:
                    json.dump(entries, f, indent=4)
            except Exception as e:
                errors.append(f"{ledger}: {e}")
        if errors:
            self.set_status("Errors occurred: " + "; ".join(errors), error=True)
        else:
            self.set_status("All ledgers saved successfully")

if __name__ == "__main__":
    app = LedgerManagerApp()
    app.mainloop()
