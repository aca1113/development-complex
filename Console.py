import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
import subprocess
import os
import shutil
import datetime
from tkinter.scrolledtext import ScrolledText

# Set the console directory to the Desktop path
CONSOLE_DIR = r"C:\Users\ajerkov\Desktop"
if not os.path.exists(CONSOLE_DIR):
    os.makedirs(CONSOLE_DIR)

class ConsoleTab(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.current_dir = os.getcwd()
        self.command_history = []
        self.history_index = -1
        self.prompt = "Console>_ "  # Console prompt
        self.font = ('DejaVu Sans Mono', 10)

        # Create text area for console output
        self.text_area = ScrolledText(
            self, wrap=tk.WORD, bg='black', fg='white',
            insertbackground='white', font=self.font, relief=tk.FLAT
        )
        self.text_area.pack(expand=True, fill=tk.BOTH)

        # Insert initial prompt
        self.text_area.insert(tk.END, self.prompt, 'prompt')
        self.text_area.mark_set(tk.INSERT, tk.END)
        self.text_area.focus_set()

        # Configure tags
        self.text_area.tag_config('prompt', foreground='#00FF00')
        self.text_area.tag_config('output', foreground='white')
        self.text_area.tag_config('error', foreground='red')

        # Bind keys
        self.text_area.bind('<Return>', self.execute_command)
        self.text_area.bind('<Up>', self.history_up)
        self.text_area.bind('<Down>', self.history_down)
        self.text_area.bind('<Key>', self.restrict_editing)
        self.text_area.bind('<Button-1>', self.restrict_click)

        # Set initial input position
        self.input_start = self.text_area.index(tk.INSERT)

    def restrict_editing(self, event):
        # Prevent editing before prompt
        cursor_pos = self.text_area.index(tk.INSERT)
        if self.text_area.compare(cursor_pos, '<', self.input_start):
            self.text_area.mark_set(tk.INSERT, tk.END)
            return 'break'
        # Handle backspace at prompt start
        if event.keysym == 'BackSpace':
            if self.text_area.compare(tk.INSERT, '==', self.input_start):
                return 'break'

    def restrict_click(self, event):
        # Prevent clicking before prompt
        click_pos = self.text_area.index(f'@{event.x},{event.y}')
        if self.text_area.compare(click_pos, '<', self.input_start):
            self.text_area.mark_set(tk.INSERT, tk.END)
            return 'break'

    def execute_command(self, event):
        # Get the command from input line
        command = self.text_area.get(self.input_start, tk.END).strip()
        self.text_area.insert(tk.END, '\n')

        if command:
            self.command_history.append(command)
            self.history_index = len(self.command_history)

            # Handle custom commands
            if command == 'help':
                self.display_help()
            elif command.startswith('cd '):
                self.change_directory(command)
            elif command == 'clear':
                self.clear_screen()
            elif command == 'list':
                self.list_files()
            elif command == 'time':
                self.display_time()
            elif command == 'date':
                self.display_date()
            elif command.startswith('mkdir '):
                self.create_directory(command)
            elif command.startswith('rmdir '):
                self.remove_directory(command)
            elif command.startswith('touch '):
                self.create_file(command)
            elif command.startswith('rm '):
                self.remove_file(command)
            elif command.startswith('copy '):
                self.copy_file(command)
            elif command.startswith('move '):
                self.move_file(command)
            elif command == 'pwd':
                self.display_current_directory()
            elif command == 'whoami':
                self.display_username()
            elif command == 'exit':
                self.master.master.destroy()
            elif command == 'save':
                self.save_contents()
            elif command == 'load':
                self.load_contents()
            elif command == 'history':
                self.display_history()
            elif command.startswith('calc'):
                self.calculate_expression(command)
            elif command == 'size':
                self.display_directory_size()
            elif command.startswith('find'):
                self.find_files(command)
            else:
                # Execute system command
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        cwd=self.current_dir
                    )
                    output = result.stdout + result.stderr
                    self.display_output(output)
                except Exception as e:
                    self.display_output(str(e), 'error')

        # Update prompt
        self.text_area.insert(tk.END, self.prompt, 'prompt')
        self.input_start = self.text_area.index(tk.END)
        self.text_area.see(tk.END)
        return 'break'

    def display_output(self, message, tag='output'):
        self.text_area.insert(tk.END, message, tag)

    def display_help(self):
        help_text = """
        Available Commands:
        - help: Show this help menu
        - cd <directory>: Change directory
        - clear: Clear the console screen
        - list: List files in the current directory
        - time: Display current time
        - date: Display current date
        - mkdir <name>: Create a directory
        - rmdir <name>: Remove a directory
        - touch <name>: Create a file
        - rm <name>: Remove a file
        - copy <src> <dest>: Copy a file
        - move <src> <dest>: Move a file
        - pwd: Display current directory
        - whoami: Display current user
        - exit: Close the console
        - save: Save console contents to a file
        - load: Load console contents from a file
        - history: Display command history
        - calc <expression>: Perform a calculation
        - size: Display size of current directory
        - find <pattern>: Search for files matching a pattern
        """
        self.display_output(help_text, 'output')

    def change_directory(self, command):
        try:
            new_dir = command.split(' ', 1)[1].strip()
            os.chdir(new_dir)
            self.current_dir = os.getcwd()
        except Exception as e:
            self.display_output(str(e), 'error')

    def clear_screen(self):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, self.prompt, 'prompt')
        self.input_start = self.text_area.index(tk.END)

    def list_files(self):
        try:
            files = os.listdir(self.current_dir)
            self.display_output('\n'.join(files) + '\n', 'output')
        except Exception as e:
            self.display_output(str(e), 'error')

    def display_time(self):
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.display_output(f"Current time: {current_time}\n", 'output')

    def display_date(self):
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.display_output(f"Current date: {current_date}\n", 'output')

    def create_directory(self, command):
        try:
            dir_name = command.split(' ', 1)[1].strip()
            os.mkdir(dir_name)
            self.display_output(f"Directory '{dir_name}' created.\n", 'output')
        except Exception as e:
            self.display_output(str(e), 'error')

    def remove_directory(self, command):
        try:
            dir_name = command.split(' ', 1)[1].strip()
            os.rmdir(dir_name)
            self.display_output(f"Directory '{dir_name}' removed.\n", 'output')
        except Exception as e:
            self.display_output(str(e), 'error')

    def create_file(self, command):
        try:
            file_name = command.split(' ', 1)[1].strip()
            open(file_name, 'a').close()
            self.display_output(f"File '{file_name}' created.\n", 'output')
        except Exception as e:
            self.display_output(str(e), 'error')

    def remove_file(self, command):
        try:
            file_name = command.split(' ', 1)[1].strip()
            os.remove(file_name)
            self.display_output(f"File '{file_name}' removed.\n", 'output')
        except Exception as e:
            self.display_output(str(e), 'error')

    def copy_file(self, command):
        try:
            src, dest = command.split(' ', 2)[1:]
            shutil.copy(src, dest)
            self.display_output(f"File '{src}' copied to '{dest}'.\n", 'output')
        except Exception as e:
            self.display_output(str(e), 'error')

    def move_file(self, command):
        try:
            src, dest = command.split(' ', 2)[1:]
            shutil.move(src, dest)
            self.display_output(f"File '{src}' moved to '{dest}'.\n", 'output')
        except Exception as e:
            self.display_output(str(e), 'error')

    def display_current_directory(self):
        self.display_output(f"{self.current_dir}\n", 'output')

    def display_username(self):
        self.display_output(f"{os.getlogin()}\n", 'output')

    def save_contents(self):
        file_path = filedialog.asksaveasfilename(
            initialdir=CONSOLE_DIR,
            defaultextension=".console",
            filetypes=[("Console Files", "*.console"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(self.text_area.get(1.0, tk.END))
                self.display_output(f"Contents saved to {file_path}\n", 'output')
            except Exception as e:
                self.display_output(f"Error saving file: {str(e)}\n", 'error')

    def load_contents(self):
        file_path = filedialog.askopenfilename(
            initialdir=CONSOLE_DIR,
            filetypes=[("Console Files", "*.console"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    contents = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, contents)
                self.text_area.see(tk.END)
                self.display_output(f"Contents loaded from {file_path}\n", 'output')
            except Exception as e:
                self.display_output(f"Error loading file: {str(e)}\n", 'error')

    def display_history(self):
        history = '\n'.join(self.command_history)
        self.display_output(f"Command History:\n{history}\n", 'output')

    def calculate_expression(self, command):
        try:
            expr = command.split(' ', 1)[1].strip()
            result = eval(expr)
            self.display_output(f"Result: {result}\n", 'output')
        except Exception as e:
            self.display_output(f"Error calculating expression: {str(e)}\n", 'error')

    def display_directory_size(self):
        try:
            total_size = sum(os.path.getsize(os.path.join(self.current_dir, f))
                             for f in os.listdir(self.current_dir)
                             if os.path.isfile(os.path.join(self.current_dir, f)))
            self.display_output(f"Directory size: {total_size} bytes\n", 'output')
        except Exception as e:
            self.display_output(str(e), 'error')

    def find_files(self, command):
        try:
            pattern = command.split(' ', 1)[1].strip()
            files = [f for f in os.listdir(self.current_dir) if pattern in f]
            self.display_output('\n'.join(files) + '\n', 'output')
        except Exception as e:
            self.display_output(str(e), 'error')

    def history_up(self, event):
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.text_area.delete(self.input_start, tk.END)
            self.text_area.insert(tk.END, self.command_history[self.history_index])
        return "break"

    def history_down(self, event):
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.text_area.delete(self.input_start, tk.END)
            self.text_area.insert(tk.END, self.command_history[self.history_index])
        else:
            self.text_area.delete(self.input_start, tk.END)
            self.history_index = len(self.command_history)
        return "break"

class ConsoleApp:
    def __init__(self, root):
        self.root = root
        # Change window title to "console" (all lowercase)
        self.root.title("console")
        self.root.configure(bg='black')

        self.toolbar = tk.Frame(self.root, bg='grey')
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.save_button = tk.Button(self.toolbar, text="Save", command=self.save_current_tab)
        self.save_button.pack(side=tk.LEFT, padx=2, pady=2)

        self.load_button = tk.Button(self.toolbar, text="Load", command=self.load_current_tab)
        self.load_button.pack(side=tk.LEFT, padx=2, pady=2)

        self.new_tab_button = tk.Button(self.toolbar, text="+", command=self.add_tab)
        self.new_tab_button.pack(side=tk.LEFT, padx=2, pady=2)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        # Add initial console tab with default name "console 1"
        self.add_tab()

    def add_tab(self):
        tab = ConsoleTab(self.notebook)
        default_title = f"console {self.notebook.index('end') + 1}"
        self.notebook.add(tab, text=default_title)
        self.notebook.select(tab)

    def save_current_tab(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        current_tab.save_contents()

    def load_current_tab(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        current_tab.load_contents()

if __name__ == '__main__':
    root = tk.Tk()
    app = ConsoleApp(root)
    root.mainloop()
