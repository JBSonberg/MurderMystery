import openai
import os
from openai import OpenAI
import random
import datetime
import requests
import json
import time
import threading
import re
import queue
import shutil
from obs_websockets import OBSWebsocketsManager
from ElevenLabs import GenerateAudioManager
from audio_player import AudioManager
from CharacterCreator import CharacterCreator
from gpt_whisper import GPTWhisperManager

# Initialize API Key
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    print("[red]API key not found. Please set the OPENAI_API_KEY environment variable or set it in the script.")
else:
    openai.api_key = api_key
    print("[green]API key found and set.")

azure_subscription_key = os.environ.get('AZURE_BG-REMOVER')
azure_endpoint = "https://bg-remover.cognitiveservices.azure.com/"

class SetTheStage:
    def __init__(self, client, designer_thread, Designer, obs_websockets_manager):
        self.client = client
        self.designer_thread = designer_thread
        self.designer = Designer
        self.obs_websockets_manager = obs_websockets_manager

    def generate_image_description(self, scene_prompt):
        self.client.beta.threads.messages.create(
            thread_id=self.designer_thread.id,
            role='user',
            content=scene_prompt
        )
        
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.designer_thread.id,
            assistant_id=self.designer.id,
            response_format="auto"
        )

        scene_description = None
        if run.status == 'completed':
            thread_messages = self.client.beta.threads.messages.list(
                thread_id=self.designer_thread.id,
                order='desc',
                limit=1,
            )
            for message in thread_messages.data:
                if message.role == 'assistant' and message.content[0].type == 'text':
                    scene_description = message.content[0].text.value
                    print(scene_description)
        return scene_description    
    
    def decide_the_theme(self):
        themes = ["fairytale", "horror", "scifi", "documentary", "fantasy", "mystery", 
                  "romance", "comedy", "noir", "thriller", "post-apocalyptic", "steampunk", 
                  "historical drama", "adventure", "superhero"
                  ]
        time_frames = ["medieval", "prehistoric", "future", "alternate reality", "modern day", 
                       "ancient times", "Victorian era", "Roaring Twenties", "Space Age", 
                       "Ice Age", "Bronze Age", "Stone Age", "Industrial Revolution", "Cyberpunk", 
                       "Utopian future", "Dystopian future"
                       ]

        theme = random.choice(themes)
        time_frame = random.choice(time_frames)

        scene_prompt = f"The scene has a {theme} setting and is cast in a {time_frame} time frame."
        scene_title = f"{theme}_{time_frame}"

        return scene_prompt, scene_title
    
    def create_background_image(self, scene_prompt, scene_title):
        file_name = f'{scene_title}.png'
        folder_path = r"C:\Users\Jesse\Pictures\StreamAssets\Scenes"
        file_path = os.path.join(folder_path, file_name)
        scene_description = self.generate_image_description(scene_prompt)          
        response = self.client.images.generate(
            model='dall-e-3',
            prompt=f'Create our scene \n\n{scene_description} \n\n***Ideal Picture***\n\nwill be standing height\nThe image should be from ground level\nThere will be no main characters in the image\nwill be atmospheric but not be overwhelmed with details',
            n=1,
            size="1792x1024",
            response_format='url'
        )
        image_url = response.data[0].url
        generated_image = requests.get(image_url).content
        with open(file_path, "wb") as image_file:
            image_file.write(generated_image)
        self.set_the_background(file_path)            
        return file_path

    def set_the_background(self, file_path):
        self.obs_websockets_manager.set_filter_visibility('Background', 'PostDeath', filter_enabled=True)
        self.obs_websockets_manager.set_image_file_path('Background', file_path)
       
    def main(self):
        scene_prompt, scene_title = self.decide_the_theme()
        file_path = self.create_background_image(scene_prompt, scene_title)
        print(file_path)
        return scene_prompt, file_path

class FillTheRoom:
    def __init__(self, create_characters):
        self.all_characters = []
        self.create_characters = create_characters

    def get_number_of_groups(self):
        while True:
            try:
                num_groups = int(input("Enter the number of groups: "))
                if num_groups > 0:
                    return num_groups
                else:
                    print("Please enter a positive number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def create_groups(self, num_groups, scene_prompt):
        all_characters = []
        character_details_by_group = {}

        # First loop to gather character details for each group
        for group_num in range(1, num_groups + 1):
            print(f"\nCreating characters for Group {group_num}:")
            character_details = self.create_characters.main(scene_prompt, group_num)  # Call the main function from CharacterCreator
            character_details_by_group[group_num] = character_details

        # Second loop to create characters using the gathered details
        for group_num in range(1, num_groups + 1):
            print(f"\nCreating characters for Group {group_num}:")
            character_details = character_details_by_group.get(group_num)
            characters = self.create_characters.create_all_characters(character_details, scene_prompt, group_num)  # Call the main function from CharacterCreator
            if characters:  # Check if the returned value is not None
                all_characters.extend(characters)
            else:
                print(f"[Warning] Group {group_num} returned no characters.")

        return all_characters

    def save_game(self, background):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join("saved_games", f"savegame_{timestamp}.json")
        thread = self.client.beta.threads.create()
        narator_thread = thread.id 
        save_data = {
            "characters": [
                {
                    "name": character[0],
                    "assistant_id": character[1],
                    "thread_id": character[2],
                    "killer": character[3],
                    "victim": character[4],
                    "relationship_group": character[5],
                    "voice": character[6],
                    "picture": character[7],
                    "obs": character[8]
                } for character in self.all_characters
            ],
            "background": background,
            "narator_thread": narator_thread
        }

        os.makedirs("saved_games", exist_ok=True)
        with open(filename, 'w') as file:
            json.dump(save_data, file, indent=4)
        print(f"Game saved to {filename}")
        return narator_thread, filename
                
    def main(self, scene_prompt, load_game=False):
        if load_game:
            return None  # No characters to load initially in this case
        
        num_groups = self.get_number_of_groups()
        self.all_characters = self.create_groups(num_groups, scene_prompt)

        return [
            {
                "name": character[0],
                "assistant_id": character[1],
                "thread_id": character[2],
                "killer": character[3],
                "victim": character[4],
                "relationship_group": character[5],
                "voice": character[6],
                "picture": character[7],
                "obs": character[8]
            } for character in self.all_characters
        ]

class ConversationManager:
    def __init__(self, client, characters, obs_websockets_manager, narator, audio_manager, elevenlabs_manager, log_dir="logs"):
        self.client = client
        self.characters = characters
        self.log_dir = log_dir
        self.obs_websockets_manager = obs_websockets_manager
        self.narator = narator
        self.audio_manager = audio_manager
        self.elevenlabs_manager = elevenlabs_manager
        os.makedirs(self.log_dir, exist_ok=True)
        self.audio_queue = queue.Queue()

    def log_interaction(self, group_index, message):
        clean_message = self.sanitize_message(message)
        log_file = os.path.join(self.log_dir, f"group_{group_index + 1}_log.txt")
        with open(log_file, 'w', encoding='utf-8') as file:
            file.write(f"{clean_message}\n")
    
    def sanitize_message(self, message):
        # Remove leading/trailing whitespace
        message = message.strip()
        # Remove multiple spaces
        message = re.sub(r'\s+', ' ', message)
        # Remove any unwanted characters (example: non-ASCII characters)
        message = re.sub(r'[^\x00-\x7F]+', '', message)
        return message

    def send_message(self, speaker_name, message, listener_thread_id):
        self.client.beta.threads.messages.create(
            thread_id=listener_thread_id,
            role="user",
            content=f"[{speaker_name}] {message}"
        )

    def get_response(self, thread_id, assistant_id):
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
            response_format="auto"
        )

        time.sleep(0.5)

        ai_response = None
        if run.status == 'completed':
            thread_messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order='desc',
                limit=1,
            )
            for message in thread_messages.data:
                if message.role == 'assistant' and message.content[0].type == 'text':
                    ai_response = message.content[0].text.value

        return ai_response

    def interact(self, speaker, listeners, message):
        for listener in listeners:
            self.send_message(speaker, message, listener["thread_id"])

        responder = random.choice(listeners)
        response = self.get_response(responder["thread_id"], responder["assistant_id"])

        return response

    def group_conversation(self, group, group_index, num_exchanges=5):
        message = '[Game Master] Remember to stay in characters at all times!'
        self.narator.send_user_message_to_all(message, self.characters)
        message = "[Approaches]"
        for _ in range(num_exchanges):
            for i in range(len(group)):
                speaker = group[i]
                listeners = [char for j, char in enumerate(group) if j != i]
                response = self.interact(speaker, listeners, message)
                self.log_interaction(group_index, message)
                print(f"{speaker['name']} to group: {message}")
                message = response
                if group_index == 1:
                    self.obs_websockets_manager.set_source_visibility('Main', 'TheLogs', True)
                    random_number = random.randint(4, 8)
                    time.sleep(random_number)
                    self.obs_websockets_manager.set_source_visibility('Main', 'TheLogs', False)
                else:
                    random_number = random.randint(4, 8)
                    time.sleep(random_number)

    def create_groups(self, num_groups=6):
        random.shuffle(self.characters)
        groups = [[] for _ in range(num_groups)]
        for index, character in enumerate(self.characters):
            groups[index % num_groups].append(character)
        return groups 
    
    def message_to_killer(self, message):
        # Retrieve killer character from self.characters
        killer_character = next((character for character in self.characters if character["killer"]), None)
        victim_character = next((character for character in self.characters if character["victim"]), None)
        
        # Define possible deaths
        deaths = [
            "stabbed with a knife", "shot with a gun", "poisoned", "strangled",
            "bludgeoned with a blunt object", "pushed off a height", "drowned",
            "suffocated with a pillow", "burned in a fire", "electrocuted", "hit by a car",
            "pushed in front of a moving vehicle", "crushed by a heavy object",
            "run over by a vehicle", "hit with a heavy object", "injected with a lethal substance",
            "pushed onto train tracks", "hit with a bat", "attacked by a wild animal",
            "pushed into a vat of acid", "blown up in an explosion", "pushed into a furnace",
            "locked in a freezer", "left to die in the wilderness", "drowned in a bathtub",
            "thrown from a moving vehicle", "locked in a car trunk", "pushed off a cliff", "thrown out of a window",
            "killed in a staged accident", "attacked with a sword", "attacked with a machete",
            "hit with a crowbar", "hit with a hammer", "poisoned with gas", "pushed into a river",
            "left to freeze in the cold", "locked in a sauna", "attacked with an axe", "attacked with a chainsaw",
            "left to die of dehydration", "pushed into quicksand", "attacked with a spear", "attacked with a crossbow",
            "left to be bitten by venomous snakes", "thrown into a pit of spikes", "hit with a rock", "attacked with a bottle",
            "attacked with a piece of broken glass", "thrown onto sharp objects", "hit with a metal pipe", "attacked with a wrench",
            "pushed into an industrial machine", "thrown into a wood chipper", "left in a locked room to suffocate",
            "poisoned with contaminated food", "attacked with a shovel", "hit with a fire extinguisher", "attacked with a garden tool",
            "locked in a sealed room and poisoned", "attacked with a syringe", "thrown into a pit of wild animals",
            "left to die in a collapsing building", "left to die in a burning building", "left to drown in quicksand", "thrown into an icy lake"
        ]
        
        # Select a random death method
        death = random.choice(deaths)

        # Check if a killer character was found
        if not killer_character:
            print("No killer character found.")
            return
        
        # Check if a victim character was found
        if not victim_character:
            print("No victim character found.")
            return
        
        # Get victim's name
        victim = victim_character["name"]
        
        # Get killer's thread ID
        killer_thread_id = killer_character["thread_id"]
        
        # Set default message if none provided
        if message is None:
            message = f"Keep vigilant, it is almost time to kill {victim} by {death}"
        
        # Send the message
        self.client.beta.threads.messages.create(
            thread_id=killer_thread_id,
            role="user",
            content=f"[Game Master] {message}"
        )
        return death
    
    def message_to_victim(self, message):
        # Retrieve killer character from self.characters
        killer_character = next((character for character in self.characters if character["killer"]), None)
        victim_character = next((character for character in self.characters if character["victim"]), None)

        # Check if a killer character was found
        if not killer_character:
            print("No killer character found.")
            return
        
        # Check if a victim character was found
        if not victim_character:
            print("No victim character found.")
            return
        
        # Get killer's thread ID
        victim_thread_id = victim_character["thread_id"]
        killer = killer_character["name"]
        # Set default message if none provided
        if message is None:
            message = f"You're excited to enjoy the festivities tonight."
        
        # Send the message
        self.client.beta.threads.messages.create(
            thread_id=victim_thread_id,
            role="user",
            content=f"[Game Master] {message}\n\n Don't directly tell anyone but {killer} is here to kill you. Be cautious of them and let a few clues slip in your conversations."
        )
                
    def parallel_conversations(self, groups, num_exchanges=5):
        killer_victim_same_group = False
        death = self.message_to_killer(message=False)
        self.message_to_victim(message=False)
        prompt = "The party is going well so far! Describe what you see in the room. Don't be too specific with names for I haven't given any to you yet."
        greeting = self.narator.greeting(prompt)
        self.narator.send_message_to_all(greeting, self.characters)
        
        while not killer_victim_same_group:
            threads = []
            
            # prompt = "The party is going well so far! Describe what you see in the room. Don't be too specific with names for I haven't given any to you yet."
            # greeting = self.narator.greeting(prompt)
            # self.narator.send_message_to_all(greeting, self.characters)
            self.obs_websockets_manager.stop_background_movement()
            self.obs_websockets_manager.congregate_characters('Characters', groups, move_step = 8, delay = 0.1)
            self.obs_websockets_manager.start_background_movement('Characters', groups, move_step=2, delay=.1)
            self.obs_websockets_manager.set_source_visibility('Main', 'TheLogs', True)
            self.obs_websockets_manager.set_source_visibility('Main', 'Crowd', True)

            for group_index, group in enumerate(groups):
                thread = threading.Thread(target=self.group_conversation, args=(group, group_index, num_exchanges))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            killer_victim_same_group = self.check_killer_victim_same_group(groups)
            
            if killer_victim_same_group:
                print("Killer and victim are in the same group. Ending conversations.")
                # Call the method to handle the murder scenario here
                victim = self.handle_murder(death)
                break
            else:
                print("Killer and victim are not in the same group. Reorganizing groups.")
                # Reorganize groups and continue the loop
                self.message_to_killer(
                    message="You're blending in nicely, Be sure to 'accidentally' give out clues. Everyone you talk to will later be interviewed about the murder and we want there to be evidence leading to you, but dont make it too easy.")
                self.message_to_victim(message="You're having fun but are feeling more and more uneasy.")
                groups = self.create_groups()
        return victim, death
                
    def check_killer_victim_same_group(self, groups):
        for group in groups:
            has_killer = any(character['killer'] for character in group)
            has_victim = any(character['victim'] for character in group)
            if has_killer and has_victim:
                return True
        return False

    def handle_murder(self, death):
        # Find the victim character
        victim = None
        for character in self.characters:
            if character['victim']:
                victim = character
                break
        
        if victim:
            self.obs_websockets_manager.set_source_visibility('Main', 'Crowd', False)
            self.obs_websockets_manager.set_source_visibility('Main', 'TheLogs', source_visible=False)
            self.obs_websockets_manager.lightning()
            self.audio_manager.play_audio('Sounds\Lightning.mp3', sleep_during_playback=False, delete_file=False, play_using_music=False)
            initial_prompt = f'{victim["name"]} was murdered! They were {death}\n\n Now set the stage for our protagonist to come in and try to solve the crime.'
            message = self.narator.greeting(initial_prompt)
            self.narator.send_message_to_all(message, self.characters)
            self.obs_websockets_manager.set_source_visibility('Main', 'GameScreen', source_visible=False)
            self.obs_websockets_manager.stop_background_movement()
            self.obs_websockets_manager.arrange_characters_in_crescent('Characters', num_groups=6, num_characters_per_group=6, center_x=850, center_y=600, ellipse_width=1300, ellipse_height=550, screen_width=1920, screen_height=1080)
            self.obs_websockets_manager.death_position('Characters', victim['obs'])
            input('Press Enter to turn lights back on')
            self.obs_websockets_manager.set_source_visibility('Main', 'GameScreen', source_visible=True)
            self.obs_websockets_manager.lightning()
            self.audio_manager.play_audio('Sounds\Lightning.mp3', sleep_during_playback=False, delete_file=False, play_using_music=False)
            self.obs_websockets_manager.set_source_visibility('Main', 'DeathZoom', source_visible=True)
            print(f"{victim['name']} has been murdered. Begin Investigations.")
            return victim
        else:
            print("Error: No victim found.")

    def post_murder_reactions(self, victim, death):
        characters = [char for char in self.characters if not char['victim']]
        random.shuffle(characters)

        message = f"{victim['name']} has been found dead! They were {death}! You think you know who did it! It was someone you met at this party. Call them out in front of everyone."

        def generate_responses():
            for character in characters:
                response = self.interact('Game Master', [character], message)
                temp_audio_path, temp_subtitle_path = self.elevenlabs_manager.speech_with_subtitles(character['voice'], response)
                
                if temp_audio_path and temp_subtitle_path:
                    self.audio_queue.put((temp_audio_path, temp_subtitle_path, character))

        # Run the response generation in a separate thread
        generate_thread = threading.Thread(target=generate_responses)
        generate_thread.start()

        # Start processing the queue after a short delay
        input('wait for audio to start coming in then hit enter')
        self.process_audio_queue()

        # Wait for the response generation thread to finish
        generate_thread.join()
                
    def process_audio_queue(self):
        while not self.audio_queue.empty():
            temp_audio_path, temp_subtitle_path, character = self.audio_queue.get()

            final_audio_path = "output.mp3"
            final_subtitle_path = "subtitles.json"

            shutil.move(temp_audio_path, final_audio_path)
            shutil.move(temp_subtitle_path, final_subtitle_path)
            self.obs_websockets_manager.pull_to_front_and_smoothly_enlarge('Characters', character['obs'], move_step = 6, step_delay=0.05)
            print(f"Playing audio for {character['name']}.")
            self.obs_websockets_manager.set_source_visibility('Main', 'TheSubs', source_visible=True)
            input('Continue? Press Enter to move to the next reaction.')
            self.obs_websockets_manager.smoothly_reduce_and_move_back('Characters', character['obs'], move_step=6, step_delay=.1)
        
class Narator:
    def __init__(self, client, elevenlabs_manager, audio_manager, obs_websockets_manager, narator_thread):
        self.client = client
        self.narator = self.client.beta.assistants.retrieve("asst_ysE9ZCPUe7dFXstMZmLzvaBq")  # Replace with your narator assistant ID
        self.narator_thread = narator_thread
        self.elevenlabs_manager = elevenlabs_manager
        self.audio_manager = audio_manager
        self.obs_websockets_manager = obs_websockets_manager

    def greeting(self, initial_prompt):
        self.client.beta.threads.messages.create(
            thread_id=self.narator_thread,
            role="user",
            content=initial_prompt
        )
        
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.narator_thread,
            assistant_id=self.narator.id,
            response_format="auto"
        )

        time.sleep(0.5)

        greeting = None
        if run.status == 'completed':
            thread_messages = self.client.beta.threads.messages.list(
                thread_id=self.narator_thread,
                order='desc',
                limit=1,
            )
            for message in thread_messages.data:
                if message.role == 'assistant' and message.content[0].type == 'text':
                    greeting = message.content[0].text.value

        return greeting
    
    def send_message_to_all(self, message, characters):
        def task():
            for character in characters:
                self.client.beta.threads.messages.create(
                    thread_id=character['thread_id'],
                    role="user",
                    content=f"[Narrator] {message}"
                )
            self.elevenlabs_manager.speech_with_subtitles_streamed("ZF6FPAbjXT4488VcRRnw",message)
            self.obs_websockets_manager.set_source_visibility('Main', 'TheSubs', source_visible=False)
            self.obs_websockets_manager.set_source_visibility('Main', 'TheLogs', source_visible=False)
            self.obs_websockets_manager.set_source_visibility('Main', 'TheSubs', source_visible=True)
        threading.Thread(target=task).start()
        
    def send_message_to_user(self, message):
        def task():
            self.elevenlabs_manager.speech_with_subtitles_streamed("ZF6FPAbjXT4488VcRRnw",message)
            self.obs_websockets_manager.set_source_visibility('Main', 'TheSubs', source_visible=False)
            self.obs_websockets_manager.set_source_visibility('Main', 'TheLogs', source_visible=False)
            self.obs_websockets_manager.set_source_visibility('Main', 'TheSubs', source_visible=True)
        threading.Thread(target=task).start()
        
    def send_user_message_to_all(self, message, characters):
        for character in characters:
            self.client.beta.threads.messages.create(
                thread_id=character['thread_id'],
                role="user",
                content=f"[Game Master] {message}"
            )

class InterviewManager:
    def __init__(self, client, characters, elevenlabs_manager, whisper, obs_websockets_manager, narator):
        self.client = client
        self.characters = characters
        self.elevenlabs_manager = elevenlabs_manager
        self.whisper = whisper
        self.obs_websockets_manager = obs_websockets_manager
        self.narator = narator
        self.interviewing = False

    def list_characters(self):
        # Return a list of characters available for interview
        available_characters = [char for char in self.characters if not char['victim']]
        for index, char in enumerate(available_characters, 1):
            print(f"{index}. {char['name']}")
        return available_characters

    def select_character(self, char_index):
        available_characters = self.list_characters()
        if 1 <= char_index <= len(available_characters):
            return available_characters[char_index - 1]
        else:
            return None

    def interview_character(self, character):
        while True:
            user_choice = input(f"Would you like to talk to {character['name']}? (y/n): ").strip().lower()
            if user_choice == 'n':
                self.obs_websockets_manager.smoothly_reduce_and_move_back('Characters', character['obs'], move_step=9, step_delay=.1)   
                break
            elif user_choice == 'y':
                print(f"Listening... please speak your message to {character['name']}.")
                user_message = self.whisper.speechtotext_from_mic_continuous()
                print(f"You said: {user_message}")

                self.send_message_to_character(character, user_message)
                response = self.get_response_from_character(character)
                print(f"{character['name']} says: {response}")
                self.speak_response(character, response)
            else:
                print("Invalid choice. Please enter 'y' or 'n'.")

    def send_message_to_character(self, character, message):
        # Send a message to the selected character
        self.client.beta.threads.messages.create(
            thread_id=character['thread_id'],
            role='user',
            content=f'[Detective]{message}'
        )

    def get_response_from_character(self, character):
        # Get response from the selected character
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=character['thread_id'],
            assistant_id=character['assistant_id'],
            response_format='auto'
        )

        response = None
        if run.status == 'completed':
            thread_messages = self.client.beta.threads.messages.list(
                thread_id=character['thread_id'],
                order='desc',
                limit=1
            )
            for message in thread_messages.data:
                if message.role == 'assistant' and message.content[0].type == 'text':
                    response = message.content[0].text.value
        return response

    def speak_response(self, character, message):
        self.elevenlabs_manager.speech_with_subtitles(character['voice'], message)
        self.obs_websockets_manager.set_source_visibility('Main', 'TheSubs', source_visible=False)
        self.obs_websockets_manager.set_source_visibility('Main', 'TheLogs', source_visible=False)
        self.obs_websockets_manager.set_source_visibility('Main', 'TheSubs', source_visible=True)
        
    def main_speaker(self, character, message):
        # Use ElevenLabs for TTS
        self.elevenlabs_manager.speech_with_subtitles(character['voice'], message)
        self.obs_websockets_manager.pull_to_front_and_smoothly_enlarge('Characters', character['obs'], move_step=8, step_delay=.1)
        input("Press '=' to continue: ")
        self.obs_websockets_manager.smoothly_reduce_and_move_back('Characters', character['obs'], move_step=9, step_delay=.1)

    def accuse(self):
        while True:
            self.list_characters()
            char_index = input("Enter the number of the character you want to accuse (or type '=' to end accusation): ").strip()
            if char_index.lower() == '=':
                self.list_characters()
                return False  # Accusation process ends, return to interview

            try:
                char_index = int(char_index)
                character = self.select_character(char_index)
                if character:
                    if character['killer']:
                        self.obs_websockets_manager.set_source_visibility('Main', 'Win', True)
                        time.sleep(.1)
                        self.obs_websockets_manager.pull_to_front_and_smoothly_enlarge('Characters', character['obs'], move_step=8, step_delay=.1)
                        prompt = f"Our great detective has solved the case and discovered that {character['name']} was the Killer. Now wrap this story up with a final fairwell"
                        print(f"You have accused {character['name']}, and you are correct! The game is over.")
                        message = self.narator.greeting(prompt)
                        self.narator.send_message_to_user(message)
                        return True  # Accusation correct, game over
                    else:
                        self.obs_websockets_manager.set_source_visibility('Main', 'Wrong', True)
                        time.sleep(.1)
                        self.obs_websockets_manager.pull_to_front_and_smoothly_enlarge('Characters', character['obs'], move_step=8, step_delay=.1)
                        prompt = f"Our great detective has wrongly accused {character['name']} of being the killer. Make them feel a little bad about it before sending them off to try again."
                        print(f"You have accused {character['name']}, and you are Wrong!")
                        message = self.narator.greeting(prompt)
                        self.obs_websockets_manager.set_source_visibility('Main', 'Wrong', False)
                        self.narator.send_message_to_user(message)
                        self.obs_websockets_manager.smoothly_reduce_and_move_back('Characters', character['obs'], move_step=6, step_delay=.1)
                        print(f"You have accused {character['name']}, but they are not the killer. Try again.")
                        return False  # Accusation incorrect, continue interviews
                else:
                    print("Character not found. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
    def main(self):
        while True:
            self.list_characters()
                       
            char_index = input("Enter the number of the character you want to interview (or type '=' to end, '-' to accuse): ").strip()
            if char_index.lower() == '=':
                break

            if char_index == '-':
                if self.accuse():
                    break
                else:
                    continue

            try:
                char_index = int(char_index)
                character = self.select_character(char_index)
                if character:
                    self.obs_websockets_manager.pull_to_front_and_smoothly_enlarge('Characters', character['obs'], move_step=8, step_delay=.1)
                    self.interview_character(character)
                else:
                    print("Character not found. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
               
class Game:
    def __init__(self, client, designer_thread, Designer):
        self.client = client
        self.create_characters = CharacterCreator()
        self.whisper = GPTWhisperManager()
        self.elevenlabs_manager = GenerateAudioManager()
        self.audio_manager = AudioManager()
        self.obs_websockets_manager = OBSWebsocketsManager()
        self.fill_the_room = FillTheRoom(self.create_characters)
        self.set_the_stage = SetTheStage(client, designer_thread, Designer, self.obs_websockets_manager)
        self.conversation_manager = None

    def load_game(self):
        save_dir = "saved_games"
        save_files = [f for f in os.listdir(save_dir) if f.endswith('.json')]
        
        if not save_files:
            print("No saved games found.")
            return None, None
        
        print("Saved games:")
        for idx, file in enumerate(save_files):
            print(f"{idx + 1}: {file}")
        
        choice = int(input("Enter the number of the save file you want to load: ")) - 1
        file_path = os.path.join(save_dir, save_files[choice])
        
        with open(os.path.join(save_dir, save_files[choice]), 'r') as file:
            save_data = json.load(file)
        
        characters = save_data["characters"]
        background = save_data["background"]
        narator_thread = save_data["narator_thread"]
        
        return characters, background, narator_thread, file_path
    
    def update_all_thread_ids(self, filename):
        with open(filename, 'r') as file:
            save_data = json.load(file)
            
        nthread = self.client.beta.threads.create()
        n_id = nthread.id
        save_data["narator_thread"] = n_id

        for character in save_data["characters"]:
            thread = self.client.beta.threads.create()  # Create a new thread
            new_thread_id = thread.id
            character["thread_id"] = new_thread_id

        with open(filename, 'w') as file:
            json.dump(save_data, file, indent=4)
        print(f"Thread IDs updated for all characters in {filename}") 
    
    def set_character_visibility(self, characters):
        for character in characters:
            source_name = character['obs']
            self.obs_websockets_manager.set_source_visibility('Characters',source_name, source_visible=True)

    def update_character_images(self, characters):
        for character in characters:
            source_name = character['obs']
            file_path = character['picture']
            self.obs_websockets_manager.set_image_file_path(source_name, file_path)

    def main(self):
        self.obs_websockets_manager.set_all_characters_visibility(False)
        self.obs_websockets_manager.set_filter_visibility('GameScreen', 'PostDeath', filter_enabled=True)
        self.obs_websockets_manager.set_initial_positions('Characters', num_groups=6, num_characters_per_group=6)
        load_choice = input("Do you want to load a saved game? (y/n): ").strip().lower()
        if load_choice == 'y':
            characters, background, narator_thread, file_path = self.load_game()
            self.set_the_stage.set_the_background(background)
            self.update_character_images(characters)
            self.set_character_visibility(characters)
            self.obs_websockets_manager.move_around(file_path,'Characters', 2, .1)
            new_choice = input("Do you want to start from the beginning (y/n)?").strip().lower()
            if new_choice == 'y':
                self.update_all_thread_ids(file_path)
                input('Check if broken')
            else:
                pass
            self.obs_websockets_manager.set_filter_visibility('GameScreen', 'PostDeath', filter_enabled=False)
            self.narator = Narator(self.client, self.elevenlabs_manager, self.audio_manager, self.obs_websockets_manager, narator_thread)
            message = self.narator.greeting(initial_prompt='Welcome Back! give a very short 1 sentence welcome to the group.')
            self.narator.send_message_to_all(message,characters)
            initial_message = "welcome back to the party! remember to stay true to your character at all times. Be as kind, ruthless, gentle, or devious as they would."
            self.narator.send_user_message_to_all(initial_message, characters)
            
        else:
            scene_prompt, background = self.set_the_stage.main()
            characters = self.fill_the_room.main(scene_prompt)
            narator_thread, file_path = self.fill_the_room.save_game(background)
            self.obs_websockets_manager.move_around(file_path,'Characters', 2, .1)
            self.narator = Narator(self.client, self.elevenlabs_manager, self.audio_manager, self.obs_websockets_manager, narator_thread)
            initial_prompt = f"Here is the scene{scene_prompt}, Now produce a fitting greeting for our guests."
            greeting = self.narator.greeting(initial_prompt)
            self.narator.send_message_to_all(greeting,characters)
            initial_message = f'Welcome to the party, here is the theme {scene_prompt} \n\n Now you have a reason you are here, throughout all interactions work towards this. Remain in character at all times. This means that there are times you will be warm and charming, but there will also be times in which you are cold, calculated, rude, and or aggressive.'    
            self.narator.send_user_message_to_all(initial_message, characters)
            self.obs_websockets_manager.set_filter_visibility('Background', 'PostDeath', filter_enabled=False)
            
        
        if not characters:
            print("No characters created or loaded. Exiting.")
            return

        #Start PreMurder

        self.conversation_manager = ConversationManager(self.client, characters, self.obs_websockets_manager, self.narator, self.audio_manager, self.elevenlabs_manager)
        
        print("\nAll created characters:")
        # for character in characters:
        #     print(f"Character Name: {character['name']}, Assistant ID: {character['assistant_id']}, Thread ID: {character['thread_id']}, Killer: {'Yes' if character['killer'] else 'No'}, Victim: {'Yes' if character['victim'] else 'No'}, Relationship Group: {character['relationship_group']}, Picture File Path: {character['picture']}")


        murder_happened = input("Has the murder happened yet? (y/n/t): yes goes to interviews, no restarts group conversations, t triggers death, remember you have to write in the death when this happens. ").strip().lower()
        if murder_happened == 'n':
            # Create groups and manage conversations
            groups = self.conversation_manager.create_groups()
            print("\nParallel Group Conversations:")
            victim, death = self.conversation_manager.parallel_conversations(groups)
            self.conversation_manager.post_murder_reactions(victim, death)
            input('Continue?')
        if murder_happened == 't':
            victim = None
            for character in characters:
                if character.get('victim') == True:
                    victim = character
                    break
            death = input("how did the victim die?")
            self.obs_websockets_manager.set_source_visibility('Main', 'Crowd', False)
            self.obs_websockets_manager.set_source_visibility('Main', 'TheLogs', source_visible=False)
            self.obs_websockets_manager.lightning()
            self.audio_manager.play_audio('Sounds\Lightning.mp3', sleep_during_playback=False, delete_file=False, play_using_music=False)
            initial_prompt = f'{victim["name"]} was murdered! They were {death}\n\n Now set the stage for our protagonist to come in and try to solve the crime.'
            message = self.narator.greeting(initial_prompt)
            self.obs_websockets_manager.set_source_visibility('Main', 'GameScreen', source_visible=False)
            self.obs_websockets_manager.stop_background_movement()
            self.obs_websockets_manager.arrange_characters_in_crescent('Characters', num_groups=6, num_characters_per_group=6, center_x=850, center_y=600, ellipse_width=1300, ellipse_height=550, screen_width=1920, screen_height=1080)
            self.obs_websockets_manager.death_position('Characters', victim['obs'])
            self.narator.send_message_to_all(message, self.characters)
            self.obs_websockets_manager.set_source_visibility('Main', 'GameScreen', source_visible=True)
            self.obs_websockets_manager.lightning()
            self.audio_manager.play_audio('Sounds\Lightning.mp3', sleep_during_playback=False, delete_file=False, play_using_music=False)
            self.obs_websockets_manager.set_source_visibility('Main', 'DeathZoom', source_visible=True)
            print(f"{victim['name']} has been murdered. Begin Investigations.")
            self.conversation_manager.post_murder_reactions(victim,death)
            input('continue?')
        self.interview_manager = InterviewManager(self.client, characters, self.elevenlabs_manager, self.whisper, self.obs_websockets_manager, self.narator)
        self.interview_manager.main()
                
if __name__ == "__main__":
    client = OpenAI()
    designer_thread = client.beta.threads.create()
    Designer = client.beta.assistants.retrieve("asst_thL9KhFcTjZxLqhIlZGnWJZQ")
    game = Game(client, designer_thread, Designer)
    game.main()
