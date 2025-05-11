from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
import os
from apikey import api_data
import webbrowser
from pytube import Search
import requests

app = Flask(__name__)

# Configure Gemini API
GENAI_API_KEY = os.getenv('GENAI_API_KEY', api_data)
genai.configure(api_key=GENAI_API_KEY)

def clean_text(text):
    """Remove asterisks and clean the text."""
    return text.replace('*', '')

def play_youtube_video(query):
    """Search and play a YouTube video."""
    try:
        # Search for the video
        s = Search(query)
        if not s.results:
            return "Sorry, I couldn't find any videos matching your request."
        
        # Get the first video result
        video = s.results[0]
        
        # Return the video URL and title
        return {
            'url': f"https://www.youtube.com/watch?v={video.video_id}",
            'title': video.title
        }
    except Exception as e:
        return f"Error playing video: {str(e)}"

def process_command(query):
    """Process the user's command and perform appropriate action."""
    query = query.lower()
    
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

@app.route('/')
def index():
    return app.send_static_file('index.html')

# For local development
if __name__ == '__main__':
    app.run(debug=True) 