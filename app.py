from slack_bolt import App
import json
import random
import asyncio
from datetime import datetime
import os
import aiohttp
import requests
from typing import Optional
import threading
import time

# some random variables i might need later
max_facts_per_day = 50
current_trivia_count=0
bot_version="1.0-slack"
last_api_call_time=None
debug_mode=False
fact_limit=1000

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

facts=[
    "Bananas are berries but strawberries aren't",
    "Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs",
    "A group of flamingos is called a 'flamboyance'",
    "Octopuses have three hearts and blue blood",
    "The shortest war in history lasted only 38-45 minutes",
    "Wombat poop is cube-shaped",
    "There are more possible games of chess than atoms in the observable universe",
    "Sea otters hold hands while sleeping so they don't drift apart",
    "A shrimp's heart is in its head",
    "Butterflies taste with their feet",
    "The Great Wall of China isn't visible from space with the naked eye",
    "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid",
    "Oxford University is older than the Aztec Empire",
    "A day on Venus is longer than its year",
    "Sharks are older than trees",
    "The unicorn is Scotland's national animal",
    "Lobsters were once considered prison food",
    "Bubble wrap was originally invented as wallpaper",
    "The dot over a lowercase 'i' or 'j' is called a tittle",
    "Penguins have knees",
    "A group of pandas is called an embarrassment",
    "Carrots were originally purple",
    "The human brain uses about 20% of the body's total energy",
    "Sloths can rotate their heads 270 degrees",
    "A blue whale's heart is as big as a small car",
    "Dolphins have names for each other",
    "Cats can't taste sweetness",
    "A group of owls is called a parliament",
    "The longest recorded flight of a chicken is 13 seconds",
    "Elephants are afraid of bees",
    "Goldfish have better color vision than humans",
    "A single cloud can weigh more than a million pounds",
    "The human nose can detect about 1 trillion different scents",
    "Koalas sleep 18-22 hours per day",
    "A group of frogs is called an army",
    "Snails can sleep for up to 3 years",
    "The tongue is the strongest muscle in the human body relative to its size",
    "Polar bears have black skin under their white fur",
    "A group of jellyfish is called a smack",
    "Hummingbirds are the only birds that can fly backwards"
]

fact_reactions={}
user_scores={}
daily_trivia={}
user_submitted_facts=[]
api_facts_cache=[]
fact_categories={
    "animals":["Bananas are berries but strawberries aren't","Octopuses have three hearts and blue blood","Sea otters hold hands while sleeping so they don't drift apart","A shrimp's heart is in its head","Butterflies taste with their feet","Penguins have knees","Cats can't taste sweetness","Elephants are afraid of bees","Goldfish have better color vision than humans","Koalas sleep 18-22 hours per day","Snails can sleep for up to 3 years","Polar bears have black skin under their white fur","Hummingbirds are the only birds that can fly backwards"],
    "history":["Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid","Oxford University is older than the Aztec Empire","The shortest war in history lasted only 38-45 minutes","Lobsters were once considered prison food"],
    "science":["There are more possible games of chess than atoms in the observable universe","The Great Wall of China isn't visible from space with the naked eye","A day on Venus is longer than its year","Sharks are older than trees","The human brain uses about 20% of the body's total energy","A single cloud can weigh more than a million pounds","The human nose can detect about 1 trillion different scents"],
    "random":["A group of flamingos is called a 'flamboyance'","Wombat poop is cube-shaped","The unicorn is Scotland's national animal","Bubble wrap was originally invented as wallpaper","The dot over a lowercase 'i' or 'j' is called a tittle","A group of pandas is called an embarrassment","Carrots were originally purple","Sloths can rotate their heads 270 degrees","Dolphins have names for each other","A group of owls is called a parliament","The longest recorded flight of a chicken is 13 seconds","A blue whale's heart is as big as a small car","A group of frogs is called an army","The tongue is the strongest muscle in the human body relative to its size","A group of jellyfish is called a smack"],
    "user_submitted":[]
}

daily_channel=None
bot_start_time=datetime.now()

def load_fact_data():
    global fact_reactions,user_scores,daily_trivia,user_submitted_facts,api_facts_cache
    try:
        with open('fact_data.json','r',encoding='utf-8') as f:
            data=json.load(f)
            fact_reactions=data.get('fact_reactions',{})
            user_scores=data.get('user_scores',{})
            daily_trivia=data.get('daily_trivia',{})
            user_submitted_facts=data.get('user_submitted_facts',[])
            api_facts_cache=data.get('api_facts_cache',[])
    except FileNotFoundError:
        print("No existing fact data found, starting fresh...")
        fact_reactions={}
        user_scores={}
        daily_trivia={}
        user_submitted_facts=[]
        api_facts_cache=[]
    except json.JSONDecodeError as e:
        print(f"Error reading fact data JSON: {e}")
        fact_reactions={}
        user_scores={}
        daily_trivia={}
        user_submitted_facts=[]
        api_facts_cache=[]
    except Exception as error:
        print(f"Unexpected error loading fact data: {error}")
        fact_reactions={}
        user_scores={}
        daily_trivia={}
        user_submitted_facts=[]
        api_facts_cache=[]
    
    fact_categories["user_submitted"]=user_submitted_facts
    
    all_facts=[]
    for category_facts in fact_categories.values():
        all_facts.extend(category_facts)
    all_facts.extend(api_facts_cache)
    
    for fact in all_facts:
        if fact not in fact_reactions:
            fact_reactions[fact]={'thumbs_up':0,'thumbs_down':0}

def save_fact_data():
    max_retries=3
    for attempt in range(max_retries):
        try:
            backup_data={
                'fact_reactions':fact_reactions,
                'user_scores':user_scores,
                'daily_trivia':daily_trivia,
                'user_submitted_facts':user_submitted_facts,
                'api_facts_cache':api_facts_cache
            }
            with open('fact_data.json','w',encoding='utf-8') as f:
                json.dump(backup_data,f,indent=2)
            return True
        except Exception as error:
            print(f'Error saving fact data (attempt {attempt+1}): {error}')
            if attempt<max_retries-1:
                time.sleep(0.5)
            else:
                print("Failed to save data after all retries!")
                return False

def fetch_random_fact_from_api():
    apis=[
        "https://uselessfacts.jsph.pl/random.json?language=en",
        "https://catfact.ninja/fact",
        "https://dog-api.kinduff.com/api/facts",
        "https://meowfacts.herokuapp.com/"
    ]
    
    for api_url in apis:
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code==200:
                try:
                    data=response.json()
                except:
                    continue
                
                fact=None
                if 'text' in data:
                    fact=data['text']
                elif 'fact' in data:
                    fact=data['fact']
                elif 'data' in data and isinstance(data['data'],list) and data['data']:
                    fact=data['data'][0]
                
                if fact and len(fact)>10 and len(fact)<500:
                    if fact not in api_facts_cache and fact not in str(get_all_facts()):
                        api_facts_cache.append(fact)
                        fact_reactions[fact]={'thumbs_up':0,'thumbs_down':0}
                        save_fact_data()
                    return fact
        except requests.Timeout:
            print(f"Timeout fetching from {api_url}")
            continue
        except requests.RequestException as e:
            print(f"Request error fetching from {api_url}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error fetching from {api_url}: {e}")
            continue
    
    return None

def get_all_facts():
    all_facts=[]
    for category_facts in fact_categories.values():
        all_facts.extend(category_facts)
    all_facts.extend(api_facts_cache)
    return list(set(all_facts))

def load_more_facts_sync():
    print("Loading more facts from APIs...")
    successful_loads=0
    failed_loads=0
    for i in range(8):
        try:
            fact=fetch_random_fact_from_api()
            if fact:
                print(f"Added new fact: {fact[:50]}...")
                successful_loads+=1
            else:
                failed_loads+=1
            time.sleep(1.2)
        except Exception as e:
            print(f"Error loading fact {i+1}: {e}")
            failed_loads+=1
            continue
    print(f"Successfully loaded {successful_loads} new facts, failed: {failed_loads}")

# Slack command handlers
@app.command("/fact")
def fact_command(ack, respond, command):
    ack()
    try:
        all_facts=get_all_facts()
        
        if len(all_facts)<20:
            try:
                load_more_facts_sync()
                all_facts=get_all_facts()
            except:
                pass
        
        if not all_facts:
            respond("Sorry, no facts available right now! Try again later.")
            return
            
        fact=random.choice(all_facts)
        
        thumbs_up=fact_reactions.get(fact,{}).get('thumbs_up',0)
        thumbs_down=fact_reactions.get(fact,{}).get('thumbs_down',0)
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🧠 *Fun Fact from BrainyJim!*\n\n{fact}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Reactions: :thumbsup: {thumbs_up} | :thumbsdown: {thumbs_down}"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":thumbsup:"
                    },
                    "action_id": f"thumbs_up_{len(fact_reactions)}"
                }
            }
        ]
        
        respond(blocks=blocks)
        
    except Exception as error:
        respond("Something went wrong getting a fact! Please try again.")
        print(f"Error in fact command: {error}")

@app.command("/categoryfact")
def category_fact_command(ack, respond, command):
    ack()
    try:
        category = command['text'].strip().lower()
        
        if not category:
            available_cats=', '.join(fact_categories.keys())
            respond(f"Please specify a category! Choose from: {available_cats}")
            return
            
        if category not in fact_categories:
            available_cats=', '.join(fact_categories.keys())
            respond(f"Invalid category! Choose from: {available_cats}")
            return
        
        category_facts=fact_categories[category]
        if not category_facts:
            respond(f"No facts available for {category} category yet!")
            return
            
        fact=random.choice(category_facts)
        
        thumbs_up=fact_reactions.get(fact,{}).get('thumbs_up',0)
        thumbs_down=fact_reactions.get(fact,{}).get('thumbs_down',0)
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🧠 *{category.title()} Fact from BrainyJim!*\n\n{fact}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Reactions: :thumbsup: {thumbs_up} | :thumbsdown: {thumbs_down}"
                }
            }
        ]
        
        respond(blocks=blocks)
        
    except Exception as error:
        respond("Error getting category fact! Try again.")
        print(f"Error in category fact command: {error}")

@app.command("/trivia")
def trivia_command(ack, respond, command):
    ack()
    trivia_questions=[
        {"question":"What animal's poop is cube-shaped?","answer":"wombat","options":["koala","wombat","kangaroo","platypus"]},
        {"question":"How many hearts does an octopus have?","answer":"3","options":["2","3","4","5"]},
        {"question":"What is Scotland's national animal?","answer":"unicorn","options":["dragon","unicorn","lion","eagle"]},
        {"question":"How long can a snail sleep?","answer":"3 years","options":["1 year","2 years","3 years","6 months"]},
        {"question":"What was bubble wrap originally invented as?","answer":"wallpaper","options":["packaging","wallpaper","insulation","carpet"]},
        {"question":"What is the dot over a lowercase 'i' called?","answer":"tittle","options":["dot","tittle","point","mark"]},
        {"question":"Which is older: Oxford University or the Aztec Empire?","answer":"oxford","options":["oxford","aztec","same age","unknown"]},
        {"question":"Can cats taste sweetness?","answer":"no","options":["yes","no","only some","depends on breed"]},
        {"question":"Are bananas berries?","answer":"yes","options":["yes","no","sometimes","depends on type"]},
        {"question":"How long was the shortest war in history?","answer":"38-45 minutes","options":["10 minutes","38-45 minutes","2 hours","1 day"]},
        {"question":"What color were carrots originally?","answer":"purple","options":["orange","purple","yellow","white"]},
        {"question":"How many degrees can sloths rotate their heads?","answer":"270","options":["180","270","360","90"]}
    ]
    
    try:
        question_data=random.choice(trivia_questions)
        user_id=command['user_id']
        
        if user_id not in user_scores:
            user_scores[user_id]={"correct":0,"total":0}
        
        user_score=user_scores[user_id]
        
        option_buttons = []
        for i, option in enumerate(question_data['options']):
            option_buttons.append({
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": f"{i+1}. {option}"
                },
                "action_id": f"trivia_answer_{i}_{len(daily_trivia)}"
            })
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🎯 *BrainyJim Trivia Challenge!*\n\n*Question:* {question_data['question']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your Score: ✅ {user_score['correct']}/{user_score['total']} correct"
                }
            },
            {
                "type": "actions",
                "elements": option_buttons
            }
        ]
        
        trivia_id = f"trivia_{len(daily_trivia)}"
        daily_trivia[trivia_id]={
            "answer":question_data['answer'],
            "options":question_data['options'],
            "user_id":user_id
        }
        save_fact_data()
        
        respond(blocks=blocks)
        
    except Exception as error:
        respond("Error starting trivia! Please try again.")
        print(f"Error in trivia command: {error}")

@app.command("/leaderboard")
def leaderboard_command(ack, respond):
    ack()
    try:
        if not user_scores:
            respond("No scores yet! Play some trivia with `/trivia`!")
            return
        
        sorted_users=sorted(user_scores.items(),key=lambda x:x[1]['correct'],reverse=True)[:10]
        
        leaderboard_text="🏆 *BrainyJim Trivia Leaderboard*\n\n"
        for i,(user_id,score) in enumerate(sorted_users,1):
            try:
                # In Slack we can't easily get usernames, so we'll use user IDs
                username=f"<@{user_id}>"
            except:
                username=f"User {user_id}"
            
            percentage=(score['correct']/score['total']*100) if score['total']>0 else 0
            leaderboard_text+=f"{i}. {username} - {score['correct']}/{score['total']} ({percentage:.1f}%)\n"
        
        respond(leaderboard_text)
    except Exception as error:
        respond("Error loading leaderboard! Try again.")
        print(f"Error in leaderboard command: {error}")

@app.command("/mystats")
def mystats_command(ack, respond, command):
    ack()
    user_id = command['user_id']
    
    if user_id not in user_scores:
        respond("You haven't played any trivia yet! Try `/trivia` to start!")
        return
    
    score = user_scores[user_id]
    percentage = (score['correct'] / score['total'] * 100) if score['total'] > 0 else 0
    
    all_users = list(user_scores.keys())
    sorted_users = sorted(user_scores.items(), key=lambda x: x[1]['correct'], reverse=True)
    
    rank = next((i+1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id), len(all_users))
    
    stats_text = f"📊 *<@{user_id}>'s Stats*\n\n"
    stats_text += f"Trivia Score: ✅ {score['correct']}/{score['total']} correct ({percentage:.1f}%)\n"
    stats_text += f"Rank: #{rank} out of {len(all_users)} players"
    
    respond(stats_text)

@app.command("/categories")
def categories_command(ack, respond):
    ack()
    categories_text = "📚 *Available Fact Categories*\n\n"
    
    for category, facts in fact_categories.items():
        categories_text += f"• *{category.title().replace('_', ' ')}*: {len(facts)} facts\n"
    
    categories_text += f"• *API Facts*: {len(api_facts_cache)} facts from APIs\n"
    
    total_facts = len(get_all_facts())
    categories_text += f"\n*Total Facts*: {total_facts} facts available!\n"
    categories_text += "\nUse `/categoryfact [category]` to get a fact from a specific category!"
    
    respond(categories_text)

@app.command("/submitfact")
def submit_fact_command(ack, respond, command):
    ack()
    fact = command['text'].strip()
    
    if len(fact) < 10:
        respond("Your fact is too short! Please make it at least 10 characters long.")
        return
    
    if len(fact) > 500:
        respond("Your fact is too long! Please keep it under 500 characters.")
        return
    
    if fact in get_all_facts():
        respond("This fact already exists in our database!")
        return
    
    user_submitted_facts.append(fact)
    fact_categories["user_submitted"] = user_submitted_facts
    fact_reactions[fact] = {'thumbs_up': 0, 'thumbs_down': 0}
    save_fact_data()
    
    success_text = "✅ *Fact Submitted Successfully!*\n\n"
    success_text += f"Thank you for contributing to our fact database!\n\n*Your fact:* {fact}\n\n"
    success_text += "Your fact is now part of our database and can appear in random fact selections!"
    
    respond(success_text)

@app.command("/morefacts")
def load_more_facts_command(ack, respond):
    ack()
    respond("Loading more facts from online sources... please wait!")
    
    initial_count = len(get_all_facts())
    load_more_facts_sync()
    new_count = len(get_all_facts())
    
    facts_added = new_count - initial_count
    
    success_text = f"📚 *Fact Database Updated!*\n\n"
    success_text += f"Successfully added {facts_added} new facts from online sources!\n"
    success_text += f"Total Facts: {new_count} facts now available\n"
    success_text += f"API Facts: {len(api_facts_cache)} facts from APIs"
    
    respond(success_text)

@app.command("/guess")
def guess_command(ack, respond, command):
    ack()
    try:
        number = int(command['text'].strip())
    except ValueError:
        respond("Please provide a valid number between 1 and 100!")
        return
        
    if number < 1 or number > 100:
        respond("Please guess a number between 1 and 100!")
        return
    
    secret_number = random.randint(1, 100)
    difference = abs(number - secret_number)
    
    all_facts = get_all_facts()
    
    if difference == 0:
        title = "🎯 PERFECT GUESS!"
        description = f"Amazing! You guessed exactly {secret_number}!"
    elif difference <= 5:
        title = "🔥 So Close!"
        description = f"Very close! You guessed {number}, I was thinking of {secret_number}!"
    elif difference <= 15:
        title = "👍 Good Guess!"
        description = f"Not bad! You guessed {number}, I was thinking of {secret_number}!"
    else:
        title = "😅 Nice Try!"
        description = f"You guessed {number}, I was thinking of {secret_number}!"
    
    fact = random.choice(all_facts)
    
    result_text = f"*{title}*\n\n{description}\n\n🧠 *Bonus Fact:* {fact}"
    
    respond(result_text)

@app.command("/funfact")
def funfact_command(ack, respond, command):
    ack()
    topic = command['text'].strip()
    
    if not topic:
        respond("Please specify a topic! Example: `/funfact space`")
        return
    
    topic_lower = topic.lower()
    
    topic_facts = {
        "space": ["A day on Venus is longer than its year", "The human nose can detect about 1 trillion different scents", "A single cloud can weigh more than a million pounds"],
        "ocean": ["A blue whale's heart is as big as a small car", "A shrimp's heart is in its head", "Sea otters hold hands while sleeping so they don't drift apart"],
        "food": ["Bananas are berries but strawberries aren't", "Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs", "Carrots were originally purple", "Cats can't taste sweetness"],
        "body": ["The human brain uses about 20% of the body's total energy", "The human nose can detect about 1 trillion different scents", "The tongue is the strongest muscle in the human body relative to its size", "Butterflies taste with their feet"],
        "time": ["Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid", "Oxford University is older than the Aztec Empire", "The shortest war in history lasted only 38-45 minutes"]
    }
    
    matching_facts = []
    for key, facts in topic_facts.items():
        if topic_lower in key or key in topic_lower:
            matching_facts.extend(facts)
    
    if not matching_facts:
        all_facts = []
        for category_facts in fact_categories.values():
            all_facts.extend(category_facts)
        fact = random.choice(all_facts)
        result_text = f"🤔 *Couldn't find that topic...*\n\nBut here's a random fact instead!\n\n{fact}"
    else:
        fact = random.choice(matching_facts)
        result_text = f"🧠 *Fun Fact about {topic.title()}!*\n\n{fact}"
    
    respond(result_text)

@app.command("/random")
def random_command(ack, respond):
    ack()
    random_actions = [
        "fact", "compliment", "joke", "challenge", "riddle", "tip"
    ]
    
    action = random.choice(random_actions)
    
    if action == "fact":
        all_facts = get_all_facts()
        fact = random.choice(all_facts)
        result_text = f"🎲 *Random Fact!*\n\n{fact}"
    elif action == "compliment":
        compliments = [
            "You're absolutely fantastic!",
            "You have amazing taste in Slack bots!",
            "Your curiosity is inspiring!",
            "You're the reason I love sharing facts!",
            "You make learning fun!",
            "Your questions always brighten my day!"
        ]
        result_text = f"💝 *Random Compliment!*\n\n{random.choice(compliments)}"
    elif action == "joke":
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "What do you call a fake noodle? An impasta!",
            "Why don't eggs tell jokes? They'd crack each other up!"
        ]
        result_text = f"😂 *Random Joke!*\n\n{random.choice(jokes)}"
    elif action == "challenge":
        challenges = [
            "Try to learn one new fact today!",
            "Share a fact with a friend!",
            "Look up something you've always wondered about!",
            "Ask me about a topic you're curious about!",
            "Try the trivia command and beat your score!"
        ]
        result_text = f"🎯 *Random Challenge!*\n\n{random.choice(challenges)}"
    elif action == "riddle":
        riddles = [
            "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I? (Answer: A map!)",
            "What has hands but cannot clap? (Answer: A clock!)",
            "What gets wetter the more it dries? (Answer: A towel!)",
            "What has keys but no locks? (Answer: A piano!)",
            "What can travel around the world while staying in a corner? (Answer: A stamp!)"
        ]
        result_text = f"🧩 *Random Riddle!*\n\n{random.choice(riddles)}"
    else:  # tip
        tips = [
            "Use `/categories` to see all available fact categories!",
            "Try `/guess [number]` for a fun guessing game!",
            "Use `/trivia` to test your knowledge!",
            "Check `/leaderboard` to see the top players!",
            "Use `/funfact [topic]` to get facts about specific topics!",
            "Use `/mystats` to check your personal stats!",
            "Try `/submitfact` to add your own facts!"
        ]
        result_text = f"💡 *Random Tip!*\n\n{random.choice(tips)}"
    
    respond(result_text)

# Handle button clicks for trivia answers
@app.action("trivia_answer_0")
@app.action("trivia_answer_1")  
@app.action("trivia_answer_2")
@app.action("trivia_answer_3")
def handle_trivia_answer(ack, body, respond):
    ack()
    
    action_id = body["actions"][0]["action_id"]
    user_id = body["user"]["id"]
    
    # Extract answer index and trivia ID from action_id
    parts = action_id.split("_")
    choice_index = int(parts[2])
    trivia_id = f"trivia_{parts[3]}"
    
    if trivia_id in daily_trivia:
        trivia_data = daily_trivia[trivia_id]
        if user_id == trivia_data['user_id']:
            
            selected_answer = trivia_data['options'][choice_index]
            correct_answer = trivia_data['answer']
            
            user_scores[trivia_data['user_id']]['total'] += 1
            
            if selected_answer.lower() == correct_answer.lower():
                user_scores[trivia_data['user_id']]['correct'] += 1
                result_emoji = "✅"
                result_text = "Correct!"
            else:
                result_emoji = "❌"
                result_text = f"Wrong! The correct answer was: {correct_answer}"
            
            user_score = user_scores[trivia_data['user_id']]
            percentage = (user_score['correct'] / user_score['total'] * 100) if user_score['total'] > 0 else 0
            
            final_text = f"*{result_emoji} Trivia Result*\n\n{result_text}\n\nYour Score: ✅ {user_score['correct']}/{user_score['total']} correct ({percentage:.1f}%)"
            
            respond(final_text, replace_original=True)
            
            del daily_trivia[trivia_id]
            save_fact_data()

# Handle mentions and direct messages
@app.event("app_mention")
def handle_mention(event, say):
    content = event['text'].lower()
    user_id = event['user']
    
    if 'fact' in content:
        all_facts = get_all_facts()
        fact = random.choice(all_facts)
        
        thumbs_up = fact_reactions[fact]['thumbs_up']
        thumbs_down = fact_reactions[fact]['thumbs_down']
        
        fact_text = f"🧠 *Fun Fact from BrainyJim!*\n\n{fact}\n\nReactions: :thumbsup: {thumbs_up} | :thumbsdown: {thumbs_down}"
        
        say(fact_text)
    
    elif 'hello' in content or 'hi' in content:
        greetings = [
            f"Hello there, <@{user_id}>! 🧠",
            f"Hi <@{user_id}>! Ready for some brain food? 🧠",
            f"Hey <@{user_id}>! What can I teach you today? 📚",
            f"Greetings, <@{user_id}>! Let's learn something new! ✨"
        ]
        say(random.choice(greetings))
    
    elif 'help' in content:
        help_text = "🤖 *BrainyJim Help*\n\nHere's what I can do for you!\n\n"
        help_text += "*Slash Commands:*\n"
        help_text += "• `/fact` - Random fact\n"
        help_text += "• `/categoryfact` - Category-specific fact\n"
        help_text += "• `/trivia` - Play trivia\n"
        help_text += "• `/guess` - Number guessing game\n"
        help_text += "• `/funfact` - Topic-specific fact\n"
        help_text += "• `/random` - Random interaction\n"
        help_text += "• `/leaderboard` - See top players\n"
        help_text += "• `/mystats` - Your stats\n"
        help_text += "• `/categories` - View categories\n\n"
        help_text += "*Mention Commands:*\nJust mention me and say 'fact', 'hello', or 'help'!"
        
        say(help_text)
    
    elif 'thank' in content:
        thanks_responses = [
            "You're so welcome! 😊",
            "Happy to help! 🎉",
            "My pleasure! Keep learning! 📚",
            "Anytime! Knowledge is power! 💪",
            "You're awesome! 🌟"
        ]
        say(random.choice(thanks_responses))
    
    else:
        responses = [
            "I'm here to share amazing facts! Try `/fact` or just ask for a fact! 🧠",
            "Want to learn something cool? Use `/random` for a surprise! 🎲",
            "I love questions! Try `/trivia` to test your knowledge! 🎯",
            "Curious about something? Use `/funfact [topic]` to learn more! 🔍",
            "Say 'help' and I'll show you all my commands! 🤖"
        ]
        say(random.choice(responses))

def send_daily_fact():
    try:
        # For Slack, we would need to post to a specific channel
        # This is just a placeholder - in a real implementation you'd need channel IDs
        all_facts=get_all_facts()
        if not all_facts:
            try:
                load_more_facts_sync()
                all_facts=get_all_facts()
            except:
                print("Failed to load facts for daily fact")
                return
        
        if not all_facts:
            print("No facts available for daily fact")
            return
            
        fact=random.choice(all_facts)
        
        thumbs_up=fact_reactions.get(fact,{}).get('thumbs_up',0)
        thumbs_down=fact_reactions.get(fact,{}).get('thumbs_down',0)
        
        daily_text = f"🌅 *Daily Fun Fact from BrainyJim!*\n\n{fact}\n\n"
        daily_text += f"Reactions: :thumbsup: {thumbs_up} | :thumbsdown: {thumbs_down}\n"
        daily_text += f"Daily fact for {datetime.now().strftime('%B %d, %Y')} • {len(all_facts)} facts in database"
        
        print(f"Daily fact ready: {fact}")
        # In a real implementation, you'd post this to configured channels
        
    except Exception as error:
        print(f"Error preparing daily fact: {error}")

def start_scheduler_sync():
    while True:
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:
            send_daily_fact()
            time.sleep(60)
        time.sleep(30)

# Startup initialization  
def initialize_bot():
    print('BrainyJim Slack Bot connected!')
    
    if not os.path.exists('fact_data.json'):
        try:
            with open('fact_data.json','w') as f:
                json.dump({},f)
        except Exception as e:
            print(f"Could not create fact_data.json: {e}")
    
    load_fact_data()
    
    initial_facts=len(get_all_facts())
    print(f"Loaded {initial_facts} facts from database")
    
    if len(api_facts_cache)<10:
        print("Loading additional facts from APIs...")
        try:
            load_more_facts_sync()
            print(f"Now have {len(get_all_facts())} total facts")
        except Exception as e:
            print(f"Error loading facts from APIs: {e}")
    
    # Start the daily fact scheduler in a separate thread
    scheduler_thread = threading.Thread(target=start_scheduler_sync, daemon=True)
    scheduler_thread.start()

if __name__ == "__main__":
    initialize_bot()
    
    # Get port from environment variable for Railway
    port = int(os.environ.get("PORT", 3000))
    
    # Check if we have the required environment variables
    SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
    
    if SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET:
        try:
            # Use HTTP mode for Railway deployment
            app.start(port=port)
        except Exception as error:
            print(f"Unexpected error starting bot: {error}")
    else:
        print("ERROR: SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET environment variables not set!")
        print("Please set your Slack tokens as environment variables")
