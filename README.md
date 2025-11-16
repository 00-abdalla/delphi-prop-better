# Delphi

**Delphi** is a fully-automated NBA player prop prediction system that ingests live and historical data, engineers features, trains gradient boosting models, and exposes predictions via FastAPI and Discord bot interfaces.

## Features

- **Data Ingestion**: NBA games, player stats, injuries, odds from multiple books (mock providers for V1)
- **Feature Engineering**: Rolling averages, minutes projections, game context, injury flags
- **ML Models**: LightGBM models for Points, Assists, Rebounds (mean + variance predictions)
- **EV & Edge Calculation**: Compare model probabilities vs sportsbook lines
- **FastAPI Backend**: REST endpoints for props, players, games, model sheets
- **Discord Bot**: Slash commands to query top edges and player props
- **PostgreSQL**: Full data persistence with SQLAlchemy 2.x ORM
- **Docker**: Containerized deployment with docker-compose

## Tech Stack

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy 2.x + Alembic
- PostgreSQL
- Redis (optional)
- LightGBM, numpy, pandas, scikit-learn, scipy
- discord.py
- httpx

## Quick Start (Local Development)

### Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Poetry

### Setup

1. **Clone and install dependencies**:
   ```bash
   poetry install
   poetry shell
   ```

2. **Set environment variables** - Create `.env`:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/delphi_ai
   REDIS_URL=redis://localhost:6379/0
   API_HOST=0.0.0.0
   API_PORT=8000
   MODEL_DIR=./models
   LOG_LEVEL=INFO
   DISCORD_BOT_TOKEN=your_discord_bot_token
   API_BASE_URL=http://localhost:8000
   ```

3. **Initialize database**:
   ```bash
   python scripts/init_db.py
   ```

4. **Backfill historical data** (mock):
   ```bash
   python -m data_pipeline.jobs.backfill_history
   ```

5. **Train models**:
   ```bash
   python -m ml.training.train_all
   ```

6. **Run daily update** (features + scoring):
   ```bash
   python -m data_pipeline.jobs.daily_update
   ```

7. **Start FastAPI server**:
   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Start Discord bot** (optional):
   ```bash
   python -m discord_bot.bot
   ```

## Quick Start (Docker)

```bash
cd infra
docker-compose up --build

# Initialize DB (inside container):
docker-compose exec api python scripts/init_db.py
docker-compose exec api python -m data_pipeline.jobs.backfill_history
docker-compose exec api python -m ml.training.train_all
docker-compose exec api python -m data_pipeline.jobs.daily_update
```

Access: http://localhost:8000 (Docs: http://localhost:8000/docs)

## API Endpoints

- `GET /v1/props/top` - Top edges by stat type
- `GET /v1/props/player/{player_id}` - Props for a player
- `GET /v1/props/game/{game_id}` - Props for a game
- `GET /v1/players/search?q=LeBron` - Search players
- `GET /v1/players/{player_id}/props` - Player props
- `GET /v1/games/{game_id}/props` - Game props
- `GET /v1/modelsheets/{date}` - Model sheet for date

## Discord Commands

- `/top [stat_type] [min_edge]` - Show top model edges
- `/player <name>` - Player props and edges
- `/game <id>` - Game props
- `/modelsheet [date]` - Full model sheet

## Testing

```bash
pytest tests/
```

## License

MIT
