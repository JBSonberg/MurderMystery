import openai
import os
from openai import OpenAI
import random
import re
import requests
import time

# Initialize API Key
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    print("[red]API key not found. Please set the OPENAI_API_KEY environment variable or set it in the script.")
else:
    openai.api_key = api_key
    print("[green]API key found and set.")
client = OpenAI

azure_subscription_key = os.environ.get('AZURE_BG-REMOVER')
azure_endpoint = "https://bg-remover.cognitiveservices.azure.com/"

client = OpenAI()
character_counter = 0
Creator = client.beta.assistants.retrieve("asst_haRMOdji0AaUcplLpOUAU9eH")
creator_thread = client.beta.threads.create()
print(creator_thread)

Designer = client.beta.assistants.retrieve("asst_ijHrTRDzpceE05KXAblwglXp")
designer_thread = client.beta.threads.create()
print(designer_thread)

def get_user_input(prompt, randomize=True):
    user_input = input(prompt)
    if user_input.strip() == "" and randomize:
        return None  # Indicate that the value should be randomized
    return user_input

def new_character(index, killer, victim, gender=None, alignment=None, education=None, personality=None, hobby=None, skill=None, fear=None, goal=None, accent=None, relations=None, occupation=None, health_status=None, financial_status=None):
    global character_counter
    character_counter = index + 1
    
    genders = [
        "Male","Female"
    ]
    if gender is None:
        gender = random.choice(genders)
        
    alignments = [ 
        "Lawful Good", "Neutral Good", "Chaotic Good",
        "Lawful Neutral", "True Neutral", "Chaotic Neutral",
        "Lawful Evil", "Neutral Evil", "Chaotic Evil"
    ]
    if alignment is None:
        alignment = random.choice(alignments)
    
    occupations = [
        "Accountant", "Actor", "Actuary", "Adjudicator", "Administrator", "Advocate", "Agricultural Engineer", "Agricultural Scientist", "Agronomist", "Air Traffic Controller",
        "Aircraft Mechanic", "Airline Pilot", "Animator", "Anthropologist", "Appraiser", "Archaeologist", "Architect", "Archivist", "Art Conservator", "Art Director",
        "Artist", "Assessor", "Astronomer", "Athlete", "Audiologist", "Author", "Auto Mechanic", "Baker", "Banker", "Barber", "Bartender", "Biochemist", "Biologist", 
        "Biomedical Engineer", "Biotechnologist", "Blacksmith", "Blogger", "Bookkeeper", "Botanist", "Broker", "Budget Analyst", "Building Inspector", "Bus Driver", 
        "Business Consultant", "Butcher", "Cab Driver", "Cafeteria Worker", "Camera Operator", "Car Salesman", "Carpenter", "Cartographer", "Cashier", "Chef", "Chemical Engineer", 
        "Chemist", "Chiropractor", "City Planner", "Civil Engineer", "Claims Adjuster", "Clergy", "Coach", "Commercial Diver", "Commercial Pilot", "Communications Specialist", 
        "Community Worker", "Computer Engineer", "Computer Programmer", "Computer Scientist", "Concierge", "Conservationist", "Construction Manager", "Consultant", 
        "Contractor", "Copywriter", "Correctional Officer", "Cosmetologist", "Counselor", "Court Reporter", "Crane Operator", "Creative Director", "Crime Scene Investigator", 
        "Criminal Investigator", "Critic", "Curator", "Customer Service Representative", "Dancer", "Data Analyst", "Data Scientist", "Database Administrator", "Decorator", 
        "Delivery Driver", "Dentist", "Designer", "Detective", "Dietitian", "Director", "Dispatcher", "DJ", "Doctor", "Dog Trainer", "Drafter", "Economist", "Editor", 
        "Education Consultant", "Educator", "Electrician", "Engineer", "Environmental Engineer", "Environmental Scientist", "Event Planner", "Executive", "Farmer", 
        "Fashion Designer", "Film Director", "Film Editor", "Financial Advisor", "Financial Analyst", "Firefighter", "Fisherman", "Fitness Instructor", "Flight Attendant", 
        "Florist", "Food Scientist", "Forensic Scientist", "Forester", "Freight Handler", "Game Designer", "Game Developer", "Gardener", "Geographer", "Geologist", 
        "Graphic Designer", "Gunsmith", "Hair Stylist", "Health Educator", "Historian", "Home Health Aide", "Horticulturist", "Hotel Manager", "Human Resources Specialist", 
        "Illustrator", "Industrial Designer", "Industrial Engineer", "Information Scientist", "Inspector", "Insurance Agent", "Interior Designer", "Interpreter", 
        "Inventor", "Investment Banker", "IT Specialist", "Journalist", "Judge", "Laboratory Technician", "Land Surveyor", "Landscape Architect", "Law Clerk", "Lawyer", 
        "Librarian", "Linguist", "Loan Officer", "Locksmith", "Logistician", "Machine Operator", "Machinist", "Magician", "Management Consultant", "Manufacturing Engineer", 
        "Marine Biologist", "Marketing Manager", "Massage Therapist", "Mathematician", "Mechanic", "Medical Assistant", "Medical Scientist", "Meteorologist", "Microbiologist", 
        "Middle School Teacher", "Military Officer", "Miner", "Model", "Mortician", "Museum Curator", "Musician", "Network Administrator", "Neurologist", "Nuclear Engineer", 
        "Nurse", "Nutritionist", "Occupational Therapist", "Oceanographer", "Optician", "Optometrist", "Painter", "Paramedic", "Park Ranger", "Parole Officer", 
        "Pathologist", "Pediatrician", "Personal Trainer", "Pet Groomer", "Pharmacist", "Photographer", "Physical Therapist", "Physician", "Physicist", "Pilot", "Plumber", 
        "Police Officer", "Political Scientist", "Politician", "Postal Worker", "Producer", "Professor", "Project Manager", "Property Manager", "Psychiatrist", 
        "Psychologist", "Public Relations Specialist", "Publisher", "Radiologist", "Real Estate Agent", "Receptionist", "Recreation Worker", "Recruiter", "Registered Nurse", 
        "Reporter", "Research Scientist", "Restaurant Manager", "Retail Manager", "Roofer", "Sailor", "Sales Manager", "Sales Representative", "School Counselor", 
        "School Principal", "Scientist", "Scriptwriter", "Secretary", "Security Guard", "Set Designer", "Sociologist", "Software Developer", "Software Engineer", "Sound Engineer", 
        "Special Education Teacher", "Speech Pathologist", "Statistician", "Stockbroker", "Structural Engineer", "Surgeon", "Surveyor", "Systems Analyst", "Tailor", 
        "Tax Advisor", "Teacher", "Technical Writer", "Telemarketer", "Television Producer", "Theater Director", "Therapist", "Tour Guide", "Town Planner", "Train Conductor", 
        "Translator", "Travel Agent", "Truck Driver", "Tutor", "Urban Planner", "UX Designer", "Veterinarian", "Video Editor", "Videographer", "Waiter", "Web Designer", 
        "Web Developer", "Welder", "Writer", "Zoologist",
        "Iguana Tamer", "Jump Roper", "Teleport Engineer", "Dream Weaver", "Dragon Trainer", "Cloud Sculptor", "Time Traveler", "Candy Sculptor", "Unicorn Breeder", "Mystery Shopper",
        "Professional Sleeper", "Penguinologist", "Space Tour Guide", "Galactic Historian", "Virtual Reality Architect", "Alien Communicator", "Potion Brewer", "Magic Carpet Cleaner", 
        "Ghost Hunter", "Zombie Wrangler", "Robot Therapist", "Fairy Tale Writer", "Treasure Hunter", "Bubble Blower", "Toy Maker", "Rain Dancer", "Wind Chaser", "Shadow Catcher",
        "Glitter Fairy", "Star Gazer", "Wormhole Navigator", "Secret Keeper", "Wish Granter", "Time Keeper", "Portal Opener", "Spacetime Curator", "Moon Miner", "Stardust Collector",
        "Galactic Gardener", "Supernova Analyst", "Aurora Painter", "Constellation Designer", "Cosmic Chef", "Asteroid Sculptor", "Nebula Nurturer", "Starship Mechanic", "Parallel Universe Explorer"
    ]    
    if occupation is None:
        occupation = random.choice(occupations)
    
    hobbies = [
        "Reading", "Traveling", "Cooking", "Gardening", "Painting", "Fishing", "Hiking", "Photography", "Dancing", "Writing",
        "Knitting", "Scrapbooking", "Baking", "Cycling", "Running", "Swimming", "Yoga", "Bird Watching", "Astronomy", "Chess",
        "Collecting Stamps", "Collecting Coins", "Pottery", "Woodworking", "Metalworking", "Drawing", "Sculpting", "Calligraphy", "Playing Guitar", "Playing Piano",
        "Playing Violin", "Singing", "Listening to Music", "Watching Movies", "Playing Video Games", "Board Games", "Card Games", "Puzzles", "Origami", "Juggling",
        "Magic Tricks", "Quilting", "Sewing", "Embroidery", "Crocheting", "Model Building", "RC Cars", "Drones", "Archery", "Fencing",
        "Martial Arts", "Boxing", "Kickboxing", "Judo", "Karate", "Tae Kwon Do", "Jiu-Jitsu", "Mixed Martial Arts", "Weightlifting", "Bodybuilding",
        "Rock Climbing", "Mountaineering", "Surfing", "Sailing", "Kayaking", "Canoeing", "Stand-Up Paddleboarding", "Windsurfing", "Kitesurfing", "Snowboarding",
        "Skiing", "Ice Skating", "Roller Skating", "Rollerblading", "Skateboarding", "Parkour", "Freerunning", "BMX", "Mountain Biking", "Horseback Riding",
        "Camping", "Backpacking", "Survival Skills", "Foraging", "Hunting", "Trapping", "Fishing", "Spearfishing", "Snorkeling", "Scuba Diving",
        "Free Diving", "Caving", "Spelunking", "Geocaching", "Metal Detecting", "Treasure Hunting", "Birdhouse Building", "Beekeeping", "Butterfly Watching", "Herping",
        "Reptile Keeping", "Amateur Radio", "Podcasting", "Blogging", "Vlogging", "Filmmaking", "Video Editing", "Animation", "Graphic Design", "Web Design",
        "App Development", "Coding", "Robotics", "3D Printing", "Virtual Reality", "Augmented Reality", "Artificial Intelligence", "Machine Learning", "Data Science", "Astronomy",
        "Astrophotography", "Meteorology", "Volunteering", "Charity Work", "Mentoring", "Tutoring", "Teaching", "Learning Languages", "Sign Language", "Public Speaking",
        "Debating", "Politics", "History", "Philosophy", "Religion", "Spirituality", "Meditation", "Mindfulness", "Tai Chi", "Qigong",
        "Fitness Training", "Aerobics", "Pilates", "Zumba", "Dance Fitness", "Obstacle Course Racing", "Triathlon", "Duathlon", "Pentathlon", "Decathlon",
        "Dog Training", "Pet Sitting", "Dog Walking", "Cat Sitting", "Pet Grooming", "Aquascaping", "Fish Keeping", "Aquarium Design", "Bird Keeping", "Exotic Pets",
        "Terrarium Design", "Vivarium Design", "Paludarium Design", "Gardening", "Organic Farming", "Urban Farming", "Hydroponics", "Aquaponics", "Permaculture", "Sustainable Living",
        "Green Energy", "Recycling", "Upcycling", "Composting", "DIY Projects", "Home Improvement", "Interior Design", "Furniture Making", "Antiquing", "Collecting Antiques",
        "Collecting Art", "Collecting Comics", "Collecting Action Figures", "Collecting Toys", "Collecting Vinyl Records", "Collecting Dolls", "Collecting Model Trains", "Collecting Cars", "Collecting Motorcycles", "Collecting Vintage Clothing",
        "Collecting Books", "Collecting Autographs", "Collecting Sports Memorabilia", "Collecting Trading Cards", "Collecting Wine", "Collecting Beer", "Wine Tasting", "Beer Brewing", "Distilling Spirits", "Cocktail Mixing",
        "Coffee Roasting", "Tea Blending", "Bread Making", "Cheese Making", "Charcuterie", "Canning", "Pickling", "Fermenting", "Mushroom Hunting", "Foraging Wild Edibles",
        "Plant Identification", "Wildcrafting", "Herbalism", "Aromatherapy", "Essential Oils", "Perfume Making", "Soap Making", "Candle Making", "Jewelry Making", "Beadwork",
        "Time Travel", "Dragon Taming", "Unicorn Riding", "Space Tourism", "Moon Gardening", "Alien Communication", "Teleportation Experiments", "Flying Carpets", "Potion Brewing", "Fairy Tale Writing",
        "Ghost Hunting", "Zombie Chasing", "Robot Building", "Superhero Training", "Mind Reading", "Invisibility Practice", "Dragon Riding", "Monster Hunting", "Magic Shows", "Fortune Telling",
        "Stargazing", "Asteroid Mining", "Planet Hopping", "Dimension Hopping", "Space Cooking", "Alien Cooking", "Starship Piloting", "Galactic Gardening", "Black Hole Research", "Parallel Universe Exploration",
        "Cosmic Art", "Martian Rock Collecting", "Light Saber Dueling", "Space Junk Sculpting", "Time Loop Observing", "Wormhole Navigation", "Supernova Watching", "Intergalactic Fishing", "Cosmic Yoga", "Space Farming"
    ]

    if hobby is None: 
        hobby = random.choice(hobbies)
        hobby += f" and {random.choice(hobbies)}"
    
    skills = [
        "Negotiation", "Survival", "Marksmanship", "Hand-to-Hand Combat", "Stealth", "Investigation", "Medical Knowledge", "Engineering", "Piloting", "Language Skills",
        "Leadership", "Public Speaking", "Writing", "Editing", "Graphic Design", "Web Development", "Software Development", "Data Analysis", "Project Management", "Time Management",
        "Critical Thinking", "Problem Solving", "Decision Making", "Creativity", "Adaptability", "Teamwork", "Collaboration", "Conflict Resolution", "Customer Service", "Sales",
        "Marketing", "SEO", "Social Media Management", "Content Creation", "Copywriting", "Branding", "Business Strategy", "Financial Planning", "Accounting", "Budgeting",
        "Bookkeeping", "Human Resources", "Recruiting", "Training", "Coaching", "Mentoring", "Event Planning", "Fundraising", "Public Relations", "Advertising",
        "Market Research", "Customer Relationship Management", "Supply Chain Management", "Logistics", "Inventory Management", "Quality Control", "Risk Management", "Compliance", "Legal Research", "Contract Negotiation",
        "Legal Writing", "Mediation", "Arbitration", "Litigation", "Counseling", "Therapy", "Psychotherapy", "Counseling Psychology", "Clinical Psychology", "Behavioral Analysis",
        "Educational Psychology", "School Counseling", "Career Counseling", "Crisis Intervention", "Life Coaching", "Health Coaching", "Fitness Training", "Nutrition Counseling", "Diet Planning", "Exercise Physiology",
        "Sports Coaching", "Athletic Training", "Physical Therapy", "Occupational Therapy", "Speech Therapy", "Rehabilitation", "Massage Therapy", "Chiropractic Care", "Acupuncture", "Herbal Medicine",
        "Homeopathy", "Naturopathy", "Ayurveda", "Traditional Chinese Medicine", "Reflexology", "Reiki", "Energy Healing", "Mindfulness", "Meditation", "Yoga",
        "Tai Chi", "Qigong", "Pilates", "Aerobics", "Dance", "Ballet", "Jazz Dance", "Hip Hop Dance", "Tap Dance", "Contemporary Dance",
        "Modern Dance", "Ballroom Dance", "Salsa", "Tango", "Waltz", "Swing Dance", "Folk Dance", "Line Dance", "Square Dance", "Cheerleading",
        "Gymnastics", "Acrobatics", "Parkour", "Freerunning", "Martial Arts", "Boxing", "Wrestling", "Judo", "Karate", "Tae Kwon Do",
        "Jiu-Jitsu", "Krav Maga", "Capoeira", "Kung Fu", "Aikido", "Kickboxing", "Mixed Martial Arts", "Fencing", "Archery", "Shooting",
        "Hunting", "Trapping", "Fishing", "Spearfishing", "Boating", "Sailing", "Kayaking", "Canoeing", "Stand-Up Paddleboarding", "Windsurfing",
        "Kitesurfing", "Surfing", "Water Skiing", "Wakeboarding", "Scuba Diving", "Snorkeling", "Free Diving", "Swimming", "Lifeguarding", "Water Safety",
        "Rock Climbing", "Bouldering", "Mountaineering", "Ice Climbing", "Hiking", "Backpacking", "Camping", "Bushcraft", "Orienteering", "Map Reading",
        "Compass Use", "GPS Navigation", "First Aid", "CPR", "Emergency Response", "Disaster Preparedness", "Firefighting", "Search and Rescue", "Law Enforcement", "Security",
        "Self-Defense", "Tactical Training", "Driving", "Motorcycle Riding", "Bicycling", "Horseback Riding", "Animal Training", "Animal Care", "Veterinary Medicine", "Farriery",
        "Blacksmithing", "Welding", "Carpentry", "Woodworking", "Cabinet Making", "Furniture Making", "Home Improvement", "Plumbing", "Electrical Work", "HVAC",
        "Landscaping", "Gardening", "Organic Farming", "Urban Farming", "Hydroponics", "Aquaponics", "Permaculture", "Sustainable Living", "Green Energy", "Solar Energy",
        "Wind Energy", "Geothermal Energy", "Bioenergy", "Recycling", "Composting", "Upcycling", "DIY Projects", "Craftsmanship", "Artisan Skills", "Baking",
        "Cooking", "Canning", "Pickling", "Fermenting", "Cheese Making", "Bread Making", "Pastry Making", "Cake Decorating", "Chocolate Making", "Candy Making"
    ]
    if skill is None:
        skill = random.choice(skills)
        skill += f", {random.choice(skills)}"
        skill += f", and {random.choice(skills)}"
    
    personality_traits = [
        "Brave", "Cautious", "Charismatic", "Impulsive", "Analytical",
        "Ruthless", "Kind-hearted", "Cunning", "Loyal", "Secretive",
        "Optimistic", "Pessimistic", "Adventurous", "Shy", "Outgoing",
        "Sarcastic", "Humorous", "Serious", "Mischievous", "Inquisitive",
        "Introverted", "Extroverted", "Hardworking", "Lazy", "Empathetic",
        "Stoic", "Imaginative", "Realistic", "Passionate", "Apathetic",
        "Curious", "Nurturing", "Spontaneous", "Meticulous", "Clumsy",
        "Witty", "Skeptical", "Generous", "Selfish", "Gentle",
        "Assertive", "Submissive", "Eccentric", "Pragmatic", "Dreamy",
        "Loud", "Quiet", "Resourceful", "Naive", "Determined",
        "Indecisive", "Inventive", "Dramatic", "Easy-going", "Competitive",
        "Supportive", "Detached", "Fickle", "Grumpy", "Cheerful",
        "Aloof", "Warm", "Bold", "Timid", "Patient",
        "Impatient", "Cynical", "Trusting", "Playful", "Serious",
        "Quirky", "Observant", "Forgetful", "Calculating", "Zealous",
        "Carefree", "Sassy", "Loyal", "Unpredictable", "Sentimental",
        "Tidy", "Messy", "Frugal", "Spendthrift", "Brash",
        "Tactful", "Insecure", "Confident", "Brooding", "Jovial",
        "Worrywart", "Free-spirited", "Workaholic", "Perfectionist", "Gullible",
        "Romantic", "Realist", "Chatterbox", "Silent", "Stoic","Dominatrix"
    ]
    if personality is None:
        personality = random.choice(personality_traits)
        personality += f", {random.choice(personality_traits)}"
        personality += f", and {random.choice(personality_traits)}"
    
    fears = [
        "Heights", "Water", "Enclosed Spaces", "Failure", "Rejection",
        "Loneliness", "Darkness", "Public Speaking", "Spiders", "Death"
    ]
    if fear is None:
        fear = random.choice(fears)
    
    goals = [
        "Trying to have fun", "Drinking to forget", "Brought by friends", "Networking for business", "Celebrating a promotion", 
        "Looking for love", "Escaping home life", "Supporting a friend", "Enjoying the music", "Meeting new people", 
        "Exploring new experiences", "Curiosity", "Reconnecting with old friends", "Hoping to find inspiration", "Following a crush", 
        "Enjoying the atmosphere", "Seeking adventure", "Finding a distraction", "On a date", "Celebrating a milestone", 
        "Showing off a new outfit", "Testing a new look", "Scoping out potential clients", "Getting over a breakup", 
        "Enjoying a rare night out", "Winning a bet", "Fulfilling a promise", "Trying to fit in", "Chasing a thrill", 
        "Seeking solitude in a crowd", "Making a statement", "Observing people", "Gathering material for a story", "Catching up with a friend", 
        "Enjoying a hobby", "Taking a break from work", "Escaping boredom", "Looking for inspiration", "Attending out of obligation", 
        "Practicing social skills", "Reliving memories", "Enjoying good food and drink", "Being a plus-one", "Avoiding loneliness", 
        "Doing something different", "Marking an anniversary", "Killing time", "Checking out the venue", "Escaping the routine"
    ]
    if goal is None:
        goal = random.choice(goals)
    
    education_levels = [
        "High School", "Bachelor's Degree", "Master's Degree", "PhD", "No Formal Education" "Street Smarts",
    ]
    if education is None:
        education = random.choice(education_levels)
    
    financial_statuses = [
        "Poor", "Working Class", "Middle Class", "Upper Middle Class", "Wealthy"
    ]
    if financial_status is None:
        financial_status = random.choice(financial_statuses)
    
    health_statuses = [
        "Excellent Health", "Good Health", "Average Health", "Poor Health", "Terminal Illness"
    ]
    if health_status is None:
        health_status = random.choice(health_statuses)
    
    accents = [
        "Australian", "British (Cockney)", "British (Received Pronunciation)", "British (Scottish)", "British (Welsh)",
        "Canadian", "Irish", "American (Southern)", "American (New York)", "American (Midwestern)",
        "American (Californian)", "American (Boston)", "American (Texan)", "French", "German",
        "Italian", "Spanish", "Russian", "Japanese", "Chinese",
        "Korean", "Indian", "Brazilian", "Mexican", "South African",
        "Nigerian", "Jamaican", "Greek", "Turkish", "Dutch",
        "Swedish", "Norwegian", "Danish", "Finnish", "Polish",
        "Portuguese", "Thai", "Vietnamese", "Filipino", "Indonesian",
        "Malaysian", "Singaporean", "Egyptian", "Moroccan", "Israeli",
        "Lebanese", "Argentinian", "Chilean", "Colombian", "Peruvian"
        ]
    if accent is None:
        accent = random.choice(accents)
        
    relation_ships = [
        "A","B","C","D","E"
    ]
    if relations is None:
        relations = random.choice(relation_ships)
    
    motives = [
        "Revenge", "Jealousy", "Greed", "Fear of exposure", "Desire for power", "Protecting a loved one", 
        "Personal gain", "Hatred", "Self-defense", "Mental illness", "Political beliefs", "Religious beliefs", 
        "Caught victim with their spouse", "Found buried treasure and didn't want to split", 
        "Inheritance dispute", "Blackmail gone wrong", "Covering up another crime", "Love triangle", 
        "Financial ruin", "Career advancement", "Protecting a secret identity", "Avenging a loved one", 
        "Power struggle", "Rivalry", "Mistaken identity", "Revenge for a family member", "Unrequited love", 
        "Preventing a scandal", "Coerced by another", "Escape from an abusive relationship", "Sibling rivalry", 
        "Desperation from debt", "Eliminating a threat", "Reclaiming stolen property", "Misinformation or misunderstanding", 
        "Accidental killing", "Paranoia", "Delusional beliefs", "Obsession", "Preventing a prophecy", "Envy of victim's success", 
        "Drug-induced violence", "Cult influence", "Preventing a takeover", "Disposing of a witness", "Vendetta", 
        "Protecting family honor", "Manipulated by a third party", "Desperate for attention", "Secret love affair", 
        "Botched robbery", "Loyalty to a mentor", "Breaking a curse", "Covering up a scandal", "Extortion threat", 
        "Revenge for past betrayal", "Fear of losing power", "Covering up an affair"
        ]

    # Create the prompt for generating the character
    prompt = f"\nCreate a character {character_counter} with the following details:\n"
    prompt += f"\nGender: {gender}\n"
    if killer:
        motive = random.choice(motives)
        prompt += f"\nThey are the killer \n Motive: {motive}\n"
    else:
        prompt += f"\nKiller: No\n Reason you are here: {goal}\n"
    #prompt += f"\nAre you the Victim?: {'Yes' if victim else 'No'}\n"
    prompt += f"\nAlignment: {alignment}\n"
    prompt += f"\nOccupation: {occupation}\n"
    prompt += f"\nHobby: {hobby}\n"
    prompt += f"\nSkill: {skill}\n"
    prompt += f"\nPersonality Trait: {personality}\n"
    prompt += f"\nFear: {fear}\n"
    #prompt += f"\nGoal: {goal}\n"
    prompt += f"\nEducation: {education}\n"
    prompt += f"\nFinancial Status: {financial_status}\n"
    prompt += f"\nHealth Status: {health_status}\n"
    prompt += f"\nThere speaking accent is {accent}\n"
    prompt += f"\nThey belong to relationship group : {relations} this means they know everyone in group {relations} in one way or another.\n "
    prompt += "\nProvide a detailed backstory and profile. You must include -Backstory - Personality - Social Connections (if they have any with the characters being made) - Goals - Secrets\n"
    
    client.beta.threads.messages.create(
        thread_id=creator_thread.id,
        role="user",
        content=prompt,
    )
    return {
        "index": index,
        "killer": killer,
        "victim": victim,
        "relations": relations
    }
    
def create_all_characters(character_details, scene_prompt):
    global character_counter
    client.beta.threads.messages.create(
        thread_id=creator_thread.id,
        role="user",
        content="You have been given a group of characters. If there are more than one and If they all belong to the same relationship group take a moment to draw connections between them. Take your time here, you are the Producer, and it is your job to make sure the Characters are compelling.",
    )
    client.beta.threads.runs.create_and_poll(
        thread_id=creator_thread.id,
        assistant_id=Creator.id,
        response_format="auto",
    )
    characters = []
    for details in character_details:
        client.beta.threads.messages.create(
            thread_id=creator_thread.id,
            role="user",
            content=f"Give me Character{details['index'] + 1}",
        )
        run = client.beta.threads.runs.create_and_poll(
            thread_id=creator_thread.id,
            assistant_id=Creator.id,
            response_format="auto"
        )
        character_profile = None
        if run.status == 'completed':
            thread_messages = client.beta.threads.messages.list(
                thread_id=creator_thread.id,
                order='desc',
                limit=1,
            )
            for message in thread_messages.data:
                if message.role == 'assistant' and message.content[0].type == 'text':
                    character_profile = message.content[0].text.value
                    name, assistant, thread = create_assistant_from_profile(character_profile)
                    picture = create_image(character_profile, name, scene_prompt)
                    characters.append((name, assistant, thread, details["killer"], details["victim"], details["relations"], picture))
                    print(f"New assistant created with name: {name}")
                    print(f"Assistant ID: {assistant}")
                    print(f"Thread ID: {thread}")
                    print(f"Killer: {'Yes' if details['killer'] else 'No'}")
                    print(f"Victim: {'Yes' if details['victim'] else 'No'}")
                    print(f"Relationship Group: {details['relations']}")
        else:
            print(run.status)
        character_counter -= 1
    return characters

def extract_name(character_profile):
    match = re.search(r'Name:\s*([^\n]+)', character_profile)
    if match:
        name = match.group(1).strip()
        return name
    return "Unnamed Character"

def create_assistant_from_profile(character_profile):
    name = extract_name(character_profile)
    if name.startswith('**'):
        name = name[2:]

    assistants = client.beta.assistants.create(
        name=name,
        instructions=f"You are, {name} Become them and respond as they would.\n Only use words, do not describe actions.\n\n{character_profile}",
        model="gpt-4o"
    )
    threads = client.beta.threads.create()
    thread = threads.id
    assistant = assistants.id

    return name, assistant, thread

def sanitize_filename(name):
    # Remove any invalid characters from the filename
    sanitized = re.sub(r'[^\w\-_\. ]', '_', name)
    return sanitized

def generate_image_description(character_profile, scene_prompt):
    client.beta.threads.messages.create(
        thread_id=designer_thread.id,
        role='user',
        content=f'Heres the scene {scene_prompt}, and here is the character profile \n\n{character_profile}'
    )
    
    run = client.beta.threads.runs.create_and_poll(
        thread_id=designer_thread.id,
        assistant_id=Designer.id,
        response_format="auto"
    )

    appearance = None
    if run.status == 'completed':
        thread_messages = client.beta.threads.messages.list(
            thread_id=designer_thread.id,
            order='desc',
            limit=1,
        )
        for message in thread_messages.data:
            if message.role == 'assistant' and message.content[0].type == 'text':
                appearance = message.content[0].text.value
                print(appearance)
    return appearance

def create_image(character_profile, name, scene_prompt):
    clean_name = sanitize_filename(name)
    file_name = f'{clean_name}.png'
    folder_path = r"C:\Users\Jesse\Pictures\StreamAssets\Characters"
    appearance = generate_image_description(character_profile, scene_prompt)
        #old way
        # client.beta.threads.messages.create(
        #     thread_id=designer_thread.id,
        #     role='user',
        #     content=character_profile
        # )
        
        # run = client.beta.threads.runs.create_and_poll(
        #     thread_id=designer_thread.id,
        #     assistant_id=Designer.id,
        #     response_format="auto"
        # )

        # appearance = None
        # if run.status == 'completed':
        #     thread_messages = client.beta.threads.messages.list(
        #         thread_id=designer_thread.id,
        #         order='desc',
        #         limit=1,
        #     )
        #     for message in thread_messages.data:
        #         if message.role == 'assistant' and message.content[0].type == 'text':
        #             appearance = message.content[0].text.value
        #             print(appearance)
    max_retries = 3
    for attempt in range(max_retries):
        try:            
            response = client.images.generate(
                model='dall-e-3',
                prompt=f'Create a Vetical full body image of {name} with no other characters or objects in the frame.\n The character should be standing alone against a plain backdrop.\n Here is your prompt \n {appearance}\n\n MOST IMPORTANT RULE - Only One Character printed one time - and must be vertical',
                n=1,
                size="1024x1792",
                response_format='url'
            )
            # Wait for the image URL to become available
            image_url = None
            while not image_url:
                try:
                    image_url = response.data[0].url
                except (KeyError, IndexError):
                    print("Image not ready yet. Waiting...")
                    time.sleep(2)  # Wait for 1 second before checking again

            # Prepare the JSON payload for Azure API
            payload = {
                "url": image_url
            }
            print(f"Payload: {payload}")
            
            # Send the image URL to Azure Background Removal API
            azure_url = f"{azure_endpoint}/computervision/imageanalysis:segment?api-version=2023-02-01-preview&mode=backgroundRemoval"
            headers = {
                "Ocp-Apim-Subscription-Key": azure_subscription_key,
                "Content-Type": "application/json"
            }
            print(f"Sending request to Azure: {azure_url}")
            
            response = requests.post(azure_url, headers=headers, json=payload)
            print(f"Azure response status code: {response.status_code}")

            # Check if the response is successful
            if response.status_code == 200:
                # Save the PNG response directly to a file
                mask_image_path = os.path.join(folder_path, os.path.splitext(file_name)[0] + "_mask.png")
                with open(mask_image_path, "wb") as mask_file:
                    mask_file.write(response.content)
                print(f"Mask image saved to {mask_image_path}")
            else:
                print(f"Failed to remove background: {response.status_code}, {response.text}")
                return None

            return mask_image_path
        except openai.error.BadRequestError as e:
            error_details = e.args[0]  # Retrieve the error details
            if 'content_policy_violation' in error_details:
                print(f"Content policy violation detected: {error_details}. Attempt {attempt + 1} of {max_retries}.")
                # Generate a new safe description
                appearance = generate_image_description(character_profile)
                print(f"Generated new appearance description: {appearance}")
            else:
                raise

    print("Max retries reached. Failed to generate image due to content policy violations.")
    return None

def main(scene_prompt):
    num_characters = int(input("Enter the number of characters to create: "))

    killer_index = None
    victim_index = None

    choice = input("Do you want a killer, a victim, or both? (k/v/b/n): ").strip().lower()
    if choice == "b":
        killer_index = random.choice(range(num_characters))
        victim_index = random.choice([i for i in range(num_characters) if i != killer_index])
    elif choice == "k":
        killer_index = random.choice(range(num_characters))
    elif choice == "v":
        victim_index = random.choice(range(num_characters))

    relation_choice = input("Would you like to pick relations? (y/n): ").strip().lower()
    if relation_choice == "y":
        relations = input("Enter relationship group name: ").strip()
    else:
        relations = None

    customize = input("Would you like to customize characters? (y/n): ").strip().lower()

    character_details = []

    for i in range(num_characters):
        print(f"\nCreating character {i + 1}:")
        killer = (i == killer_index)
        victim = (i == victim_index)

        if customize == 'y':
            gender = get_user_input("Enter gender (or leave blank to randomize): ")
            alignment = get_user_input("Enter alignment (or leave blank to randomize): ")
            education = get_user_input("Enter education level (or leave blank to randomize): ")
            personality = get_user_input("Enter personality trait (or leave blank to randomize): ")
            hobby = get_user_input("Enter hobby (or leave blank to randomize): ")
            skill = get_user_input("Enter skill (or leave blank to randomize): ")
            fear = get_user_input("Enter fear (or leave blank to randomize): ")
            goal = get_user_input("Enter goal (or leave blank to randomize): ")
            accent = get_user_input("Enter accent (or leave blank to randomize): ")
            occupation = get_user_input("Enter occupation (or leave blank to randomize): ")
            health_status = get_user_input("Enter health status (or leave blank to randomize): ")
            financial_status = get_user_input("Enter financial status (or leave blank to randomize): ")

            character_info = new_character(i, killer, victim, gender, alignment, education, personality, hobby, skill, fear, goal, accent, relations, occupation, health_status, financial_status)
        else:
            character_info = new_character(i, killer, victim, relations)
        
        character_details.append(character_info)

    print("\nCreating all characters...")
    characters = create_all_characters(character_details, scene_prompt)
    return characters

# Make sure this script is only executed if this module is the main program
if __name__ == "__main__":
    characters = main()
    print("\nCreated characters:")
    for name, assistant, thread in characters:
        print(f"Character Name: {name}, Assistant ID: {assistant}, thread = {thread}")
