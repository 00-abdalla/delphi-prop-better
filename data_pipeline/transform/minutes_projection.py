"""Minutes projection utilities."""
import pandas as pd


class MinutesProjector:
    """Simple minutes projector based on recent averages."""
    
    def project(self, player_history_df: pd.DataFrame, n_games: int = 5) -> float:
        """
        Project minutes for a player based on recent game history.
        
        Args:
            player_history_df: DataFrame with 'minutes' column
            n_games: Number of recent games to average
            
        Returns:
            Projected minutes (clipped to [10, 42])
        """
        if player_history_df.empty:
            return 25.0  # Default
        
        # Get last n games
        recent = player_history_df.head(n_games)
        
        if recent.empty:
            return 25.0
        
        # Simple average
        avg_minutes = recent["minutes"].mean()
        
        # Clip to reasonable bounds
        return max(10.0, min(42.0, avg_minutes))
