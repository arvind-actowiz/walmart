import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Optional
import json


class DatabaseManager:
    def __init__(self, db_config: Dict):
        """
        Initialize database connection with configuration
        
        Args:
            db_config: Dictionary containing database credentials
                {
                    'host': 'localhost',
                    'database': 'your_db',
                    'user': 'your_user',
                    'password': 'your_password',
                    'port': 3306
                }
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None

    def __enter__(self):
        """Connect to database when entering context manager"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection when exiting context manager"""
        self.close()

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)
            print("Successfully connected to database")
        except Error as e:
            print(f"Database connection failed: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")

    def execute_query(self, query: str, params: Optional[tuple] = None):
        """Execute a single SQL query"""
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return self.cursor
        except Error as e:
            self.connection.rollback()
            print(f"Query failed: {e}\nQuery: {query}")
            raise
    
        
    def insert_subcategories(self, subcategories: List[Dict]):
        """
        Insert scraped subcategories into database
        Args:
            subcategories: List of subcategories dictionaries with:
                - category_name
                - category_url
                - subcategory_name
                - subcategory_url
        """
        try:
            insert_query = """
                INSERT INTO subcategories (
                    category_name, category_url, subcategory_name, subcategory_url
                ) VALUES (
                    %(category_name)s, %(category_url)s, %(subcategory_url)s, %(subcategory_url)s)
            """
            
            self.cursor.executemany(insert_query, subcategories)
            self.connection.commit()
            print(f"Inserted/updated {len(subcategories)} subcategories")

        except Error as e:
            self.connection.rollback()
            print(f"Subcategories insertion failed: {e}")
            raise
    

