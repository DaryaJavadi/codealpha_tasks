"""
Language Translator Application - Using LibreTranslate API
Works with Python 3.13+

LibreTranslate is a FREE and Open Source translation API
NO BILLING ACCOUNT REQUIRED!

Required installations:
pip install requests
pip install pyperclip
pip install pyttsx3  # Optional: for text-to-speech

API Options:
1. Use public instance (FREE, no setup): https://libretranslate.com
2. Or host your own instance for unlimited usage
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import pyperclip
import threading
import json

# ============ API CONFIGURATION ============
# Public LibreTranslate instance (FREE, no API key needed!)
API_URL = "https://libretranslate.com/translate"
# Optional: Get a free API key from https://libretranslate.com for higher limits
API_KEY = ""  # Leave empty for free usage, or add key for more requests
# ==========================================

# Supported languages
LANGUAGES = {
    'en': 'English', 'ar': 'Arabic', 'az': 'Azerbaijani', 'zh': 'Chinese',
    'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'eo': 'Esperanto',
    'fi': 'Finnish', 'fr': 'French', 'de': 'German', 'el': 'Greek',
    'he': 'Hebrew', 'hi': 'Hindi', 'hu': 'Hungarian', 'id': 'Indonesian',
    'ga': 'Irish', 'it': 'Italian', 'ja': 'Japanese', 'ko': 'Korean',
    'fa': 'Persian', 'pl': 'Polish', 'pt': 'Portuguese', 'ru': 'Russian',
    'sk': 'Slovak', 'es': 'Spanish', 'sv': 'Swedish', 'tr': 'Turkish',
    'uk': 'Ukrainian', 'vi': 'Vietnamese'
}

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Language Translator - LibreTranslate API")
        self.root.geometry("750x650")
        self.root.resizable(False, False)
        
        # Create main frame
        main_frame = tk.Frame(root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="🌍 Language Translator", 
                              font=("Arial", 22, "bold"), bg="#f0f0f0", fg="#333")
        title_label.pack(pady=(0, 10))
        
        # API Status
        api_label = tk.Label(main_frame, text="✅ Using LibreTranslate (FREE & Open Source)", 
                            font=("Arial", 10, "italic"), bg="#f0f0f0", fg="#4CAF50")
        api_label.pack(pady=(0, 15))
        
        # Language selection frame
        lang_frame = tk.Frame(main_frame, bg="#f0f0f0")
        lang_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Source language
        src_label = tk.Label(lang_frame, text="Source Language:", 
                            font=("Arial", 11, "bold"), bg="#f0f0f0")
        src_label.grid(row=0, column=0, padx=5, sticky="w")
        
        self.src_lang = ttk.Combobox(lang_frame, width=22, state="readonly")
        lang_list = ['Auto Detect'] + [f"{name} ({code})" for code, name in sorted(LANGUAGES.items(), key=lambda x: x[1])]
        self.src_lang['values'] = lang_list
        self.src_lang.current(0)  # Auto detect default
        self.src_lang.grid(row=0, column=1, padx=5)
        
        # Swap button
        swap_btn = tk.Button(lang_frame, text="⇄", command=self.swap_languages,
                           font=("Arial", 12, "bold"), bg="#9c27b0", fg="white",
                           width=3, cursor="hand2", relief=tk.RAISED)
        swap_btn.grid(row=0, column=2, padx=10)
        
        # Target language
        dest_label = tk.Label(lang_frame, text="Target Language:", 
                             font=("Arial", 11, "bold"), bg="#f0f0f0")
        dest_label.grid(row=0, column=3, padx=5, sticky="w")
        
        self.dest_lang = ttk.Combobox(lang_frame, width=22, state="readonly")
        self.dest_lang['values'] = [f"{name} ({code})" for code, name in sorted(LANGUAGES.items(), key=lambda x: x[1])]
        # Set Spanish as default
        spanish_idx = [i for i, v in enumerate(self.dest_lang['values']) if '(es)' in v][0]
        self.dest_lang.current(spanish_idx)
        self.dest_lang.grid(row=0, column=4, padx=5)
        
        # Input text area
        input_label = tk.Label(main_frame, text="Enter Text to Translate:", 
                              font=("Arial", 11, "bold"), bg="#f0f0f0")
        input_label.pack(anchor="w", pady=(0, 5))
        
        input_frame = tk.Frame(main_frame, bg="#f0f0f0")
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        self.input_text = tk.Text(input_frame, height=8, font=("Arial", 11), 
                                 wrap=tk.WORD, relief=tk.SOLID, borderwidth=2)
        input_scrollbar = tk.Scrollbar(input_frame, command=self.input_text.yview)
        self.input_text.config(yscrollcommand=input_scrollbar.set)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Character count
        self.char_count = tk.Label(main_frame, text="Characters: 0", 
                                   font=("Arial", 9), bg="#f0f0f0", fg="#666")
        self.char_count.pack(anchor="e", pady=(2, 0))
        self.input_text.bind('<KeyRelease>', self.update_char_count)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(pady=15)
        
        translate_btn = tk.Button(button_frame, text="🔄 Translate", 
                                 command=self.translate_text,
                                 font=("Arial", 12, "bold"), bg="#4CAF50", 
                                 fg="white", padx=25, pady=10, cursor="hand2",
                                 relief=tk.RAISED, borderwidth=2)
        translate_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(button_frame, text="🗑️ Clear", 
                            command=self.clear_text,
                            font=("Arial", 12, "bold"), bg="#f44336", 
                            fg="white", padx=25, pady=10, cursor="hand2",
                            relief=tk.RAISED, borderwidth=2)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Output text area
        output_label = tk.Label(main_frame, text="Translation:", 
                               font=("Arial", 11, "bold"), bg="#f0f0f0")
        output_label.pack(anchor="w", pady=(0, 5))
        
        output_frame = tk.Frame(main_frame, bg="#f0f0f0")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = tk.Text(output_frame, height=8, font=("Arial", 11), 
                                  wrap=tk.WORD, relief=tk.SOLID, borderwidth=2,
                                  state=tk.DISABLED, bg="#ffffff")
        output_scrollbar = tk.Scrollbar(output_frame, command=self.output_text.yview)
        self.output_text.config(yscrollcommand=output_scrollbar.set)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Copy and Speak buttons
        action_frame = tk.Frame(main_frame, bg="#f0f0f0")
        action_frame.pack(pady=(10, 0))
        
        copy_btn = tk.Button(action_frame, text="📋 Copy Translation", 
                           command=self.copy_translation,
                           font=("Arial", 10, "bold"), bg="#2196F3", 
                           fg="white", padx=15, pady=7, cursor="hand2",
                           relief=tk.RAISED, borderwidth=2)
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        # Try to import text-to-speech
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            speak_btn = tk.Button(action_frame, text="🔊 Speak Translation", 
                               command=self.speak_translation,
                               font=("Arial", 10, "bold"), bg="#FF9800", 
                               fg="white", padx=15, pady=7, cursor="hand2",
                               relief=tk.RAISED, borderwidth=2)
            speak_btn.pack(side=tk.LEFT, padx=5)
        except ImportError:
            self.tts_engine = None
        
        # Status label
        self.status_label = tk.Label(main_frame, text="Ready to translate - No setup required!", 
                                    font=("Arial", 10, "italic"), 
                                    bg="#f0f0f0", fg="#666")
        self.status_label.pack(pady=(10, 0))
        
        # Info label
        info_label = tk.Label(main_frame, 
                             text="💡 Tip: For unlimited usage, get a free API key at libretranslate.com",
                             font=("Arial", 8), bg="#f0f0f0", fg="#999", wraplength=700)
        info_label.pack(pady=(5, 0))
    
    def get_lang_code(self, selection):
        """Extract language code from selection string"""
        if selection == 'Auto Detect':
            return 'auto'
        return selection.split('(')[-1].strip(')')
    
    def update_char_count(self, event=None):
        """Update character count"""
        count = len(self.input_text.get("1.0", tk.END).strip())
        self.char_count.config(text=f"Characters: {count}")
    
    def swap_languages(self):
        """Swap source and target languages"""
        if self.src_lang.get() == 'Auto Detect':
            messagebox.showinfo("Info", "Cannot swap when source is 'Auto Detect'")
            return
        
        src_idx = self.src_lang.current()
        dest_idx = self.dest_lang.current()
        
        # Adjust for Auto Detect in source
        self.src_lang.current(dest_idx + 1)  # +1 because of Auto Detect
        self.dest_lang.current(src_idx - 1)  # -1 to account for Auto Detect
    
    def translate_text(self):
        """Translate the input text using LibreTranslate API"""
        input_txt = self.input_text.get("1.0", tk.END).strip()
        
        if not input_txt:
            messagebox.showwarning("Warning", "Please enter text to translate!")
            return
        
        src = self.get_lang_code(self.src_lang.get())
        dest = self.get_lang_code(self.dest_lang.get())
        
        if src != 'auto' and dest and src == dest:
            messagebox.showinfo("Info", "Source and target languages are the same!")
            return
        
        self.status_label.config(text="🔄 Translating using LibreTranslate API...", fg="#2196F3")
        self.root.update()
        
        # Run translation in separate thread
        thread = threading.Thread(target=self._perform_translation, 
                                 args=(input_txt, src, dest))
        thread.daemon = True
        thread.start()
    
    def _perform_translation(self, text, src, dest):
        """Perform translation using LibreTranslate API"""
        try:
            # Prepare request payload
            payload = {
                'q': text,
                'source': src,
                'target': dest,
                'format': 'text'
            }
            
            # Add API key if provided
            if API_KEY:
                payload['api_key'] = API_KEY
            
            # Make API request
            response = requests.post(
                API_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get('translatedText', '')
                detected_lang = result.get('detectedLanguage', {}).get('language', src)
                
                # Update UI in main thread
                self.root.after(0, self._update_translation, translated_text, detected_lang, dest)
            elif response.status_code == 429:
                self.root.after(0, self._show_error, 
                              "Rate limit reached. Please wait a moment or get a free API key at libretranslate.com")
            elif response.status_code == 403:
                self.root.after(0, self._show_error, 
                              "API access denied. Please get a free API key at libretranslate.com")
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', f'API Error: {response.status_code}')
                self.root.after(0, self._show_error, error_msg)
                
        except requests.exceptions.Timeout:
            self.root.after(0, self._show_error, "Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            self.root.after(0, self._show_error, 
                          "Connection error. Please check your internet connection.")
        except Exception as e:
            self.root.after(0, self._show_error, str(e))
    
    def _update_translation(self, translated_text, src, dest):
        """Update the output text area with translation"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", translated_text)
        self.output_text.config(state=tk.DISABLED)
        
        src_name = LANGUAGES.get(src, 'Auto-detected') if src != 'auto' else 'Auto-detected'
        dest_name = LANGUAGES.get(dest, dest)
        self.status_label.config(
            text=f"✅ Translated from {src_name} to {dest_name} (LibreTranslate API)", 
            fg="#4CAF50"
        )
    
    def _show_error(self, error_msg):
        """Show error message"""
        self.status_label.config(text=f"❌ Error: {error_msg}", fg="#f44336")
        messagebox.showerror("Translation Error", f"An error occurred:\n\n{error_msg}")
    
    def clear_text(self):
        """Clear all text fields"""
        self.input_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.char_count.config(text="Characters: 0")
        self.status_label.config(text="Ready to translate - No setup required!", fg="#666")
    
    def copy_translation(self):
        """Copy translation to clipboard"""
        translation = self.output_text.get("1.0", tk.END).strip()
        
        if not translation:
            messagebox.showinfo("Info", "No translation to copy!")
            return
        
        try:
            pyperclip.copy(translation)
            self.status_label.config(text="✅ Copied to clipboard!", fg="#4CAF50")
        except Exception:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(translation)
                self.status_label.config(text="✅ Copied to clipboard!", fg="#4CAF50")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy: {str(e)}")
    
    def speak_translation(self):
        """Speak the translation using text-to-speech"""
        if not self.tts_engine:
            messagebox.showinfo("Info", "Text-to-speech not available.\nInstall: pip install pyttsx3")
            return
        
        translation = self.output_text.get("1.0", tk.END).strip()
        
        if not translation:
            messagebox.showinfo("Info", "No translation to speak!")
            return
        
        try:
            self.status_label.config(text="🔊 Speaking...", fg="#FF9800")
            self.root.update()
            self.tts_engine.say(translation)
            self.tts_engine.runAndWait()
            self.status_label.config(text="✅ Speech completed!", fg="#4CAF50")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to speak: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()