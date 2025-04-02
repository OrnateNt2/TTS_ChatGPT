from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from openai import OpenAI
from dotenv import load_dotenv
import os
import tempfile

app = Flask(__name__)
app.secret_key = os.urandom(24)  # для flash-сообщений

# Загрузка переменных окружения из .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("API ключ не найден в .env файле.")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.proxyapi.ru/openai/v1",
)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Получаем текст из поля формы
        text = request.form.get('text')
        # Или пытаемся прочитать загруженный файл
        uploaded_file = request.files.get('file')
        input_text = None
        if uploaded_file and uploaded_file.filename != '':
            try:
                input_text = uploaded_file.read().decode('utf-8')
            except Exception as e:
                flash("Ошибка чтения файла: " + str(e))
                return redirect(url_for('index'))
        elif text:
            input_text = text
        else:
            flash("Введите текст или загрузите файл с текстом.")
            return redirect(url_for('index'))
        
        # Генерируем аудио с помощью TTS API
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio_path = temp_audio.name
        
        try:
            with client.audio.speech.with_streaming_response.create(
                model="tts-1-hd",  # Используем модель tts-1-hd
                voice="nova",      # Голос можно менять: alloy, echo, fable, onyx, nova, shimmer
                input=input_text,
            ) as response:
                response.stream_to_file(temp_audio_path)
        except Exception as e:
            flash("Ошибка при генерации аудио: " + str(e))
            os.remove(temp_audio_path)
            return redirect(url_for('index'))
        
        # Отправляем сгенерированный файл пользователю
        return send_file(temp_audio_path, as_attachment=True, download_name="speech.mp3")
    return render_template("index.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
