#!/usr/bin/env python3
"""
Quick test runner for F1 Scuderia Picker Bot

This script runs individual test categories for easier debugging and development.
"""

import sys
import os
import unittest
import tempfile
import sqlite3

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all required imports work"""
    print("🔍 Testing imports...")
    try:
        import discord
        from discord.ext import commands
        from discord import app_commands, ui, Interaction
        import requests
        import aiohttp
        from dotenv import load_dotenv
        import sqlite3
        import asyncio
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database_operations():
    """Test database operations with temporary database"""
    print("\n🗄️ Testing database operations...")
    
    # Create temporary database
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db_path = test_db.name
    test_db.close()
    
    try:
        # Initialize database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_picks (
                user_id INTEGER PRIMARY KEY,
                team TEXT NOT NULL,
                driver TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ea_username TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        
        # Test unique driver constraint
        def save_user_pick(user_id, ea_username, team, driver):
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT user_id FROM user_picks WHERE driver = ? AND user_id != ?', (driver, user_id))
            existing_pick = cursor.fetchone()
            
            if existing_pick:
                conn.close()
                return False
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_picks (user_id, ea_username, team, driver, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, ea_username, team, driver))
            
            conn.commit()
            conn.close()
            return True
        
        # Test 1: First user selects driver
        result1 = save_user_pick(1, 'user1', 'Red Bull Racing', 'Max Verstappen')
        print(f"  ✅ First user selecting Max Verstappen: {result1}")
        if result1 != True:
            raise AssertionError("First user should be able to select driver")
        
        # Test 2: Second user tries same driver
        result2 = save_user_pick(2, 'user2', 'Red Bull Racing', 'Max Verstappen')
        print(f"  ✅ Second user selecting Max Verstappen: {result2}")
        if result2 != False:
            raise AssertionError("Second user should NOT be able to select same driver")
        
        # Test 3: Second user selects different driver
        result3 = save_user_pick(2, 'user2', 'Mercedes', 'Lewis Hamilton')
        print(f"  ✅ Second user selecting Lewis Hamilton: {result3}")
        if result3 != True:
            raise AssertionError("Second user should be able to select different driver")
        
        # Test 4: Get selected drivers
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT driver FROM user_picks')
        results = cursor.fetchall()
        selected_drivers = {driver[0] for driver in results}
        conn.close()
        
        expected = {'Max Verstappen', 'Lewis Hamilton'}
        print(f"  ✅ Selected drivers: {selected_drivers}")
        if selected_drivers != expected:
            raise AssertionError(f"Selected drivers should be {expected}")
        
        print("✅ Database operations test passed")
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False
    finally:
        # Clean up
        os.unlink(test_db_path)

def test_driver_filtering_logic():
    """Test the logic for filtering available drivers"""
    print("\n🏎️ Testing driver filtering logic...")
    
    try:
        # Mock F1 teams data
        f1_teams = [
            {'name': 'Red Bull Racing', 'drivers': ['Max Verstappen', 'Sergio Perez']},
            {'name': 'Ferrari', 'drivers': ['Charles Leclerc', 'Carlos Sainz']},
            {'name': 'Mercedes', 'drivers': ['Lewis Hamilton', 'George Russell']}
        ]
        
        selected_drivers = {'Max Verstappen', 'Charles Leclerc'}
        
        # Test team filtering
        available_teams = []
        for team in f1_teams:
            available_drivers = [d for d in team['drivers'] if d not in selected_drivers]
            if available_drivers:
                available_teams.append({
                    'name': team['name'],
                    'available_count': len(available_drivers)
                })
        
        print(f"  ✅ Teams with available drivers: {len(available_teams)}")
        if len(available_teams) != 3:
            raise AssertionError("All teams should have available drivers")
        
        # Test driver filtering for specific team
        red_bull_drivers = ['Max Verstappen', 'Sergio Perez']
        available_red_bull = [d for d in red_bull_drivers if d not in selected_drivers]
        
        print(f"  ✅ Available Red Bull drivers: {available_red_bull}")
        if available_red_bull != ['Sergio Perez']:
            raise AssertionError("Only Sergio Perez should be available")
        
        # Test total count calculation
        total_drivers = sum(len(team['drivers']) for team in f1_teams)
        available_count = total_drivers - len(selected_drivers)
        
        print(f"  ✅ Total drivers: {total_drivers}, Available: {available_count}")
        if total_drivers != 6:
            raise AssertionError("Should have 6 total drivers")
        if available_count != 4:
            raise AssertionError("Should have 4 available drivers")
        
        print("✅ Driver filtering logic test passed")
        return True
        
    except Exception as e:
        print(f"❌ Driver filtering logic test failed: {e}")
        return False

def test_edge_cases():
    """Test edge cases and error scenarios"""
    print("\n🚨 Testing edge cases...")
    
    try:
        # Test empty driver list
        selected_drivers = set()
        team_drivers = []
        available = [d for d in team_drivers if d not in selected_drivers]
        if len(available) != 0:
            raise AssertionError("Empty team should have no available drivers")
        print("  ✅ Empty driver list handled correctly")
        
        # Test all drivers selected
        all_drivers = ['Driver1', 'Driver2', 'Driver3']
        selected_drivers = set(all_drivers)
        available = [d for d in all_drivers if d not in selected_drivers]
        if len(available) != 0:
            raise AssertionError("No drivers should be available when all selected")
        print("  ✅ All drivers selected scenario handled correctly")
        
        # Test case sensitivity (drivers should be exact match)
        selected_drivers = {'max verstappen'}  # lowercase
        team_drivers = ['Max Verstappen']  # proper case
        available = [d for d in team_drivers if d not in selected_drivers]
        if len(available) != 1:
            raise AssertionError("Case sensitivity should matter")
        print("  ✅ Case sensitivity handled correctly")
        
        print("✅ Edge cases test passed")
        return True
        
    except Exception as e:
        print(f"❌ Edge cases test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run the full test suite"""
    print("\n📋 Running comprehensive test suite...")
    try:
        from test_bot import run_tests
        result = run_tests()
        return result.wasSuccessful()
    except Exception as e:
        print(f"❌ Could not run comprehensive tests: {e}")
        return False

def main():
    """Main test runner"""
    print("🧪 F1 Scuderia Picker Bot - Quick Test Runner")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Database Operations", test_database_operations),
        ("Driver Filtering Logic", test_driver_filtering_logic),
        ("Edge Cases", test_edge_cases),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Quick Test Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All quick tests passed!")
        
        # Offer to run comprehensive tests
        print("\n🔬 Run comprehensive test suite? (y/n): ", end="")
        try:
            if input().lower().startswith('y'):
                success = run_comprehensive_tests()
                if success:
                    print("\n✅ All comprehensive tests passed!")
                    return 0
                else:
                    print("\n❌ Some comprehensive tests failed")
                    return 1
        except (KeyboardInterrupt, EOFError):
            # Handle user interruption gracefully
            print("\n⚠️  Test interrupted by user")
            pass
        
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    exit(main())
