import whisper

class Transcribe:
    def __init__(self):
        self.model = whisper.load_model("base")  
        
    def transcribe_whisper(self, path):
        result = self.model.transcribe(path)
        return result.get("text", "").strip()
