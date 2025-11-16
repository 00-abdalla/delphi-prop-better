#!/bin/bash

# Delphi - Complete Setup Script
# Run this to set up and test the entire system

set -e  # Exit on error

echo "🚀 Delphi - Complete Setup"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Install dependencies
echo -e "\n${BLUE}Step 1: Installing dependencies...${NC}"
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Installing..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

poetry install
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 2: Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\n${BLUE}Step 2: Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo "⚠️  Please edit .env with your database credentials"
    echo "   Then run this script again"
    exit 0
fi

# Step 3: Check database connection
echo -e "\n${BLUE}Step 3: Checking database connection...${NC}"
if command -v pg_isready &> /dev/null; then
    if pg_isready -h localhost > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is running${NC}"
    else
        echo "❌ PostgreSQL is not running"
        echo "   Start it with: brew services start postgresql"
        echo "   Or use Docker: cd infra && docker-compose up -d db"
        exit 1
    fi
else
    echo "⚠️  pg_isready not found (PostgreSQL may not be installed)"
fi

# Step 4: Initialize database
echo -e "\n${BLUE}Step 4: Initializing database...${NC}"
poetry run python scripts/init_db.py
echo -e "${GREEN}✓ Database initialized${NC}"

# Step 5: Backfill historical data
echo -e "\n${BLUE}Step 5: Backfilling historical data (this may take a minute)...${NC}"
poetry run python -m data_pipeline.jobs.backfill_history
echo -e "${GREEN}✓ Historical data loaded${NC}"

# Step 6: Train models
echo -e "\n${BLUE}Step 6: Training models (this may take a few minutes)...${NC}"
poetry run python -m ml.training.train_all
echo -e "${GREEN}✓ Models trained${NC}"

# Step 7: Run daily update
echo -e "\n${BLUE}Step 7: Running daily update (features + scoring)...${NC}"
poetry run python -m data_pipeline.jobs.daily_update
echo -e "${GREEN}✓ Daily update complete${NC}"

# Step 8: Run tests
echo -e "\n${BLUE}Step 8: Running tests...${NC}"
poetry run pytest tests/ -v
echo -e "${GREEN}✓ Tests passed${NC}"

# Step 9: Show next steps
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${BLUE}Next steps:${NC}"
echo ""
echo "1. Start the API server:"
echo "   poetry run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Visit the API docs:"
echo "   http://localhost:8000/docs"
echo ""
echo "3. Test an API endpoint:"
echo "   curl 'http://localhost:8000/v1/props/top?stat_type=points&min_edge=0.05&limit=10'"
echo ""
echo "4. (Optional) Start Discord bot:"
echo "   export DISCORD_BOT_TOKEN=your_token"
echo "   poetry run python -m discord_bot.bot"
echo ""
echo "5. Schedule daily jobs (cron example):"
echo "   # Daily update at 9 AM"
echo "   0 9 * * * cd /path/to/project && poetry run python -m data_pipeline.jobs.daily_update"
echo "   # Live reprice every 15 minutes during games"
echo "   */15 * * * * cd /path/to/project && poetry run python -m data_pipeline.jobs.live_reprice"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Overview"
echo "   - QUICKSTART.md - Detailed guide"
echo "   - IMPLEMENTATION_SUMMARY.md - Technical details"
echo ""
echo "🎉 Happy betting!"
