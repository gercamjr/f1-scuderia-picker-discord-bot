import os
import discord
import requests
import aiohttp
import sqlite3
from discord.ext import commands
from discord import app_commands, ui, Interaction
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# API Endpoint
OPENF1_DRIVERS_URL = "https://api.openf1.org/v1/drivers"
OPENF1_MEETINGS_URL = "https://api.openf1.org/v1/meetings"

# Database file
DB_FILE = "f1_picks.db"

# A list to store F1 teams and drivers, which will be populated from the API
F1_TEAMS = []

def init_database():
    """Initialize the SQLite database and create the user_picks table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_picks (
            user_id INTEGER PRIMARY KEY,
            ea_username TEXT NOT NULL,
            team TEXT NOT NULL,
            driver TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if ea_username column exists, if not add it (for existing databases)
    cursor.execute("PRAGMA table_info(user_picks)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'ea_username' not in columns:
        cursor.execute('ALTER TABLE user_picks ADD COLUMN ea_username TEXT DEFAULT "Unknown"')
        print("Added ea_username column to existing database.")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def save_user_pick(user_id, ea_username, team, driver):
    """Save or update a user's team, driver pick, and EA username in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if the driver is already selected by another user
    cursor.execute('SELECT user_id FROM user_picks WHERE driver = ? AND user_id != ?', (driver, user_id))
    existing_pick = cursor.fetchone()
    
    if existing_pick:
        conn.close()
        return False  # Driver already taken by another user
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_picks (user_id, ea_username, team, driver, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, ea_username, team, driver))
    
    conn.commit()
    conn.close()
    return True  # Successfully saved

def get_user_pick(user_id):
    """Retrieve a user's pick from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT team, driver, ea_username FROM user_picks WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return {'team': result[0], 'driver': result[1], 'ea_username': result[2]}
    return None

def get_all_picks():
    """Retrieve all user picks from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id, team, driver, ea_username FROM user_picks ORDER BY updated_at DESC')
    results = cursor.fetchall()
    
    conn.close()
    
    picks = {}
    for user_id, team, driver, ea_username in results:
        picks[user_id] = {'ea_username': ea_username, 'team': team, 'driver': driver}
    
    return picks

def get_selected_drivers():
    """Retrieve all currently selected drivers from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT driver FROM user_picks')
    results = cursor.fetchall()
    
    conn.close()
    
    return {driver[0] for driver in results}  # Return a set of selected drivers

# Set up the bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def fetch_f1_data():
    """
    Fetches F1 team and driver data from the OpenF1 API and populates the F1_TEAMS list.
    """
    global F1_TEAMS
    
    print("Fetching F1 data from OpenF1 API...")
    try:
        async with aiohttp.ClientSession() as session:
            # Get the latest meeting key to ensure we have the most current data
            async with session.get(f"{OPENF1_MEETINGS_URL}?year=2025&country_name=Spain", timeout=10) as meetings_response:
                meetings_response.raise_for_status()
                meetings_data = await meetings_response.json()
                
                if not meetings_data:
                    print("Could not find latest meeting data from API.")
                    raise Exception("No meetings data found")

                latest_meeting_key = meetings_data[0]['meeting_key']

            # Fetch all drivers for the latest meeting
            async with session.get(f"{OPENF1_DRIVERS_URL}?meeting_key={latest_meeting_key}", timeout=10) as drivers_response:
                drivers_response.raise_for_status()
                drivers_data = await drivers_response.json()

                if not drivers_data:
                    print("No driver data found for the latest meeting.")
                    raise Exception("No drivers data found")

        # Process the data to group drivers by team
        teams_dict = {}
        for driver in drivers_data:
            team_name = driver.get('team_name')
            driver_full_name = f"{driver.get('first_name', '')} {driver.get('last_name', '')}".strip()
            
            if team_name and driver_full_name:
                if team_name not in teams_dict:
                    teams_dict[team_name] = {'name': team_name, 'drivers': []}
                teams_dict[team_name]['drivers'].append(driver_full_name)
        
        # Convert the dictionary back to a list
        F1_TEAMS = list(teams_dict.values())
        F1_TEAMS.sort(key=lambda x: x['name']) # Sort teams alphabetically
        print(f"Successfully fetched and processed data for {len(F1_TEAMS)} teams.")

    except Exception as e:
        print(f"An error occurred while fetching data from OpenF1 API: {e}")        
        
    if not F1_TEAMS:
        print("Fatal error: Could not fetch F1 data, and hardcoded list is empty. Bot cannot function.")
        # Consider a more robust shutdown or retry mechanism here
    
    # Store the processed data in an accessible format for the bot
    print("F1 data loaded. Teams and drivers are ready.")


# Modal for collecting EA username
class EAUsernameModal(ui.Modal, title='Enter Your EA Username'):
    def __init__(self):
        super().__init__()

    ea_username = ui.TextInput(
        label='EA Username',
        placeholder='Enter your EA username here...',
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: Interaction):
        # Start the team selection process after getting EA username
        if not F1_TEAMS:
            await interaction.response.send_message(
                "F1 data is not currently available. Please try again in a few moments.",
                ephemeral=True
            )
            return
        
        # Check if there are any available drivers left
        selected_drivers = get_selected_drivers()
        total_drivers = sum(len(team.get('drivers', [])) for team in F1_TEAMS)
        available_count = total_drivers - len(selected_drivers)
        
        if available_count == 0:
            await interaction.response.send_message(
                "All drivers have been selected while you were filling out the form! 🏁\nUse `/available` to see which drivers are taken or `/leaderboard` to see all picks.",
                ephemeral=True
            )
            return
        
        # Store the EA username in the view and proceed to team selection
        team_view = TeamSelectView(str(self.ea_username.value))
        await interaction.response.send_message(
            f'Thanks **{self.ea_username.value}**! Now please select your favorite F1 team:\n*({available_count} driver{"s" if available_count != 1 else ""} still available)*',
            view=team_view,
            ephemeral=True
        )

# A View for selecting the F1 Team using a dropdown menu
class TeamSelectView(ui.View):
    def __init__(self, ea_username):
        super().__init__()
        self.team = None
        self.ea_username = ea_username

        if not F1_TEAMS:
            # Create a dummy option when no data is available
            error_options = [discord.SelectOption(label='Error', description='Try again later.', value='error')]
            self.team_select_callback.options = error_options
            self.team_select_callback.placeholder = 'F1 data not available...'
            self.team_select_callback.disabled = True
            return

        # Get currently selected drivers to check which teams have available drivers
        selected_drivers = get_selected_drivers()

        # Create team options from F1_TEAMS data, ensuring unique team names
        # and showing only teams with available drivers
        seen_teams = set()
        team_options = []
        for team in F1_TEAMS:
            name = team.get('name')
            if name and name not in seen_teams:  # Ensure team has a name and is unique
                # Check if team has any available drivers
                available_drivers = [driver for driver in team.get('drivers', []) if driver not in selected_drivers]
                if available_drivers:  # Only show teams with available drivers
                    driver_count = len(available_drivers)
                    description = f"{driver_count} driver{'s' if driver_count != 1 else ''} available"
                    team_options.append(discord.SelectOption(
                        label=name, 
                        value=name,
                        description=description
                    ))
                    seen_teams.add(name)
        
        # Only add the select if we have valid options
        if team_options:
            self.team_select_callback.options = team_options
        else:
            # Fallback if no valid team options
            error_options = [discord.SelectOption(label='No teams available', description='All drivers have been selected', value='error')]
            self.team_select_callback.options = error_options
            self.team_select_callback.placeholder = 'All drivers taken...'
            self.team_select_callback.disabled = True

    @ui.select(placeholder='Choose your favorite F1 team...', custom_id='team_select')
    async def team_select_callback(self, interaction: Interaction, select: ui.Select):
        selected_value = select.values[0]
        
        # Handle error case
        if selected_value == 'error':
            await interaction.response.send_message(
                'No teams have available drivers. All drivers have been selected by other users.',
                ephemeral=True
            )
            self.stop()
            return
            
        self.team = selected_value
        selected_team_data = next((team for team in F1_TEAMS if team['name'] == self.team), None)
        
        if selected_team_data and selected_team_data.get('drivers'):
            driver_view = DriverSelectView(self.ea_username, self.team, selected_team_data['drivers'])
            await interaction.response.edit_message(
                content=f'You have selected **{self.team}**. Now, please choose your driver:',
                view=driver_view
            )
        else:
            await interaction.response.edit_message(
                content=f'Sorry, no drivers found for **{self.team}**. Please try again.',
                view=None
            )
        self.stop()

# A View for selecting the F1 Driver using a dropdown menu
class DriverSelectView(ui.View):
    def __init__(self, ea_username, team_name, drivers):
        super().__init__()
        self.ea_username = ea_username
        self.team_name = team_name

        # Get currently selected drivers to filter them out
        selected_drivers = get_selected_drivers()

        # Create driver options with proper validation, ensuring unique driver names
        # and filtering out already selected drivers
        seen_drivers = set()
        driver_options = []
        for driver in drivers:
            if (driver and driver not in seen_drivers and driver not in selected_drivers):
                driver_options.append(discord.SelectOption(label=driver, value=driver))
                seen_drivers.add(driver)
        
        # Only add the select if we have valid options
        if driver_options:
            self.driver_select_callback.options = driver_options
        else:
            # Fallback if no valid driver options
            error_options = [discord.SelectOption(label='No available drivers', description='All drivers from this team are taken', value='error')]
            self.driver_select_callback.options = error_options
            self.driver_select_callback.placeholder = 'No available drivers...'
            self.driver_select_callback.disabled = True

    @ui.select(placeholder='Choose your favorite driver...', custom_id='driver_select')
    async def driver_select_callback(self, interaction: Interaction, select: ui.Select):
        selected_value = select.values[0]
        
        # Handle error case
        if selected_value == 'error':
            await interaction.response.send_message(
                'No available drivers for this team. All drivers may already be selected by other users.',
                ephemeral=True
            )
            self.stop()
            return
            
        driver = selected_value
        
        # Attempt to save the pick - this will fail if the driver was just selected by someone else
        success = save_user_pick(interaction.user.id, self.ea_username, self.team_name, driver)
        
        if success:
            await interaction.response.edit_message(
                content=f'**Successfully saved your pick!**\n'
                f'**EA Username:** {self.ea_username}\n'
                f'**Team:** {self.team_name}\n'
                f'**Driver:** {driver}',
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f'**Sorry!** The driver **{driver}** was just selected by another user. Please try selecting a different driver or team.',
                view=None
            )
        self.stop()

# Bot ready event
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    # Initialize the database
    init_database()
    # Fetch F1 data when the bot is ready
    await fetch_f1_data()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# The slash command to start the selection process
@bot.tree.command(name="pick", description="Select your favorite F1 team and driver.")
async def pick(interaction: Interaction):
    if not F1_TEAMS:
        await interaction.response.send_message(
            "F1 data is not currently available. Please try again in a few moments.",
            ephemeral=True
        )
        return
    
    # Check if there are any available drivers left
    selected_drivers = get_selected_drivers()
    total_drivers = sum(len(team.get('drivers', [])) for team in F1_TEAMS)
    available_count = total_drivers - len(selected_drivers)
    
    if available_count == 0:
        await interaction.response.send_message(
            "All drivers have been selected! 🏁\nUse `/available` to see which drivers are taken or `/leaderboard` to see all picks.",
            ephemeral=True
        )
        return
    
    # Show EA username modal first
    ea_modal = EAUsernameModal()
    await interaction.response.send_modal(ea_modal)

# The slash command to view the user's current pick
@bot.tree.command(name="mypick", description="View your current F1 team and driver selection.")
async def my_pick(interaction: Interaction):
    user_id = interaction.user.id
    pick = get_user_pick(user_id)
    if pick:
        embed = discord.Embed(
            title="Your F1 Pick",
            description=f"**EA Username:** {pick['ea_username']}\n**Team:** {pick['team']}\n**Driver:** {pick['driver']}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(
            'You have not made a selection yet. Use `/pick` to get started!',
            ephemeral=True
        )

# The slash command to view the leaderboard
@bot.tree.command(name="leaderboard", description="View the picks of all users in this server.")
async def leaderboard(interaction: Interaction):
    all_picks = get_all_picks()
    if not all_picks:
        await interaction.response.send_message(
            "No picks have been made yet. Be the first to use `/pick`!",
            ephemeral=True
        )
        return

    leaderboard_str = ""
    for user_id, pick in all_picks.items():
        ea_username = pick.get('ea_username', 'Unknown')
        leaderboard_str += f"**{ea_username}:** {pick['team']} / {pick['driver']}\n"

    embed = discord.Embed(
        title="F1 Scuderia Leaderboard",
        description=leaderboard_str,
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

# The slash command to view available drivers
@bot.tree.command(name="available", description="View all available drivers that haven't been selected yet.")
async def available_drivers(interaction: Interaction):
    if not F1_TEAMS:
        await interaction.response.send_message(
            "F1 data is not currently available. Please try again in a few moments.",
            ephemeral=True
        )
        return

    selected_drivers = get_selected_drivers()
    available_str = ""
    total_available = 0

    for team in F1_TEAMS:
        team_name = team.get('name', 'Unknown Team')
        available_team_drivers = [driver for driver in team.get('drivers', []) if driver not in selected_drivers]
        
        if available_team_drivers:
            available_str += f"**{team_name}:** {', '.join(available_team_drivers)}\n"
            total_available += len(available_team_drivers)

    if total_available == 0:
        embed = discord.Embed(
            title="Available Drivers",
            description="All drivers have been selected! 🏁",
            color=discord.Color.red()
        )
    else:
        embed = discord.Embed(
            title=f"Available Drivers ({total_available} remaining)",
            description=available_str,
            color=discord.Color.green()
        )
    
    await interaction.response.send_message(embed=embed)

# Run the bot only if this script is executed directly
if __name__ == '__main__':
    if not TOKEN:  # This handles both None and empty string
        print("❌ Error: DISCORD_TOKEN environment variable not set")
        print("Please set the DISCORD_TOKEN in your .env file or environment variables")
        exit(1)
    bot.run(TOKEN)