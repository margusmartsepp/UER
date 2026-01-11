#!/usr/bin/env python3
"""Test LM Studio / local OpenAI-compatible server calls."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_litellm_direct():
    """Test LiteLLM directly with lm_studio/ prefix."""
    from litellm import acompletion
    
    print("=" * 80)
    print("LITELLM DIRECT TEST")
    print("=" * 80)
    print()
    
    api_base = "http://localhost:1234/v1"
    model_name = "meta-llama-3.1-8b-instruct"
    
    # Set environment variables as per LiteLLM docs
    os.environ["LM_STUDIO_API_BASE"] = api_base
    os.environ["LM_STUDIO_API_KEY"] = ""  # Optional, default is empty
    
    # Test: lm_studio/ prefix (correct method per LiteLLM docs)
    print("TEST: lm_studio/ prefix with LM_STUDIO_API_BASE env var")
    print(f"Model: lm_studio/{model_name}")
    print(f"LM_STUDIO_API_BASE: {api_base}")
    print()
    
    try:
        response = await acompletion(
            model=f"lm_studio/{model_name}",
            messages=[{"role": "user", "content": "Say hello in 5 words"}],
            max_tokens=50,
        )
        print("✓ SUCCESS!")
        print(f"Response: {response.choices[0].message.content}")
        print()
        return True
    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        print()
        return False


async def test_uer_gateway():
    """Test UER Gateway with local server."""
    from uer.llm.gateway import LLMGateway
    
    print("=" * 80)
    print("UER GATEWAY TEST")
    print("=" * 80)
    print()
    
    # Set environment variable
    os.environ["OPENAI_API_BASE"] = "http://localhost:1234/v1"
    
    gateway = LLMGateway()
    
    # Get provider info
    provider_info = await gateway.get_provider_info()
    
    if "openai" in provider_info:
        info = provider_info["openai"]
        print(f"Provider type: {info['type']}")
        print(f"Models available: {len(info['available_models'])}")
        
        if info['available_models']:
            test_model = info['available_models'][0]
            print(f"Testing with model: {test_model}")
            print()
            
            try:
                response = await gateway.call(
                    model=test_model,
                    messages=[{"role": "user", "content": "Create a function to calculate BMI in Python"}],
                    max_tokens=1024,
                    temperature=0.7,
                )
                print("✓ SUCCESS!")
                print(f"Response preview: {response['choices'][0]['message']['content'][:200]}...")
            except Exception as e:
                print(f"✗ FAILED: {str(e)}")
        else:
            print("⚠ No models available")
    else:
        print("⚠ OpenAI provider not detected")


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "LM STUDIO / LOCAL SERVER TEST" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    print("This test will try different LiteLLM configurations to find")
    print("the correct way to call local OpenAI-compatible servers.")
    print()
    print("Prerequisites:")
    print("  - LM Studio (or similar) running at http://localhost:1234")
    print("  - Model loaded: meta-llama-3.1-8b-instruct (or similar)")
    print()
    
    input("Press Enter to start tests...")
    print()
    
    await test_litellm_direct()
    await test_uer_gateway()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
