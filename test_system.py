"""Quick system test to verify everything works."""
from backend.app.db import SessionLocal
from backend.app.db.models import Game, PlayerGameFeatures, PropPrediction, Team, Player

db = SessionLocal()

print("=== SYSTEM HEALTH CHECK ===\n")

# Check teams
team_count = db.query(Team).count()
print(f"✓ Teams: {team_count}")

# Check players
player_count = db.query(Player).count()
print(f"✓ Players: {player_count}")

# Check games
game_count = db.query(Game).count()
print(f"✓ Games: {game_count}")

# Check features
feature_count = db.query(PlayerGameFeatures).count()
print(f"✓ Feature records: {feature_count}")

# Check predictions
prediction_count = db.query(PropPrediction).count()
print(f"✓ Predictions: {prediction_count}")

# Show sample game dates
print("\n=== RECENT GAMES ===")
games = db.query(Game.game_date, Game.status).distinct().order_by(Game.game_date.desc()).limit(5).all()
for game_date, status in games:
    print(f"  {game_date} - {status}")

# Show models
import os
print("\n=== TRAINED MODELS ===")
model_dir = "models"
if os.path.exists(model_dir):
    models = [f for f in os.listdir(model_dir) if f.endswith('.txt')]
    for model in models:
        size = os.path.getsize(os.path.join(model_dir, model))
        print(f"  ✓ {model} ({size:,} bytes)")
else:
    print("  ✗ Models directory not found")

print("\n=== STATUS ===")
if team_count > 0 and player_count > 0 and game_count > 0:
    print("✅ Data pipeline: READY")
else:
    print("⚠️  Data pipeline: INCOMPLETE")

if feature_count > 0:
    print("✅ Feature engineering: WORKING")
else:
    print("⚠️  Feature engineering: NO DATA")

if len(models) == 3:
    print("✅ ML models: TRAINED")
else:
    print(f"⚠️  ML models: {len(models)}/3 trained")

if prediction_count > 0:
    print("✅ Predictions: GENERATED")
else:
    print("⚠️  Predictions: NONE YET (run daily_update on a game date)")

db.close()
