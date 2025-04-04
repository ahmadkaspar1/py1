import pyaudio
from vosk import KaldiRecognizer
import threading
import time

class DrStoneMode:
    def __init__(self, language, detect_language_fn, reshape_text_fn, get_response_fn, speak_text_fn, keyboard_module, vosk_model):
        self.language = language
        self.detect_language = detect_language_fn
        self.reshape_text = reshape_text_fn
        self.get_response_from_model = get_response_fn
        self.speak_text = speak_text_fn
        self.keyboard = keyboard_module  # إضافة keyboard كمعامل
        self.model = vosk_model  # نموذج Vosk الذي تم تمريره من main.py
        self.stream = self.setup_audio_stream()

    def setup_audio_stream(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        stream.start_stream()
        return stream

    def recognize_speech(self):
        rec = KaldiRecognizer(self.model, 16000)
        recognized_text = ""

        while self.keyboard.is_pressed('space'):  # استمرار التسجيل طالما زر المسافة مضغوط
            try:
                data = self.stream.read(1024)
                if len(data) == 0:
                    break

                if rec.AcceptWaveform(data):
                    result = rec.Result()
                    text = eval(result)["text"]
                    if text:
                        recognized_text += text + " "
                else:
                    partial_result = rec.PartialResult()
                    if self.language == "Arabic" and '"partial"' in partial_result:
                        partial_text = eval(partial_result)["partial"]
                        print(f"Partial: {self.reshape_text(partial_text)}", end="\r")
                    else:
                        partial_text = eval(partial_result)["partial"]
                        print(f"Partial: {partial_text}", end="\r")
            except Exception as e:
                print(f"Error: {e}")
                continue

        final_result = rec.FinalResult()
        final_text = eval(final_result)["text"]
        if final_text:
            recognized_text += final_text

        return recognized_text.strip()

    def run(self):
        print("\n--- Dr. Stone Mode Activated ---")
        print("Press and hold 'spacebar' to talk. Press 'q' to quit.")

        stop_event = threading.Event()

        try:
            while True:
                # التحقق من زر المسافة
                if self.keyboard.is_pressed('space'):
                    print("\n--- Recording started ---")
                    recognized_text = self.recognize_speech()
                    
                    if recognized_text.strip():
                        if self.language == "Arabic":
                            reshaped_recognized_text = self.reshape_text(recognized_text.strip())
                            print(f"You said (Arabic): {reshaped_recognized_text}")
                        else:
                            print(f"You said (English): {recognized_text.strip()}")

                        response = self.get_response_from_model([{"role": "user", "content": recognized_text.strip()}])

                        if self.language == "Arabic":
                            reshaped_response = self.reshape_text(response)
                            print(f"API Response (Arabic): {reshaped_response}")
                        else:
                            print(f"API Response (English): {response}")

                        print("\nSpeaking response... (Press 'space' to interrupt)")
                        stop_event.clear()  # إعادة تعيين الحدث
                        speaking_thread = threading.Thread(target=self.speak_text, args=(response, stop_event, self.detect_language, self.reshape_text))
                        speaking_thread.start()

                        # التحقق المستمر من زر المسافة لإيقاف الكلام
                        while speaking_thread.is_alive():
                            if self.keyboard.is_pressed('space'):  # إذا تم الضغط على المسافة
                                stop_event.set()  # إيقاف الكلام
                                print("\nInterrupted! Listening again...")
                                break
                            time.sleep(0.1)  # تأخير بسيط لتجنب استهلاك المعالج

                # التحقق من زر الخروج
                elif self.keyboard.is_pressed('q'):
                    print("\nExiting Dr. Stone Mode...")
                    break

        finally:
            self.stream.stop_stream()
            self.stream.close()
            print("--- Dr. Stone Mode Deactivated ---")