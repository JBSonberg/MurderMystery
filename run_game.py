from flask import Flask, render_template, send_from_directory, jsonify
from MurderMystery import Game
from openai import OpenAI
import threading
import os
import json
import logging

app = Flask(__name__)
SUBTITLE_FILE = 'subtitles.json'
LOG_DIR = 'logs'
OUTPUT_AUDIO = 'output.mp3'
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def read_log_files():
    logs = []
    for i in range(1, 7):
        log_file = os.path.join(LOG_DIR, f"group_{i}_log.txt")
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as file:
                logs.append(file.read())
        else:
            logs.append(f"Log file for group {i} not found.")
    return logs

@app.route('/')
def home():
    logs = read_log_files()
    return render_template('index.html', logs=logs)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/audio')
def audio():
    print(f"Serving audio file: {OUTPUT_AUDIO}")
    audio_path = os.path.join(os.getcwd(), OUTPUT_AUDIO)
    return send_from_directory(os.path.dirname(audio_path), os.path.basename(audio_path))


@app.route('/subtitles')
def subtitles():
    subtitle_path = os.path.join(os.getcwd(), SUBTITLE_FILE)
    print(f"Serving subtitle file: {subtitle_path}")
    with open(subtitle_path, 'r', encoding='utf-8') as file:
        subtitle_data = json.load(file)
    return jsonify(subtitle_data)

@app.route('/subs')
def subs():
    return render_template('subs.html')

def run_game():
    # Start the game
    client = OpenAI()
    designer_thread = client.beta.threads.create()
    Designer = client.beta.assistants.retrieve("asst_thL9KhFcTjZxLqhIlZGnWJZQ")
    game = Game(client, designer_thread, Designer)
    game.main()

if __name__ == "__main__":
    # Run the Flask app in a separate thread
    flask_thread = threading.Thread(target=app.run, kwargs={'port': 5000})
    flask_thread.start()

     #Run the game in the main thread
    run_game()
