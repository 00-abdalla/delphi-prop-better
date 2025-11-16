"""Tests for EV calculations."""
import pytest

from backend.app.core.utils.ev_calculations import (
    american_to_decimal,
    american_to_prob,
    compute_ev_and_edge,
    decimal_to_american,
    prob_to_american,
)


def test_american_to_prob():
    """Test American odds to probability conversion."""
    assert american_to_prob(-110) == pytest.approx(0.5238, abs=0.001)
    assert american_to_prob(+150) == pytest.approx(0.4, abs=0.001)
    assert american_to_prob(-200) == pytest.approx(0.6667, abs=0.001)


def test_american_to_decimal():
    """Test American odds to decimal conversion."""
    assert american_to_decimal(-110) == pytest.approx(1.9091, abs=0.001)
    assert american_to_decimal(+150) == pytest.approx(2.5, abs=0.001)
    assert american_to_decimal(-200) == pytest.approx(1.5, abs=0.001)


def test_decimal_to_american():
    """Test decimal to American odds conversion."""
    assert decimal_to_american(1.91) == pytest.approx(-110, abs=1)
    assert decimal_to_american(2.5) == 150
    assert decimal_to_american(1.5) == -100


def test_prob_to_american():
    """Test probability to American odds conversion."""
    assert prob_to_american(0.5238) == pytest.approx(-110, abs=2)
    assert prob_to_american(0.4) == pytest.approx(150, abs=2)


def test_compute_ev_and_edge():
    """Test EV and edge calculation."""
    # 55% win probability at -110
    ev, edge = compute_ev_and_edge(0.55, -110)
    assert ev > 0  # Positive EV
    assert edge == pytest.approx(0.55 - 0.5238, abs=0.001)
    
    # 50% win probability at -110 (fair line)
    ev, edge = compute_ev_and_edge(0.5238, -110)
    assert ev == pytest.approx(0, abs=0.001)
    assert edge == pytest.approx(0, abs=0.001)
    
    # 45% win probability at -110 (negative EV)
    ev, edge = compute_ev_and_edge(0.45, -110)
    assert ev < 0
    assert edge < 0
