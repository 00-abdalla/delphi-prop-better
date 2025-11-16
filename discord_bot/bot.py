"""Discord bot for Delphi."""
import os
from datetime import date

import discord
import httpx
from discord import app_commands

from backend.app.logging_config import get_logger

logger = get_logger(__name__)

# Configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable not set")


class DelphiBot(discord.Client):
    """Discord bot client for Delphi."""
    
    def __init__(self):
        """Initialize bot with intents."""
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def setup_hook(self):
        """Setup hook called on bot startup."""
        await self.tree.sync()
        logger.info("Command tree synced")
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Bot logged in as {self.user}")
        logger.info(f"Connected to {len(self.guilds)} guilds")
    
    async def close(self):
        """Cleanup on bot shutdown."""
        await self.http_client.aclose()
        await super().close()


# Initialize bot
bot = DelphiBot()


@bot.tree.command(name="top", description="Show top model edges")
@app_commands.describe(
    stat_type="Stat type (points, assists, rebounds)",
    min_edge="Minimum edge threshold (default: 0.05)",
)
async def top_command(
    interaction: discord.Interaction,
    stat_type: str = "points",
    min_edge: float = 0.05,
):
    """Show top prop edges."""
    await interaction.response.defer()
    
    try:
        url = f"{API_BASE_URL}/v1/props/top"
        params = {
            "stat_type": stat_type,
            "min_edge": min_edge,
            "limit": 10,
        }
        
        response = await bot.http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        props = data.get("props", [])
        
        if not props:
            await interaction.followup.send(f"No props found for {stat_type} with edge >= {min_edge}")
            return
        
        # Format response
        lines = [f"**Top {stat_type.upper()} Edges** (min edge: {min_edge:.1%})\n"]
        
        for i, prop in enumerate(props[:10], 1):
            line_str = (
                f"{i}. **{prop['player_name']}** ({prop['team_abbrev']}) "
                f"vs {prop['opponent']}\n"
                f"   Line: {prop['line']} | Side: {prop['side'].upper()} @ {prop['odds']}\n"
                f"   Edge: **{prop['edge']:.1%}** | EV: {prop['ev']:.3f} | "
                f"Model: {prop['predicted_mean']:.1f}\n"
            )
            lines.append(line_str)
        
        message = "\n".join(lines)
        await interaction.followup.send(message[:2000])  # Discord limit
    
    except Exception as e:
        logger.error(f"Error in /top command: {e}")
        await interaction.followup.send(f"Error: {str(e)}")


@bot.tree.command(name="player", description="Show props for a player")
@app_commands.describe(name="Player name to search")
async def player_command(interaction: discord.Interaction, name: str):
    """Show props for a player."""
    await interaction.response.defer()
    
    try:
        # Search for player
        search_url = f"{API_BASE_URL}/v1/players/search"
        search_response = await bot.http_client.get(search_url, params={"q": name, "limit": 5})
        search_response.raise_for_status()
        search_data = search_response.json()
        
        players = search_data.get("players", [])
        
        if not players:
            await interaction.followup.send(f"No players found matching '{name}'")
            return
        
        # Use first match
        player = players[0]
        player_id = player["id"]
        
        # Get props
        props_url = f"{API_BASE_URL}/v1/players/{player_id}/props"
        props_response = await bot.http_client.get(props_url)
        props_response.raise_for_status()
        props_data = props_response.json()
        
        props = props_data.get("props", [])
        
        if not props:
            await interaction.followup.send(f"No props found for {player['name']}")
            return
        
        # Format response
        lines = [f"**{player['name']}** ({player['team_abbrev']})\n"]
        
        for prop in props[:10]:
            edge_over = prop.get("edge_over", 0)
            edge_under = prop.get("edge_under", 0)
            best_side = "OVER" if edge_over >= edge_under else "UNDER"
            best_edge = max(edge_over, edge_under)
            
            line_str = (
                f"**{prop['stat_display']}**: {prop['line']}\n"
                f"  Best: {best_side} @ {prop.get('over_odds' if best_side == 'OVER' else 'under_odds')} "
                f"(Edge: {best_edge:.1%})\n"
                f"  Model: {prop.get('predicted_mean', 'N/A')}\n"
            )
            lines.append(line_str)
        
        message = "\n".join(lines)
        await interaction.followup.send(message[:2000])
    
    except Exception as e:
        logger.error(f"Error in /player command: {e}")
        await interaction.followup.send(f"Error: {str(e)}")


@bot.tree.command(name="game", description="Show props for a game")
@app_commands.describe(game_id="Game ID")
async def game_command(interaction: discord.Interaction, game_id: int):
    """Show props for a game."""
    await interaction.response.defer()
    
    try:
        url = f"{API_BASE_URL}/v1/games/{game_id}/props"
        response = await bot.http_client.get(url)
        response.raise_for_status()
        data = response.json()
        
        game = data.get("game", {})
        props = data.get("props", [])
        
        if not props:
            await interaction.followup.send(f"No props found for game {game_id}")
            return
        
        # Format response
        lines = [
            f"**Game {game_id}**: {game['away_team_abbrev']} @ {game['home_team_abbrev']}\n"
            f"Date: {game['game_date']}\n"
        ]
        
        # Show top 10 by edge
        for i, prop in enumerate(props[:10], 1):
            best_edge = prop.get("best_edge", 0)
            best_side = prop.get("best_side", "").upper()
            
            line_str = (
                f"{i}. **{prop['player_name']}** - {prop['stat_display']}: {prop['line']}\n"
                f"   {best_side} (Edge: {best_edge:.1%})\n"
            )
            lines.append(line_str)
        
        message = "\n".join(lines)
        await interaction.followup.send(message[:2000])
    
    except Exception as e:
        logger.error(f"Error in /game command: {e}")
        await interaction.followup.send(f"Error: {str(e)}")


@bot.tree.command(name="modelsheet", description="Show model sheet for a date")
@app_commands.describe(target_date="Date (YYYY-MM-DD), defaults to today")
async def modelsheet_command(interaction: discord.Interaction, target_date: str = None):
    """Show model sheet."""
    await interaction.response.defer()
    
    if target_date is None:
        target_date = date.today().isoformat()
    
    try:
        url = f"{API_BASE_URL}/v1/modelsheets/{target_date}"
        response = await bot.http_client.get(url)
        response.raise_for_status()
        data = response.json()
        
        lines = [f"**Model Sheet for {target_date}**\n"]
        
        for stat_type, stat_data in data.get("stat_types", {}).items():
            props = stat_data.get("props", [])
            if props:
                lines.append(f"\n**{stat_type.upper()}** ({len(props)} props)")
                for i, prop in enumerate(props[:5], 1):
                    lines.append(
                        f"{i}. {prop['player_name']}: {prop['line']} {prop['side'].upper()} "
                        f"(Edge: {prop['edge']:.1%})"
                    )
        
        message = "\n".join(lines)
        await interaction.followup.send(message[:2000])
    
    except Exception as e:
        logger.error(f"Error in /modelsheet command: {e}")
        await interaction.followup.send(f"Error: {str(e)}")


def main():
    """Run the Discord bot."""
    logger.info("Starting Delphi Discord bot")
    logger.info(f"API base URL: {API_BASE_URL}")
    
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise


if __name__ == "__main__":
    main()
