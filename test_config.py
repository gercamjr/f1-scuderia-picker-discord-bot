# Test Configuration for F1 Scuderia Picker Bot

# Test Database Settings
TEST_DB_PREFIX = "test_"
TEST_TIMEOUT = 30  # seconds

# Mock Data for Testing
MOCK_F1_TEAMS = [
    {
        'name': 'Red Bull Racing',
        'drivers': ['Max Verstappen', 'Sergio Perez']
    },
    {
        'name': 'Ferrari', 
        'drivers': ['Charles Leclerc', 'Carlos Sainz']
    },
    {
        'name': 'Mercedes',
        'drivers': ['Lewis Hamilton', 'George Russell']
    },
    {
        'name': 'McLaren',
        'drivers': ['Lando Norris', 'Oscar Piastri']
    },
    {
        'name': 'Aston Martin',
        'drivers': ['Fernando Alonso', 'Lance Stroll']
    }
]

# Test User Data
MOCK_USERS = [
    {'user_id': 100001, 'ea_username': 'testuser1', 'team': 'Red Bull Racing', 'driver': 'Max Verstappen'},
    {'user_id': 100002, 'ea_username': 'testuser2', 'team': 'Ferrari', 'driver': 'Charles Leclerc'},
    {'user_id': 100003, 'ea_username': 'testuser3', 'team': 'Mercedes', 'driver': 'Lewis Hamilton'},
]

# Test Scenarios
TEST_SCENARIOS = {
    'unique_constraint': {
        'description': 'Test unique driver constraint',
        'steps': [
            'User A selects Max Verstappen',
            'User B tries to select Max Verstappen (should fail)',
            'User B selects Lewis Hamilton (should succeed)'
        ]
    },
    'all_drivers_taken': {
        'description': 'Test behavior when all drivers are selected',
        'steps': [
            'Fill all driver slots',
            'New user tries to pick (should show no options)',
            'User changes pick (should free up a driver)'
        ]
    },
    'team_filtering': {
        'description': 'Test team filtering based on available drivers',
        'steps': [
            'Some drivers selected from each team',
            'Check that teams show correct availability counts',
            'Verify teams with no available drivers are hidden'
        ]
    }
}

# Expected Test Results
EXPECTED_RESULTS = {
    'total_drivers': 10,  # 5 teams × 2 drivers each
    'total_teams': 5,
    'min_available_after_selection': 8,  # After 2 drivers selected
    'max_concurrent_users': 10  # One per driver
}
