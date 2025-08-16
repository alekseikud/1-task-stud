# 1-task-stud

Python + Postgres pipeline that bootstraps a database, loads tables/functions, ingests JSON datasets, and generates JSON/XML reports. **Docker-only** workflow with an interactive in-container menu.

## Features
- Ensures app **database** and **role** (via admin creds).
- Applies schema and SQL functions from `sql/`.
- Seeds `rooms` and `students` from JSON.
- Generates **JSON** and **XML** reports into `reports/`.
- Simple interactive CLI menu.

## Project layout

```text
.
├── datasets
│   ├── parsed/
│   ├── rooms (1).json
│   ├── rooms (2).json
│   ├── students (1).json
│   └── students (2).json
├── docker-compose.yaml
├── Dockerfile
├── logger.log
├── main.py
├── README.md
├── reports/
├── requirements.txt
├── scripts
│   ├── __init__.py
│   ├── connection.py
│   ├── logger.py
│   ├── report.py
│   ├── setup_db.py
│   └── test_normalisation.py
└── sql
    ├── create_ages_view.sql
    ├── functions.sql
    ├── reporting
    │   ├── rooms_different_sex.sql
    │   ├── rooms_highest_age_diff.sql
    │   ├── rooms_lowest_avg_age.sql
    │   └── rooms_stud_number.sql
    └── tables.sql
````

> Cache files (e.g., `__pycache__`, `*.pyc`) intentionally omitted.

## Requirements

* Docker & Docker Compose

## Environment

Create a `.env` in the repo root:

```dotenv
# Admin (superuser) used by the db service and for bootstrapping
ADMIN=postgres
ADMIN_PASSWORD=postgres
ADMIN_DBNAME=postgres

# App DB user/db ensured by the setup step
APP_DB_USER=myuser
APP_DB_PASSWORD=mypass
APP_DB_NAME=mydb
```

Optional (libpq defaults used by psycopg):

```dotenv
PGHOST=db   # can be changed in docker-compose.yaml

PGPORT=5432 # is used as default (for change modify      
            # server_connect() in scripts/setup_db.py)
```

## Docker usage

Ensure host folders are mounted so inputs/outputs are visible on your machine:

```yaml
# docker-compose.yaml (app service)
volumes:
  - ./datasets:/app/datasets
  - ./reports:/app/reports
```

Bring services up and run the app **interactively** (menu needs a TTY):

```bash
docker compose up -d db
docker compose run --rm --service-ports app
```

Or keep the app running and exec into it:

```bash
docker compose up -d
docker compose exec -it app python -m main
```

## Interactive menu

After setup, you’ll see:

```
1. insert_data('rooms')
2. insert_data('students')
3. report_to_json()
4. report_to_xml()
5. report both (json+xml)
9. rerun full setup
0. exit
```

You can enter multiple actions at once, e.g. `1 2 5` or `1, 2, 5`.

## How it works (high level)

1. **reset\_parameters** — ensures app role/database using admin creds.
2. **grant\_priveleges** — grants schema usage/create and default privileges.
3. **create\_tables** — runs `sql/tables.sql` (+ views).
4. **load\_funtions** — loads `sql/functions.sql`.
5. **insert\_data** — loads JSON from `datasets/` into tables (reports disabled during seeding by default).
6. **report\_to\_json/xml** — runs reporting queries from `sql/reporting/` and writes to `reports/`.


## Notes

* `POSTGRES_*` envs in the `db` service only apply on **first init** of the volume; subsequent runs rely on the setup step.
* Don’t mount a named volume over `/app/datasets` or `/app/reports`; it will hide your bind mounts.
* Add `.DS_Store` and similar junk to `.gitignore`.

## License

```
MIT license
```
