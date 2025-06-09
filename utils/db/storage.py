
import sqlite3 as lite

class DatabaseManager(object):

    def __init__(self, path):
        self.conn = lite.connect(path, check_same_thread=False)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()

    def _execute(self, arg, values=None):
        """A private method to execute queries, reducing redundancy."""
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur

    def create_tables(self):
        self.query('CREATE TABLE IF NOT EXISTS products (idx text, title text, body text, photo blob, price int, tag text)')
        self.query('CREATE TABLE IF NOT EXISTS orders (cid int, usr_name text, usr_address text, products text, status text)') # Added status column
        self.query('CREATE TABLE IF NOT EXISTS cart (cid int, idx text, quantity int)')
        self.query('CREATE TABLE IF NOT EXISTS categories (idx text, title text)')
        self.query('CREATE TABLE IF NOT EXISTS wallet (cid int, balance real)')
        self.query('CREATE TABLE IF NOT EXISTS questions (cid int, question text)')
        
    def query(self, arg, values=None):
        """For executing queries that modify the database (INSERT, UPDATE, DELETE)."""
        self._execute(arg, values)
        self.conn.commit()

    def fetchone(self, arg, values=None):
        """For fetching a single record."""
        cursor = self._execute(arg, values)
        return cursor.fetchone()

    def fetchall(self, arg, values=None):
        """For fetching all matching records."""
        cursor = self._execute(arg, values)
        return cursor.fetchall()
        
    def get_last_row_id(self):
        """Returns the row id of the most recently inserted row."""
        return self.cur.lastrowid

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Explicitly closes the connection."""
        if self.conn:
            self.conn.close()

    def __del__(self):
        self.close()


'''

products: idx text, title text, body text, photo blob, price int, tag text

orders: cid int, usr_name text, usr_address text, products text, status text

cart: cid int, idx text, quantity int ==> product_idx

categories: idx text, title text

wallet: cid int, balance real

questions: cid int, question text

'''
