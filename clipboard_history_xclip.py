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
    def __init__(self, max_items=50):
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

class ClipboardGUI:
    def __init__(self, clipboard_manager):
        self.clipboard_manager = clipboard_manager
        self.root = tk.Tk()
        self.root.title("Clipboard History")
        self.root.geometry("600x400")
        self.setup_ui()
        
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
            preview = item['preview'].replace('\n', '\\n').replace('\t', '\\t')
            display_text = f"[{timestamp}] {preview}"
            self.history_listbox.insert(tk.END, display_text)
    
    def copy_selected(self):
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            history = self.clipboard_manager.history
            if index < len(history):
                text = history[index]['content']
                if self.clipboard_manager.copy_to_clipboard(text):
                    messagebox.showinfo("Copied", "Text copied to clipboard!")
                else:
                    messagebox.showerror("Error", "Failed to copy to clipboard!")
    
    def on_double_click(self, event):
        self.copy_selected()
        self.root.quit()  # Close window after copying
    
    def on_arrow_key(self, event):
        """Handle Up/Down arrow keys for navigation."""
        current_selection = self.history_listbox.curselection()
        if not current_selection:
            # If nothing selected, select first item
            self.history_listbox.selection_set(0)
            self.history_listbox.activate(0)
            return

        current_index = current_selection[0]
        if event.keysym == 'Up' and current_index > 0:
            next_index = current_index - 1
        elif event.keysym == 'Down' and current_index < self.history_listbox.size() - 1:
            next_index = current_index + 1
        else:
            return  # Don't go out of bounds

        self.history_listbox.selection_clear(0, tk.END)
        self.history_listbox.selection_set(next_index)
        self.history_listbox.activate(next_index)
        self.history_listbox.see(next_index)  # Scroll to item if needed


    def on_enter_key(self, event):
        """Handle Enter key: copy selected and close."""
        self.copy_selected()
        self.root.quit()

    def clear_history(self):
        if messagebox.askyesno("Confirm", "Clear all clipboard history?"):
            self.clipboard_manager.history = []
            self.clipboard_manager.save_history()
        self.refresh_history()
    
    def run(self):
        self.root.mainloop()

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