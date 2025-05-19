import sounddevice as sd
import webrtcvad
import numpy as np
import collections
from scipy.io.wavfile import write
import threading

class AudioRecorderVAD:
    def __init__(self, sample_rate=16000, frame_duration=30, silence_duration=2):
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration 
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        self.silence_duration = silence_duration
        self.vad = webrtcvad.Vad(1)  
        self.should_stop_playback = threading.Event()

    def _is_speech(self, frame_bytes):
        return self.vad.is_speech(frame_bytes, self.sample_rate)

    def record_until_silence(self):
        print("Recording... Speak into the mic. Silence will stop recording.")
        stream = sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16', blocksize=self.frame_size)
        audio_frames = []
        silence_buffer = collections.deque(maxlen=int(self.silence_duration * 1000 / self.frame_duration))

        with stream:
            while True:
                block, _ = stream.read(self.frame_size)
                block = block.flatten()
                frame_bytes = block.tobytes()

                audio_frames.append(block)

                if self._is_speech(frame_bytes):
                    silence_buffer.clear()
                else:
                    silence_buffer.append(1)

                if len(silence_buffer) == silence_buffer.maxlen:
                    print("Silence detected. Stopping.")
                    break

        audio_data = np.concatenate(audio_frames)
        temp_wav_path = ("recorded_audio.wav")
        write(temp_wav_path, self.sample_rate, audio_data)
        print(f"Saved to {temp_wav_path}")
        return temp_wav_path

    