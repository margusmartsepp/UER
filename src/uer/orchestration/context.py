"""Enhanced context manager with Jinja2 templates and registry data fetching."""

import logging
from datetime import datetime
from typing import Any

from jinja2 import BaseLoader, Environment, TemplateNotFound

from ..storage.manager import StorageManager

logger = logging.getLogger(__name__)


class RegistryLoader(BaseLoader):
    """Jinja2 loader that fetches templates from S3 storage."""

    def __init__(self, storage: StorageManager):
        """Initialize registry loader.

        Args:
            storage: Storage manager for fetching templates
        """
        self.storage = storage
        self._cache: dict[str, tuple[str, str | None]] = {}

    def get_source(self, environment: Environment, template: str):
        """Load template from storage.

        Args:
            environment: Jinja2 environment
            template: Template URI (e.g., 'registry://templates/prompt.md' or 's3://bucket/key')

        Returns:
            Tuple of (source, filename, uptodate_func)
        """
        # Check cache first
        if template in self._cache:
            source, etag = self._cache[template]
            return source, template, lambda: True

        try:
            if not self.storage.is_available():
                logger.warning(f"Storage not available, cannot load template: {template}")
                raise TemplateNotFound(template)

            # Fetch from storage
            content, metadata = self.storage.get_sync(template)
            source = content.decode("utf-8")
            etag = metadata.etag if hasattr(metadata, "etag") else None

            # Cache it
            self._cache[template] = (source, etag)

            logger.debug(f"Loaded template from {template} ({len(source)} chars)")
            return source, template, lambda: True

        except Exception as e:
            logger.error(f"Failed to load template {template}: {e}")
            raise TemplateNotFound(template) from None


class ContextManager:
    """Manages context assembly with Jinja2 templates and registry data fetching.

    Features:
    - Template-based context assembly
    - Registry data expansion ({{ uri | expand }})
    - Token optimization through caching
    - Dynamic variable injection
    - Nested template support
    """

    def __init__(self, storage: StorageManager | None = None):
        """Initialize context manager.

        Args:
            storage: Storage manager for registry access
        """
        self.storage = storage or StorageManager()

        # Initialize Jinja2 environment with registry loader
        self.env = Environment(
            loader=RegistryLoader(self.storage),
            autoescape=False,  # Don't escape for LLM prompts
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["expand"] = self._expand_filter
        self.env.filters["fetch"] = self._fetch_filter
        self.env.filters["truncate_tokens"] = self._truncate_tokens_filter
        self.env.filters["summarize"] = self._summarize_filter

        # Context cache for token optimization
        self._context_cache: dict[str, tuple[str, datetime]] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

        logger.info("ContextManager initialized with Jinja2 support")

    def _expand_filter(self, uri: str) -> str:
        """Jinja2 filter to expand a URI by fetching its content.

        Usage: {{ 'registry://context/analysis.txt' | expand }}

        Args:
            uri: URI to expand

        Returns:
            Content from the URI
        """
        try:
            # Check cache
            if uri in self._context_cache:
                content, cached_at = self._context_cache[uri]
                age = (datetime.now() - cached_at).total_seconds()
                if age < self._cache_ttl_seconds:
                    logger.debug(f"Cache hit for {uri} (age: {age:.1f}s)")
                    return content

            if not self.storage.is_available():
                logger.warning(f"Storage not available, cannot expand: {uri}")
                return f"[Storage unavailable: {uri}]"

            # Fetch from storage
            content_bytes, metadata = self.storage.get_sync(uri)
            content = content_bytes.decode("utf-8")

            # Cache it
            self._context_cache[uri] = (content, datetime.now())

            logger.info(f"Expanded {uri} ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"Failed to expand {uri}: {e}")
            return f"[Error expanding {uri}: {e}]"

    def _fetch_filter(self, uri: str, default: str = "") -> str:
        """Jinja2 filter to fetch content with a default fallback.

        Usage: {{ 'registry://context/optional.txt' | fetch('default value') }}

        Args:
            uri: URI to fetch
            default: Default value if fetch fails

        Returns:
            Content or default value
        """
        try:
            return self._expand_filter(uri)
        except Exception:
            return default

    def _truncate_tokens_filter(self, text: str, max_tokens: int = 1000) -> str:
        """Jinja2 filter to truncate text to approximate token count.

        Usage: {{ long_text | truncate_tokens(500) }}

        Args:
            text: Text to truncate
            max_tokens: Maximum token count (approximate)

        Returns:
            Truncated text
        """
        # Rough approximation: 4 chars per token
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text

        truncated = text[:max_chars]
        logger.debug(
            f"Truncated text from {len(text)} to {len(truncated)} chars (~{max_tokens} tokens)"
        )
        return truncated + "..."

    def _summarize_filter(self, text: str, max_lines: int = 10) -> str:
        """Jinja2 filter to summarize text by taking first N lines.

        Usage: {{ long_text | summarize(5) }}

        Args:
            text: Text to summarize
            max_lines: Maximum number of lines

        Returns:
            Summarized text
        """
        lines = text.split("\n")
        if len(lines) <= max_lines:
            return text

        summary = "\n".join(lines[:max_lines])
        logger.debug(f"Summarized text from {len(lines)} to {max_lines} lines")
        return summary + f"\n... ({len(lines) - max_lines} more lines)"

    async def render_template(
        self, template_uri: str, variables: dict[str, Any] | None = None
    ) -> str:
        """Render a Jinja2 template with variables.

        Args:
            template_uri: URI to template (e.g., 'registry://templates/prompt.md')
            variables: Variables to inject into template

        Returns:
            Rendered template content
        """
        variables = variables or {}

        try:
            template = self.env.get_template(template_uri)
            rendered = template.render(**variables)
            logger.info(f"Rendered template {template_uri} ({len(rendered)} chars)")
            return rendered

        except Exception as e:
            logger.error(f"Failed to render template {template_uri}: {e}")
            raise

    def render_string(self, template_string: str, variables: dict[str, Any] | None = None) -> str:
        """Render a template string with variables.

        Args:
            template_string: Template content as string
            variables: Variables to inject into template

        Returns:
            Rendered content
        """
        variables = variables or {}

        try:
            template = self.env.from_string(template_string)
            rendered = template.render(**variables)
            logger.debug(f"Rendered string template ({len(rendered)} chars)")
            return rendered

        except Exception as e:
            logger.error(f"Failed to render string template: {e}")
            raise

    async def assemble_context(
        self,
        template: str | None = None,
        context_refs: list[str] | None = None,
        variables: dict[str, Any] | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Assemble context from template and/or URIs.

        Args:
            template: Template string or URI to render
            context_refs: List of URIs to expand and include
            variables: Variables for template rendering
            max_tokens: Optional token limit for truncation

        Returns:
            Assembled context string
        """
        variables = variables or {}
        parts: list[str] = []

        # Add context refs as variables
        if context_refs:
            for i, uri in enumerate(context_refs):
                try:
                    content = self._expand_filter(uri)
                    variables[f"context_{i}"] = content
                    variables[f"context_{i}_uri"] = uri
                except Exception as e:
                    logger.warning(f"Failed to load context ref {uri}: {e}")

        # Render template if provided
        if template:
            if template.startswith("registry://") or template.startswith("s3://"):
                # Template URI
                rendered = await self.render_template(template, variables)
            else:
                # Template string
                rendered = self.render_string(template, variables)
            parts.append(rendered)

        # Add raw context refs if no template
        elif context_refs:
            for uri in context_refs:
                try:
                    content = self._expand_filter(uri)
                    parts.append(f"# Context from {uri}\n\n{content}")
                except Exception as e:
                    logger.warning(f"Failed to expand {uri}: {e}")

        # Combine parts
        assembled = "\n\n---\n\n".join(parts)

        # Truncate if needed
        if max_tokens:
            assembled = self._truncate_tokens_filter(assembled, max_tokens)

        logger.info(f"Assembled context ({len(assembled)} chars, ~{len(assembled) // 4} tokens)")
        return assembled

    def clear_cache(self) -> None:
        """Clear the context cache."""
        self._context_cache.clear()
        logger.info("Cleared context cache")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        now = datetime.now()
        valid_entries = sum(
            1
            for _, (_, cached_at) in self._context_cache.items()
            if (now - cached_at).total_seconds() < self._cache_ttl_seconds
        )

        return {
            "total_entries": len(self._context_cache),
            "valid_entries": valid_entries,
            "ttl_seconds": self._cache_ttl_seconds,
        }
