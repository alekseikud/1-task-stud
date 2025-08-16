# Decision Log — `1-task-stud`

This document captures the key design/implementation decisions for the project, what exactly matches the original task, where I deviated (and why), and what I added beyond the spec.

---

## 1) Problem statement (from task)

- Create a relational schema (e.g., PostgreSQL) for two input files (`students`, `rooms`; many-to-one).
- Write a script that loads both files into the DB.
- Provide DB-level queries for:
  1. List of rooms with the number of students in each.
  2. Top-5 rooms with the smallest **average** student age.
  3. Top-5 rooms with the **largest age gap** among students.
  4. Rooms with **mixed genders**.
- Propose index optimizations and output an SQL script that adds necessary indexes.
- Export query results to **JSON** and **XML**.
- “Math” must be performed **in the DB** (not in app code).
- CLI should accept paths to `students` and `rooms`, DB connection info, and output format.
- No ORM; stick to SQL. Follow SOLID where sensible.

---

## 2) What was implemented **exactly as required**

### RDBMS & schema
- **PostgreSQL** with a simple **rooms ← students** model (1:N).
- DDL kept under `sql/` (tables, views, functions).  
  *Why:* explicit SQL = predictable; no accidental ORM semantics.

### Data loading
- Python loader using **psycopg[binary]** (`scripts/setup_db.py` / `insert_data`) to ingest JSON files into the DB.
- Type normalization and error handling are done before insert (see `scripts/setup_db.py` + `scripts/test_normalisation.py`).

### Queries at the **DB layer**
Implemented with SQL (no Python-side aggregation):
- **Rooms + student counts** (GROUP BY).
- **Top-5 smallest average age** (uses age calculation view).
- **Top-5 largest age gap** (max(age) - min(age) per room).
- **Mixed-gender rooms** (room containing ≥2 distinct genders).  
SQL lives in `sql/reporting/*.sql`; a helper view for age calculation is in `sql/create_ages_view.sql`.

### Export formats
- Results are exported to **JSON** and **XML** via `scripts/report.py`:
  - JSON: collect rows → `reports/json/*.json`.
  - XML: analogous export to `reports/xml/*.xml`.

### No ORM
- Direct **SQL** with `psycopg`. Parameterized statements; no ORM abstractions.

---

## 3) Indexing & performance choices

**Goal:** fast joins + reporting.

* **Primary keys via SQL:** `rooms(id)` and `students(id)` are primary keys, which (in Postgres) automatically create B-tree indexes on both columns.
* **FK join index:** added a **B-tree (non-clustered) index** on `students(room)` to speed up frequent joins and GROUP BYs on room.
* **Materialized view for reporting:** introduced a materialized view built on top of the `students` table that **stores `age` (derived from `date_of_birth`)** instead of DOB. The pipeline **refreshes this MV after each insert/seed step**, so reports read precomputed ages rather than recalculating them per query.
* **Where/why:** Keys/indexes and the MV are defined in SQL alongside the schema (`tables.sql` / `indexes.sql`) to keep bootstrap simple and deterministic; the join path `students(room) → rooms(id)` and age-based aggregations stay cheap without ORM overhead.

---

## 4) What was done **differently** from the task (and why)

- **Interface style:**  
  The task mentions a CLI with flags (paths, DB, output).  
  **I built an interactive menu** (see `main.py`) that runs setup once and then lets you trigger actions (`insert_data('rooms')`, `insert_data('students')`, export reports) by number.  
  *Why:* More readable and suitable for iterative testing under Docker; avoids retyping arguments. If strict CLI flags are required, it’s trivial to add `argparse` on top of this.

- **Runtime environment:**  
  The task didn’t require containers.  
  **I containerized** with **Docker Compose** (services: `db`, `app`), added healthchecks, and mounted host folders for datasets/reports.  
  *Why:* practice

- **DB bootstrap automation:**  
  Instead of assuming a preexisting DB/user, `reset_parameters()` creates/updates the **role** and **database** idempotently, sets **autocommit** for DROP/CREATE DATABASE, and applies **grants/default privileges**.  
  *Why:* accourding for the task main aim is: **CONNECT/USAGE/SELECT/INSERT/UPDATE/DELETE**, so it is reasonable to isolate **DB** from **DROP DATABASE** or **ALTER ROLE**

---

## 5) What was added **beyond** the spec

- **Full Docker workflow**  
  - `docker-compose.yaml`: Postgres + app, healthcheck using `pg_isready`.  
  - Bind mounts for `./datasets → /app/datasets` and `./reports → /app/reports`.

- **Interactive menu** after initial setup  
  - Runs `reset_parameters → grant_priveleges → create_tables → load_funtions` automatically on start.
  - Simple numerically-driven loop for seeding and reporting.

- **Idempotent setup & grants**  
  - Role creation is “create or alter password” (safe re-runs).  
  - Default privileges on `public` schema (future tables/sequences/functions get sensible grants).

- **Logging and simple UX**  
  - Minimal stdout confirms each step “done/failed”.  

- **Data normalization helpers + tests**  
  - Explicit type mapping/normalization for incoming JSON values.  
  - Unit tests for normalization logic.

---

## 6) Current limitations / trade-offs

- **Interactive over flags:** the menu is convenient but not the same as a strict CLI. If a CI pipeline or batch mode is required, I’ll add `argparse` flags for `--students`, `--rooms`, `--db-url`, `--out {json,xml}` and wire them before the menu loop.

---

## 7) Alternatives considered

- **MySQL vs PostgreSQL:** either works; PostgreSQL chosen since I am more familiar with it
- **Non-containerized setup:** it was firstly done, but I wanted to practice working with docker

---

## 8) Summary

The project delivers:
- Schema + loader for **rooms/students** (1:N), **pure SQL** queries for all required analytics, **JSON/XML exports**, and an **indexed** DB to support them.
- A **Docker-first**, idempotent bootstrap with health-checked Postgres and an interactive app to run seeding and reports quickly.
- Extras include automated DB/user creation, grants/default privileges, minimal UX, and normalization tests.

Deviations are intentional (interactive menu, containerization) to improve developer experience without violating core requirements (DB-level math, SQL only, exports, indexing).
