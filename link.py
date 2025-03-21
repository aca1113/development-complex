import tkinter as tk
from tkinter import ttk
import json
import os
import webbrowser

class LinkManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # Define colors and font
        self.bg_color = "#393e46"
        self.accent_color = "#03fff6"
        self.custom_font = ("MS Sans Serif", 10)
        self.configure(bg=self.bg_color)

        self.title("Link Manager")
        self.geometry("900x700")
        
        # Data: sections mapped to a list of link dictionaries
        # Example: {"Default": [{"title": "Example", "url": "http://example.com"}]}
        self.data = {}
        self.links_dir = "links"
        self.ensure_links_directory()
        self.load_sections()
        self.current_section = None
        self.create_widgets()

    def ensure_links_directory(self):
        if not os.path.exists(self.links_dir):
            os.makedirs(self.links_dir)

    def load_sections(self):
        # Load .link files from the directory (each file represents a section)
        for filename in os.listdir(self.links_dir):
            if filename.endswith(".link"):
                section_name = os.path.splitext(filename)[0]
                filepath = os.path.join(self.links_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        links = json.load(f)
                    self.data[section_name] = links
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    self.data[section_name] = []
        if not self.data:
            # Create a default section if none exist
            self.data["Default"] = []

    def create_widgets(self):
        # Set up a ttk style for the Treeview using our color scheme and font
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("Treeview", 
                        background=self.bg_color, 
                        fieldbackground=self.bg_color, 
                        foreground=self.accent_color,
                        font=self.custom_font)
        style.configure("Treeview.Heading", 
                        background=self.accent_color, 
                        foreground=self.bg_color,
                        font=self.custom_font)

        # --- Left Frame: Sections Treeview and New Section Entry ---
        self.left_frame = tk.Frame(self, bg=self.bg_color)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.tree = ttk.Treeview(self.left_frame, height=20)
        self.tree.heading("#0", text="Sections")
        self.tree.pack(fill=tk.Y, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_section_select)
        for section in self.data.keys():
            self.tree.insert("", tk.END, iid=section, text=section)
        
        new_section_frame = tk.Frame(self.left_frame, bg=self.bg_color)
        new_section_frame.pack(fill=tk.X, pady=5)
        tk.Label(new_section_frame, text="New Section:", bg=self.bg_color, 
                 fg=self.accent_color, font=self.custom_font).pack(side=tk.LEFT)
        self.new_section_entry = tk.Entry(new_section_frame, font=self.custom_font, 
                                          bg=self.bg_color, fg=self.accent_color, insertbackground=self.accent_color)
        self.new_section_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(new_section_frame, text="Add Section", command=self.add_section,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).pack(side=tk.LEFT, padx=5)

        # --- Right Frame: Search, Listbox, and Controls ---
        self.right_frame = tk.Frame(self, bg=self.bg_color)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Search Frame
        search_frame = tk.Frame(self.right_frame, bg=self.bg_color)
        search_frame.pack(fill=tk.X, pady=5)
        tk.Label(search_frame, text="Search:", bg=self.bg_color, 
                 fg=self.accent_color, font=self.custom_font).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=self.custom_font, 
                                     bg=self.bg_color, fg=self.accent_color, insertbackground=self.accent_color)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        self.global_search_var = tk.IntVar()
        self.global_search_cb = tk.Checkbutton(search_frame, text="Global", variable=self.global_search_var,
                                                command=self.on_search, bg=self.bg_color, fg=self.accent_color,
                                                selectcolor=self.bg_color, font=self.custom_font)
        self.global_search_cb.pack(side=tk.LEFT, padx=5)

        # Listbox Frame (to display links)
        listbox_frame = tk.Frame(self.right_frame, bg=self.bg_color)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        self.links_listbox = tk.Listbox(listbox_frame, font=self.custom_font, 
                                        bg=self.bg_color, fg=self.accent_color, 
                                        selectbackground=self.accent_color, selectforeground=self.bg_color)
        self.links_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(listbox_frame, command=self.links_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.links_listbox.config(yscrollcommand=scrollbar.set)
        self.links_listbox.bind("<Double-Button-1>", self.open_link)

        # Controls for link operations
        controls_frame = tk.Frame(self.right_frame, bg=self.bg_color)
        controls_frame.pack(fill=tk.X, pady=5)

        # Add Link Controls (permanent input fields)
        add_link_frame = tk.Frame(controls_frame, bg=self.bg_color)
        add_link_frame.pack(fill=tk.X, pady=2)
        tk.Label(add_link_frame, text="Title:", bg=self.bg_color, 
                 fg=self.accent_color, font=self.custom_font).grid(row=0, column=0, sticky=tk.W, padx=2)
        self.title_entry = tk.Entry(add_link_frame, font=self.custom_font, 
                                    bg=self.bg_color, fg=self.accent_color, insertbackground=self.accent_color)
        self.title_entry.grid(row=0, column=1, padx=2, sticky=tk.EW)
        tk.Label(add_link_frame, text="URL:", bg=self.bg_color, 
                 fg=self.accent_color, font=self.custom_font).grid(row=0, column=2, sticky=tk.W, padx=2)
        self.url_entry = tk.Entry(add_link_frame, font=self.custom_font, 
                                  bg=self.bg_color, fg=self.accent_color, insertbackground=self.accent_color)
        self.url_entry.grid(row=0, column=3, padx=2, sticky=tk.EW)
        tk.Button(add_link_frame, text="Add Link", command=self.add_link,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).grid(row=0, column=4, padx=2)
        add_link_frame.columnconfigure(1, weight=1)
        add_link_frame.columnconfigure(3, weight=1)

        # Move Link Controls
        move_link_frame = tk.Frame(controls_frame, bg=self.bg_color)
        move_link_frame.pack(fill=tk.X, pady=2)
        tk.Label(move_link_frame, text="Move to:", bg=self.bg_color, 
                 fg=self.accent_color, font=self.custom_font).grid(row=0, column=0, sticky=tk.W, padx=2)
        self.move_to_var = tk.StringVar()
        self.move_to_combobox = ttk.Combobox(move_link_frame, textvariable=self.move_to_var, state="readonly",
                                             font=self.custom_font)
        self.move_to_combobox.grid(row=0, column=1, padx=2, sticky=tk.EW)
        tk.Button(move_link_frame, text="Move Link", command=self.move_link,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).grid(row=0, column=2, padx=2)
        move_link_frame.columnconfigure(1, weight=1)

        # Additional Actions: Delete, Open, Save Section, Save All
        actions_frame = tk.Frame(controls_frame, bg=self.bg_color)
        actions_frame.pack(fill=tk.X, pady=2)
        tk.Button(actions_frame, text="Delete Link", command=self.delete_link,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).pack(side=tk.LEFT, padx=2)
        tk.Button(actions_frame, text="Open Link", command=self.open_link,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).pack(side=tk.LEFT, padx=2)
        tk.Button(actions_frame, text="Save Section", command=self.save_section,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).pack(side=tk.LEFT, padx=2)
        tk.Button(actions_frame, text="Save All", command=self.save_all,
                  bg=self.accent_color, fg=self.bg_color, font=self.custom_font, bd=0).pack(side=tk.LEFT, padx=2)

        # --- Status Bar ---
        self.status_label = tk.Label(self, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                     bg=self.bg_color, fg=self.accent_color, font=self.custom_font)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Initially select the default (or first available) section
        if "Default" in self.data:
            self.tree.selection_set("Default")
            self.on_section_select(None)
        else:
            first_section = list(self.data.keys())[0]
            self.tree.selection_set(first_section)
            self.on_section_select(None)

    def set_status(self, message, error=False):
        self.status_label.config(text=message, fg="red" if error else self.accent_color)

    def on_section_select(self, event):
        selected = self.tree.selection()
        if selected:
            section = selected[0]
            self.current_section = section
            self.show_links(section)
            # Update the move-to dropdown to show sections other than the current one
            available_sections = [sec for sec in self.data.keys() if sec != section]
            self.move_to_combobox['values'] = available_sections
            if available_sections:
                self.move_to_var.set(available_sections[0])
            else:
                self.move_to_var.set("")
            self.set_status(f"Selected section: {section}")

    def show_links(self, section):
        self.links_listbox.delete(0, tk.END)
        links = self.data.get(section, [])
        query = self.search_var.get().lower()
        for link in links:
            display_text = f"{link.get('title', link.get('url', ''))} - {link.get('url', '')}"
            # If a search query exists, show only matching links
            if query:
                if query in link.get('title','').lower() or query in link.get('url','').lower():
                    self.links_listbox.insert(tk.END, display_text)
            else:
                self.links_listbox.insert(tk.END, display_text)

    def on_search(self, event=None):
        query = self.search_var.get().lower()
        self.links_listbox.delete(0, tk.END)
        if self.global_search_var.get():
            for section, links in self.data.items():
                for link in links:
                    if query in link.get('title','').lower() or query in link.get('url','').lower():
                        display_text = f"[{section}] {link.get('title', link.get('url',''))} - {link.get('url','')}"
                        self.links_listbox.insert(tk.END, display_text)
            self.set_status("Global search active")
        else:
            if self.current_section:
                self.show_links(self.current_section)
                self.set_status(f"Searching in section: {self.current_section}")
            else:
                self.set_status("No section selected", error=True)

    def add_link(self):
        if not self.current_section:
            self.set_status("Select a section first", error=True)
            return
        title = self.title_entry.get().strip()
        url = self.url_entry.get().strip()
        if not title or not url:
            self.set_status("Both title and URL are required", error=True)
            return
        new_link = {"title": title, "url": url}
        self.data[self.current_section].append(new_link)
        self.title_entry.delete(0, tk.END)
        self.url_entry.delete(0, tk.END)
        self.show_links(self.current_section)
        self.set_status("Link added successfully")

    def delete_link(self):
        if not self.current_section:
            self.set_status("Select a section first", error=True)
            return
        selection = self.links_listbox.curselection()
        if not selection:
            self.set_status("Select a link to delete", error=True)
            return
        index = selection[0]
        if self.global_search_var.get():
            self.set_status("Deletion not supported in global search mode. Uncheck Global.", error=True)
            return
        try:
            del self.data[self.current_section][index]
            self.show_links(self.current_section)
            self.set_status("Link deleted")
        except Exception as e:
            self.set_status(f"Error deleting link: {str(e)}", error=True)

    def open_link(self, event=None):
        if not self.current_section:
            self.set_status("Select a section first", error=True)
            return
        selection = self.links_listbox.curselection()
        if not selection:
            self.set_status("Select a link to open", error=True)
            return
        index = selection[0]
        # In global search mode, extract the URL from the display text.
        if self.global_search_var.get():
            text = self.links_listbox.get(index)
            parts = text.split(" - ")
            if len(parts) < 2:
                self.set_status("Invalid link format", error=True)
                return
            url = parts[-1]
        else:
            link = self.data[self.current_section][index]
            url = link.get("url")
        if url:
            webbrowser.open(url)
            self.set_status(f"Opening: {url}")
        else:
            self.set_status("No URL found", error=True)

    def move_link(self):
        if not self.current_section:
            self.set_status("Select a section first", error=True)
            return
        selection = self.links_listbox.curselection()
        if not selection:
            self.set_status("Select a link to move", error=True)
            return
        dest_section = self.move_to_var.get()
        if not dest_section:
            self.set_status("Select a destination section", error=True)
            return
        index = selection[0]
        if self.global_search_var.get():
            self.set_status("Moving links is not supported in global search mode. Uncheck Global.", error=True)
            return
        try:
            link = self.data[self.current_section].pop(index)
            self.data[dest_section].append(link)
            self.show_links(self.current_section)
            self.set_status(f"Link moved to section: {dest_section}")
        except Exception as e:
            self.set_status(f"Error moving link: {str(e)}", error=True)

    def add_section(self):
        section_name = self.new_section_entry.get().strip()
        if not section_name:
            self.set_status("Section name cannot be empty", error=True)
            return
        if section_name in self.data:
            self.set_status("Section already exists", error=True)
            return
        self.data[section_name] = []
        self.tree.insert("", tk.END, iid=section_name, text=section_name)
        self.new_section_entry.delete(0, tk.END)
        self.set_status(f"Section '{section_name}' added")

    def save_section(self):
        if not self.current_section:
            self.set_status("Select a section first", error=True)
            return
        section = self.current_section
        filepath = os.path.join(self.links_dir, f"{section}.link")
        try:
            with open(filepath, 'w') as f:
                json.dump(self.data[section], f, indent=4)
            self.set_status(f"Section '{section}' saved successfully")
        except Exception as e:
            self.set_status(f"Error saving section: {str(e)}", error=True)

    def save_all(self):
        errors = []
        for section, links in self.data.items():
            filepath = os.path.join(self.links_dir, f"{section}.link")
            try:
                with open(filepath, 'w') as f:
                    json.dump(links, f, indent=4)
            except Exception as e:
                errors.append(f"{section}: {str(e)}")
        if errors:
            self.set_status("Errors occurred: " + "; ".join(errors), error=True)
        else:
            self.set_status("All sections saved successfully")

if __name__ == "__main__":
    app = LinkManagerApp()
    app.mainloop()
