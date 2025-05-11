import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import tkinter as tk
from tkinter import scrolledtext
import threading
from apikey import api_data
import os
import webbrowser
import subprocess
from pytube import Search
import pyautogui
import time

# Configure API key
GENAI_API_KEY = api_data
genai.configure(api_key=GENAI_API_KEY)

# Text-to-Speech engine
engine = None
speak_lock = threading.Lock()

# Dictionary of common applications and their paths
APPS = {
    'notepad': 'notepad.exe',
    'calculator': 'calc.exe',
    'paint': 'mspaint.exe',
    'word': 'WINWORD.EXE',
    'excel': 'EXCEL.EXE',
    'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'firefox': r'C:\Program Files\Mozilla Firefox\firefox.exe',
    'edge': r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
}

def init_tts_engine():
    """Initialize the text-to-speech engine."""
    global engine
    if engine is None:
        engine = pyttsx3.init('sapi5')
        engine.setProperty('voice', engine.getProperty('voices')[0].id)

def speak(text):
    """Convert text to speech, thread-safe."""
    init_tts_engine()
    with speak_lock:
        engine.say(text)
        engine.runAndWait()

def open_application(app_name):
    """Open the specified application."""
    app_name = app_name.lower()
    try:
        if app_name in APPS:
            subprocess.Popen(APPS[app_name])
            return f"Opening {app_name}"
        else:
            return f"Sorry, I don't know how to open {app_name}"
    except Exception as e:
        return f"Error opening {app_name}: {str(e)}"

def play_youtube_video(query):
    """Search and play a YouTube video."""
    try:
        # Search for the video
        s = Search(query)
        if not s.results:
            return "Sorry, I couldn't find any videos matching your request."
        
        # Get the first video result
        video = s.results[0]
        
        # Open the video in the default browser
        webbrowser.open(f"https://www.youtube.com/watch?v={video.video_id}")
        return f"Playing {video.title}"
    except Exception as e:
        return f"Error playing video: {str(e)}"

def clean_text(text):
    """Remove asterisks and clean the text."""
    return text.replace('*', '')

def process_command(query):
    """Process the user's command and perform appropriate action."""
    query = query.lower()
    
    # Check for application opening commands
    if "open" in query:
        for app in APPS.keys():
            if app in query:
                return open_application(app)
    
    # Check for YouTube video commands
    if any(phrase in query for phrase in ["play", "youtube", "video"]):
        # Extract the search query
        search_query = query.replace("play", "").replace("youtube", "").replace("video", "").strip()
        if search_query:
            return play_youtube_video(search_query)
    
    # If no specific command is recognized, use Gemini for general conversation
    response = generate_response(query)
    return clean_text(response)

def generate_response(query):
    """Generate a response for the given query using Gemini."""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Create a system prompt to guide the model's behavior
        system_prompt = """You are VAVI, a helpful and thoughtful AI assistant. Follow these guidelines:
        1. Think carefully before responding
        2. Consider the user's specific requirements and context
        3. Provide detailed and accurate information
        4. Be conversational but professional
        5. If unsure about something, acknowledge it
        6. Focus on being helpful and practical
        7. Avoid unnecessary technical jargon unless specifically requested
        8. Consider the user's perspective and needs"""
        
        # Combine system prompt with user query
        full_prompt = f"{system_prompt}\n\nUser Query: {query}"
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=300,  # Increased for more detailed responses
                temperature=0.7,        # Balanced between creativity and accuracy
                top_p=0.9,             # Increased for better response quality
                top_k=40,              # Maintained for response diversity
                candidate_count=1,      # Generate one high-quality response
                stop_sequences=None     # No specific stop sequences
            )
        )
        return clean_text(response.text)
    except Exception as e:
        return f"Sorry, I encountered an error: {e}"

def listen_to_command():
    """Convert speech to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        conversation_area.insert(tk.END, "Listening...\n\n")
        recognizer.pause_threshold = 1
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            query = recognizer.recognize_google(audio, language='en-in').lower()
            conversation_area.insert(tk.END, f"You: {query}\n")
            return query
        except sr.UnknownValueError:
            conversation_area.insert(tk.END, "VAVI: Sorry, I didn't catch that. Please repeat.\n")
            speak("Sorry, I didn't catch that. Please repeat.")
            return "none"
        except sr.RequestError:
            conversation_area.insert(tk.END, "VAVI: Network error. Please check your connection.\n")
            speak("Network error. Please check your connection.")
            return "none"
        except Exception as e:
            conversation_area.insert(tk.END, f"VAVI: Error: {e}\n")
            speak("Sorry, I encountered an error.")
            return "none"

# Global variable to control the conversation loop
stop_conversation = False

def handle_conversation():
    """Continuously listen to user input and respond."""
    global stop_conversation
    while not stop_conversation:
        query = listen_to_command()
        if query == "none":
            continue

        if "bye" in query or "goodbye" in query:
            conversation_area.insert(tk.END, "VAVI: Goodbye! Have a great day!\n")
            speak("Goodbye! Have a great day!")
            break

        # Process the command and get response
        response = process_command(query)
        conversation_area.insert(tk.END, f"VAVI: {response}\n")
        speak(response)

def start_conversation():
    """Start the conversation."""
    global stop_conversation
    stop_conversation = False
    conversation_thread = threading.Thread(target=handle_conversation)
    conversation_thread.daemon = True
    conversation_thread.start()
    conversation_area.insert(tk.END, "Hi, I am VAVI. How can I help you?\n\n")
    conversation_area.see(tk.END)
    speak("Hi, I am VAVI. How can I help you?")

def end_conversation():
    """End the conversation and close the application."""
    global stop_conversation
    stop_conversation = True
    conversation_area.insert(tk.END, "VAVI: Conversation ended manually. Goodbye!\n")
    speak("Conversation ended manually. Goodbye!")
    root.quit()

# Set up the GUI
root = tk.Tk()
root.title("V-A-V-I")

# Configure window size and position
window_width = 600
window_height = 500
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Create conversation area with improved styling
conversation_area = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD,
    width=50,
    height=20,
    font=("Arial", 12),
    bg="#f0f0f0",
    fg="#333333"
)
conversation_area.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

# Create button frame
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# Start button with improved styling
start_button = tk.Button(
    button_frame,
    text="Start Conversation",
    font=("Arial", 12, "bold"),
    command=start_conversation,
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=10
)
start_button.pack(side=tk.LEFT, padx=10)

# End button with improved styling
end_button = tk.Button(
    button_frame,
    text="End Conversation",
    font=("Arial", 12, "bold"),
    command=end_conversation,
    bg="#f44336",
    fg="white",
    padx=20,
    pady=10
)
end_button.pack(side=tk.LEFT, padx=10)

# Start the application
if __name__ == "__main__":
    root.mainloop() 