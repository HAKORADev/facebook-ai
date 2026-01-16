# Facebook AI Simulation Platform

**Status: Unfinished/In Development**  
*This project may never be completed. Contributions are welcome!*

## Overview

A PyQt5-based Facebook simulation platform that combines a social network GUI with autonomous AI agents. The application features a complete Facebook-like interface with post creation, comments, reactions, friend management, and an AI engine that simulates realistic user behavior using Google Gemini + LangChain.

## What Is Working

### Core Features

- **Profile Setup GUI** - First launch wizard for user profile creation
- **Main Feed** - Infinite scroll feed with posts, reactions, comments, and shares
- **Posts** - Create, edit, delete, and report posts with emoji reactions
- **Comments & Replies** - Nested comment threads with reactions and replies
- **Reactions** - Full reaction system (Like, Love, Haha, Wow, Sad, Angry)
- **Shares** - Repost and quote post functionality
- **Search** - Search posts by content across the platform
- **Profiles** - View user profiles with posts, followers, and following counts
- **Friend System** - Send, accept, decline, and manage friend requests

### AI Features

- **Random User Engine** - Autonomous AI that generates realistic social media behavior
- **Google Gemini Integration** - Uses LangChain for intelligent action generation
- **10 Pre-configured Agents** - Friend agents with unique personas and backgrounds
- **Context-Aware Actions** - AI considers platform context and user history

### Technical Features

- **JSON-Based Data Storage** - All data stored in human-readable JSON files
- **Local-First Architecture** - No external database required
- **Deterministic IDs** - Posts and content get consistent identifiers
- **Scroll Optimization** - Batch loading and memory-efficient post rendering

## What Is NOT Working / Incomplete

- **Live Updates** - The notification system and live feed updates are not implemented. The `handle_live_updates()` method has TODO comments for actual data source integration, whether through API polling, websocket, or other real-time mechanisms

- **Friend Agent 1 Integration** - The agent system framework is complete with 10 agent folders, each configured with unique personas, styles, and tools. However, the Friend Agent 1 code (the social interaction AI that was meant to power autonomous friend behavior) was never fully integrated into the main application. This represents the main unfinished piece of the project

- **Real API Integration** - This is a simulation with local JSON data and is not connected to actual Facebook, Instagram, or any real social media APIs. The platform exists entirely as a standalone local application

- **Real-Time Sync** - Multiple clients cannot synchronize data. Each instance of the application runs independently with its own local data store

- **Some UI Polish** - Minor UI inconsistencies and edge cases may exist throughout the application. The interface is functional but could benefit from additional testing and refinement

## Installation

### Prerequisites

- Python 3.8 or higher
- Google API Key (required for AI features to function)

### Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/HAKORADev/facebook-ai.git
   cd facebook-ai
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**

   ```bash
   python facebook.py
   ```

4. **First Launch Setup**

   On the first run, the application will automatically create the required folder structure, configuration files, and initial data directories. A profile setup wizard will then guide you through creating your profile, where you will enter your details including name, birth date, location, job title, relationship status, education, and a personal bio.

5. **Configure API Key**

   After the first launch, edit the `api.json` file that was automatically created in the application directory. Add your Google Gemini API key using the following format:

   ```json
   {
     "api_key": "YOUR_GOOGLE_API_KEY_HERE",
     "model": "gemini-1.5-flash"
   }
   ```

   You can obtain a free API key from Google AI Studio at https://aistudio.google.com/app/apikey

## Project Structure

```
facebook-ai/
├── facebook.py           # Main application file containing all GUI and AI code
├── requirements.txt      # Python dependencies
├── LICENSE              # MIT License
├── README.md            # This file
├── api.json             # API configuration (created automatically on first launch)
├── user/                # Main user data directory
│   ├── profile.json     # User profile information
│   ├── posts.json       # Posts created by the main user
│   ├── followers.json   # List of followers
│   ├── following.json   # List of accounts being followed
│   ├── friends.json     # List of confirmed friends
│   ├── interactions.json
│   ├── notifications.json
│   ├── blocked.json
│   └── messages/        # Direct messages storage
├── agents/              # AI friend agents directory
│   └── friends/         # 10 agent folders numbered 1 through 10
│       └── {N}/
│           ├── profile.json
│           ├── persona.json
│           ├── style.json
│           ├── config.json
│           ├── tools.json
│           └── messages/
└── system/              # System configuration and algorithms
    ├── algorithms/      # Feed algorithm settings in JSON format
    ├── platform/        # Platform description for AI context
    ├── feed/            # Feed data storage
    └── random_user/     # Random user AI configuration and tools
```

## For Developers

This project was abandoned mid-development. If you find it interesting or useful, you are very welcome to continue development from where it stopped.

### Priority Tasks for Completion

1. **Complete Live Updates** - Implement the `handle_live_updates()` method with a real-time data source. This could involve adding API polling intervals, websocket connections for instant updates, or another mechanism that allows the feed to refresh automatically without user intervention

2. **Integrate Friend Agent 1** - Connect the existing agent framework to the main GUI. The agents directory contains all the necessary configuration files and structure, but the actual AI logic needs to be hooked into the main application loop to enable autonomous friend behavior

3. **API Integration** - Add support for real social media APIs if you want to extend this beyond a local simulation. This would require OAuth handling, API rate limiting, and significant restructuring

4. **Multi-Instance Sync** - Add a server/client architecture to enable data synchronization between multiple instances running on different machines

### Extending the Platform

- **Add New Agents** - Create new folders in `agents/friends/` with profile, persona, style, config, and tools JSON files. Each agent can have unique characteristics and behaviors

- **Modify Algorithms** - Edit the JSON files in `system/algorithms/` to change how the feed is sorted, how content is recommended, and how often new content appears

- **Customize AI** - Update `system/random_user/tools.json` to add new AI actions or modify how the random user engine behaves

- **Style Changes** - Modify the PyQt5 stylesheets embedded in the code to change colors, spacing, fonts, and visual appearance throughout the application

### Architecture Notes

- The GUI is built with **PyQt5**. For newer Python versions or additional features, consider migrating to PyQt6 or PySide6
- AI features use **LangChain + Google Gemini**. This can be swapped for other LLMs like OpenAI, Anthropic, or local models by updating the initialization code
- All data is stored in **JSON files**, making it easy to backup, migrate, or manually edit content
- **Deterministic post IDs** are generated using content hashing combined with timestamps, ensuring consistent identifiers across sessions

## License

MIT License - See LICENSE file for details.

## Contact

For questions, suggestions, or contributions, feel free to reach out through GitHub issues or pull requests. This project was created as a personal experiment in building social simulation software.

---

**Final Note:** This is a personal project that may never be finished. The code represents a snapshot of work-in-progress rather than a polished product. If you find it useful, want to learn from it, or want to continue development, you are very welcome to do so. The community has made many excellent forks and improvements to similar projects, and this one is waiting for someone to pick it up where it left off.
