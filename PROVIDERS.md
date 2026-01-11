# LiteLLM providers: a unified gateway to 100+ LLM integrations

LiteLLM supports **over 100 model providers** through a consistent OpenAI-compatible interface, enabling developers to build systems that seamlessly switch between cloud APIs, enterprise deployments, and self-hosted models. The integration landscape divides into four distinct categories—each with characteristic authentication patterns and configuration approaches—but all converge on the same `completion()` API with provider prefixes for routing.

The key insight for multi-provider systems: **authentication complexity scales with enterprise requirements**. Simple API-key providers (Anthropic, Groq) need one environment variable. Enterprise clouds (Azure, Bedrock, Vertex) support 5-7 authentication methods including managed identities, STS role assumption, and OIDC federation. Self-hosted solutions (Ollama, vLLM) often need no authentication at all—just an endpoint URL.

## Three authentication tiers define the provider landscape

**Tier 1: API-key providers** use the simplest pattern. Anthropic, Mistral, Cohere, Groq, DeepSeek, Together AI, and dozens of others follow an identical approach:

```python
import os
os.environ["ANTHROPIC_API_KEY"] = "sk-..."  # Convention: PROVIDER_API_KEY
os.environ["MISTRAL_API_KEY"] = "..."
os.environ["GROQ_API_KEY"] = "..."

from litellm import completion
response = completion(model="anthropic/claude-sonnet-4-5-20250929", messages=[...])
response = completion(model="mistral/mistral-large-2407", messages=[...])
```

All API-key providers follow the `provider_prefix/model_name` convention. The complete list includes over **60 cloud API providers**: OpenAI (`openai/`), Anthropic (`anthropic/`), Mistral (`mistral/`), Cohere (`cohere_chat/`), Groq (`groq/`), DeepSeek (`deepseek/`), Together AI (`together_ai/`), Fireworks AI (`fireworks_ai/`), Perplexity (`perplexity/`), xAI (`xai/`), Replicate (`replicate/`), and many others.

**Tier 2: Enterprise cloud providers** support multiple authentication mechanisms for production deployments:

| Provider | Primary Auth | Managed Identity | Role Assumption | OIDC |
|----------|-------------|------------------|-----------------|------|
| Azure OpenAI | API Key / Azure AD | DefaultAzureCredential | Entra ID | ✓ |
| AWS Bedrock | Access Keys | EC2/Lambda IAM | STS AssumeRole | Web Identity |
| Google Vertex | Service Account | Workload Identity | Impersonation | ✓ |

Azure OpenAI uniquely requires an `api_version` parameter and uses deployment names rather than model names:

```python
response = completion(
    model="azure/my-gpt4-deployment",  # deployment name, not model
    api_base="https://my-resource.openai.azure.com/",
    api_version="2023-05-15",
    api_key="...",  # or azure_ad_token for AD auth
    messages=[...]
)
```

AWS Bedrock offers the most flexible authentication with **7+ methods**, including STS role assumption for cross-account access:

```python
response = completion(
    model="bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
    aws_role_name="arn:aws:iam::123456789:role/BedrockRole",  # STS AssumeRole
    aws_session_name="litellm-session",
    aws_region_name="us-east-1",
    messages=[...]
)
```

**Tier 3: Self-hosted solutions** require endpoint configuration rather than API keys:

```python
# Ollama - no auth needed
response = completion(
    model="ollama/llama3",
    api_base="http://localhost:11434",
    messages=[...]
)

# vLLM - hosted_vllm prefix (vllm/ is deprecated)
response = completion(
    model="hosted_vllm/meta-llama/Llama-2-7b",
    api_base="http://vllm-server:8000",
    messages=[...]
)

# LM Studio - optional dummy API key required by some versions
response = completion(
    model="lm_studio/llama-3-8b-instruct",
    api_base="http://localhost:1234/v1",
    api_key="dummy",
    messages=[...]
)
```

## Config.yaml centralizes multi-provider deployments

The LiteLLM Proxy uses YAML configuration to define model deployments, credentials, and routing behavior. Environment variables reference with `os.environ/VAR_NAME` syntax:

```yaml
model_list:
  # Multiple deployments with same model_name = load balanced
  - model_name: gpt-4
    litellm_params:
      model: azure/gpt-4-east
      api_base: https://east.openai.azure.com/
      api_key: os.environ/AZURE_EAST_KEY
      api_version: "2023-07-01-preview"
      rpm: 1000  # requests per minute for routing
      
  - model_name: gpt-4
    litellm_params:
      model: azure/gpt-4-west
      api_key: os.environ/AZURE_WEST_KEY
      api_base: https://west.openai.azure.com/
      rpm: 800

  # Anthropic as fallback
  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20240620
      api_key: os.environ/ANTHROPIC_API_KEY

  # Local Ollama for development
  - model_name: local-llama
    litellm_params:
      model: ollama/llama3
      api_base: http://localhost:11434

litellm_settings:
  fallbacks:
    - {"gpt-4": ["claude-sonnet"]}  # Failover chain
  context_window_fallbacks:
    - {"gpt-4": ["claude-sonnet"]}  # For context overflow
```

## Provider-specific parameters pass through transparently

LiteLLM forwards non-OpenAI parameters directly to providers. Key provider-specific features:

**Anthropic** supports extended thinking with the `thinking` parameter:
```python
response = completion(
    model="anthropic/claude-sonnet-4-5-20250929",
    messages=[...],
    thinking={"type": "enabled", "budget_tokens": 5000},  # Extended thinking
    max_tokens=8000
)
print(response.choices[0].message.reasoning_content)  # Thinking output
```

**DeepSeek Reasoner** uses similar syntax but without budget control:
```python
response = completion(
    model="deepseek/deepseek-reasoner",
    messages=[...],
    thinking={"type": "enabled"}  # No budget_tokens support
)
```

**Mistral's magistral models** enable reasoning via prompt engineering (LiteLLM handles this automatically):
```python
response = completion(
    model="mistral/magistral-medium-2506",
    messages=[...],
    reasoning_effort="high"  # Triggers system prompt for step-by-step thinking
)
```

**OpenAI's GPT-5 models** support verbosity control and reasoning summaries:
```python
response = completion(
    model="openai/gpt-5.1",
    messages=[...],
    reasoning_effort={"effort": "high", "summary": "detailed"},
    verbosity="low"  # Concise responses
)
```

## Router configuration enables production-grade reliability

The Router class provides load balancing, fallbacks, and distributed state management:

```python
from litellm import Router

router = Router(
    model_list=[...],  # Same format as config.yaml model_list
    routing_strategy="simple-shuffle",  # Recommended for production
    fallbacks=[{"gpt-4": ["claude-sonnet", "bedrock-claude"]}],
    num_retries=3,
    timeout=30,
    allowed_fails=3,  # Cooldown after 3 failures
    cooldown_time=30,
    # Redis for distributed state (required for multi-instance)
    redis_host="redis.example.com",
    redis_password="...",
    redis_port=6379,
)

response = await router.acompletion(model="gpt-4", messages=[...])
```

**Five routing strategies** address different optimization goals:

| Strategy | Best For |
|----------|----------|
| `simple-shuffle` | General production (default, lowest latency overhead) |
| `usage-based-routing-v2` | Staying within rate limits |
| `latency-based-routing` | Minimizing response time |
| `cost-based-routing` | Reducing spend |
| `least-busy` | Even load distribution |

## Complete provider reference spans 100+ integrations

The full provider list includes specialized categories beyond the major players:

- **Image generation**: Fal AI, Stability AI, Recraft, RunwayML
- **Embeddings**: Voyage AI, Jina AI, Cohere, Mistral
- **Speech/transcription**: ElevenLabs, Deepgram, Groq Whisper
- **Rerank**: Cohere, Together AI, vLLM
- **Sovereign/regional**: Nscale (EU), OVHCloud, Nebius AI Studio
- **Enterprise platforms**: Databricks, Snowflake, SAP GenAI Hub, WatsonX
- **Local inference**: Ollama, vLLM, LM Studio, Llamafile, Xinference, Lemonade

Each follows the same prefix pattern: `provider/model-name`. The LiteLLM documentation at docs.litellm.ai/docs/providers maintains the authoritative list.

## Multi-instance provider configuration

**Multiple deployments of the same provider** are common in enterprise environments. Azure customers often have multiple regional deployments, AWS users may have multiple accounts, and teams may run multiple local LM Studio instances.

**Azure multi-instance example:**
```python
# Primary Azure deployment
os.environ["AZURE_API_KEY"] = "key1"
os.environ["AZURE_API_BASE"] = "https://eastus.openai.azure.com/"
os.environ["AZURE_API_VERSION"] = "2023-05-15"

# Use deployment-specific model names
response = completion(model="azure/gpt-4-eastus", messages=[...])
response = completion(model="azure/gpt-4-westus", messages=[...])
```

**LM Studio multi-instance example:**
```python
# Multiple local servers on different ports
os.environ["LM_STUDIO_API_BASE"] = "http://localhost:1234/v1"  # Primary

# For additional instances, use direct api_base parameter
response = completion(
    model="lm_studio/llama-3.1-8b",
    api_base="http://localhost:1234/v1",
    messages=[...]
)

response = completion(
    model="lm_studio/mistral-7b",
    api_base="http://localhost:5678/v1",  # Different port
    messages=[...]
)
```

**Generic provider support:** UER automatically detects any provider with a configured API key. If we don't have a specific model query implementation, example models are provided. This means you can use **any of LiteLLM's 100+ providers** immediately:

```python
# These work automatically with just the API key
os.environ["COHERE_API_KEY"] = "..."
os.environ["TOGETHERAI_API_KEY"] = "..."
os.environ["REPLICATE_API_KEY"] = "..."
os.environ["HUGGINGFACE_API_KEY"] = "..."

# Use standard prefix/model format
response = completion(model="cohere_chat/command-r-plus", messages=[...])
response = completion(model="together_ai/meta-llama/Llama-3-70b-chat-hf", messages=[...])
```

## Best practices for multi-provider architectures

**Credential management**: Use environment variables with the `os.environ/VAR_NAME` syntax in config.yaml. For enterprise clouds, prefer managed identities over static credentials—Azure's `DefaultAzureCredential`, AWS's IRSA/instance roles, or GCP's Workload Identity.

**Failover design**: Define fallback chains that cross provider boundaries. Context window fallbacks handle token overflow gracefully. Content policy fallbacks route around provider-specific restrictions:

```yaml
litellm_settings:
  fallbacks: [{"openai-gpt4": ["anthropic-claude", "bedrock-claude"]}]
  context_window_fallbacks: [{"gpt-4": ["claude-3-opus"]}]  # Claude has 200k context
  content_policy_fallbacks: [{"gpt-4": ["claude-3-sonnet"]}]
```

**Production deployment**: Always use Redis for state sharing across proxy instances. Enable `pre_call_checks` to filter unhealthy deployments before requests. Set appropriate `rpm` limits per deployment to enable intelligent routing.

**Self-hosted integration**: Use `hosted_vllm/` prefix for vLLM servers (the `vllm/` prefix is deprecated). Remember `/v1` suffix in api_base URLs for Llamafile. LM Studio prefers `LM_STUDIO_API_BASE` but also supports `OPENAI_API_BASE` for compatibility.

## Conclusion

LiteLLM's provider integration model successfully abstracts authentication complexity while preserving access to provider-specific capabilities. The consistent `provider/model` prefix pattern, unified completion interface, and flexible router configuration enable architectures that span from local development (Ollama) through enterprise production (Azure/Bedrock/Vertex) with minimal code changes. For teams building LLM-powered systems, this abstraction layer significantly reduces the operational burden of multi-provider deployments while maintaining the flexibility to leverage each provider's unique strengths.