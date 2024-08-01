import os
from elevenlabs.client import AsyncElevenLabs, ElevenLabs, RequestOptions, OutputFormat
import json
import base64
import requests
import uuid


client = AsyncElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
api_key = api_key=os.getenv("ELEVENLABS_API_KEY")

class GenerateAudioManager:
    
    def speech_with_subtitles(self, voice_id, text):
        temp_audio_path = f"temp_{uuid.uuid4().hex}.mp3"
        temp_subtitle_path = f"temp_{uuid.uuid4().hex}.json"
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            print(f"Error encountered, status: {response.status_code}, content: {response.text}")
            return None, None

        response_data = response.json()
        audio_bytes = base64.b64decode(response_data["audio_base64"])

        subtitles = []
        if response_data.get("alignment"):
            alignment = response_data["alignment"]
            for i, char in enumerate(alignment["characters"]):
                subtitle = {
                    "character": char,
                    "start_time": alignment["character_start_times_seconds"][i],
                    "end_time": alignment["character_end_times_seconds"][i]
                }
                subtitles.append(subtitle)

        with open(temp_subtitle_path, 'w') as f:
            json.dump(subtitles, f, indent=4)

        with open(temp_audio_path, 'wb') as f:
            f.write(audio_bytes)

        return temp_audio_path, temp_subtitle_path
    
            
    def speech_with_subtitles_streamed(self, voice_id, text, subtitle_file='subtitles.json', output_audio='output.mp3'):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream/with-timestamps"

        headers = {
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(
            url,
            json=data,
            headers=headers,
            stream=True
        )

        if response.status_code != 200:
            print(f"Error encountered, status: {response.status_code}, content: {response.text}")
            return

        audio_bytes = b""
        subtitles = []

        for line in response.iter_lines():
            if line:  # filter out keep-alive new lines
                json_string = line.decode("utf-8")
                response_dict = json.loads(json_string)

                audio_bytes_chunk = base64.b64decode(response_dict["audio_base64"])
                audio_bytes += audio_bytes_chunk

                if response_dict.get("alignment"):
                    alignment = response_dict["alignment"]
                    for i, char in enumerate(alignment["characters"]):
                        subtitle = {
                            "character": char,
                            "start_time": alignment["character_start_times_seconds"][i],
                            "end_time": alignment["character_end_times_seconds"][i]
                        }
                        subtitles.append(subtitle)

                    with open(subtitle_file, 'w') as f:
                        json.dump(subtitles, f, indent=4)

        with open(output_audio, 'wb') as f:
            f.write(audio_bytes)
        print(f"Audio saved to {output_audio}, subtitles saved to {subtitle_file}")

    def generate_sound_effect(self, text: str, output_path: str):
        print("Generating sound effects...")

        result = elevenlabs.text_to_sound_effects.convert(
            text=text,
            duration_seconds=8,  # Optional, if not provided will automatically determine the correct length
            prompt_influence=0.3,  # Optional, if not provided will use the default value of 0.3
        )

        with open(output_path, "wb") as f:
            for chunk in result:
                f.write(chunk)

        print(f"Audio saved to {output_path}")


if __name__ == "__main__":
    #api_key=os.getenv("ELEVENLABS_API_KEY")
    manager = GenerateAudioManager()
    
    # Example to generate speech with subtitles
    voice_id = "VCaeNZPsLqFDctIVc5Do"
    text = "big ones, small ones, ones as big as your head"
    manager.speech_with_subtitles(voice_id, text)
    
    # # Example to generate sound effects
    # effect_text = 'Epic battle sound'
    # output_path = 'effect_output.wav'
    # manager.generate_sound_effect(effect_text, output_path)