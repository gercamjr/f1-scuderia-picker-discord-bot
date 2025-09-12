#!/usr/bin/env python3
"""
Test suite for F1 Scuderia Picker Discord Bot

This test suite covers:
- Database functions and unique driver constraints
- Bot imports and basic functionality
- Edge cases and error handling
"""

import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add the current directory to Python path to import bot modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestDatabaseFunctions(unittest.TestCase):
    """Test database operations and unique driver constraints"""

    def setUp(self):
        """Set up a temporary test database for each test"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.test_db_path = self.test_db.name
        self.test_db.close()

        # Initialize test database with same schema as main app
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_picks (
                user_id INTEGER PRIMARY KEY,
                team TEXT NOT NULL,
                driver TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ea_username TEXT NOT NULL
            )
        """
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.test_db_path)

    def save_user_pick(self, user_id, ea_username, team, driver):
        """Test version of save_user_pick using test database"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Check if the driver is already selected by another user
        cursor.execute(
            "SELECT user_id FROM user_picks WHERE driver = ? AND user_id != ?",
            (driver, user_id),
        )
        existing_pick = cursor.fetchone()

        if existing_pick:
            conn.close()
            return False  # Driver already taken by another user

        cursor.execute(
            """
            INSERT OR REPLACE INTO user_picks (user_id, ea_username, team, driver, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (user_id, ea_username, team, driver),
        )

        conn.commit()
        conn.close()
        return True  # Successfully saved

    def get_selected_drivers(self):
        """Test version of get_selected_drivers using test database"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT driver FROM user_picks")
        results = cursor.fetchall()
        conn.close()
        return {driver[0] for driver in results}

    def get_all_picks(self):
        """Test version of get_all_picks using test database"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, team, driver, ea_username FROM user_picks ORDER BY updated_at DESC"
        )
        results = cursor.fetchall()
        conn.close()

        picks = {}
        for user_id, team, driver, ea_username in results:
            picks[user_id] = {
                "ea_username": ea_username,
                "team": team,
                "driver": driver,
            }
        return picks

    def get_user_pick(self, user_id):
        """Test version of get_user_pick using test database"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT team, driver, ea_username FROM user_picks WHERE user_id = ?",
            (user_id,),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return {"team": result[0], "driver": result[1], "ea_username": result[2]}
        return None

    def test_unique_driver_constraint(self):
        """Test that drivers can only be selected once"""
        # First user selects Max Verstappen
        result1 = self.save_user_pick(1, "user1", "Red Bull Racing", "Max Verstappen")
        self.assertTrue(result1, "First user should be able to select Max Verstappen")

        # Second user tries to select the same driver
        result2 = self.save_user_pick(2, "user2", "Red Bull Racing", "Max Verstappen")
        self.assertFalse(
            result2, "Second user should NOT be able to select Max Verstappen"
        )

        # Second user selects a different driver
        result3 = self.save_user_pick(2, "user2", "Mercedes", "Lewis Hamilton")
        self.assertTrue(result3, "Second user should be able to select Lewis Hamilton")

    def test_user_can_change_pick(self):
        """Test that users can change their own pick"""
        # User selects initial driver
        result1 = self.save_user_pick(1, "user1", "Ferrari", "Charles Leclerc")
        self.assertTrue(result1, "User should be able to make initial selection")

        # User changes to different driver
        result2 = self.save_user_pick(1, "user1", "Mercedes", "George Russell")
        self.assertTrue(result2, "User should be able to change their selection")

        # Verify the change was saved
        pick = self.get_user_pick(1)
        self.assertEqual(
            pick["driver"],
            "George Russell",
            "Driver should be updated to George Russell",
        )
        self.assertEqual(pick["team"], "Mercedes", "Team should be updated to Mercedes")

    def test_get_selected_drivers(self):
        """Test retrieving all selected drivers"""
        # Add some test data
        self.save_user_pick(1, "user1", "Ferrari", "Charles Leclerc")
        self.save_user_pick(2, "user2", "Mercedes", "Lewis Hamilton")
        self.save_user_pick(3, "user3", "Red Bull Racing", "Max Verstappen")

        selected = self.get_selected_drivers()
        expected = {"Charles Leclerc", "Lewis Hamilton", "Max Verstappen"}
        self.assertEqual(selected, expected, f"Selected drivers should be {expected}")

    def test_get_all_picks(self):
        """Test retrieving all user picks"""
        # Add test data
        self.save_user_pick(1, "testuser1", "Ferrari", "Charles Leclerc")
        self.save_user_pick(2, "testuser2", "Mercedes", "Lewis Hamilton")

        picks = self.get_all_picks()

        self.assertEqual(len(picks), 2, "Should have 2 picks")
        self.assertIn(1, picks, "User 1 should be in picks")
        self.assertIn(2, picks, "User 2 should be in picks")

        self.assertEqual(picks[1]["ea_username"], "testuser1")
        self.assertEqual(picks[1]["team"], "Ferrari")
        self.assertEqual(picks[1]["driver"], "Charles Leclerc")

    def test_get_user_pick(self):
        """Test retrieving a specific user's pick"""
        # User with no pick
        pick = self.get_user_pick(999)
        self.assertIsNone(pick, "Non-existent user should return None")

        # User with a pick
        self.save_user_pick(1, "testuser", "McLaren", "Lando Norris")
        pick = self.get_user_pick(1)

        self.assertIsNotNone(pick, "User should have a pick")
        self.assertEqual(pick["ea_username"], "testuser")
        self.assertEqual(pick["team"], "McLaren")
        self.assertEqual(pick["driver"], "Lando Norris")


class TestBotImports(unittest.TestCase):
    """Test that all required modules can be imported"""

    def test_discord_imports(self):
        """Test Discord.py imports"""
        try:
            import discord
            from discord import Interaction, app_commands, ui
            from discord.ext import commands

            self.assertTrue(True, "Discord imports successful")
        except ImportError as e:
            self.fail(f"Discord imports failed: {e}")

    def test_standard_library_imports(self):
        """Test standard library imports"""
        try:
            import asyncio
            import os
            import sqlite3

            self.assertTrue(True, "Standard library imports successful")
        except ImportError as e:
            self.fail(f"Standard library imports failed: {e}")

    def test_third_party_imports(self):
        """Test third-party library imports"""
        try:
            import aiohttp
            import requests
            from dotenv import load_dotenv

            self.assertTrue(True, "Third-party imports successful")
        except ImportError as e:
            self.fail(f"Third-party imports failed: {e}")


class TestBotFunctionality(unittest.TestCase):
    """Test bot functionality without actually running Discord client"""

    def setUp(self):
        """Set up test environment"""
        # Mock F1_TEAMS data for testing
        self.mock_f1_teams = [
            {"name": "Red Bull Racing", "drivers": ["Max Verstappen", "Sergio Perez"]},
            {"name": "Ferrari", "drivers": ["Charles Leclerc", "Carlos Sainz"]},
            {"name": "Mercedes", "drivers": ["Lewis Hamilton", "George Russell"]},
        ]

    def test_team_filtering_logic(self):
        """Test logic for filtering teams with available drivers"""
        selected_drivers = {"Max Verstappen", "Charles Leclerc"}

        # Simulate filtering logic
        available_teams = []
        for team in self.mock_f1_teams:
            available_drivers = [
                d for d in team["drivers"] if d not in selected_drivers
            ]
            if available_drivers:
                available_teams.append(
                    {
                        "name": team["name"],
                        "available_count": len(available_drivers),
                        "available_drivers": available_drivers,
                    }
                )

        self.assertEqual(
            len(available_teams), 3, "All teams should have some available drivers"
        )

        # Red Bull should have 1 available (Sergio Perez)
        red_bull = next(t for t in available_teams if t["name"] == "Red Bull Racing")
        self.assertEqual(red_bull["available_count"], 1)
        self.assertIn("Sergio Perez", red_bull["available_drivers"])
        self.assertNotIn("Max Verstappen", red_bull["available_drivers"])

        # Ferrari should have 1 available (Carlos Sainz)
        ferrari = next(t for t in available_teams if t["name"] == "Ferrari")
        self.assertEqual(ferrari["available_count"], 1)
        self.assertIn("Carlos Sainz", ferrari["available_drivers"])
        self.assertNotIn("Charles Leclerc", ferrari["available_drivers"])

    def test_driver_availability_check(self):
        """Test driver availability checking logic"""
        selected_drivers = {"Max Verstappen", "Lewis Hamilton"}
        team_drivers = ["Max Verstappen", "Sergio Perez"]

        # Filter available drivers
        available_drivers = [d for d in team_drivers if d not in selected_drivers]

        self.assertEqual(len(available_drivers), 1)
        self.assertEqual(available_drivers[0], "Sergio Perez")
        self.assertNotIn("Max Verstappen", available_drivers)

    def test_all_drivers_taken_scenario(self):
        """Test scenario where all drivers are taken"""
        all_drivers = []
        for team in self.mock_f1_teams:
            all_drivers.extend(team["drivers"])

        selected_drivers = set(all_drivers)  # All drivers selected

        # Check if any teams have available drivers
        available_teams = []
        for team in self.mock_f1_teams:
            available_drivers = [
                d for d in team["drivers"] if d not in selected_drivers
            ]
            if available_drivers:
                available_teams.append(team)

        self.assertEqual(
            len(available_teams), 0, "No teams should have available drivers"
        )

    def test_driver_count_calculation(self):
        """Test calculation of total and available driver counts"""
        total_drivers = sum(len(team["drivers"]) for team in self.mock_f1_teams)
        selected_drivers = {"Max Verstappen", "Charles Leclerc"}
        available_count = total_drivers - len(selected_drivers)

        self.assertEqual(total_drivers, 6, "Should have 6 total drivers")
        self.assertEqual(available_count, 4, "Should have 4 available drivers")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error scenarios"""

    def setUp(self):
        """Set up test database"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.test_db_path = self.test_db.name
        self.test_db.close()

        # Initialize test database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_picks (
                user_id INTEGER PRIMARY KEY,
                team TEXT NOT NULL,
                driver TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ea_username TEXT NOT NULL
            )
        """
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.test_db_path)

    def test_empty_database(self):
        """Test functions with empty database"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Test get_selected_drivers with empty database
        cursor.execute("SELECT driver FROM user_picks")
        results = cursor.fetchall()
        selected = {driver[0] for driver in results}
        self.assertEqual(len(selected), 0, "Empty database should return empty set")

        # Test get_all_picks with empty database
        cursor.execute(
            "SELECT user_id, team, driver, ea_username FROM user_picks ORDER BY updated_at DESC"
        )
        results = cursor.fetchall()
        picks = {}
        for user_id, team, driver, ea_username in results:
            picks[user_id] = {
                "ea_username": ea_username,
                "team": team,
                "driver": driver,
            }

        self.assertEqual(len(picks), 0, "Empty database should return empty picks dict")
        conn.close()

    def test_database_connection_error(self):
        """Test handling of database connection errors"""
        # Try to connect to non-existent database path
        try:
            conn = sqlite3.connect("/invalid/path/database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            self.fail("Should have raised an exception")
        except sqlite3.OperationalError:
            # Expected behavior
            pass

    def test_duplicate_user_id_update(self):
        """Test updating existing user pick (same user_id)"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Insert initial pick
        cursor.execute(
            """
            INSERT INTO user_picks (user_id, ea_username, team, driver)
            VALUES (?, ?, ?, ?)
        """,
            (1, "testuser", "Ferrari", "Charles Leclerc"),
        )
        conn.commit()

        # Update same user's pick
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_picks (user_id, ea_username, team, driver, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (1, "testuser", "Mercedes", "Lewis Hamilton"),
        )
        conn.commit()

        # Verify only one record exists for this user
        cursor.execute("SELECT COUNT(*) FROM user_picks WHERE user_id = ?", (1,))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1, "Should have only one record per user")

        # Verify the pick was updated
        cursor.execute("SELECT team, driver FROM user_picks WHERE user_id = ?", (1,))
        result = cursor.fetchone()
        self.assertEqual(result[0], "Mercedes", "Team should be updated")
        self.assertEqual(result[1], "Lewis Hamilton", "Driver should be updated")

        conn.close()


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_classes = [
        TestDatabaseFunctions,
        TestBotImports,
        TestBotFunctionality,
        TestEdgeCases,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return result


if __name__ == "__main__":
    print("🧪 Running F1 Scuderia Picker Bot Test Suite")
    print("=" * 60)

    result = run_tests()

    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    if result.wasSuccessful():
        print("\n✅ All tests passed! 🎉")
        exit(0)
    else:
        print(f"\n❌ {len(result.failures + result.errors)} test(s) failed")
        exit(1)
