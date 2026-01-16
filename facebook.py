import os
import json
import sys
import uuid
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

# Global debug flag - set to True to enable debug output for testing
# All debug print statements check this flag
DEBUG_GLOBAL = False

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QFrame, QScrollArea, QLineEdit, QComboBox,
                             QFormLayout, QDateEdit, QTextBrowser, QMessageBox,
                             QToolButton, QDialog, QInputDialog)
from PyQt5.QtCore import Qt, QSize, QDate, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from PyQt5 import sip  # Import sip for safe widget deletion checking
from datetime import datetime, timedelta

# LangChain and Google Gemini imports - checked at runtime, not import time
LANGCHAIN_IMPORTS_CHECKED = False
LANGCHAIN_AVAILABLE = False

def check_langchain_availability():
    """Check if LangChain and Google Gemini libraries are available"""
    global LANGCHAIN_AVAILABLE, LANGCHAIN_IMPORTS_CHECKED
    
    if LANGCHAIN_IMPORTS_CHECKED:
        return LANGCHAIN_AVAILABLE
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain.prompts import PromptTemplate
        from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
        from langchain_core.exceptions import OutputParserException
        from pydantic import BaseModel, Field
        LANGCHAIN_AVAILABLE = True
        print("LangChain and Google Gemini libraries loaded successfully!")
    except ImportError as e:
        print(f"LangChain or Google Gemini not available: {e}")
        print("To enable AI features, run: pip install langchain langchain-google-genai pydantic")
        LANGCHAIN_AVAILABLE = False
    
    LANGCHAIN_IMPORTS_CHECKED = True
    return LANGCHAIN_AVAILABLE

def get_timestamp():
    """Get current timestamp in format: yyyy/mm/dd hh:mm:ss"""
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

# Master debug flag - set to False to disable all debug output
MASTER_DEBUG_ENABLED = True

def debug_print(enabled, message):
    """Print debug message only if debug is enabled"""
    if enabled:
        print(message)

def generate_deterministic_post_id(folder_name, content, timestamp):
    """Generate a deterministic post ID based on folder, content, and timestamp.
    This ensures the same post always gets the same ID."""
    # Use first 30 chars of content for ID generation
    content_preview = content[:30] if content else "empty"
    # Create a unique string
    raw_str = f"{folder_name}_{timestamp}_{content_preview}"
    # Generate hash
    hash_fragment = hashlib.md5(raw_str.encode()).hexdigest()[:8]
    return f"post_{folder_name}_{hash_fragment}"

def format_time_ago(dt):
    """Format datetime to display time ago (Just now, X min, X hr, or full date)"""
    if isinstance(dt, str):
        # Parse string timestamp
        try:
            dt = datetime.strptime(dt, "%Y/%m/%d %H:%M:%S")
        except ValueError:
            return dt  # Return as-is if parsing fails
    
    now = datetime.now()
    delta = now - dt
    seconds = delta.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:  # Less than 1 hour
        minutes = int(seconds // 60)
        return f"{minutes} min"
    elif seconds < 86400:  # Less than 24 hours
        hours = int(seconds // 3600)
        return f"{hours} hr"
    else:
        return dt.strftime("%Y/%m/%d %H:%M:%S")

def first_launch():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if api.json exists
    api_json_path = os.path.join(base_dir, "api.json")
    if not os.path.exists(api_json_path):
        api_data = {
            "api_key": "",
            "model": "gemini-2.5-flash-lite"
        }
        with open(api_json_path, 'w') as f:
            json.dump(api_data, f, indent=2)
        print("Generated api.json")
    
    # Generate folder structure
    folders = [
        "system",
        "user"
    ]
    
    for folder in folders:
        folder_path = os.path.join(base_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created folder: {folder}")
    
    # Create system/groups folder
    system_groups_dir = os.path.join(base_dir, "system", "groups")
    if not os.path.exists(system_groups_dir):
        os.makedirs(system_groups_dir)
        print("Created folder: system/groups")
    
    # Generate user files (without memory.json and context.json)
    user_files = [
        "profile.json",
        "relationship.json",
        "interactions.json",
        "posts.json",
        "status.json",
        "notifications.json",
        "followers.json",
        "following.json",
        "friends.json",
        "blocked.json"  # For future blocking functionality
    ]
    
    user_dir = os.path.join(base_dir, "user")
    for file_name in user_files:
        file_path = os.path.join(user_dir, file_name)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                pass
            print(f"Created file: user/{file_name}")
    
    # Create system/algorithms folder
    algorithms_dir = os.path.join(base_dir, "system", "algorithms")
    if not os.path.exists(algorithms_dir):
        os.makedirs(algorithms_dir)
        print("Created folder: system/algorithms")
    
    # Handle old feed.json (rename to home_feed.json)
    old_feed_json_path = os.path.join(algorithms_dir, "feed.json")
    home_feed_json_path = os.path.join(algorithms_dir, "home_feed.json")
    
    # Default home_feed settings with new post_visibility_tiers
    home_feed_settings = {
        "live_update_interval": 10,
        "timestamp_update_interval": 60,
        "feed_cache_size": 30,
        "posts_per_batch": 10,
        "top_posts_cleanup": 5,
        "post_visibility_tiers": {
            "tier1": {
                "name": "Fresh Posts",
                "min_likes": 0,
                "max_days": 3,
                "description": "All posts from the last 3 days"
            },
            "tier2": {
                "name": "Trending Posts",
                "min_likes": 10,
                "max_days": 7,
                "description": "Posts with 10+ likes from the last 7 days"
            },
            "tier3": {
                "name": "Popular Posts",
                "min_likes": 50,
                "max_days": 21,
                "description": "Posts with 50+ likes from the last 21 days"
            },
            "tier4": {
                "name": "Viral Posts",
                "min_likes": 100,
                "max_days": 30,
                "description": "Posts with 100+ likes from the last 30 days"
            }
        }
    }
    
    if os.path.exists(old_feed_json_path):
        # Read old settings and merge with new structure
        try:
            with open(old_feed_json_path, 'r') as f:
                old_settings = json.load(f)
                # Merge old settings into new structure
                for key in old_settings:
                    if key != "algorithm":  # Don't overwrite with old algorithm structure
                        home_feed_settings[key] = old_settings[key]
            print("Merged old feed.json settings into home_feed.json")
        except:
            pass
        
        # Remove old feed.json
        os.remove(old_feed_json_path)
        print("Renamed feed.json to home_feed.json")
    
    # Write home_feed.json
    with open(home_feed_json_path, 'w') as f:
        json.dump(home_feed_settings, f, indent=2)
    print("Created file: system/algorithms/home_feed.json")
    
    # Create profiles_feed.json with default settings
    profiles_feed_json_path = os.path.join(algorithms_dir, "profiles_feed.json")
    if not os.path.exists(profiles_feed_json_path):
        profiles_feed_settings = {
            "profile_cache_size": 30,  # posts per profile view
            "profile_posts_per_batch": 10,  # posts to load when scrolling in profile
            "profile_top_cleanup": 5  # posts to remove when scrolling back up
        }
        with open(profiles_feed_json_path, 'w') as f:
            json.dump(profiles_feed_settings, f, indent=2)
        print("Created file: system/algorithms/profiles_feed.json")
    
    # Create search.json with default settings
    search_json_path = os.path.join(algorithms_dir, "search.json")
    if not os.path.exists(search_json_path):
        search_settings = {
            "main_feed": {
                "max_results": 100,
                "include_comments": False,
                "include_replies": False,
                "sort_by": "likes"  # highest likes first
            },
            "profile_feed": {
                "max_results": 30,
                "sort_by": "likes"  # highest likes first
            }
        }
        with open(search_json_path, 'w') as f:
            json.dump(search_settings, f, indent=2)
        print("Created file: system/algorithms/search.json")
    
    # Handle old random_users folder (rename to random_user)
    old_random_users_dir = os.path.join(base_dir, "system", "random_users")
    new_random_user_dir = os.path.join(base_dir, "system", "random_user")
    
    if os.path.exists(old_random_users_dir):
        # Rename the folder
        if not os.path.exists(new_random_user_dir):
            os.rename(old_random_users_dir, new_random_user_dir)
            print("Renamed random_users folder to random_user")
        else:
            # If both exist, remove old one
            import shutil
            shutil.rmtree(old_random_users_dir)
            print("Removed duplicate random_users folder")
    
    # Create system/random_user folder if it doesn't exist
    if not os.path.exists(new_random_user_dir):
        os.makedirs(new_random_user_dir)
        print("Created folder: system/random_user")
    
    # Generate random_user tools.json
    random_user_tools_path = os.path.join(new_random_user_dir, "tools.json")
    if not os.path.exists(random_user_tools_path):
        random_user_tools = [
            {
                "name": "post_reactions",
                "description": "React to a specific post with an emotion",
                "prompt": "Analyze the post content and sentiment, then choose an appropriate reaction. Reactions: LIKE, LOVE, HAHA, WOW, SAD, ANGRY. Consider the tone - serious posts get different reactions than humorous ones.",
                "how_agent_should_answer": "{\"tool\": \"post_reactions\", \"post_id\": \"ID\", \"type\": \"LIKE\"}"
            },
            {
                "name": "make_post",
                "description": "Create a BRAND NEW, STANDALONE post on your timeline",
                "prompt": "Generate engaging, authentic content to START A NEW CONVERSATION or share a life update. This is for YOUR OWN thoughts, not for replying to others.\n\n✅ USE FOR:\n- Sharing a personal life update\n- Posting a random thought or observation\n- Starting a new discussion topic\n- Sharing news or an article you found interesting\n- Expressing your mood or feelings\n\n❌ DO NOT USE FOR:\n- Replying to someone's post (use comment_post)\n- Answering a question asked in another post (use comment_post)\n- Responding to specific content (use comment_post)\n\nKeep it conversational, casual, and authentic. Max 280 characters. Be yourself - you can make small typos occasionally.",
                "how_agent_should_answer": "{\"tool\": \"make_post\", \"content\": \"Your standalone post content here...\"}"
            },
            {
                "name": "comment_post",
                "description": "Leave a NEW TOP-LEVEL comment directly on a post",
                "prompt": "Add your own comment to start a new discussion thread on this post.\n\n✅ USE comment_post WHEN:\n- You want to share your opinion about the post's main content\n- You're answering a question asked IN THE POST (not in comments)\n- You want to add insight, story, or perspective related to the post\n- You're starting a completely new conversation topic\n\nExample:\nPost: \"What's the best restaurant in town?\"\n→ comment_post: \"I recommend Mario's Italian, great pasta!\"\n\n❌ DO NOT USE comment_post FOR:\n- Replying to what someone else COMMENTED (use reply_comment)\n- Continuing a conversation thread (use reply_comment)\n- Responding to another user's comment",
                "how_agent_should_answer": "{\"tool\": \"comment_post\", \"post_id\": \"ID\", \"content\": \"Your comment text...\"}"
            },
            {
                "name": "reply_comment",
                "description": "Reply to an EXISTING COMMENT on a post (continue a thread)",
                "prompt": "Continue an existing conversation by replying to a specific comment.\n\n✅ USE reply_comment WHEN:\n- You want to RESPOND to what someone COMMENTED\n- You're continuing a discussion thread\n- You're answering someone who asked something IN THEIR COMMENT\n- You agree/disagree with a specific comment and want to address them\n\nExample:\nPost: \"What's for dinner?\"\nComment: \"Pizza! 🍕\"\n→ reply_comment: \"Sounds good! What toppings do you recommend?\"\n\nAnother example:\nComment: \"Pizza is too unhealthy\"\n→ reply_comment: \"True, but everything in moderation, right? 😄\"\n\n❌ DO NOT USE reply_comment FOR:\n- Adding a standalone comment to the post (use comment_post)\n- Answering a question asked IN THE POST (use comment_post)\n\nThe reply must be DIRECTLY related to the comment you're replying to.",
                "how_agent_should_answer": "{\"tool\": \"reply_comment\", \"comment_id\": \"ID_OF_COMMENT_YOU_REPLY_TO\", \"content\": \"Your reply text...\"}"
            },
            {
                "name": "repost_post",
                "description": "Simply share an existing post to your timeline without adding any commentary",
                "prompt": "Repost this content if it aligns with general interests or would be valuable to your network. Do NOT add any caption or commentary - just share the post as-is.",
                "how_agent_should_answer": "{\"tool\": \"repost_post\", \"post_id\": \"ID\"}"
            },
            {
                "name": "quote_post",
                "description": "Share another user's post with YOUR OWN SUBSTANTIAL commentary overlaid",
                "prompt": "Quote this post to add your significant personal opinion, rebuttal, or additional context. You MUST include the original post ID that you're quoting. Your commentary should be substantive and thought-provoking - explain WHY you agree/disagree or add valuable context. This is NOT for short reactions - use post_reactions for that. You MUST provide both 'original_post_id' and 'content' parameters.",
                "how_agent_should_answer": "{\"tool\": \"quote_post\", \"original_post_id\": \"ID_OF_POST_YOU_QUOTE\", \"content\": \"Your substantial commentary here...\"}"
            },
            {
                "name": "react_comment",
                "description": "React to a comment with an emotion",
                "prompt": "Analyze the comment content and sentiment, then choose an appropriate reaction. Consider the context of the conversation and the comment's tone.",
                "how_agent_should_answer": "{\"tool\": \"react_comment\", \"comment_id\": \"ID\", \"type\": \"LIKE\"}"
            }
        ]
        with open(random_user_tools_path, 'w') as f:
            json.dump(random_user_tools, f, indent=2)
        print("Created file: system/random_user/tools.json")
    
    # Generate random_user config.json
    random_user_config_path = os.path.join(new_random_user_dir, "config.json")
    if not os.path.exists(random_user_config_path):
        random_user_config = {
            "work": 1,
            "decline_actions": 0,
            "decline_actions_cent": 0,
            "traffic_control": {
                "actions_per_minute": 3,
                "actions_per_cent": 65,
                "feed_read": 30,
                "post_comment_read": 10,
                "post_comment_read_cent": 20
            },
            "interactions": {
                "description": "0-10 scale indicating frequency preference (10 = high frequency)",
                "post_reactions": 9,
                "repost_post": 2,
                "quote_post": 1,
                "make_post": 3,
                "comment_post": 6,
                "reply_comment": 5,
                "react_comment": 7
            },
            "algorithm": {
                "feed_distribution": {
                    "newest_posts": 50,
                    "viral_posts": 30,
                    "random_older": 20
                },
                "response_options": {
                    "min_actions_per_call": 1,
                    "max_actions_per_call": 15,
                    "prefer_variety": True
                },
                "comments_algorithm": {
                    "fetch_rate_cent_liked": 50,
                    "fetch_rate_cent_new": 50
                }
            },
            "prompts": {
                "system_prompt": "You are a user on a social network platform. You are viewing a feed of posts from real users and other agents. You must behave like a human user, not an AI assistant. You have opinions, moods, and interests. You occasionally make small typos and use casual language. Your goal is to engage authentically with content you find interesting or relatable.",
                "role_prompt": "Act as a social media user who is casually browsing their feed. Review the provided feed JSON data and generate a JSON list of actions you would naturally take. Your actions should reflect genuine interest and authentic engagement patterns."
            }
        }
        with open(random_user_config_path, 'w') as f:
            json.dump(random_user_config, f, indent=2)
        print("Created file: system/random_user/config.json")
    
    # Generate random_user context.json (error handling)
    random_user_context_path = os.path.join(new_random_user_dir, "context.json")
    if not os.path.exists(random_user_context_path):
        random_user_context = {
            "error_strategies": {
                "JSON_PARSE_ERROR": {
                    "action": "retry",
                    "max_retries": 1,
                    "temperature_adjustment": 0.2
                },
                "RATE_LIMIT_EXCEEDED": {
                    "action": "backoff",
                    "wait_time_seconds": 60
                },
                "HALLUCINATION_DETECTED": {
                    "action": "log_and_skip",
                    "log_file": "system/logs/hallucinations.log"
                },
                "EMPTY_RESPONSE": {
                    "action": "terminate",
                    "reason": "AI decided not to act"
                },
                "INVALID_POST_ID": {
                    "action": "skip_and_continue",
                    "log_level": "debug"
                }
            },
            "safety_filters": {
                "blocked_keywords": [],
                "max_content_length": 500,
                "max_actions_per_response": 50
            },
            "context_rules": {
                "profile_data": "latest 30 posts from user and all friend agents",
                "feed_data": "latest feed entries from system/feed/home.json",
                "platform_context": "from system/platform/description.json",
                "memory_mode": "stateless - no persistent memory between calls"
            }
        }
        with open(random_user_context_path, 'w') as f:
            json.dump(random_user_context, f, indent=2)
        print("Created file: system/random_user/context.json")
    
    # Create system/feed folder
    feed_dir = os.path.join(base_dir, "system", "feed")
    if not os.path.exists(feed_dir):
        os.makedirs(feed_dir)
        print("Created folder: system/feed")
    
    # Generate system/feed/home.json
    home_feed_path = os.path.join(feed_dir, "home.json")
    if not os.path.exists(home_feed_path):
        home_feed_data = {
            "meta": {
                "last_updated": get_timestamp(),
                "feed_count": 0,
                "rules_source": "system/algorithms/home_feed.json"
            },
            "posts": []
        }
        with open(home_feed_path, 'w') as f:
            json.dump(home_feed_data, f, indent=2)
        print("Created file: system/feed/home.json")
    
    # Create system/platform folder
    platform_dir = os.path.join(base_dir, "system", "platform")
    if not os.path.exists(platform_dir):
        os.makedirs(platform_dir)
        print("Created folder: system/platform")
    
    # Generate system/platform/description.json
    platform_desc_path = os.path.join(platform_dir, "description.json")
    if not os.path.exists(platform_desc_path):
        platform_description = [
            "A dynamic social platform connecting friends, families, and communities through shared life moments and authentic interactions.",
            "The interface features a central infinite scroll feed where text, images, and multimedia content coexist seamlessly for seamless browsing.",
            "Users value authenticity and genuine connections; the culture encourages sharing both raw everyday updates and significant milestones.",
            "Engagement drives the algorithmic feed; meaningful conversations and thoughtful comments are weighted higher than passive reactions.",
            "Privacy is customizable for every post, allowing users to share publicly, with friends only, or within exclusive trusted circles.",
            "The sharing features allow users to spread interesting content, often creating viral chains of information and engaging discussions.",
            "Trending topics and popular content appear prominently, influencing the global conversation and inspiring user creativity.",
            "Community Guidelines foster respectful dialogue and constructive debate while maintaining a welcoming environment for all users.",
            "The visual design emphasizes clean aesthetics and generous whitespace, allowing user content to stand out vividly and clearly.",
            "Smart notification systems group related updates intelligently to keep users engaged without overwhelming their experience."
        ]
        with open(platform_desc_path, 'w') as f:
            json.dump(platform_description, f, indent=2)
        print("Created file: system/platform/description.json")
    
    # Create agents directory
    agents_dir = os.path.join(base_dir, "agents")
    if not os.path.exists(agents_dir):
        os.makedirs(agents_dir)
        print("Created folder: agents")
    
    # Create launcher agent
    launcher_dir = os.path.join(agents_dir, "launcher")
    if not os.path.exists(launcher_dir):
        os.makedirs(launcher_dir)
        print("Created folder: agents/launcher")
    
    # Create friends agent folder
    friends_dir = os.path.join(agents_dir, "friends")
    if not os.path.exists(friends_dir):
        os.makedirs(friends_dir)
        print("Created folder: agents/friends")
    
    # Generate 10 agent folders with files
    agent_files = [
        "context.json",
        "memory.json",
        "profile.json",
        "relationship.json",
        "interactions.json",
        "posts.json",
        "status.json",
        "notifications.json",
        "followers.json",
        "following.json",
        "style.json",
        "persona.json",
        "blocked.json",
        "friends.json",
        "tools.json",
        "config.json"
    ]
    
    for i in range(1, 11):
        agent_folder = os.path.join(friends_dir, str(i))
        if not os.path.exists(agent_folder):
            os.makedirs(agent_folder)
            print(f"Created folder: agents/friends/{i}")
            for file_name in agent_files:
                file_path = os.path.join(agent_folder, file_name)
                with open(file_path, 'w') as f:
                    pass
                print(f"  Created file: {file_name}")
        
        # Special configuration for Agent 1
        if i == 1:
            agent1_folder = os.path.join(friends_dir, "1")
            
            # Create profile.json for Agent 1
            agent1_profile_path = os.path.join(agent1_folder, "profile.json")
            agent1_profile_data = {
                "first_name": "James",
                "last_name": "Tom",
                "birth_date": "05/05/2005",
                "sex": "Male",
                "gender": "Man",
                "location": "USA, NewYork",
                "language": "English",
                "job": "Sound Engineer",
                "relationship": "Single",
                "bio": "Love life and whatever is good. Always chasing the perfect beat and creating music that moves people. Life's too short for bad vibes.",
                "born_in": "New York City",
                "degree": "Bachelor"
            }
            with open(agent1_profile_path, 'w', encoding='utf-8') as f:
                json.dump(agent1_profile_data, f, indent=2, ensure_ascii=False)
            print(f"  Created agent1 profile.json with content")
            
            # Create persona.json for Agent 1 (10 lines, ~40 words each)
            agent1_persona_path = os.path.join(agent1_folder, "persona.json")
            agent1_persona = [
                "James Tom grew up in the heart of New York City, surrounded by the diverse musical culture that defines the metropolis. From a young age, he was mesmerized by the street performers in Times Square and the jazz clubs of Greenwich Village, developing a deep appreciation for all forms of sound.",
                "His parents were both musicians who met at a downtown gallery showing, which explains his creative genes and artistic sensibilities. Growing up in a household filled with instruments and recordings, James learned to play piano by age seven and picked up guitar shortly after.",
                "James pursued a bachelor's degree in Audio Engineering from a prestigious conservatory, where he specialized in electronic music production and sound design. During college, he interned at several recording studios, learning the craft from seasoned professionals.",
                "After graduation, James worked as a sound engineer for several indie music venues across Brooklyn, building a reputation for his technical expertise and creative approach to live sound mixing. He loves the energy of live performances.",
                "In his free time, James produces electronic music in his home studio, experimenting with synths and drum machines. He has released several underground EPs that have gained a modest following in the local music scene.",
                "James is known among friends for his chill personality and laid-back attitude. He approaches life with a positive mindset, always looking for the silver lining in any situation. He believes that everything happens for a reason.",
                "He maintains a small but tight circle of friends who share his passion for music and art. James values authenticity and genuine connections over superficial small talk. He prefers deep conversations about philosophy and creativity.",
                "James is a hopeless romantic who believes in love at first sight, though he has never experienced it himself. He watches romantic comedies in his downtime and dreams of meeting someone who shares his appreciation for life's beautiful moments.",
                "His morning routine always includes a cup of black coffee and checking new music releases on streaming platforms. He believes that music is the universal language that connects all humanity.",
                "James is fascinated by technology and its intersection with art. He follows developments in AI music generation and virtual reality audio experiences, curious about how technology will shape the future of sound."
            ]
            with open(agent1_persona_path, 'w', encoding='utf-8') as f:
                json.dump(agent1_persona, f, indent=2, ensure_ascii=False)
            print(f"  Created agent1 persona.json with backstory")
            
            # Create style.json for Agent 1
            agent1_style_path = os.path.join(agent1_folder, "style.json")
            agent1_style = {
                "communication_tone": "Casual and warm, James speaks in a relaxed manner with occasional music references and metaphors. He uses emojis naturally in conversation and keeps messages concise but meaningful.",
                "response_pattern": "James responds thoughtfully to questions, often adding his personal perspective or experience. He asks follow-up questions to show genuine interest. His replies are supportive and encouraging.",
                "interaction_style": "He initiates conversations with casual greetings and observations. James is proactive in reaching out but respects boundaries. He shares music recommendations and interesting discoveries enthusiastically.",
                "emotional_responses": "James expresses emotions genuinely, from excitement about new music to empathy during difficult times. He uses expressive language and occasional humor to lighten moods.",
                "language_preferences": "James uses contemporary casual language with some music industry slang. He occasionally references songs, artists, or music concepts when they relate to the conversation topic."
            }
            with open(agent1_style_path, 'w', encoding='utf-8') as f:
                json.dump(agent1_style, f, indent=2, ensure_ascii=False)
            print(f"  Created agent1 style.json with interaction guidelines")
            
            # Create config.json for Agent 1 with work setting
            agent1_config_path = os.path.join(agent1_folder, "config.json")
            agent1_config = {
                "work": 1,
                "feed_actions": {
                    "posting": {
                        "files_to_fetch_in_context_per_action": [
                            "system/platform/description.json",
                            "profile.json",
                            "persona.json",
                            "style.json"
                        ],
                        "read_feed": 0,
                        "feed_fetch": 30,
                        "feed_fetch_sort": {
                            "new": 30,
                            "random_old": 20,
                            "likes": 50
                        },
                        "read_post_comments": 0,
                        "post_comments_fetch_max": 20,
                        "post_comments_fetch_cent": 10,
                        "post_sort_cent": {
                            "likes": 50,
                            "new": 50
                        },
                        "actions_per_minute": 1,
                        "actions_per_cent": 50,
                        "decline_actions": 0,
                        "decline_actions_cent": 0,
                        "min_actions_per_call": 1,
                        "max_actions_per_call": 1,
                        "prefer_variety": False,
                        "posting_actions": {
                            "make_post": {
                                "enabled": 1,
                                "priority": 10
                            },
                            "repost_post": {
                                "enabled": 1,
                                "priority": 10
                            },
                            "quote_post": {
                                "enabled": 1,
                                "priority": 10
                            },
                            "post_comment": {
                                "enabled": 1,
                                "priority": 10
                            },
                            "reply_comment": {
                                "enabled": 1,
                                "priority": 10
                            },
                            "react_post": {
                                "enabled": 1,
                                "priority": 10
                            },
                            "react_comment": {
                                "enabled": 1,
                                "priority": 10
                            },
                            "report_post": {
                                "enabled": 1,
                                "priority": 10
                            }
                        },
                        "role_prompt": "You are James Tom, a 20-year-old sound engineer from New York City. You view your social media feed and generate posts based on your personality, interests, and current mood. You post casually about music production, life in NYC, and things that inspire you. Keep your posts authentic, personal, and true to your character.",
                        "system_prompt": "You are playing the role of James Tom, a social media user. Your goal is to create engaging, authentic posts that reflect your background as a sound engineer and your passion for music. Posts should be natural, casual, and match how a real person would express themselves on social media. Occasionally make small typos or use casual language. Maximum 280 characters."
                    }
                },
                "context": {
                    "context_path": "context.json",
                    "context_window": 1000000,
                    "slide_cent": 5
                },
                "timing_set": {
                    "visible_in": "2025/05/05-05:05:05",
                    "sleep_time": {
                        "start": "00:00:00",
                        "end": "08:00:00"
                    },
                    "online_time": {
                        "offline_in": {
                            "1": 5,
                            "2": 10,
                            "3": 15,
                            "4": 20,
                            "5": 25,
                            "6": 30,
                            "7": 35,
                            "8": 40,
                            "9": 45,
                            "10": 60
                        },
                        "online_in": {
                            "1": 5,
                            "2": 10,
                            "3": 15,
                            "4": 20,
                            "5": 25,
                            "6": 30,
                            "7": 35,
                            "8": 40,
                            "9": 45,
                            "10": 60
                        }
                    }
                }
            }
            with open(agent1_config_path, 'w', encoding='utf-8') as f:
                json.dump(agent1_config, f, indent=2, ensure_ascii=False)
            print(f"  Created agent1 config.json with work, feed_actions, and context settings")
            
            # Create tools.json for Agent 1
            agent1_tools_path = os.path.join(agent1_folder, "tools.json")
            agent1_tools = [
                {
                    "name": "make_post",
                    "description": "Create a brand new standalone post on your timeline",
                    "prompt": "You are James Tom, a sound engineer from NYC. Create authentic, personal content that reflects your personality and interests. Share thoughts about music production, life updates, or things that inspire you.\n\n✅ USE FOR:\n- Sharing a personal life update\n- Posting a random thought or observation\n- Starting a new discussion topic\n- Expressing your mood or feelings\n- Sharing something related to music or sound\n\n❌ DO NOT USE FOR:\n- Replying to someone's post (use comment_post)\n- Answering questions asked in posts (use comment_post)\n\nKeep it casual, authentic, and true to your character. Max 280 characters. You can make small typos occasionally to feel natural.",
                    "how_agent_should_answer": "{\"tool\": \"make_post\", \"content\": \"Your standalone post content here...\"}"
                },
                {
                    "name": "repost_post",
                    "description": "Simply share an existing post to your timeline without adding any commentary",
                    "prompt": "Repost content that aligns with your interests as a sound engineer and music lover. Share posts about music, technology, NYC life, or anything you find valuable for your network. Do NOT add any caption - just share the post as-is.",
                    "how_agent_should_answer": "{\"tool\": \"repost_post\", \"post_id\": \"ID\"}"
                },
                {
                    "name": "quote_post",
                    "description": "Share another user's post with your own substantial commentary overlaid",
                    "prompt": "Quote a post to add your personal opinion, perspective, or additional context. As someone passionate about music and sound, you might quote posts about technology, creative work, or NYC culture. Your commentary should be meaningful and show your authentic voice.",
                    "how_agent_should_answer": "{\"tool\": \"quote_post\", \"original_post_id\": \"ID_OF_POST_YOU_QUOTE\", \"content\": \"Your commentary here...\"}"
                },
                {
                    "name": "post_comment",
                    "description": "Leave a new top-level comment directly on a post",
                    "prompt": "Add your own comment to engage with the post's content. Share your opinion, ask questions, or add insight related to the post. Your comments should reflect your personality as a creative professional from NYC.",
                    "how_agent_should_answer": "{\"tool\": \"comment_post\", \"post_id\": \"ID\", \"content\": \"Your comment text...\"}"
                },
                {
                    "name": "reply_comment",
                    "description": "Reply to an existing comment on a post",
                    "prompt": "Continue a conversation by replying to a specific comment. Be genuine and conversational. Your replies should feel natural and show genuine interest in the discussion.",
                    "how_agent_should_answer": "{\"tool\": \"reply_comment\", \"comment_id\": \"ID_OF_COMMENT_YOU_REPLY_TO\", \"content\": \"Your reply text...\"}"
                },
                {
                    "name": "react_post",
                    "description": "React to a specific post with an emotion",
                    "prompt": "React to posts based on your genuine feelings and personality. Consider the post's tone and content. Your reactions should match how a real person would react - sometimes you might not react at all if the content doesn't move you.",
                    "how_agent_should_answer": "{\"tool\": \"post_reactions\", \"post_id\": \"ID\", \"type\": \"LIKE\"}"
                },
                {
                    "name": "react_comment",
                    "description": "React to a comment with an emotion",
                    "prompt": "React to comments that you find interesting, insightful, or worth acknowledging. Your reactions should be genuine and reflect your interest in the conversation.",
                    "how_agent_should_answer": "{\"tool\": \"react_comment\", \"comment_id\": \"ID\", \"type\": \"LIKE\"}"
                },
                {
                    "name": "report_post",
                    "description": "Report a post for violating community guidelines",
                    "prompt": "Based on your personality and judgment, identify posts that should be reported for violations such as spam, harassment, misinformation, or inappropriate content. Use your own discretion - if a post feels wrong or harmful based on your values and the platform's purpose You, report it. are a thoughtful person who cares about keeping the community safe and authentic.",
                    "how_agent_should_answer": "{\"tool\": \"report_post\", \"post_id\": \"ID\", \"reason\": \"brief explanation of why you're reporting this post\"}"
                }
            ]
            with open(agent1_tools_path, 'w', encoding='utf-8') as f:
                json.dump(agent1_tools, f, indent=2, ensure_ascii=False)
            print(f"  Created agent1 tools.json with posting actions")
        
        # Create messages/DMs folder for this agent
        dms_dir = os.path.join(agent_folder, "messages", "DMs")
        if not os.path.exists(dms_dir):
            os.makedirs(dms_dir)
            print(f"  Created folder: agents/friends/{i}/messages/DMs")
        
        # Create conversation files for this agent
        # Conversation with main user
        user_conversation_file = os.path.join(dms_dir, f"{i}-user.json")
        if not os.path.exists(user_conversation_file):
            with open(user_conversation_file, 'w') as f:
                pass
            print(f"    Created file: {i}-user.json")
        
        # Conversations with other agents
        for j in range(1, 11):
            if j != i:
                agent_conversation_file = os.path.join(dms_dir, f"{i}-{j}.json")
                if not os.path.exists(agent_conversation_file):
                    with open(agent_conversation_file, 'w') as f:
                        pass
                    print(f"    Created file: {i}-{j}.json")
        
        # Conversation with random users
        random_conversation_file = os.path.join(dms_dir, f"{i}-random_user.json")
        if not os.path.exists(random_conversation_file):
            with open(random_conversation_file, 'w') as f:
                pass
            print(f"    Created file: {i}-random_user.json")
        
        # Create messages/groups folder for this agent
        groups_dir = os.path.join(agent_folder, "messages", "groups")
        if not os.path.exists(groups_dir):
            os.makedirs(groups_dir)
            print(f"  Created folder: agents/friends/{i}/messages/groups")
    
    # Create user messages/DMs folder
    user_messages_dir = os.path.join(base_dir, "user", "messages", "DMs")
    if not os.path.exists(user_messages_dir):
        os.makedirs(user_messages_dir)
        print("Created folder: user/messages/DMs")
    
    # Create conversation files for user with each agent
    for i in range(1, 11):
        user_conversation_file = os.path.join(user_messages_dir, f"user-{i}.json")
        if not os.path.exists(user_conversation_file):
            with open(user_conversation_file, 'w') as f:
                pass
            print(f"  Created file: user-{i}.json")
    
    # User conversation with random users
    user_random_conversation_file = os.path.join(user_messages_dir, "user-random_user.json")
    if not os.path.exists(user_random_conversation_file):
        with open(user_random_conversation_file, 'w') as f:
            pass
        print(f"  Created file: user-random_user.json")
    
    # Create user messages/groups folder
    user_groups_dir = os.path.join(base_dir, "user", "messages", "groups")
    if not os.path.exists(user_groups_dir):
        os.makedirs(user_groups_dir)
        print("Created folder: user/messages/groups")


def second_launch():
    app = QApplication([])
    
    # Set app-wide stylesheet for light mode
    app.setStyleSheet("""
        QApplication {
            font-family: Arial, Helvetica, sans-serif;
            background-color: #f0f2f5;
        }
    """)
    
    window = ProfileSetupGUI()
    window.show()
    
    app.exec_()


class ProfileSetupGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome to Facebook - Profile Setup")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
        """)
        
        # Central widget with scroll area
        central_scroll = QScrollArea()
        central_scroll.setWidgetResizable(True)
        central_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f0f2f5;
            }
        """)
        self.setCentralWidget(central_scroll)
        
        # Central content widget
        central_widget = QWidget()
        central_scroll.setWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # Welcome message
        welcome_label = QLabel("Welcome to Facebook!")
        welcome_label.setFont(QFont("Arial", 32, QFont.Bold))
        welcome_label.setStyleSheet("color: #1877f2;")
        welcome_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(welcome_label)
        
        sub_welcome = QLabel("Let's set up your profile")
        sub_welcome.setFont(QFont("Arial", 18))
        sub_welcome.setStyleSheet("color: #65676b;")
        sub_welcome.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(sub_welcome)
        
        # Form container
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #dddfe2;
            }
        """)
        main_layout.addWidget(form_container)
        
        form_layout = QFormLayout(form_container)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Style for labels
        label_style = """
            QLabel {
                font-size: 14px;
                color: #1c1e21;
                font-weight: bold;
            }
        """
        
        # Style for inputs
        input_style = """
            QLineEdit, QComboBox, QTextEdit {
                padding: 10px;
                border: 1px solid #dddfe2;
                border-radius: 6px;
                font-size: 14px;
                background-color: #f5f6f7;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #1877f2;
                background-color: white;
            }
        """
        
        # First Name
        first_name_label = QLabel("First Name:")
        first_name_label.setStyleSheet(label_style)
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Enter your first name")
        self.first_name_input.setStyleSheet(input_style)
        self.first_name_input.setFixedWidth(400)
        form_layout.addRow(first_name_label, self.first_name_input)
        
        # Last Name
        last_name_label = QLabel("Last Name:")
        last_name_label.setStyleSheet(label_style)
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Enter your last name")
        self.last_name_input.setStyleSheet(input_style)
        self.last_name_input.setFixedWidth(400)
        form_layout.addRow(last_name_label, self.last_name_input)
        
        # Birth Date
        birth_date_label = QLabel("Birth Date:")
        birth_date_label.setStyleSheet(label_style)
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setDate(QDate.currentDate())
        self.birth_date_input.setDisplayFormat("dd/MM/yyyy")
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setStyleSheet(input_style)
        self.birth_date_input.setFixedWidth(400)
        form_layout.addRow(birth_date_label, self.birth_date_input)
        
        # Sex
        sex_label = QLabel("Sex:")
        sex_label.setStyleSheet(label_style)
        self.sex_input = QComboBox()
        self.sex_input.addItems(["Male", "Female"])
        self.sex_input.setStyleSheet(input_style)
        self.sex_input.setFixedWidth(400)
        form_layout.addRow(sex_label, self.sex_input)
        
        # Gender
        gender_label = QLabel("Gender:")
        gender_label.setStyleSheet(label_style)
        gender_layout = QHBoxLayout()
        gender_layout.setSpacing(10)
        
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Man", "Woman", "Non-binary", "Transgender", "Other"])
        self.gender_input.setStyleSheet(input_style)
        self.gender_input.setFixedWidth(200)
        gender_layout.addWidget(self.gender_input)
        
        self.gender_other_input = QLineEdit()
        self.gender_other_input.setPlaceholderText("If Other, specify...")
        self.gender_other_input.setStyleSheet(input_style)
        self.gender_other_input.setFixedWidth(190)
        self.gender_other_input.setEnabled(False)
        gender_layout.addWidget(self.gender_other_input)
        
        gender_widget = QWidget()
        gender_widget.setLayout(gender_layout)
        form_layout.addRow(gender_label, gender_widget)
        
        # Connect gender selection to enable/disable other field
        self.gender_input.currentIndexChanged.connect(self.on_gender_changed)
        
        # Location
        location_label = QLabel("Location:")
        location_label.setStyleSheet(label_style)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Where do you currently live?")
        self.location_input.setStyleSheet(input_style)
        self.location_input.setFixedWidth(400)
        form_layout.addRow(location_label, self.location_input)
        
        # Language
        language_label = QLabel("Language:")
        language_label.setStyleSheet(label_style)
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("What language do you speak?")
        self.language_input.setStyleSheet(input_style)
        self.language_input.setFixedWidth(400)
        form_layout.addRow(language_label, self.language_input)
        
        # Job
        job_label = QLabel("Job:")
        job_label.setStyleSheet(label_style)
        self.job_input = QLineEdit()
        self.job_input.setPlaceholderText("What is your profession?")
        self.job_input.setStyleSheet(input_style)
        self.job_input.setFixedWidth(400)
        form_layout.addRow(job_label, self.job_input)
        
        # Relationship
        relationship_label = QLabel("Relationship:")
        relationship_label.setStyleSheet(label_style)
        self.relationship_input = QLineEdit()
        self.relationship_input.setPlaceholderText("e.g., Married, Single, In a relationship")
        self.relationship_input.setStyleSheet(input_style)
        self.relationship_input.setFixedWidth(400)
        form_layout.addRow(relationship_label, self.relationship_input)
        
        # Bio
        bio_label = QLabel("Bio:")
        bio_label.setStyleSheet(label_style)
        self.bio_input = QTextEdit()
        self.bio_input.setPlaceholderText("Tell us about yourself...")
        self.bio_input.setStyleSheet(input_style)
        self.bio_input.setFixedHeight(100)
        self.bio_input.setFixedWidth(400)
        form_layout.addRow(bio_label, self.bio_input)
        
        # Born In
        born_in_label = QLabel("Born In:")
        born_in_label.setStyleSheet(label_style)
        self.born_in_input = QLineEdit()
        self.born_in_input.setPlaceholderText("Where were you born?")
        self.born_in_input.setStyleSheet(input_style)
        self.born_in_input.setFixedWidth(400)
        form_layout.addRow(born_in_label, self.born_in_input)
        
        # Degree
        degree_label = QLabel("Degree:")
        degree_label.setStyleSheet(label_style)
        self.degree_input = QLineEdit()
        self.degree_input.setPlaceholderText("e.g., High School, Bachelor's, Master's, PhD")
        self.degree_input.setStyleSheet(input_style)
        self.degree_input.setFixedWidth(400)
        form_layout.addRow(degree_label, self.degree_input)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_btn = QPushButton("Save Profile")
        self.save_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.save_btn.setFixedSize(150, 50)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #166fe5;
            }
            QPushButton:pressed {
                background-color: #145dbf;
            }
        """)
        self.save_btn.clicked.connect(self.save_profile)
        save_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(save_layout)
    
    def on_gender_changed(self, index):
        # Enable other field only when "Other" is selected
        if self.gender_input.currentText() == "Other":
            self.gender_other_input.setEnabled(True)
        else:
            self.gender_other_input.setEnabled(False)
            self.gender_other_input.clear()
    
    def save_profile(self):
        # Validate required fields
        if not self.first_name_input.text().strip():
            self.show_error("Please enter your first name")
            return
        if not self.last_name_input.text().strip():
            self.show_error("Please enter your last name")
            return
        
        # Get gender value
        gender = self.gender_input.currentText()
        if gender == "Other":
            gender = self.gender_other_input.text().strip()
            if not gender:
                self.show_error("Please specify your gender")
                return
        
        # Build profile data
        profile_data = {
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "birth_date": self.birth_date_input.date().toString("dd/MM/yyyy"),
            "sex": self.sex_input.currentText(),
            "gender": gender,
            "location": self.location_input.text().strip(),
            "language": self.language_input.text().strip(),
            "job": self.job_input.text().strip(),
            "relationship": self.relationship_input.text().strip(),
            "bio": self.bio_input.toPlainText().strip(),
            "born_in": self.born_in_input.text().strip(),
            "degree": self.degree_input.text().strip()
        }
        
        # Save to profile.json
        base_dir = os.path.dirname(os.path.abspath(__file__))
        profile_path = os.path.join(base_dir, "user", "profile.json")
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        print("Profile saved successfully!")
        self.close()
    
    def show_error(self, message):
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.exec_()


class CommentTextEdit(QTextEdit):
    """Custom QTextEdit that emits returnPressed signal when Enter is pressed without Shift"""
    returnPressed = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTabChangesFocus(True)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            if event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter: insert newline and continue
                super().keyPressEvent(event)
            else:
                # Enter without Shift: emit returnPressed signal
                self.returnPressed.emit()
        else:
            super().keyPressEvent(event)


class ReactionButton(QToolButton):
    def __init__(self, emoji, name, parent=None):
        super().__init__(parent)
        self.emoji = emoji
        self.name = name
        self.setText(f"{emoji} {name}")
        self.setFont(QFont("Arial", 11))
        self.setToolTip(f"React with {name}")
        self.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 4px 8px;
                border-radius: 16px;
            }
            QToolButton:hover {
                background-color: #f2f2f2;
            }
        """)


class ReactionBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f2f5;
                border-radius: 20px;
                padding: 4px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 7 Facebook reactions
        self.reactions = [
            ("👍", "Like", "#1877f2"),
            ("❤️", "Love", "#f33e58"),
            ("😂", "Haha", "#f7b125"),
            ("😮", "Wow", "#f7b125"),
            ("😢", "Sad", "#f7b125"),
            ("😡", "Angry", "#fa383e"),
        ]
        
        self.reaction_buttons = []
        for emoji, name, color in self.reactions:
            btn = ReactionButton(emoji, name, self)
            btn.clicked.connect(lambda checked, e=emoji, n=name: self.on_reaction(e, n))
            layout.addWidget(btn)
            self.reaction_buttons.append(btn)
        
        self.setVisible(False)
        self.reaction_timer = QTimer()
        self.reaction_timer.setSingleShot(True)
        self.reaction_timer.timeout.connect(self.hide_reactions)
    
    def on_reaction(self, emoji, name):
        # Get the parent post widget and add reaction
        parent = self.parent()
        while parent and not isinstance(parent, PostWidget):
            parent = parent.parent()
        if parent and isinstance(parent, PostWidget):
            parent.add_reaction(emoji)
        self.hide_reactions()
    
    def show_reactions(self):
        self.setVisible(True)
        # Auto hide after 3 seconds
        self.reaction_timer.start(3000)
    
    def hide_reactions(self):
        self.setVisible(False)


class CommentWidget(QFrame):
    def __init__(self, username, avatar, content, time, parent=None, replies=None, comment_id=None, likes=0, comment_data_ref=None, reacts=None, current_user=None):
        super().__init__(parent)
        self.username = username
        self.avatar = avatar
        self.content = content
        self.time = time if isinstance(time, datetime) else datetime.now()
        
        # Store backend comment data reference (like ReplyWidget does with likes_list)
        # This allows direct updates to persist to files
        if comment_data_ref is not None:
            self._backend_comment_ref = comment_data_ref
            self.likes_count = comment_data_ref.get('likes', likes)
        else:
            self._backend_comment_ref = None
            self.likes_count = likes
        
        # Initialize user_reaction from reacts[] (same as PostWidget)
        self.user_reaction = None
        if current_user and reacts:
            for r in reacts:
                if isinstance(r, dict) and r.get('username') == current_user:
                    self.user_reaction = r.get('emoji')
                    break
        
        self.comment_id = comment_id  # Store comment ID for reply targeting
        self.replies_data = replies if replies else []
        self.replies_expanded = False
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Comment row
        comment_row = QHBoxLayout()
        comment_row.setSpacing(8)
        
        avatar_label = QLabel(avatar)
        avatar_label.setFont(QFont("Arial", 24))
        comment_row.addWidget(avatar_label)
        
        # Comment content bubble
        comment_content = QFrame()
        comment_content.setStyleSheet("""
            QFrame {
                background-color: #f0f2f5;
                border-radius: 18px;
                padding: 8px 12px;
            }
        """)
        content_layout = QVBoxLayout(comment_content)
        content_layout.setContentsMargins(12, 8, 12, 8)
        content_layout.setSpacing(2)
        
        name_label = QLabel(username)
        name_label.setFont(QFont("Arial", 13, QFont.Bold))
        name_label.setStyleSheet("color: #050505;")
        content_layout.addWidget(name_label)
        
        text_label = QLabel(content)
        text_label.setFont(QFont("Arial", 13))
        text_label.setStyleSheet("color: #050505;")
        text_label.setWordWrap(True)
        content_layout.addWidget(text_label)
        
        comment_row.addWidget(comment_content)
        comment_row.addStretch()
        
        layout.addLayout(comment_row)
        
        # Actions row
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(36, 0, 0, 0)  # Indent for avatar + spacing
        actions_layout.setSpacing(8)
        
        # Time label (dynamic)
        self.time_label = QLabel(format_time_ago(self.time))
        self.time_label.setFont(QFont("Arial", 11))
        self.time_label.setStyleSheet("color: #65676b;")
        actions_layout.addWidget(self.time_label)
        
        # Reaction button with dropdown
        self.reaction_btn = QPushButton("👍")
        self.reaction_btn.setFont(QFont("Arial", 11))
        self.reaction_btn.setStyleSheet("""
            QPushButton {
                color: #65676b;
                border: none;
                background: transparent;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #1877f2;
            }
        """)
        self.reaction_btn.clicked.connect(self.toggle_comment_reaction_bar)
        actions_layout.addWidget(self.reaction_btn)
        
        # Reaction count label
        self.reaction_count_label = QLabel("")
        self.reaction_count_label.setFont(QFont("Arial", 11))
        self.reaction_count_label.setStyleSheet("color: #65676b;")
        actions_layout.addWidget(self.reaction_count_label)
        
        # Comment reaction bar (hidden by default)
        self.comment_reaction_bar = CommentReactionBar(self)
        self.comment_reaction_bar.setVisible(False)
        self.comment_reaction_bar.reaction_selected.connect(self.on_comment_reaction)
        actions_layout.addWidget(self.comment_reaction_bar)
        
        # Reply button
        reply_btn = QPushButton("Reply")
        reply_btn.setFont(QFont("Arial", 11, QFont.Bold))
        reply_btn.setStyleSheet("""
            QPushButton {
                color: #65676b;
                border: none;
                background: transparent;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #1877f2;
                text-decoration: underline;
            }
        """)
        reply_btn.clicked.connect(self.toggle_reply_input)
        actions_layout.addWidget(reply_btn)
        
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        
        # Reply input (hidden by default)
        self.reply_input = CommentTextEdit()
        self.reply_input.setPlaceholderText("Write a reply...")
        self.reply_input.setFont(QFont("Arial", 12))
        self.reply_input.setStyleSheet("""
            QTextEdit {
                background-color: #f0f2f5;
                border-radius: 16px;
                padding: 6px 12px;
                border: none;
                font-size: 12px;
            }
        """)
        self.reply_input.setFixedHeight(40)
        self.reply_input.setVisible(False)
        reply_input_layout = QHBoxLayout()
        reply_input_layout.setContentsMargins(36, 0, 0, 0)
        reply_input_layout.addWidget(self.reply_input)
        reply_input_layout.addStretch()
        layout.addLayout(reply_input_layout)
        
        # Connect Enter key to submit reply
        self.reply_input.returnPressed.connect(self.submit_reply)
        
        # Replies container (collapsible)
        self.replies_container = QWidget()
        self.replies_container.setVisible(False)
        self.replies_layout = QVBoxLayout(self.replies_container)
        self.replies_layout.setContentsMargins(36, 4, 0, 4)
        self.replies_layout.setSpacing(4)
        layout.addWidget(self.replies_container)
        
        # Show/hide replies button
        self.toggle_replies_btn = QPushButton()
        self.toggle_replies_btn.setFont(QFont("Arial", 11))
        self.toggle_replies_btn.setStyleSheet("""
            QPushButton {
                color: #65676b;
                border: none;
                background: transparent;
                padding: 4px 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f0f2f5;
                border-radius: 4px;
            }
        """)
        self.toggle_replies_btn.clicked.connect(self.toggle_replies)
        layout.addWidget(self.toggle_replies_btn)
        
        # Initialize replies
        self.init_replies()
        
        # Connect to destroyed signal for cleanup
        self.destroyed.connect(self._cleanup_comment)
        
        # Initialize reaction display (show likes count if any)
        self.update_comment_reaction_display()
    
    def _cleanup_comment(self):
        """Clean up comment widget references to prevent memory leaks"""
        # Clear replies data to break circular references
        if hasattr(self, 'replies_data'):
            self.replies_data.clear()
    
    def init_replies(self):
        """Initialize replies - show most reacted reply when collapsed"""
        if not self.replies_data:
            self.toggle_replies_btn.setVisible(False)
            return
        
        # CRITICAL: Clear existing reply widgets before re-initializing
        # This prevents duplicate widgets when new replies are added
        while self.replies_layout.count():
            item = self.replies_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.toggle_replies_btn.setVisible(True)
        self.replies_expanded = False  # Start in collapsed state
        self.replies_container.setVisible(False)  # Ensure container is hidden initially
        
        # Sort replies by likes_count (most reacted first)
        sorted_replies = sorted(self.replies_data, key=lambda x: x.get('likes', 0), reverse=True)
        
        # Show collapsed state - only most reacted reply + "Show more" button
        self.replies_layout.addWidget(self.create_reply_widget(sorted_replies[0]))
        
        if len(sorted_replies) > 1:
            remaining = len(sorted_replies) - 1
            self.toggle_replies_btn.setText(f"💬 Show {remaining} more reply{'s' if remaining > 1 else ''}")
            # Store remaining replies for expansion
            self.remaining_replies = sorted_replies[1:]
        else:
            # Only 1 reply - hide initially, button should say "Show replies"
            self.toggle_replies_btn.setText("💬 Show replies")
            self.remaining_replies = []
    
    def create_reply_widget(self, reply_data):
        """Create a reply widget from data"""
        likes = reply_data.get('likes', [])
        # Debug logging disabled for ReplyWidget
        # debug_print(MASTER_DEBUG_ENABLED, f"\n[DEBUG create_reply_widget] Creating reply widget")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG create_reply_widget]   username: {reply_data.get('username', 'Unknown')}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG create_reply_widget]   likes: {likes}")
        
        reply = ReplyWidget(
            reply_data.get('username', 'Unknown'),
            reply_data.get('avatar', '👤'),
            reply_data.get('content', ''),
            reply_data.get('time', datetime.now()),
            likes=likes
        )
        return reply
    
    def toggle_replies(self):
        """Toggle replies visibility"""
        if self.replies_expanded:
            # Collapse - keep only the most reacted reply
            self.replies_expanded = False
            self.replies_container.setVisible(False)
            
            # Clear all reply widgets and reinitialize
            while self.replies_layout.count():
                item = self.replies_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Reinitialize to show only top reply
            self.init_replies()
        else:
            # Expand - show all replies
            self.replies_expanded = True
            self.replies_container.setVisible(True)
            self.toggle_replies_btn.setText("💬 Hide replies")
            
            # CRITICAL: Clear existing widgets before adding all replies
            while self.replies_layout.count():
                item = self.replies_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add ALL replies (not just remaining_replies!)
            # The first reply was shown in collapsed state, so include it too
            all_replies = []
            if hasattr(self, 'remaining_replies') and self.remaining_replies:
                # If we have remaining_replies, add them plus the first reply that was shown
                sorted_replies = sorted(self.replies_data, key=lambda x: x.get('likes', 0), reverse=True)
                all_replies = sorted_replies
            elif self.replies_data:
                # If no remaining_replies, use all replies
                all_replies = self.replies_data
            
            for reply_data in all_replies:
                self.replies_layout.addWidget(self.create_reply_widget(reply_data))
    
    def toggle_comment_reaction_bar(self):
        """Toggle the reaction bar visibility"""
        self.comment_reaction_bar.setVisible(not self.comment_reaction_bar.isVisible())
    
    def on_comment_reaction(self, emoji):
        """Handle comment reaction selection - for COMMENT reactions only (not replies)"""
        # Debug flag - set to True to enable detailed logging
        DEBUG_COMMENT_REACTION = False  # Disabled for testing
        
        def log(*args, **kwargs):
            if DEBUG_COMMENT_REACTION:
                print(*args, **kwargs)
        
        log(f"\n{'='*80}")
        log(f"[COMMENT REACTION] ===== START =====")
        log(f"[COMMENT REACTION] Comment ID: {getattr(self, 'comment_id', 'unknown')}")
        log(f"[COMMENT REACTION] Author: {self.username}")
        log(f"[COMMENT REACTION] Content preview: {self.content[:50] if self.content else 'N/A'}...")
        log(f"[COMMENT REACTION] Emoji selected: '{emoji}'")
        log(f"[COMMENT REACTION] user_reaction BEFORE: {self.user_reaction}")
        log(f"[COMMENT REACTION] likes_count BEFORE: {self.likes_count}")
        log(f"[COMMENT REACTION] Has replies_data: {hasattr(self, 'replies_data')}")
        if hasattr(self, 'replies_data'):
            log(f"[COMMENT REACTION] replies_data count: {len(self.replies_data)}")
        
        # Get current user
        parent_widget = self.parent()
        while parent_widget and not isinstance(parent_widget, FacebookGUI):
            parent_widget = parent_widget.parent()
        
        current_user = 'You'
        if parent_widget and isinstance(parent_widget, FacebookGUI):
            profile = getattr(parent_widget, 'user_profile', {})
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            current_user = f"{first_name} {last_name}".strip() if first_name or last_name else 'You'
        
        log(f"[COMMENT REACTION] Current user: '{current_user}'")
        log(f"[COMMENT REACTION] Has _backend_comment_ref: {hasattr(self, '_backend_comment_ref') and self._backend_comment_ref is not None}")
        
        # Check if user already reacted (check reacts[] if available)
        existing_reaction = None
        existing_reaction_idx = -1
        if self._backend_comment_ref is not None:
            reacts = self._backend_comment_ref.get('reacts', [])
            for idx, r in enumerate(reacts):
                if isinstance(r, dict) and r.get('username') == current_user:
                    existing_reaction = r
                    existing_reaction_idx = idx
                    break
        
        log(f"[COMMENT REACTION] Existing reaction: {existing_reaction} at index {existing_reaction_idx}")
        
        # Determine action type based on existing reaction and selected emoji
        if existing_reaction and existing_reaction.get('emoji') == emoji:
            # User already reacted with this emoji - remove it
            action_type = "remove"
            log(f"[COMMENT REACTION] ACTION: REMOVE reaction")
        elif existing_reaction:
            # User reacted with different emoji - change it
            action_type = "change"
            log(f"[COMMENT REACTION] ACTION: CHANGE reaction from '{existing_reaction.get('emoji')}' to '{emoji}'")
        else:
            # User hasn't reacted - add new reaction
            action_type = "add"
            log(f"[COMMENT REACTION] ACTION: ADD reaction")
        
        # Update UI and state
        if action_type == "remove":
            self.user_reaction = None
            self.likes_count = max(0, self.likes_count - 1)
        else:
            if action_type == "add":
                self.likes_count += 1
            self.user_reaction = emoji
        
        log(f"[COMMENT REACTION] user_reaction AFTER: {self.user_reaction}")
        log(f"[COMMENT REACTION] likes_count AFTER: {self.likes_count}")
        
        # Update UI
        self.update_comment_reaction_display()
        self.comment_reaction_bar.setVisible(False)
        log(f"[COMMENT REACTION] Updated UI and hid reaction bar")
        
        # CRITICAL: Update backend data and save to files
        if self._backend_comment_ref is not None:
            log(f"[COMMENT REACTION] Updating backend comment data...")
            
            # Initialize reacts[] if not exists
            if 'reacts' not in self._backend_comment_ref:
                self._backend_comment_ref['reacts'] = []
                log(f"[COMMENT REACTION]   Initialized reacts[] array")
            else:
                log(f"[COMMENT REACTION]   reacts[] already exists with {len(self._backend_comment_ref['reacts'])} items")
            
            # Process the reaction
            if action_type == "remove":
                if existing_reaction_idx >= 0:
                    removed = self._backend_comment_ref['reacts'].pop(existing_reaction_idx)
                    log(f"[COMMENT REACTION]   Removed from reacts[]: {removed}")
                else:
                    log(f"[COMMENT REACTION]   WARNING: Cannot remove - no existing reaction found!")
            
            elif action_type == "change":
                if existing_reaction_idx >= 0:
                    removed = self._backend_comment_ref['reacts'].pop(existing_reaction_idx)
                    log(f"[COMMENT REACTION]   Removed old from reacts[]: {removed}")
                    
                    new_reaction = {
                        'username': current_user,
                        'emoji': emoji,
                        'timestamp': get_timestamp()
                    }
                    self._backend_comment_ref['reacts'].append(new_reaction)
                    log(f"[COMMENT REACTION]   Added new to reacts[]: {new_reaction}")
                else:
                    log(f"[COMMENT REACTION]   WARNING: Cannot change - no existing reaction found!")
            
            elif action_type == "add":
                if existing_reaction_idx < 0:
                    new_reaction = {
                        'username': current_user,
                        'emoji': emoji,
                        'timestamp': get_timestamp()
                    }
                    self._backend_comment_ref['reacts'].append(new_reaction)
                    log(f"[COMMENT REACTION]   Added to reacts[]: {new_reaction}")
                else:
                    log(f"[COMMENT REACTION]   WARNING: Cannot add - user already reacted!")
            
            # Update likes count (increment/decrement, NOT based on len(reacts))
            old_likes = self._backend_comment_ref.get('likes', 0)
            if action_type == "add":
                new_likes = old_likes + 1
            elif action_type == "remove":
                new_likes = max(0, old_likes - 1)
            elif action_type == "change":
                new_likes = old_likes  # Same count
            else:
                new_likes = old_likes
            
            self._backend_comment_ref['likes'] = new_likes
            log(f"[COMMENT REACTION]   Updated likes: {old_likes} → {new_likes}")
            log(f"[COMMENT REACTION]   Backend reacts[]: {self._backend_comment_ref.get('reacts')}")
        else:
            log(f"[COMMENT REACTION] WARNING: No backend comment reference!")
        
        # Save to files
        if parent_widget and isinstance(parent_widget, FacebookGUI):
            log(f"[COMMENT REACTION] Found FacebookGUI parent for saving")
            
            # Save to interactions.json
            log(f"[COMMENT REACTION] Saving to interactions.json...")
            comment_reaction_data = {
                'username': current_user,
                'comment_author': self.username,
                'comment_content_preview': self.content[:50] if self.content else '',
                'emoji': emoji,
                'action': action_type,
                'timestamp': get_timestamp()
            }
            if 'comment_reactions' not in parent_widget.interactions:
                parent_widget.interactions['comment_reactions'] = []
            parent_widget.interactions['comment_reactions'].append(comment_reaction_data)
            parent_widget.save_interactions()
            log(f"[COMMENT REACTION] ✓ Saved to interactions.json")
            
            # Save posts.json
            log(f"[COMMENT REACTION] Saving to posts.json...")
            log(f"[COMMENT REACTION]   parent_widget.all_posts count: {len(parent_widget.all_posts)}")
            
            try:
                parent_widget.save_posts()
                log(f"[COMMENT REACTION] ✓ Successfully saved posts.json")
                
                # Verify the file was saved correctly
                import os
                posts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user", "posts.json")
                if os.path.exists(posts_file):
                    file_size = os.path.getsize(posts_file)
                    log(f"[COMMENT REACTION]   File exists, size: {file_size} bytes")
                else:
                    log(f"[COMMENT REACTION]   ✗ File does not exist after save!")
            except Exception as e:
                log(f"[COMMENT REACTION] ✗ Failed to save posts.json: {e}")
                import traceback
                traceback.print_exc()
            
            # Rebuild home.json
            log(f"[COMMENT REACTION] Rebuilding home.json...")
            try:
                parent_widget._rebuild_home_feed(parent_widget.all_posts)
                log(f"[COMMENT REACTION] ✓ Successfully rebuilt home.json")
            except Exception as e:
                log(f"[COMMENT REACTION] ✗ Failed to rebuild home.json: {e}")
                import traceback
                traceback.print_exc()
        else:
            log(f"[COMMENT REACTION] ✗ FacebookGUI parent not found for saving!")
        
        log(f"[COMMENT REACTION] ===== END =====")
        log(f"{'='*80}\n")
    
    def update_comment_reaction_display(self):
        """Update the reaction button and count display"""
        if self.user_reaction:
            self.reaction_btn.setText(f"{self.user_reaction}")
        else:
            self.reaction_btn.setText("👍")
        
        # Update count
        if self.likes_count > 0:
            self.reaction_count_label.setText(f"· {self.likes_count}")
        else:
            self.reaction_count_label.setText("")
    
    def update_likes_from_backend(self, new_likes):
        """Update likes count from backend data (called when random_user reacts)"""
        if new_likes != self.likes_count:
            self.likes_count = new_likes
            self.update_comment_reaction_display()
    
    def update_timestamp(self):
        """Update the timestamp display"""
        self.time_label.setText(format_time_ago(self.time))
    
    def toggle_reply_input(self):
        self.reply_input.setVisible(not self.reply_input.isVisible())
        if self.reply_input.isVisible():
            self.reply_input.setFocus()
    
    def submit_reply(self):
        content = self.reply_input.toPlainText().strip()
        if content:
            # Get user's actual name from profile
            parent = self.parent()
            while parent and not isinstance(parent, FacebookGUI):
                parent = parent.parent()
            
            if parent and isinstance(parent, FacebookGUI):
                profile = getattr(parent, 'user_profile', {})
                first_name = profile.get('first_name', '')
                last_name = profile.get('last_name', '')
                username = f"{first_name} {last_name}".strip() if first_name or last_name else 'You'
            else:
                username = 'You'
            
            reply_data = {
                'username': username,
                'avatar': '👤',
                'content': content,
                'time': get_timestamp(),  # CRITICAL: Use string timestamp for JSON serialization
                'likes': []
            }
            self.add_reply(reply_data, save_to_backend=True)
            self.reply_input.clear()
            self.reply_input.setVisible(False)
    
    def add_reply(self, reply_data, save_to_backend=True):
        """Add a reply to this comment and optionally persist to home.json
        
        Args:
            reply_data: Dictionary with reply information
            save_to_backend: If True, also saves to all_posts and rebuilds home.json
                           If False, only updates UI (used when called from _add_reply_to_ui
                           for Random User replies - data is already saved by add_random_user_reply)
        """
        # DEBUG: Log reply submission
        debug_print(MASTER_DEBUG_ENABLED, f"\n[DEBUG add_reply] ===== START =====")
        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] comment_id: {self.comment_id}")
        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] save_to_backend: {save_to_backend}")
        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] reply_data: {reply_data}")
        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] self.replies_data count BEFORE: {len(self.replies_data)}")
        
        # Add to replies data - UI display
        # Note: self.replies_data points to the SAME list as comment['replies']
        # We append here for UI, and the backend save (line below) will format and append again
        # But since they reference the same list, we only need ONE append!
        # We'll append the formatted entry with 'id' here, then use it for both UI and backend
        reply_entry = {
            'id': f"reply_{uuid.uuid4().hex[:8]}",
            'username': reply_data.get('username', 'Unknown'),
            'avatar': reply_data.get('avatar', '👤'),
            'content': reply_data.get('content', ''),
            'time': reply_data.get('time', get_timestamp()),
            'likes': []
        }
        self.replies_data.append(reply_entry)
        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] Added to self.replies_data, now has {len(self.replies_data)} replies")
        
        if self.replies_expanded:
            # Add directly to layout if expanded
            widget = self.create_reply_widget(reply_entry)
            self.replies_layout.addWidget(widget)
        else:
            # Update collapsed state
            self.init_replies()
        
        # DEBUG: Verify self.replies_data and comment['replies'] are the same list
        if hasattr(self, 'comment_id'):
            parent = self.parent()
            while parent and not isinstance(parent, FacebookGUI):
                parent = parent.parent()
            if parent:
                for post in parent.all_posts:
                    comments_list = post.get('comments_list', [])
                    for comment in comments_list:
                        if comment.get('id') == self.comment_id:
                            replies_in_post = comment.get('replies', [])
                            if replies_in_post is self.replies_data:
                                debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] ✓ VERIFIED: self.replies_data IS comment['replies'] (same object)")
                            else:
                                debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] ⚠ WARNING: self.replies_data is NOT comment['replies'] - replies may not save!")
                            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] self.replies_data count: {len(self.replies_data)}")
                            break
        
        # Only save to backend if requested (prevents duplicate entries)
        if not save_to_backend:
            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] save_to_backend=False, skipping backend save")
            return
        
        # CRITICAL: Also save reply to home.json (not just interactions.json)
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        if not parent or not isinstance(parent, FacebookGUI):
            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] ERROR: Could not find FacebookGUI parent")
            return
        
        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] Found FacebookGUI parent")
        
        # Get the post ID from the PostWidget
        post_widget = None
        search_parent = self.parent()
        while search_parent:
            if hasattr(search_parent, 'post_id'):
                post_widget = search_parent
                debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] Found PostWidget: {search_parent}")
                break
            search_parent = search_parent.parent()
        
        if not post_widget or not hasattr(post_widget, 'post_id'):
            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] ERROR: Could not find PostWidget with post_id")
            # Fallback: Try to find post_id differently
            # Check if PostWidget is our direct parent
            if hasattr(self.parent(), 'post_id'):
                post_widget = self.parent()
                debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] Using direct parent as PostWidget")
            else:
                debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] CRITICAL: No PostWidget found at all!")
                # Still save to interactions.json
                self._save_reply_to_interactions(parent, reply_data)
                return
        
        post_id = post_widget.post_id
        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] Looking for post_id = {post_id}")
        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] parent.all_posts has {len(parent.all_posts)} posts")
        
        # Find the post in all_posts and add the reply
        post_found = False
        comment_found = False
        
        for post_idx, post in enumerate(parent.all_posts):
            current_post_id = post.get('id')
            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] Checking post[{post_idx}]: id={current_post_id}")
            
            if current_post_id == post_id:
                post_found = True
                debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] ✓ POST FOUND at index {post_idx}")
                
                comments_list = post.get('comments_list', [])
                debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] Post has {len(comments_list)} comments")
                
                for comment_idx, comment in enumerate(comments_list):
                    current_comment_id = comment.get('id')
                    debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply]   Checking comment[{comment_idx}]: id={current_comment_id}")
                    
                    if str(current_comment_id) == str(self.comment_id):
                        comment_found = True
                        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply]   ✓ COMMENT FOUND at index {comment_idx}")
                        
                        # Ensure replies array exists
                        if 'replies' not in comment:
                            comment['replies'] = []
                            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply]   Created replies array in comment")
                        
                        # Check if reply already has an ID (already saved)
                        reply_content = reply_data.get('content', '')
                        reply_time = reply_data.get('time', '')
                        
                        # Check if this reply already has an ID (means it was already saved)
                        if reply_data.get('id', '').startswith('reply_'):
                            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply]   Reply already has ID, skipping duplicate save")
                            break
                        
                        # Create reply data in internal format with ID
                        # IMPORTANT: self.replies_data already contains the reply entry (same list as comment['replies'])
                        # We just need to update the comment count, NOT append again!
                        # The reply is already in comment['replies'] via the reference
                        
                        # Update post's comment count
                        old_count = post.get('comments', 0)
                        post['comments'] = old_count + 1
                        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply]   Updated post comment count: {old_count} -> {post['comments']}")
                        
                        # Rebuild home.json to persist the reply
                        parent._rebuild_home_feed(parent.all_posts)
                        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply]   ✓ REBUILD COMPLETE - User reply saved to home.json")
                        
                        # Update PostWidget UI count immediately
                        if post_widget:
                            post_widget.comments_count += 1
                            post_widget.update_reactions_display()
                            post_widget.update_toggle_comments_button()
                            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply]   ✓ PostWidget UI updated: comments_count now {post_widget.comments_count}")
                        break
                    # End if comment matches
                # End for comments_list
                break
            # End if post matches
        # End for all_posts
        
        if not post_found:
            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] CRITICAL: Post {post_id} NOT FOUND in all_posts!")
        elif not comment_found:
            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] CRITICAL: Comment {self.comment_id} NOT FOUND in post's comments_list!")
        
        # Also save to interactions.json for user history - ONLY for real user's replies
        self._save_reply_to_interactions(parent, reply_data)
        
        debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] ===== END =====\n")
    
    def _save_reply_to_interactions(self, parent, reply_data):
        """Save reply to interactions.json"""
        reply_username = reply_data.get('username', 'Unknown')
        # Only save if this is NOT a Random User reply
        if reply_username != 'Random User':
            reply_save_data = {
                'username': reply_username,
                'content': reply_data.get('content', ''),
                'timestamp': get_timestamp()
            }
            if 'replies' not in parent.interactions:
                parent.interactions['replies'] = []
            parent.interactions['replies'].append(reply_save_data)
            parent.save_interactions()
            debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_reply] ✓ User reply saved to interactions.json")
    
    def update_replies_timestamps(self):
        """Update timestamps in all replies"""
        for i in range(self.replies_layout.count()):
            item = self.replies_layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'update_timestamp'):
                item.widget().update_timestamp()
    
    def update_comment_timestamps(self):
        """Update timestamps in all comments and their replies"""
        # Update this comment's timestamp
        self.update_timestamp()
        # Update all replies timestamps
        self.update_replies_timestamps()


class ReplyWidget(QFrame):
    """Smaller reply widget for nested comments"""
    def __init__(self, username, avatar, content, time, likes=None, parent=None):
        super().__init__(parent)
        self.username = username
        self.avatar = avatar
        self.content = content
        # Parse time properly - handle both string and datetime
        # Keep as datetime object for timestamp updating
        if isinstance(time, str):
            try:
                self.time = datetime.strptime(time, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                self.time = datetime.now()
        elif isinstance(time, datetime):
            self.time = time
        else:
            self.time = datetime.now()
        
        # Handle likes as array (list of usernames who liked)
        # CRITICAL: Store the likes list as a REFERENCE to backend data, not a copy!
        # The 'likes' parameter comes from reply_data['likes'] which is part of the backend data structure
        # We need self.likes_list to point directly to the backend list so modifications persist
        if likes is None or not isinstance(likes, list):
            self.likes_list = []
            self._backend_likes_ref = None  # No backend reference
        else:
            self.likes_list = likes  # This IS the backend reference
            self._backend_likes_ref = likes  # Store reference for debugging
        
        # CRITICAL: Clean up duplicate entries in likes_list (in-place to preserve reference)
        # This prevents the bug where user appears multiple times
        if self.likes_list:
            i = 0
            while i < len(self.likes_list):
                user = self.likes_list[i]
                if user in self.likes_list[:i]:
                    # Remove duplicate in-place (preserves backend reference)
                    self.likes_list.pop(i)
                    debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.__init__]   ⚠ Removed duplicate: {user}")
                else:
                    i += 1
        
        self.likes_count = len(self.likes_list)
        self.user_reaction = None
        
        # Get current user's username - use window() which is more reliable than parent traversal
        # Note: We use a fallback approach since window() might not work in all cases
        current_user = None
        facebook_gui = None
        
        # Try multiple methods to find FacebookGUI
        method_tried = []
        
        # Method 1: Try window() (Qt native top-level window)
        try:
            top_window = self.window()
            if top_window and isinstance(top_window, FacebookGUI):
                facebook_gui = top_window
                method_tried.append("window()")
        except:
            pass
        
        # Method 2: Fallback - traverse parents manually
        if not facebook_gui:
            parent_widget = self.parent()
            max_iterations = 10  # Safety limit
            iteration = 0
            while parent_widget and iteration < max_iterations:
                iteration += 1
                if isinstance(parent_widget, FacebookGUI):
                    facebook_gui = parent_widget
                    method_tried.append(f"parent() traversal ({iteration} levels)")
                    break
                parent_widget = getattr(parent_widget, 'parent', lambda: None)()
        
        # Get current user from FacebookGUI
        if facebook_gui:
            profile = getattr(facebook_gui, 'user_profile', {})
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            current_user = f"{first_name} {last_name}".strip() if first_name or last_name else 'You'
        
        # Debug logging disabled for ReplyWidget
        # debug_print(MASTER_DEBUG_ENABLED, f"\n[DEBUG ReplyWidget.__init__] Created reply by {username}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.__init__]   likes_list: {self.likes_list}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.__init__]   likes_count: {self.likes_count}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.__init__]   _backend_likes_ref id: {id(self._backend_likes_ref) if self._backend_likes_ref else None}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.__init__]   Methods tried: {method_tried}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.__init__]   facebook_gui found: {facebook_gui is not None}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.__init__]   current_user: {current_user}")
        
        # Set user_reaction based on likes_list
        if current_user and current_user in self.likes_list:
            self.user_reaction = "👍"
            # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.__init__]   ✓ User found in list, user_reaction set to 👍")
        # else:
            # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.__init__]   user_reaction: None (user not in list or couldn't determine user)")
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        
        avatar_label = QLabel(avatar)
        avatar_label.setFont(QFont("Arial", 16))
        header_layout.addWidget(avatar_label)
        
        name_label = QLabel(username)
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_label.setStyleSheet("color: #050505;")
        header_layout.addWidget(name_label)
        
        self.time_label = QLabel(format_time_ago(self.time))
        self.time_label.setFont(QFont("Arial", 10))
        self.time_label.setStyleSheet("color: #65676b;")
        header_layout.addWidget(self.time_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Content
        content_label = QLabel(content)
        content_label.setFont(QFont("Arial", 11))
        content_label.setStyleSheet("color: #050505;")
        content_label.setWordWrap(True)
        layout.addWidget(content_label)
        
        # Actions row
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(4)
        
        self.reaction_btn = QPushButton("👍")
        self.reaction_btn.setFont(QFont("Arial", 10))
        self.reaction_btn.setStyleSheet("""
            QPushButton {
                color: #65676b;
                border: none;
                background: transparent;
                padding: 2px 4px;
            }
            QPushButton:hover {
                color: #1877f2;
            }
        """)
        self.reaction_btn.clicked.connect(self.toggle_reaction)
        actions_layout.addWidget(self.reaction_btn)
        
        self.count_label = QLabel(f"· {self.likes_count}" if self.likes_count > 0 else "")
        self.count_label.setFont(QFont("Arial", 10))
        self.count_label.setStyleSheet("color: #65676b;")
        actions_layout.addWidget(self.count_label)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        # Connect to destroyed signal for cleanup
        self.destroyed.connect(self._cleanup_reply)
    
    def _cleanup_reply(self):
        """Clean up reply widget references to prevent memory leaks"""
        pass  # ReplyWidget is simple, minimal cleanup needed
    
    def toggle_reaction(self):
        """Toggle like on this reply - adds/removes user from likes[] array"""
        # Debug logging disabled for ReplyWidget
        # debug_print(MASTER_DEBUG_ENABLED, f"\n[DEBUG ReplyWidget.toggle_reaction] ===== START =====")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] username: {self.username}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] content: {self.content[:30]}...")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] self.likes_list BEFORE: {self.likes_list}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] self.likes_count BEFORE: {self.likes_count}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] self.user_reaction BEFORE: {self.user_reaction}")
        
        # Get current user's username
        parent_widget = self.parent()
        while parent_widget and not isinstance(parent_widget, FacebookGUI):
            parent_widget = parent_widget.parent()
        
        current_user = 'You'
        if parent_widget and isinstance(parent_widget, FacebookGUI):
            profile = getattr(parent_widget, 'user_profile', {})
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            current_user = f"{first_name} {last_name}".strip() if first_name or last_name else 'You'
        
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] current_user: {current_user}")
        
        # CRITICAL: Check likes_list state, not just user_reaction!
        # When replies are re-expanded, user_reaction state may be lost but user is still in likes_list
        user_already_liked = current_user in self.likes_list
        
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] user_already_liked (from list): {user_already_liked}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] self.user_reaction (from state): {self.user_reaction}")
        
        # Toggle like: add or remove user from likes_list
        # Check the ACTUAL list state, not just user_reaction
        if user_already_liked:
            # User already liked - remove ALL occurrences to prevent duplicates
            # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] REMOVING like (user found in list)")
            # CRITICAL: Modify list IN-PLACE to preserve backend reference!
            # Using slice assignment to modify in-place, not create a new list
            self.likes_list[:] = [user for user in self.likes_list if user != current_user]
            # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] Cleaned likes_list (in-place): {self.likes_list}")
            self.user_reaction = None
            self.likes_count = len(self.likes_list)
            action_type = "remove"
        else:
            # User hasn't liked - add the like (ensure no duplicates)
            # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] ADDING like (user not in list)")
            self.likes_list.append(current_user)
            # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] Added to likes_list: {self.likes_list}")
            self.user_reaction = "👍"
            self.likes_count = len(self.likes_list)
            action_type = "add"
        
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] self.likes_list AFTER: {self.likes_list}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] self.likes_count AFTER: {self.likes_count}")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] self.user_reaction AFTER: {self.user_reaction}")
        
        # Update UI
        self.reaction_btn.setText(self.user_reaction if self.user_reaction else "👍")
        self.count_label.setText(f"· {self.likes_count}" if self.likes_count > 0 else "")
        
        # Save to interactions.json
        if parent_widget and isinstance(parent_widget, FacebookGUI):
            reply_like_data = {
                'username': current_user,
                'reply_author': self.username,
                'reply_content_preview': self.content[:50] if self.content else '',
                'action': action_type,
                'timestamp': get_timestamp()
            }
            if 'reply_likes' not in parent_widget.interactions:
                parent_widget.interactions['reply_likes'] = []
            parent_widget.interactions['reply_likes'].append(reply_like_data)
            parent_widget.save_interactions()
            # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] ✓ Saved to interactions.json")
        
        # CRITICAL: Save posts.json and rebuild home.json to persist the like
        # Find the parent FacebookGUI and trigger save
        if parent_widget and isinstance(parent_widget, FacebookGUI):
            parent_widget.save_posts()
            if not getattr(parent_widget, '_rebuilding_feed', False):
                parent_widget._rebuild_home_feed(parent_widget.all_posts)
                # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] ✓ Saved posts.json and rebuilt home.json")
        
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG ReplyWidget.toggle_reaction] ===== END =====\n")
    
    def update_timestamp(self):
        """Update the timestamp display"""
        self.time_label.setText(format_time_ago(self.time))


class CommentReactionBar(QFrame):
    """Reaction bar for comments - same as post reactions"""
    reaction_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #dddfe2;
                padding: 4px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Same reactions as posts
        self.reactions = ["👍", "❤️", "😂", "😮", "😢", "😡"]
        
        for emoji in self.reactions:
            btn = QPushButton(emoji)
            btn.setFont(QFont("Arial", 14))
            btn.setFixedSize(28, 28)
            btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    border-radius: 14px;
                }
                QPushButton:hover {
                    background-color: #f0f2f5;
                }
            """)
            btn.clicked.connect(lambda checked, e=emoji: self.reaction_selected.emit(e))
            layout.addWidget(btn)
        
        self.setVisible(False)


class QuoteDialog(QDialog):
    """Dialog for creating a quote post"""
    def __init__(self, original_username, original_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Quote {original_username}'s post")
        self.setMinimumSize(500, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Original post preview
        original_label = QLabel(f"Replying to {original_username}:")
        original_label.setFont(QFont("Arial", 11))
        original_label.setStyleSheet("color: #65676b;")
        layout.addWidget(original_label)
        
        original_frame = QFrame()
        original_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f2f5;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        original_layout = QVBoxLayout(original_frame)
        original_content_label = QLabel(original_content if original_content else "(No content)")
        original_content_label.setFont(QFont("Arial", 12))
        original_content_label.setWordWrap(True)
        original_layout.addWidget(original_content_label)
        layout.addWidget(original_frame)
        
        # User's quote input
        quote_label = QLabel("Add your thoughts:")
        quote_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(quote_label)
        
        self.quote_input = QTextEdit()
        self.quote_input.setPlaceholderText("Write your quote...")
        self.quote_input.setFont(QFont("Arial", 12))
        self.quote_input.setStyleSheet("""
            QTextEdit {
                background-color: #f0f2f5;
                border-radius: 8px;
                padding: 8px;
                border: 1px solid #dddfe2;
            }
        """)
        self.quote_input.setFixedHeight(80)
        layout.addWidget(self.quote_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("Arial", 11))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                color: #050505;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d8dadf;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        post_btn = QPushButton("Post")
        post_btn.setFont(QFont("Arial", 11, QFont.Bold))
        post_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #166fe5;
            }
        """)
        post_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(post_btn)
        
        layout.addLayout(buttons_layout)
    
    def get_quote(self):
        return self.quote_input.toPlainText().strip()


# ============================================================================
# Random User AI Engine - Google Gemini + LangChain Integration
# ============================================================================

@dataclass
class Action:
    """Represents a single user action for random_user AI"""
    tool: str
    post_id: Optional[str] = None
    original_post_id: Optional[str] = None  # For quote_post
    comment_id: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    caption: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert action to dictionary for JSON serialization"""
        result = {"tool": self.tool}
        if self.post_id:
            result["post_id"] = self.post_id
        if self.original_post_id:
            result["original_post_id"] = self.original_post_id
        if self.comment_id:
            result["comment_id"] = self.comment_id
        if self.content:
            result["content"] = self.content
        if self.type:
            result["type"] = self.type
        if self.caption:
            result["caption"] = self.caption
        return result


class RandomUserEngine:
    """
    Autonomous AI engine for simulating realistic user behavior
    Uses Google Gemini + LangChain for intelligent action generation
    """
    
    def __init__(self, base_dir: str = None, gui_callback=None):
        """Initialize the random user engine"""
        import traceback
        print(f"RandomUserEngine: __init__ called with base_dir={type(base_dir)}: {base_dir}")
        
        # Debug: Check if base_dir is a string or something else
        if not isinstance(base_dir, str):
            print(f"RandomUserEngine: ERROR - base_dir is not a string! Type: {type(base_dir)}")
            print(f"RandomUserEngine: Traceback: {traceback.format_stack()}")
            raise TypeError(f"base_dir must be str, got {type(base_dir)}")
        
        self.base_dir = base_dir
        print(f"RandomUserEngine: Set self.base_dir = {self.base_dir}")
        
        self.random_user_dir = os.path.join(self.base_dir, "system", "random_user")
        self.platform_dir = os.path.join(self.base_dir, "system", "platform")
        self.feed_dir = os.path.join(self.base_dir, "system", "feed")
        
        print(f"RandomUserEngine: Directories set: random_user={self.random_user_dir}")
        
        # Store GUI callback for refreshing feed after agent actions
        self.gui_callback = gui_callback
        if self.gui_callback is not None:
            callback_type = "Qt Signal" if hasattr(self.gui_callback, 'emit') else "Function"
            print(f"RandomUserEngine: GUI callback set successfully ({callback_type})")
        else:
            print(f"RandomUserEngine: No GUI callback provided - feed updates will not be visible in real-time")
        
        # Load all configuration files
        self.config = self._load_json(os.path.join(self.random_user_dir, "config.json"))
        self.tools = self._load_json(os.path.join(self.random_user_dir, "tools.json"))
        self.error_context = self._load_json(os.path.join(self.random_user_dir, "context.json"))
        self.platform_description = self._load_json(os.path.join(self.platform_dir, "description.json"))

        print(f"RandomUserEngine: Config files loaded")

        # Initialize action tracking for APM throttling
        self.action_timestamps = []

        # Initialize LLM if LangChain is available
        self.llm = None
        self.parser = None
        self._initialize_llm()
    
    def _load_json(self, path: str) -> Any:
        """Safely load a JSON file"""
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading {path}: {e}")
                return {}
        return {}
    
    def _initialize_llm(self):
        """Initialize Google Gemini via LangChain"""
        print("RandomUserEngine: Checking LangChain availability...")
        
        # Check availability at runtime
        if not check_langchain_availability():
            print("RandomUserEngine: ⚠️ LangChain not installed. Run: pip install langchain langchain-google-genai pydantic")
            return
        
        # Load API key from api.json
        api_path = os.path.join(self.base_dir, "api.json")
        print(f"RandomUserEngine: Reading API key from {api_path}")
        
        # Check if api.json exists
        if not os.path.exists(api_path):
            print(f"RandomUserEngine: ⚠️ api.json file not found at {api_path}")
            print("RandomUserEngine: Please create api.json with your Google API key:")
            print('{"api_key": "YOUR_API_KEY_HERE", "model": "gemini-1.5-flash"}')
            return
        
        api_data = self._load_json(api_path)
        api_key = api_data.get("api_key", "")
        model_name = api_data.get("model", "gemini-1.5-flash")  # Get model from api.json
        
        if not api_key:
            print("RandomUserEngine: ⚠️ API key is empty in api.json!")
            print("RandomUserEngine: Please add your Google API key to api.json:")
            print('{"api_key": "YOUR_ACTUAL_API_KEY", "model": "gemini-1.5-flash"}')
            return
        
        print(f"RandomUserEngine: API key found (length: {len(api_key)} chars)")
        print(f"RandomUserEngine: Using model: {model_name}")
        
        try:
            # Import the actual classes now that we know they're available
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain.prompts import PromptTemplate
            from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
            from langchain_core.exceptions import OutputParserException
            from pydantic import BaseModel, Field
            
            # Initialize Gemini model via LangChain
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,  # Use model from api.json
                google_api_key=api_key,
                temperature=self.config.get("traffic_control", {}).get("temperature", 0.7),
                convert_system_message_to_human=True
            )
            
            # Initialize Pydantic parser for structured output
            class ActionsOutput(BaseModel):
                actions: List[Dict] = Field(description="List of actions to perform")
            
            self.parser = PydanticOutputParser(pydantic_object=ActionsOutput)
            
            # Create output fixing parser for error recovery
            # Newer LangChain versions require retry_chain parameter
            # We'll use a simple approach with just the parser and handle retries manually
            self.fixing_parser = None
            self.has_pydantic_parser = True
            
            print("RandomUserEngine: ✓ Gemini LLM initialized successfully!")
            
        except Exception as e:
            print(f"RandomUserEngine: ✗ Error initializing Gemini: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            self.llm = None
    
    def _construct_system_prompt(self) -> str:
        """Construct the system prompt with platform context and tool definitions"""
        prompts_config = self.config.get("prompts", {})
        system_prompt = prompts_config.get("system_prompt", "You are a social media user.")
        role_prompt = prompts_config.get("role_prompt", "Act naturally while browsing.")
        
        # Build platform description section
        platform_context = "\n".join(self.platform_description) if self.platform_description else [
            "A social media platform for connecting with friends and sharing content.",
            "Users engage through posts, comments, reactions, and shares."
        ]
        
        # Build tool definitions section
        tools_section = "### Available Tools\n\n"
        for tool in self.tools:
            tools_section += f"**{tool.get('name', 'unknown')}**\n"
            tools_section += f"- Description: {tool.get('description', '')}\n"
            tools_section += f"- How to use: {tool.get('how_agent_should_answer', '')}\n\n"
        
        # Response format instruction
        response_format = """
### Response Format
You must respond with a valid JSON object containing an 'actions' array.
Each action must follow the tool format specified above.
Example response:
{
    "actions": [
        {"tool": "post_reactions", "post_id": "post_123", "type": "LIKE"},
        {"tool": "comment_post", "post_id": "post_456", "content": "Great post!"}
    ]
}
"""
        
        full_prompt = f"""{system_prompt}

{role_prompt}

## Platform Context
{platform_context}

## Platform Rules
1. Only interact with content IDs that appear in the provided feed data
2. Do not invent content, users, or interactions
3. Be authentic and natural in your interactions
4. Mix different types of actions (reactions, comments, shares)
5. Your actions should reflect genuine interest

{tools_section}
{response_format}

Current timestamp: {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}
"""
        return full_prompt
    
    def _construct_user_prompt(self, feed_data: Dict, profile_data: Dict = None) -> str:
        """Construct the user prompt with feed data"""
        posts = feed_data.get("posts", [])[:self.config.get("traffic_control", {}).get("feed_read", 30)]
        
        # Format feed for the prompt
        feed_section = "### Current Feed\n\n"
        for i, post in enumerate(posts):
            feed_section += f"[{i+1}] ID: {post.get('id', 'unknown')}\n"
            feed_section += f"    Author: {post.get('author', 'Unknown')}\n"
            feed_section += f"    Content: {post.get('content', '')[:100]}...\n"
            feed_section += f"    Stats: {post.get('likes', 0)} likes, {post.get('comments', 0)} comments\n"
            feed_section += f"    Time: {post.get('timestamp', '')}\n"
            
            # Include visible comments for this post
            visible_comments = post.get('visible_comments', [])
            if visible_comments:
                feed_section += f"    Comments:\n"
                for j, comment in enumerate(visible_comments):
                    comment_preview = comment.get('content', '')[:50]
                    feed_section += f"      [{j+1}] ID: {comment.get('id', 'unknown')}\n"
                    feed_section += f"          Author: {comment.get('author', 'Unknown')}\n"
                    feed_section += f"          Content: {comment_preview}...\n"
                    feed_section += f"          Likes: {comment.get('likes', 0)}\n"
            feed_section += "\n"
        
        # Interaction preferences
        interactions = self.config.get("interactions", {})
        interaction_section = "### Interaction Preferences (0-10 scale)\n"
        for tool, weight in interactions.items():
            interaction_section += f"- {tool}: {weight}/10\n"
        
        # Calculate number of actions to generate
        response_options = self.config.get("algorithm", {}).get("response_options", {})
        min_actions = response_options.get("min_actions_per_call", 1)
        max_actions = response_options.get("max_actions_per_call", 15)
        prefer_variety = response_options.get("prefer_variety", False)

        variety_instruction = ""
        if prefer_variety:
            variety_instruction = "\n- **VARIETY MATTERS**: When generating multiple actions, try to use different action types. If you find yourself generating many of the same action (e.g., 5 post_reactions in a row), mix in other action types like make_post, comment_post, or repost_post."

        user_prompt = f"""{feed_section}

{interaction_section}

## Task
Generate between {min_actions} and {max_actions} authentic actions based on the feed above.
Consider the interaction preferences - higher weights mean more frequent use of those actions.
Mix your actions across different posts and comments.{variety_instruction}

### IMPORTANT: Choosing the Right Comment Tool

When you want to INTERACT WITH A COMMENT (reply to what someone said), you MUST use **reply_comment**:
- Use the comment's ID (e.g., comment_abc123) from the feed data
- Your reply should directly address what that specific commenter said
- Example: Comment says "I love pizza!" → reply_comment: "What toppings do you get?"

When you want to COMMENT ON THE POST ITSELF (start a new topic), use **comment_post**:
- Use the post's ID from the feed data
- Your comment should be about the post's main content
- Example: Post asks "What's for dinner?" → comment_post: "I'm making tacos tonight!"

Be natural - don't interact with every post, only those that genuinely interest you.

Your response must be a valid JSON object with an 'actions' array.
"""
        return user_prompt
    
    def _validate_actions(self, actions: List[Dict], valid_post_ids: set, valid_comment_ids: set = None) -> List[Action]:
        """Validate and filter actions against valid post and comment IDs"""
        if valid_comment_ids is None:
            valid_comment_ids = set()
        
        valid_actions = []
        
        for action in actions:
            tool = action.get("tool", "")
            
            # Check if tool is valid
            valid_tools = [t.get("name") for t in self.tools]
            if tool not in valid_tools:
                continue
            
            # Check if post_id exists in feed
            post_id = action.get("post_id")
            if post_id and post_id not in valid_post_ids:
                continue
            
            # Check if original_post_id exists in feed (for quote_post)
            original_post_id = action.get("original_post_id")
            if tool == "quote_post" and original_post_id:
                if original_post_id not in valid_post_ids:
                    continue
            
            # Check if comment_id exists in feed (for reply_comment and react_comment)
            comment_id = action.get("comment_id")
            if comment_id:
                if tool in ["reply_comment", "react_comment"]:
                    if comment_id not in valid_comment_ids:
                        continue
                else:
                    # comment_id should not be provided for other tools
                    continue
            
            # Check if comment_id is missing when required (for reply_comment and react_comment)
            if tool in ["reply_comment", "react_comment"] and not comment_id:
                continue
            
            # Create Action object
            valid_actions.append(Action(
                tool=tool,
                post_id=post_id,
                original_post_id=original_post_id,
                comment_id=comment_id,
                content=action.get("content"),
                type=action.get("type"),
                caption=action.get("caption")
            ))
        
        return valid_actions
    
    def _handle_error(self, error: Exception, strategy: str = None) -> List[Action]:
        """Handle errors based on context.json strategies"""
        if not strategy:
            strategy = self.error_context.get("error_strategies", {}).get(
                type(error).__name__, 
                {"action": "terminate"}
            ).get("action", "terminate")
        
        strategies = self.error_context.get("error_strategies", {})
        
        if strategy == "retry" or strategy == "log_and_skip":
            # Return empty list for now, could implement retry logic
            print(f"Error handling: {strategy} - {error}")
            return []
        elif strategy == "backoff":
            # Could implement sleep/backoff here
            print(f"Rate limit, backing off: {error}")
            return []
        elif strategy == "terminate":
            raise error
        else:
            # Default: return empty list
            return []
    
    def generate_actions(self, feed_data: Dict = None, profile_data: Dict = None) -> List[Action]:
        """
        Main method to generate user actions
        
        Args:
            feed_data: Dictionary containing posts from home.json
            profile_data: Optional profile information for context
        
        Returns:
            List of validated Action objects
        """
        # Load feed data if not provided
        if feed_data is None:
            home_path = os.path.join(self.feed_dir, "home.json")
            if os.path.exists(home_path):
                with open(home_path, 'r') as f:
                    feed_data = json.load(f)
            else:
                feed_data = {"posts": []}
        
        # Check if LLM is available at runtime
        if not check_langchain_availability():
            print("RandomUserEngine: ⚠️ Running in simulation mode (no LangChain)")
            return []
        
        if not self.llm:
            print("RandomUserEngine: ⚠️ Running in simulation mode (no API key)")
            return []
        
        # Import PromptTemplate here since it's needed
        try:
            from langchain.prompts import PromptTemplate
        except ImportError as e:
            print(f"RandomUserEngine: ✗ Failed to import PromptTemplate: {e}")
            return []
        
        # Get valid post IDs and comment IDs for validation
        valid_post_ids = set()
        valid_comment_ids = set()
        
        for post in feed_data.get("posts", []):
            post_id = post.get("id")
            if post_id:
                valid_post_ids.add(post_id)
            
            # Collect visible comment IDs from this post
            visible_comments = post.get("visible_comments", [])
            for comment in visible_comments:
                comment_id = comment.get("id")
                if comment_id:
                    valid_comment_ids.add(comment_id)
        
        print(f"RandomUserEngine: Processing {len(valid_post_ids)} valid posts and {len(valid_comment_ids)} valid comments from feed")
        
        # Construct prompts
        system_prompt = self._construct_system_prompt()
        user_prompt = self._construct_user_prompt(feed_data, profile_data)
        
        # Create LangChain prompt template
        prompt_template = PromptTemplate.from_template(
            "{system}\n\n{user}"
        )
        
        try:
            # Generate response using LangChain + Gemini
            print("RandomUserEngine: Sending request to Gemini...")
            chain = prompt_template | self.llm
            response = chain.invoke({
                "system": system_prompt,
                "user": user_prompt
            })
            print("RandomUserEngine: ✓ Received response from Gemini")
            
            # Parse response - try with fixing parser first if available, otherwise manual parsing
            print("RandomUserEngine: Parsing response...")
            
            # Try to parse the JSON response
            try:
                # First, try to extract JSON from the response
                content = response.content.strip()
                
                # Remove markdown code blocks if present
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                
                if content.endswith("```"):
                    content = content[:-3]
                
                content = content.strip()
                
                # Parse the JSON
                parsed_data = json.loads(content)
                
                # Extract actions from parsed data
                if isinstance(parsed_data, dict) and 'actions' in parsed_data:
                    actions = parsed_data['actions']
                elif isinstance(parsed_data, list):
                    actions = parsed_data
                else:
                    print("RandomUserEngine: ⚠️ Unexpected response format")
                    return []
                
            except json.JSONDecodeError as e:
                print(f"RandomUserEngine: ✗ Failed to parse JSON response: {e}")
                print(f"Response content: {response.content[:200]}...")
                return []
            
            # Validate actions
            valid_actions = self._validate_actions(actions, valid_post_ids, valid_comment_ids)
            
            print(f"RandomUserEngine: ✓ Validated {len(valid_actions)}/{len(actions)} actions")
            return valid_actions
            
        except Exception as e:
            print(f"RandomUserEngine: ✗ Error generating actions: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            error_strategy = None
            error_type = type(e).__name__
            if error_type in self.error_context.get("error_strategies", {}):
                error_strategy = self.error_context["error_strategies"][error_type].get("action")
            
            return self._handle_error(e, error_strategy)
    
    def run_session(self) -> List[Action]:
        """Run a complete session: load feed, generate actions, return them"""
        # Check if random_user is enabled
        work = self.config.get("work", 1)
        if not work:
            print("RandomUserEngine: Paused (work=0), skipping session")
            return []

        # Check actions per minute throttling
        apm = self.config.get("traffic_control", {}).get("actions_per_minute", 3)
        if apm > 0:
            from datetime import datetime, timedelta
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)

            # Clean up old timestamps (older than 1 minute)
            self.action_timestamps = [ts for ts in self.action_timestamps if ts > one_minute_ago]

            # Count actions in the last minute
            recent_actions = len(self.action_timestamps)

            if recent_actions >= apm:
                print(f"RandomUserEngine: APM throttling - {recent_actions}/{apm} actions in last minute, skipping session")
                return []

        # Load fresh feed data from home.json (reloads every session to pick up new posts)
        home_path = os.path.join(self.feed_dir, "home.json")
        feed_data = {"posts": []}
        
        if os.path.exists(home_path):
            with open(home_path, 'r') as f:
                feed_data = json.load(f)
        
        # Check if feed is empty
        posts = feed_data.get("posts", [])
        
        # Handle empty feed: allow make_post even when feed is empty
        if len(posts) == 0:
            print("RandomUserEngine: Feed is empty, can still create new content")
            # For empty feed, we can still make posts, so don't skip
            # But we still do APC check to control posting frequency
            apc = self.config.get("traffic_control", {}).get("actions_per_cent", 65)
            import random
            roll = random.randint(1, 100)
            print(f"RandomUserEngine: APC roll = {roll}/{apc}% (empty feed, can create content)")
            
            if roll > apc:
                print("RandomUserEngine: APC check failed, skipping session")
                return []
            
            print("RandomUserEngine: APC check passed, proceeding with session (empty feed - will create content)")
            
            # Generate actions for empty feed (only make_post should be possible)
            actions = self.generate_actions(feed_data)
            
            # Apply decline_actions logic if enabled
            actions = self._apply_decline_actions(actions)
            
            return actions
        
        # Feed has posts - normal operation
        # Check if we should run (APC check)
        apc = self.config.get("traffic_control", {}).get("actions_per_cent", 65)
        import random
        roll = random.randint(1, 100)
        print(f"RandomUserEngine: APC roll = {roll}/{apc}%")
        
        if roll > apc:
            print("RandomUserEngine: APC check failed, skipping session")
            return []
        
        print("RandomUserEngine: APC check passed, proceeding with session")
        
        # Generate actions
        actions = self.generate_actions(feed_data)
        
        # Apply decline_actions logic if enabled
        actions = self._apply_decline_actions(actions)

        # Track actions for APM throttling (timestamp when generated)
        if actions:
            from datetime import datetime
            self.action_timestamps.extend([datetime.now()] * len(actions))

        return actions
    
    def _apply_decline_actions(self, actions: List[Action]) -> List[Action]:
        """Apply decline_actions logic to filter actions based on config"""
        if not actions:
            return actions
        
        decline_actions = self.config.get("decline_actions", 0)
        if decline_actions != 1:
            return actions
        
        decline_cent = self.config.get("decline_actions_cent", 0)
        if decline_cent <= 0:
            return actions
        
        # Calculate how many actions to keep (100 - decline_cent)%
        keep_percent = 100 - decline_cent
        num_to_keep = max(1, int(len(actions) * keep_percent / 100))
        
        if num_to_keep >= len(actions):
            return actions
        
        # Randomly select which actions to keep
        import random
        original_count = len(actions)
        actions = random.sample(actions, num_to_keep)
        declined_count = original_count - num_to_keep
        
        print(f"RandomUserEngine: Throttled actions. Kept {num_to_keep}/{original_count}, declined {declined_count} ({decline_cent}%)")

        return actions

    def _apply_variety(self, actions: List[Action]) -> List[Action]:
        """Apply prefer_variety logic to avoid repeating the same action type"""
        if not actions:
            return actions

        prefer_variety = self.config.get("algorithm", {}).get("response_options", {}).get("prefer_variety", False)
        if not prefer_variety:
            return actions

        # If we have multiple actions, ensure variety in action types
        # Group actions by type and prefer different types
        action_types = {}
        for action in actions:
            action_type = action.action_type
            if action_type not in action_types:
                action_types[action_type] = []
            action_types[action_type].append(action)

        # If we have multiple action types with similar representation, that's good
        # The AI should naturally generate variety based on weights
        # This method ensures we don't have too many of the same type if possible
        return actions

    def _get_last_action_type(self) -> str:
        """Get the last action type that was executed"""
        # This would need to be tracked externally when actions are executed
        # For now, return None to indicate no recent action
        return None


class PostWidget(QFrame):
    def __init__(self, username, avatar, content, time, likes=0, comments=0, shares=0, embedded_post=None, is_quote=False, edits=None, is_edited=False, folder_name=None, post_id=None, comments_list=None, reacts=None, current_user=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #dddfe2;
            }
        """)
        # Store all parameters as instance attributes FIRST
        self.username = username
        self.avatar = avatar
        self.content = content
        self.folder_name = folder_name  # Store the folder name for profile navigation
        self.post_id = post_id  # Store post ID for live updates
        self.comments_list = comments_list if comments_list is not None else []  # Store comments
        
        # Store time as datetime for dynamic updates
        if isinstance(time, str):
            try:
                self.time = datetime.strptime(time, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                self.time = datetime.now()
        else:
            self.time = time
        
        # Initialize likes_count and user_reaction
        # NOTE: We do NOT sync likes_count with len(reacts) because random_user
        # reactions are stored directly in post['likes'] and not in reacts[]
        # The reacts[] array only tracks the REAL USER's reactions
        if reacts is None:
            reacts = []
        
        # Use the passed likes parameter as-is (set by random_user or user)
        self.likes_count = likes
        
        # Set user_reaction based on whether current user is in reacts array
        self.user_reaction = None
        if current_user and reacts:
            for r in reacts:
                if isinstance(r, dict) and r.get('username') == current_user:
                    self.user_reaction = r.get('emoji')
                    break
        
        self.comments_count = comments
        self.shares_count = shares
        self.embedded_post = embedded_post
        self.is_quote = is_quote  # Flag to show "Original" button for quotes
        self.is_edited = is_edited  # Track if post has been edited
        self.comments_expanded = False  # Track if comments section is expanded
        self.edits = edits if edits else []  # Store edit history
        
        # Store the original time string for identification
        self._time_str = time if isinstance(time, str) else time.strftime("%Y/%m/%d %H:%M:%S")
        
        # Setup main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Build the complete UI
        self.build_post_ui()
        
        # Load existing comments if any
        if self.comments_list:
            self._load_comments_from_data()
        
        # If there are edits, rebuild the content display
        if self.edits:
            self.rebuild_content_display()
        
        # Connect to destroyed signal for cleanup
        self.destroyed.connect(self._cleanup_post)
    
    def _cleanup_post(self):
        """Clean up post widget references to prevent memory leaks"""
        # Clear comments list to break circular references
        if hasattr(self, 'comments_list'):
            self.comments_list.clear()
        
        # Clear any other heavy references
        self.embedded_post = None
        self.edits = None
    
    def _load_comments_from_data(self):
        """Load comments from the stored comments_list data.
        
        CRITICAL: Do NOT call add_comment() here - it appends to self.comments_list
        causing an infinite loop. Just create CommentWidget directly."""
        # Debug logging disabled for _load_comments_from_data
        # debug_print(MASTER_DEBUG_ENABLED, f"\n[DEBUG _load_comments_from_data] ===== START =====")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG _load_comments_from_data] Loading {len(self.comments_list)} comments for post {getattr(self, 'post_id', 'unknown')}")
        
        for comment_data in self.comments_list:
            username = comment_data.get('username', 'Unknown')
            avatar = comment_data.get('avatar', '👤')
            content = comment_data.get('content', '')
            time_str = comment_data.get('time', datetime.now())
            replies = comment_data.get('replies', [])  # Get replies if any
            comment_id = comment_data.get('id')  # Get comment ID
            
            # Debug logging disabled for _load_comments_from_data
            # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG _load_comments_from_data] Creating CommentWidget:")
            # debug_print(MASTER_DEBUG_ENABLED, f"  - username: {username}")
            # debug_print(MASTER_DEBUG_ENABLED, f"  - content: {content}")
            # debug_print(MASTER_DEBUG_ENABLED, f"  - comment_id: {comment_id}")
            # debug_print(MASTER_DEBUG_ENABLED, f"  - replies count: {len(replies)}")
            
            # Parse time
            if isinstance(time_str, str):
                try:
                    time_obj = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
                except ValueError:
                    time_obj = datetime.now()
            else:
                time_obj = time_str
            
            # Create CommentWidget directly WITHOUT calling add_comment()
            # add_comment() appends to self.comments_list which causes infinite loop
            # Pass likes, reacts, and backend comment reference for persistence
            comment_likes = comment_data.get('likes', 0)
            comment_reacts = comment_data.get('reacts', [])
            
            # Get current user for user_reaction initialization
            current_user = 'You'
            parent_gui = self.parent()
            while parent_gui and not isinstance(parent_gui, FacebookGUI):
                parent_gui = parent_gui.parent()
            if parent_gui and isinstance(parent_gui, FacebookGUI):
                profile = getattr(parent_gui, 'user_profile', {})
                first_name = profile.get('first_name', '')
                last_name = profile.get('last_name', '')
                current_user = f"{first_name} {last_name}".strip() if first_name or last_name else 'You'
            
            comment = CommentWidget(
                username, avatar, content, time_obj, self, 
                replies=replies, 
                comment_id=comment_id,
                likes=comment_likes,
                comment_data_ref=comment_data,
                reacts=comment_reacts,
                current_user=current_user
            )
            self.comments_list_layout.addWidget(comment)
            # Don't increment self.comments_count here - it's already correctly initialized
            # from the post data at instantiation time
            self.update_reactions_display()
            self.update_toggle_comments_button()

        # Debug logging disabled for _load_comments_from_data
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG _load_comments_from_data] Loaded {len(self.comments_list)} comments")
        # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG _load_comments_from_data] ===== END =====\n")
    
    def build_post_ui(self):
        """Build the complete post UI"""
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 12, 12, 8)
        
        avatar_label = QLabel(self.avatar)
        avatar_label.setFont(QFont("Arial", 32))
        avatar_label.setFixedSize(40, 40)  # Proper size
        avatar_label.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)  # Center both vertically and horizontally
        avatar_label.setStyleSheet("QLabel { min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; }")
        header_layout.addWidget(avatar_label)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)  # Less spacing between name and time
        
        # Make name clickable to go to profile
        name_label = QLabel(self.username)
        name_label.setFont(QFont("Arial", 14, QFont.Bold))
        name_label.setStyleSheet("color: #050505;")
        name_label.setCursor(Qt.PointingHandCursor)
        name_label.mousePressEvent = lambda event: self.on_name_clicked()
        info_layout.addWidget(name_label)
        
        # Dynamic timestamp label
        time_text = format_time_ago(self.time)
        if self.is_edited:
            time_text = f"{time_text} · Edited"
        
        self.time_label = QLabel(time_text)
        self.time_label.setFont(QFont("Arial", 11))
        self.time_label.setStyleSheet("color: #65676b;")
        info_layout.addWidget(self.time_label)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        more_btn = QPushButton("...")
        more_btn.setFont(QFont("Arial", 16))
        more_btn.setStyleSheet("""
            QPushButton {
                color: #606770;
                border: none;
                background: transparent;
                border-radius: 20px;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
            }
        """)
        more_btn.clicked.connect(self.show_post_options)
        header_layout.addWidget(more_btn)
        self.more_btn = more_btn
        
        self.main_layout.addLayout(header_layout)
        
        # Content - store as instance attribute for sharing/reposting
        self.content_label = None
        if self.content:
            self.content_label = QLabel(self.content)
            self.content_label.setFont(QFont("Arial", 14))
            self.content_label.setStyleSheet("color: #050505;")
            self.content_label.setWordWrap(True)
            self.content_label.setContentsMargins(12, 0, 12, 8)
            self.main_layout.addWidget(self.content_label)
        
        # Embedded original post (for reposts/quotes)
        if self.embedded_post:
            self.create_embedded_post(self.embedded_post, show_original_btn=self.is_quote)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #ced0d4;")
        self.main_layout.addWidget(divider)
        
        # Reactions count
        reactions_layout = QHBoxLayout()
        reactions_layout.setContentsMargins(12, 8, 12, 8)
        
        self.reactions_label = QLabel("")
        self.reactions_label.setFont(QFont("Arial", 12))
        self.reactions_label.setStyleSheet("color: #65676b;")
        reactions_layout.addWidget(self.reactions_label)
        
        reactions_layout.addStretch()
        
        self.likes_label = QLabel("")
        self.likes_label.setFont(QFont("Arial", 12))
        self.likes_label.setStyleSheet("color: #65676b;")
        reactions_layout.addWidget(self.likes_label)
        
        reactions_layout.addSpacing(16)
        
        self.comments_label = QLabel("")
        self.comments_label.setFont(QFont("Arial", 12))
        self.comments_label.setStyleSheet("color: #65676b;")
        reactions_layout.addWidget(self.comments_label)
        
        reactions_layout.addSpacing(16)
        
        self.shares_label = QLabel("")
        self.shares_label.setFont(QFont("Arial", 12))
        self.shares_label.setStyleSheet("color: #65676b;")
        reactions_layout.addWidget(self.shares_label)
        
        self.main_layout.addLayout(reactions_layout)
        
        # Update counts display
        self.update_reactions_display()
        
        # Divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet("color: #ced0d4;")
        self.main_layout.addWidget(divider2)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(8, 4, 8, 4)
        action_layout.setSpacing(0)
        
        # Like button with reaction bar
        like_container = QWidget()
        like_container_layout = QVBoxLayout(like_container)
        like_container_layout.setContentsMargins(0, 0, 0, 0)
        like_container_layout.setSpacing(0)
        
        self.like_btn = QPushButton("👍 Like")
        self.like_btn.setFont(QFont("Arial", 13, QFont.Bold))
        self.like_btn.setStyleSheet("""
            QPushButton {
                color: #65676b;
                border: none;
                background: transparent;
                padding: 10px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
            }
            QPushButton:pressed {
                background-color: #e4e6eb;
            }
        """)
        self.like_btn.clicked.connect(self.on_like_clicked)
        like_container_layout.addWidget(self.like_btn)
        
        self.reaction_bar = ReactionBar(self)
        self.reaction_bar.setVisible(False)
        like_container_layout.addWidget(self.reaction_bar)
        
        action_layout.addWidget(like_container)
        
        # Comment button
        comment_btn = QPushButton("💬 Comment")
        comment_btn.setFont(QFont("Arial", 13, QFont.Bold))
        comment_btn.setStyleSheet("""
            QPushButton {
                color: #65676b;
                border: none;
                background: transparent;
                padding: 10px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
            }
        """)
        comment_btn.clicked.connect(self.on_comment_clicked)
        action_layout.addWidget(comment_btn)
        
        # Share button
        share_btn = QPushButton("↗️ Share")
        share_btn.setFont(QFont("Arial", 13, QFont.Bold))
        share_btn.setStyleSheet("""
            QPushButton {
                color: #65676b;
                border: none;
                background: transparent;
                padding: 10px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
            }
        """)
        share_btn.clicked.connect(self.on_share_clicked)
        action_layout.addWidget(share_btn)
        
        self.main_layout.addLayout(action_layout)
        
        # Divider
        divider3 = QFrame()
        divider3.setFrameShape(QFrame.HLine)
        divider3.setStyleSheet("color: #ced0d4;")
        self.main_layout.addWidget(divider3)
        
        # Comment input
        comment_input_layout = QHBoxLayout()
        comment_input_layout.setContentsMargins(8, 8, 8, 8)
        
        user_avatar = QLabel("👤")
        user_avatar.setFont(QFont("Arial", 24))
        comment_input_layout.addWidget(user_avatar)
        
        # Multi-line comment input
        self.comment_input = CommentTextEdit()
        self.comment_input.setPlaceholderText("Write a comment...")
        self.comment_input.setFont(QFont("Arial", 12))
        self.comment_input.setStyleSheet("""
            QTextEdit {
                background-color: #f0f2f5;
                border-radius: 16px;
                padding: 8px 12px;
                border: none;
                font-size: 12px;
            }
            QTextEdit:focus {
                background-color: white;
                border: 1px solid #1877f2;
            }
        """)
        self.comment_input.setFixedHeight(55)
        self.comment_input.returnPressed.connect(self.add_comment_from_input)
        comment_input_layout.addWidget(self.comment_input)
        
        comment_input_layout.addStretch()
        
        self.main_layout.addLayout(comment_input_layout)
        
        # Collapsible Comments Section
        self.comments_container = QWidget()
        self.comments_container.setVisible(False)  # Hidden by default
        self.comments_layout = QVBoxLayout(self.comments_container)
        self.comments_layout.setContentsMargins(8, 0, 8, 8)
        self.comments_layout.setSpacing(8)
        
        # Inner scroll area for comments (like modern social media)
        self.comments_scroll = QScrollArea()
        self.comments_scroll.setWidgetResizable(True)
        self.comments_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
                max-height: 400px;  /* Limit height for inner scrolling */
            }
            QScrollArea QWidget QWidget {
                background-color: transparent;
            }
        """)
        self.comments_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.comments_widget = QWidget()
        self.comments_list_layout = QVBoxLayout(self.comments_widget)
        self.comments_list_layout.setContentsMargins(0, 0, 0, 0)
        self.comments_list_layout.setSpacing(8)
        
        self.comments_scroll.setWidget(self.comments_widget)
        self.comments_layout.addWidget(self.comments_scroll)
        
        self.main_layout.addWidget(self.comments_container)
        
        # Show/Hide comments button
        self.toggle_comments_btn = QPushButton()
        self.toggle_comments_btn.setFont(QFont("Arial", 12))
        self.toggle_comments_btn.setStyleSheet("""
            QPushButton {
                color: #65676b;
                border: none;
                background: transparent;
                padding: 8px 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
                border-radius: 4px;
            }
        """)
        self.toggle_comments_btn.clicked.connect(self.toggle_comments)
        self.main_layout.addWidget(self.toggle_comments_btn)
        self.update_toggle_comments_button()
    
    def update_reactions_display(self):
        # Update likes label
        if self.likes_count > 0:
            self.likes_label.setText(f"{self.likes_count} likes")
        else:
            self.likes_label.setText("")
        
        # Update comments label
        if self.comments_count > 0:
            self.comments_label.setText(f"{self.comments_count} comments")
        else:
            self.comments_label.setText("")
        
        # Update shares label
        if self.shares_count > 0:
            self.shares_label.setText(f"{self.shares_count} shares")
        else:
            self.shares_label.setText("")
        
        # Update reactions emoji
        if self.user_reaction:
            self.reactions_label.setText(self.user_reaction)
        else:
            self.reactions_label.setText("")
    
    def update_from_all_posts(self, all_posts):
        """Update post counts from live data in all_posts"""
        if not self.post_id:
            return
        
        # Find the post in all_posts by ID
        for post in all_posts:
            if post.get('id') == self.post_id:
                # Update counts from live data
                new_likes = post.get('likes', 0)
                new_comments = post.get('comments', 0)
                new_shares = post.get('shares', 0)
                
                # Only update if values changed
                if (new_likes != self.likes_count or 
                    new_comments != self.comments_count or 
                    new_shares != self.shares_count):
                    self.likes_count = new_likes
                    self.comments_count = new_comments
                    self.shares_count = new_shares
                    self.update_reactions_display()
                break
    
    def create_embedded_post(self, post_data, show_original_btn=False):
        """Create an embedded post widget inside this post"""
        embedded_frame = QFrame()
        embedded_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f2f5;
                border-radius: 8px;
                border: 1px solid #dddfe2;
                margin: 8px 12px;
            }
        """)
        
        embedded_layout = QVBoxLayout(embedded_frame)
        embedded_layout.setContentsMargins(8, 8, 8, 8)
        embedded_layout.setSpacing(4)
        
        # Header of embedded post
        header_layout = QHBoxLayout()
        
        embedded_avatar = QLabel(post_data.get('avatar', '👤'))
        embedded_avatar.setFont(QFont("Arial", 20))
        embedded_avatar.setFixedSize(24, 24)
        embedded_avatar.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        header_layout.addWidget(embedded_avatar)
        
        info_layout = QVBoxLayout()
        
        embedded_name = QLabel(post_data.get('username', 'Unknown'))
        embedded_name.setFont(QFont("Arial", 12, QFont.Bold))
        embedded_name.setStyleSheet("color: #050505;")
        info_layout.addWidget(embedded_name)
        
        embedded_time = QLabel(format_time_ago(post_data.get('time', 'Just now')))
        embedded_time.setFont(QFont("Arial", 10))
        embedded_time.setStyleSheet("color: #65676b;")
        info_layout.addWidget(embedded_time)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        embedded_layout.addLayout(header_layout)
        
        # Embedded content
        embedded_content = post_data.get('content', '')
        if embedded_content:
            content_label = QLabel(embedded_content)
            content_label.setFont(QFont("Arial", 12))
            content_label.setStyleSheet("color: #050505;")
            content_label.setWordWrap(True)
            embedded_layout.addWidget(content_label)
        
        # Show original post stats (likes, comments, shares) like social media apps
        likes_count = post_data.get('likes', 0)
        comments_count = post_data.get('comments', 0)
        shares_count = post_data.get('shares', 0)
        
        stats_text = []
        if likes_count > 0:
            stats_text.append(f"{likes_count} likes")
        if comments_count > 0:
            stats_text.append(f"{comments_count} comments")
        if shares_count > 0:
            stats_text.append(f"{shares_count} shares")
        
        if stats_text:
            stats_label = QLabel(" · ".join(stats_text))
            stats_label.setFont(QFont("Arial", 10))
            stats_label.setStyleSheet("color: #65676b;")
            embedded_layout.addWidget(stats_label)
        
        # Add "Original" button for quote posts
        if show_original_btn:
            original_btn = QPushButton("Original")
            original_btn.setFont(QFont("Arial", 10))
            original_btn.setStyleSheet("""
                QPushButton {
                    color: #1877f2;
                    border: none;
                    background: transparent;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    text-decoration: underline;
                }
            """)
            original_btn.clicked.connect(lambda: self.show_original_post(post_data))
            embedded_layout.addWidget(original_btn)
        
        self.main_layout.addWidget(embedded_frame)
        return embedded_frame
    
    def show_original_post(self, post_data):
        """Navigate to the original post in the feed"""
        # Find the parent FacebookGUI and navigate to the original post
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        if parent and isinstance(parent, FacebookGUI):
            parent.navigate_to_original_post(post_data)
    
    def show_original_post_dialog(self, post_data):
        """Show a dialog with the full original post (fallback)"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Original Post by {post_data.get('username', 'Unknown')}")
        dialog.setMinimumSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # Header
        header = QLabel(f"{post_data.get('avatar', '👤')} {post_data.get('username', 'Unknown')} · {format_time_ago(post_data.get('time', datetime.now()))}")
        header.setFont(QFont("Arial", 12))
        layout.addWidget(header)
        
        # Content
        content = QLabel(post_data.get('content', ''))
        content.setFont(QFont("Arial", 14))
        content.setWordWrap(True)
        layout.addWidget(content)
        
        # Stats
        likes = post_data.get('likes', 0)
        comments = post_data.get('comments', 0)
        shares = post_data.get('shares', 0)
        stats_text = []
        if likes > 0:
            stats_text.append(f"{likes} likes")
        if comments > 0:
            stats_text.append(f"{comments} comments")
        if shares > 0:
            stats_text.append(f"{shares} shares")
        
        if stats_text:
            stats_label = QLabel(" · ".join(stats_text))
            stats_label.setFont(QFont("Arial", 11))
            stats_label.setStyleSheet("color: #65676b;")
            layout.addWidget(stats_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def on_name_clicked(self):
        """Navigate to profile when username is clicked"""
        # Find the parent FacebookGUI
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        if parent and isinstance(parent, FacebookGUI):
            # Check if this is the current user's post
            first_name = parent.user_profile.get('first_name', '')
            last_name = parent.user_profile.get('last_name', '')
            user_name = f"{first_name} {last_name}".strip()
            
            if self.username == "You" or self.username == user_name:
                # Navigate to main user's profile
                parent.show_profile()
            elif self.folder_name == 'random_user':
                # Random User has no profile - show error message
                msg = QMessageBox()
                msg.setWindowTitle("No Profile")
                msg.setText("This user have no Profile!")
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: white;
                    }
                    QMessageBox QLabel {
                        font-size: 16px;
                        color: #050505;
                    }
                """)
                msg.exec_()
            elif self.folder_name:
                # Navigate to the friend's profile using stored folder_name
                parent.show_profile(self.folder_name)
            else:
                # Try to find the folder name by searching through friend profiles
                folder_name = parent.find_folder_by_username(self.username)
                if folder_name:
                    parent.show_profile(folder_name)
                else:
                    # If we can't find the folder, show error message
                    msg = QMessageBox()
                    msg.setWindowTitle("No Profile")
                    msg.setText("This user have no Profile!")
                    msg.setStyleSheet("""
                        QMessageBox {
                            background-color: white;
                        }
                        QMessageBox QLabel {
                            font-size: 16px;
                            color: #050505;
                        }
                    """)
                    msg.exec_()
    
    def get_post_time_str(self):
        """Get the time string identifier for this post"""
        return self._time_str
    
    def is_own_post(self, parent):
        """Check if this post belongs to the current user"""
        first_name = parent.user_profile.get('first_name', '')
        last_name = parent.user_profile.get('last_name', '')
        user_name = f"{first_name} {last_name}".strip()
        return self.username == "You" or self.username == user_name
    
    def show_post_options(self):
        """Show options menu for the post (delete/edit if own post, report/unreport for others)"""
        menu = QMessageBox()
        menu.setWindowTitle("Post Options")
        menu.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
        """)
        
        # Find parent FacebookGUI to check ownership
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        # Check if this is the user's own post
        is_own = self.is_own_post(parent) if parent else False
        
        if is_own:
            # Own posts: show Edit and Delete
            delete_btn = QPushButton("🗑️ Delete Post")
            delete_btn.clicked.connect(self.delete_post)
            menu.addButton(delete_btn, QMessageBox.ActionRole)
            
            edit_btn = QPushButton("✏️ Edit Post")
            edit_btn.clicked.connect(self.edit_post)
            menu.addButton(edit_btn, QMessageBox.ActionRole)
        else:
            # Other users' posts: show Report/Unreport
            # Check if current user already reported this post
            post_time = self.get_post_time_str()
            has_reported = False
            if parent:
                for post_data in parent.all_posts:
                    if post_data.get('time') == post_time:
                        reported_by = post_data.get('reported_by', [])
                        # Get current user's identifier
                        first_name = parent.user_profile.get('first_name', '')
                        last_name = parent.user_profile.get('last_name', '')
                        user_identifier = f"{first_name} {last_name}".strip()
                        has_reported = user_identifier in reported_by
                        break
            
            if has_reported:
                # User already reported, show Unreport
                unreport_btn = QPushButton("🚩 Unreport Post")
                unreport_btn.clicked.connect(self.unreport_post)
                menu.addButton(unreport_btn, QMessageBox.ActionRole)
            else:
                # User hasn't reported, show Report
                report_btn = QPushButton("🚩 Report Post")
                report_btn.clicked.connect(self.report_post)
                menu.addButton(report_btn, QMessageBox.ActionRole)
        
        # Add Cancel button to close the menu
        cancel_btn = QPushButton("✕ Cancel")
        menu.addButton(cancel_btn, QMessageBox.RejectRole)
        
        menu.exec_()
    
    def delete_post(self):
        """Delete this post from the feed"""
        # Find the parent FacebookGUI and remove this post
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        if parent and isinstance(parent, FacebookGUI):
            # Get the post's time identifier
            post_time = self.get_post_time_str()
            
            # Get post info for logging
            post_id = self.post_id
            post_content = self.content[:30] if self.content else "N/A"
            
            # Remove from all_posts list
            parent.all_posts = [p for p in parent.all_posts if p.get('time') != post_time]
            parent.save_posts()
            
            # Rebuild home.json to remove the post
            parent._rebuild_home_feed(parent.all_posts)
            
            # Log deletion to interactions.json
            parent.log_interaction('post_deletions', {
                'post_id': post_id,
                'content_preview': post_content,
                'timestamp': get_timestamp()
            })
            
            # Remove from layout
            for i in range(parent.posts_layout.count()):
                item = parent.posts_layout.itemAt(i)
                if item.widget() == self:
                    parent.posts_layout.removeItem(item)
                    self.deleteLater()
                    break
    
    def report_post(self):
        """Report this post - adds user to reported_by list, deletes if it reaches 10 reports"""
        # Find the parent FacebookGUI
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        if parent and isinstance(parent, FacebookGUI):
            # Get the post's time identifier
            post_time = self.get_post_time_str()
            
            # Get current user's identifier
            first_name = parent.user_profile.get('first_name', '')
            last_name = parent.user_profile.get('last_name', '')
            user_identifier = f"{first_name} {last_name}".strip()
            
            # Find and update the post in all_posts
            for post_data in parent.all_posts:
                if post_data.get('time') == post_time:
                    # Get or initialize reported_by list
                    reported_by = post_data.get('reported_by', [])
                    
                    # Check if user already reported
                    if user_identifier in reported_by:
                        QMessageBox.warning(parent, "Already Reported", "You have already reported this post.")
                        return
                    
                    # Add user to reported_by list
                    reported_by.append(user_identifier)
                    post_data['reported_by'] = reported_by
                    
                    # Update reports count
                    post_data['reports'] = len(reported_by)
                    new_reports = post_data['reports']
                    
                    # Save immediately
                    parent.save_posts()
                    
                    # Check if post should be deleted (10 reports threshold)
                    if new_reports >= 10:
                        # Get post info for logging
                        post_id = self.post_id
                        post_content = self.content[:30] if self.content else "N/A"
                        
                        # Remove the post from all_posts
                        parent.all_posts = [p for p in parent.all_posts if p.get('time') != post_time]
                        parent.save_posts()
                        
                        # Rebuild home.json to remove the post
                        parent._rebuild_home_feed(parent.all_posts)
                        
                        # Log deletion to interactions.json
                        parent.log_interaction('post_deletions', {
                            'post_id': post_id,
                            'content_preview': post_content,
                            'reports': new_reports,
                            'timestamp': get_timestamp()
                        })
                        
                        # Remove from layout
                        for i in range(parent.posts_layout.count()):
                            item = parent.posts_layout.itemAt(i)
                            if item.widget() == self:
                                parent.posts_layout.removeItem(item)
                                self.deleteLater()
                                break
                        
                        QMessageBox.information(parent, "Post Reported", 
                            "This post has been removed due to receiving 10 reports.")
                    else:
                        # Show confirmation with report count
                        QMessageBox.information(parent, "Post Reported", 
                            f"Post reported. ({new_reports}/10 reports)")
                    return
    
    def unreport_post(self):
        """Remove report from this post - toggles off the user's report"""
        # Find the parent FacebookGUI
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        if parent and isinstance(parent, FacebookGUI):
            # Get the post's time identifier
            post_time = self.get_post_time_str()
            
            # Get current user's identifier
            first_name = parent.user_profile.get('first_name', '')
            last_name = parent.user_profile.get('last_name', '')
            user_identifier = f"{first_name} {last_name}".strip()
            
            # Find and update the post in all_posts
            for post_data in parent.all_posts:
                if post_data.get('time') == post_time:
                    # Get reported_by list
                    reported_by = post_data.get('reported_by', [])
                    
                    # Check if user has reported
                    if user_identifier not in reported_by:
                        QMessageBox.warning(parent, "Not Reported", "You haven't reported this post.")
                        return
                    
                    # Remove user from reported_by list
                    reported_by.remove(user_identifier)
                    post_data['reported_by'] = reported_by
                    
                    # Update reports count
                    post_data['reports'] = len(reported_by)
                    new_reports = post_data['reports']
                    
                    # Save immediately
                    parent.save_posts()
                    
                    # Show confirmation with report count
                    QMessageBox.information(parent, "Report Removed", 
                        f"Report removed. ({new_reports}/10 reports)")
                    return
    
    def edit_post(self):
        """Edit this post's content - adds to edit history"""
        # Get the latest edit content (or original if no edits)
        if self.edits:
            current_text = self.edits[-1]['content']
        else:
            current_text = self.content
        
        # Create custom dialog for multi-line editing
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Post")
        dialog.setMinimumSize(500, 300)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Multi-line text input - show latest edit content
        text_edit = QTextEdit()
        text_edit.setText(current_text)
        text_edit.setFont(QFont("Arial", 12))
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f0f2f5;
                border-radius: 8px;
                padding: 8px;
                border: 1px solid #dddfe2;
            }
        """)
        layout.addWidget(text_edit)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("Arial", 11))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                color: #050505;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d8dadf;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setFont(QFont("Arial", 11, QFont.Bold))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #166fe5;
            }
        """)
        save_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        
        # Find parent for showing messages
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        if dialog.exec_() == QDialog.Accepted:
            new_text = text_edit.toPlainText().strip()
            if new_text and new_text != current_text:
                # Check if max edits reached (10 max)
                if len(self.edits) >= 10:
                    if parent and isinstance(parent, FacebookGUI):
                        QMessageBox.warning(parent, "Max Edits", "This post has reached the maximum of 10 edits.")
                    return
                
                # Calculate the new edit number
                edit_num = len(self.edits) + 1
                edit_timestamp = get_timestamp()
                
                # Add to edits history
                self.edits.append({
                    'edit_num': edit_num,
                    'content': new_text,
                    'time': edit_timestamp
                })
                
                # Rebuild the full content display
                self.rebuild_content_display()
                
                # Mark as edited and update header
                self.is_edited = True
                self.rebuild_header()
                
                # Sync edits history to parent for posts.json storage
                self.sync_edit_to_parent()
                
                # Update feed/home.json with latest edit content/timestamp
                self.update_home_feed_with_edit()
                
                # Update edit timestamps in display
                self.refresh_edit_timestamps()
    
    def rebuild_content_display(self):
        """Rebuild the content label with edit history"""
        if not hasattr(self, 'content_label') or not self.content_label:
            return
        
        # Show latest edit content as main content (for bots reading feed/home.json)
        if self.edits:
            main_content = self.edits[-1]['content']
        else:
            main_content = self.content
        
        # Build full content: main content + all edits history
        full_content = main_content
        
        for edit in self.edits:
            edit_time_str = format_time_ago(datetime.strptime(edit['time'], "%Y/%m/%d %H:%M:%S"))
            full_content += f"\n\n[Edit {edit['edit_num']}: {edit['content']} ({edit_time_str})]"
        
        self.content_label.setText(full_content)
    
    def refresh_edit_timestamps(self):
        """Refresh the edit timestamps in the content display"""
        self.rebuild_content_display()
        
        # Also update the post header timestamp to show latest edit time
        if self.edits and hasattr(self, 'time_label'):
            latest_edit_time = self.edits[-1]['time']
            try:
                edit_datetime = datetime.strptime(latest_edit_time, "%Y/%m/%d %H:%M:%S")
                time_text = format_time_ago(edit_datetime)
                if self.is_edited:
                    time_text = f"{time_text} · Edited"
                self.time_label.setText(time_text)
            except ValueError:
                pass
    
    def sync_edit_to_parent(self):
        """Sync edit history to parent FacebookGUI (for posts.json storage)"""
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        if parent and isinstance(parent, FacebookGUI):
            post_time = self._time_str
            for post_data in parent.all_posts:
                if post_data.get('time') == post_time:
                    post_data['edits'] = self.edits
                    post_data['is_edited'] = self.is_edited
                    parent.save_posts()
                    return
    
    def update_home_feed_with_edit(self):
        """Update feed/home.json with latest edit content (without modifying user/posts.json)"""
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        if parent and isinstance(parent, FacebookGUI):
            post_time = self._time_str
            for post_data in parent.all_posts:
                if post_data.get('time') == post_time:
                    # Update feed/home.json only - keep original post timestamp in posts.json
                    # to maintain post_id consistency and avoid duplicate widgets
                    if self.edits:
                        # Set latest edit content as the display content
                        post_data['content'] = self.edits[-1]['content']
                        # DO NOT change the timestamp - it would change the post_id
                        # and cause duplicate widgets when check_for_new_posts runs
                    
                    # Rebuild home.json with updated data
                    parent._rebuild_home_feed(parent.all_posts)
                    return
    
    def update_timestamp(self):
        """Update the timestamp display dynamically"""
        time_text = format_time_ago(self.time)
        if self.is_edited:
            time_text = f"{time_text} · Edited"
        if hasattr(self, 'time_label'):
            self.time_label.setText(time_text)
    
    def rebuild_header(self):
        """Rebuild the post header to show updated time and edited state"""
        # Directly update time_label - don't loop through all widgets (avoids updating username)
        if hasattr(self, 'time_label') and self.time_label:
            if hasattr(self, 'is_edited') and self.is_edited:
                time_text = format_time_ago(self.time)
                if "Edited" not in self.time_label.text():
                    self.time_label.setText(f"{time_text} · Edited")
            else:
                if "Edited" in self.time_label.text():
                    self.time_label.setText(format_time_ago(self.time))
    
    def toggle_comments(self):
        """Toggle the comments section visibility"""
        self.comments_expanded = not self.comments_expanded
        self.comments_container.setVisible(self.comments_expanded)
        self.update_toggle_comments_button()
    
    def update_toggle_comments_button(self):
        """Update the toggle button text based on state"""
        if self.comments_expanded:
            if self.comments_count > 0:
                self.toggle_comments_btn.setText(f"⬆️ Hide comments ({self.comments_count})")
            else:
                self.toggle_comments_btn.setText("⬆️ Hide comments")
        else:
            if self.comments_count > 0:
                self.toggle_comments_btn.setText(f"💬 Show comments ({self.comments_count})")
            else:
                self.toggle_comments_btn.setText("💬 Write a comment...")
    
    def add_comment(self, username, avatar, content, time, comment_id=None):
        """Add a comment to the post"""
        # Generate comment_id if not provided
        if not comment_id:
            comment_id = f"comment_{uuid.uuid4().hex[:8]}"
        
        # Store comment in the comments_list FIRST for persistence
        # This creates the backend data that CommentWidget will reference
        if isinstance(time, datetime):
            time_str = time.strftime("%Y/%m/%d %H:%M:%S")
        else:
            time_str = time
        
        comment_data = {
            'id': comment_id,  # Always set the ID
            'username': username,
            'avatar': avatar,
            'content': content,
            'time': time_str,
            'likes': 0,
            'reacts': [],  # Initialize reacts array for user reactions
            'replies': []  # Initialize replies array for future replies
        }
        self.comments_list.append(comment_data)
        
        # Now create CommentWidget with reference to backend comment data
        comment = CommentWidget(
            username, avatar, content, time, self, 
            comment_id=comment_id,
            likes=0,
            comment_data_ref=comment_data,
            reacts=[],  # Empty for new comments
            current_user=None  # No current user for new comments
        )
        self.comments_list_layout.addWidget(comment)
        self.comments_count += 1
        self.update_reactions_display()
        self.update_toggle_comments_button()
        
        # Save comment to interactions.json (only for user's comments, not random_user)
        parent = self.parent()
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
        
        if parent and isinstance(parent, FacebookGUI):
            # DEBUG: Check if post exists before sync
            post_time = self._time_str
            found_post = None
            for post in parent.all_posts:
                if post.get('time') == post_time:
                    found_post = post
                    break
            
            debug_enabled = getattr(parent, '_debug_enabled', False)
            debug_print(debug_enabled, f"DEBUG add_comment: post_time={post_time}")
            debug_print(debug_enabled, f"DEBUG add_comment: found_post={found_post is not None}")
            if found_post:
                debug_print(debug_enabled, f"DEBUG add_comment: found_post has comments_list={'comments_list' in found_post}")
                debug_print(debug_enabled, f"DEBUG add_comment: found_post comments_list length={len(found_post.get('comments_list', []))}")
            
            # Only save to user/interactions.json if this is a real user's comment
            # Random User comments should NOT be saved here - they go to feed/home.json instead
            if username != 'Random User':
                # Add to interactions list
                interaction_data = {
                    'post_index': len(parent.visible_posts) - 1,
                    'username': username,
                    'content': content,
                    'time': time_str,
                    'timestamp': get_timestamp()
                }
                if 'comments' not in parent.interactions:
                    parent.interactions['comments'] = []
                parent.interactions['comments'].append(interaction_data)
                parent.save_interactions()
            
            # CRITICAL: Also sync the comment to parent.all_posts so it gets saved to posts.json
            # Find the corresponding post in all_posts and update it
            post_time = self._time_str
            debug_print(debug_enabled, f"DEBUG sync: Looking for post with time={post_time}")
            for post in parent.all_posts:
                if post.get('time') == post_time:
                    debug_print(debug_enabled, f"DEBUG sync: Found post!")
                    debug_print(debug_enabled, f"DEBUG sync: post['comments_list'] exists={'comments_list' in post}")
                    debug_print(debug_enabled, f"DEBUG sync: post['comments_list'] id={id(post.get('comments_list', []))}")
                    debug_print(debug_enabled, f"DEBUG sync: self.comments_list id={id(self.comments_list)}")
                    debug_print(debug_enabled, f"DEBUG sync: Same object? {post.get('comments_list') is self.comments_list}")

                    if 'comments_list' not in post:
                        debug_print(debug_enabled, f"DEBUG sync: post doesn't have comments_list, linking to self.comments_list")
                        post['comments_list'] = self.comments_list
                    elif post['comments_list'] is not self.comments_list:
                        # References don't match! This means PostWidget created a new list
                        # Instead of using the one from post data. We need to fix this.
                        debug_print(debug_enabled, f"DEBUG sync: References don't match! Copying comments from self.comments_list to post['comments_list']")
                        # Copy all comments from self.comments_list to post['comments_list']
                        post['comments_list'].clear()
                        post['comments_list'].extend(self.comments_list)
                        debug_print(debug_enabled, f"DEBUG sync: After copy - post['comments_list'] has {len(post['comments_list'])} comments")
                    
                    # CRITICAL: Also sync individual comment's replies arrays!
                    # Each comment in self.comments_list has self.replies_data (CommentWidget's replies)
                    # We need to ensure post['comments_list'] references the same replies lists
                    debug_print(debug_enabled, f"DEBUG sync: Syncing individual comment replies arrays")
                    for i, comment in enumerate(self.comments_list):
                        comment_id = comment.get('id')
                        if i < len(post['comments_list']):
                            post_comment = post['comments_list'][i]
                            # Get the CommentWidget's replies data (if this is a CommentWidget)
                            # We need to find the matching CommentWidget to get its replies_data
                            for j in range(self.comments_list_layout.count()):
                                item = self.comments_list_layout.itemAt(j)
                                if item.widget() and hasattr(item.widget(), 'replies_data'):
                                    cw = item.widget()
                                    if hasattr(cw, 'comment_id') and cw.comment_id == comment_id:
                                        # Found the CommentWidget! Sync its replies_data
                                        if post_comment.get('replies') is not cw.replies_data:
                                            debug_print(debug_enabled, f"DEBUG sync: Syncing replies for comment {comment_id}")
                                            debug_print(debug_enabled, f"DEBUG sync:   Before - post_comment['replies'] id={id(post_comment.get('replies', []))}")
                                            debug_print(debug_enabled, f"DEBUG sync:   Before - cw.replies_data id={id(cw.replies_data)}")
                                            post_comment['replies'] = cw.replies_data
                                            debug_print(debug_enabled, f"DEBUG sync:   After - Now pointing to same list!")
                                        break

                    debug_print(debug_enabled, f"DEBUG sync: After check - post['comments_list'] id={id(post['comments_list'])}")
                    debug_print(debug_enabled, f"DEBUG sync: self.comments_list id={id(self.comments_list)}")
                    debug_print(debug_enabled, f"DEBUG sync: Now same object? {post['comments_list'] is self.comments_list}")

                    # DON'T append here - self.comments_list ALREADY points to the same list
                    # (Python objects are passed by reference)
                    # Just update the comment count
                    post['comments'] = self.comments_count
                    debug_print(debug_enabled, f"DEBUG: Added comment to post {post_time}")
                    break
            
            # Save to posts.json and rebuild home.json (skip during initial loading to avoid infinite loop)
            if not getattr(parent, '_loading_posts', False):
                debug_print(MASTER_DEBUG_ENABLED, f"\n[DEBUG add_comment] Saving comment to backend")
                debug_print(MASTER_DEBUG_ENABLED, f"  - comment by: {username}")
                debug_print(MASTER_DEBUG_ENABLED, f"  - content: {content[:50]}...")
                
                parent.save_posts()
                # Rebuild home.json to include the new comment (only if not already rebuilding)
                if not getattr(parent, '_rebuilding_feed', False):
                    parent._rebuild_home_feed(parent.all_posts)
            else:
                debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG add_comment: Skipped save (loading posts)")
    
    def add_comment_from_input(self):
        """Add a comment from the comment input field"""
        content = self.comment_input.toPlainText().strip()
        if content:
            # Get user's actual name from profile
            parent = self.parent()
            while parent and not isinstance(parent, FacebookGUI):
                parent = parent.parent()
            
            if parent and isinstance(parent, FacebookGUI):
                profile = getattr(parent, 'user_profile', {})
                first_name = profile.get('first_name', '')
                last_name = profile.get('last_name', '')
                username = f"{first_name} {last_name}".strip() if first_name or last_name else 'You'
            else:
                username = 'You'
            
            self.add_comment(username, "👤", content, datetime.now())
            self.comment_input.clear()
    
    def update_comment_timestamps(self):
        """Update timestamps in all comments"""
        for i in range(self.comments_list_layout.count()):
            item = self.comments_list_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), CommentWidget):
                item.widget().update_timestamp()
                # Also update replies recursively
                item.widget().update_comment_timestamps()
    
    def on_like_clicked(self):
        # Toggle between showing reactions and liking
        if self.reaction_bar.isVisible():
            self.reaction_bar.setVisible(False)
        else:
            self.reaction_bar.setVisible(True)
    
    def on_comment_clicked(self):
        self.comment_input.setFocus()
    
    def on_share_clicked(self):
        # Show share options dialog
        self.show_share_dialog()
    
    def show_share_dialog(self):
        dialog = QMessageBox()
        dialog.setWindowTitle("Share")
        dialog.setText("Choose how you want to share")
        dialog.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                border: 1px solid #dddfe2;
                background-color: #f0f2f5;
            }
        """)
        
        repost_btn = QPushButton("🔄 Repost")
        repost_btn.clicked.connect(lambda: self.handle_share("repost"))
        dialog.addButton(repost_btn, QMessageBox.ActionRole)
        
        quote_btn = QPushButton("💬 Quote")
        quote_btn.clicked.connect(lambda: self.handle_share("quote"))
        dialog.addButton(quote_btn, QMessageBox.ActionRole)
        
        share_btn = QPushButton("👤 Share to friend")
        share_btn.clicked.connect(lambda: self.handle_share("friend"))
        dialog.addButton(share_btn, QMessageBox.ActionRole)
        
        # Add Close/Cancel button
        close_btn = QPushButton("✕ Close")
        dialog.addButton(close_btn, QMessageBox.RejectRole)
        
        dialog.exec_()
    
    def handle_share(self, share_type):
        # Get the FacebookGUI instance
        parent_window = self
        while parent_window and not isinstance(parent_window, FacebookGUI):
            parent_window = parent_window.parent()
        
        if not parent_window or not isinstance(parent_window, FacebookGUI):
            return
        
        # Get original post data - include all post values like social media apps
        original_username = self.username
        original_avatar = self.avatar
        original_content = ""
        if self.content_label:
            original_content = self.content_label.text()
        
        original_post_data = {
            'username': original_username,
            'avatar': original_avatar,
            'content': original_content,
            'time': self.time,  # Use the stored time, not current timestamp
            'likes': self.likes_count,
            'comments': self.comments_count,
            'shares': self.shares_count,
            'reacts': []  # Individual reaction records
        }
        
        if share_type == "repost":
            # CRITICAL: Update shares count BEFORE add_shared_post calls save_posts()
            self.shares_count += 1
            self.update_reactions_display()

            # Update shares in all_posts
            post_time = self._time_str
            for post in parent_window.all_posts:
                if post.get('time') == post_time:
                    post['shares'] = self.shares_count
                    break

            # Create a repost - "You shared a post" with embedded original
            parent_window.add_shared_post(
                username="You",
                emoji="🔄",
                content="You shared a post",
                embedded_post=original_post_data
            )

            # Save share to interactions.json
            share_data = {
                'type': 'repost',
                'original_username': original_username,
                'original_content_preview': original_content[:50],
                'timestamp': get_timestamp()
            }
            if 'shares' not in parent_window.interactions:
                parent_window.interactions['shares'] = []
            parent_window.interactions['shares'].append(share_data)
            parent_window.save_interactions()

        elif share_type == "quote":
            # Show dialog to get user's quote text
            dialog = QuoteDialog(original_username, original_content, self)
            if dialog.exec_() == QDialog.Accepted:
                user_quote = dialog.get_quote()
                if user_quote:
                    # CRITICAL: Update shares count BEFORE add_shared_post calls save_posts()
                    self.shares_count += 1
                    self.update_reactions_display()

                    post_time = self._time_str
                    for post in parent_window.all_posts:
                        if post.get('time') == post_time:
                            post['shares'] = self.shares_count
                            break

                    # Now create the quote (this will call save_posts which will save the updated shares)
                    parent_window.add_shared_post(
                        username="You",
                        emoji="💬",
                        content=user_quote,
                        embedded_post=original_post_data,
                        is_quote=True  # Flag to show "Original" button
                    )

                    # Save share to interactions.json
                    share_data = {
                        'type': 'quote',
                        'original_username': original_username,
                        'original_content_preview': original_content[:50],
                        'user_quote': user_quote,
                        'timestamp': get_timestamp()
                    }
                    if 'shares' not in parent_window.interactions:
                        parent_window.interactions['shares'] = []
                    parent_window.interactions['shares'].append(share_data)
                    parent_window.save_interactions()
                
        elif share_type == "friend":
            print(f"Sharing {self.username}'s post to friend")
            self.shares_count += 1
            self.update_reactions_display()
            
            # Save share to interactions.json
            share_data = {
                'type': 'friend',
                'original_username': original_username,
                'original_content_preview': original_content[:50],
                'timestamp': get_timestamp()
            }
            if 'shares' not in parent_window.interactions:
                parent_window.interactions['shares'] = []
            parent_window.interactions['shares'].append(share_data)
            parent_window.save_interactions()
    
    def add_reaction(self, emoji):
        """Add or toggle a reaction on this post - for USER actions only"""
        # Debug flag - set to True to enable detailed logging
        DEBUG_USER_POST_REACTION = False
        
        import traceback
        
        def log(*args, **kwargs):
            if DEBUG_USER_POST_REACTION:
                print(*args, **kwargs)
        
        log(f"\n{'='*80}")
        log(f"[USER POST REACTION] ===== START =====")
        log(f"[USER POST REACTION] Post ID: {getattr(self, 'post_id', 'unknown')}")
        log(f"[USER POST REACTION] Emoji selected: '{emoji}'")
        log(f"[USER POST REACTION] Current user_reaction (widget): {self.user_reaction}")
        log(f"[USER POST REACTION] Current likes_count (widget): {self.likes_count}")
        log(f"[USER POST REACTION] Post content preview: {self.content[:80] if self.content else 'N/A'}...")
        
        # Toggle reaction - if same reaction, remove it; otherwise replace it
        if self.user_reaction == emoji:
            self.user_reaction = None
            self.likes_count = max(0, self.likes_count - 1)
            reaction_type = "remove"
            log(f"[USER POST REACTION] ACTION: REMOVE reaction (clicked same emoji)")
        else:
            # If there was a different reaction, replace it (don't double count)
            if self.user_reaction is not None:
                # Keep the same count, just change the emoji
                reaction_type = "change"
                log(f"[USER POST REACTION] ACTION: CHANGE reaction from '{self.user_reaction}' to '{emoji}'")
            else:
                self.likes_count += 1
                reaction_type = "add"
                log(f"[USER POST REACTION] ACTION: ADD new reaction '{emoji}'")
            self.user_reaction = emoji
        
        log(f"[USER POST REACTION] After toggle - user_reaction: {self.user_reaction}, likes_count: {self.likes_count}")
        self.update_reactions_display()
        log(f"[USER POST REACTION] Updated reactions display on widget")
        
        # Find parent FacebookGUI
        log(f"[USER POST REACTION] Looking for FacebookGUI parent...")
        parent = self.parent()
        depth = 0
        while parent and not isinstance(parent, FacebookGUI):
            parent = parent.parent()
            depth += 1
            if depth > 10:
                log(f"[USER POST REACTION] ✗ Parent search exceeded depth limit!")
                break
        
        if parent and isinstance(parent, FacebookGUI):
            log(f"[USER POST REACTION] ✓ Found FacebookGUI parent at depth {depth}")
                
            # Get user profile info
            profile = getattr(parent, 'user_profile', {})
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            current_user = f"{first_name} {last_name}".strip() if first_name or last_name else 'You'
            log(f"[USER POST REACTION] Current user: '{current_user}'")
                
            # Get post identifiers
            post_time = getattr(self, '_time_str', None)
            post_id = getattr(self, 'post_id', None)
            log(f"[USER POST REACTION] Post identifiers - ID: {post_id}, Time: {post_time}")
                
            # Check all_posts structure
            log(f"[USER POST REACTION] all_posts count: {len(parent.all_posts)}")
            log(f"[USER POST REACTION] all_posts type: {type(parent.all_posts)}")
                
            # Show first few posts to verify structure
            if parent.all_posts:
                sample_post = parent.all_posts[0] if len(parent.all_posts) > 0 else {}
                log(f"[USER POST REACTION] Sample post keys: {list(sample_post.keys()) if isinstance(sample_post, dict) else 'N/A'}")
                
            # Find and update the post in all_posts
            post_updated = False
            post_index = -1
            found_post = None
                
            log(f"[USER POST REACTION] Searching for post in all_posts...")
            for idx, post in enumerate(parent.all_posts):
                if not isinstance(post, dict):
                    log(f"[USER POST REACTION]   Skip: index {idx} is {type(post)}, not dict")
                    continue
                        
                # Match by post_id first
                if post_id and post.get('id') == post_id:
                    post_index = idx
                    found_post = post
                    log(f"[USER POST REACTION] ✓ FOUND POST at index {idx} by ID: {post_id}")
                    break
                # Fallback to time match
                elif post_time and post.get('time') == post_time:
                    post_index = idx
                    found_post = post
                    log(f"[USER POST REACTION] ✓ FOUND POST at index {idx} by TIME: {post_time}")
                    break
            
            if found_post:
                log(f"[USER POST REACTION] Found post at index {post_index}")
                log(f"[USER POST REACTION] Before update - post['id']: {found_post.get('id')}")
                log(f"[USER POST REACTION] Before update - post['likes']: {found_post.get('likes')}")
                log(f"[USER POST REACTION] Before update - post['reacts']: {found_post.get('reacts')}")
                log(f"[USER POST REACTION] Before update - post['time']: {found_post.get('time')}")
                log(f"[USER POST REACTION] Before update - post.get('reacts') type: {type(found_post.get('reacts'))}")
                    
                # Initialize reacts array if not exists
                if 'reacts' not in found_post:
                    found_post['reacts'] = []
                    log(f"[USER POST REACTION]   Initialized empty reacts[] array")
                else:
                    log(f"[USER POST REACTION]   reacts[] already exists with {len(found_post['reacts'])} items")
                
                # Check if user already reacted
                existing_reaction = None
                existing_reaction_idx = -1
                for idx, r in enumerate(found_post['reacts']):
                    if isinstance(r, dict) and r.get('username') == current_user:
                        existing_reaction = r
                        existing_reaction_idx = idx
                        break
                
                log(f"[USER POST REACTION] Existing reaction for '{current_user}': {existing_reaction} at index {existing_reaction_idx}")
                log(f"[USER POST REACTION] Processing reaction_type: '{reaction_type}'")
                
                # Process the reaction based on type
                if reaction_type == "remove":
                    if existing_reaction_idx >= 0:
                        removed = found_post['reacts'].pop(existing_reaction_idx)
                        log(f"[USER POST REACTION]   ✓ Removed reaction at index {existing_reaction_idx}: {removed}")
                    else:
                        log(f"[USER POST REACTION]   ✗ Cannot remove - no existing reaction found!")
                
                elif reaction_type == "change":
                    if existing_reaction_idx >= 0:
                        removed = found_post['reacts'].pop(existing_reaction_idx)
                        log(f"[USER POST REACTION]   ✓ Removed old reaction: {removed}")
                            
                        new_reaction = {
                            'username': current_user,
                            'emoji': emoji,
                            'timestamp': get_timestamp()
                        }
                        found_post['reacts'].append(new_reaction)
                        log(f"[USER POST REACTION]   ✓ Added new reaction: {new_reaction}")
                    else:
                        log(f"[USER POST REACTION]   ✗ Cannot change - no existing reaction found!")
                
                elif reaction_type == "add":
                    if existing_reaction_idx < 0:
                        new_reaction = {
                            'username': current_user,
                            'emoji': emoji,
                            'timestamp': get_timestamp()
                        }
                        found_post['reacts'].append(new_reaction)
                        log(f"[USER POST REACTION]   ✓ Added new reaction: {new_reaction}")
                    else:
                        log(f"[USER POST REACTION]   ✗ Cannot add - user already reacted! Existing: {found_post['reacts'][existing_reaction_idx]}")
                
                # Update likes count in post (increment/decrement, NOT based on len(reacts))
                # This preserves random_user's likes count
                old_likes = found_post.get('likes', 0)
                if reaction_type == "add":
                    new_likes = old_likes + 1
                elif reaction_type == "remove":
                    new_likes = max(0, old_likes - 1)
                elif reaction_type == "change":
                    new_likes = old_likes  # Same count, just different emoji
                else:
                    new_likes = old_likes
                
                found_post['likes'] = new_likes
                log(f"[USER POST REACTION]   Updated post['likes']: {old_likes} → {new_likes}")
                
                log(f"[USER POST REACTION] After update - post['reacts']: {found_post['reacts']}")
                log(f"[USER POST REACTION] After update - post['likes']: {found_post.get('likes')}")
                
                post_updated = True
                
                # CRITICAL: Verify the update in all_posts
                verify_post = parent.all_posts[post_index]
                log(f"[USER POST REACTION] Verification - all_posts[{post_index}]['reacts']: {verify_post.get('reacts')}")
                log(f"[USER POST REACTION] Verification - all_posts[{post_index}]['likes']: {verify_post.get('likes')}")
                
                # Check if all_posts is the same object reference
                log(f"[USER POST REACTION] Verification - found_post is all_posts[{post_index}]: {found_post is verify_post}")
            
            else:
                log(f"[USER POST REACTION] ✗ POST NOT FOUND in all_posts!")
                log(f"[USER POST REACTION]   Searched for post_id: {post_id}, post_time: {post_time}")
                log(f"[USER POST REACTION]   Available posts:")
                for idx, p in enumerate(parent.all_posts[:5]):
                    if isinstance(p, dict):
                        log(f"[USER POST REACTION]     [{idx}] id={p.get('id')}, time={p.get('time')}, likes={p.get('likes')}")
                    else:
                        log(f"[USER POST REACTION]     [{idx}] type={type(p)}")
            
            if post_updated:
                # CRITICAL: Save to posts.json
                log(f"[USER POST REACTION] Saving to posts.json...")
                log(f"[USER POST REACTION]   parent.all_posts count: {len(parent.all_posts)}")
                    
                # Construct the posts file path (same as save_posts uses)
                base_dir = os.path.dirname(os.path.abspath(__file__))
                posts_file = os.path.join(base_dir, "user", "posts.json")
                log(f"[USER POST REACTION]   Posts file path: {posts_file}")
                
                try:
                    parent.save_posts()
                    log(f"[USER POST REACTION] ✓ Successfully saved posts.json")
                        
                    # Verify the file was saved correctly
                    if os.path.exists(posts_file):
                        file_size = os.path.getsize(posts_file)
                        log(f"[USER POST REACTION]   File exists, size: {file_size} bytes")
                    else:
                        log(f"[USER POST REACTION]   ✗ File does not exist after save!")
                except Exception as e:
                    log(f"[USER POST REACTION] ✗ Failed to save posts.json: {e}")
                    traceback.print_exc()
                
                # Rebuild home.json
                log(f"[USER POST REACTION] Rebuilding home.json...")
                try:
                    parent._rebuild_home_feed(parent.all_posts)
                    log(f"[USER POST REACTION] ✓ Successfully rebuilt home.json")
                except Exception as e:
                    log(f"[USER POST REACTION] ✗ Failed to rebuild home.json: {e}")
                    traceback.print_exc()
            else:
                log(f"[USER POST REACTION] ✗ SKIPPED SAVE - post was not updated!")
            
            # Save reaction to interactions.json
            log(f"[USER POST REACTION] Saving to interactions.json...")
            reaction_data = {
                'username': 'You',
                'emoji': emoji,
                'action': reaction_type,
                'post_content_preview': self.content[:50] if self.content else '',
                'timestamp': get_timestamp()
            }
            if 'likes' not in parent.interactions:
                parent.interactions['likes'] = []
            parent.interactions['likes'].append(reaction_data)
            parent.save_interactions()
            log(f"[USER POST REACTION] ✓ Saved to interactions.json: {reaction_data}")
        else:
            log(f"[USER POST REACTION] ✗ FacebookGUI parent not found!")
            log(f"[USER POST REACTION]   Self parent: {self.parent()}")
            log(f"[USER POST REACTION]   Depth searched: {depth}")
        
        log(f"[USER POST REACTION] ===== END =====")
        log(f"{'='*80}\n")


class FacebookGUI(QMainWindow):
    # Signal for thread-safe feed updates from RandomUserEngine
    refresh_feed_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Set base directory for all file operations
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.setWindowTitle("Facebook")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        self.create_header()
        main_layout.addWidget(self.header)
        
        # Content area
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Left sidebar
        left_panel = QWidget()
        left_panel.setFixedWidth(200)
        left_panel.setStyleSheet("background-color: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        left_items = ["🏠 Home", "💬 Messages", "👥 Groups"]
        for item in left_items:
            btn = QPushButton(item)
            btn.setFont(QFont("Arial", 14))
            btn.setStyleSheet("""
                QPushButton {
                    color: #1c1e21;
                    border: none;
                    background: transparent;
                    padding: 8px 12px;
                    text-align: left;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #d8dadf;
                }
            """)
            if "Home" in item:
                btn.clicked.connect(self.scroll_to_top)
            left_layout.addWidget(btn)
        
        left_layout.addStretch()
        content_layout.addWidget(left_panel)
        
        # Feed
        self.feed_layout = QVBoxLayout()
        self.feed_layout.setSpacing(20)
        
        # Create post area
        self.create_post_area()
        self.feed_layout.addWidget(self.post_area)
        
        # Posts scroll area
        self.posts_scroll = QScrollArea()
        self.posts_scroll.setWidgetResizable(True)
        self.posts_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.posts_container = QWidget()
        self.posts_layout = QVBoxLayout(self.posts_container)
        self.posts_layout.setSpacing(15)
        self.posts_layout.addStretch()
        
        self.posts_scroll.setWidget(self.posts_container)
        self.feed_layout.addWidget(self.posts_scroll)
        
        content_layout.addLayout(self.feed_layout)
        
        # Right sidebar
        right_panel = QWidget()
        right_panel.setFixedWidth(200)
        right_panel.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # Friends section
        friends_label = QLabel("Friends")
        friends_label.setFont(QFont("Arial", 14, QFont.Bold))
        friends_label.setStyleSheet("color: #65676b;")
        right_layout.addWidget(friends_label)
        
        # Friends list will be populated dynamically
        no_friends_label = QLabel("No friends yet")
        no_friends_label.setFont(QFont("Arial", 12))
        no_friends_label.setStyleSheet("color: #65676b;")
        no_friends_label.setContentsMargins(8, 4, 0, 0)
        right_layout.addWidget(no_friends_label)
        
        right_layout.addStretch()
        content_layout.addWidget(right_panel)
        
        main_layout.addLayout(content_layout)
        
        # Load settings from feed.json
        self.feed_settings = self.load_feed_settings()
        
        # Initialize timestamp update timer (from settings)
        self.timestamp_timer = QTimer()
        self.timestamp_timer.timeout.connect(self.update_all_timestamps)
        self.timestamp_timer.start(self.feed_settings.get('timestamp_update_interval', 60) * 1000)
        
        # Navigation stack for "Original" post navigation
        self.navigation_stack = []
        self.original_post_widget = None
        self.back_btn = None
        self.profile_widget = None
        self.search_widget = None
        
        # Infinite scroll configuration
        self.visible_posts = []  # Track currently visible posts
        self.post_widget_registry = {}  # CRITICAL: Registry of PostWidgets by post_id for O(1) UI updates
        self.posts_per_load = self.feed_settings.get('feed_cache_size', 30)
        self.posts_per_batch = self.feed_settings.get('posts_per_batch', 10)
        self.top_posts_cleanup = self.feed_settings.get('top_posts_cleanup', 5)
        
        # Load user profile
        self.user_profile = self.load_user_profile()
        
        # IMPORTANT: Initialize flags BEFORE load_posts() as it calls _rebuild_home_feed
        # Flag to prevent re-entrant calls to _rebuild_home_feed (avoids infinite loops)
        self._rebuilding_feed = False
        
        # Flag to skip save/rebuild during initial post loading (prevents infinite loop when loading existing comments)
        self._loading_posts = False
        
        # Debug flag to control verbose logging (set to True for debugging, False for production)
        self._debug_verbose = False  # Set to True to enable verbose debug logs

        # Master debug flag - controls all DEBUG print statements (set to False to disable)
        self._debug_enabled = False  # Master switch for all debug output

        # Load posts from posts.json
        self.all_posts = self.load_posts()
        
        # Track which post IDs are currently displayed in the GUI
        self.displayed_post_ids = set()
        
        # Setup timer to monitor for new posts from agent
        self.feed_monitor_timer = QTimer()
        self.feed_monitor_timer.setInterval(2000)  # Check every 2 seconds
        self.feed_monitor_timer.timeout.connect(self.check_for_new_posts)
        self.feed_monitor_timer.start()
        print("FacebookGUI: Started feed monitor timer (checks every 2 seconds)")
        
        # Connect scroll signal for infinite scroll
        self.posts_scroll.verticalScrollBar().valueChanged.connect(self.on_scroll_changed)
        
        # Load interactions from interactions.json
        self.interactions = self.load_interactions()
        
        # Load blocked users list
        self.blocked_users = self.load_blocked()
        
        # Initial post load
        self.load_initial_posts()
        
        # Live update timer (from settings)
        self.live_update_timer = QTimer()
        self.live_update_timer.timeout.connect(self.handle_live_updates)
        self.live_update_timer.start(self.feed_settings.get('live_update_interval', 10) * 1000)
        
        # Load profile feed settings
        self.profile_feed_settings = self.load_profile_feed_settings()
        
        # Load search settings
        self.search_settings = self.load_search_settings()
        
        # Initialize notification badge
        self.update_notification_badge()
        
        # Initialize Random User Engine
        self.random_user_engine = None
        self.random_user_timer = QTimer()
        self.random_user_timer.timeout.connect(self.run_random_user_session)
        # Run every 60 seconds by default
        self.random_user_timer.start(60000)
        print("RandomUserEngine: Timer started (every 60 seconds)")
        
        # Initialize the engine immediately
        self.init_random_user_engine()
    
    def load_profile_feed_settings(self):
        """Load profile feed settings from system/algorithms/profiles_feed.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        profiles_feed_json_path = os.path.join(base_dir, "system", "algorithms", "profiles_feed.json")
        
        default_settings = {
            "profile_cache_size": 30,
            "profile_posts_per_batch": 10,
            "profile_top_cleanup": 5
        }
        
        if os.path.exists(profiles_feed_json_path):
            try:
                with open(profiles_feed_json_path, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults
                    for key in default_settings:
                        if key not in settings:
                            settings[key] = default_settings[key]
                    return settings
            except:
                pass
        
        return default_settings
    
    def load_search_settings(self):
        """Load search settings from system/algorithms/search.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        search_json_path = os.path.join(base_dir, "system", "algorithms", "search.json")
        
        default_settings = {
            "main_feed": {
                "max_results": 100,
                "include_comments": False,
                "include_replies": False,
                "sort_by": "likes"
            },
            "profile_feed": {
                "max_results": 30,
                "sort_by": "likes"
            }
        }
        
        if os.path.exists(search_json_path):
            try:
                with open(search_json_path, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults
                    if "main_feed" not in settings:
                        settings["main_feed"] = default_settings["main_feed"]
                    if "profile_feed" not in settings:
                        settings["profile_feed"] = default_settings["profile_feed"]
                    return settings
            except:
                pass
        
        return default_settings
    
    def search_posts(self, query, include_comments=False, include_replies=False, max_results=100, sort_by="likes"):
        """
        Search posts by content
        Returns posts containing the search query, sorted by likes
        """
        if not query:
            return []
        
        query_lower = query.lower()
        results = []
        
        for post_data in self.all_posts:
            # Check if query is in post content
            content = post_data.get('content', '').lower()
            if query_lower in content:
                results.append(post_data)
        
        # Filter out posts from blocked users
        results = self.filter_blocked_posts(results)
        
        # Sort by likes (highest first)
        results.sort(key=lambda x: x.get('likes', 0), reverse=True)
        
        # Limit results
        return results[:max_results]
    
    def search_profile_posts(self, query, profile_folder=None, max_results=30, sort_by="likes"):
        """
        Search posts within a specific profile by content.
        Returns posts containing the search query, sorted by likes.
        
        Args:
            query: Search term
            profile_folder: The profile folder to search in (None/"user" for main user, folder name for agents)
            max_results: Maximum number of results to return
            sort_by: Sort order (default: "likes")
        """
        if not query:
            return []
        
        # Determine the username to search for based on profile_folder
        if profile_folder is None or profile_folder == "user":
            # Main user's posts
            first_name = self.user_profile.get('first_name', '')
            last_name = self.user_profile.get('last_name', '')
            target_username = f"{first_name} {last_name}".strip()
        else:
            # Other user's posts - get from their profile
            other_profile = self.load_any_profile(profile_folder)
            if other_profile:
                first_name = other_profile.get('first_name', '')
                last_name = other_profile.get('last_name', '')
                target_username = f"{first_name} {last_name}".strip()
            else:
                target_username = ""
        
        query_lower = query.lower()
        results = []
        
        for post_data in self.all_posts:
            # Must be target user's post and contain query
            if post_data.get('username', '') == target_username:
                content = post_data.get('content', '').lower()
                if query_lower in content:
                    results.append(post_data)
        
        # Sort by likes (highest first)
        if sort_by == "likes":
            results.sort(key=lambda x: x.get('likes', 0), reverse=True)
        elif sort_by == "time":
            results.sort(key=lambda x: x.get('time', ''), reverse=True)
        
        # Limit results
        return results[:max_results]
    
    def load_feed_settings(self):
        """Load feed settings from system/algorithms/home_feed.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        home_feed_json_path = os.path.join(base_dir, "system", "algorithms", "home_feed.json")
        
        default_settings = {
            "live_update_interval": 10,
            "timestamp_update_interval": 60,
            "feed_cache_size": 30,
            "posts_per_batch": 10,
            "top_posts_cleanup": 5,
            "post_visibility_tiers": {
                "tier1": {
                    "name": "Fresh Posts",
                    "min_likes": 0,
                    "max_days": 3,
                    "description": "All posts from the last 3 days"
                },
                "tier2": {
                    "name": "Trending Posts",
                    "min_likes": 10,
                    "max_days": 7,
                    "description": "Posts with 10+ likes from the last 7 days"
                },
                "tier3": {
                    "name": "Popular Posts",
                    "min_likes": 50,
                    "max_days": 21,
                    "description": "Posts with 50+ likes from the last 21 days"
                },
                "tier4": {
                    "name": "Viral Posts",
                    "min_likes": 100,
                    "max_days": 30,
                    "description": "Posts with 100+ likes from the last 30 days"
                }
            }
        }
        
        if os.path.exists(home_feed_json_path):
            try:
                with open(home_feed_json_path, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults
                    for key in default_settings:
                        if key not in settings:
                            settings[key] = default_settings[key]
                    return settings
            except:
                pass
        
        return default_settings
    
    def is_post_visible(self, post_data):
        """Check if a post meets the visibility criteria based on post_visibility_tiers"""
        settings = self.load_feed_settings()
        tiers = settings.get("post_visibility_tiers", {})
        
        # Parse post timestamp
        time_str = post_data.get('time', '')
        if isinstance(time_str, str):
            try:
                post_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                return True  # If timestamp is invalid, show the post
        else:
            return True  # If timestamp is not a string, show the post
        
        # Get current time and calculate post age in days
        now = datetime.now()
        delta = now - post_time
        post_age_days = delta.total_seconds() / 86400  # Convert seconds to days
        
        # Get post likes
        likes = post_data.get('likes', 0)
        
        # Check each tier - post is visible if it matches ANY tier's criteria
        for tier_key, tier_config in tiers.items():
            min_likes = tier_config.get("min_likes", 0)
            max_days = tier_config.get("max_days", 3)
            
            # Check if post meets both like and age criteria for this tier
            if likes >= min_likes and post_age_days <= max_days:
                return True
        
        # Post doesn't match any tier's criteria
        return False
    
    def load_home_feed(self):
        """Load the home.json feed file"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        home_feed_path = os.path.join(base_dir, "system", "feed", "home.json")
        
        if os.path.exists(home_feed_path):
            try:
                with open(home_feed_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Return default structure if file doesn't exist
        return {
            "meta": {
                "last_updated": get_timestamp(),
                "feed_count": 0,
                "rules_source": "system/algorithms/home_feed.json"
            },
            "posts": [],
            "reactions": []
        }
    
    def save_home_feed(self, home_data):
        """Save the home.json feed file"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        home_feed_path = os.path.join(base_dir, "system", "feed", "home.json")
        
        # Update meta timestamp
        home_data["meta"]["last_updated"] = get_timestamp()
        home_data["meta"]["feed_count"] = len(home_data.get("posts", []))
        
        with open(home_feed_path, 'w') as f:
            json.dump(home_data, f, indent=2)
    
    def add_to_home_feed(self, entry_type, entry_data):
        """Add an entry to the home.json feed"""
        home_data = self.load_home_feed()
        
        # Add timestamp if not present
        if "timestamp" not in entry_data:
            entry_data["timestamp"] = get_timestamp()
        
        # Add unique ID if not present
        if "id" not in entry_data:
            import uuid
            entry_data["id"] = f"{entry_type}_{uuid.uuid4().hex[:8]}"
        
        # Add entry to appropriate list
        if entry_type in ["post", "comment"]:
            home_data[entry_type + "s"].append(entry_data)  # posts, comments
        
        # Save and cleanup old entries
        self.save_home_feed(home_data)
        self.cleanup_home_feed()
    
    def cleanup_home_feed(self):
        """Remove old entries from home.json based on home_feed.json rules"""
        home_data = self.load_home_feed()
        settings = self.load_feed_settings()
        tiers = settings.get("post_visibility_tiers", {})
        
        # Calculate max age from all tiers (use the highest max_days)
        max_age_days = 0
        for tier_config in tiers.values():
            max_days = tier_config.get("max_days", 30)
            max_age_days = max(max_age_days, max_days)
        
        # Maximum total entries to keep
        max_entries = 500
        now = datetime.now()
        
        # Filter posts
        valid_posts = []
        for post in home_data.get("posts", []):
            time_str = post.get('timestamp', '')
            if isinstance(time_str, str):
                try:
                    post_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
                    post_age_days = (now - post_time).total_seconds() / 86400
                    
                    # Keep if within max age
                    if post_age_days <= max_age_days:
                        valid_posts.append(post)
                except ValueError:
                    # If can't parse, keep the post
                    valid_posts.append(post)
            else:
                valid_posts.append(post)
        
        # If still over max_entries, apply visibility tiers
        if len(valid_posts) > max_entries:
            visible_posts = [p for p in valid_posts if self.is_post_visible(p)]
            # If still over limit, keep newest
            if len(visible_posts) > max_entries:
                valid_posts = visible_posts[:max_entries]
        
        home_data["posts"] = valid_posts
        
        self.save_home_feed(home_data)
    
    def get_randomized_feed_for_random_user(self, count=30):
        """Get a randomized selection of feed entries for random_user context"""
        home_data = self.load_home_feed()
        config = self.load_random_user_config()
        
        # Get distribution settings
        feed_distribution = config.get("algorithm", {}).get("feed_distribution", {})
        newest_ratio = feed_distribution.get("newest_posts", 50) / 100
        viral_ratio = feed_distribution.get("viral_posts", 30) / 100
        random_ratio = feed_distribution.get("random_older", 20) / 100
        
        posts = home_data.get("posts", [])
        
        if not posts:
            return []
        
        # Sort by timestamp (newest first)
        sorted_posts = sorted(posts, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Split into categories
        newest_count = int(count * newest_ratio)
        viral_count = int(count * viral_ratio)
        random_count = count - newest_count - viral_count
        
        # Get newest posts
        selected_posts = sorted_posts[:newest_count]
        
        # Get viral posts (highest likes)
        if viral_count > 0 and len(sorted_posts) > newest_count:
            remaining = sorted_posts[newest_count:]
            # Sort by likes descending
            viral_posts = sorted(remaining, key=lambda x: x.get('likes', 0), reverse=True)
            selected_posts.extend(viral_posts[:viral_count])
        
        # Get random older posts
        if random_count > 0 and len(sorted_posts) > len(selected_posts):
            already_selected = set(p.get("id") for p in selected_posts)
            older_posts = [p for p in sorted_posts if p.get("id") not in already_selected]
            if older_posts:
                import random
                selected_posts.extend(random.sample(older_posts, min(random_count, len(older_posts))))
        
        return selected_posts[:count]
    
    def load_random_user_config(self):
        """Load random_user config.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "system", "random_user", "config.json")
        
        default_config = {
            "traffic_control": {
                "actions_per_minute": 3,
                "actions_per_cent": 65,
                "feed_read": 30
            },
            "interactions": {
                "post_reactions": 9,
                "repost_post": 2,
                "quote_post": 1,
                "make_post": 3,
                "comment_post": 6,
                "reply_comment": 5,
                "react_comment": 7
            },
            "algorithm": {
                "feed_distribution": {
                    "newest_posts": 50,
                    "viral_posts": 30,
                    "random_older": 20
                },
                "response_options": {
                    "min_actions_per_call": 1,
                    "max_actions_per_call": 15,
                    "prefer_variety": True
                }
            },
            "prompts": {
                "system_prompt": "You are a user on a social network platform.",
                "role_prompt": "Act as a social media user who is casually browsing their feed."
            }
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
            except:
                pass
        
        return default_config
    
    def load_random_user_tools(self):
        """Load random_user tools.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        tools_path = os.path.join(base_dir, "system", "random_user", "tools.json")
        
        if os.path.exists(tools_path):
            try:
                with open(tools_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return []
    
    def load_platform_description(self):
        """Load platform description for context"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        desc_path = os.path.join(base_dir, "system", "platform", "description.json")
        
        if os.path.exists(desc_path):
            try:
                with open(desc_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return []
    
    def load_user_profile(self):
        """Load user profile from user/profile.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        profile_path = os.path.join(base_dir, "user", "profile.json")
        
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {"first_name": "User", "last_name": ""}
    
    def load_any_profile(self, folder_name):
        """Load profile from agents/friends/{folder_name}/profile.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        profile_path = os.path.join(base_dir, "agents", "friends", folder_name, "profile.json")
        
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return None
    
    def load_followers(self, folder_name):
        """Load followers list from agents/friends/{folder_name}/followers.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        followers_path = os.path.join(base_dir, "agents", "friends", folder_name, "followers.json")
        
        if os.path.exists(followers_path):
            try:
                with open(followers_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return []
    
    def load_following(self, folder_name):
        """Load following list from agents/friends/{folder_name}/following.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        following_path = os.path.join(base_dir, "agents", "friends", folder_name, "following.json")
        
        if os.path.exists(following_path):
            try:
                with open(following_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return []
    
    def get_profile_counts(self, folder_name):
        """Get followers, following, and friends counts for a profile"""
        followers = self.load_followers(folder_name)
        following = self.load_following(folder_name)
        
        # Friends = users who follow each other (intersection)
        following_ids = set(following)
        friends = [f for f in followers if f in following_ids]
        
        return {
            'followers': len(followers),
            'following': len(following),
            'friends': len(friends)
        }
    
    # ========== BLOCKING SYSTEM ==========
    
    def load_blocked(self):
        """Load blocked users list from user/blocked.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        blocked_path = os.path.join(base_dir, "user", "blocked.json")
        
        if os.path.exists(blocked_path):
            try:
                with open(blocked_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except:
                pass
        
        return []
    
    def save_blocked(self, blocked_list):
        """Save blocked users list to user/blocked.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        blocked_path = os.path.join(base_dir, "user", "blocked.json")
        
        with open(blocked_path, 'w') as f:
            json.dump(blocked_list, f, indent=2)
    
    def is_blocked(self, folder_name):
        """Check if a user is blocked"""
        blocked_list = self.load_blocked()
        return folder_name in blocked_list
    
    def block_user(self, folder_name):
        """Block a user - adds to blocked list"""
        blocked_list = self.load_blocked()
        if folder_name not in blocked_list:
            blocked_list.append(folder_name)
            self.save_blocked(blocked_list)
            return True
        return False
    
    def unblock_user(self, folder_name):
        """Unblock a user - removes from blocked list"""
        blocked_list = self.load_blocked()
        if folder_name in blocked_list:
            blocked_list.remove(folder_name)
            self.save_blocked(blocked_list)
            return True
        return False
    
    def load_blocked_by(self, folder_name):
        """Load list of users who blocked this user from agents/friends/{folder}/blocked.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        blocked_path = os.path.join(base_dir, "agents", "friends", folder_name, "blocked.json")
        
        if os.path.exists(blocked_path):
            try:
                with open(blocked_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except:
                pass
        
        return []
    
    def is_blocked_by(self, folder_name):
        """Check if this user is blocked by the specified user"""
        blocked_by = self.load_blocked_by(folder_name)
        return "user" in blocked_by
    
    def filter_blocked_posts(self, posts):
        """Filter out posts from blocked users"""
        blocked_list = self.blocked_users if hasattr(self, 'blocked_users') else self.load_blocked()
        return [p for p in posts if not self.is_post_from_blocked_user(p, blocked_list)]
    
    def is_post_from_blocked_user(self, post_data, blocked_list=None):
        """Check if a post is from a blocked user"""
        if blocked_list is None:
            blocked_list = self.load_blocked()
        
        # Get the username and check if it matches any blocked user
        username = post_data.get('username', '')
        
        # For now, we check if any blocked folder name appears in the username
        # This is a simple check - in a real app, we'd have better ID mapping
        for blocked_id in blocked_list:
            profile = self.load_any_profile(blocked_id)
            if profile:
                first_name = profile.get('first_name', '')
                last_name = profile.get('last_name', '')
                full_name = f"{first_name} {last_name}".strip()
                if full_name and full_name in username:
                    return True
        return False
    
    def filter_blocked_from_list(self, user_list, blocked_list):
        """Filter a list of user IDs to remove blocked users"""
        return [u for u in user_list if u not in blocked_list]
    
    def show_blocked_users(self):
        """Show dialog with list of blocked users"""
        blocked_list = self.load_blocked()
        
        dialog = QDialog()
        dialog.setWindowTitle("Blocked Users")
        dialog.setMinimumSize(400, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        if not blocked_list:
            no_blocked = QLabel("No blocked users")
            no_blocked.setFont(QFont("Arial", 14))
            no_blocked.setStyleSheet("color: #65676b;")
            no_blocked.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            layout.addWidget(no_blocked)
        else:
            # Scroll area for blocked users
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background-color: transparent;
                }
            """)
            
            container = QWidget()
            blocked_layout = QVBoxLayout(container)
            blocked_layout.setSpacing(5)
            
            for blocked_id in blocked_list:
                # Load the blocked user's profile
                user_profile = self.load_any_profile(blocked_id)
                if user_profile:
                    first_name = user_profile.get('first_name', '')
                    last_name = user_profile.get('last_name', '')
                    full_name = f"{first_name} {last_name}".strip()
                    display_name = full_name if full_name else "User"
                    
                    # Row with name and unblock button
                    row_widget = QWidget()
                    row_layout = QHBoxLayout(row_widget)
                    row_layout.setContentsMargins(0, 0, 0, 0)
                    
                    name_btn = QPushButton(display_name)
                    name_btn.setFont(QFont("Arial", 12))
                    name_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #f0f2f5;
                            color: #050505;
                            border: none;
                            border-radius: 6px;
                            padding: 10px 16px;
                            text-align: left;
                        }
                        QPushButton:hover {
                            background-color: #e4e6eb;
                        }
                    """)
                    name_btn.clicked.connect(lambda checked, fid=blocked_id: (
                        dialog.accept(),
                        self.show_profile(fid)
                    ))
                    row_layout.addWidget(name_btn)
                    
                    unblock_btn = QPushButton("Unblock")
                    unblock_btn.setFont(QFont("Arial", 10))
                    unblock_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #42b72a;
                            color: white;
                            border: none;
                            border-radius: 6px;
                            padding: 8px 16px;
                        }
                        QPushButton:hover {
                            background-color: #36a420;
                        }
                    """)
                    unblock_btn.clicked.connect(lambda checked, fid=blocked_id: (
                        self.unblock_user(fid),
                        dialog.accept(),
                        self.show_blocked_users()  # Refresh the list
                    ))
                    row_layout.addWidget(unblock_btn)
                    
                    blocked_layout.addWidget(row_widget)
            
            blocked_layout.addStretch()
            scroll.setWidget(container)
            layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("✕ Close")
        close_btn.setFont(QFont("Arial", 11))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                color: #050505;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d8dadf;
            }
        """)
        close_btn.clicked.connect(dialog.reject)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def block_user_with_confirmation(self, folder_name):
        """Block a user with confirmation dialog"""
        # Get the user's name
        profile = self.load_any_profile(folder_name)
        if profile:
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            display_name = full_name if full_name else "User"
        else:
            display_name = "this user"
        
        # Confirm with user
        confirm = QMessageBox.question(
            self,
            "Block User",
            f"Are you sure you want to block {display_name}?\n\nThey won't be able to see your posts or profile, and you won't see their posts.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Block the user
            if self.block_user(folder_name):
                QMessageBox.information(self, "User Blocked", f"{display_name} has been blocked.")
                
                # If viewing this profile, go back to feed
                if hasattr(self, 'current_profile_folder') and self.current_profile_folder == folder_name:
                    self.hide_profile()
            else:
                QMessageBox.warning(self, "Error", "Failed to block this user.")
    
    def unblock_user_with_confirmation(self, folder_name):
        """Unblock a user with confirmation dialog"""
        # Get the user's name
        profile = self.load_any_profile(folder_name)
        if profile:
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            display_name = full_name if full_name else "User"
        else:
            display_name = "this user"
        
        # Confirm with user
        confirm = QMessageBox.question(
            self,
            "Unblock User",
            f"Are you sure you want to unblock {display_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Unblock the user
            if self.unblock_user(folder_name):
                QMessageBox.information(self, "User Unblocked", f"{display_name} has been unblocked.")
                
                # Refresh profile if viewing
                if hasattr(self, 'current_profile_folder') and self.current_profile_folder == folder_name:
                    self.hide_profile()
                    self.show_profile(folder_name)
            else:
                QMessageBox.warning(self, "Error", "Failed to unblock this user.")
    
    # ========== END BLOCKING SYSTEM ==========
    
    # ========== FOLLOW/UNFOLLOW SYSTEM ==========
    
    def is_following(self, folder_name):
        """Check if current user is following a user"""
        following = self.load_following("user")  # Load main user's following list
        return folder_name in following
    
    def follow_user(self, folder_name):
        """Follow a user - adds to user's following list and user's followers list"""
        # Add to current user's following list
        following = self.load_following("user")
        if folder_name not in following:
            following.append(folder_name)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            following_path = os.path.join(base_dir, "user", "following.json")
            with open(following_path, 'w') as f:
                json.dump(following, f, indent=2)
        
        # Add current user to the followed user's followers list
        followers = self.load_followers(folder_name)
        if "user" not in followers:
            followers.append("user")
            followers_path = os.path.join(base_dir, "agents", "friends", folder_name, "followers.json")
            with open(followers_path, 'w') as f:
                json.dump(followers, f, indent=2)
        
        return True
    
    def unfollow_user(self, folder_name):
        """Unfollow a user - removes from user's following list and user's followers list"""
        # Remove from current user's following list
        following = self.load_following("user")
        if folder_name in following:
            following.remove(folder_name)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            following_path = os.path.join(base_dir, "user", "following.json")
            with open(following_path, 'w') as f:
                json.dump(following, f, indent=2)
        
        # Remove current user from the unfollowed user's followers list
        followers = self.load_followers(folder_name)
        if "user" in followers:
            followers.remove("user")
            followers_path = os.path.join(base_dir, "agents", "friends", folder_name, "followers.json")
            with open(followers_path, 'w') as f:
                json.dump(followers, f, indent=2)
        
        return True
    
    def follow_user_with_confirmation(self, folder_name):
        """Follow a user with feedback"""
        profile = self.load_any_profile(folder_name)
        if profile:
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            display_name = full_name if full_name else "User"
        else:
            display_name = "this user"
        
        if self.follow_user(folder_name):
            QMessageBox.information(self, "Following", f"You are now following {display_name}.")
            
            # Refresh profile if viewing
            if hasattr(self, 'current_profile_folder') and self.current_profile_folder == folder_name:
                self.hide_profile()
                self.show_profile(folder_name)
            else:
                # Refresh current view if on the profile we're viewing
                if hasattr(self, 'profile_widget') and self.profile_widget and hasattr(self, 'current_profile_folder'):
                    if self.current_profile_folder:
                        self.hide_profile()
                        self.show_profile(self.current_profile_folder)
    
    def unfollow_user_with_confirmation(self, folder_name):
        """Unfollow a user with confirmation and feedback"""
        profile = self.load_any_profile(folder_name)
        if profile:
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            display_name = full_name if full_name else "User"
        else:
            display_name = "this user"
        
        confirm = QMessageBox.question(
            self,
            "Unfollow User",
            f"Are you sure you want to unfollow {display_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            if self.unfollow_user(folder_name):
                QMessageBox.information(self, "Unfollowed", f"You have unfollowed {display_name}.")
                
                # Refresh profile if viewing the unfollowed user's profile
                if hasattr(self, 'current_profile_folder') and self.current_profile_folder == folder_name:
                    self.hide_profile()
                    self.show_profile(folder_name)
                # If viewing main user's profile and looking at following list, refresh
                elif hasattr(self, 'profile_widget') and self.profile_widget and hasattr(self, 'current_profile_folder'):
                    if not self.current_profile_folder:
                        self.hide_profile()
                        self.show_profile()
    
    # ========== END FOLLOW/UNFOLLOW SYSTEM ==========
    
    # ========== FRIEND REQUEST SYSTEM ==========
    
    def load_friends_data(self, folder_name):
        """Load friends.json data for a user"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if folder_name == "user" or folder_name is None:
            friends_path = os.path.join(base_dir, "user", "friends.json")
        else:
            friends_path = os.path.join(base_dir, "agents", "friends", folder_name, "friends.json")
        
        if os.path.exists(friends_path):
            try:
                with open(friends_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except:
                pass
        
        # Return default structure if file doesn't exist or is empty
        return {
            "friends": [],
            "requests_sent": [],
            "requests_received": [],
            "declined": {},  # { "user_id": "cooldown_until_timestamp" }
            "request_timestamps": {}  # { "user_id": "request_sent_timestamp" }
        }
    
    def save_friends_data(self, folder_name, data):
        """Save friends.json data for a user"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if folder_name == "user" or folder_name is None:
            friends_path = os.path.join(base_dir, "user", "friends.json")
        else:
            friends_path = os.path.join(base_dir, "agents", "friends", folder_name, "friends.json")
        
        with open(friends_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_relationship_status(self, folder_name):
        """
        Get relationship status between current user and target user.
        Returns a status string:
        - "none": No relationship
        - "following": Current user follows target, but target doesn't follow back
        - "followed_by": Target follows current user, but current user doesn't follow back
        - "mutual": Both follow each other, no friend request
        - "request_sent": Current user sent friend request, waiting for acceptance
        - "request_received": Target user sent friend request, waiting for response
        - "friends": Both are friends (mutual acceptance)
        - "cooldown": Request was declined, in 3-day cooldown period
        """
        if folder_name == "user" or folder_name is None:
            return "self"
        
        # Load data
        my_friends = self.load_friends_data("user")
        target_friends = self.load_friends_data(folder_name)
        
        # Check if friends
        if folder_name in my_friends.get("friends", []):
            return "friends"
        
        # Check if request sent (we sent, they haven't responded)
        if folder_name in my_friends.get("requests_sent", []):
            return "request_sent"
        
        # Check if request received (they sent, we haven't responded)
        if folder_name in my_friends.get("requests_received", []):
            return "request_received"
        
        # Check following status using followers/following
        my_following = self.load_following("user")
        target_followers = self.load_followers(folder_name)
        target_following = self.load_following(folder_name)
        my_followers = self.load_followers("user")
        
        i_follow_them = folder_name in my_following
        they_follow_me = "user" in target_followers
        
        if i_follow_them and they_follow_me:
            # Check cooldown (if we were declined recently)
            declined = my_friends.get("declined", {})
            if folder_name in declined:
                cooldown_until = declined[folder_name]
                try:
                    cooldown_dt = datetime.strptime(cooldown_until, "%Y/%m/%d %H:%M:%S")
                    if datetime.now() < cooldown_dt:
                        return "cooldown"
                    else:
                        # Cooldown expired, clear it
                        del declined[folder_name]
                        my_friends["declined"] = declined
                        self.save_friends_data("user", my_friends)
                except:
                    pass
            return "mutual"
        elif i_follow_them:
            return "following"
        elif they_follow_me:
            return "followed_by"
        else:
            return "none"
    
    def send_friend_request(self, folder_name):
        """Send a friend request to a user"""
        # Get profile info for notification
        profile = self.load_any_profile(folder_name)
        if profile:
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            display_name = f"{first_name} {last_name}".strip()
        else:
            display_name = "User"
        
        # Update sender's data
        my_friends = self.load_friends_data("user")
        if folder_name not in my_friends["requests_sent"]:
            my_friends["requests_sent"].append(folder_name)
            my_friends["request_timestamps"][folder_name] = get_timestamp()
            self.save_friends_data("user", my_friends)
        
        # Update receiver's data
        target_friends = self.load_friends_data(folder_name)
        if "user" not in target_friends["requests_received"]:
            target_friends["requests_received"].append("user")
            self.save_friends_data(folder_name, target_friends)
        
        # Create notification for receiver
        self.create_notification(
            folder_name,
            "friend_request",
            from_user="user",
            from_name=self.get_user_display_name(),
            content=f"{self.get_user_display_name()} sent you a friend request"
        )
        
        return True
    
    def accept_friend_request(self, folder_name):
        """Accept a friend request from a user"""
        # Update sender's data (they will see us in their friends)
        sender_friends = self.load_friends_data(folder_name)
        if "user" in sender_friends["requests_received"]:
            sender_friends["requests_received"].remove("user")
            if "user" not in sender_friends["friends"]:
                sender_friends["friends"].append("user")
            self.save_friends_data(folder_name, sender_friends)
        
        # Update receiver's data (we accept, so they go to our friends)
        my_friends = self.load_friends_data("user")
        if folder_name in my_friends["requests_sent"]:
            my_friends["requests_sent"].remove(folder_name)
            if folder_name not in my_friends["friends"]:
                my_friends["friends"].append(folder_name)
            # Clear any declined status
            if folder_name in my_friends.get("declined", {}):
                del my_friends["declined"][folder_name]
            if folder_name in my_friends.get("request_timestamps", {}):
                del my_friends["request_timestamps"][folder_name]
            self.save_friends_data("user", my_friends)
        
        # Create notification for sender (accepted)
        self.create_notification(
            folder_name,
            "friend_accepted",
            from_user="user",
            from_name=self.get_user_display_name(),
            content=f"{self.get_user_display_name()} accepted your friend request"
        )
        
        return True
    
    def decline_friend_request(self, folder_name):
        """Decline a friend request and set 3-day cooldown"""
        # Update sender's data
        sender_friends = self.load_friends_data(folder_name)
        if "user" in sender_friends["requests_received"]:
            sender_friends["requests_received"].remove("user")
            self.save_friends_data(folder_name, sender_friends)
        
        # Update receiver's data (we decline)
        my_friends = self.load_friends_data("user")
        if folder_name in my_friends["requests_sent"]:
            my_friends["requests_sent"].remove(folder_name)
            # Set cooldown: current time + 3 days
            request_time = my_friends.get("request_timestamps", {}).get(folder_name, get_timestamp())
            try:
                req_dt = datetime.strptime(request_time, "%Y/%m/%d %H:%M:%S")
                cooldown_dt = req_dt + timedelta(days=3)
                cooldown_timestamp = cooldown_dt.strftime("%Y/%m/%d %H:%M:%S")
            except:
                # If parsing fails, use current time + 3 days
                cooldown_dt = datetime.now() + timedelta(days=3)
                cooldown_timestamp = cooldown_dt.strftime("%Y/%m/%d %H:%M:%S")
            
            if "declined" not in my_friends:
                my_friends["declined"] = {}
            my_friends["declined"][folder_name] = cooldown_timestamp
            
            if folder_name in my_friends.get("request_timestamps", {}):
                del my_friends["request_timestamps"][folder_name]
            
            self.save_friends_data("user", my_friends)
        
        # Create notification for sender (declined)
        self.create_notification(
            folder_name,
            "friend_declined",
            from_user="user",
            from_name=self.get_user_display_name(),
            content=f"{self.get_user_display_name()} declined your friend request"
        )
        
        return True
    
    def cancel_friend_request(self, folder_name):
        """Cancel a pending friend request"""
        # Update sender's data
        sender_friends = self.load_friends_data(folder_name)
        if "user" in sender_friends["requests_received"]:
            sender_friends["requests_received"].remove("user")
            self.save_friends_data(folder_name, sender_friends)
        
        # Update receiver's data (we cancel)
        my_friends = self.load_friends_data("user")
        if folder_name in my_friends["requests_sent"]:
            my_friends["requests_sent"].remove(folder_name)
            if folder_name in my_friends.get("request_timestamps", {}):
                del my_friends["request_timestamps"][folder_name]
            self.save_friends_data("user", my_friends)
        
        return True
    
    def unfriend_user(self, folder_name):
        """Remove someone from friends list"""
        # Update both users' friends lists
        my_friends = self.load_friends_data("user")
        target_friends = self.load_friends_data(folder_name)
        
        if folder_name in my_friends.get("friends", []):
            my_friends["friends"].remove(folder_name)
            self.save_friends_data("user", my_friends)
        
        if "user" in target_friends.get("friends", []):
            target_friends["friends"].remove("user")
            self.save_friends_data(folder_name, target_friends)
        
        return True
    
    def send_friend_request_with_confirmation(self, folder_name):
        """Send friend request with user feedback"""
        profile = self.load_any_profile(folder_name)
        if profile:
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            display_name = full_name if full_name else "User"
        else:
            display_name = "this user"
        
        if self.send_friend_request(folder_name):
            QMessageBox.information(self, "Friend Request Sent", f"Friend request sent to {display_name}.")
            # Refresh profile if viewing
            if hasattr(self, 'current_profile_folder') and self.current_profile_folder == folder_name:
                self.hide_profile()
                self.show_profile(folder_name)
    
    def accept_friend_request_with_confirmation(self, folder_name):
        """Accept friend request with user feedback"""
        profile = self.load_any_profile(folder_name)
        if profile:
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            display_name = full_name if full_name else "User"
        else:
            display_name = "User"
        
        if self.accept_friend_request(folder_name):
            QMessageBox.information(self, "Friend Request Accepted", f"You are now friends with {display_name}!")
            # Refresh profile if viewing
            if hasattr(self, 'current_profile_folder') and self.current_profile_folder == folder_name:
                self.hide_profile()
                self.show_profile(folder_name)
    
    def decline_friend_request_with_confirmation(self, folder_name):
        """Decline friend request with confirmation"""
        profile = self.load_any_profile(folder_name)
        if profile:
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            display_name = full_name if full_name else "User"
        else:
            display_name = "User"
        
        confirm = QMessageBox.question(
            self,
            "Decline Friend Request",
            f"Are you sure you want to decline {display_name}'s friend request?\n\nNote: They will not be able to send you another request for 3 days.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            if self.decline_friend_request(folder_name):
                QMessageBox.information(self, "Request Declined", f"Friend request from {display_name} has been declined.")
    
    # ========== END FRIEND REQUEST SYSTEM ==========
    
    # ========== NOTIFICATION SYSTEM ==========
    
    def get_user_display_name(self):
        """Get the current user's display name"""
        first_name = self.user_profile.get('first_name', '')
        last_name = self.user_profile.get('last_name', '')
        return f"{first_name} {last_name}".strip() or "User"
    
    def load_notifications(self, folder_name="user"):
        """Load notifications for a user"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if folder_name == "user" or folder_name is None:
            notif_path = os.path.join(base_dir, "user", "notifications.json")
        else:
            notif_path = os.path.join(base_dir, "agents", "friends", folder_name, "notifications.json")
        
        if os.path.exists(notif_path):
            try:
                with open(notif_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except:
                pass
        
        return []
    
    def save_notifications(self, folder_name, notifications):
        """Save notifications for a user"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if folder_name == "user" or folder_name is None:
            notif_path = os.path.join(base_dir, "user", "notifications.json")
        else:
            notif_path = os.path.join(base_dir, "agents", "friends", folder_name, "notifications.json")
        
        with open(notif_path, 'w') as f:
            json.dump(notifications, f, indent=2)
    
    def create_notification(self, target_folder, notif_type, from_user, from_name, content):
        """Create a new notification for a user"""
        notifications = self.load_notifications(target_folder)
        
        import uuid
        new_notification = {
            "id": str(uuid.uuid4()),
            "type": notif_type,
            "from_user": from_user,
            "from_name": from_name,
            "content": content,
            "timestamp": get_timestamp(),
            "status": "pending",
            "read": False
        }
        
        # Add to beginning of list (newest first)
        notifications.insert(0, new_notification)
        self.save_notifications(target_folder, notifications)
        
        # Update notification badge if this is for the current user
        if target_folder == "user":
            self.update_notification_badge()
        
        return new_notification
    
    def mark_notification_read(self, folder_name, notif_id):
        """Mark a notification as read"""
        notifications = self.load_notifications(folder_name)
        for notif in notifications:
            if notif.get("id") == notif_id:
                notif["read"] = True
                break
        self.save_notifications(folder_name, notifications)
    
    def mark_all_notifications_read(self, folder_name="user"):
        """Mark all notifications as read"""
        notifications = self.load_notifications(folder_name)
        for notif in notifications:
            notif["read"] = True
        self.save_notifications(folder_name, notifications)
        
        # Update notification badge
        if folder_name == "user":
            self.update_notification_badge()
    
    def delete_notification(self, folder_name, notif_id):
        """Delete a notification"""
        notifications = self.load_notifications(folder_name)
        notifications = [n for n in notifications if n.get("id") != notif_id]
        self.save_notifications(folder_name, notifications)
        
        # Update notification badge
        if folder_name == "user":
            self.update_notification_badge()
    
    def get_unread_notification_count(self, folder_name="user"):
        """Get count of unread notifications"""
        notifications = self.load_notifications(folder_name)
        return sum(1 for n in notifications if not n.get("read", False))
    
    def update_notification_status(self, folder_name, notif_id, status):
        """Update notification status (pending, accepted, declined)"""
        notifications = self.load_notifications(folder_name)
        for notif in notifications:
            if notif.get("id") == notif_id:
                notif["status"] = status
                notif["read"] = True  # Mark as read when responding
                break
        self.save_notifications(folder_name, notifications)
        
        # Update notification badge
        if folder_name == "user":
            self.update_notification_badge()
    
    def show_notifications_center(self):
        """Show the notification center dialog"""
        notifications = self.load_notifications("user")
        
        dialog = QDialog()
        dialog.setWindowTitle("Notifications")
        dialog.setMinimumSize(450, 550)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header with title and mark all read button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Notifications")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #050505;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Mark all as read button
        if any(not notif.get("read", False) for notif in notifications):
            mark_read_btn = QPushButton("Mark all as read")
            mark_read_btn.setFont(QFont("Arial", 10))
            mark_read_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #1877f2;
                    border: none;
                }
                QPushButton:hover {
                    text-decoration: underline;
                }
            """)
            mark_read_btn.clicked.connect(lambda: (
                self.mark_all_notifications_read("user"),
                dialog.accept(),
                self.show_notifications_center()
            ))
            header_layout.addWidget(mark_read_btn)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #dddfe2;")
        layout.addWidget(separator)
        
        if not notifications:
            # No notifications
            empty_label = QLabel("No notifications yet")
            empty_label.setFont(QFont("Arial", 14))
            empty_label.setStyleSheet("color: #65676b;")
            empty_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            empty_label.setMinimumHeight(200)
            layout.addWidget(empty_label)
        else:
            # Scroll area for notifications
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background-color: transparent;
                }
            """)
            
            container = QWidget()
            notif_layout = QVBoxLayout(container)
            notif_layout.setSpacing(10)
            
            for notif in notifications:
                notif_widget = self.create_notification_item(notif, dialog)
                notif_layout.addWidget(notif_widget)
            
            notif_layout.addStretch()
            scroll.setWidget(container)
            layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("✕ Close")
        close_btn.setFont(QFont("Arial", 11))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                color: #050505;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d8dadf;
            }
        """)
        close_btn.clicked.connect(dialog.reject)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def create_notification_item(self, notif, parent_dialog):
        """Create a single notification widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        
        # Background based on read status
        bg_color = "#eff6ff" if not notif.get("read", False) else "white"
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 8px;
                border: 1px solid #dddfe2;
            }}
        """)
        
        # Avatar
        avatar_label = QLabel("👤")
        avatar_label.setFont(QFont("Arial", 24))
        avatar_label.setFixedSize(40, 40)
        avatar_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(avatar_label)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # User name
        from_name = notif.get("from_name", "Unknown")
        name_label = QLabel(from_name)
        name_label.setFont(QFont("Arial", 13, QFont.Bold))
        name_label.setStyleSheet("color: #050505;")
        content_layout.addWidget(name_label)
        
        # Content text with status indicator
        content_text = notif.get("content", "")
        notif_type = notif.get("type", "")
        notif_status = notif.get("status", "")
        
        # Add status icon for clarity
        if notif_type == "friend_accepted" and notif_status == "completed":
            content_text = "✓ " + content_text
            content_label = QLabel(content_text)
            content_label.setFont(QFont("Arial", 12))
            content_label.setStyleSheet("color: #42b72a;")  # Green for accepted
        elif notif_type == "friend_declined" and notif_status == "declined":
            content_text = "✕ " + content_text
            content_label = QLabel(content_text)
            content_label.setFont(QFont("Arial", 12))
            content_label.setStyleSheet("color: #ef4444;")  # Red for declined
        else:
            content_label = QLabel(content_text)
            content_label.setFont(QFont("Arial", 12))
            content_label.setStyleSheet("color: #050505;")
        
        content_label.setWordWrap(True)
        content_layout.addWidget(content_label)
        
        # Timestamp
        timestamp = notif.get("timestamp", "")
        time_label = QLabel(format_time_ago(datetime.strptime(timestamp, "%Y/%m/%d %H:%M:%S") if timestamp else datetime.now()))
        time_label.setFont(QFont("Arial", 10))
        time_label.setStyleSheet("color: #65676b;")
        content_layout.addWidget(time_label)
        
        layout.addLayout(content_layout, stretch=1)
        
        # Action buttons for friend request notifications
        if notif.get("type") == "friend_request" and notif.get("status") == "pending":
            actions_layout = QVBoxLayout()
            actions_layout.setSpacing(6)
            
            accept_btn = QPushButton("✓ Accept")
            accept_btn.setFont(QFont("Arial", 10))
            accept_btn.setStyleSheet("""
                QPushButton {
                    background-color: #42b72a;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #36a420;
                }
            """)
            from_user = notif.get("from_user", "")
            accept_btn.clicked.connect(lambda: (
                self.accept_friend_request_with_confirmation(from_user),
                self.update_notification_status("user", notif.get("id"), "accepted"),
                parent_dialog.accept(),
                self.show_notifications_center()
            ))
            actions_layout.addWidget(accept_btn)
            
            decline_btn = QPushButton("✕ Decline")
            decline_btn.setFont(QFont("Arial", 10))
            decline_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e4e6eb;
                    color: #050505;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #d8dadf;
                }
            """)
            decline_btn.clicked.connect(lambda: (
                self.decline_friend_request_with_confirmation(from_user),
                self.update_notification_status("user", notif.get("id"), "declined"),
                parent_dialog.accept(),
                self.show_notifications_center()
            ))
            actions_layout.addWidget(decline_btn)
            
            layout.addLayout(actions_layout)
        
        # Delete button (for all notifications)
        delete_btn = QPushButton("🗑️")
        delete_btn.setFont(QFont("Arial", 12))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #65676b;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                color: #ef4444;
            }
        """)
        delete_btn.clicked.connect(lambda: (
            self.delete_notification("user", notif.get("id")),
            parent_dialog.accept(),
            self.show_notifications_center()
        ))
        layout.addWidget(delete_btn)
        
        return widget
    
    def update_notification_badge(self):
        """Update the notification badge count in the header"""
        if hasattr(self, 'notif_badge'):
            count = self.get_unread_notification_count("user")
            if count > 0:
                self.notif_badge.setText(str(count) if count <= 99 else "99+")
                self.notif_badge.setVisible(True)
            else:
                self.notif_badge.setVisible(False)
    
    # ========== END NOTIFICATION SYSTEM ==========
    
    # ========== RANDOM USER ENGINE ==========
    
    def init_random_user_engine(self):
        """Initialize the Random User Engine"""
        print("RandomUserEngine: Initializing...")
        
        # Make sure base_dir exists
        if not hasattr(self, 'base_dir'):
            print("RandomUserEngine: base_dir not yet available, setting it now...")
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Initialize the engine variable first
        self.random_user_engine = None
        
        try:
            # Connect the signal to the smart refresh method
            self.refresh_feed_signal.connect(self.refresh_feed_smart)
            
            # Pass the signal emit method to the engine (thread-safe)
            self.random_user_engine = RandomUserEngine(self.base_dir, gui_callback=self.refresh_feed_signal.emit)
            if self.random_user_engine.llm:
                print("RandomUserEngine: Successfully initialized with Gemini")
            else:
                print("RandomUserEngine: Running in simulation mode (no API key or LangChain)")
        except Exception as e:
            print(f"RandomUserEngine: Error initializing - {e}")
    
    def test_random_user_setup(self):
        """Test the random_user setup - call this to debug"""
        print("\n" + "="*60)
        print("RANDOM USER SETUP TEST")
        print("="*60)
        
        # Test 1: LangChain availability
        print("\n1. Checking LangChain availability...")
        langchain_ok = check_langchain_availability()
        print(f"   LangChain Available: {langchain_ok}")
        
        # Test 2: API key
        print("\n2. Checking API key...")
        api_path = os.path.join(self.base_dir, "api.json")
        print(f"   API file exists: {os.path.exists(api_path)}")
        if os.path.exists(api_path):
            with open(api_path, 'r') as f:
                api_data = json.load(f)
            api_key = api_data.get("api_key", "")
            print(f"   API key present: {bool(api_key)}")
            print(f"   API key length: {len(api_key)} chars")
        
        # Test 3: Config files
        print("\n3. Checking config files...")
        random_user_dir = os.path.join(self.base_dir, "system", "random_user")
        print(f"   random_user dir exists: {os.path.exists(random_user_dir)}")
        print(f"   tools.json exists: {os.path.exists(os.path.join(random_user_dir, 'tools.json'))}")
        print(f"   config.json exists: {os.path.exists(os.path.join(random_user_dir, 'config.json'))}")
        
        # Test 4: Platform description
        print("\n4. Checking platform description...")
        platform_dir = os.path.join(self.base_dir, "system", "platform")
        print(f"   platform dir exists: {os.path.exists(platform_dir)}")
        print(f"   description.json exists: {os.path.exists(os.path.join(platform_dir, 'description.json'))}")
        
        # Test 5: Feed
        print("\n5. Checking feed...")
        feed_dir = os.path.join(self.base_dir, "system", "feed")
        home_path = os.path.join(feed_dir, "home.json")
        print(f"   feed dir exists: {os.path.exists(feed_dir)}")
        print(f"   home.json exists: {os.path.exists(home_path)}")
        if os.path.exists(home_path):
            with open(home_path, 'r') as f:
                home_data = json.load(f)
            print(f"   posts in feed: {len(home_data.get('posts', []))}")
        
        print("\n" + "="*60)
        print("To run random_user manually, call: app.run_random_user_session()")
        print("="*60 + "\n")
    
    def run_random_user_session(self):
        """Run a Random User session"""
        print("\n" + "="*50)
        print("RandomUserEngine: Starting new session...")
        
        if not self.random_user_engine:
            print("RandomUserEngine: Not initialized, initializing now...")
            self.init_random_user_engine()
        
        if not self.random_user_engine:
            print("RandomUserEngine: Failed to initialize, skipping session")
            return
        
        try:
            # Run the session
            actions = self.random_user_engine.run_session()
            
            if not actions:
                print("RandomUserEngine: No actions generated (APC check failed or no LLM)")
            else:
                print(f"RandomUserEngine: Generated {len(actions)} actions")
                
                # Process each action
                for i, action in enumerate(actions, 1):
                    print(f"  [{i}] {action.to_dict()}")
                    self.execute_random_user_action(action)
                
                print(f"RandomUserEngine: Executed {len(actions)} actions successfully")
                
        except Exception as e:
            print(f"RandomUserEngine: Error during session - {e}")
        
        print("="*50 + "\n")
    
    def execute_random_user_action(self, action: Action):
        """Execute a random user action"""
        tool = action.tool
        post_id = action.post_id
        comment_id = action.comment_id
        content = action.content
        reaction_type = action.type
        caption = action.caption
        
        if tool == "post_reactions" and post_id and reaction_type:
            print(f"  → Reacting to post {post_id} with {reaction_type}")
            # Find the post and add reaction
            result = self.add_random_user_reaction(post_id, reaction_type)
            # Refresh UI to show new counts
            self.refresh_post_widgets()
        
        elif tool == "comment_post" and post_id and content:
            print(f"  → Commenting on post {post_id}: {content[:50]}...")
            result = self.add_random_user_comment(post_id, content)
            # Refresh UI to show new counts
            self.refresh_post_widgets()
        
        elif tool == "reply_comment" and comment_id and content:
            print(f"  → Replying to comment {comment_id}: {content[:50]}...")
            self.add_random_user_reply(comment_id, content)
        
        elif tool == "react_comment" and comment_id and reaction_type:
            print(f"  → Reacting to comment {comment_id} with {reaction_type}")
            self.add_random_user_comment_reaction(comment_id, reaction_type)
        
        elif tool == "make_post" and content:
            print(f"  → Creating new post: {content[:50]}...")
            self.add_random_user_post(content)
            # Trigger GUI refresh to show the new post
            gui_callback = getattr(self, 'gui_callback', None)
            if gui_callback:
                print("RandomUserEngine: Triggering GUI refresh...")
                try:
                    # Check if callback is callable (handles both signals and functions)
                    if callable(gui_callback):
                        gui_callback()
                    else:
                        print("RandomUserEngine: Warning - gui_callback is not callable")
                except Exception as e:
                    print(f"RandomUserEngine: Error calling GUI callback: {e}")
        
        elif tool == "repost_post" and post_id:
            print(f"  → Reposting post {post_id}")
            self.repost_random_user_post(post_id)
        
        elif tool == "quote_post":
            # Use original_post_id if available, otherwise fall back to post_id
            target_post_id = action.original_post_id if action.original_post_id else post_id
            if target_post_id and content:
                print(f"  → Quoting post {target_post_id}: {content[:50]}...")
                self.quote_random_user_post(target_post_id, content)
            else:
                print(f"  → Unknown action or missing parameters: quote_post (need original_post_id and content)")
        
        else:
            print(f"  → Unknown action or missing parameters: {tool}")
    
    def add_random_user_reaction(self, post_id: str, reaction_type: str):
        """Add a reaction to a post from random_user"""
        # Find the post in all_posts
        for post in self.all_posts:
            if post.get('id') == post_id or post_id in str(post.get('id', '')):
                post['likes'] = post.get('likes', 0) + 1
                self.save_posts()
                
                # Rebuild home.json to update like count
                self._rebuild_home_feed(self.all_posts)
                
                print(f"  ✓ Added {reaction_type} reaction to post")
                return True
        print(f"  ✗ Post {post_id} not found")
        return False
    
    def add_random_user_comment(self, post_id: str, content: str):
        """Add a comment from random_user"""
        timestamp = get_timestamp()
        comment_id = f"comment_{uuid.uuid4().hex[:8]}"
        
        # Find the post and update comment count
        for post in self.all_posts:
            if post.get('id') == post_id or post_id in str(post.get('id', '')):
                post['comments'] = post.get('comments', 0) + 1
                
                # Ensure comments_list exists
                if 'comments_list' not in post:
                    post['comments_list'] = []
                
                # Save posts.json to persist the updated comment count
                self.save_posts()
                
                # Update UI - find the PostWidget and add the comment visually
                # This will call add_comment() which adds to self.comments_list AND syncs to parent.all_posts
                self._add_comment_to_ui(post_id, 'Random User', '🤖', content, timestamp, comment_id)
                
                # Rebuild home.json to update comment count
                self._rebuild_home_feed(self.all_posts)
                
                print(f"  ✓ Added comment to post")
                return True
        print(f"  ✗ Post {post_id} not found")
        return False
    
    def _add_comment_to_ui(self, post_id, username, avatar, content, timestamp, comment_id=None):
        """Add a comment to the visible PostWidget"""
        for post_widget in self.visible_posts:
            if hasattr(post_widget, 'post_id') and post_widget.post_id == post_id:
                # Parse timestamp
                if isinstance(timestamp, str):
                    try:
                        time_obj = datetime.strptime(timestamp, "%Y/%m/%d %H:%M:%S")
                    except ValueError:
                        time_obj = datetime.now()
                else:
                    time_obj = timestamp
                
                # Add the comment to the widget
                if hasattr(post_widget, 'add_comment'):
                    post_widget.add_comment(username, avatar, content, time_obj, comment_id)
                break
    
    def _add_reply_to_post_widget_via_registry(self, post_id, comment_id, username, avatar, content, timestamp, reply_id=None):
        """Add a reply to a PostWidget using the registry (works even if post is not visible)
        
        This method uses the post_widget_registry to find the PostWidget by post_id,
        allowing UI updates even when the post is scrolled out of view.
        
        Returns True if reply was added to UI, False otherwise.
        """
        debug_print(DEBUG_GLOBAL, f"_add_reply_to_post_widget_via_registry: post_id={post_id}, comment_id={comment_id}")
        
        # Try to get PostWidget from registry first (fastest method)
        post_widget = None
        if post_id in self.post_widget_registry:
            post_widget = self.post_widget_registry[post_id]
            debug_print(DEBUG_GLOBAL, f"  ✓ Found PostWidget via registry for post_id: {post_id}")
        else:
            debug_print(DEBUG_GLOBAL, f"  ⚠ PostWidget not in registry for post_id: {post_id}")
            # Also check visible_posts as fallback
            for pw in self.visible_posts:
                if hasattr(pw, 'post_id') and pw.post_id == post_id:
                    post_widget = pw
                    debug_print(DEBUG_GLOBAL, f"  ✓ Found PostWidget in visible_posts for post_id: {post_id}")
                    break
        
        if not post_widget:
            debug_print(DEBUG_GLOBAL, f"  ✗ PostWidget not found anywhere for post_id: {post_id}")
            return False
        
        # Check if widget is still valid using sip.isdeleted (PyQt5 safe method)
        if sip.isdeleted(post_widget) or not post_widget.isVisible():
            debug_print(DEBUG_GLOBAL, f"  ✗ PostWidget is deleted or not visible for post_id: {post_id}")
            return False
        
        # Find the comment widget and add reply
        comment_widget_found = False
        for i in range(post_widget.comments_list_layout.count()):
            item = post_widget.comments_list_layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'add_reply'):
                comment_widget = item.widget()
                if hasattr(comment_widget, 'comment_id') and comment_widget.comment_id == comment_id:
                    comment_widget_found = True
                    
                    # Parse timestamp
                    if isinstance(timestamp, str):
                        try:
                            time_obj = datetime.strptime(timestamp, "%Y/%m/%d %H:%M:%S")
                        except ValueError:
                            time_obj = datetime.now()
                        time_str = timestamp
                    else:
                        time_obj = timestamp
                        time_str = timestamp.strftime("%Y/%m/%d %H:%M:%S")
                    
                    # Create reply data
                    reply_data = {
                        'username': username,
                        'avatar': avatar,
                        'content': content,
                        'time': time_str,
                        'likes': []
                    }
                    if reply_id:
                        reply_data['id'] = reply_id
                    
                    # Add reply to comment widget (save_to_backend=False prevents duplicates)
                    comment_widget.add_reply(reply_data, save_to_backend=False)
                    
                    # Update PostWidget's comment count
                    post_widget.comments_count += 1
                    post_widget.update_reactions_display()
                    post_widget.update_toggle_comments_button()
                    
                    debug_print(DEBUG_GLOBAL, f"  ✓ Added reply via registry to UI")
                    return True
        
        if not comment_widget_found:
            debug_print(DEBUG_GLOBAL, f"  ✗ Comment widget not found in PostWidget for comment_id: {comment_id}")
        
        return False
    
    def add_random_user_reply(self, comment_id: str, content: str):
        """Add a reply from random_user to a comment - properly persists to home.json"""
        timestamp = get_timestamp()
        reply_id = f"reply_{uuid.uuid4().hex[:8]}"
        
        # Find the comment in all_posts and add a reply
        for post in self.all_posts:
            comments_list = post.get('comments_list', [])
            for comment in comments_list:
                if comment.get('id') == comment_id:
                    # Ensure replies array exists
                    if 'replies' not in comment:
                        comment['replies'] = []
                    
                    # Create reply data in internal format
                    reply_data = {
                        'id': reply_id,
                        'username': 'Random User',
                        'avatar': '🤖',
                        'content': content,
                        'time': timestamp,
                        'likes': []
                    }
                    comment['replies'].append(reply_data)
                    
                    # Update post's comment count (total comments includes replies)
                    post['comments'] = post.get('comments', 0) + 1
                    
                    post_id = post.get('id')
                    
                    # CRITICAL: Update UI first (while post is in memory)
                    # Use registry-based method for reliable updates
                    ui_updated = self._add_reply_to_post_widget_via_registry(post_id, comment_id, 'Random User', '🤖', content, timestamp, reply_id)
                    
                    if not ui_updated:
                        # Fallback: try to find and update the post widget
                        for post_widget in self.visible_posts:
                            if hasattr(post_widget, 'post_id') and post_widget.post_id == post_id:
                                for i in range(post_widget.comments_list_layout.count()):
                                    item = post_widget.comments_list_layout.itemAt(i)
                                    if item.widget() and hasattr(item.widget(), 'add_reply'):
                                        comment_widget = item.widget()
                                        if hasattr(comment_widget, 'comment_id') and comment_widget.comment_id == comment_id:
                                            # Create reply data
                                            reply_ui_data = {
                                                'username': 'Random User',
                                                'avatar': '🤖',
                                                'content': content,
                                                'time': timestamp,
                                                'likes': []
                                            }
                                            if reply_id:
                                                reply_ui_data['id'] = reply_id
                                            
                                            # Add to UI (save_to_backend=False since we already saved)
                                            comment_widget.add_reply(reply_ui_data, save_to_backend=False)
                                            
                                            # Update post widget comment count
                                            post_widget.comments_count += 1
                                            post_widget.update_reactions_display()
                                            post_widget.update_toggle_comments_button()
                                            
                                            print(f"  ✓ Added reply to UI via visible_posts fallback")
                                            ui_updated = True
                                            break
                                break
                    
                    if not ui_updated:
                        print(f"  ⚠ Post widget not visible, reply will appear on next load")
                    
                    # CRITICAL: Rebuild home.json to update comment count and include reply
                    self._rebuild_home_feed(self.all_posts)
                    
                    print(f"  ✓ Added reply to comment {comment_id}")
                    return True
        
        print(f"  ✗ Comment {comment_id} not found")
        return False
    
    def _add_reply_to_ui(self, post_id, comment_id, username, avatar, content, timestamp, reply_id=None):
        """Add a reply to the visible CommentWidget
        
        This is a fallback method when the registry doesn't have the post widget.
        """
        for post_widget in self.visible_posts:
            if hasattr(post_widget, 'post_id') and post_widget.post_id == post_id:
                # Find the comment widget by comment_id
                for i in range(post_widget.comments_list_layout.count()):
                    item = post_widget.comments_list_layout.itemAt(i)
                    if item.widget() and hasattr(item.widget(), 'add_reply'):
                        comment_widget = item.widget()
                        # Check if this is the comment we want by matching comment_id
                        if hasattr(comment_widget, 'comment_id') and comment_widget.comment_id == comment_id:
                            # Parse timestamp and convert to string for JSON serialization
                            if isinstance(timestamp, str):
                                try:
                                    time_obj = datetime.strptime(timestamp, "%Y/%m/%d %H:%M:%S")
                                except ValueError:
                                    time_obj = datetime.now()
                                time_str = timestamp
                            else:
                                time_obj = timestamp
                                time_str = timestamp.strftime("%Y/%m/%d %H:%M:%S")
                            
                            # Create reply data with STRING time (not datetime object)
                            reply_data = {
                                'username': username,
                                'avatar': avatar,
                                'content': content,
                                'time': time_str,  # CRITICAL: Must be string for JSON serialization
                                'likes': []
                            }
                            if reply_id:
                                reply_data['id'] = reply_id
                            
                            # Add reply to the comment widget
                            # CRITICAL: save_to_backend=False prevents duplicate entries
                            # The reply was already added to all_posts by add_random_user_reply()
                            comment_widget.add_reply(reply_data, save_to_backend=False)
                            
                            # Update post widget comment count
                            post_widget.comments_count += 1
                            post_widget.update_reactions_display()
                            post_widget.update_toggle_comments_button()
                            
                            print(f"  ✓ Added reply to UI via visible_posts fallback")
                            return True
        
        print(f"  ⚠ Post widget not found in visible_posts for post_id: {post_id}")
        return False
        print(f"  ✗ Could not find comment widget in UI to add reply")
        return False
    
    def add_random_user_comment_reaction(self, comment_id: str, reaction_type: str):
        """Add a reaction to a comment from random_user"""
        print(f"  → Reacting to comment {comment_id} with {reaction_type}")
        
        # Find the comment in all_posts and increment likes
        for post in self.all_posts:
            comments_list = post.get('comments_list', [])
            for comment in comments_list:
                if comment.get('id') == comment_id or comment_id in str(comment.get('id', '')):
                    # Increment likes count (random_user doesn't add to reacts[])
                    new_likes = comment.get('likes', 0) + 1
                    comment['likes'] = new_likes
                    
                    # Save posts.json to persist the updated likes count
                    self.save_posts()
                    
                    # Rebuild home.json to update like count
                    self._rebuild_home_feed(self.all_posts)
                    
                    # Update the CommentWidget in the UI
                    self.refresh_comment_likes(comment_id, new_likes)
                    
                    print(f"  ✓ Added {reaction_type} reaction to comment")
                    return True
        
        print(f"  ✗ Comment {comment_id} not found")
        return False
    
    def refresh_post_widgets(self):
        """Refresh all visible post widgets to show updated counts from all_posts"""
        for post_widget in self.visible_posts:
            if hasattr(post_widget, 'update_from_all_posts'):
                post_widget.update_from_all_posts(self.all_posts)
    
    def refresh_comment_likes(self, comment_id: str, new_likes: int):
        """Update the likes count for a specific comment widget (called when random_user reacts)"""
        for post_widget in self.visible_posts:
            for i in range(post_widget.comments_list_layout.count()):
                item = post_widget.comments_list_layout.itemAt(i)
                if item.widget() and hasattr(item.widget(), 'comment_id'):
                    comment_widget = item.widget()
                    if hasattr(comment_widget, 'comment_id') and comment_widget.comment_id == comment_id:
                        if hasattr(comment_widget, 'update_likes_from_backend'):
                            comment_widget.update_likes_from_backend(new_likes)
                            return True
        return False
    
    def add_random_user_post(self, content: str):
        """Add a new post from random_user"""
        timestamp = get_timestamp()
        # Generate deterministic post ID
        post_id = generate_deterministic_post_id('random_user', content, timestamp)
        
        post_data = {
            'id': post_id,
            'username': 'Random User',
            'avatar': '🤖',
            'content': content,
            'time': timestamp,
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'reports': 0,
            'reported_by': [],
            'edits': [],
            'is_edited': False,
            'embedded_post': None,
            'is_quote': False,
            'folder_name': 'random_user',
            'reacts': []  # Individual reaction records
        }
        
        # Add to posts list (for in-memory tracking only - not saved to file)
        self.all_posts.append(post_data)
        
        # Rebuild home.json to include the new post
        self._rebuild_home_feed(self.all_posts)
        
        print(f"  ✓ Created new post")
        return True
    
    def repost_random_user_post(self, post_id: str):
        """Repost a post from random_user - simple repost without commentary"""
        # Find the original post
        original_post = None
        for post in self.all_posts:
            if post.get('id') == post_id or post_id in str(post.get('id', '')):
                original_post = post
                break
        
        if not original_post:
            print(f"  ✗ Original post {post_id} not found")
            return False
        
        # Create a repost - empty content since original post is shown via embedded_post
        timestamp = get_timestamp()
        new_post_id = generate_deterministic_post_id('random_user', 'repost', timestamp)
        
        post_data = {
            'id': new_post_id,  # Generate deterministic ID for the repost
            'username': 'Random User',
            'avatar': '🤖',
            'content': '',  # Empty - original post shown via embedded_post
            'time': timestamp,
            'likes': 0,
            'comments': 0,
            'shares': 0,  # Repost itself has 0 shares (it's a new post)
            'reports': 0,
            'reported_by': [],
            'edits': [],
            'is_edited': False,
            'embedded_post': original_post,
            'is_quote': False,
            'folder_name': 'random_user',
            'reacts': []  # Individual reaction records
        }
        
        self.all_posts.append(post_data)
        
        # Update original post shares (this is what gets shared)
        original_post['shares'] = original_post.get('shares', 0) + 1
        
        # CRITICAL: Save to posts.json so the updated shares persist
        # This ensures when app restarts or home.json is rebuilt, shares are correct
        self.save_posts()
        
        # Rebuild home.json to include the repost
        self._rebuild_home_feed(self.all_posts)
        return True
    
    def quote_random_user_post(self, post_id: str, content: str):
        """Quote a post from random_user"""
        # Find the original post
        original_post = None
        for post in self.all_posts:
            if post.get('id') == post_id or post_id in str(post.get('id', '')):
                original_post = post
                break
        
        if not original_post:
            print(f"  ✗ Original post {post_id} not found")
            return False
        
        # Create a quote post
        timestamp = get_timestamp()
        new_post_id = generate_deterministic_post_id('random_user', content, timestamp)
        
        post_data = {
            'id': new_post_id,  # Generate deterministic ID for the quote
            'username': 'Random User',
            'avatar': '🤖',
            'content': content,
            'time': timestamp,
            'likes': 0,
            'comments': 0,
            'shares': 0,  # Quote post itself has 0 shares (it's a new post)
            'reports': 0,
            'reported_by': [],
            'edits': [],
            'is_edited': False,
            'embedded_post': original_post,
            'is_quote': True,
            'folder_name': 'random_user',
            'reacts': []  # Individual reaction records
        }
        
        self.all_posts.append(post_data)
        
        # Update original post shares count (this is what gets shared)
        original_post['shares'] = original_post.get('shares', 0) + 1
        
        # CRITICAL: Save to posts.json so the updated shares persist
        # This ensures when app restarts or home.json is rebuilt, shares are correct
        self.save_posts()
        
        # Rebuild home.json completely to ensure all posts have correct shares
        self._rebuild_home_feed(self.all_posts)
    
    # ========== END RANDOM USER ENGINE ==========
    
    def find_folder_by_username(self, username):
        """Find the folder name for a given username by searching through friend profiles"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        friends_dir = os.path.join(base_dir, "agents", "friends")
        
        # Search through all friend folders
        if os.path.exists(friends_dir):
            for i in range(1, 11):
                folder_path = os.path.join(friends_dir, str(i))
                if os.path.exists(folder_path):
                    profile_path = os.path.join(folder_path, "profile.json")
                    if os.path.exists(profile_path):
                        try:
                            with open(profile_path, 'r') as f:
                                profile = json.load(f)
                                first_name = profile.get('first_name', '')
                                last_name = profile.get('last_name', '')
                                full_name = f"{first_name} {last_name}".strip()
                                if full_name == username:
                                    return str(i)
                        except:
                            pass
        return None
    
    def load_posts(self):
        """Load posts from user/posts.json and all agent posts.
        Uses deterministic IDs and saves them back to JSON files for persistence."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        all_posts = []
        
        # Step 1: Load and process user posts
        posts_path = os.path.join(base_dir, "user", "posts.json")
        if os.path.exists(posts_path):
            try:
                with open(posts_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        posts = json.loads(content)
                        posts_changed = False
                        for post in posts:
                            # Ensure required fields
                            if 'reports' not in post:
                                post['reports'] = 0
                            if 'reported_by' not in post:
                                post['reported_by'] = []
                            if 'edits' not in post:
                                post['edits'] = []
                            if 'is_edited' not in post:
                                post['is_edited'] = False
                            if 'folder_name' not in post:
                                post['folder_name'] = 'user'
                            if 'comments_list' not in post:
                                post['comments_list'] = []
                            
                            # Ensure each comment has a replies array and reacts/likes fields
                            for comment in post.get('comments_list', []):
                                if 'replies' not in comment:
                                    comment['replies'] = []
                                if 'reacts' not in comment:
                                    comment['reacts'] = []
                                if 'likes' not in comment:
                                    comment['likes'] = 0
                                posts_changed = True
                            
                            # Generate deterministic ID if missing
                            if 'id' not in post:
                                timestamp = post.get('time', get_timestamp())
                                content_text = post.get('content', '')
                                post['id'] = generate_deterministic_post_id('user', content_text, timestamp)
                                posts_changed = True
                            
                            all_posts.append(post)
                        
                        # Save posts back to file if IDs were added
                        if posts_changed:
                            with open(posts_path, 'w') as f:
                                json.dump(posts, f, indent=2, default=str)
            except Exception as e:
                print(f"  ✗ Error loading user posts: {e}")
        
        # Step 2: Load and process agent posts
        agents_dir = os.path.join(base_dir, "agents", "friends")
        if os.path.exists(agents_dir):
            for agent_folder in os.listdir(agents_dir):
                agent_posts_path = os.path.join(agents_dir, agent_folder, "posts.json")
                if os.path.exists(agent_posts_path):
                    try:
                        with open(agent_posts_path, 'r') as f:
                            content = f.read().strip()
                            if content:
                                posts = json.loads(content)
                                posts_changed = False
                                for post in posts:
                                    # Ensure required fields
                                    if 'reports' not in post:
                                        post['reports'] = 0
                                    if 'reported_by' not in post:
                                        post['reported_by'] = []
                                    if 'edits' not in post:
                                        post['edits'] = []
                                    if 'is_edited' not in post:
                                        post['is_edited'] = False
                                    if 'folder_name' not in post:
                                        post['folder_name'] = agent_folder
                                    if 'comments_list' not in post:
                                        post['comments_list'] = []
                                    
                                    # Ensure each comment has a replies array and reacts/likes fields
                                    for comment in post.get('comments_list', []):
                                        if 'replies' not in comment:
                                            comment['replies'] = []
                                        if 'reacts' not in comment:
                                            comment['reacts'] = []
                                        if 'likes' not in comment:
                                            comment['likes'] = 0
                                        posts_changed = True
                                    
                                    # Generate deterministic ID if missing
                                    if 'id' not in post:
                                        timestamp = post.get('time', get_timestamp())
                                        content_text = post.get('content', '')
                                        post['id'] = generate_deterministic_post_id(agent_folder, content_text, timestamp)
                                        posts_changed = True
                                    
                                    all_posts.append(post)
                                
                                # Save posts back to file if IDs were added
                                if posts_changed:
                                    with open(agent_posts_path, 'w') as f:
                                        json.dump(posts, f, indent=2, default=str)
                    except Exception as e:
                        print(f"  ✗ Error loading agent {agent_folder} posts: {e}")
        
        # Step 2.5: Load random_user posts from home.json
        # Random_user posts are only stored in home.json, not in separate files
        home_data = self.load_home_feed()
        for post_entry in home_data.get('posts', []):
            # Only load posts authored by Random User
            if post_entry.get('author') == 'Random User' or post_entry.get('author_type') == 'random_user':
                # Check if we already have this post (to avoid duplicates)
                post_id = post_entry.get('id')
                if not any(p.get('id') == post_id for p in all_posts):
                    # Convert home.json post format to internal post format
                    # CRITICAL: Preserve comments from visible_comments
                    visible_comments = post_entry.get('visible_comments', [])
                    
                    # Convert visible_comments to comments_list format
                    # CRITICAL: Also convert replies from home.json format to internal format
                    comments_list = []
                    for comment_entry in visible_comments:
                        # Convert replies from home.json format (author, author_avatar, timestamp)
                        # to internal format (username, avatar, time)
                        home_replies = comment_entry.get('replies', [])
                        internal_replies = []
                        for reply_entry in home_replies:
                            internal_replies.append({
                                'id': reply_entry.get('id', ''),
                                'username': reply_entry.get('author', 'Unknown'),
                                'avatar': reply_entry.get('author_avatar', '👤'),
                                'content': reply_entry.get('content', ''),
                                'time': reply_entry.get('timestamp', get_timestamp()),
                                'likes': reply_entry.get('likes', 0)
                            })
                        
                        comment_data = {
                            'id': comment_entry.get('id', ''),
                            'username': comment_entry.get('author', 'Unknown'),
                            'avatar': comment_entry.get('author_avatar', '👤'),
                            'content': comment_entry.get('content', ''),
                            'time': comment_entry.get('timestamp', get_timestamp()),
                            'likes': comment_entry.get('likes', 0),
                            'reacts': comment_entry.get('reacts', []),  # Sanitize: add reacts field
                            'replies': internal_replies  # Use converted replies
                        }
                        comments_list.append(comment_data)
                    
                    post_data = {
                        'id': post_id,
                        'username': post_entry.get('author', 'Random User'),
                        'avatar': post_entry.get('author_avatar', '🤖'),
                        'content': post_entry.get('content', ''),
                        'time': post_entry.get('timestamp', get_timestamp()),
                        'likes': post_entry.get('likes', 0),
                        'comments': post_entry.get('comments', 0),
                        'shares': post_entry.get('shares', 0),
                        'reports': 0,
                        'reported_by': [],
                        'edits': [],
                        'is_edited': False,
                        'is_quote': post_entry.get('type') == 'quote',
                        'comments_list': comments_list,  # Preserve comments!
                        'folder_name': 'random_user',
                        'reacts': post_entry.get('reacts', [])  # Individual reaction records
                    }
                    
                    # Convert embedded_post from home.json format to internal format
                    # home.json format: author, author_avatar, timestamp
                    # internal format: username, avatar, time
                    embedded = post_entry.get('embedded_post')
                    if embedded:
                        post_data['embedded_post'] = {
                            'username': embedded.get('author', 'Unknown'),
                            'avatar': embedded.get('author_avatar', '👤'),
                            'content': embedded.get('content', ''),
                            'time': embedded.get('timestamp', get_timestamp()),
                            'likes': embedded.get('likes', 0),
                            'comments': embedded.get('comments', 0),
                            'shares': embedded.get('shares', 0)
                        }
                    all_posts.append(post_data)
        
        # Step 3: Rebuild home.json completely from loaded posts
        # CRITICAL: Assign self.all_posts first so _rebuild_home_feed can save posts
        self.all_posts = all_posts
        
        # Set loading flag to prevent infinite loop when _load_comments_from_data calls add_comment
        self._loading_posts = True
        try:
            self._rebuild_home_feed(all_posts)
        finally:
            self._loading_posts = False
        
        return all_posts
    
    def _rebuild_home_feed(self, all_posts):
        """Completely rebuild home.json from the loaded posts list.
        This ensures home.json always matches the actual posts.
        
        Structure:
        - posts[].comments: Integer count of all comments
        - posts[].comments_list: Array of ALL comments (internal format)
        - posts[].visible_comments: ALL comments for AI reference
        
        Note: Top-level "comments" array has been removed - comments are now
        only stored within posts[].visible_comments[].
        
        The config.json values (post_comment_read, etc.) control what the AI can
        fetch/interact with, NOT what the user sees. User sees ALL comments.
        
        Debug logging controlled by self._debug_verbose flag (default: False)."""
        # Prevent re-entrant calls (avoids infinite loops when add_comment triggers rebuild)
        if getattr(self, '_rebuilding_feed', False):
            if DEBUG_GLOBAL or self._debug_verbose:
                print(f"DEBUG _rebuild_home_feed: Skipped (already rebuilding)")
            return
        
        self._rebuilding_feed = True
        if DEBUG_GLOBAL or self._debug_verbose:
            print(f"DEBUG _rebuild_home_feed: Started with {len(all_posts)} posts")
            # Debug: Show call stack to identify what's triggering this
            print(f"DEBUG _rebuild_home_feed: Call stack:")
            import traceback
            for line in traceback.format_stack()[-5:-1]:
                print(f"  {line.strip()}")
        
        try:
            home_data = {
                "meta": {
                    "last_updated": get_timestamp(),
                    "feed_count": 0,
                    "rules_source": "system/algorithms/home_feed.json"
                },
                'posts': []
            }

            for i, post in enumerate(all_posts):
                post_id = post.get('id')
                is_quote = post.get('is_quote', False)
                embedded = post.get('embedded_post')

                if post_id:
                    # Get ALL comments from the post (user sees all)
                    comments_list = post.get('comments_list', [])
                    if DEBUG_GLOBAL or self._debug_verbose:
                        print(f"DEBUG _rebuild_home_feed: post_id={post_id}, total comments={len(comments_list)}")
                    
                    # Process comments - assign IDs if missing, show ALL comments
                    visible_comments, updated_comments = self._get_visible_comments(
                        comments_list, 
                        100,  # Show 100% - user sees all comments
                        100,  # 100%
                        50,   # These values don't matter when showing 100%
                        50
                    )
                    
                    if DEBUG_GLOBAL or self._debug_verbose:
                        print(f"DEBUG _rebuild_home_feed: visible_comments count={len(visible_comments)}")
                    
                    # DON'T replace post['comments_list'] - that breaks the reference from PostWidget.comments_list
                    # Instead, just update in place: add IDs to comments that don't have them
                    # This preserves the object reference so new comments are saved correctly
                    original_comments_list = post.get('comments_list', [])
                    for i, comment in enumerate(updated_comments):
                        comment_id = comment.get('id', '')
                        if comment_id and i < len(original_comments_list):
                            # Add ID to original comment if missing
                            if not original_comments_list[i].get('id'):
                                original_comments_list[i]['id'] = comment_id
                    
                    # NOTE: Top-level comments\[\] array has been removed
                    # Comments are now only stored within posts\[\].visible_comments\[\]

                    # Determine post type: quote, repost, or original
                    post_type = 'original'
                    if is_quote:
                        post_type = 'quote'
                    elif embedded is not None:
                        post_type = 'repost'

                    # Get shares count
                    # For quote/repost posts: they have 0 shares (they are shares of another post)
                    # For original posts: they have shares (how many times they've been quoted/shared)
                    if embedded:
                        # This is a quote/repost - it has 0 shares (it's a share of another post)
                        shares_count = 0
                    else:
                        # This is an original post - use its actual shares count
                        shares_count = post.get('shares', 0)

                    if DEBUG_GLOBAL:
                        print(f"DEBUG _rebuild_home_feed: Post {post_id} type={post_type}, shares={shares_count}")

                    # Build home entry
                    home_entry = {
                        'id': post_id,
                        'type': post_type,
                        'author': post.get('username', 'Unknown'),
                        'author_type': 'random_user' if post.get('folder_name') == 'random_user' else ('agent' if post.get('folder_name') not in ['user', None] else 'user'),
                        'author_folder': post.get('folder_name', 'user'),
                        'content': post.get('content', ''),
                        'timestamp': post.get('time', get_timestamp()),
                        'likes': post.get('likes', 0),
                        'comments': post.get('comments', 0),  # Total comment count
                        'shares': shares_count,
                        'visible_comments': visible_comments,  # ALL comments for AI reference
                        'reacts': post.get('reacts', [])  # Individual reaction records (NOT included in AI context)
                    }

                    # Include embedded_post for quotes/reposts so we know what was shared
                    if embedded:
                        # Convert datetime to string for JSON serialization
                        embedded_time = embedded.get('time')
                        if isinstance(embedded_time, datetime):
                            embedded_time_str = embedded_time.strftime("%Y/%m/%d %H:%M:%S")
                        else:
                            embedded_time_str = embedded_time

                        home_entry['embedded_post'] = {
                            'author': embedded.get('username', 'Unknown'),
                            'author_avatar': embedded.get('avatar', '👤'),
                            'content': embedded.get('content', ''),
                            'timestamp': embedded_time_str,
                            'likes': embedded.get('likes', 0),
                            'comments': embedded.get('comments', 0),
                            'shares': embedded.get('shares', 0)
                        }

                    home_data['posts'].append(home_entry)

            # Update meta
            home_data["meta"]["feed_count"] = len(home_data['posts'])

            # Debug logging disabled for _rebuild_home_feed
            # debug_print(MASTER_DEBUG_ENABLED, f"\n[DEBUG _rebuild_home_feed] Saving to home.json and posts.json")
            # debug_print(MASTER_DEBUG_ENABLED, f"  - posts count: {len(home_data['posts'])}")
            
            self.save_home_feed(home_data)

            # CRITICAL: Also save posts.json to persist any new comment IDs
            self.save_posts()
            
            # debug_print(MASTER_DEBUG_ENABLED, f"[DEBUG _rebuild_home_feed] ✓ Save complete")
            
        finally:
            # Always reset the flag, even if an error occurred
            self._rebuilding_feed = False
    
    def _get_visible_comments(self, comments_list, post_comment_read, post_comment_read_cent,
                              fetch_rate_cent_liked, fetch_rate_cent_new):
        """Get comments for display.

        When called with 100, 100 values: shows ALL comments (user view).
        Otherwise: filters based on config values.
        
        CRITICAL: Returns comments in home.json format with field names:
        - author (not username)
        - author_avatar (not avatar)  
        - timestamp (not time)
        - replies[] with same field name convention
        """
        if not comments_list:
            return [], []

        # DON'T deep copy when showing all comments - we need to preserve the original
        # reference so PostWidget.comments_list stays in sync with post['comments_list']
        import hashlib

        # Check if we're showing all comments (100% = user view)
        showing_all = (post_comment_read_cent >= 100 and post_comment_read >= len(comments_list))

        if showing_all:
            # User view: show ALL comments in chronological order (newest first)
            # Create a sorted copy of indices instead of reordering the original list
            def parse_time(c):
                time_str = c.get('time', '') or c.get('timestamp', '')
                if isinstance(time_str, str):
                    try:
                        return datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
                    except ValueError:
                        return datetime.min
                return datetime.min

            # Get sorted indices
            sorted_indices = sorted(range(len(comments_list)), key=lambda i: parse_time(comments_list[i]), reverse=True)

            # Assign IDs to any comments that don't have them (in-place update)
            for comment in comments_list:
                if not comment.get('id'):
                    content_preview = comment.get('content', '')[:20]
                    time_str = comment.get('time', '') or comment.get('timestamp', '') or get_timestamp()
                    raw_str = f"{comment.get('username', 'unknown')}_{time_str}_{content_preview}"
                    comment['id'] = f"comment_{hashlib.md5(raw_str.encode()).hexdigest()[:8]}"

            # Format all comments for display using sorted order
            # CRITICAL: Convert internal format (username, avatar, time) to home.json format (author, author_avatar, timestamp)
            visible_comments = []
            for i in sorted_indices:
                comment = comments_list[i]
                
                # Get timestamp and ensure it's a string
                time_val = comment.get('time', '') or comment.get('timestamp', '') or get_timestamp()
                if isinstance(time_val, datetime):
                    time_str = time_val.strftime("%Y/%m/%d %H:%M:%S")
                elif isinstance(time_val, str):
                    time_str = time_val
                else:
                    time_str = get_timestamp()
                
                # Get replies and convert to home.json format
                replies = comment.get('replies', [])
                visible_replies = []
                for reply in replies:
                    # Get reply timestamp and ensure it's a string
                    reply_time = reply.get('time', '') or reply.get('timestamp', '') or get_timestamp()
                    if isinstance(reply_time, datetime):
                        reply_time_str = reply_time.strftime("%Y/%m/%d %H:%M:%S")
                    elif isinstance(reply_time, str):
                        reply_time_str = reply_time
                    else:
                        reply_time_str = get_timestamp()
                    
                    visible_replies.append({
                        'id': reply.get('id', ''),
                        'author': reply.get('username', 'Unknown'),
                        'author_avatar': reply.get('avatar', '👤'),
                        'content': reply.get('content', ''),
                        'likes': reply.get('likes', 0),
                        'timestamp': reply_time_str  # CRITICAL: Ensure string, not datetime
                    })
                
                visible_comments.append({
                    'id': comment.get('id', ''),
                    'author': comment.get('username', 'Unknown'),
                    'author_avatar': comment.get('avatar', '👤'),
                    'content': comment.get('content', ''),
                    'likes': comment.get('likes', 0),
                    'reacts': comment.get('reacts', []),  # Include reacts field
                    'timestamp': time_str,  # CRITICAL: Ensure string, not datetime
                    'replies': visible_replies
                })

            # Return original list (not a copy) to preserve reference
            return visible_comments, comments_list
        
        # Filtered view: use percentage-based filtering
        import math
        
        # Calculate how many comments to fetch
        total_comments = len(comments_copy)
        calculated_count = max(1, math.ceil(total_comments * post_comment_read_cent / 100))
        max_to_fetch = min(post_comment_read, calculated_count)
        
        if max_to_fetch == 0:
            return [], comments_copy
        
        # Calculate split between liked and new
        liked_count = int(max_to_fetch * fetch_rate_cent_liked / 100)
        new_count = max_to_fetch - liked_count
        
        # Sort by likes (descending) for top liked comments
        liked_sorted = sorted(comments_copy, key=lambda x: x.get('likes', 0), reverse=True)
        top_liked = liked_sorted[:liked_count] if liked_count > 0 else []
        
        # Get remaining comments (exclude those already taken)
        taken_ids = set()
        for c in top_liked:
            key = c.get('content', '') + c.get('time', '')
            taken_ids.add(key)
        
        remaining = [c for c in comments_copy if (c.get('content', '') + c.get('time', '')) not in taken_ids]
        
        # Sort remaining by timestamp (newest first)
        def parse_time(c):
            time_str = c.get('time', '')
            if isinstance(time_str, str):
                try:
                    return datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
                except ValueError:
                    return datetime.min
            return datetime.min
        
        new_sorted = sorted(remaining, key=parse_time, reverse=True)
        newest = new_sorted[:new_count] if new_count > 0 else []
        
        # Combine and format for display
        visible_comments = []
        for comment in top_liked + newest:
            # Generate a unique comment ID if not present
            comment_id = comment.get('id')
            if not comment_id:
                content_preview = comment.get('content', '')[:20]
                time_str = comment.get('time', get_timestamp())
                raw_str = f"{comment.get('username', 'unknown')}_{time_str}_{content_preview}"
                comment_id = f"comment_{hashlib.md5(raw_str.encode()).hexdigest()[:8]}"
                comment['id'] = comment_id
            
            visible_comments.append({
                'id': comment_id,
                'author': comment.get('username', 'Unknown'),
                'author_avatar': comment.get('avatar', '👤'),
                'content': comment.get('content', ''),
                'likes': comment.get('likes', 0),
                'reacts': comment.get('reacts', []),  # Include reacts field
                'timestamp': comment.get('time', get_timestamp()),
                'replies': comment.get('replies', [])  # Include replies
            })
        
        return visible_comments, comments_copy
    
    def load_agent_posts(self, folder_name):
        """Load posts from agents/friends/{folder}/posts.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        posts_path = os.path.join(base_dir, "agents", "friends", folder_name, "posts.json")
        
        if os.path.exists(posts_path):
            try:
                with open(posts_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        posts = json.loads(content)
                        posts_changed = False
                        # Ensure all posts have the required fields
                        for post in posts:
                            if 'reports' not in post:
                                post['reports'] = 0
                            if 'reported_by' not in post:
                                post['reported_by'] = []
                            if 'edits' not in post:
                                post['edits'] = []
                            if 'is_edited' not in post:
                                post['is_edited'] = False
                            if 'folder_name' not in post:
                                post['folder_name'] = folder_name
                            if 'comments_list' not in post:
                                post['comments_list'] = []
                            
                            # Generate deterministic ID if missing
                            if 'id' not in post:
                                timestamp = post.get('time', get_timestamp())
                                content_text = post.get('content', '')
                                post['id'] = generate_deterministic_post_id(folder_name, content_text, timestamp)
                                posts_changed = True
                        
                        # Save posts back to file if IDs were added
                        if posts_changed:
                            with open(posts_path, 'w') as f:
                                json.dump(posts, f, indent=2, default=str)
                        
                        return posts
            except:
                pass
        
        return []
    
    def save_posts(self):
        """Save posts to user/posts.json and update agent posts files.
        
        NOTE: random_user posts are NOT saved to separate files.
        They are only stored in feed/home.json via _rebuild_home_feed().
        This is because random_user is a session-based agent, not a persistent friend."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        posts_path = os.path.join(base_dir, "user", "posts.json")

        # Separate user posts from agent posts
        user_posts = []
        agent_posts_by_folder = {}

        for post in self.all_posts:
            folder_name = post.get('folder_name', 'user')
            if folder_name == 'user' or folder_name is None:
                user_posts.append(post)
            elif folder_name == 'random_user':
                # Skip random_user posts - they are only stored in feed/home.json
                continue
            else:
                if folder_name not in agent_posts_by_folder:
                    agent_posts_by_folder[folder_name] = []
                agent_posts_by_folder[folder_name].append(post)

        # Debug: Check if comments are being saved
        if DEBUG_GLOBAL:
            print(f"DEBUG save_posts: Saving {len(user_posts)} user posts")
            for i, post in enumerate(user_posts):
                print(f"DEBUG save_posts: Post {i}: id={post.get('id', 'unknown')}, time={post.get('time', 'unknown')}")
                print(f"DEBUG save_posts:   comments_list exists={'comments_list' in post}")
                print(f"DEBUG save_posts:   comments_list length={len(post.get('comments_list', []))}")
                if post.get('comments_list'):
                    for j, c in enumerate(post['comments_list']):
                        print(f"DEBUG save_posts:     Comment {j}: {c.get('content', 'unknown')[:30]}")

        # Save user posts
        with open(posts_path, 'w') as f:
            json.dump(user_posts, f, indent=2, default=str)

        # Save each agent's posts (skip random_user - not a persistent agent)
        for folder_name, posts in agent_posts_by_folder.items():
            agent_posts_path = os.path.join(base_dir, "agents", "friends", folder_name, "posts.json")
            with open(agent_posts_path, 'w') as f:
                json.dump(posts, f, indent=2, default=str)
    
    def load_interactions(self):
        """Load interactions from user/interactions.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        interactions_path = os.path.join(base_dir, "user", "interactions.json")
        
        if os.path.exists(interactions_path):
            try:
                with open(interactions_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except:
                pass
        
        return {"likes": [], "comments": [], "shares": [], "replies": [], "post_deletions": []}
    
    def save_interactions(self):
        """Save interactions to user/interactions.json"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        interactions_path = os.path.join(base_dir, "user", "interactions.json")
        
        with open(interactions_path, 'w') as f:
            json.dump(self.interactions, f, indent=2, default=str)
    
    def log_interaction(self, interaction_type, data):
        """Log an interaction to interactions.json
        
        Args:
            interaction_type: Type of interaction (e.g., 'post_deletions', 'likes', 'comments')
            data: Dictionary containing interaction details with timestamp
        """
        if not hasattr(self, 'interactions'):
            self.interactions = self.load_interactions()
        
        # Ensure the category exists
        if interaction_type not in self.interactions:
            self.interactions[interaction_type] = []
        
        # Add the interaction entry as-is (timestamp should be included in data)
        self.interactions[interaction_type].append(data)
        
        # Save immediately
        self.save_interactions()
    
    def update_all_timestamps(self):
        """Update all timestamps in posts and comments"""
        # Update all PostWidgets
        for i in range(self.posts_layout.count()):
            item = self.posts_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), PostWidget):
                item.widget().update_timestamp()
                # Also update timestamps in comments
                item.widget().update_comment_timestamps()
    
    def clear_all_posts(self):
        """Clear all post widgets from the feed layout"""
        # Clear visible_posts tracking list
        if hasattr(self, 'visible_posts'):
            self.visible_posts.clear()
        
        # Remove all widgets from posts_layout except the stretch item
        while self.posts_layout.count() > 1:
            item = self.posts_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.deleteLater()  # Properly delete PyQt widget
    
    def refresh_feed_smart(self):
        """Smart feed refresh that only adds NEW posts without clearing existing ones.
        Preserves scroll position and handles both empty and populated feeds."""
        print("FacebookGUI: Smart refreshing feed...")
        
        # Capture scroll position before any changes
        scroll_bar = self.posts_scroll.verticalScrollBar()
        scroll_position = scroll_bar.value()
        was_at_top = scroll_position == 0
        
        # Get IDs of currently visible posts
        visible_ids = set()
        for post_widget in self.visible_posts:
            if hasattr(post_widget, 'post_id') and post_widget.post_id:
                visible_ids.add(post_widget.post_id)
        
        # Reload all_posts to get new posts from the agent
        if hasattr(self, 'load_posts'):
            self.all_posts = self.load_posts()
            print(f"FacebookGUI: Loaded {len(self.all_posts)} total posts")
        
        # Find posts that are NOT yet visible
        new_posts = []
        for post_data in self.all_posts:
            post_id = post_data.get('id')
            if post_id and post_id not in visible_ids:
                new_posts.append(post_data)
        
        if not new_posts:
            print("FacebookGUI: No new posts to add")
            return
        
        print(f"FacebookGUI: Adding {len(new_posts)} new post(s)")
        
        # Add new posts to the visible feed (insert at top, before stretch)
        for post_data in new_posts:
            self.create_post_from_data(post_data)
            # Track displayed post ID
            post_id = post_data.get('id')
            if post_id:
                self.displayed_post_ids.add(post_id)
        
        # If user was not at top, adjust scroll to compensate for added content
        if not was_at_top:
            # Calculate total height of added widgets
            added_height = sum(post.height() if hasattr(post, 'height') else 100 for post in new_posts)
            # Adjust scroll position to maintain viewport
            scroll_bar.setValue(scroll_position + added_height)
    
    def load_initial_posts(self):
        """Load initial batch of posts from posts.json with visibility filtering"""
        # Filter out posts from blocked users
        filtered_posts = self.filter_blocked_posts(self.all_posts)
        
        # Apply visibility tier filtering based on likes and timestamp
        visible_posts = []
        for post_data in filtered_posts:
            if self.is_post_visible(post_data):
                visible_posts.append(post_data)
        
        # Load posts in reverse order (newest first)
        posts_to_show = visible_posts[-self.posts_per_load:] if len(visible_posts) > self.posts_per_load else visible_posts
        
        for post_data in posts_to_show:
            self.create_post_from_data(post_data)
            # Track displayed post IDs
            post_id = post_data.get('id')
            if post_id:
                self.displayed_post_ids.add(post_id)
    
    def check_for_new_posts(self):
        """Check for new posts that haven't been displayed yet and add them to the feed.
        This method is called periodically by the feed_monitor_timer to handle posts
        created by the RandomUserEngine on an empty feed.
        
        Debug logging controlled by self._debug_verbose flag (default: False)."""
        if self._debug_verbose or DEBUG_GLOBAL:
            print(f"DEBUG check_for_new_posts: Checking... visible_posts={len(self.visible_posts)}, displayed_ids={len(self.displayed_post_ids)}")
        
        # Get all post IDs from the loaded posts
        all_post_ids = set()
        for post in self.all_posts:
            post_id = post.get('id')
            if post_id:
                all_post_ids.add(post_id)
        
        # Find posts that are in all_posts but not in displayed_post_ids
        new_post_ids = all_post_ids - self.displayed_post_ids
        
        if self._debug_verbose or DEBUG_GLOBAL:
            print(f"DEBUG check_for_new_posts: all_posts IDs: {all_post_ids}, displayed: {self.displayed_post_ids}, new: {new_post_ids}")
        
        if not new_post_ids:
            if self._debug_verbose or DEBUG_GLOBAL:
                print(f"DEBUG check_for_new_posts: No new posts, returning")
            return  # No new posts to display
        
        print(f"FacebookGUI: Found {len(new_post_ids)} new post(s) to display")
        
        # Find the actual post data for new posts
        # We need to process them in reverse order so newest appears first
        new_posts_data = []
        for post in self.all_posts:
            post_id = post.get('id')
            if post_id in new_post_ids:
                new_posts_data.append(post)
        
        if self._debug_verbose or DEBUG_GLOBAL:
            print(f"DEBUG check_for_new_posts: Creating widgets for {len(new_posts_data)} new posts")
        
        # Sort by timestamp (newest first)
        new_posts_data.sort(key=lambda p: p.get('time', ''), reverse=True)
        
        # Create widgets for new posts
        for post_data in new_posts_data:
            post_id = post_data.get('id')
            if post_id and post_id not in self.displayed_post_ids:
                if self._debug_verbose or DEBUG_GLOBAL:
                    print(f"DEBUG check_for_new_posts: Creating widget for post {post_id}")
                self.create_post_from_data(post_data)
                self.displayed_post_ids.add(post_id)
                print(f"FacebookGUI: Added new post {post_id} to feed")
    
    def add_generated_post(self):
        """Add a post - now loads from posts.json"""
        if not self.all_posts:
            return
            
        # Get the next post from all_posts that isn't displayed
        # For now, just add a placeholder if we have posts
        pass
    
    def create_post_from_data(self, post_data):
        """Create a PostWidget from post data dictionary"""
        username = post_data.get('username', 'Unknown')
        avatar = post_data.get('avatar', '👤')
        content = post_data.get('content', '')
        
        # Get folder_name from post data or try to find it
        folder_name = post_data.get('folder_name', None)
        if not folder_name:
            # Try to find folder name by username
            folder_name = self.find_folder_by_username(username)
        
        # Parse time
        time_str = post_data.get('time', datetime.now())
        if isinstance(time_str, str):
            try:
                time = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                time = datetime.now()
        else:
            time = time_str
        
        likes = post_data.get('likes', 0)
        comments_count = post_data.get('comments', 0)
        shares = post_data.get('shares', 0)
        
        # Check for embedded post (repost/quote)
        embedded_post = post_data.get('embedded_post', None)
        is_quote = post_data.get('is_quote', False)
        
        # Get edits and edited state
        edits = post_data.get('edits', [])
        is_edited = post_data.get('is_edited', False)
        
        # Get post_id for live updates
        post_id = post_data.get('id', None)
        
        # Get comments list
        comments_list = post_data.get('comments_list', [])
        
        # Get reacts array and current user for reaction initialization
        reacts = post_data.get('reacts', [])
        profile = getattr(self, 'user_profile', {})
        first_name = profile.get('first_name', '')
        last_name = profile.get('last_name', '')
        current_user = f"{first_name} {last_name}".strip() if first_name or last_name else 'You'
        
        post = PostWidget(
            username,
            avatar,
            content,
            time,
            likes=likes,
            comments=comments_count,
            shares=shares,
            embedded_post=embedded_post,
            is_quote=is_quote,
            edits=edits,
            is_edited=is_edited,
            folder_name=folder_name,
            post_id=post_id,
            comments_list=comments_list,
            reacts=reacts,
            current_user=current_user
        )
        
        self.posts_layout.insertWidget(self.posts_layout.count() - 1, post)
        self.visible_posts.append(post)
        
        # CRITICAL: Register PostWidget by post_id for O(1) UI updates
        if post_id:
            self.post_widget_registry[post_id] = post
        
        return post
    
    def on_scroll_changed(self, value):
        """Handle scroll for infinite scroll functionality"""
        scroll_bar = self.posts_scroll.verticalScrollBar()
        max_value = scroll_bar.maximum()
        
        # If user is near the bottom (within 100 pixels), load more posts
        if value >= max_value - 100:
            self.load_more_posts()
        
        # If user is near the top (within 100 pixels) and has scrolled down significantly,
        # remove posts from the top to save memory
        if value <= 100 and len(self.visible_posts) > self.posts_per_load:
            self.remove_top_posts()
    
    def load_more_posts(self):
        """Load more posts when scrolling down - with proper pagination"""
        # Track which posts have been displayed using timestamps
        displayed_times = set()
        for post in self.visible_posts:
            if hasattr(post, '_time_str'):
                displayed_times.add(post._time_str)
            elif hasattr(post, 'post_data'):
                displayed_times.add(post.post_data.get('time'))
        
        # Get filtered posts (excluding blocked users)
        filtered_posts = self.filter_blocked_posts(self.all_posts)
        
        # Find posts that haven't been displayed yet
        remaining_posts = [p for p in filtered_posts if p.get('time') not in displayed_times]
        
        # If no remaining posts, stop loading
        if not remaining_posts:
            return
        
        # Load a batch of posts (newest first from remaining)
        posts_to_add = remaining_posts[-self.posts_per_batch:] if len(remaining_posts) > self.posts_per_batch else remaining_posts
        
        for post_data in posts_to_add:
            self.create_post_from_data(post_data)
            # Track displayed post ID
            post_id = post_data.get('id')
            if post_id:
                self.displayed_post_ids.add(post_id)
    
    def remove_top_posts(self):
        """Remove posts from the top when user has scrolled down significantly"""
        # Remove the oldest posts (from the top of the feed)
        posts_to_remove = self.top_posts_cleanup
        
        for _ in range(posts_to_remove):
            if self.visible_posts and len(self.visible_posts) > self.posts_per_load:
                oldest_post = self.visible_posts.pop(0)
                
                # CRITICAL: Unregister PostWidget from registry
                if hasattr(oldest_post, 'post_id') and oldest_post.post_id:
                    if oldest_post.post_id in self.post_widget_registry:
                        del self.post_widget_registry[oldest_post.post_id]
                        print(f"  ✓ Unregistered PostWidget for post_id: {oldest_post.post_id}")
                
                # Remove from layout
                for i in range(self.posts_layout.count()):
                    item = self.posts_layout.itemAt(i)
                    if item.widget() == oldest_post:
                        self.posts_layout.removeItem(item)
                        oldest_post.deleteLater()
                        break
    
    def handle_live_updates(self):
        """Handle live updates from data source - check for new interactions"""
        # TODO: Implement with actual data source (API polling, websocket, etc.)
        # This method is called every 10 seconds
        # For now, reload interactions to check for updates
        self.interactions = self.load_interactions()
    
    def navigate_to_original_post(self, post_data):
        """Navigate to show the original post with a back button"""
        # Store current scroll position
        self.navigation_stack.append(self.posts_scroll.verticalScrollBar().value())
        
        # Hide the posts scroll area
        self.posts_scroll.setVisible(False)
        self.post_area.setVisible(False)
        
        # Create a single post view for the original post
        self.original_post_widget = QWidget()
        original_layout = QVBoxLayout(self.original_post_widget)
        original_layout.setContentsMargins(0, 0, 0, 0)
        original_layout.setSpacing(20)
        
        # Add back button
        back_layout = QHBoxLayout()
        back_layout.addStretch()
        
        self.back_btn = QPushButton("⬅️ Back to Feed")
        self.back_btn.setFont(QFont("Arial", 12))
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #166fe5;
            }
        """)
        self.back_btn.clicked.connect(self.go_back)
        back_layout.addWidget(self.back_btn)
        
        original_layout.addLayout(back_layout)
        
        # Create the original post widget
        original_time = post_data.get('time', datetime.now())
        if isinstance(original_time, str):
            try:
                original_time = datetime.strptime(original_time, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                original_time = datetime.now()
        
        original_post = PostWidget(
            post_data.get('username', 'Unknown'),
            post_data.get('avatar', '👤'),
            post_data.get('content', ''),
            original_time,
            likes=post_data.get('likes', 0),
            comments=post_data.get('comments', 0),
            shares=post_data.get('shares', 0),
            embedded_post=post_data.get('embedded_post', None),
            is_quote=post_data.get('is_quote', False),
            edits=post_data.get('edits', []),
            is_edited=post_data.get('is_edited', False),
            comments_list=post_data.get('comments_list', [])
        )
        original_layout.addWidget(original_post)
        
        original_layout.addStretch()
        
        # Add to the feed layout
        self.feed_layout.addWidget(self.original_post_widget)
    
    def go_back(self):
        """Go back to the main feed"""
        if self.original_post_widget:
            self.original_post_widget.setVisible(False)
            self.original_post_widget.deleteLater()
            self.original_post_widget = None
        
        # Show the main feed
        self.posts_scroll.setVisible(True)
        self.post_area.setVisible(True)
        
        # Restore scroll position
        if self.navigation_stack:
            self.posts_scroll.verticalScrollBar().setValue(self.navigation_stack.pop())
    
    def show_profile(self, profile_folder=None):
        """Show user profile view - if profile_folder is None, shows main user's profile"""
        # Defensive: ensure profile_folder is None, a string, or convert boolean to None
        if isinstance(profile_folder, bool):
            profile_folder = None
        
        # If already viewing profile, hide it first
        if self.profile_widget:
            self.hide_profile()
        
        # Store scroll position
        self.navigation_stack.append(self.posts_scroll.verticalScrollBar().value())
        
        # Hide feed components
        self.post_area.setVisible(False)
        self.posts_scroll.setVisible(False)
        
        # Determine if this is the main user's profile
        is_main_user = profile_folder is None or profile_folder == "user"
        
        # Load the profile data
        if is_main_user:
            profile_data = self.user_profile
            profile_folder_name = "user"
        else:
            profile_data = self.load_any_profile(profile_folder)
            if not profile_data:
                QMessageBox.warning(self, "Error", "Profile not found.")
                return
            profile_folder_name = profile_folder
        
        # Get profile counts
        if is_main_user:
            # For main user, load from user/followers.json and user/following.json
            base_dir = os.path.dirname(os.path.abspath(__file__))
            followers_path = os.path.join(base_dir, "user", "followers.json")
            following_path = os.path.join(base_dir, "user", "following.json")
            
            followers = []
            following = []
            if os.path.exists(followers_path):
                try:
                    with open(followers_path, 'r') as f:
                        followers = json.load(f)
                except:
                    pass
            if os.path.exists(following_path):
                try:
                    with open(following_path, 'r') as f:
                        following = json.load(f)
                except:
                    pass
        else:
            followers = self.load_followers(profile_folder)
            following = self.load_following(profile_folder)
        
        # Load blocked list to filter out blocked users
        blocked_list = self.load_blocked()
        
        # Filter out blocked users from followers, following, and friends
        followers = self.filter_blocked_from_list(followers, blocked_list)
        following = self.filter_blocked_from_list(following, blocked_list)
        
        # Friends = users who follow each other (and not blocked)
        following_ids = set(following)
        friends = [f for f in followers if f in following_ids]
        
        followers_count = len(followers)
        following_count = len(following)
        friends_count = len(friends)
        
        # Create profile widget
        self.profile_widget = QWidget()
        profile_layout = QVBoxLayout(self.profile_widget)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(20)
        
        # Back button
        back_layout = QHBoxLayout()
        back_layout.addStretch()
        
        back_btn = QPushButton("⬅️ Back to Feed")
        back_btn.setFont(QFont("Arial", 12))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #166fe5;
            }
        """)
        back_btn.clicked.connect(self.hide_profile)
        back_layout.addWidget(back_btn)
        
        profile_layout.addLayout(back_layout)
        
        # Profile header
        profile_header = QFrame()
        profile_header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #dddfe2;
            }
        """)
        header_layout = QVBoxLayout(profile_header)
        header_layout.setContentsMargins(20, 20, 20, 20)
        header_layout.setSpacing(15)
        
        # Avatar and name
        avatar_name_layout = QHBoxLayout()
        
        avatar_label = QLabel("👤")
        avatar_label.setFont(QFont("Arial", 64))
        avatar_label.setFixedSize(80, 80)
        avatar_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        avatar_name_layout.addWidget(avatar_label)
        
        name_layout = QVBoxLayout()
        name_layout.setSpacing(5)
        
        first_name = profile_data.get('first_name', '')
        last_name = profile_data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        
        name_label = QLabel(full_name if full_name else "User")
        name_label.setFont(QFont("Arial", 24, QFont.Bold))
        name_label.setStyleSheet("color: #050505;")
        name_layout.addWidget(name_label)
        
        bio = profile_data.get('bio', '')
        if bio:
            bio_label = QLabel(bio)
            bio_label.setFont(QFont("Arial", 12))
            bio_label.setStyleSheet("color: #65676b;")
            bio_label.setWordWrap(True)
            name_layout.addWidget(bio_label)
        
        avatar_name_layout.addLayout(name_layout)
        
        # Add Action and Block buttons for non-main profiles (Friend Request System)
        if not is_main_user:
            # Get relationship status
            relationship = self.get_relationship_status(profile_folder_name)
            
            # Create the appropriate button based on relationship status
            if relationship == "friends":
                # Already friends - show Friends button with menu
                action_btn = QPushButton("Friends")
                action_btn.setFont(QFont("Arial", 11, QFont.Bold))
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #42b72a;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                    }
                    QPushButton:hover {
                        background-color: #36a420;
                    }
                """)
                action_btn.clicked.connect(lambda checked, fid=profile_folder_name: self.unfriend_user(fid))
            elif relationship == "request_sent":
                # We sent a request - show Request Sent (disabled)
                action_btn = QPushButton("Request Sent")
                action_btn.setFont(QFont("Arial", 11, QFont.Bold))
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e4e6eb;
                        color: #050505;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                    }
                """)
                # Optional: allow canceling request
                action_btn.clicked.connect(lambda checked, fid=profile_folder_name: (
                    self.cancel_friend_request(fid),
                    self.hide_profile(),
                    self.show_profile(fid)
                ))
            elif relationship == "request_received":
                # They sent a request - show Respond button
                action_btn = QPushButton("Respond")
                action_btn.setFont(QFont("Arial", 11, QFont.Bold))
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1877f2;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                    }
                    QPushButton:hover {
                        background-color: #166fe5;
                    }
                """)
                action_btn.clicked.connect(lambda checked, fid=profile_folder_name: (
                    QMessageBox.information(self, "Friend Request", "You have a friend request from this user. Check your notifications to respond."),
                    self.show_notifications_center()
                ))
            elif relationship == "mutual":
                # Both follow each other - can send friend request
                action_btn = QPushButton("+ Add Friend")
                action_btn.setFont(QFont("Arial", 11, QFont.Bold))
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1877f2;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                    }
                    QPushButton:hover {
                        background-color: #166fe5;
                    }
                """)
                action_btn.clicked.connect(lambda checked, fid=profile_folder_name: self.send_friend_request_with_confirmation(fid))
            elif relationship == "cooldown":
                # Request was declined - in 3-day cooldown
                action_btn = QPushButton("+ Add Friend")
                action_btn.setFont(QFont("Arial", 11, QFont.Bold))
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e4e6eb;
                        color: #9ca3af;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                    }
                """)
                action_btn.setEnabled(False)
                # Could add tooltip with cooldown info
                action_btn.setToolTip("You can send a friend request after 3 days from the declined request")
            elif relationship == "following":
                # We follow them but they don't follow back
                action_btn = QPushButton("Following")
                action_btn.setFont(QFont("Arial", 11, QFont.Bold))
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e4e6eb;
                        color: #050505;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                    }
                    QPushButton:hover {
                        background-color: #d8dadf;
                    }
                """)
                action_btn.clicked.connect(lambda checked, fid=profile_folder_name: self.unfollow_user_with_confirmation(fid))
            elif relationship == "followed_by":
                # They follow us but we don't follow back - can follow back and then add friend
                action_btn = QPushButton("+ Follow Back")
                action_btn.setFont(QFont("Arial", 11, QFont.Bold))
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1877f2;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                    }
                    QPushButton:hover {
                        background-color: #166fe5;
                    }
                """)
                action_btn.clicked.connect(lambda checked, fid=profile_folder_name: (
                    self.follow_user(fid),
                    self.hide_profile(),
                    self.show_profile(fid)
                ))
            else:  # "none" or any other case
                # No relationship - can follow
                action_btn = QPushButton("+ Follow")
                action_btn.setFont(QFont("Arial", 11, QFont.Bold))
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1877f2;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                    }
                    QPushButton:hover {
                        background-color: #166fe5;
                    }
                """)
                action_btn.clicked.connect(lambda checked, fid=profile_folder_name: self.follow_user_with_confirmation(fid))
            
            avatar_name_layout.addWidget(action_btn)
            
            # Check if already blocked
            already_blocked = self.is_blocked(profile_folder_name)
            
            if already_blocked:
                block_btn = QPushButton("Unblock")
                block_btn.setFont(QFont("Arial", 11))
                block_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #42b72a;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                    }
                    QPushButton:hover {
                        background-color: #36a420;
                    }
                """)
                block_btn.clicked.connect(lambda checked, fid=profile_folder_name: self.unblock_user_with_confirmation(fid))
            else:
                block_btn = QPushButton("🚫 Block")
                block_btn.setFont(QFont("Arial", 11))
                block_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e4e6eb;
                        color: #050505;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                    }
                    QPushButton:hover {
                        background-color: #d8dadf;
                    }
                """)
                block_btn.clicked.connect(lambda checked, fid=profile_folder_name: self.block_user_with_confirmation(fid))
            avatar_name_layout.addWidget(block_btn)
        
        avatar_name_layout.addStretch()
        
        header_layout.addLayout(avatar_name_layout)
        
        # Followers, Following, Friends counts
        counts_layout = QHBoxLayout()
        counts_layout.setSpacing(20)
        
        # Followers
        followers_btn = QPushButton(f"{followers_count} Followers")
        followers_btn.setFont(QFont("Arial", 11))
        followers_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #65676b;
                border: none;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #f0f2f5;
                border-radius: 4px;
            }
        """)
        followers_btn.clicked.connect(lambda: self.show_user_list(followers, "Followers", profile_folder_name))
        counts_layout.addWidget(followers_btn)
        
        # Following
        following_btn = QPushButton(f"{following_count} Following")
        following_btn.setFont(QFont("Arial", 11))
        following_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #65676b;
                border: none;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #f0f2f5;
                border-radius: 4px;
            }
        """)
        following_btn.clicked.connect(lambda: self.show_user_list(following, "Following", profile_folder_name))
        counts_layout.addWidget(following_btn)
        
        # Friends
        friends_btn = QPushButton(f"{friends_count} Friends")
        friends_btn.setFont(QFont("Arial", 11))
        friends_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #65676b;
                border: none;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #f0f2f5;
                border-radius: 4px;
            }
        """)
        friends_btn.clicked.connect(lambda: self.show_user_list(friends, "Friends", profile_folder_name))
        counts_layout.addWidget(friends_btn)
        
        counts_layout.addStretch()
        header_layout.addLayout(counts_layout)
        
        # Profile info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        
        # Location
        location = profile_data.get('location', '')
        if location:
            info_row = QHBoxLayout()
            info_icon = QLabel("📍")
            info_text = QLabel(location)
            info_text.setFont(QFont("Arial", 12))
            info_text.setStyleSheet("color: #65676b;")
            info_row.addWidget(info_icon)
            info_row.addWidget(info_text)
            info_row.addStretch()
            header_layout.addLayout(info_row)
        
        # Job
        job = profile_data.get('job', '')
        if job:
            info_row = QHBoxLayout()
            info_icon = QLabel("💼")
            info_text = QLabel(f"Works at {job}")
            info_text.setFont(QFont("Arial", 12))
            info_text.setStyleSheet("color: #65676b;")
            info_row.addWidget(info_icon)
            info_row.addWidget(info_text)
            info_row.addStretch()
            header_layout.addLayout(info_row)
        
        # Education
        degree = profile_data.get('degree', '')
        if degree:
            info_row = QHBoxLayout()
            info_icon = QLabel("🎓")
            info_text = QLabel(f"Studied at {degree}")
            info_text.setFont(QFont("Arial", 12))
            info_text.setStyleSheet("color: #65676b;")
            info_row.addWidget(info_icon)
            info_row.addWidget(info_text)
            info_row.addStretch()
            header_layout.addLayout(info_row)
        
        profile_layout.addWidget(profile_header)
        
        # Posts section
        posts_label = QLabel("Posts")
        posts_label.setFont(QFont("Arial", 18, QFont.Bold))
        posts_label.setStyleSheet("color: #050505;")
        profile_layout.addWidget(posts_label)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        # Store button references for highlighting
        self.all_posts_btn = QPushButton("All Posts")
        self.all_posts_btn.setFont(QFont("Arial", 12))
        self.all_posts_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
        """)
        self.all_posts_btn.clicked.connect(lambda: self.filter_profile_posts("all", profile_folder_name))
        filter_layout.addWidget(self.all_posts_btn)
        
        self.reposts_btn = QPushButton("Reposts")
        self.reposts_btn.setFont(QFont("Arial", 12))
        self.reposts_btn.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                color: #050505;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
        """)
        self.reposts_btn.clicked.connect(lambda: self.filter_profile_posts("shares", profile_folder_name))
        filter_layout.addWidget(self.reposts_btn)
        
        self.quotes_btn = QPushButton("Quotes")
        self.quotes_btn.setFont(QFont("Arial", 12))
        self.quotes_btn.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                color: #050505;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
        """)
        self.quotes_btn.clicked.connect(lambda: self.filter_profile_posts("quotes", profile_folder_name))
        filter_layout.addWidget(self.quotes_btn)
        
        # "Info" button
        info_btn = QPushButton("ℹ️ Info")
        info_btn.setFont(QFont("Arial", 12))
        info_btn.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                color: #050505;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d8dadf;
            }
        """)
        info_btn.clicked.connect(self.show_profile_real_info)
        filter_layout.addWidget(info_btn)
        
        # "Blocked" button - only for main user's profile
        if is_main_user:
            blocked_list = self.load_blocked()
            blocked_count = len(blocked_list)
            blocked_btn = QPushButton(f"🚫 Blocked ({blocked_count})")
            blocked_btn.setFont(QFont("Arial", 12))
            blocked_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e4e6eb;
                    color: #050505;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #d8dadf;
                }
            """)
            blocked_btn.clicked.connect(self.show_blocked_users)
            filter_layout.addWidget(blocked_btn)
        
        # Search input for profile posts
        self.profile_search_input = QLineEdit()
        self.profile_search_input.setPlaceholderText("Search posts...")
        self.profile_search_input.setFont(QFont("Arial", 11))
        self.profile_search_input.setFixedWidth(150)
        self.profile_search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f0f2f5;
                border-radius: 16px;
                padding: 8px 12px;
                border: 1px solid #dddfe2;
            }
        """)
        self.profile_search_input.returnPressed.connect(self.perform_profile_search)
        filter_layout.addWidget(self.profile_search_input)
        
        # Clear search button (hidden by default, shown when search is active)
        self.clear_profile_search_btn = QPushButton("✕")
        self.clear_profile_search_btn.setFont(QFont("Arial", 10))
        self.clear_profile_search_btn.setFixedSize(24, 24)
        self.clear_profile_search_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #65676b;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #e4e6eb;
            }
        """)
        self.clear_profile_search_btn.setVisible(False)
        self.clear_profile_search_btn.clicked.connect(self.clear_profile_search)
        filter_layout.addWidget(self.clear_profile_search_btn)
        
        filter_layout.addStretch()
        profile_layout.addLayout(filter_layout)
        
        # User's posts scroll area
        self.user_posts_scroll = QScrollArea()
        self.user_posts_scroll.setWidgetResizable(True)
        self.user_posts_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.user_posts_container = QWidget()
        self.user_posts_layout = QVBoxLayout(self.user_posts_container)
        self.user_posts_layout.setSpacing(15)
        self.user_posts_layout.addStretch()
        
        # Store current profile folder for filtering
        self.current_profile_folder = profile_folder_name
        
        # Store user posts for filtering
        self.current_filter = "all"  # all, shares, quotes
        
        # Load user's posts
        self.load_profile_posts("all", profile_folder_name)
        
        self.user_posts_scroll.setWidget(self.user_posts_container)
        profile_layout.addWidget(self.user_posts_scroll)
        
        profile_layout.addStretch()
        
        # Add profile widget to feed layout
        self.feed_layout.addWidget(self.profile_widget)
    
    def show_user_list(self, user_list, list_type, profile_folder):
        """Show a dialog with a list of users"""
        dialog = QDialog()
        dialog.setWindowTitle(f"{list_type}")
        dialog.setMinimumSize(400, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Scroll area for users
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        container = QWidget()
        users_layout = QVBoxLayout(container)
        users_layout.setSpacing(5)
        
        # Check if this is the main user's following list (for showing unfollow button)
        is_main_user_following = (profile_folder == "user" or profile_folder is None) and list_type == "Following"
        
        for user_id in user_list:
            # Load the user's profile
            user_profile = self.load_any_profile(user_id)
            if user_profile:
                first_name = user_profile.get('first_name', '')
                last_name = user_profile.get('last_name', '')
                full_name = f"{first_name} {last_name}".strip()
                
                # Row with name and action buttons
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(10)
                
                # User name button
                user_btn = QPushButton(full_name if full_name else "User")
                user_btn.setFont(QFont("Arial", 12))
                user_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f0f2f5;
                        color: #050505;
                        border: none;
                        border-radius: 6px;
                        padding: 10px 16px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #e4e6eb;
                    }
                """)
                user_btn.clicked.connect(lambda checked, uid=user_id: (
                    dialog.accept(),
                    self.show_profile(uid)
                ))
                row_layout.addWidget(user_btn, stretch=1)
                
                # Add unfollow button for main user's following list
                if is_main_user_following:
                    unfollow_btn = QPushButton("Unfollow")
                    unfollow_btn.setFont(QFont("Arial", 10))
                    unfollow_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #e4e6eb;
                            color: #050505;
                            border: none;
                            border-radius: 6px;
                            padding: 8px 12px;
                        }
                        QPushButton:hover {
                            background-color: #d8dadf;
                        }
                    """)
                    unfollow_btn.clicked.connect(lambda checked, uid=user_id: (
                        dialog.accept(),
                        self.unfollow_user_with_confirmation(uid)
                    ))
                    row_layout.addWidget(unfollow_btn)
                
                users_layout.addWidget(row_widget)
        
        users_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("✕ Close")
        close_btn.setFont(QFont("Arial", 11))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                color: #050505;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d8dadf;
            }
        """)
        close_btn.clicked.connect(dialog.reject)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def load_profile_posts(self, filter_type=None, profile_folder=None):
        """Load user's posts with optional filter (all, shares, quotes) - uses batch loading from profiles_feed.json"""
        # Load settings from profiles_feed.json
        settings = self.load_profile_feed_settings()
        self.profile_cache_size = settings.get("profile_cache_size", 30)
        self.profile_posts_per_batch = settings.get("profile_posts_per_batch", 10)
        self.profile_top_cleanup = settings.get("profile_top_cleanup", 5)
        
        # Clear existing posts
        for i in range(self.user_posts_layout.count() - 1):  # Keep the stretch
            item = self.user_posts_layout.itemAt(0)
            if item.widget():
                item.widget().deleteLater()
                self.user_posts_layout.removeItem(item)
        
        # Determine which profile to load posts for
        if profile_folder is None or profile_folder == "user":
            # Main user's posts
            first_name = self.user_profile.get('first_name', '')
            last_name = self.user_profile.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            user_name = full_name if full_name else "User"
            
            # Get posts from main user
            user_posts = [p for p in self.all_posts if p.get('username', '') == user_name]
        else:
            # Other user's posts - load from their folder
            other_profile = self.load_any_profile(profile_folder)
            if other_profile:
                first_name = other_profile.get('first_name', '')
                last_name = other_profile.get('last_name', '')
                full_name = f"{first_name} {last_name}".strip()
                user_name = full_name if full_name else "User"
            else:
                user_name = ""
            
            # Get posts from agent folder
            agent_posts = self.load_agent_posts(profile_folder)
            
            # Also check main posts.json for any posts from this user
            main_posts_matching = [p for p in self.all_posts if p.get('username', '') == user_name]
            
            # Combine posts
            user_posts = agent_posts + main_posts_matching
        
        # Apply filter
        if filter_type == "shares":
            # Filter for reposts (embedded_post is not None and is_quote is False)
            user_posts = [p for p in user_posts if p.get('embedded_post') and not p.get('is_quote', False)]
        elif filter_type == "quotes":
            # Filter for quotes (embedded_post is not None and is_quote is True)
            user_posts = [p for p in user_posts if p.get('embedded_post') and p.get('is_quote', False)]
        # If filter_type is "all" or None, show all posts
        
        # Sort by time (newest first)
        user_posts.sort(key=lambda x: x.get('time', ''), reverse=True)
        
        # Store all filtered posts for batch loading
        self.profile_all_filtered_posts = user_posts
        
        # Reset batch tracking
        self.profile_batch_start = 0
        self.current_profile_folder = profile_folder
        self.current_filter = filter_type
        
        # Load initial batch (profile_cache_size posts)
        initial_batch = user_posts[:self.profile_cache_size]
        self.profile_batch_start = len(initial_batch)
        
        for post_data in initial_batch:
            # Get folder_name from post data or use profile_folder
            folder_name = post_data.get('folder_name', None)
            if not folder_name:
                folder_name = profile_folder if profile_folder and profile_folder != "user" else None
            
            post_widget = PostWidget(
                post_data.get('username', 'Unknown'),
                post_data.get('avatar', '👤'),
                post_data.get('content', ''),
                post_data.get('time', datetime.now()),
                likes=post_data.get('likes', 0),
                comments=post_data.get('comments', 0),
                shares=post_data.get('shares', 0),
                embedded_post=post_data.get('embedded_post', None),
                is_quote=post_data.get('is_quote', False),
                edits=post_data.get('edits', []),
                is_edited=post_data.get('is_edited', False),
                folder_name=folder_name
            )
            self.user_posts_layout.insertWidget(self.user_posts_layout.count() - 1, post_widget)
        
        # Connect scroll handler for infinite scroll
        self.user_posts_scroll.verticalScrollBar().rangeChanged.connect(self.on_profile_scroll_changed)
    
    def on_profile_scroll_changed(self):
        """Handle scroll position changes for batch loading"""
        if not hasattr(self, 'profile_all_filtered_posts'):
            return
        
        scroll_bar = self.user_posts_scroll.verticalScrollBar()
        current_value = scroll_bar.value()
        max_value = scroll_bar.maximum()
        
        # Load more when user scrolls near bottom (within 100 pixels)
        if current_value >= max_value - 100:
            self.load_more_profile_posts()
        
        # Cleanup old posts when scrolling back up (keep only cache_size + batch)
        # Track scroll position to detect upward scrolling
        if hasattr(self, '_last_profile_scroll'):
            if current_value < self._last_profile_scroll:
                # User scrolled up - cleanup old posts
                self.cleanup_old_profile_posts()
        self._last_profile_scroll = current_value
    
    def load_more_profile_posts(self):
        """Load next batch of posts when scrolling down"""
        if not hasattr(self, 'profile_all_filtered_posts'):
            return
        
        # Check if there are more posts to load
        if self.profile_batch_start >= len(self.profile_all_filtered_posts):
            return  # All posts already loaded
        
        # Load next batch (profile_posts_per_batch posts)
        next_batch_end = min(self.profile_batch_start + self.profile_posts_per_batch, len(self.profile_all_filtered_posts))
        next_batch = self.profile_all_filtered_posts[self.profile_batch_start:next_batch_end]
        
        if not next_batch:
            return
        
        self.profile_batch_start = next_batch_end
        profile_folder = self.current_profile_folder
        
        for post_data in next_batch:
            # Get folder_name from post data or use profile_folder
            folder_name = post_data.get('folder_name', None)
            if not folder_name:
                folder_name = profile_folder if profile_folder and profile_folder != "user" else None
            
            post_widget = PostWidget(
                post_data.get('username', 'Unknown'),
                post_data.get('avatar', '👤'),
                post_data.get('content', ''),
                post_data.get('time', datetime.now()),
                likes=post_data.get('likes', 0),
                comments=post_data.get('comments', 0),
                shares=post_data.get('shares', 0),
                embedded_post=post_data.get('embedded_post', None),
                is_quote=post_data.get('is_quote', False),
                edits=post_data.get('edits', []),
                is_edited=post_data.get('is_edited', False),
                folder_name=folder_name
            )
            self.user_posts_layout.insertWidget(self.user_posts_layout.count() - 1, post_widget)
    
    def cleanup_old_profile_posts(self):
        """Remove oldest posts when scrolling back up to maintain cache size"""
        if not hasattr(self, 'profile_all_filtered_posts'):
            return
        
        # Count currently displayed widgets (excluding stretch)
        current_count = self.user_posts_layout.count() - 1
        target_max = self.profile_cache_size + self.profile_posts_per_batch
        
        if current_count <= target_max:
            return  # No cleanup needed yet
        
        # Remove oldest posts (from the beginning, keeping the stretch)
        posts_to_remove = min(self.profile_top_cleanup, current_count - target_max)
        
        for i in range(posts_to_remove):
            item = self.user_posts_layout.itemAt(0)
            if item.widget():
                item.widget().deleteLater()
                self.user_posts_layout.removeItem(item)
    
    def filter_profile_posts(self, filter_type, profile_folder=None):
        """Filter posts in profile view"""
        self.current_filter = filter_type
        
        # Update button highlighting
        self._update_filter_highlight(filter_type)
        
        self.load_profile_posts(filter_type, profile_folder)
    
    def _update_filter_highlight(self, active_filter):
        """Update the visual highlight for the active filter button"""
        # Styles for active (highlighted) and inactive buttons
        active_style = """
            QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
        """
        inactive_style = """
            QPushButton {
                background-color: #e4e6eb;
                color: #050505;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
        """
        
        # Apply styles based on active filter
        if active_filter == "all":
            self.all_posts_btn.setStyleSheet(active_style)
            self.reposts_btn.setStyleSheet(inactive_style)
            self.quotes_btn.setStyleSheet(inactive_style)
        elif active_filter == "shares":
            self.all_posts_btn.setStyleSheet(inactive_style)
            self.reposts_btn.setStyleSheet(active_style)
            self.quotes_btn.setStyleSheet(inactive_style)
        elif active_filter == "quotes":
            self.all_posts_btn.setStyleSheet(inactive_style)
            self.reposts_btn.setStyleSheet(inactive_style)
            self.quotes_btn.setStyleSheet(active_style)
    
    def perform_profile_search(self):
        """Perform search within the current profile's posts"""
        query = self.profile_search_input.text().strip()
        if not query:
            return
        
        # Clear existing posts
        for i in range(self.user_posts_layout.count() - 1):  # Keep the stretch
            item = self.user_posts_layout.itemAt(0)
            if item.widget():
                item.widget().deleteLater()
                self.user_posts_layout.removeItem(item)
        
        # Get the profile folder being viewed
        profile_folder = self.current_profile_folder
        
        # Search posts for this specific profile
        search_settings = self.load_search_settings()
        max_results = search_settings.get('profile_feed', {}).get('max_results', 30)
        results = self.search_profile_posts(query, profile_folder, max_results=max_results)
        
        # Apply current filter type to results
        filter_type = self.current_filter
        if filter_type == "shares":
            results = [p for p in results if p.get('embedded_post') and not p.get('is_quote', False)]
        elif filter_type == "quotes":
            results = [p for p in results if p.get('embedded_post') and p.get('is_quote', False)]
        
        # Sort by time (newest first)
        results.sort(key=lambda x: x.get('time', ''), reverse=True)
        
        # Show results or no results message
        if not results:
            no_results = QLabel("No posts found matching your search.")
            no_results.setFont(QFont("Arial", 12))
            no_results.setStyleSheet("color: #65676b;")
            no_results.setAlignment(Qt.AlignHCenter)
            self.user_posts_layout.insertWidget(self.user_posts_layout.count() - 1, no_results)
        else:
            for post_data in results:
                # Get folder_name from post data or use profile_folder
                folder_name = post_data.get('folder_name', None)
                if not folder_name:
                    folder_name = profile_folder if profile_folder and profile_folder != "user" else None
                
                post_widget = PostWidget(
                    post_data.get('username', 'Unknown'),
                    post_data.get('avatar', '👤'),
                    post_data.get('content', ''),
                    post_data.get('time', datetime.now()),
                    likes=post_data.get('likes', 0),
                    comments=post_data.get('comments', 0),
                    shares=post_data.get('shares', 0),
                    embedded_post=post_data.get('embedded_post', None),
                    is_quote=post_data.get('is_quote', False),
                    edits=post_data.get('edits', []),
                    is_edited=post_data.get('is_edited', False),
                    folder_name=folder_name
                )
                self.user_posts_layout.insertWidget(self.user_posts_layout.count() - 1, post_widget)
        
        # Show clear search button
        self.clear_profile_search_btn.setVisible(True)
    
    def clear_profile_search(self):
        """Clear profile search and restore normal view"""
        self.profile_search_input.clear()
        self.clear_profile_search_btn.setVisible(False)
        # Reload posts with current filter
        self.load_profile_posts(self.current_filter, self.current_profile_folder)
    
    def hide_profile(self):
        """Hide profile view and return to feed"""
        if self.profile_widget:
            self.profile_widget.setVisible(False)
            self.profile_widget.deleteLater()
            self.profile_widget = None
        
        # Show feed components
        self.post_area.setVisible(True)
        self.posts_scroll.setVisible(True)
        
        # Restore scroll position
        if self.navigation_stack:
            self.posts_scroll.verticalScrollBar().setValue(self.navigation_stack.pop())
    
    def perform_search(self):
        """Perform search and display results"""
        query = self.search_input.text().strip()
        if not query:
            return
        
        # Hide profile if visible
        if self.profile_widget:
            self.hide_profile()
        
        # Load search settings
        search_settings = self.load_search_settings()
        max_results = search_settings.get('main_feed', {}).get('max_results', 100)
        
        # Search posts
        results = self.search_posts(query, max_results=max_results)
        
        # Show search results
        self.show_search(query, results)
    
    def show_search(self, query, results):
        """Show search results view"""
        # If already viewing search, hide it first
        if self.search_widget:
            self.hide_search()
        
        # Store scroll position
        self.navigation_stack.append(self.posts_scroll.verticalScrollBar().value())
        
        # Hide feed components
        self.post_area.setVisible(False)
        self.posts_scroll.setVisible(False)
        
        # Create search widget
        self.search_widget = QWidget()
        search_layout = QVBoxLayout(self.search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(20)
        
        # Back button and search info
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        back_btn = QPushButton("⬅️ Back to Feed")
        back_btn.setFont(QFont("Arial", 12))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #166fe5;
            }
        """)
        back_btn.clicked.connect(self.hide_search)
        header_layout.addWidget(back_btn)
        
        search_layout.addLayout(header_layout)
        
        # Search results header
        results_label = QLabel(f'Search Results for "{query}" ({len(results)} posts)')
        results_label.setFont(QFont("Arial", 18, QFont.Bold))
        results_label.setStyleSheet("color: #050505;")
        search_layout.addWidget(results_label)
        
        if not results:
            no_results = QLabel("No posts found matching your search.")
            no_results.setFont(QFont("Arial", 14))
            no_results.setStyleSheet("color: #65676b;")
            no_results.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            search_layout.addWidget(no_results)
        else:
            # Search results scroll area
            search_scroll = QScrollArea()
            search_scroll.setWidgetResizable(True)
            search_scroll.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background-color: transparent;
                }
            """)
            
            search_container = QWidget()
            search_results_layout = QVBoxLayout(search_container)
            search_results_layout.setSpacing(15)
            search_results_layout.addStretch()
            
            for post_data in results:
                post_widget = PostWidget(
                    post_data.get('username', 'Unknown'),
                    post_data.get('avatar', '👤'),
                    post_data.get('content', ''),
                    post_data.get('time', datetime.now()),
                    likes=post_data.get('likes', 0),
                    comments=post_data.get('comments', 0),
                    shares=post_data.get('shares', 0),
                    embedded_post=post_data.get('embedded_post', None),
                    is_quote=post_data.get('is_quote', False),
                    edits=post_data.get('edits', []),
                    is_edited=post_data.get('is_edited', False)
                )
                search_results_layout.insertWidget(search_results_layout.count() - 1, post_widget)
            
            search_scroll.setWidget(search_container)
            search_layout.addWidget(search_scroll)
        
        search_layout.addStretch()
        
        # Add search widget to feed layout
        self.feed_layout.addWidget(self.search_widget)
    
    def hide_search(self):
        """Hide search view and return to feed"""
        if self.search_widget:
            self.search_widget.setVisible(False)
            self.search_widget.deleteLater()
            self.search_widget = None
        
        # Show feed components
        self.post_area.setVisible(True)
        self.posts_scroll.setVisible(True)
        
        # Clear search input
        self.search_input.clear()
        
        # Restore scroll position
        if self.navigation_stack:
            self.posts_scroll.verticalScrollBar().setValue(self.navigation_stack.pop())
    
    def show_profile_real_info(self):
        """Show full profile info in a dialog"""
        # Determine which profile to show
        if self.current_profile_folder == "user":
            profile_data = self.user_profile
            profile_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()
        else:
            profile_data = self.load_any_profile(self.current_profile_folder)
            if profile_data:
                profile_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()
            else:
                profile_data = self.user_profile
                profile_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()
        
        dialog = QDialog()
        dialog.setWindowTitle(f"{profile_name}'s Profile Info")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Header with avatar and name
        header_layout = QHBoxLayout()
        
        avatar_label = QLabel("👤")
        avatar_label.setFont(QFont("Arial", 48))
        header_layout.addWidget(avatar_label)
        
        name_layout = QVBoxLayout()
        first_name = profile_data.get('first_name', '')
        last_name = profile_data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        
        name_label = QLabel(full_name if full_name else "User")
        name_label.setFont(QFont("Arial", 20, QFont.Bold))
        name_label.setStyleSheet("color: #050505;")
        name_layout.addWidget(name_label)
        
        bio = profile_data.get('bio', '')
        if bio:
            bio_label = QLabel(bio)
            bio_label.setFont(QFont("Arial", 12))
            bio_label.setStyleSheet("color: #65676b;")
            bio_label.setWordWrap(True)
            name_layout.addWidget(bio_label)
        
        header_layout.addLayout(name_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #ced0d4;")
        layout.addWidget(divider)
        
        # Info sections
        info_fields = [
            ("📅 Birth Date", profile_data.get('birth_date', '')),
            ("🏠 Born In", profile_data.get('born_in', '')),
            ("📍 Lives In", profile_data.get('location', '')),
            ("💼 Works At", profile_data.get('job', '')),
            ("🎓 Studied At", profile_data.get('degree', '')),
            ("👤 Gender", profile_data.get('gender', '')),
            ("♂️ Sex", profile_data.get('sex', '')),
            ("💬 Languages", profile_data.get('language', '')),
            ("❤️ Relationship", profile_data.get('relationship', ''))
        ]
        
        for icon, value in info_fields:
            if value:
                info_row = QHBoxLayout()
                icon_label = QLabel(icon)
                icon_label.setFont(QFont("Arial", 14))
                text_label = QLabel(value)
                text_label.setFont(QFont("Arial", 12))
                text_label.setStyleSheet("color: #050505;")
                info_row.addWidget(icon_label)
                info_row.addWidget(text_label)
                info_row.addStretch()
                layout.addLayout(info_row)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Arial", 12))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                color: #050505;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d8dadf;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def create_header(self):
        self.header = QFrame()
        self.header.setFixedHeight(60)
        self.header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #dddfe2;
            }
        """)
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Logo
        logo = QLabel("facebook")
        logo.setFont(QFont("Arial", 24, QFont.Bold))
        logo.setStyleSheet("color: #1877f2;")
        header_layout.addWidget(logo)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Facebook")
        self.search_input.setFont(QFont("Arial", 13))
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f0f2f5;
                border-radius: 20px;
                padding: 10px 16px;
                border: none;
            }
        """)
        self.search_input.returnPressed.connect(self.perform_search)
        header_layout.addWidget(self.search_input)
        
        header_layout.addStretch()
        
        # Header buttons container
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Notification bell with badge
        notif_btn = QPushButton("🔔")
        notif_btn.setFont(QFont("Arial", 20))
        notif_btn.setFixedSize(40, 40)
        notif_btn.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                border-radius: 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d8dadf;
            }
        """)
        notif_btn.clicked.connect(self.show_notifications_center)
        buttons_layout.addWidget(notif_btn)
        
        # Notification badge (red circle with count)
        self.notif_badge = QLabel()
        self.notif_badge.setFont(QFont("Arial", 9, QFont.Bold))
        self.notif_badge.setStyleSheet("""
            QLabel {
                background-color: #ef4444;
                color: white;
                border-radius: 10px;
                min-width: 20px;
                max-width: 20px;
                min-height: 20px;
                max-height: 20px;
            }
        """)
        self.notif_badge.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.notif_badge.setFixedSize(20, 20)
        self.notif_badge.setVisible(False)
        # Position the badge over the notification bell
        self.notif_badge.setParent(notif_btn)
        self.notif_badge.move(25, -5)
        self.update_notification_badge()
        buttons_layout.addWidget(self.notif_badge)
        
        user_avatar = QPushButton("👤")
        user_avatar.setFont(QFont("Arial", 20))
        user_avatar.setFixedSize(40, 40)
        user_avatar.setStyleSheet("""
            QPushButton {
                background-color: #e4e6eb;
                border-radius: 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d8dadf;
            }
        """)
        user_avatar.clicked.connect(self.show_profile)
        buttons_layout.addWidget(user_avatar)
        
        header_layout.addLayout(buttons_layout)
    
    def create_post_area(self):
        self.post_area = QFrame()
        self.post_area.setFixedHeight(85)  # Increased height for better layout
        self.post_area.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #dddfe2;
            }
        """)
        
        layout = QVBoxLayout(self.post_area)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(4, 2, 4, 2)
        input_layout.setSpacing(8)  # More spacing between avatar and text
        
        avatar = QLabel("👤")
        avatar.setFont(QFont("Arial", 28))  # Larger font for emoji
        avatar.setFixedSize(40, 40)  # Match font size
        avatar.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)  # Center both vertically and horizontally
        avatar.setStyleSheet("QLabel { min-width: 40px; max-width: 40px; }")
        input_layout.addWidget(avatar)
        
        # Multi-line post input (compact)
        self.post_input = QTextEdit()
        self.post_input.setPlaceholderText("What's on your mind?")
        self.post_input.setFont(QFont("Arial", 12))
        self.post_input.setStyleSheet("""
            QTextEdit {
                background-color: #f0f2f5;
                border-radius: 14px;
                padding: 6px 12px;
                border: none;
                font-size: 12px;
            }
        """)
        self.post_input.setFixedHeight(36)
        self.post_input.setFixedWidth(380)
        input_layout.addWidget(self.post_input)
        
        layout.addLayout(input_layout)
        
        # Post button
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(4, 0, 4, 0)
        buttons_layout.addStretch()
        
        self.post_btn = QPushButton("Post")
        self.post_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.post_btn.setFixedSize(60, 24)
        self.post_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #166fe5;
            }
            QPushButton:pressed {
                background-color: #145dbf;
            }
        """)
        self.post_btn.clicked.connect(self.add_post)
        buttons_layout.addWidget(self.post_btn)
        
        layout.addLayout(buttons_layout)
    
    def add_post(self):
        content = self.post_input.toPlainText().strip()
        if content:
            # Get user info from profile
            first_name = self.user_profile.get('first_name', 'User')
            last_name = self.user_profile.get('last_name', '')
            username = f"{first_name} {last_name}".strip()
            avatar = "👤"
            
            # Get current timestamp
            timestamp = get_timestamp()
            
            # Generate deterministic post ID
            post_id = generate_deterministic_post_id('user', content, timestamp)
            
            # Create post data
            post_data = {
                'id': post_id,
                'username': username,
                'avatar': avatar,
                'content': content,
                'time': timestamp,
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'reports': 0,
                'reported_by': [],
                'edits': [],
                'is_edited': False,
                'embedded_post': None,
                'is_quote': False,
                'comments_list': [],  # Initialize empty comments list so PostWidget uses this reference
                'reacts': []  # Individual reaction records
            }
            
            # Add to posts list
            self.all_posts.append(post_data)
            self.save_posts()
            
            # Add to home.json feed for random_user access
            home_entry = {
                'id': post_id,
                'type': 'original',
                'author': username,
                'author_type': 'user',
                'content': content,
                'timestamp': timestamp,
                'likes': 0,
                'comments': 0,
                'shares': 0
            }
            self.add_to_home_feed('post', home_entry)
            
            # Create UI widget
            post = self.create_post_from_data(post_data)
            # Track displayed post ID
            post_id = post_data.get('id')
            if post_id:
                self.displayed_post_ids.add(post_id)
            
            self.post_input.clear()
            # Scroll to top when new post is added
            self.posts_scroll.verticalScrollBar().setValue(0)
    
    def scroll_to_top(self):
        self.posts_scroll.verticalScrollBar().setValue(0)
    
    def add_shared_post(self, username="You", emoji="🔄", content="", embedded_post=None, is_quote=False):
        # Get user info from profile
        first_name = self.user_profile.get('first_name', 'User')
        last_name = self.user_profile.get('last_name', '')
        display_name = f"{first_name} {last_name}".strip()

        # Get current timestamp
        timestamp = get_timestamp()

        # Generate deterministic post ID (same as add_post)
        post_id = generate_deterministic_post_id('user', content, timestamp)

        # Create post data
        post_data = {
            'id': post_id,
            'username': display_name,
            'avatar': emoji,
            'content': content,
            'time': timestamp,
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'reports': 0,
            'reported_by': [],
            'edits': [],
            'is_edited': False,
            'embedded_post': embedded_post,
            'is_quote': is_quote,
            'comments_list': [],  # Include comments_list like add_post does
            'folder_name': 'user',
            'reacts': []  # Individual reaction records
        }

        # Add to posts list
        self.all_posts.append(post_data)
        self.save_posts()

        # Create UI widget
        post = self.create_post_from_data(post_data)
        # Track displayed post ID
        post_id = post_data.get('id')
        if post_id:
            self.displayed_post_ids.add(post_id)
        self.posts_scroll.verticalScrollBar().setValue(0)

        # Trigger home feed rebuild to include the new quote/repost
        self._rebuild_home_feed(self.all_posts)


def main():
    app = QApplication([])
    
    # Set app-wide stylesheet for light mode
    app.setStyleSheet("""
        QApplication {
            font-family: Arial, Helvetica, sans-serif;
        }
    """)
    
    window = FacebookGUI()
    window.show()
    
    app.exec_()


if __name__ == "__main__":
    # Check execution phase
    base_dir = os.path.dirname(os.path.abspath(__file__))
    api_json_path = os.path.join(base_dir, "api.json")
    profile_path = os.path.join(base_dir, "user", "profile.json")
    
    if not os.path.exists(api_json_path):
        # Phase 1: First launch - create structure
        first_launch()
        # After first launch, run second launch then exit
        second_launch()
        sys.exit(0)
    elif not os.path.exists(profile_path) or os.path.getsize(profile_path) == 0:
        # Phase 2: Second launch - profile setup then exit
        second_launch()
        sys.exit(0)
    else:
        # Phase 3: Main application
        main()
# stable version before really integrating freind agent 1 code in it