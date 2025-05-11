from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import tempfile
import os
from apikey import api_data
import webbrowser
import subprocess
from pytube import Search

app = Flask(__name__)

# Configure Gemini API
GENAI_API_KEY = os.getenv('GENAI_API_KEY', api_data)
genai.configure(api_key=GENAI_API_KEY)

# Text-to-Speech engine (thread-safe)
engine = None

def init_tts_engine():
    """Initialize the text-to-speech engine."""
    global engine
    if engine is None:
        engine = pyttsx3.init('sapi5')
        engine.setProperty('voice', engine.getProperty('voices')[0].id)

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

def clean_text(text):
    """Remove asterisks and clean the text."""
    return text.replace('*', '')

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

@app.route('/api/gemini', methods=['POST'])
def gemini_response():
    data = request.json
    query = data.get('query', '')
    try:
        response = process_command(query)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'response': f"Sorry, I encountered an error: {e}"}), 500

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    audio_file = request.files['audio']
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp:
        audio_file.save(temp.name)
        with sr.AudioFile(temp.name) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio, language='en-in').lower()
                return jsonify({'text': text})
            except sr.UnknownValueError:
                return jsonify({'text': "Sorry, I didn't catch that. Please repeat."})
            except sr.RequestError:
                return jsonify({'text': "Network error. Please check your connection."})
            except Exception as e:
                return jsonify({'text': f"Error: {e}"})
        os.unlink(temp.name)

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text', '')
    
    # Create a temporary file for the audio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_filename = temp_file.name
    temp_file.close()
    
    try:
        # Initialize TTS engine
        init_tts_engine()
        
        # Save the audio to the temporary file
        engine.save_to_file(text, temp_filename)
        engine.runAndWait()
        
        # Send the file
        return send_file(
            temp_filename,
            mimetype='audio/wav',
            as_attachment=False,
            download_name='response.wav'
        )
    finally:
        # Clean up the temporary file after sending
        try:
            os.unlink(temp_filename)
        except:
            pass

@app.route('/')
def index():
    return app.send_static_file('index.html')

# For local development
if __name__ == '__main__':
    app.run(debug=True) 