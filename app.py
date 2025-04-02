import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from openai import OpenAI
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Загрузка переменных окружения из .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("API ключ не найден в .env файле.")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.proxyapi.ru/openai/v1",
)

# Папка для аудиофайлов
audio_dir = os.path.join(app.root_path, "static", "audio")
os.makedirs(audio_dir, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Чтение текста из поля или файла
        text = request.form.get('text')
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
        
        # Дополнительные параметры
        model = request.form.get('model') or "tts-1-hd"
        voice = request.form.get('voice') or "nova"
        instructions = request.form.get('instructions', '').strip()
        
        # Генерация уникального имени файла
        filename = f"speech_{uuid.uuid4().hex}.mp3"
        audio_file_path = os.path.join(audio_dir, filename)
        
        # Параметры для запроса
        params = {
            "model": model,
            "voice": voice,
            "input": input_text,
        }
        if instructions:
            params["instructions"] = instructions
        
        try:
            with client.audio.speech.with_streaming_response.create(**params) as response:
                response.stream_to_file(audio_file_path)
        except Exception as e:
            flash("Ошибка при генерации аудио: " + str(e))
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return redirect(url_for('index'))
        
        # Формируем URL для доступа к файлу
        audio_url = url_for('static', filename=f"audio/{filename}")
        return render_template("result.html", audio_url=audio_url)
    return render_template("index.html")

if __name__ == '__main__':
    # Приложение будет доступно по ip:5000 (например, 194.87.130.222:5000)
    app.run(host='0.0.0.0', port=5000)
