import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig
from jinja2 import Template
import time
import threading
import queue

# Import local modules
from History_and_logs import History
from Transcribe import Transcribe
import Generate_audio 
from RAG_input import RAGQueryProcessor
from Extra_functions import play_random_audio, playaudio, model_selection
from Record_audio import AudioRecorderVAD
from Logic import main_for_detection 

class AudioProcessingThread(threading.Thread):
    def __init__(self, voice_model, text, result_queue):
        threading.Thread.__init__(self)
        self.voice_model = voice_model
        self.text = text
        self.result_queue = result_queue
        self.user_audio_path = None
        self.processing_complete = threading.Event()

    def run(self):
        try:
            # This will block until main_for_detection completes
            self.user_audio_path = main_for_detection(self.voice_model, self.text)
            self.result_queue.put(self.user_audio_path)
        except Exception as e:
            print(f"Error in audio processing: {e}")
            self.result_queue.put(None)
        finally:
            # Signal that processing is complete
            self.processing_complete.set()
def main():
    try:
        load_dotenv()
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            SYSTEM_PROMPT = f.read()

        user_name = input("What's your name?: ")
        user_mood = "happy"
        user_age = int(input("What is Your Age?:"))
        want_rag = input("Do you want to enable Rag (y/n):").lower()

        history = History(user_name+"_conversation_history.json")
        loaded_history = history.load_history()

        voice_model, model_selected = model_selection(user_age)

        if want_rag == "y":
            RAGQueryProcessor().initialize_chatbot()
        else:
            pass

        SYSTEM_PROMPT = Template(SYSTEM_PROMPT).render(name=user_name, mood=user_mood)

        client = genai.Client(api_key=api_key)
        chat = client.chats.create(
            model="gemini-2.0-flash",
            config=GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            history=loaded_history
        )

        print(f"Hello {user_name}! I'm ready to chat. Please speak when prompted.")
        
        initial_greeting = f"Hello {user_name}! How can I help you today?"
        initial_audio = Generate_audio.generate_audio(initial_greeting, voice_model, "Welcome.mp3")
        playaudio(initial_audio)
        time.sleep(3)

        user_audio_path = AudioRecorderVAD().record_until_silence()
        while True:
            if user_audio_path:
                play_random_audio(model_selected)
                transcribed_input = Transcribe().transcribe_whisper(user_audio_path)
                print(f"You said: {transcribed_input}")
                start_time = time.time()
                
                if transcribed_input.lower() in ["exit", "quit", "goodbye", "bye"]:
                    print("Ending conversation...")
                    break

                if want_rag == "y":
                    input_text = RAGQueryProcessor().user_input_with_rag(transcribed_input)
                else:
                    input_text = transcribed_input

                response = chat.send_message(input_text)
                print(response.text)

                # Create a queue to store the result of audio processing
                result_queue = queue.Queue()

                # Create and start the audio processing thread
                audio_thread = AudioProcessingThread(voice_model, response.text, result_queue)
                audio_thread.start()
                print("Processing audio response... Please wait.")
                audio_thread.processing_complete.wait()
                # Wait for the thread to complete and get the result
                user_audio_path = result_queue.get()
                # Retrieve the result from the queue
                               
                print(f"Chatbot: {response.text}")
                history.user(transcribed_input)
                history.model(response.text)
                print(time.time()-start_time)
            else:
                print("No audio input. Please try again.")
                
    except KeyboardInterrupt:
        print("\nChatbot terminated by user.")

if __name__ == "__main__":
    main()