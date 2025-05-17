import json
import os

import tempfile

class History:
    def __init__(self, filename="conversation_history.JSON"):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

    def load_history(self):
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
            return []

    def save_history(self, history_list):
        dirpath = os.path.dirname(self.filename) or "."
        with tempfile.NamedTemporaryFile("w", dir=dirpath, delete=False, encoding="utf-8") as tf:
            json.dump(history_list, tf, indent=2)
            tf.flush()
            os.fsync(tf.fileno())
            tmpname = tf.name
        os.replace(tmpname, self.filename)

    def add_entry(self, entry):
        history = self.load_history()
        history.append(entry)
        self.save_history(history)
    
    def user(self, text: str):
        self.add_entry({
            "role": "user",
            "parts": [{"text": text}]
        })

    def model(self, text: str):
        self.add_entry({
            "role": "model",
            "parts": [{"text": text}]
        })
