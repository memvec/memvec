#!/usr/bin/env python3
"""Run the SQL in `create_schema.sql` against a MySQL server.

Usage examples:
  python create_schema.py --host 127.0.0.1 --user root --password root
  DB_HOST=127.0.0.1 DB_USER=root DB_PASSWORD=root python create_schema.py
"""

import argparse
import os
import sys
import mysql.connector


def run_sql(host, port, user, password, sql_file):
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        cnx = mysql.connector.connect(host=host, port=port, user=user, password=password)
        cursor = cnx.cursor()
        # mysql-connector supports executing multiple statements with multi=True
        for result in cursor.execute(sql, multi=True):
            # iterate to ensure execution; errors will raise
            pass
        cnx.commit()
        print("Schema created (or already present).")
    except mysql.connector.Error as err:
        print("Error while creating schema:", err)
        sys.exit(1)
    finally:
        try:
            cursor.close()
            cnx.close()
        except Exception:
            pass


def parse_args():
    p = argparse.ArgumentParser(description="Apply SQL schema to a MySQL server")
    p.add_argument("--host", default=os.getenv("DB_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "3306")))
    p.add_argument("--user", default=os.getenv("DB_USER", "root"))
    p.add_argument("--password", default=os.getenv("DB_PASSWORD", ""))
    p.add_argument("--file", default=os.path.join(os.path.dirname(__file__), "create_schema.sql"))
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_sql(args.host, args.port, args.user, args.password, args.file)
