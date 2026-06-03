"""Sales-effectiveness layer for the telesales agent.

Modules:
    deal_score: 0-100 deal score per offer.
    value_score: value-for-money heuristic per category.
    urgency: closer cues from stock and price history.
    trust: warranty / authentic / return formatting.
    objections: Vietnamese objection handling.
    composer: orchestrates the sales layer into the agent answer.
"""

from app.agent.sales.composer import compose_telesales_answer

__all__ = ["compose_telesales_answer"]
