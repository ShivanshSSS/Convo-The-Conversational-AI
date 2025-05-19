import os
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    SpeakWSOptions,
)
import signal
import time
import numpy as np
import pygame
import threading 
import pyaudio
import webrtcvad
from deepgram import DeepgramClient, SpeakOptions

DG_API_KEY = ("YOUR API KEY")
dg = DeepgramClient(DG_API_KEY)

def generate_audio(text: str, voice_model: str ,filename: str) -> str:
    
    filename = filename
    dg.speak.rest.v("1").save(
        filename,
        {"text": text},
        SpeakOptions(model=voice_model)
    )
    return filename

def stream_audio(text_input,voice_model):
    options = SpeakWSOptions(
            model=voice_model,
            encoding="linear16",
            sample_rate=16000,
        )
    config = DeepgramClientOptions(
            options={"speaker_playback": "true"},
        )
    deepgram = DeepgramClient("YOUR API KEY", config)
    dg_connection = deepgram.speak.websocket.v("1")
    dg_connection.start(options)
    dg_connection.send_text(text_input)
    dg_connection.flush()
    dg_connection.wait_for_complete()
    dg_connection.finish()

