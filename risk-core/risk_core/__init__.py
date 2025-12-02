"""
Risk Core Library
Pure Python risk calculation engine - no HTTP, no DB dependencies
"""

__version__ = "0.1.0"

# Main entry point
from .aggregation import aggregate_portfolio_risks

# Public API
__all__ = [
    "aggregate_portfolio_risks",
    "__version__",
]
