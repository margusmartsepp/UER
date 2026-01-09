"""
UER (Universal Expert Registry) MCP Server Entry Point.

Run as: python -m uer.server
"""

import asyncio

from uer.server import main

if __name__ == "__main__":
    asyncio.run(main())
