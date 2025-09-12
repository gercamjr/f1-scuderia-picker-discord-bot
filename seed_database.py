#!/usr/bin/env python3
"""
Seed script to populate the F1 picks database with initial data from the Discord leaderboard.
"""

import sqlite3

# Database file
DB_FILE = "f1_picks.db"

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
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def save_user_pick(user_id, ea_username, team, driver):
    """Save or update a user's team, driver pick, and EA username in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_picks (user_id, ea_username, team, driver, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, ea_username, team, driver))
    
    conn.commit()
    conn.close()

def seed_leaderboard_data():
    """Seed the database with the leaderboard data from the Discord image."""
    
    # Data from the Discord leaderboard image
    # Using made-up Discord user IDs since we can't get the real ones from usernames
    seed_data = [
        (100000001, "gcadventure", "Aston Martin", "Fernando Alonso"),
        (100000002, "jphshield23", "Kick Sauber", "Nico Hulkenberg"),
        (100000003, "gacrmomo", "Aston Martin", "Lance Stroll"),
        (100000004, "jamesngoose69", "Red Bull Racing", "Max Verstappen"),
        (100000005, "lotusteve", "Kick Sauber", "Gabriel Bortoleto"),
        (100000006, "greyoak2462", "McLaren", "Oscar Piastri"),
        (100000007, "boonie7474", "McLaren", "Lando Norris"),
        (100000008, "scottyboy2373692", "Mercedes", "George Russell"),
    ]
    
    print("Seeding database with leaderboard data...")
    
    for user_id, ea_username, team, driver in seed_data:
        save_user_pick(user_id, ea_username, team, driver)
        print(f"Added pick for {ea_username} (ID: {user_id}): {team} / {driver}")
    
    print(f"\nSuccessfully seeded {len(seed_data)} user picks!")

def verify_data():
    """Verify that the data was inserted correctly."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM user_picks')
    count = cursor.fetchone()[0]
    
    cursor.execute('SELECT user_id, ea_username, team, driver FROM user_picks ORDER BY user_id')
    all_picks = cursor.fetchall()
    
    conn.close()
    
    print(f"\nDatabase verification:")
    print(f"Total picks in database: {count}")
    print("\nAll picks:")
    for user_id, ea_username, team, driver in all_picks:
        print(f"  {ea_username} (ID: {user_id}): {team} / {driver}")

if __name__ == "__main__":
    print("F1 Scuderia Picker - Database Seeding Script")
    print("=" * 50)
    
    # Initialize database
    init_database()
    
    # Seed with leaderboard data
    seed_leaderboard_data()
    
    # Verify the data
    verify_data()
    
    print("\nSeeding complete!")
