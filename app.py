from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Murder Mystery Game"

@app.route('/log')
def log():
    log_file = 'conversation_log.txt'
    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            log_content = file.read()
    else:
        log_content = "No conversation log available."
    return render_template('log.html', log_content=log_content)

if __name__ == "__main__":
    app.run(debug=True)
