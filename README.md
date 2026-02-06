# LED Monitor Docker Stack

This project spins up a MySQL database together with a FastAPI backend that ingests the JSON payload defined in `json_scanboard.docx` and keeps the `monitor.sql` schema up to date.

## What's Included
- **MySQL 8.4** with the schema from `monitor.sql` applied automatically (`db/schema.sql`).
- **FastAPI backend** (`backend/app`) exposing:
  - `GET /health` – container readiness probe.
  - `POST /ingest` – accepts the LED monitor JSON payload and refreshes the database snapshot for the provided `sys.port`.
  - `GET /monitor/{device_id}` – returns the last stored snapshot for a given `device_id`.
- **Docker Compose** orchestration plus an `.env.example` to keep credentials in sync.

## Running Locally
1. Copy the environment template if you want to override credentials (including host bindings/ports to avoid clashes with other services):
   ```bash
   cp .env.example .env
   ```
2. Build and start everything:
   ```bash
   docker compose up --build
   ```
3. Send a payload once the backend is healthy:
   ```bash
   curl -X POST http://localhost:8000/ingest \
     -H 'Content-Type: application/json' \
     -d @sample_payload.json
   ```

## Git Workflow for Deployment
1. Initialize the repository locally (already done in this workspace) and point it to your remote:
   ```bash
   git remote add origin <git-url>
   git add .
   git commit -m "Initial stack"
   git push -u origin main
   ```
2. On the deployment server, install Docker + docker compose and ensure SSH access to the Git remote.
3. Copy `scripts/deploy.sh` to the server (or run directly from the repo) and set the required env vars before executing:
   ```bash
   export REPO_URL=git@github.com:you/led-monitor.git
   export WORKDIR=/opt/led-monitor
   export BRANCH=main
   ./scripts/deploy.sh
   ```
   - First run clones the repository into `$WORKDIR`.
   - Subsequent runs fetch the latest commits, check out `$BRANCH`, and run `docker compose up -d --build`.
4. To deploy new changes, push to the remote `main` branch and rerun the script (or wrap it in a systemd timer/CI job for automation).

The script never touches credentials; configure them through `.env` (ignored by Git) and keep production secrets on the server only.

## Payload Expectations
`POST /ingest` validates the payload exactly as described in `json_scanboard.docx`, adding `sys.dev` for your internal device ID:
- `ts` must be ISO-8601.
- `sys` describes the control system. `dev` is your internal identifier (stored as `device_id`) and `port` is the COM port. For backward compatibility you may also send a root-level `device_id`; the service will use `sys.dev` first and fall back to the root field.
- `snds` is an array of objects with `i`, `dvi`, `vid` (0/1 accepted).
- `bds` is an array of 6-item lists `[sender, port, board, status, temperature, voltage]`. Status short codes (`OK`, `E`, `U`) are normalized to the ENUM values defined in `monitor.sql`.
- Duplicate `snds[].i` or `bds[][sender,port,board]` entries are automatically deduplicated per payload, keeping the last occurrence.

`GET /monitor/{device_id}` devuelve el último snapshot persistido con el mismo formato (más una marca de tiempo ISO en `ts` y `snds[].last_update`). Usa este endpoint para alimentar dashboards sin tocar directamente MySQL.

Each request replaces the snapshot (`sending_card`, `scan_board`) for the matching `control_system`. Historic deltas are out of scope by design.

## MySQL Access
Credentials and port bindings come from `.env` (see `.env.example`). By default:
- DB host bind IP: `127.0.0.1`
- DB host port: `3306`
- Database: `monitor`
- User: `monitor`
- Password: `monitorpass`

Use `docker compose exec db mysql -u monitor -pmonitorpass monitor` to inspect data.

If those host ports collide with other services, edit `.env`:
```env
DB_HOST_BIND=127.0.0.1   # or another interface/IP
DB_PORT=13306            # exposed host port -> container 3306
BACKEND_HOST_BIND=0.0.0.0
BACKEND_PORT=18000       # exposed host port -> container 8000
```
The compose file reads these variables so you can run multiple stacks side by side without port conflicts.

## Development Notes
- The backend uses SQLAlchemy 2.x with the PyMySQL driver.
- `db/schema.sql` re-creates the `monitor` database if needed, so you can drop volumes safely.
- When `sys.init = 0`, the payload is still persisted (even if `snds`/`bds` are empty) to capture controller state.
4. Consultar datos almacenados para una pantalla:
   ```bash
   curl http://localhost:8000/monitor/DEVICE-123
   ```
   Sustituye `DEVICE-123` por el `sys.dev` usado al ingerir datos.
