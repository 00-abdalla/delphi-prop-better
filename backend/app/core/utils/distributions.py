"""Statistical distribution utilities."""
from dataclasses import dataclass
from math import sqrt

from scipy.stats import norm


@dataclass
class NormalStatDistribution:
    """
    Normal distribution representation for a player stat.
    
    Uses continuity correction (+0.5) for discrete stats.
    """
    
    mean: float
    variance: float
    
    def prob_over(self, line: float) -> float:
        """
        Calculate probability of going over the line.
        
        Args:
            line: The prop line value
            
        Returns:
            Probability (0-1) of exceeding the line
        """
        std = sqrt(self.variance) if self.variance > 0 else 1e-6
        # Apply continuity correction: P(X > line) = P(X >= line + 0.5)
        return 1.0 - norm.cdf(line + 0.5, loc=self.mean, scale=std)
    
    def prob_under(self, line: float) -> float:
        """
        Calculate probability of going under the line.
        
        Args:
            line: The prop line value
            
        Returns:
            Probability (0-1) of being below the line
        """
        std = sqrt(self.variance) if self.variance > 0 else 1e-6
        # Apply continuity correction: P(X < line) = P(X <= line - 0.5)
        return norm.cdf(line - 0.5, loc=self.mean, scale=std)
    
    def prob_exact(self, value: float) -> float:
        """
        Calculate probability of exact value (for discrete stats).
        
        Args:
            value: The exact stat value
            
        Returns:
            Probability of hitting exactly this value
        """
        std = sqrt(self.variance) if self.variance > 0 else 1e-6
        return norm.cdf(value + 0.5, loc=self.mean, scale=std) - norm.cdf(
            value - 0.5, loc=self.mean, scale=std
        )
    
    def percentile(self, p: float) -> float:
        """
        Get the value at the given percentile.
        
        Args:
            p: Percentile (0-1)
            
        Returns:
            The stat value at that percentile
        """
        std = sqrt(self.variance) if self.variance > 0 else 1e-6
        return norm.ppf(p, loc=self.mean, scale=std)
