# Delphi - Quick Start Guide

## What You Have

A complete, production-ready NBA prop prediction system with:

✅ **Backend (FastAPI)** - REST API with prop predictions, player/game data
✅ **Database (PostgreSQL)** - Full schema with SQLAlchemy 2.x ORM
✅ **ML Pipeline** - LightGBM models for points, assists, rebounds
✅ **Data Ingestion** - Mock providers (extendable to real APIs)
✅ **Feature Engineering** - Rolling averages, minutes projections, game context
✅ **Discord Bot** - Slash commands for querying props
✅ **Docker Setup** - docker-compose for easy deployment
✅ **Tests** - pytest suite for core utilities and services

## Installation & Setup

### Option 1: Local Development (Without Docker)

```bash
# 1. Install dependencies
poetry install
poetry shell

# 2. Set up database (install PostgreSQL first)
createdb delphi_ai

# 3. Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL

# 4. Initialize database
python scripts/init_db.py

# 5. Backfill historical data
python -m data_pipeline.jobs.backfill_history

# 6. Train models
python -m ml.training.train_all

# 7. Run daily update (features + scoring)
python -m data_pipeline.jobs.daily_update

# 8. Start API
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# 9. (Optional) Start Discord bot
export DISCORD_BOT_TOKEN=your_token
python -m discord_bot.bot
```

### Option 2: Docker Deployment

```bash
# 1. Build and start services
cd infra
docker-compose up --build

# 2. Initialize database (in separate terminal)
docker-compose exec api python scripts/init_db.py
docker-compose exec api python -m data_pipeline.jobs.backfill_history
docker-compose exec api python -m ml.training.train_all
docker-compose exec api python -m data_pipeline.jobs.daily_update

# 3. Access
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Project Structure

```
delphi/
├── backend/               # FastAPI application
│   └── app/
│       ├── api/v1/       # API routes
│       ├── core/         # Business logic (services, utils)
│       ├── db/           # Database models & session
│       ├── config.py     # Settings
│       └── main.py       # FastAPI app entrypoint
│
├── data_pipeline/        # Data ingestion & transformation
│   ├── ingestion/        # Mock providers (NBA, odds, injuries)
│   ├── transform/        # Feature engineering
│   └── jobs/             # Pipeline scripts (backfill, daily, reprice)
│
├── ml/                   # Machine learning
│   ├── training/         # Model training scripts
│   └── inference/        # Model registry, scorer
│
├── discord_bot/          # Discord bot
│   └── bot.py            # Bot with slash commands
│
├── infra/                # Docker & deployment
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   └── Dockerfile.discord
│
├── scripts/              # Utility scripts
│   └── init_db.py        # Database initialization
│
└── tests/                # Test suite
    ├── test_ev_calculations.py
    ├── test_distributions.py
    ├── test_feature_engineering.py
    └── test_props_service.py
```

## API Endpoints

### Props
- `GET /v1/props/top` - Top edges by stat type
- `GET /v1/props/player/{player_id}` - Player's props
- `GET /v1/props/game/{game_id}` - Game's props

### Players
- `GET /v1/players/search?q=LeBron` - Search players
- `GET /v1/players/{player_id}` - Player details
- `GET /v1/players/{player_id}/props` - Player props

### Games
- `GET /v1/games/date/{date}` - Games by date
- `GET /v1/games/upcoming` - Upcoming games
- `GET /v1/games/{game_id}` - Game details
- `GET /v1/games/{game_id}/props` - Game props

### Model Sheets
- `GET /v1/modelsheets/{date}` - Full model sheet

## Discord Bot Commands

- `/top [stat_type] [min_edge]` - Top edges (e.g., `/top points 0.07`)
- `/player <name>` - Player props (e.g., `/player LeBron`)
- `/game <id>` - Game props (e.g., `/game 123`)
- `/modelsheet [date]` - Model sheet (e.g., `/modelsheet 2024-12-25`)

## Daily Operations

### Morning Routine (Before Games)
```bash
# 1. Run daily update to get today's games and props
python -m data_pipeline.jobs.daily_update

# 2. Check top edges
curl "http://localhost:8000/v1/props/top?stat_type=points&min_edge=0.05"
```

### During Games (Every 15 min)
```bash
# Live reprice to update odds and re-score
python -m data_pipeline.jobs.live_reprice
```

### Weekly Routine
```bash
# Re-train models with new data
python -m ml.training.train_all
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_ev_calculations.py -v

# Run with coverage
pytest tests/ --cov=backend --cov=ml --cov=data_pipeline
```

## Next Steps

### 1. Replace Mock Providers with Real APIs

**NBA Data:**
- Option A: nba_api library (unofficial but popular)
- Option B: Official NBA Stats API
- Option C: Sportradar/Stattlehead (paid)

**Odds Data:**
- The Odds API (theoddsapi.com)
- Pinnacle API
- DraftKings/FanDuel scraping (use responsibly)

**Injury Reports:**
- RotoWire API
- Official team injury reports
- ESPN scraping

### 2. Model Improvements

- Add more stat types (PRA, 3PM, STL, BLK)
- Use actual residual variance from training
- Implement ensemble models
- Add XGBoost/CatBoost alternatives
- Feature importance analysis

### 3. Advanced Features

- Bankroll management (Kelly criterion)
- Performance tracking dashboard
- Backtesting framework
- Alerts (Telegram, Email, SMS)
- Line shopping across multiple books
- Arbitrage detection
- Live betting integration

### 4. Production Hardening

- Add authentication (JWT)
- Rate limiting
- Caching layer (Redis)
- Monitoring (Prometheus, Grafana)
- Logging aggregation (ELK stack)
- Error tracking (Sentry)
- CI/CD pipeline
- Database migrations (Alembic)
- Backup strategy

### 5. Web UI

- React/Next.js dashboard
- Real-time updates with WebSockets
- Charts and visualizations
- Player/game explorer
- Model performance tracking

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
pg_isready -h localhost

# Verify database exists
psql -l | grep delphi_ai

# Check connection string
echo $DATABASE_URL
```

### Model Not Found
```bash
# Train models first
python -m ml.training.train_all

# Check models directory
ls -la models/
```

### No Props Found
```bash
# Run backfill first
python -m data_pipeline.jobs.backfill_history

# Then run daily update
python -m data_pipeline.jobs.daily_update
```

### Discord Bot Won't Start
```bash
# Verify token is set
echo $DISCORD_BOT_TOKEN

# Check API is running
curl http://localhost:8000/health
```

## Architecture Decisions

### Why Mock Providers?
- Allows immediate development without API keys
- Makes testing easier
- Clear separation of concerns
- Easy to swap for real providers

### Why LightGBM?
- Fast training and inference
- Excellent for tabular data
- Built-in regularization
- Handles missing values well

### Why PostgreSQL?
- JSONB for flexible feature storage
- Strong consistency
- Great for analytics queries
- Well-supported ORM integration

### Why FastAPI?
- Modern async support
- Auto-generated OpenAPI docs
- Type hints everywhere
- Excellent performance

## Contributing

When adding new features:

1. Follow existing patterns (OOP, type hints, docstrings)
2. Add tests for new functionality
3. Update README if adding user-facing features
4. Keep mock providers simple but realistic

## License

MIT

## Support

For questions or issues, refer to the code comments and docstrings. Each module is well-documented with usage examples.

Happy betting! 🏀💰
