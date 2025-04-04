import threading
import pyaudio
from vosk import Model, KaldiRecognizer
import keyboard  # استيراد مكتبة keyboard هنا
from arabic_reshaper import reshape
import bidi.algorithm as bidialg
import requests
import json
from gtts import gTTS
import os
from playsound import playsound
import pyttsx3
import tempfile
import time
import sys

# استيراد المودات
from drstone_mode import DrStoneMode

# وظائف عامة
def choose_language():
    print("Choose a language:")
    print("1. English")
    print("2. Arabic")
    choice = input("Enter your choice (1 or 2): ")
    if choice == "1":
        return "English"
    elif choice == "2":
        return "Arabic"
    else:
        print("Invalid choice. Defaulting to English.")
        return "English"

def detect_language(text):
    """Detect if text is Arabic or English based on Unicode characters."""
    for char in text:
        if '\u0600' <= char <= '\u06FF':  # Arabic Unicode range
            return 'ar'
    return 'en'

def reshape_text(text):
    """Reshape Arabic text for proper display."""
    reshaped = reshape(text)
    return bidialg.get_display(reshaped)

def get_response_from_model(messages):
    api_key = "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"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "openai/gpt-3.5-turbo",  # Model name
        "messages": messages,            # List of messages
        "temperature": 0.7,              # Adjust creativity
        "max_tokens": 200                # Maximum number of tokens
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Error occurred: {response.status_code}, {error_message}"
    except Exception as e:
        return f"An error occurred during the request: {e}"

def speak_text(text, stop_event, detect_language_fn, reshape_text_fn):
    """Convert text to speech based on detected language and allow interruption."""
    language = detect_language_fn(text)
    
    if language == 'ar':  # إذا كان النص عربيًا
        try:
            tts = gTTS(text=text, lang='ar')
            
            # إنشاء ملف مؤقت فريد
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_filename = temp_file.name
                tts.save(temp_filename)
            
            while not stop_event.is_set():  # Check if stop event is triggered
                playsound(temp_filename)
                break
            
            os.remove(temp_filename)  # حذف الملف بعد الانتهاء
        except Exception as e:
            print(f"Arabic TTS Error: {e}")
    elif language == 'en':  # إذا كان النص إنجليزيًا
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[0].id)  # اختيار الصوت الإنجليزي
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 1.0)
            
            def on_word(name, location, length):
                if stop_event.is_set():  # Stop speaking if interrupted
                    engine.stop()
            
            engine.connect('started-word', on_word)
            engine.say(text)
            engine.startLoop(False)
            while not stop_event.is_set():  # Keep running until interrupted
                engine.iterate()
                time.sleep(0.1)  # تأخير بسيط لتجنب استهلاك المعالج
            engine.endLoop()
        except Exception as e:
            print(f"English TTS Error: {e}")
    else:
        print("Unsupported language for TTS.")

# نقطة الدخول الرئيسية
def main():
    print("Welcome to the Chat Program!")
    
    # اختيار اللغة عند بدء التشغيل
    language = choose_language()
    print(f"Language set to: {language}")

    # تحميل نموذج Vosk بناءً على اللغة
    if language == "English":
        print("Loading English Vosk model...")
        vosk_model = Model(r"D:\ahmad\PYTHONPROJECT\vosk-model-small-en-us-0.15")  # المسار المطلق للنموذج الإنجليزي
    elif language == "Arabic":
        print("Loading Arabic Vosk model...")
        vosk_model = Model(r"D:\ahmad\PYTHONPROJECT\vosk-model-ar-mgb2-0.4")  # المسار المطلق للنموذج العربي

    # تحميل المودات
    drstone_mode = DrStoneMode(language, detect_language, reshape_text, get_response_from_model, speak_text, keyboard, vosk_model)

    # وظيفة إعادة التشغيل
    def restart_program():
        print("\nRestarting program...")
        os.execl(sys.executable, sys.executable, *sys.argv)

    # تشغيل رصد الضغط على مفتاح 'r' في خلفية البرنامج
    restart_thread = threading.Thread(target=lambda: keyboard.wait('r'))
    restart_thread.daemon = True
    restart_thread.start()

    # تشغيل Dr. Stone Mode مباشرة بدون قائمة
    print("\n--- Starting Dr. Stone Mode ---")
    drstone_mode.run()

if __name__ == "__main__":
    main()