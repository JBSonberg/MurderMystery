import openai
import os
from openai import OpenAI
import random
import datetime
import requests
import json
import time
from CharacterCreator import main as create_characters

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
    def __init__(self, client, designer_thread, Designer):
        self.client = client
        self.designer_thread = designer_thread
        self.designer = Designer

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
                  "historical drama", "adventure", "superhero"]
        time_frames = ["medieval", "prehistoric", "future", "alternate reality", "modern day", 
                       "ancient times", "Victorian era", "Roaring Twenties", "Space Age", 
                       "Ice Age", "Bronze Age", "Stone Age", "Industrial Revolution", "Cyberpunk", 
                       "Utopian future", "Dystopian future"]

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
            prompt=f'Create our scene \n\n{scene_description} \n\n***Ideal Picture***\n\nwill have a floor\nThe image should be from ground level\nThere will be no main characters in the image\nwill be atmospheric but not be overwhelmed with details',
            n=1,
            size="1792x1024",
            response_format='url'
        )
        image_url = response.data[0].url
        generated_image = requests.get(image_url).content
        with open(file_path, "wb") as image_file:
            image_file.write(generated_image)            
        return file_path, scene_prompt

    def load_background(self):
        folder_path = "saved_games"
        save_files = os.listdir(folder_path)

        if not save_files:
            print("No saved games found.")
            return

        print("Saved games:")
        for idx, save_file in enumerate(save_files, 1):
            print(f"{idx}. {save_file}")

        choice = int(input("Enter the number of the save file you want to load: "))
        save_file = save_files[choice - 1]
        save_file_path = os.path.join(folder_path, save_file)

        with open(save_file_path, 'r') as file:
            save_data = json.load(file)
            return save_data["background"]

    def main(self, load_game=False):
        if load_game:
            return self.load_background()
        else:
            scene_prompt, scene_title = self.decide_the_theme()
            file_path, scene_prompt = self.create_background_image(scene_prompt, scene_title)
            return file_path, scene_prompt
        
class FillTheRoom:
    def __init__(self):
        self.all_characters = []
        self.save_dir = "saved_games"

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
        for group_num in range(1, num_groups + 1):
            print(f"\nCreating characters for Group {group_num}:")
            characters = create_characters(scene_prompt=scene_prompt)  # Pass the scene prompt
            if characters:  # Check if the returned value is not None
                all_characters.extend(characters)
            else:
                print(f"[Warning] Group {group_num} returned no characters.")
        return all_characters

    def create_random_characters(self, scene_prompt):
        print("\nCreating random characters:")
        characters = create_characters(scene_prompt=scene_prompt)  # Pass the scene prompt
        if characters:
            return characters
        else:
            print("[Warning] No characters created.")
            return []

    def save_game(self, background):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.save_dir, f"savegame_{timestamp}.json")
        save_data = {
            "characters": [
                {
                    "name": character[0],
                    "assistant_id": character[1],
                    "thread_id": character[2],
                    "killer": character[3],
                    "victim": character[4],
                    "relationship_group": character[5],
                    "picture": character[6]
                } for character in self.all_characters
            ],
            "background": background
        }

        os.makedirs(self.save_dir, exist_ok=True)
        with open(filename, 'w') as file:
            json.dump(save_data, file, indent=4)
        print(f"Game saved to {filename}")

    def main(self, scene_prompt, load_game=False):
        if load_game:
            self.load_game()
        else:
            choice = input("Do you want groups of people or all random characters? (g/r): ").strip().lower()
            if choice == 'g':
                num_groups = self.get_number_of_groups()
                self.all_characters = self.create_groups(num_groups, scene_prompt)
            elif choice == 'r':
                self.all_characters = self.create_random_characters(scene_prompt)
            else:
                print("Invalid choice. Please enter 'g' for groups or 'r' for random.")
                return

            print("\nAll created characters:")
            for name, assistant, thread, killer, victim, relations, picture in self.all_characters:
                print(f"Character Name: {name}\n Assistant ID: {assistant}\n Thread ID: {thread}\n Killer: {'Yes' if killer else 'No'} \nVictim: {'Yes' if victim else 'No'} \nRelationship group: {relations} \npicture file path = {picture}")

    def load_game(self):
        folder_path = "saved_games"
        save_files = os.listdir(folder_path)

        if not save_files:
            print("No saved games found.")
            return

        print("Saved games:")
        for idx, save_file in enumerate(save_files, 1):
            print(f"{idx}. {save_file}")

        choice = int(input("Enter the number of the save file you want to load: "))
        save_file = save_files[choice - 1]
        save_file_path = os.path.join(folder_path, save_file)

        with open(save_file_path, 'r') as file:
            save_data = json.load(file)
            self.all_characters = [
                (
                    character["name"],
                    character["assistant_id"],
                    character["thread_id"],
                    character["killer"],
                    character["victim"],
                    character["relationship_group"],
                    character["picture"]
                ) for character in save_data["characters"]
            ]
            print(f"Loaded game from {save_file_path}")
            
class Game:
    def __init__(self, client, designer_thread, Designer):
        self.fill_the_room = FillTheRoom()
        self.set_the_stage = SetTheStage(client, designer_thread, Designer)

    def main(self):
        load_choice = input("Do you want to load a saved game? (y/n): ").strip().lower()
        if load_choice == 'y':
            self.fill_the_room.main(load_game=True)
            self.set_the_stage.load_background()
        else:
            background, scene_prompt = self.set_the_stage.main()
            self.fill_the_room.main(scene_prompt)
            self.fill_the_room.save_game(background)

if __name__ == "__main__":
    client = OpenAI
    designer_thread = client.beta.threads.create()
    Designer = client.beta.assistants.retrieve("asst_thL9KhFcTjZxLqhIlZGnWJZQ")
    game = Game(client, designer_thread, Designer)
    game.main()