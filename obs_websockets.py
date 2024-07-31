import time
import random
import sys
import threading
import math
from obswebsocket import obsws, requests  # noqa: E402
from websockets_auth import WEBSOCKET_HOST, WEBSOCKET_PORT, WEBSOCKET_PASSWORD
import json

##########################################################
##########################################################

class OBSWebsocketsManager:
    ws = None
    stop_event = None
    
    def __init__(self):
        # Connect to websockets
        self.ws = obsws(WEBSOCKET_HOST, WEBSOCKET_PORT, WEBSOCKET_PASSWORD)
        try:
            self.ws.connect()
        except:
            print("\nPANIC!!\nCOULD NOT CONNECT TO OBS!\nDouble check that you have OBS open and that your websockets server is enabled in OBS.")
            time.sleep(10)
            sys.exit()
        print("Connected to OBS Websockets!\n")
        
        self.stop_event = threading.Event()

    def refresh_browser_source(self, source_name):
        # Get the current settings of the browser source
        response = self.ws.call(requests.GetInputSettings(inputName=source_name))
        current_settings = response.datain["inputSettings"]
        
        # Update the URL to refresh the browser source
        # This can be done by appending a timestamp to the URL to ensure it reloads
        url = current_settings["url"]
        refreshed_url = url.split('?')[0] + f'?_={int(time.time())}'
        
        # Set the new settings with the refreshed URL
        current_settings["url"] = refreshed_url
        self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings=current_settings))

        # Optionally, reset the URL back to the original to allow further refreshes
        time.sleep(1)  # Delay to ensure the browser source refreshes
        current_settings["url"] = url
        self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings=current_settings))

    def disconnect(self):
        self.ws.disconnect()

    # Set the current scene
    def set_scene(self, new_scene):
        self.ws.call(requests.SetCurrentProgramScene(sceneName=new_scene))

    # Set the visibility of any source's filters
    def set_filter_visibility(self, source_name, filter_name, filter_enabled=True):
        self.ws.call(requests.SetSourceFilterEnabled(sourceName=source_name, filterName=filter_name, filterEnabled=filter_enabled))

    # Set the visibility of any source
    def set_source_visibility(self, scene_name, source_name, source_visible=True):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        myItemID = response.datain['sceneItemId']
        self.ws.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=myItemID, sceneItemEnabled=source_visible))

    # Returns the current text of a text source
    def get_text(self, source_name):
        response = self.ws.call(requests.GetInputSettings(inputName=source_name))
        return response.datain["inputSettings"]["text"]

    # Returns the text of a text source
    def set_text(self, source_name, new_text):
        self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings = {'text': new_text}))

    def get_source_transform(self, scene_name, source_name):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        myItemID = response.datain['sceneItemId']
        response = self.ws.call(requests.GetSceneItemTransform(sceneName=scene_name, sceneItemId=myItemID))
        transform = {}
        transform["positionX"] = response.datain["sceneItemTransform"]["positionX"]
        transform["positionY"] = response.datain["sceneItemTransform"]["positionY"]
        transform["scaleX"] = response.datain["sceneItemTransform"]["scaleX"]
        transform["scaleY"] = response.datain["sceneItemTransform"]["scaleY"]
        transform["rotation"] = response.datain["sceneItemTransform"]["rotation"]
        transform["sourceWidth"] = response.datain["sceneItemTransform"]["sourceWidth"] # original width of the source
        transform["sourceHeight"] = response.datain["sceneItemTransform"]["sourceHeight"] # original width of the source
        transform["width"] = response.datain["sceneItemTransform"]["width"] # current width of the source after scaling, not including cropping. If the source has been flipped horizontally, this number will be negative.
        transform["height"] = response.datain["sceneItemTransform"]["height"] # current height of the source after scaling, not including cropping. If the source has been flipped vertically, this number will be negative.
        transform["cropLeft"] = response.datain["sceneItemTransform"]["cropLeft"] # the amount cropped off the *original source width*. This is NOT scaled, must multiply by scaleX to get current # of cropped pixels
        transform["cropRight"] = response.datain["sceneItemTransform"]["cropRight"] # the amount cropped off the *original source width*. This is NOT scaled, must multiply by scaleX to get current # of cropped pixels
        transform["cropTop"] = response.datain["sceneItemTransform"]["cropTop"] # the amount cropped off the *original source height*. This is NOT scaled, must multiply by scaleY to get current # of cropped pixels
        transform["cropBottom"] = response.datain["sceneItemTransform"]["cropBottom"] # the amount cropped off the *original source height*. This is NOT scaled, must multiply by scaleY to get current # of cropped pixels
        return transform

    # The transform should be a dictionary containing any of the following keys with corresponding values
    # positionX, positionY, scaleX, scaleY, rotation, width, height, sourceWidth, sourceHeight, cropTop, cropBottom, cropLeft, cropRight
    # e.g. {"scaleX": 2, "scaleY": 2.5}
    # Note: there are other transform settings, like alignment, etc, but these feel like the main useful ones.
    # Use get_source_transform to see the full list
    def set_source_transform(self, scene_name, source_name, new_transform):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        myItemID = response.datain['sceneItemId']
        self.ws.call(requests.SetSceneItemTransform(sceneName=scene_name, sceneItemId=myItemID, sceneItemTransform=new_transform))

    def move_images_randomly(self, scene_name, groups, move_step, delay, direction_change_prob=0.1):
        try:
            # Flatten the list of groups to get all characters
            all_characters = [character for group in groups for character in group]

            # Initialize the positions for all images
            current_transforms = {character['obs']: self.get_source_transform(scene_name, character['obs']) for character in all_characters}

            # Initialize direction and step counters for each image
            directions = {character['obs']: (random.uniform(-move_step, move_step), random.uniform(-move_step, move_step)) for character in all_characters}
            steps_remaining = {character['obs']: random.randint(20, 50) for character in all_characters}

            screen_width = 1920
            screen_height = 1080

            while not self.stop_event.is_set():  # Run until stop event is set
                for character in all_characters:
                    try:
                        source_name = character['obs']
                        current_transform = current_transforms[source_name]

                        # Update position based on current direction and steps remaining
                        direction = directions[source_name]
                        new_position_x = current_transform['positionX'] + direction[0]
                        new_position_y = current_transform['positionY'] + direction[1]

                        # Ensure positions stay within screen boundaries
                        new_position_x = max(0, min(new_position_x, screen_width))
                        new_position_y = max(0, min(new_position_y, screen_height))

                        current_transform['positionX'] = new_position_x
                        current_transform['positionY'] = new_position_y

                        # Calculate scale based on Y value
                        normalized_y = new_position_y / screen_height  # Normalize Y to be between 0 and 1
                        scale_factor = 1/3 - (1/3 - 0.25) * normalized_y  # Subtle inverse proportional scale between 0.25 and 1/3
                        current_transform['scaleX'] = scale_factor
                        current_transform['scaleY'] = scale_factor

                        self.set_source_transform(scene_name, source_name, current_transform)

                        # Decrease steps remaining or change direction based on probability
                        steps_remaining[source_name] -= 1
                        if steps_remaining[source_name] <= 0 or random.random() < direction_change_prob:
                            directions[source_name] = (random.uniform(-move_step, move_step), random.uniform(-move_step, move_step))
                            steps_remaining[source_name] = random.randint(20, 50)

                    except Exception as e:
                        print(f"Error processing character {character['obs']}: {e}")

                try:
                    self.update_z_order_and_scale(scene_name, [character['obs'] for character in all_characters])
                except Exception as e:
                    print(f"Error updating z-order and scale: {e}")

                time.sleep(delay)

        except Exception as e:
            print(f"Error in move_images_randomly: {e}")
        
    def start_background_movement(self, scene_name, groups, move_step, delay):
        self.stop_event.clear()  # Reset the stop event before starting new threads
        
        movement_thread = threading.Thread(
            target=self.move_images_randomly,
            args=(scene_name, groups, move_step, delay),
            daemon=True  # This ensures that the thread will exit when the main program exits
        )
        movement_thread.start()
        
    def stop_background_movement(self):
        self.stop_event.set()  # Signal the stop event to stop movement threads

    def get_input_settings(self, input_name):
        return self.ws.call(requests.GetInputSettings(inputName=input_name))

    def get_input_kind_list(self):
        return self.ws.call(requests.GetInputKindList())

    def get_scene_items(self, scene_name):
        return self.ws.call(requests.GetSceneItemList(sceneName=scene_name))

    def set_image_file_path(self, source_name, file_path):
        input_settings = self.ws.call(requests.GetInputSettings(inputName=source_name)).datain["inputSettings"]
        input_settings["file"] = file_path
        self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings=input_settings))

    def set_all_characters_visibility(self, visibility=True):
        for group_num in range(1, 7):
            for character_num in range(1, 7):
                source_name = f'G{group_num}C{character_num}'
                self.set_source_visibility('Characters', source_name, visibility)

    def set_source_order(self, scene_name, source_name, new_index):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        myItemID = response.datain['sceneItemId']
        self.ws.call(requests.SetSceneItemIndex(
            sceneName=scene_name, 
            sceneItemId=myItemID, 
            sceneItemIndex=new_index
        ))

    def pull_to_front_and_smoothly_enlarge(self, scene_name, source_name, move_step, step_delay):
        def task():
            current_transform = self.get_source_transform(scene_name, source_name)
            scale_factor = 2

            # Set target scaling
            target_scaleX = scale_factor
            target_scaleY = scale_factor

            # Calculate target position
            target_x = 200
            target_y = -440

            # Bring the source to the front
            self.set_source_order(scene_name, source_name, new_index=36)

            # Calculate deltas
            delta_scaleX = target_scaleX - current_transform['scaleX']
            delta_scaleY = target_scaleY - current_transform['scaleY']
            delta_x = target_x - current_transform['positionX']
            delta_y = target_y - current_transform['positionY']

            # Calculate number of steps needed based on move_step
            steps = max(
                int(abs(delta_scaleX) / move_step),
                int(abs(delta_scaleY) / move_step),
                int(abs(delta_x) / move_step),
                int(abs(delta_y) / move_step)
            )

            delta_scaleX /= steps
            delta_scaleY /= steps
            delta_x /= steps
            delta_y /= steps

            for _ in range(steps):
                current_transform['scaleX'] += delta_scaleX
                current_transform['scaleY'] += delta_scaleY
                current_transform['positionX'] += delta_x
                current_transform['positionY'] += delta_y

                self.set_source_transform(scene_name, source_name, current_transform)
                self.set_source_order(scene_name, source_name, new_index=36)
                time.sleep(step_delay)
            
        threading.Thread(target=task).start()

    def smoothly_reduce_and_move_back(self, scene_name, source_name, move_step, step_delay, center_offset_range=800, screen_width=1920, screen_height=1080, vertical_offset=800):
        def task():
            # Get the current transform
            current_transform = self.get_source_transform(scene_name, source_name)

            # Calculate random start position and scale
            center_x = screen_width / 2.3
            center_y = screen_height / 1.5
            random_x = center_x + random.uniform(-center_offset_range, center_offset_range)
            random_y = center_y + random.uniform(-vertical_offset, vertical_offset)
            lower_y_bound = screen_height / 2
            upper_y_bound = screen_height - vertical_offset
            random_y = max(lower_y_bound, min(random_y, upper_y_bound))
            normalized_y = random_y / screen_height
            scale_factor = 1/3 - (1/3 - 0.25) * normalized_y

            # Calculate target positions and scales
            target_scaleX = scale_factor
            target_scaleY = scale_factor
            target_x = random_x
            target_y = random_y

            # Calculate deltas
            delta_scaleX = target_scaleX - current_transform['scaleX']
            delta_scaleY = target_scaleY - current_transform['scaleY']
            delta_x = target_x - current_transform['positionX']
            delta_y = target_y - current_transform['positionY']

            # Calculate number of steps needed based on move_step
            steps = max(
                int(abs(delta_scaleX) / move_step),
                int(abs(delta_scaleY) / move_step),
                int(abs(delta_x) / move_step),
                int(abs(delta_y) / move_step)
            )

            delta_scaleX /= steps
            delta_scaleY /= steps
            delta_x /= steps
            delta_y /= steps

            for _ in range(steps):
                current_transform['scaleX'] += delta_scaleX
                current_transform['scaleY'] += delta_scaleY
                current_transform['positionX'] += delta_x
                current_transform['positionY'] += delta_y

                self.set_source_transform(scene_name, source_name, current_transform)
                self.set_source_order(scene_name, source_name, new_index=12)
                time.sleep(step_delay)
                
        threading.Thread(target=task).start()

    def death_position(self, scene_name, source_name, scale_factor=0.41, duration=2, step_delay=0.05, screen_width=1500, screen_height=1080):
        current_transform = self.get_source_transform(scene_name, source_name)

        # Set target scaling
        target_scaleX = scale_factor
        target_scaleY = scale_factor

        # Calculate target position
        target_x = 1432 
        target_y = 747 

        # Set the target rotation to 90 degrees
        target_rotation = current_transform['rotation'] + 90

        # Update the transform directly
        current_transform['scaleX'] = target_scaleX
        current_transform['scaleY'] = target_scaleY
        current_transform['positionX'] = target_x
        current_transform['positionY'] = target_y
        current_transform['rotation'] = target_rotation

        self.set_source_transform(scene_name, source_name, current_transform)
        self.set_source_order(scene_name, source_name, new_index=36)

    def set_random_start_position(self, scene_name, source_name, center_offset_range=800, screen_width=1920, screen_height=1080, vertical_offset=800):
        current_transform = self.get_source_transform(scene_name, source_name)

        # Calculate random position around the center in the bottom half of the screen
        center_x = screen_width / 2.3
        center_y = screen_height / 1.5  # Adjusted to raise characters up on the y-axis

        # Adding random offset within the specified range
        random_x = center_x + random.uniform(-center_offset_range, center_offset_range)
        random_y = center_y + random.uniform(-vertical_offset, vertical_offset)

        # Ensure the random_y doesn't go too low
        lower_y_bound = screen_height / 2
        upper_y_bound = screen_height - vertical_offset
        random_y = max(lower_y_bound, min(random_y, upper_y_bound))

        # Set position
        current_transform['positionX'] = random_x
        current_transform['positionY'] = random_y

        # Calculate scale based on Y value consistent with other functions
        normalized_y = random_y / screen_height  # Normalize Y to be between 0 and 1
        scale_factor = 1/3 - (1/3 - 0.25) * normalized_y  # Consistent scale factor range as in other methods
        current_transform['scaleX'] = scale_factor
        current_transform['scaleY'] = scale_factor

        # Apply the new transform and set z-order
        self.set_source_transform(scene_name, source_name, current_transform)
        self.update_z_order_and_scale(scene_name, [source_name])

    def arrange_characters_in_crescent(self, scene_name, num_groups=6, num_characters_per_group=6, center_x=850, center_y=600, ellipse_width=1300, ellipse_height=550, screen_width=1920, screen_height=1080):
        total_characters = num_groups * num_characters_per_group
        angle_step = math.pi / total_characters  # Use half-circle (π radians)

        for group_index in range(1, num_groups + 1):
            for character_index in range(1, num_characters_per_group + 1):
                source_name = f"G{group_index}C{character_index}"
                character_index_in_total = (group_index - 1) * num_characters_per_group + (character_index - 1)
                angle = angle_step * character_index_in_total

                # Ellipse equation parameters
                x = center_x + (ellipse_width / 2) * math.cos(angle)
                y = center_y - (ellipse_height / 2) * math.sin(angle)  # Flip by subtracting instead of adding

                # Fetch current transform and modify accordingly
                current_transform = self.get_source_transform(scene_name, source_name)
                current_transform['positionX'] = x
                current_transform['positionY'] = y

                # Calculate scale based on Y value
                normalized_y = y / screen_height  # Normalize Y to be between 0 and 1
                scale_factor = 1/3 - (1/3 - 0.25) * normalized_y  # Subtle inverse proportional scale between 0.25 and 1/3
                current_transform['scaleX'] = scale_factor
                current_transform['scaleY'] = scale_factor

                # Apply the new transform
                self.set_source_transform(scene_name, source_name, current_transform)

        self.update_z_order_and_scale(scene_name, [f"G{group_index}C{character_index}" for group_index in range(1, num_groups + 1) for character_index in range(1, num_characters_per_group + 1)])

    def read_and_group_characters(self, json_file_path, num_groups=6):
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        characters = data.get("characters", [])
        
        # Sort characters by relationship group or any other relevant criteria
        characters.sort(key=lambda x: x["relationship_group"])
        
        # Group the characters evenly into the specified number of groups
        groups = [[] for _ in range(num_groups)]
        
        for i, character in enumerate(characters):
            groups[i % num_groups].append(character)
            
        return groups

    def get_bottom_group_centers(self, screen_width, screen_height, num_groups):
        group_centers = []
        y_position = screen_height * 0.5  # 90% down the screen, near the bottom
        horizontal_spacing = screen_width / (num_groups + 1)

        for i in range(num_groups):
            x_position = horizontal_spacing * (i + 1)
            group_centers.append((x_position, y_position))
        
        return group_centers

    def congregate_characters(self, scene_name, groups, move_step, delay):
        # Initialize positions for all characters
        current_transforms = {
            str(character['obs']): self.get_source_transform(scene_name, str(character['obs']))
            for group in groups for character in group
        }

        screen_width = 1700
        screen_height = 1080
        num_groups = len(groups)

        # Calculate the bottom group centers using the custom function
        group_centers = self.get_bottom_group_centers(screen_width, screen_height, num_groups)

        # Generate random offsets for characters within each group
        group_offsets = [
            (random.randint(-30, 30), random.randint(-30, 30)) for _ in range(num_groups) for _ in range(6)
        ]

        all_characters_reached = False

        while not all_characters_reached:
            all_characters_reached = True  # Assume all characters have reached their target

            for group_index, group in enumerate(groups):
                group_center = group_centers[group_index]
                for character_index, character in enumerate(group):
                    source_name = str(character['obs'])

                    if source_name not in current_transforms:
                        print(f"Error: {source_name} not found in current_transforms")
                        continue

                    current_transform = current_transforms[source_name]

                    target_x = group_center[0] + 5 * group_offsets[group_index * 6 + character_index][0]
                    target_y = group_center[1] + 2 * group_offsets[group_index * 6 + character_index][1]

                    direction_x = target_x - current_transform['positionX']
                    direction_y = target_y - current_transform['positionY']

                    distance = (direction_x ** 2 + direction_y ** 2) ** 0.5
                    move_amount = min(move_step, distance)

                    if distance > 0:
                        dir_x = move_amount * direction_x / distance
                        dir_y = move_amount * direction_y / distance

                        current_transform['positionX'] += dir_x
                        current_transform['positionY'] += dir_y

                        all_characters_reached = False  # If any character is still moving, not all have reached their target

                    normalized_y = current_transform['positionY'] / screen_height
                    scale_factor = 1/3 - (1/3 - 0.25) * normalized_y
                    current_transform['scaleX'] = scale_factor
                    current_transform['scaleY'] = scale_factor

                    self.set_source_transform(scene_name, source_name, current_transform)

            self.update_z_order_and_scale(scene_name, current_transforms.keys())
            time.sleep(delay)

    def update_z_order_and_scale(self, scene_name, source_names):
        current_transforms = {source_name: self.get_source_transform(scene_name, source_name) for source_name in source_names}
        screen_height = 1080  # Assuming screen height is 1080, adjust if different

        # Sort by Y-coordinate (ascending order, lower Y-values at the top, higher Y-values at the bottom)
        sorted_sources = sorted(source_names, key=lambda name: current_transforms[name]['positionY'])

        # Assign z-order and update scale based on Y-coordinate
        for index, source_name in enumerate(sorted_sources):
            self.set_source_order(scene_name, source_name, index)

            # Calculate scale based on Y value
            y_position = current_transforms[source_name]['positionY']
            normalized_y = y_position / screen_height  # Normalize Y to be between 0 and 1
            scale_factor = 1/3 - (1/3 - 0.25) * normalized_y  # Subtle inverse proportional scale between 0.25 and 1/3

            current_transforms[source_name]['scaleX'] = scale_factor
            current_transforms[source_name]['scaleY'] = scale_factor

            self.set_source_transform(scene_name, source_name, current_transforms[source_name])

    def set_initial_positions(self, scene_name, num_groups=6, num_characters_per_group=6):
        for group_index in range(1, num_groups + 1):  # Groups G1 to G6
            for character_index in range(1, num_characters_per_group + 1):  # Characters C1 to C6 within each group
                source_name = f"G{group_index}C{character_index}"
                self.set_random_start_position(
                    scene_name, 
                    source_name,
                )

    def lightning(self):
        def task():
            self.set_filter_visibility('GameScreen', 'Night', filter_enabled=True)
            self.set_filter_visibility('GameScreen', 'PostDeath', filter_enabled=False)
            self.set_filter_visibility('GameScreen', 'Lightning', filter_enabled=True)
            time.sleep(.3)
            self.set_filter_visibility('GameScreen', 'Lightning2', filter_enabled=True)
            time.sleep(.3)
            self.set_filter_visibility('GameScreen', 'Night', filter_enabled=False)
            self.set_filter_visibility('GameScreen', 'PostDeath', filter_enabled=True)
            self.set_filter_visibility('GameScreen', 'Lightning', filter_enabled=False)
            time.sleep(.3)
            self.set_filter_visibility('GameScreen', 'Lightning2', filter_enabled=False)
            time.sleep(3)
            self.set_filter_visibility('GameScreen', 'Night', filter_enabled=True)
            self.set_filter_visibility('GameScreen', 'PostDeath', filter_enabled=False)
            self.set_filter_visibility('GameScreen', 'Lightning', filter_enabled=True)
            time.sleep(.1)
            self.set_filter_visibility('GameScreen', 'Lightning2', filter_enabled=True)
            time.sleep(.3)
            self.set_filter_visibility('GameScreen', 'Night', filter_enabled=False)
            self.set_filter_visibility('GameScreen', 'PostDeath', filter_enabled=True)
            self.set_filter_visibility('GameScreen', 'Lightning', filter_enabled=False)
            time.sleep(.3)
            self.set_filter_visibility('GameScreen', 'Lightning2', filter_enabled=False)
            self.set_filter_visibility('GameScreen', 'PostDeath', filter_enabled=False)
            
        threading.Thread(target=task).start()

        
if __name__ == '__main__':
    obswebsockets_manager = OBSWebsocketsManager()
    source_name = 'G1C1'
    scale_factor = .41
    scene_name = 'Characters'
    obswebsockets_manager.set_image_file_path("G1C1", r'C:\Users\Jesse\Pictures\StreamAssets\Characters\ Madison _Maddie_ Caldwell_mask.png')
    json_file_path = r'C:\Users\Jesse\JessesPrograms\MurderMystery\saved_games\savegame_20240717_163238.json'
    move_duration = 25 # Duration in seconds for characters to move to their groups
    move_step = 8 # Pixels to move per step
    delay = 0.1  # Delay in seconds between each movement step
    groups = obswebsockets_manager.read_and_group_characters(json_file_path)
    #obswebsockets_manager.set_initial_positions('Characters')
    #obswebsockets_manager.congregate_characters('Characters', groups, move_step, delay)
    # obswebsockets_manager.start_background_movement('Characters', groups, move_step, delay)
    # time.sleep(100)
    # obswebsockets_manager.stop_background_movement()
    
    # # # print("Connecting to OBS Websockets")
    # # # obswebsockets_manager.set_all_characters_visibility(True)
    # obswebsockets_manager.set_initial_positions("Characters",)
    #obswebsockets_manager.arrange_characters_in_crescent('Characters')
    # time.sleep(3)
    #obswebsockets_manager.death_position(scene_name, source_name)
    
    # time.sleep(2)
    
    
    # time.sleep(3)
    # #     # Example usage:
    # # # move image "test_source" in the scene "test_scene" for 60 seconds
    # # # with step movement of 5 pixels and delay of 0.1 seconds
    # obswebsockets_manager.start_background_movement("Characters", groups, move_step=1, delay=0.1)
    # time.sleep(10)
    # obswebsockets_manager.lightning()
    # time.sleep(10)
    
    # for i in range(5):
    #     print("Foreground task running ...", i)
    #     time.sleep(3.1)

    # print("Foreground task completed.")
    # print("grouping characters")
    
    # obswebsockets_manager.congregate_characters('Characters', move_step, delay)
    #obswebsockets_manager.pull_to_front_and_smoothly_enlarge(scene_name, source_name, move_step, delay)
    #obswebsockets_manager.smoothly_reduce_and_move_back(scene_name, source_name, move_step, delay)
    
    # # print("Setting the file path for an image source")
    # # obswebsockets_manager.set_image_file_path('G1C1', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G1C2', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G1C3', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G1C4', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G1C5', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G1C6', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')

    # # obswebsockets_manager.set_image_file_path('G2C1', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G2C2', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G2C3', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G2C4', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G2C5', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G2C6', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')

    # # obswebsockets_manager.set_image_file_path('G3C1', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G3C2', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G3C3', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G3C4', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G3C5', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G3C6', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')

    # # obswebsockets_manager.set_image_file_path('G4C1', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G4C2', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G4C3', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G4C4', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G4C5', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G4C6', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')

    # # obswebsockets_manager.set_image_file_path('G5C1', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G5C2', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G5C3', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G5C4', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G5C5', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G5C6', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')

    # # obswebsockets_manager.set_image_file_path('G6C1', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G6C2', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G6C3', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G6C4', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G6C5', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    # # obswebsockets_manager.set_image_file_path('G6C6', r'C:\Users\Jesse\Pictures\StreamAssets\Characters\Un.png')
    
    
    obswebsockets_manager.set_all_characters_visibility(False)

#############################################