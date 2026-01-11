#!/usr/bin/env python3
"""Test security warnings for API key exposure in config."""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.config_guide import ConfigGuide
from uer.llm.config_registry import ConfigRegistry


async def main() -> None:
    """Test security warning system."""
    print("=" * 80)
    print("SECURITY WARNING SYSTEM TEST")
    print("=" * 80)
    print()

    # Test 1: Detect MCP client
    print("TEST 1: Detect MCP client location")
    print("-" * 80)
    client_info = ConfigGuide.detect_mcp_client()
    print(f"System: {client_info['system']}")
    print(f"Detected clients: {len(client_info['detected_clients'])}")
    for client in client_info["detected_clients"]:
        print(f"  ✓ {client['name']} ({client['platform']})")
        print(f"    Config: {client['config_file']}")
    print()

    # Test 2: Try to set API key in config (should trigger warning)
    print("TEST 2: Set API key in config (should trigger security warning)")
    print("-" * 80)
    config_file = Path.home() / ".uer" / "test_security_config.json"
    registry = ConfigRegistry(config_file)

    openai_config = {
        "credentials": {
            "OPENAI_API_KEY": "sk-test-key-123",  # This should trigger warning
        }
    }

    result = registry.set_provider("openai", openai_config)

    if "_security_risk" in result:
        print("✓ Security warning triggered!")
        print(f"  Level: {result['_security_risk']['level']}")
        print(f"  Issue: {result['_security_risk']['issue']}")
        print(f"  Risk: {result['_security_risk']['risk'][:100]}...")
        print(f"  Recommendation: {result['_security_risk']['recommendation']}")
    else:
        print("✗ No security warning (unexpected)")
    print()

    # Test 3: Get configuration guide
    print("TEST 3: Get secure configuration guide for OpenAI")
    print("-" * 80)
    guide = ConfigGuide.get_full_guide("openai")

    print(f"Provider: {guide['provider']}")
    print(f"Required env vars: {guide['configuration_guide']['required_env_vars']}")
    print(f"Security note: {guide['configuration_guide']['security_note'][:100]}...")

    if guide["configuration_guide"]["detected_client"]:
        print(f"\nDetected client: {guide['configuration_guide']['detected_client']}")
        print(f"Config file: {guide['configuration_guide']['config_file']}")
        print("\nInstructions:")
        print(guide["configuration_guide"]["instructions"][:300] + "...")
    else:
        print("\nNo MCP client detected")
    print()

    # Test 4: Why this matters
    print("TEST 4: Configuration rationale")
    print("-" * 80)
    why = guide["why_this_matters"]
    print(f"Security:\n  {why['security']}\n")
    print(f"Convenience:\n  {why['convenience']}\n")
    print(f"User control:\n  {why['user_control']}")
    print()

    # Test 5: Set non-sensitive config (no warning)
    print("TEST 5: Set non-sensitive config (should NOT trigger warning)")
    print("-" * 80)
    azure_instance = {
        "instances": [
            {
                "name": "my-deployment",
                "endpoint": "https://my-resource.openai.azure.com",
            }
        ]
    }

    result = registry.set_provider("azure", azure_instance)

    if "_security_risk" in result:
        print("✗ Security warning triggered (unexpected)")
    else:
        print("✓ No security warning (correct - no API keys)")
    print()

    # Test 6: Multiple providers guide
    print("TEST 6: Configuration guides for multiple providers")
    print("-" * 80)
    providers = ["openai", "anthropic", "gemini", "azure", "bedrock"]

    for provider in providers:
        guide = ConfigGuide.get_full_guide(provider)
        config = guide["configuration_guide"]
        print(f"\n{provider}:")
        print(f"  Required: {', '.join(config['required_env_vars'])}")
        if config["optional_env_vars"]:
            print(f"  Optional: {', '.join(config['optional_env_vars'])}")
    print()

    print("=" * 80)
    print("SECURITY FEATURES")
    print("=" * 80)
    print("\n✓ Detects API keys in config and warns LLMs")
    print("✓ Detects MCP client location automatically")
    print("✓ Provides client-specific configuration instructions")
    print("✓ Explains security risks of sharing keys in chat")
    print("✓ Guides users to secure environment variable setup")
    print("✓ Prevents credential exposure in training data")

    print("\nLLM Workflow:")
    print("1. User: 'Set up OpenAI for me'")
    print("2. LLM: Calls llm_config_guide instead of asking for key")
    print("3. LLM: Shows user where to add key in MCP client config")
    print("4. User: Adds key to config file (not in chat)")
    print("5. Result: Key never exposed in conversation")

    # Cleanup
    if config_file.exists():
        config_file.unlink()
        print(f"\n✓ Cleaned up test file: {config_file}")


if __name__ == "__main__":
    asyncio.run(main())
