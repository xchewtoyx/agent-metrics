"""Base exception type for the agent-metrics library.

Kept in its own module so any submodule can raise the shared error without
depending on an unrelated domain module.
"""

from __future__ import annotations


class AgentMetricsError(ValueError):
    """Base exception for agent-metrics library errors."""

    pass
