from flask import Flask, render_template, request, jsonify
import logging
import threading
import os
import signal
from arabic_reshaper import reshape
import bidi.algorithm as bidialg
from main import DrStoneMode, get_response_from_model, speak_text, keyboard, Model

app = Flask(__name__)

# تعطيل سجلات Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# متغيرات عالمية
program_running = False
stop_event = None
language = None  # لتخزين اللغة المختارة
messages = []  # قائمة لتخزين الرسائل التي ستظهر على الموقع
main_thread = None  # لتخزين العملية الرئيسية

# وظائف مشتركة
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

@app.route('/')
def index():
    """عرض الصفحة الرئيسية."""
    return render_template('index.html', messages=messages)

@app.route('/drstone')
def drstone():
    """عرض صفحة Dr. Stone."""
    return render_template('drstone.html', messages=messages)

@app.route('/command', methods=['POST'])
def command():
    """استقبال الأوامر من الأزرار."""
    global program_running, stop_event, language, main_thread

    cmd = request.form['command']

    if cmd == 'start':
        if not program_running:
            add_message("Welcome! Please choose a language.")
            return jsonify({"status": "success", "message": "Choose a language."})
        else:
            return jsonify({"status": "error", "message": "Already started."})

    elif cmd in ['english', 'arabic']:
        if not program_running:
            language = cmd.capitalize()
            add_message(f"Language set to: {language}")
            program_running = True
            stop_event = threading.Event()  # إنشاء حدث للتوقف
            main_thread = threading.Thread(target=run_drstone_mode)
            main_thread.start()
            add_message("Press SPACE to start speaking.")
            return jsonify({"status": "success", "message": f"Language set to: {language}. Dr. Stone Mode activated."})
        else:
            return jsonify({"status": "error", "message": "Already running."})

    elif cmd == 'stop':
        if program_running:
            stop_event.set()  # إيقاف العمليات الجارية
            if main_thread and main_thread.is_alive():
                try:
                    # إجبار الإيقاف باستخدام terminate (إذا كانت العملية لا تستجيب)
                    os.kill(os.getpid(), signal.SIGINT)  # إيقاف كامل البرنامج
                except Exception as e:
                    print(f"Error during forced stop: {e}")
            program_running = False
            language = None
            add_message("Stopped successfully.")
            return jsonify({"status": "success", "message": "Stopped successfully."})
        else:
            return jsonify({"status": "error", "message": "Not running."})

    elif cmd == 'restart':
        if program_running:
            stop_event.set()  # إيقاف العمليات الجارية أولاً
            program_running = False
            language = None
        program_running = True
        add_message("Restarted successfully. Please choose a language.")
        return jsonify({"status": "success", "message": "Restarted successfully."})

    else:
        return jsonify({"status": "error", "message": "Unknown command."})

def run_drstone_mode():
    """تشغيل وضع Dr. Stone مع إضافة الرسائل إلى القائمة."""
    def add_message_from_program(message):
        add_message(message)

    # تشغيل وضع Dr. Stone باللغة المختارة
    drstone_mode = DrStoneMode(
        language=language,
        detect_language_fn=detect_language,
        reshape_text_fn=reshape_text,
        get_response_fn=get_response_from_model,
        speak_text_fn=speak_text,
        keyboard_module=keyboard,
        vosk_model=load_vosk_model(language)
    )
    drstone_mode.run()

def load_vosk_model(language):
    """تحميل نموذج Vosk بناءً على اللغة."""
    if language == "English":
        print("Loading English Vosk model...")
        return Model(r"D:\ahmad\PYTHONPROJECT\vosk-model-small-en-us-0.15")  # المسار المطلق للنموذج الإنجليزي
    elif language == "Arabic":
        print("Loading Arabic Vosk model...")
        return Model(r"D:\ahmad\PYTHONPROJECT\vosk-model-ar-mgb2-0.4")  # المسار المطلق للنموذج العربي

def add_message(message):
    """إضافة رسالة جديدة إلى القائمة وإزالة الرسائل القديمة إذا زادت عن 20."""
    print(message)  # عرض الرسالة في Terminal
    messages.append(message)
    if len(messages) > 20:
        messages.pop(0)

@app.route('/get_messages', methods=['GET'])
def get_messages():
    """إرجاع جميع الرسائل الحالية."""
    return jsonify({"messages": messages})

if __name__ == '__main__':
    app.run(debug=True)