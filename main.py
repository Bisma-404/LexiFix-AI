import tkinter as tk
from tkinter import scrolledtext, messagebox, Frame, Label, Button
import google.generativeai as genai
import os
import threading
from dotenv import load_dotenv
from PIL import Image, ImageTk
import difflib
import re

load_dotenv()

class LexiFixSpellChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("LexiFix - AI Spell and Grammar Checker")
        
        window_width = 1000
        window_height = 770
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.configure(bg="#7e57c2")
        
        self.bg_color = "#ffffff"
        self.text_color = "#333333"
        self.primary_color = "#7e57c2"
        self.header_color = "#7e57c2"
        self.button_color = "#7e57c2"
        self.error_underline = "#ff4444"
        
        self.model = None
        self.initialize_gemini()
        
        self.logo_img = None
        try:
            img = Image.open("lexifix_logo.png")
            img = img.resize((90, 90), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Could not load logo image: {e}")
        
        self.setup_ui()

    def initialize_gemini(self):
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                messagebox.showwarning("API Key Missing", "Please set GEMINI_API_KEY in .env file")
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to initialize Gemini: {str(e)}")

    def setup_ui(self):
        main_frame = Frame(self.root, bg=self.header_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header = Frame(main_frame, bg=self.header_color, pady=15)
        header.pack(fill=tk.X)
        
        title_container = Frame(header, bg=self.header_color)
        title_container.pack(expand=True)
        
        if self.logo_img:
            logo_label = Label(title_container, image=self.logo_img, bg=self.header_color)
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_frame = Frame(title_container, bg=self.header_color)
        title_frame.pack(side=tk.LEFT)
        
        Label(title_frame, text="LexiFix", font=("Segoe UI", 24, "bold"), bg=self.header_color, fg="white").pack(anchor='w')
        Label(title_frame, text="AI Spell and Grammar Checker", font=("Segoe UI", 12), bg=self.header_color, fg="white").pack(anchor='w')
        
        content_frame = Frame(main_frame, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        input_frame = Frame(content_frame, bg="white", padx=15, pady=15)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        Label(input_frame, text="Original Text:", font=("Segoe UI", 10, "bold"), bg="white", fg="#333333").pack(anchor="w")
        
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 12),
            bg=self.bg_color,
            fg=self.text_color,
            padx=15,
            pady=15,
            height=9,
            bd=1,
            highlightthickness=1,
            highlightbackground="#e0e0e0",
            relief=tk.FLAT
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.input_text.tag_config("error", underline=True, underlinefg=self.error_underline)
        
        btn_frame = Frame(input_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.check_btn = Button(btn_frame,
                              text="Check & Correct Text",
                              command=self.check_spelling,
                              bg=self.button_color,
                              fg="white",
                              font=("Segoe UI", 10, "bold"),
                              bd=0,
                              padx=20,
                              pady=8,
                              relief=tk.FLAT)
        self.check_btn.pack(side=tk.RIGHT)
        
        separator = Frame(content_frame, bg=self.header_color, height=10)
        separator.pack(fill=tk.X)
        
        output_frame = Frame(content_frame, bg="white", padx=15, pady=15)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        Label(output_frame, text="Corrected Text:", font=("Segoe UI", 10, "bold"), bg="white", fg="#333333").pack(anchor="w")
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 12),
            bg=self.bg_color,
            fg=self.text_color,
            padx=15,
            pady=15,
            height=14,
            bd=1,
            highlightthickness=1,
            highlightbackground="#e0e0e0",
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    def check_spelling(self):
        if not self.model:
            messagebox.showwarning("Offline", "Spell check unavailable - API not connected")
            return
            
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Empty", "Please enter some text to check")
            return
        
        self.check_btn.config(text="Processing...", state=tk.DISABLED)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Processing your text...")
        self.output_text.config(state=tk.DISABLED)
        self.root.update()
        
        threading.Thread(target=self.process_text, args=(text,), daemon=True).start()

    def process_text(self, text):
        try:
            response = self.model.generate_content([
                "You are a precise text differencing tool. For the following text, list all changed words",
                "in format 'original->corrected', one per line. Only return the changes, nothing else:",
                f"Original: {text}",
                "Corrected: " + self.model.generate_content([
                    "Correct all errors in this text while preserving meaning and style:",
                    text
                ]).text
            ])
            
            changes = [line.split("->") for line in response.text.split("\n") if "->" in line]
            corrected_text = self.model.generate_content([
                "Correct all errors in this text while preserving meaning and style:",
                text
            ]).text
            
            self.root.after(0, self.highlight_changes, text, changes)
            self.root.after(0, self.display_results, corrected_text)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Check failed: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.check_btn.config(text="Check & Correct Text", state=tk.NORMAL))

    def highlight_changes(self, original_text, changes):
        self.input_text.tag_remove("error", "1.0", tk.END)
        
        search_pos = "1.0"
        for original_word, corrected_word in changes:
            while True:
                start_pos = self.input_text.search(
                    r"\m" + re.escape(original_word) + r"\M", 
                    search_pos, 
                    stopindex=tk.END,
                    regexp=True
                )
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(original_word)}c"
                self.input_text.tag_add("error", start_pos, end_pos)
                search_pos = end_pos

    def display_results(self, corrected_text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, corrected_text)
        self.output_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = LexiFixSpellChecker(root)
    root.mainloop()
