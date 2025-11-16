# Delphi - System Verification Checklist

## ✅ Pre-Flight Checklist

Run through this checklist to verify your system is working correctly.

### 1. Environment Setup
- [ ] Python 3.12+ installed: `python --version`
- [ ] Poetry installed: `poetry --version`
- [ ] PostgreSQL installed and running: `pg_isready`
- [ ] `.env` file created from `.env.example`
- [ ] Database URL configured in `.env`

### 2. Database
```bash
# Run these commands and verify success
poetry run python scripts/init_db.py
# Should see: "✓ Database tables created successfully"

# Verify tables exist
psql delphi_ai -c "\dt"
# Should see: teams, players, games, box_scores, props, etc.
```

Expected tables (12 total):
- [ ] teams
- [ ] players
- [ ] games
- [ ] box_scores
- [ ] injury_reports
- [ ] stat_types
- [ ] prop_markets
- [ ] props
- [ ] odds_snapshots
- [ ] player_game_features
- [ ] prop_predictions
- [ ] posted_plays

### 3. Data Pipeline
```bash
# Backfill historical data
poetry run python -m data_pipeline.jobs.backfill_history
# Should see: "Historical data backfill complete"

# Verify data loaded
psql delphi_ai -c "SELECT COUNT(*) FROM teams;"
# Should see: 30

psql delphi_ai -c "SELECT COUNT(*) FROM players;"
# Should see: 150

psql delphi_ai -c "SELECT COUNT(*) FROM games;"
# Should see: ~450 (90 days * 5-10 games per day)

psql delphi_ai -c "SELECT COUNT(*) FROM box_scores;"
# Should see: thousands
```

Data verification:
- [ ] 30 teams inserted
- [ ] 150 players inserted
- [ ] ~450 games for last 90 days
- [ ] Box scores for completed games
- [ ] 3 stat types (points, assists, rebounds)

### 4. Machine Learning
```bash
# Train all models
poetry run python -m ml.training.train_all
# Should see training progress for points, assists, rebounds

# Verify models exist
ls -la models/
# Should see: points_model.txt, assists_model.txt, rebounds_model.txt
```

Model verification:
- [ ] points_model.txt exists and is not empty
- [ ] assists_model.txt exists and is not empty
- [ ] rebounds_model.txt exists and is not empty
- [ ] No errors during training
- [ ] Reasonable RMSE values (< 10 for points)

### 5. Feature Engineering & Scoring
```bash
# Run daily update
poetry run python -m data_pipeline.jobs.daily_update
# Should see: "Daily update job complete"

# Verify features created
psql delphi_ai -c "SELECT COUNT(*) FROM player_game_features;"
# Should see: hundreds of feature records

# Verify props created
psql delphi_ai -c "SELECT COUNT(*) FROM props WHERE prop_date = CURRENT_DATE;"
# Should see: dozens to hundreds

# Verify predictions created
psql delphi_ai -c "SELECT COUNT(*) FROM prop_predictions;"
# Should see: dozens to hundreds
```

Pipeline verification:
- [ ] Today's games created
- [ ] Props and odds generated
- [ ] Features built for today's players
- [ ] Predictions generated for all props
- [ ] No errors during pipeline

### 6. API Testing
```bash
# Start API in background
poetry run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &

# Wait a few seconds for startup
sleep 5

# Test health endpoint
curl http://localhost:8000/health
# Should see: {"status":"healthy"}

# Test root endpoint
curl http://localhost:8000/
# Should see: {"name":"Delphi","version":"1.0.0","status":"operational"}

# Test top props
curl "http://localhost:8000/v1/props/top?stat_type=points&min_edge=0.05&limit=5"
# Should see: JSON with props array

# Test player search
curl "http://localhost:8000/v1/players/search?q=LeBron&limit=5"
# Should see: JSON with players array

# Test games
curl "http://localhost:8000/v1/games/upcoming?limit=10"
# Should see: JSON with games array
```

API verification:
- [ ] Server starts without errors
- [ ] Health check returns 200
- [ ] Props endpoint returns data
- [ ] Player search works
- [ ] Games endpoint returns data
- [ ] No 500 errors
- [ ] Response times < 200ms

### 7. Discord Bot (Optional)
```bash
# Set Discord token
export DISCORD_BOT_TOKEN=your_actual_token

# Start bot
poetry run python -m discord_bot.bot
# Should see: "Bot logged in as YourBot#1234"
```

Bot verification:
- [ ] Bot connects successfully
- [ ] Bot appears online in Discord
- [ ] `/top` command works
- [ ] `/player` command works
- [ ] `/game` command works
- [ ] `/modelsheet` command works

### 8. Tests
```bash
# Run test suite
poetry run pytest tests/ -v

# Run with coverage
poetry run pytest tests/ --cov=backend --cov=ml --cov=data_pipeline
```

Test verification:
- [ ] test_ev_calculations.py passes (8/8)
- [ ] test_distributions.py passes (4/4)
- [ ] test_feature_engineering.py passes (1/1)
- [ ] test_props_service.py passes (3/3)
- [ ] Overall: 16/16 tests pass
- [ ] No warnings or errors

### 9. Docker (Optional)
```bash
# Build and start all services
cd infra
docker-compose up --build -d

# Check services are running
docker-compose ps
# Should see: db, redis, api, discord_bot all "Up"

# Initialize database inside container
docker-compose exec api python scripts/init_db.py
docker-compose exec api python -m data_pipeline.jobs.backfill_history
docker-compose exec api python -m ml.training.train_all
docker-compose exec api python -m data_pipeline.jobs.daily_update

# Test API
curl http://localhost:8000/health
```

Docker verification:
- [ ] All containers running
- [ ] Database container healthy
- [ ] API accessible on port 8000
- [ ] Discord bot connected
- [ ] No container crashes

### 10. End-to-End Smoke Test
```bash
# This script tests the complete flow
poetry run python -c "
from datetime import date
from backend.app.db import SessionLocal
from backend.app.db.models import Prop, PropPrediction

db = SessionLocal()
props = db.query(Prop).filter(Prop.prop_date == date.today()).count()
predictions = db.query(PropPrediction).count()
db.close()

print(f'Props: {props}')
print(f'Predictions: {predictions}')
assert props > 0, 'No props found'
assert predictions > 0, 'No predictions found'
print('✓ End-to-end test passed!')
"
```

Final verification:
- [ ] Props exist for today
- [ ] Predictions exist
- [ ] No database errors
- [ ] All systems operational

## 🎉 System Status

If all checks pass:
- ✅ **Database**: Working
- ✅ **Data Pipeline**: Working
- ✅ **Models**: Trained
- ✅ **API**: Operational
- ✅ **Tests**: Passing

**System Status: READY FOR PRODUCTION** 🚀

## 🐛 Troubleshooting Guide

### Database Connection Failed
```bash
# Check PostgreSQL is running
pg_isready -h localhost

# If not running, start it
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux

# Or use Docker
cd infra && docker-compose up -d db
```

### Models Not Training
```bash
# Check you have enough data
psql delphi_ai -c "SELECT COUNT(*) FROM box_scores;"
# Need at least 100+ box scores

# Check feature vectors exist
psql delphi_ai -c "SELECT COUNT(*) FROM player_game_features;"
# Need features for training
```

### API Returns Empty Results
```bash
# Run daily update again
poetry run python -m data_pipeline.jobs.daily_update

# Check date
# API defaults to today - make sure props exist for today
psql delphi_ai -c "SELECT COUNT(*) FROM props WHERE prop_date = CURRENT_DATE;"
```

### Import Errors
```bash
# Make sure you're running from project root
pwd  # Should show: /path/to/delphi

# Make sure poetry shell is active
poetry shell

# Reinstall dependencies
poetry install
```

## 📊 Expected Performance

After successful setup:

- **Database size**: ~50-100 MB (with 90 days of mock data)
- **API response time**: 50-200ms
- **Model training time**: 1-5 minutes (for all 3 models)
- **Daily update time**: 30-60 seconds
- **Props per day**: 100-500 (depending on games)
- **Memory usage**: 500MB-1GB (API + models)

## 🎯 Next Actions

Once all checks pass:

1. **Schedule daily jobs** (use cron or systemd timers)
2. **Replace mock providers** with real APIs
3. **Monitor performance** and retrain models weekly
4. **Track bets** in posted_plays table
5. **Iterate on features** and models

Enjoy your working prop prediction system! 🏀💰
