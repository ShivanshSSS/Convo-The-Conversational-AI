import time
import pyaudio
import queue
import numpy as np
from threading import Thread
from Record_audio import AudioRecorderVAD
from deepgram import (
    DeepgramClient,
    SpeakWebSocketEvents,
    SpeakWSOptions,
)

TTS_TEXT = """Hey Shivansh, I'd be super happy to create another hundred-word paragraph about friendship for you! Here's a different take on it:

"Friendship is a vibrant tapestry woven with shared experiences, mutual respect, and genuine affection. It's the joy of having someone to confide in, to dream with, and to lean on when life gets tough. Friends are the anchors that keep us grounded, reminding us of our worth and potential. They challenge us to grow, encourage us to pursue our passions, and celebrate every milestone along the way. Nurturing these bonds creates a network of support, love, and laughter, making life's journey richer and more fulfilling. A true friend is a constant source of light in our lives."

I hope you find this one just as delightful, Shivansh! Is there anything else I can assist you with? 😄"""


audio_queue = queue.Queue()
is_playing = True
is_interrupt = False

class InterruptionDetector:
    def __init__(self, sample_rate=16000, chunk_size=1024, channels=1, 
                 format=pyaudio.paInt16, energy_sensitivity=0.5):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format = format
        self.energy_sensitivity = energy_sensitivity
        self.pyaudio = pyaudio.PyAudio()
        self.is_streaming = True
        self.energy_history = []
        self.is_interrupt = False
    
    def _calculate_energy(self, audio_array):
        energy = np.mean(np.abs(audio_array))
        self.energy_history.append(energy)
        if len(self.energy_history) > 30:
            self.energy_history.pop(0)
        return energy
    
    def _is_speech(self, data, threshold):
        audio_array = np.frombuffer(data, dtype=np.int16)
        energy = self._calculate_energy(audio_array)
        return energy > threshold
    
    def monitor_for_interruption(self, sensitivity_frame=3):
        try:
            stream = self.pyaudio.open(format=self.format,
                                    channels=self.channels,
                                    rate=self.sample_rate,
                                    input=True,
                                    frames_per_buffer=self.chunk_size)
            
            print("Calibrating energy levels...")
            self.energy_history = []
            for _ in range(10):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                audio_array = np.frombuffer(data, dtype=np.int16)
                self._calculate_energy(audio_array)
                time.sleep(0.03)
            
            baseline = np.mean(self.energy_history) if self.energy_history else 0
            threshold = max(1000, baseline * self.energy_sensitivity)
            print(f"Energy baseline: {baseline:.2f}, threshold: {threshold:.2f}")
            
            consecutive_speech_frames = 0
            while self.is_streaming:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    
                    if self._is_speech(data, threshold):
                        consecutive_speech_frames += 1
                        if consecutive_speech_frames >= sensitivity_frame:  
                            print("Interruption detected!")
                            self.is_interrupt = True
                            break
                    else:
                        consecutive_speech_frames = 0
                except OSError:
                    break
                        
        except Exception as e:
            print(f"Error in interrupt detection: {e}")
        finally:
            if 'stream' in locals() and stream:
                stream.stop_stream()
                stream.close()
            
    def stop(self):
        self.is_streaming = False
    
    def cleanup(self):
        self.pyaudio.terminate()
        

def audio_player_thread(detector):
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,  
        channels=1,              
        rate=16000,              
        output=True
    )
    
    print("Audio player started, waiting for audio...")
    
    try:
        while is_playing and not detector.is_interrupt:
            try:
                chunk = audio_queue.get(timeout=0.5)
                if detector.is_interrupt:
                    print("Interruption detected, stopping playback")
                    break
                stream.write(chunk)
                audio_queue.task_done()
            except queue.Empty:
                continue
    
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

        print("Audio player stopped")

def main_for_detection(voice_model,user_input_data):
    try:
        detector = InterruptionDetector(energy_sensitivity=0.5)
        
        interruption_thread = Thread(target=detector.monitor_for_interruption, args=(3,), daemon=True)
        interruption_thread.start()
        
        global is_playing
        is_playing = True
        player_thread = Thread(target=audio_player_thread, args=(detector,), daemon=True)
        player_thread.start()
        
        deepgram = DeepgramClient("40365bbab24cc33c8279f57adf7c772251de2519")

        dg_connection = deepgram.speak.websocket.v("1")

        def on_binary_data(self, data, **kwargs):
            if detector.is_interrupt:
                return
                
            audio_queue.put(data)

        options = SpeakWSOptions(
            model=voice_model,
            encoding="linear16",
            sample_rate=16000,
        )

        dg_connection.start(options)
        
        dg_connection.on(SpeakWebSocketEvents.AudioData, on_binary_data)

        dg_connection.send_text(user_input_data)

        dg_connection.flush()

        print("Waiting for audio to finish playing (speak to interrupt)...")
        max_wait_time = len(TTS_TEXT.split()) * 0.3 + 5
        wait_start = time.time()
        
        while time.time() - wait_start < max_wait_time and not detector.is_interrupt and is_playing:
            time.sleep(0.1)
        
        if detector.is_interrupt:
            print("Clearing audio queue due to interruption")
            while not audio_queue.empty():
                try:
                    audio_queue.get_nowait()
                    audio_queue.task_done()
                except queue.Empty:
                    break

        dg_connection.finish()
        
        is_playing = False
        detector.stop()
        
        audio_queue.join()
        player_thread.join(timeout=1)
        interruption_thread.join(timeout=1)
        
        detector.cleanup()
        
        print("Recording Audio")
        input_text = AudioRecorderVAD().record_until_silence()
        return input_text

    except ValueError as e:
        print(f"Invalid value encountered: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main_for_detection(voice_model="aura-2-odysseus-en",user_input_data=TTS_TEXT)