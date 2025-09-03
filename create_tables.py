import sqlite3
import os
from pathlib import Path

class CreateTables:
    def __init__(self, db_name = "database/alertbot_db.sqlite"):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        base_dir = Path(__file__).resolve().parent
        os.makedirs(base_dir / "database", exist_ok=True)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS bambu_products (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT UNIQUE,
                            inserted_on DATETIME DEFAULT CURRENT_TIMESTAMP
                            )               
                        """)
      
        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS bambu_prices (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_id INTEGER,
                            normal_price REAL,
                            discount_price REAL,
                            inserted_on DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(product_id) REFERENCES bambu_products(id)
                            )
                        """)
        
        conn.commit()
        conn.close()