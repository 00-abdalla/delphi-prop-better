"""Expected value and odds conversion utilities."""


def american_to_prob(odds: int) -> float:
    """
    Convert American odds to implied probability.
    
    Args:
        odds: American odds (e.g., -110, +150)
        
    Returns:
        Implied probability (0-1)
    """
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)


def american_to_decimal(odds: int) -> float:
    """
    Convert American odds to decimal odds.
    
    Args:
        odds: American odds (e.g., -110, +150)
        
    Returns:
        Decimal odds (e.g., 1.91, 2.50)
    """
    if odds < 0:
        return 1 + (100 / abs(odds))
    else:
        return 1 + (odds / 100)


def decimal_to_american(decimal_odds: float) -> int:
    """
    Convert decimal odds to American odds.
    
    Args:
        decimal_odds: Decimal odds (e.g., 1.91, 2.50)
        
    Returns:
        American odds
    """
    if decimal_odds >= 2.0:
        return int((decimal_odds - 1) * 100)
    else:
        return int(-100 / (decimal_odds - 1))


def prob_to_american(prob: float) -> int:
    """
    Convert probability to fair American odds.
    
    Args:
        prob: Probability (0-1)
        
    Returns:
        American odds
    """
    if prob >= 0.5:
        return int(-100 * prob / (1 - prob))
    else:
        return int(100 * (1 - prob) / prob)


def compute_ev_and_edge(p_model: float, odds_american: int) -> tuple[float, float]:
    """
    Compute expected value and edge for a bet.
    
    Args:
        p_model: Model's probability of winning (0-1)
        odds_american: American odds for the bet
        
    Returns:
        Tuple of (ev, edge) where:
        - ev: Expected value of $1 stake (in dollars)
        - edge: Difference between model prob and implied prob (p_model - p_book)
    """
    # Convert odds to decimal for EV calculation
    decimal_odds = american_to_decimal(odds_american)
    
    # EV calculation: p_win * profit - (1 - p_win) * stake
    # Where profit = stake * (decimal_odds - 1)
    # For $1 stake: EV = p_model * (decimal_odds - 1) - (1 - p_model)
    ev = p_model * (decimal_odds - 1) - (1 - p_model)
    
    # Edge is the difference between model probability and book's implied probability
    p_book = american_to_prob(odds_american)
    edge = p_model - p_book
    
    return ev, edge


def kelly_criterion(edge: float, odds_american: int, kelly_fraction: float = 0.25) -> float:
    """
    Calculate Kelly Criterion bet size.
    
    Args:
        edge: Edge (p_model - p_book)
        odds_american: American odds
        kelly_fraction: Fraction of full Kelly to use (default 0.25 = quarter Kelly)
        
    Returns:
        Recommended bet size as fraction of bankroll (0-1)
    """
    decimal_odds = american_to_decimal(odds_american)
    p_book = american_to_prob(odds_american)
    p_model = p_book + edge
    
    # Full Kelly: f = (p * (b + 1) - 1) / b, where b = decimal_odds - 1
    b = decimal_odds - 1
    full_kelly = (p_model * (b + 1) - 1) / b
    
    # Apply fractional Kelly and ensure non-negative
    return max(0.0, full_kelly * kelly_fraction)


def compute_clv(opening_odds: int, closing_odds: int) -> float:
    """
    Compute Closing Line Value (CLV).
    
    CLV measures how much value was captured by betting at opening vs closing line.
    
    Args:
        opening_odds: American odds when bet was placed
        closing_odds: American odds at close
        
    Returns:
        CLV in decimal odds units (positive = good, negative = bad)
    """
    opening_decimal = american_to_decimal(opening_odds)
    closing_decimal = american_to_decimal(closing_odds)
    
    return opening_decimal - closing_decimal
