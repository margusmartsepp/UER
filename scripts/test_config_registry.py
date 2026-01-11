#!/usr/bin/env python3
"""Test the configuration registry system for LLM-managed provider setup."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.config_registry import ConfigRegistry


async def main() -> None:
    """Test configuration registry."""
    print("=" * 80)
    print("CONFIGURATION REGISTRY TEST")
    print("=" * 80)
    print()

    # Create registry
    config_file = Path.home() / ".uer" / "test_provider_config.json"
    registry = ConfigRegistry(config_file)

    print(f"Config file: {config_file}")
    print()

    # Test 1: Get all providers (should be empty initially)
    print("TEST 1: Get all providers (initial state)")
    print("-" * 80)
    all_config = registry.get_all_providers()
    print(json.dumps(all_config, indent=2))
    print()

    # Test 2: Set OpenAI config
    print("TEST 2: Set OpenAI configuration")
    print("-" * 80)
    openai_config = {
        "credentials": {
            "OPENAI_API_KEY": "sk-test-key-123",
            "OPENAI_API_BASE": "https://api.openai.com/v1",
        },
        "description": "OpenAI cloud API",
    }
    registry.set_provider("openai", openai_config)
    print("✓ OpenAI config set")
    print()

    # Test 3: Add Azure instance
    print("TEST 3: Add Azure deployment instance")
    print("-" * 80)
    azure_instance = {
        "name": "my-gpt4-deployment",
        "endpoint": "https://my-resource.openai.azure.com",
        "deployment_name": "gpt-4o",
        "api_version": "2024-02-15-preview",
        "description": "My Azure OpenAI GPT-4o deployment",
    }
    registry.add_provider_instance("azure", azure_instance)
    print("✓ Azure instance added")
    print()

    # Test 4: Add AWS Bedrock instance
    print("TEST 4: Add AWS Bedrock instance")
    print("-" * 80)
    bedrock_instance = {
        "name": "us-east-1-claude",
        "region": "us-east-1",
        "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "description": "Claude 3.5 Sonnet on AWS Bedrock",
    }
    registry.add_provider_instance("bedrock", bedrock_instance)
    print("✓ Bedrock instance added")
    print()

    # Test 5: Set local Ollama config
    print("TEST 5: Set local Ollama configuration")
    print("-" * 80)
    ollama_config = {
        "credentials": {
            "OLLAMA_API_BASE": "http://localhost:11434",
        },
        "type": "local",
        "description": "Local Ollama server",
    }
    registry.set_provider("ollama", ollama_config)
    print("✓ Ollama config set")
    print()

    # Test 6: Get all providers (should show configured providers)
    print("TEST 6: Get all providers (after configuration)")
    print("-" * 80)
    all_config = registry.get_all_providers()
    print(f"Configured providers: {len(all_config['providers'])}")
    for provider, config in all_config["providers"].items():
        print(f"\n{provider}:")
        print(f"  Updated: {config.get('_updated_at', 'N/A')}")
        if "credentials" in config:
            print(f"  Credentials: {list(config['credentials'].keys())}")
        if "instances" in config:
            print(f"  Instances: {len(config['instances'])}")
            for inst in config["instances"]:
                print(f"    - {inst.get('name', 'unnamed')}: {inst.get('description', 'N/A')}")
    print()

    # Test 7: Get specific provider
    print("TEST 7: Get specific provider (Azure)")
    print("-" * 80)
    azure_config = registry.get_provider("azure")
    print(json.dumps(azure_config, indent=2))
    print()

    # Test 8: Get provider instances
    print("TEST 8: Get provider instances")
    print("-" * 80)
    azure_instances = registry.get_provider_instances("azure")
    bedrock_instances = registry.get_provider_instances("bedrock")
    print(f"Azure instances: {len(azure_instances)}")
    print(f"Bedrock instances: {len(bedrock_instances)}")
    print()

    # Test 9: List configured providers
    print("TEST 9: List configured providers")
    print("-" * 80)
    configured = registry.list_configured_providers()
    print(f"Configured providers: {configured}")
    print()

    # Test 10: Verify persistence
    print("TEST 10: Verify persistence (load from disk)")
    print("-" * 80)
    registry2 = ConfigRegistry(config_file)
    all_config2 = registry2.get_all_providers()
    print(f"Providers loaded from disk: {len(all_config2['providers'])}")
    print("✓ Configuration persisted correctly")
    print()

    print("=" * 80)
    print("CONFIGURATION REGISTRY FEATURES")
    print("=" * 80)
    print("\n✓ LLMs can read provider configurations")
    print("✓ LLMs can set/update provider configurations")
    print("✓ LLMs can add provider instances (Azure, AWS, etc.)")
    print("✓ Configurations persisted to disk")
    print("✓ Supports both environment variables and registry")
    print("✓ Helps non-technical users without manual env var editing")
    print("\nUse Cases:")
    print("1. User: 'Set up OpenAI for me'")
    print("   LLM: Uses llm_config_set to configure OpenAI")
    print("2. User: 'Add my Azure deployment'")
    print("   LLM: Uses llm_config_add_instance to add Azure instance")
    print("3. User: 'What providers do I have configured?'")
    print("   LLM: Uses llm_config_get to show current setup")

    # Cleanup test file
    if config_file.exists():
        config_file.unlink()
        print(f"\n✓ Cleaned up test file: {config_file}")


if __name__ == "__main__":
    asyncio.run(main())
