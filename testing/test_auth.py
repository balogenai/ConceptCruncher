import unittest
import sqlite3
from backend.auth import register_user, authenticate_user, get_user_id, initialize_database
import os

class TestAuthFunctions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set environment variable for testing
        os.environ["TESTING"] = "true"
        # Initialize the database before running tests
        initialize_database()

    def setUp(self):
        # Clear the database before each test
        conn = sqlite3.connect("data/test_concept_cruncher.db")
        c = conn.cursor()
        c.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def test_register_user_success(self):
        result = register_user("testuser", "password123")
        self.assertTrue(result)

    def test_register_user_duplicate(self):
        register_user("testuser", "password123")
        result = register_user("testuser", "password123")
        self.assertFalse(result)

    def test_authenticate_user_success(self):
        register_user("testuser", "password123")
        result = authenticate_user("testuser", "password123")
        self.assertTrue(result)

    def test_authenticate_user_failure(self):
        register_user("testuser", "password123")
        result = authenticate_user("testuser", "wrongpassword")
        self.assertFalse(result)

    def test_get_user_id_success(self):
        register_user("testuser", "password123")
        user_id = get_user_id("testuser")
        self.assertIsNotNone(user_id)

    def test_get_user_id_failure(self):
        user_id = get_user_id("nonexistentuser")
        self.assertIsNone(user_id)

if __name__ == "__main__":
    unittest.main()