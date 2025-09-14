#!/usr/bin/env python3
"""
Linux Clipboard History Manager
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox



class ClipboardHistory:
    def __init__(self, max_items=100):
        self.max_items = max_items
        self.history_file = Path.home() / '.clipboard_history.json'
        self.history = self.load_history()
        self.last_clipboard = ""
        
    def load_history(self):
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
        return []
    
    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def get_clipboard(self):
        try:
            result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], 
                                  capture_output=True, text=True, timeout=5)
            return result.stdout if result.returncode == 0 else ""
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            return ""
    
    def set_clipboard(self, text):
        try:
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                     stdin=subprocess.PIPE, text=True)
            process.communicate(input=text, timeout=5)
            return process.returncode == 0
        except Exception as e:
            print(f"Error setting clipboard: {e}")
            return False
    
    def add_to_history(self, text):
        if not text or text == self.last_clipboard:
            return
            
        # Skip very large content
        if len(text) > 1024 * 1024:
            print("Skipping very large clipboard content")
            return
            
        # Remove if already exists
        self.history = [item for item in self.history if item['content'] != text]
        
        # Add to beginning
        new_item = {
            'content': text,
            'timestamp': datetime.now().isoformat(),
            'preview': text[:100] + ('...' if len(text) > 100 else '')
        }
        self.history.insert(0, new_item)
        
        # Keep only max_items
        if len(self.history) > self.max_items:
            self.history = self.history[:self.max_items]
            
        self.save_history()
        self.last_clipboard = text
    
    def monitor_clipboard(self):
        print("Clipboard monitoring started. Press Ctrl+C to stop.")
        try:
            self.last_clipboard = self.get_clipboard()
            
            while True:
                try:
                    current_clipboard = self.get_clipboard()
                    if current_clipboard != self.last_clipboard:
                        self.add_to_history(current_clipboard)
                        print(f"Added to history: {current_clipboard[:50]}...")
                    time.sleep(1)
                except Exception as e:
                    print(f"Error monitoring clipboard: {e}")
                    time.sleep(5)
        except KeyboardInterrupt:
            print("\nClipboard monitoring stopped.")
    
    def copy_to_clipboard(self, text):
        if self.set_clipboard(text):
            self.last_clipboard = text
            return True
        return False



def check_appearance():
    """Checks if macOS is in dark mode."""
    cmd = 'defaults read -g AppleInterfaceStyle'
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, shell=True)
    return bool(p.communicate()[0])  # True if Dark Mode, False if Light

def apply_theme(style, dark_mode, listbox):
    """Apply light/dark theme without changing base theme (macOS safe)."""
    if dark_mode:
        bg = "#2B2B2B"
        fg = "white"
        btn_bg = "#3C3C3C"
        btn_fg = "white"
        active_bg = "#505050"
    else:
        bg = "white"
        fg = "black"
        btn_bg = "#E0E0E0"
        btn_fg = "black"
        active_bg = "#C0C0C0"

    # ttk styles
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background=btn_bg, foreground=btn_fg)
    style.map("TButton", background=[("active", active_bg)])

    # Plain tk widgets (like Listbox) must be colored manually
    listbox.configure(bg=bg, fg=fg, selectbackground=active_bg, selectforeground=fg)


class ClipboardGUI:
    def __init__(self, clipboard_manager):
        self.clipboard_manager = clipboard_manager
        self.root = tk.Tk()
        self.root.geometry("600x400")
        
        # Capture the ID of the window that launched the GUI
        self.previous_window_id = self.get_active_window_id()
        dark = check_appearance()
        #apply_theme(self.style, dark, self.history_listbox)
        self.setup_ui()
        
    def get_active_window_id(self):
        try:
            result = subprocess.run(['xdotool', 'getactivewindow'], 
                                    capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            print(f"Error getting active window ID: {e}")
            return None

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Clipboard History", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # History listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.history_listbox = tk.Listbox(list_frame, font=('Courier', 10))
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", 
                                 command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.history_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0))
        
        ttk.Button(button_frame, text="Copy Selected", 
                  command=self.copy_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Refresh", 
                  command=self.refresh_history).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear History", 
                  command=self.clear_history).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Close", 
                  command=self.root.quit).pack(side=tk.LEFT)
        
        # Bind keyboard navigation
        self.history_listbox.bind('<Up>', self.on_arrow_key)
        self.history_listbox.bind('<Down>', self.on_arrow_key)
        self.history_listbox.bind('<Return>', self.on_enter_key)
        self.history_listbox.bind('<Escape>', lambda e: self.root.quit())

        # Set focus to listbox so keys work immediately
        self.history_listbox.focus_set()
        
        # Load initial history
        self.refresh_history()


    def refresh_history(self):
        self.history_listbox.delete(0, tk.END)
        history = self.clipboard_manager.history

        for i, item in enumerate(history):
            timestamp = datetime.fromisoformat(item['timestamp']).strftime('%H:%M:%S')
            
            # Clean and truncate to single line
            content = item['content']
            # Replace newlines, returns, tabs with spaces
            content_clean = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            # Collapse multiple spaces into single space
            content_clean = ' '.join(content_clean.split())
            # Truncate to 80 characters, keep beginning
            if len(content_clean) > 80:
                preview = content_clean[:77] + "..."
            else:
                preview = content_clean

            display_text = f"[{timestamp}] {preview}"
            # Ensure no newlines sneak in (final safety)
            display_text = display_text.replace('\n', ' ').replace('\r', '')
            self.history_listbox.insert(tk.END, display_text)

        # Auto-select first item if any exist
        if self.history_listbox.size() > 0:
            self.history_listbox.selection_set(0)
            self.history_listbox.activate(0)
            self.history_listbox.see(0)
            self.history_listbox.focus_set()
     
    def copy_selected(self):
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            history = self.clipboard_manager.history
            if index < len(history):
                text = history[index]['content']
    
    def on_double_click(self, event):
        self.copy_selected()
        self.root.after(50, self._simulate_paste)
        self.root.quit()
    
    def on_arrow_key(self, event):
        """Handle Up/Down arrow keys for navigation."""
        current_active = self.history_listbox.winfo_parent().selection_includes()
        if not current_active:
            # If nothing is active, activate the first item
            if self.history_listbox.size() > 0:
                self.history_listbox.selection_set(0)
                self.history_listbox.activate(0)
                self.history_listbox.see(0)
            return

        current_index = self.history_listbox.index(current_active)
        next_index = current_index

        if event.keysym == 'Up':
            next_index = max(0, current_index - 1)
        elif event.keysym == 'Down':
            next_index = min(self.history_listbox.size() - 1, current_index + 1)
        
        # Clear the entire selection first to be safe
        self.history_listbox.selection_clear(0, tk.END)
        # Set the new selection and activate the same item
        self.history_listbox.selection_set(next_index)
        self.history_listbox.activate(next_index)
        self.history_listbox.see(next_index)  # Ensure the new selection is visible

    def on_enter_key(self, event):
        selection = self.history_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.clipboard_manager.history):
            return
        text = self.clipboard_manager.history[index]['content']
        self.clipboard_manager.set_clipboard(text)  # Sets the clipboard content
        
        # Give the system a moment to register the new clipboard content
        self.root.after(500, self._simulate_paste)
        
        # Close the GUI window immediately after the command is queued
        self.root.quit()

    def _simulate_paste(self):
        try:
            if self.previous_window_id:
                # Switch focus back to the original window
                subprocess.run(['xdotool', 'windowactivate', '--sync', self.previous_window_id], check=True)
            
            # Now, simulate the paste command
            # Use Ctrl+Shift+V for most terminals, or Shift+Insert as an alternative
            subprocess.run(['xdotool', 'key', 'ctrl+shift+v'], check=True)
        except Exception as e:
            print(f"Failed to paste: {e}")

    def clear_history(self):
        if messagebox.askyesno("Confirm", "Clear all clipboard history?"):
            self.clipboard_manager.history = []
            self.clipboard_manager.save_history()
        self.refresh_history()
    
    def run(self):
        # After window is shown, force focus
        self.root.after(100, self._grab_focus)
        self.root.mainloop()

    def _grab_focus(self):
        """Force focus on window and listbox after GUI is visible."""
        self.root.focus_force()  # Force focus on window
        self.history_listbox.focus_set()  # Focus on listbox
        # Ensure first item is selected (in case refresh happened before focus)
        if self.history_listbox.size() > 0:
            self.history_listbox.selection_set(0)
            self.history_listbox.activate(0)
            self.history_listbox.see(0)


def main():
    parser = argparse.ArgumentParser(description='Linux Clipboard History Manager')
    parser.add_argument('--daemon', action='store_true', 
                       help='Run as background daemon')
    parser.add_argument('--gui', action='store_true', 
                       help='Show GUI history browser')
    parser.add_argument('--list', action='store_true', 
                       help='List clipboard history in terminal')
    parser.add_argument('--max-items', type=int, default=50,
                       help='Maximum number of items to keep (default: 50)')
    
    args = parser.parse_args()
    
    # Check if xclip is available
    try:
        subprocess.run(['xclip', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: xclip is not installed or not in PATH")
        print("Please install it with: sudo apt install xclip")
        sys.exit(1)
    
    clipboard_manager = ClipboardHistory(max_items=args.max_items)
    
    if args.daemon:
        clipboard_manager.monitor_clipboard()
    elif args.gui:
        gui = ClipboardGUI(clipboard_manager)
        gui.run()
    elif args.list:
        history = clipboard_manager.history
        if not history:
            print("No clipboard history found.")
        else:
            print(f"Clipboard History ({len(history)} items):")
            print("-" * 50)
            for i, item in enumerate(history, 1):
                timestamp = datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                print(f"{i}. [{timestamp}] {item['preview']}")
                print()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()