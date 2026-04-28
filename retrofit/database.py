import os
import sqlite3
from typing import List, Dict, Any


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            base = os.path.dirname(__file__)
            db_path = os.path.join(base, "data", "finance.db")
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """
        Create the loans table if it doesn't exist.
        Adds residual_value for leasing (migrates existing tables).
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    rate REAL NOT NULL,
                    term INTEGER NOT NULL,
                    payment REAL NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    residual_value REAL
                )
            """)
            conn.commit()
            # Migration: add residual_value if table existed from older schema
            cursor.execute("PRAGMA table_info(loans)")
            columns = [row[1] for row in cursor.fetchall()]
            if "residual_value" not in columns:
                cursor.execute("ALTER TABLE loans ADD COLUMN residual_value REAL")
                conn.commit()

    def save_calculation(self, calculation_data: Dict[str, Any]) -> int:
        """
        Save a loan or lease calculation to the database.
        For leasing, residual_value is stored; for loan it is None.
        Returns: The ID of the inserted record
        """
        residual = calculation_data.get("residual_value")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO loans (type, amount, rate, term, payment, start_date, end_date, residual_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    calculation_data["type"],
                    calculation_data["amount"],
                    calculation_data["rate"],
                    calculation_data["term"],
                    calculation_data["payment"],
                    calculation_data["start_date"],
                    calculation_data["end_date"],
                    residual,
                ),
            )
            conn.commit()
            last_row_id = cursor.lastrowid
            if last_row_id is None:
                raise ValueError("Failed to get the ID of the inserted record")
            return int(last_row_id)

    def get_all_calculations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all saved calculations from the database
        Returns: List of dictionaries containing calculation data
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM loans")
            rows = cursor.fetchall()

        # Convert to list of dictionaries
        return [dict(row) for row in rows]

    def delete_calculation(self, loan_id: int) -> bool:
        """
        Delete a calculation by ID
        Returns: True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM loans WHERE id = ?", (loan_id,))
            conn.commit()
            return cursor.rowcount > 0
