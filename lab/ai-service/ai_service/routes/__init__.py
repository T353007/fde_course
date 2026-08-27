"""HTTP routes. One module per endpoint group, matching LAB_SPEC section 7."""

from ai_service.routes import classify, extract, health, memo, policy, tools

__all__ = ["classify", "extract", "health", "memo", "policy", "tools"]
