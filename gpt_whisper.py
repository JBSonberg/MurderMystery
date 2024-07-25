import openai
from openai import OpenAI
import os
import pyaudio
import wave
import keyboard
from rich import print

client = OpenAI()

class GPTWhisperManager:
    def __init__(self):
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("[red]API key not found. Please set the OPENAI_API_KEY environment variable or set it in the script.")
            raise ValueError("API key not found.")
        else:
            openai.api_key = api_key
            print("[green]API key found and set.")

    def record_audio(self, filename="temp_audio.wav"):
        # Recording parameters
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024

        # Initialize PyAudio
        audio = pyaudio.PyAudio()

        # Start Recording
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        print("Recording... Press = to stop recording.")

        frames = []

        while not keyboard.is_pressed('='):
            data = stream.read(CHUNK)
            frames.append(data)

        print("Finished recording.")

        # Stop Recording
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save the recorded data as a WAV file
        wave_file = wave.open(filename, 'wb')
        wave_file.setnchannels(CHANNELS)
        wave_file.setsampwidth(audio.get_sample_size(FORMAT))
        wave_file.setframerate(RATE)
        wave_file.writeframes(b''.join(frames))
        wave_file.close()

        return filename

    def transcribe_audio(self, filename):
        with open(filename, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                language="en",
                temperature=1,
                response_format="text",
            )
        return transcript

    def speechtotext_from_mic_continuous(self):
        try:
            audio_filename = self.record_audio()
            transcription = self.transcribe_audio(audio_filename)
            os.remove(audio_filename)  # Clean up the temporary file
            return transcription
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""

# Test function to list available GPT models
def test_list_gpt_models():
    try:
        models = openai.Model.list()
        print("Available models:")
        for model in models.data:
            print(model.id)
    except Exception as e:
        print(f"An error occurred while fetching models: {e}")

# Test function for recording and transcribing audio
def test_gpt_whisper_manager():
    manager = GPTWhisperManager()
    print("Press F4 to start recording. Press F3 to stop recording.")
    while True:
        if keyboard.is_pressed('f4'):
            transcription = manager.speechtotext_from_mic_continuous()
            print(f"Transcription: {transcription}")
            break

if __name__ == "__main__":
    print("Testing available GPT models with the provided API key.")
    test_list_gpt_models()
    print("Testing GPT Whisper Manager.")
    test_gpt_whisper_manager()
