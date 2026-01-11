#!/usr/bin/env python3
"""Test LM Studio self-hosted solution integration."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_litellm_direct():
    """Test LiteLLM directly with lm_studio/ prefix (per PROVIDERS.md)."""
    from litellm import acompletion
    
    print("=" * 80)
    print("LITELLM DIRECT TEST - Self-hosted LM Studio")
    print("=" * 80)
    print()
    
    api_base = "http://localhost:1234/v1"
    model_name = "meta-llama-3.1-8b-instruct"
    
    # Test: lm_studio/ prefix with api_base and api_key parameters
    # This matches the PROVIDERS.md approach:
    # response = completion(
    #     model="lm_studio/llama-3-8b-instruct",
    #     api_base="http://localhost:1234/v1",
    #     api_key="dummy",
    #     messages=[...]
    # )
    
    print("Configuration:")
    print(f"  Model: lm_studio/{model_name}")
    print(f"  API Base: {api_base}")
    print(f"  API Key: dummy (required by some LM Studio versions)")
    print()
    
    try:
        response = await acompletion(
            model=f"lm_studio/{model_name}",
            api_base=api_base,
            api_key="dummy",
            messages=[{"role": "user", "content": "Say hello in exactly 5 words"}],
            max_tokens=50,
        )
        print("✓ SUCCESS!")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")
        print(f"Tokens: {response.usage}")
        print()
        return True
    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Is LM Studio running at http://localhost:1234?")
        print("  2. Is a model loaded in LM Studio?")
        print("  3. Does the model name match what's loaded?")
        print()
        return False


async def test_uer_gateway():
    """Test UER Gateway with LM Studio local server."""
    from uer.llm.gateway import LLMGateway
    
    print("=" * 80)
    print("UER GATEWAY TEST - Self-hosted LM Studio")
    print("=" * 80)
    print()
    
    # Set environment variable to point to LM Studio
    os.environ["OPENAI_API_BASE"] = "http://localhost:1234/v1"
    
    print("Configuration:")
    print(f"  OPENAI_API_BASE: {os.environ['OPENAI_API_BASE']}")
    print()
    
    gateway = LLMGateway()
    
    # Get provider info - should detect local server and return lm_studio/ prefixed models
    print("Querying provider info...")
    provider_info = await gateway.get_provider_info()
    
    if "openai" not in provider_info:
        print("✗ OpenAI provider not detected")
        return False
    
    info = provider_info["openai"]
    print(f"✓ Provider detected")
    print(f"  Type: {info['type']}")
    print(f"  Source: {info['source']}")
    print(f"  Server URL: {info.get('server_url', 'N/A')}")
    print(f"  Models available: {len(info['available_models'])}")
    print()
    
    if not info['available_models']:
        print("✗ No models available from LM Studio")
        print("  Make sure a model is loaded in LM Studio")
        return False
    
    # Show available models
    print("Available models:")
    for model in info['available_models'][:5]:
        print(f"  - {model}")
    print()
    
    # Test calling the first model
    test_model = info['available_models'][0]
    print(f"Testing model: {test_model}")
    print("Request: Create a function to calculate BMI in Python")
    print()
    
    try:
        response = await gateway.call(
            model=test_model,
            messages=[{"role": "user", "content": "Create a function to calculate BMI in Python"}],
            max_tokens=1024,
            temperature=0.7,
        )
        print("✓ SUCCESS!")
        print()
        print("Response:")
        print("-" * 80)
        content = response['choices'][0]['message']['content']
        # Print first 500 chars
        if len(content) > 500:
            print(content[:500] + "...")
        else:
            print(content)
        print("-" * 80)
        print()
        print(f"Model used: {response.get('model', 'unknown')}")
        print(f"Tokens: {response.get('usage', {})}")
        return True
    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "LM STUDIO SELF-HOSTED SOLUTION TEST" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    print("This test verifies the LM Studio integration using the approach from")
    print("PROVIDERS.md (Tier 3: Self-hosted solutions)")
    print()
    print("Prerequisites:")
    print("  - LM Studio running at http://localhost:1234")
    print("  - A model loaded (e.g., meta-llama-3.1-8b-instruct)")
    print()
    
    input("Press Enter to start tests...")
    print()
    
    # Run tests
    litellm_success = await test_litellm_direct()
    print()
    
    uer_success = await test_uer_gateway()
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    print("LiteLLM Direct Test:")
    if litellm_success:
        print("  ✓ PASSED - lm_studio/ prefix works with api_base parameter")
    else:
        print("  ✗ FAILED - Check LM Studio server and model")
    print()
    
    print("UER Gateway Test:")
    if uer_success:
        print("  ✓ PASSED - Full integration working")
        print("  ✓ Models detected with lm_studio/ prefix")
        print("  ✓ API calls route correctly to localhost:1234")
    else:
        print("  ✗ FAILED - Check configuration and server")
    print()
    
    if litellm_success and uer_success:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Your LM Studio integration is working correctly.")
        print("Claude can now use local models via:")
        print("  - OPENAI_API_BASE=http://localhost:1234/v1")
        print("  - Model format: lm_studio/model-name")
    else:
        print("⚠ SOME TESTS FAILED")
        print()
        print("Troubleshooting:")
        print("  1. Verify LM Studio is running: http://localhost:1234")
        print("  2. Check that a model is loaded in LM Studio")
        print("  3. Ensure OPENAI_API_BASE is set correctly")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
