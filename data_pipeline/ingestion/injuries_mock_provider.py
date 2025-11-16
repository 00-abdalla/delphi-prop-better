"""Mock injury report provider."""
import random
from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from backend.app.logging_config import get_logger

logger = get_logger(__name__)


class BaseInjuryProvider(ABC):
    """Abstract base class for injury data providers."""
    
    @abstractmethod
    def get_injury_reports(self, report_date: date) -> list[dict[str, Any]]:
        """Get injury reports for a specific date."""
        pass


class InjuriesMockProvider(BaseInjuryProvider):
    """Mock provider that generates fake injury reports."""
    
    def __init__(self):
        """Initialize mock injury provider."""
        self.statuses = ["out", "doubtful", "questionable", "probable"]
        self.descriptions = [
            "knee soreness",
            "ankle sprain",
            "rest",
            "illness",
            "back tightness",
            "hamstring strain",
            "shoulder injury",
            "concussion protocol",
            "foot pain",
            "load management",
        ]
    
    def get_injury_reports(self, report_date: date) -> list[dict[str, Any]]:
        """
        Generate fake injury reports for a date.
        
        Args:
            report_date: Date of the injury report
            
        Returns:
            List of injury report dictionaries
        """
        # Generate 5-15 random injury reports per day
        num_reports = random.randint(5, 15)
        
        reports = []
        for i in range(num_reports):
            player_id = f"player_{random.randint(1, 150)}"
            status = random.choice(self.statuses)
            description = random.choice(self.descriptions)
            
            reports.append({
                "player_external_id": player_id,
                "report_date": report_date,
                "status": status,
                "description": description,
            })
        
        logger.info(f"Mock injury provider: generated {len(reports)} injury reports for {report_date}")
        return reports
