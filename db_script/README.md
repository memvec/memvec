db_script — schema helpers for mem_vec ✅

This folder contains a MySQL-compatible schema and a small runner script used to create the `memvec` database and the `events` and `memories` tables used by the application.

Files
- `create_schema.sql` — SQL that creates the `memvec` DB and the two tables.
- `create_schema.py` — small Python utility that reads the SQL file and executes it using `mysql-connector-python`.

How to run
1. Ensure `mysql-connector-python` is installed (it's already in `requirements.txt`).
2. Run the script:

   DB_HOST=127.0.0.1 DB_USER=root DB_PASSWORD=root python db_script/create_schema.py

Or pass options directly:

   python db_script/create_schema.py --host 127.0.0.1 --user root --password root

Notes
- The SQL uses `utf8mb4` and InnoDB.
- The `payload` and `value` columns are `JSON` (MySQL 5.7+ / 8.x).
- The script connects to the server and executes all statements in the SQL file. For CI, prefer providing a dedicated test DB and credentials.
