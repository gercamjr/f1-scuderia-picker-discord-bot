#!/usr/bin/env python3
"""
Database management utility for the F1 Scuderia Picker bot.
Terminal-based tool to manage the SQLite database.
"""

import os
import sqlite3
import sys
from datetime import datetime

# Database file
DB_FILE = "f1_picks.db"


def reset_database():
    """Clear all user picks from the database."""
    if not os.path.exists(DB_FILE):
        print(f"❌ Database file '{DB_FILE}' not found.")
        return False

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM user_picks")
        count_before = cursor.fetchone()[0]

        # Clear all picks
        cursor.execute("DELETE FROM user_picks")

        conn.commit()
        conn.close()

        print(f"✅ Database reset successful!")
        print(f"   Removed {count_before} user pick(s)")
        print(f"   Users can now start fresh with /pick")
        print(f"   Reset completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True

    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False


def show_database_stats():
    """Show current database statistics."""
    if not os.path.exists(DB_FILE):
        print(f"❌ Database file '{DB_FILE}' not found.")
        print("   Run the bot once to create the database.")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Get total picks
        cursor.execute("SELECT COUNT(*) FROM user_picks")
        total_picks = cursor.fetchone()[0]

        # Get unique teams and drivers
        cursor.execute("SELECT COUNT(DISTINCT team) FROM user_picks")
        unique_teams = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT driver) FROM user_picks")
        unique_drivers = cursor.fetchone()[0]

        # Get all picks with timestamps
        cursor.execute(
            """
            SELECT ea_username, team, driver, updated_at 
            FROM user_picks 
            ORDER BY updated_at DESC
        """
        )
        picks = cursor.fetchall()

        conn.close()

        print(f"📊 F1 Scuderia Picker Database Statistics")
        print(f"   Database: {DB_FILE}")
        print(f"   Total picks: {total_picks}")
        print(f"   Unique teams selected: {unique_teams}")
        print(f"   Unique drivers selected: {unique_drivers}")
        print()

        if picks:
            print("Current picks (most recent first):")
            for ea_username, team, driver, updated_at in picks:
                print(f"   • {ea_username}: {team} / {driver} ({updated_at})")
        else:
            print("   📭 No picks found - database is empty")

        print(f"\n💡 To clear all picks: python db_reset.py reset")

    except Exception as e:
        print(f"❌ Error reading database: {e}")


def main():
    if len(sys.argv) < 2:
        print("🏁 F1 Scuderia Picker - Database Management")
        print()
        print("Usage:")
        print("  python db_reset.py reset    - Clear all user picks")
        print("  python db_reset.py stats    - Show database statistics")
        print("  python db_reset.py help     - Show this help message")
        print()
        print("Examples:")
        print("  python db_reset.py stats    # Check current picks")
        print("  python db_reset.py reset    # Clear everything (with confirmation)")
        return

    command = sys.argv[1].lower()

    if command == "reset":
        print(
            "🚨 WARNING: This will permanently delete ALL user picks from the database!"
        )
        print("   This action cannot be undone.")
        print()
        confirmation = input("Type 'RESET' (all caps) to confirm: ")

        if confirmation == "RESET":
            print("\nProceeding with database reset...")
            reset_database()
        else:
            print("❌ Reset cancelled - no changes made")

    elif command == "stats":
        show_database_stats()

    elif command in ["help", "--help", "-h"]:
        print("🏁 F1 Scuderia Picker - Database Management")
        print()
        print("This tool manages the SQLite database for the Discord bot.")
        print()
        print("Available commands:")
        print("  reset  - Clear all user picks (requires confirmation)")
        print("  stats  - Show current database statistics and all picks")
        print("  help   - Show this help message")
        print()
        print("The database stores:")
        print("  • User ID (Discord user ID)")
        print("  • EA Username")
        print("  • Selected F1 Team")
        print("  • Selected F1 Driver")
        print("  • Timestamp of selection")

    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python db_reset.py help' for available commands")


if __name__ == "__main__":
    main()
