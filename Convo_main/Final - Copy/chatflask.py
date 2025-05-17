import os, time, queue, threading
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
from google import genai
from google.genai.types import GenerateContentConfig
from jinja2 import Template

from History_and_logs import History
from Transcribe import Transcribe
import Generate_audio
from RAG_input import RAGQueryProcessor
from Extra_functions import model_selection
from Logic import main_for_detection

# — Flask setup —
app = Flask(__name__, static_folder='static', template_folder='templates')
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY")

# Load system prompt
with open("system_prompt.txt", encoding="utf-8") as f:
    raw_prompt = f.read()

# History + GenAI client
history = History("conversation_history.json")
client  = genai.Client(api_key=API_KEY)
chat    = None

# Session globals
voice_model    = None
model_selected = None
enable_rag     = False

# AudioProcessingThread (VAD + TTS)
class AudioProcessingThread(threading.Thread):
    def __init__(self, model, text, result_q):
        super().__init__()
        self.model    = model
        self.text     = text
        self.result_q = result_q
        self.done     = threading.Event()

    def run(self):
        try:
            path = main_for_detection(self.model, self.text)
            self.result_q.put(path)
        except Exception as e:
            print("VAD thread error:", e)
            self.result_q.put(None)
        finally:
            self.done.set()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_session():
    global chat, voice_model, model_selected, enable_rag

    data    = request.json or {}
    name    = data.get("name","User").strip()
    age     = int(data.get("age",0))
    enable_rag = bool(data.get("rag", False))

    # Initialize chat with system prompt
    prompt = Template(raw_prompt).render(name=name, mood="happy")
    chat   = client.chats.create(
        model="gemini-2.0-flash",
        config=GenerateContentConfig(system_instruction=prompt),
        history=history.load_history()
    )

    # RAG setup
    if enable_rag:
        RAGQueryProcessor().initialize_chatbot()

    # Choose voice
    voice_model, model_selected = model_selection(age)

    # Generate greeting audio
    greeting = f"Hello {name}! How can I help you today?"
    os.makedirs("static/audio", exist_ok=True)
    fname = f"audio/welcome_{int(time.time())}.wav"
    full  = os.path.join("static", fname)
    Generate_audio.generate_audio(greeting, voice_model, full)
    url = url_for('static', filename=fname)

    return jsonify({
        "greeting_text":  greeting,
        "greeting_audio": url,
        "model_selected": model_selected
    })

@app.route('/message', methods=['POST'])
def message():
    audio = request.files.get('audio_data')
    if not audio:
        return jsonify(error="No audio"), 400

    # Save upload
    os.makedirs("uploads", exist_ok=True)
    path = os.path.join("uploads", audio.filename)
    audio.save(path)

    # Transcribe
    try:
        user_text = Transcribe().transcribe_whisper(path)
    except Exception as e:
        print("Transcribe error:", e)
        return jsonify(error="Transcription failed"), 500
    if not user_text:
        return jsonify(error="Empty transcription"), 400

    history.user(user_text)

    # RAG or not
    try:
        input_text = (RAGQueryProcessor().user_input_with_rag(user_text)
                      if enable_rag else user_text)
    except Exception:
        input_text = user_text

    # Chat reply
    resp = chat.send_message(input_text)
    history.model(resp.text)

    return jsonify(user_text=user_text, bot_text=resp.text)

@app.route('/tts', methods=['POST'])
def tts():
    global voice_model

    data = request.json or {}
    text = data.get("text","")
    if not text:
        return jsonify(error="No text"), 400

    # Run VAD+TTS in thread
    q      = queue.Queue()
    thread = AudioProcessingThread(voice_model, text, q)
    thread.start()
    thread.done.wait()
    path   = q.get()
    url    = ("/" + path) if path and path.startswith("static/") else path
    return jsonify(audio_url=url)

if __name__ == '__main__':
    app.run(debug=True)
