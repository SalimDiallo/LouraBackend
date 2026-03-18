"""
AI Tools Package
================
Auto-loads all tool modules to register them in the global registry.

To add new tools:
1. Create a new file (e.g., ai/tools/finance_tools.py)
2. Use the @register_tool decorator on your functions
3. Import the module here

That's it! The tools are automatically available to the AI agent.
"""

# Import all tool modules to trigger @register_tool decorators
from ai.tools import hr_tools
from ai.tools import inventory_tools

# Re-export the registry for convenience
from ai.tools.registry import registry, register_tool

__all__ = ['registry', 'register_tool']
