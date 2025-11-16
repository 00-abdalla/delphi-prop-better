"""Tests for distribution utilities."""
import pytest

from backend.app.core.utils.distributions import NormalStatDistribution


def test_normal_distribution_prob_over():
    """Test probability over calculation."""
    dist = NormalStatDistribution(mean=25.0, variance=16.0)  # std = 4
    
    # Should be ~50% at the mean
    prob = dist.prob_over(25.0)
    assert 0.45 < prob < 0.55
    
    # Should be less likely far above mean
    prob_high = dist.prob_over(35.0)
    assert prob_high < 0.1


def test_normal_distribution_prob_under():
    """Test probability under calculation."""
    dist = NormalStatDistribution(mean=25.0, variance=16.0)
    
    # Should be ~50% at the mean
    prob = dist.prob_under(25.0)
    assert 0.45 < prob < 0.55
    
    # Should be less likely far below mean
    prob_low = dist.prob_under(15.0)
    assert prob_low < 0.1


def test_prob_over_and_under_sum():
    """Test that prob_over + prob_under is close to 1."""
    dist = NormalStatDistribution(mean=25.0, variance=16.0)
    
    # Note: They won't sum exactly to 1 due to continuity correction
    prob_over = dist.prob_over(25.0)
    prob_under = dist.prob_under(25.0)
    
    # Should be close to 1
    assert 0.95 < (prob_over + prob_under) < 1.05


def test_percentile():
    """Test percentile calculation."""
    dist = NormalStatDistribution(mean=25.0, variance=16.0)
    
    # 50th percentile should be at the mean
    p50 = dist.percentile(0.5)
    assert 24.5 < p50 < 25.5
    
    # Higher percentiles should be higher values
    p90 = dist.percentile(0.9)
    assert p90 > 25.0
