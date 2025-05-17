import random
import pygame
import threading
import os.path

pygame.mixer.init()

def playaudio(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return False
    
    def play_sound_thread():
        try:
            sound = pygame.mixer.Sound(file_path)
            sound.play()
        except Exception as e:
            print(f"Error playing sound: {e}")
    
    sound_thread = threading.Thread(target=play_sound_thread)
    sound_thread.daemon = True 
    sound_thread.start()
    
    return True

def stop_all():
    pygame.mixer.stop()

def set_volume(volume):
    if 0.0 <= volume <= 1.0:
        pygame.mixer.music.set_volume(volume)
    else:
        print("Volume must be between 0.0 and 1.0")

def play_random_audio(file_list):
    if not file_list:
        print("Error: Empty file list provided.")
        return False, None
    
    valid_files = [f for f in file_list if os.path.exists(f)]
    
    if not valid_files:
        print("Error: No valid files found in the provided list.")
        return False, None
    
    selected_file = random.choice(valid_files)
    
    success = playaudio(selected_file)
    
    return success, selected_file


def select_file(voice_model):
    thalia = ["audio/thalia_interesting.mp3","audio/thalia_interesting.mp3","audio/thalia_interesting.mp3","audio/thalia_interesting.mp3"]
    odysseus = ["audio/odysseus_interesting.mp3","audio/odysseus_interesting.mp3","audio/odysseus_interesting.mp3","audio/odysseus_interesting.mp3"]
    arcas = ["audio/arcas_interesting.mp3","audio/arcas_interesting.mp3","audio/arcas_interesting.mp3","audio/arcas_interesting.mp3"]
    andromea = ["audio/andromeda_interesting.mp3","audio/andromeda_interesting.mp3","audio/andromeda_interesting.mp3","audio/andromeda_interesting.mp3"]
    
    if voice_model == "aura-2-thalia-en":
        return thalia
    elif voice_model == "aura-2-odysseus-en":
        return odysseus
    elif voice_model== "aura-2-arcas-en":
        return arcas
    else :
        return andromea

def run_audio_in_mod(user_input):
    model_selected = select_file(user_input) 
    return_file =play_random_audio(model_selected)
    playaudio(return_file)

def age_to_voice_model(age: int) -> str:
    if age <= 12:
        return "aura-2-thalia-en"      # younger/kid-friendly voice
    elif 13 <= age <= 19:
        return "aura-2-odysseus-en"    # teen voice
    elif 20 <= age <= 60:
        return "aura-2-arcas-en"       # adult voice
    else:
        return "aura-2-cora-en"   # senior-friendly voice

def model_selection(user_age):
    voice_model = age_to_voice_model(user_age)
    model_selected = select_file(voice_model)
    return voice_model,model_selected