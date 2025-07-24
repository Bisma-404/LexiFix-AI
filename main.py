import tkinter as tk
from tkinter import scrolledtext, messagebox, Frame, Label, Button
import google.generativeai as genai
import os
import threading
from dotenv import load_dotenv
from PIL import Image, ImageTk
import re

load_dotenv()

class LexiFixSpellChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("LexiFix - AI Spell and Grammar Checker")
        
        # Window size and centering
        window_width = 1000
        window_height = 770
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.configure(bg="#7e57c2")
        
        # Color scheme
        self.bg_color = "#ffffff"
        self.text_color = "#333333"
        self.primary_color = "#7e57c2"
        self.header_color = "#7e57c2"
        self.button_color = "#7e57c2"
        self.error_underline = "#ff4444"
        
        # Initialize Gemini API
        self.model = None
        self.initialize_gemini()
        
        # Load logo image
        self.logo_img = None
        try:
            img = Image.open("lexifix_logo.png")
            img = img.resize((90, 90), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Could not load logo image: {e}")
        
        self.setup_ui()

    def initialize_gemini(self):
        """Initialize Gemini API"""
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
        """Setup the user interface"""
        main_frame = Frame(self.root, bg=self.header_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header with logo and title
        header = Frame(main_frame, bg=self.header_color, pady=15)
        header.pack(fill=tk.X)
        
        title_container = Frame(header, bg=self.header_color)
        title_container.pack(expand=True)
        
        if self.logo_img:
            logo_label = Label(title_container, image=self.logo_img, bg=self.header_color)
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_frame = Frame(title_container, bg=self.header_color)
        title_frame.pack(side=tk.LEFT)
        
        Label(title_frame, 
             text="LexiFix", 
             font=("Segoe UI", 24, "bold"), 
             bg=self.header_color, 
             fg="white").pack(anchor='w')
        
        Label(title_frame, 
             text="AI Spell and Grammar Checker", 
             font=("Segoe UI", 12), 
             bg=self.header_color, 
             fg="white").pack(anchor='w')
        
        # Content frame
        content_frame = Frame(main_frame, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top panel - Original text
        input_frame = Frame(content_frame, bg="white", padx=15, pady=15)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        Label(input_frame,
             text="Original Text:",
             font=("Segoe UI", 10, "bold"),
             bg="white",
             fg="#333333").pack(anchor="w")
        
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
        
        # Configure error tag
        self.input_text.tag_config("error", underline=True, underlinefg=self.error_underline)
        
        # Button
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
        
        # Purple separator
        separator = Frame(content_frame, bg=self.header_color, height=10)
        separator.pack(fill=tk.X)
        
        # Bottom panel - Corrected text
        output_frame = Frame(content_frame, bg="white", padx=15, pady=15)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        Label(output_frame,
             text="Corrected Text:",
             font=("Segoe UI", 10, "bold"),
             bg="white",
             fg="#333333").pack(anchor="w")
        
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
        """Check spelling and grammar"""
        if not self.model:
            messagebox.showwarning("Offline", "Spell check unavailable - API not connected")
            return
            
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Empty", "Please enter some text to check")
            return
        
        # Show loading state
        self.check_btn.config(text="Processing...", state=tk.DISABLED)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Processing your text...")
        self.output_text.config(state=tk.DISABLED)
        self.root.update()
        
        # Run in background thread
        threading.Thread(target=self.process_text, args=(text,), daemon=True).start()

    def process_text(self, text):
        """Process the text in background"""
        try:
            prompt = f"""Correct all spelling and grammar errors in this text while preserving its meaning and style. 
            Return only the corrected text without any additional explanations or formatting:
            
            {text}"""
            
            response = self.model.generate_content(prompt)
            corrected_text = response.text
            
            # Highlight differences
            self.highlight_errors(text, corrected_text)
            
            # Display results
            self.root.after(0, self.display_results, corrected_text)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Check failed: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.check_btn.config(
                text="Check & Correct Text", 
                state=tk.NORMAL
            ))

    def highlight_errors(self, original_text, corrected_text):
        """Highlight the specific errors in the original text"""
        # Clear previous highlights
        self.input_text.tag_remove("error", "1.0", tk.END)
        
        # Split into words for comparison
        original_words = original_text.split()
        corrected_words = corrected_text.split()
        
        # Start searching from beginning
        search_pos = "1.0"
        
        for orig_word, corr_word in zip(original_words, corrected_words):
            if orig_word != corr_word:
                # Find the word in the text widget (using regex for whole words)
                start_pos = self.input_text.search(
                    r"\y" + re.escape(orig_word) + r"\y", 
                    search_pos, 
                    stopindex=tk.END,
                    regexp=True
                )
                if start_pos:
                    end_pos = f"{start_pos}+{len(orig_word)}c"
                    self.input_text.tag_add("error", start_pos, end_pos)
                    search_pos = end_pos
            
            # Move to next word position
            next_space = self.input_text.search(" ", search_pos, stopindex=tk.END)
            if next_space:
                search_pos = f"{next_space}+1c"

    def display_results(self, corrected_text):
        """Display the corrected text"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, corrected_text)
        self.output_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = LexiFixSpellChecker(root)
    root.mainloop()