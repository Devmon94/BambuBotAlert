import sqlite3
from datetime import datetime

class QueriesDB:
    def __init__(self, db_name = "database/alertbot_db.sqlite"):
        self.db_name = db_name

    def _set_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  
        return conn

    def insert_bambu_product(self, name):
        conn = self._set_connection()
        cursor = conn.cursor()

        cursor.execute("""
                        INSERT OR IGNORE INTO bambu_products
                            (name)
                            VALUES
                            (?)
                       """,(
                            name,
                        ))
        
        conn.commit()
        conn.close()

    def insert_bambu_prices(self, product_id, normal_price, discount_price):
        conn = self._set_connection()
        cursor = conn.cursor()

        cursor.execute("""
                        INSERT OR IGNORE INTO bambu_prices
                            (product_id,
                             normal_price,
                             discount_price)
                            VALUES
                            (?, ?, ?)
                       """,(
                            product_id,
                            normal_price,
                            discount_price
                       ))
        
        conn.commit()
        conn.close()

    def select_bambu_product_id(self, name):
        conn = self._set_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM bambu_products WHERE name = ?",(name,))
        row = cursor.fetchone()
        
        conn.close()

        return row[0]
  
    def select_bambu_prices(self, product_id):
        conn = self._set_connection()
        cursor = conn.cursor()

        cursor.execute("""SELECT normal_price, discount_price FROM bambu_prices 
                           WHERE product_id = ?
                           ORDER BY inserted_on DESC""",(product_id,))
        row = cursor.fetchone()
        
        conn.close()

        if row:
            return row
        else:
            return None
    
    def select_bambu_historical_prices(self):
        conn = self._set_connection()
        cursor = conn.cursor()

        cursor.execute("""SELECT 
                            p.name,
                            h.normal_price,
                            h.discount_price,
                            h.inserted_on
                          FROM bambu_prices h
                          JOIN bambu_products p ON h.product_id = p.id
                          ORDER BY h.inserted_on DESC
                       """)
        
        rows = cursor.fetchall()
        conn.close()

        return rows