#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from scripts.database import engine

def test_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            print("✅ Conexión a PostgreSQL exitosa")
    except Exception as e:
        print("❌ Error conectando a PostgreSQL")
        print(e)

if __name__ == "__main__":
    test_connection()