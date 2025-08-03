# f1-scuderia-picker-discord-bot

## Overview

F1 Scuderia Picker is a Discord bot that allows users to select their favorite Formula 1 team and driver using interactive dropdown menus. It fetches real-time data from the OpenF1 API and provides a leaderboard of user picks within the server.

## Features

- Select your favorite F1 team and driver via Discord slash commands
- Real-time data from the OpenF1 API
- View your current pick
- See a leaderboard of all user selections in the server

## Setup Instructions

1. **Clone the repository**
2. **Install Python 3.13 and create a virtual environment** (recommended)
3. **Install dependencies**:
   - `discord.py`
   - `aiohttp`
   - `requests`
   - `python-dotenv`
4. **Create a `.env` file** in the project root with your Discord bot token:

   ```env
   DISCORD_TOKEN=your-bot-token-here
   ```

5. **Run the bot**:

   ```bash
   source py-mac/bin/activate
   python bot.py
   ```

## Usage

- `/pick` — Start the selection process for your favorite team and driver
- `/mypick` — View your current selection
- `/leaderboard` — See all user picks in the server

## Notes

- The bot fetches the latest F1 teams and drivers for the Spanish Grand Prix (2025) from the OpenF1 API.
- All picks are stored in memory and reset when the bot restarts.

## License

MIT
