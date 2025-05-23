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
    

    def get_pending_subcategories(self) -> List[Dict]:
        """Fetch subcategories that haven't been processed yet"""
        self.cursor.execute("""
            SELECT id, category_name, category_url, subcategory_name, subcategory_url
            FROM subcategories
            WHERE status IS NULL OR status != 'done'
        """)
        return self.cursor.fetchall()

    
    def insert_products(self, products: List[Dict]):
        """
        Insert scraped product details into the database.
        """
        try:
            insert_query = """
                INSERT INTO products (
                    item_id, upc, product_id, url, name, categories, 
                    image, store_id, store_location, price, mrp,
                    discount, availability, keyword, size
                ) VALUES (
                    %(item_id)s, %(upc)s, %(product_id)s, %(url)s, %(name)s, 
                    %(categories)s, %(image)s, %(store_id)s, %(store_location)s, 
                    %(price)s, %(mrp)s, %(discount)s, %(availability)s, 
                    %(keyword)s, %(size)s
                )
            """

            # Convert `categories` list to JSON string before insert
            for product in products:
                product["categories"] = json.dumps(product.get("categories", []))

            self.cursor.executemany(insert_query, products)
            self.connection.commit()
            print(f"Inserted/updated {len(products)} products")

        except Error as e:
            self.connection.rollback()
            print(f"Product insertion failed: {e}")
            raise

    def check_if_product_exists(self, product_url: str) -> bool:
        """
        Checks if a product with the given URL exists in the 'products' table.

        Args:
            product_url: The URL of the product to check.

        Returns:
            True if the product exists, False otherwise.
        """
        try:
            query = "SELECT 1 FROM products WHERE url = %s LIMIT 1"
            self.cursor.execute(query, (product_url,))
            result = self.cursor.fetchone()
            return result is not None
        except Error as e:
            print(f"Error checking product existence: {e}")
            raise
