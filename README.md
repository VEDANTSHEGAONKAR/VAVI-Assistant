# VAVI - Voice Assistant

A voice-controlled assistant built with Python that uses Google's Gemini AI for natural language processing and speech recognition.

## Features

- Voice input and output
- Natural language processing using Google's Gemini AI
- Modern GUI interface
- Real-time conversation capabilities

## Prerequisites

- Python 3.7 or higher
- Google Cloud API key for Gemini AI
- Microphone for voice input
- Speakers for voice output

## Installation

1. Clone this repository or download the source code.

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a file named `apikey.py` in the same directory and add your Google API key:
```python
api_data = "YOUR_GOOGLE_API_KEY"
```

## Usage

1. Run the application:
```bash
python vavi.py
```

2. Click the "Start Conversation" button to begin interacting with VAVI.

3. Speak into your microphone to give commands or ask questions.

4. Click the "End Conversation" button to close the application.

## Controls

- **Start Conversation**: Begins the voice interaction
- **End Conversation**: Closes the application

## Note

Make sure you have a working microphone and speakers connected to your system. The application requires an internet connection for speech recognition and AI processing. 