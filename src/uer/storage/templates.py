"""
Template manager with Jinja2 for context expansion.

Provides Jinja2 template rendering with custom filters to expand
content from S3 storage, enabling efficient context injection.
"""

from jinja2 import BaseLoader, Environment, TemplateNotFound
from typing import Optional

from .base import StorageBackend, ObjectNotFoundError


class S3TemplateLoader(BaseLoader):
    """
    Jinja2 loader that loads templates from S3 storage.

    Templates are stored in the uer-templates bucket.
    """

    def __init__(self, backend: StorageBackend, bucket: str = "uer-templates"):
        """
        Initialize S3 template loader.

        Args:
            backend: Storage backend
            bucket: Bucket to load templates from (default: uer-templates)
        """
        self.backend = backend
        self.bucket = bucket

    def get_source(self, environment: Environment, template: str):
        """
        Load template source from S3.

        Args:
            environment: Jinja2 environment
            template: Template key (e.g., "meeting-notes.md")

        Returns:
            Tuple of (source, filename, uptodate_func)

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            # Load template from S3
            data, metadata = self.backend.get_object(self.bucket, template)
            source = data.decode("utf-8")

            # Return (source, filename, uptodate function)
            # uptodate function returns True if template is still current
            return source, template, lambda: True

        except ObjectNotFoundError:
            raise TemplateNotFound(template)

    async def get_source_async(self, template: str):
        """
        Async version of get_source.

        Args:
            template: Template key

        Returns:
            Tuple of (source, filename, uptodate_func)

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            data, metadata = await self.backend.get_object(self.bucket, template)
            source = data.decode("utf-8")
            return source, template, lambda: True
        except ObjectNotFoundError:
            raise TemplateNotFound(template)


class TemplateManager:
    """
    Manage Jinja2 templates with S3 storage and custom filters.

    Custom filters:
    - {{ uri | expand }}: Load content from S3 URI
    - {{ key | s3 }}: Load content from default templates bucket
    """

    def __init__(
        self, backend: StorageBackend, bucket: str = "uer-templates", enable_async: bool = True
    ):
        """
        Initialize template manager.

        Args:
            backend: Storage backend
            bucket: Default bucket for templates (default: uer-templates)
            enable_async: Enable async template rendering (default: True)
        """
        self.backend = backend
        self.bucket = bucket

        # Create Jinja2 environment
        self.loader = S3TemplateLoader(backend, bucket)
        self.env = Environment(
            loader=self.loader,
            enable_async=enable_async,
            autoescape=False,  # Don't escape markdown/text
        )

        # Register custom filters
        self.env.filters["expand"] = self._make_expand_filter()
        self.env.filters["s3"] = self._make_s3_filter()

    def _make_expand_filter(self):
        """
        Create expand filter for async template rendering.

        Usage: {{ "s3://bucket/key" | expand }}
        """

        async def expand_filter(uri: str) -> str:
            """
            Jinja2 filter to expand content from S3 URI.

            Args:
                uri: S3 URI (e.g., "s3://uer-context/report.json")

            Returns:
                Content from S3 as string
            """
            from .manager import parse_uri

            bucket, key = parse_uri(uri)
            data, _ = await self.backend.get_object(bucket, key)
            return data.decode("utf-8")

        return expand_filter

    def _make_s3_filter(self):
        """
        Create s3 filter for loading from default bucket.

        Usage: {{ "context/background.md" | s3 }}
        """

        async def s3_filter(key: str) -> str:
            """
            Jinja2 filter to load content from default templates bucket.

            Args:
                key: Object key in templates bucket

            Returns:
                Content from S3 as string
            """
            data, _ = await self.backend.get_object(self.bucket, key)
            return data.decode("utf-8")

        return s3_filter

    async def render(self, template_key: str, context: dict) -> str:
        """
        Render template with context.

        Args:
            template_key: Template key in bucket (e.g., "meeting-notes.md")
            context: Context variables for template

        Returns:
            Rendered template as string

        Example:
            >>> rendered = await templates.render(
            ...     "meeting-notes.md",
            ...     {
            ...         "meeting": {
            ...             "title": "Sprint Planning",
            ...             "date": "2026-01-10",
            ...             "attendees": ["Alice", "Bob"]
            ...         }
            ...     }
            ... )
        """
        # Load template source
        source, _, _ = await self.loader.get_source_async(template_key)

        # Create template from source
        template = self.env.from_string(source)

        # Render template
        rendered = await template.render_async(**context)
        return rendered

    async def render_string(self, template_string: str, context: dict) -> str:
        """
        Render template from string instead of stored template.

        Args:
            template_string: Template content as string
            context: Context variables for template

        Returns:
            Rendered template

        Example:
            >>> rendered = await templates.render_string(
            ...     "# Meeting: {{ title }}\\n{{ background | s3 }}",
            ...     {"title": "Sprint Planning", "background": "context/bg.md"}
            ... )
        """
        template = self.env.from_string(template_string)
        rendered = await template.render_async(**context)
        return rendered

    async def list_templates(self, prefix: str = "") -> list[str]:
        """
        List available templates.

        Args:
            prefix: Optional prefix to filter by (e.g., "project-specs/")

        Returns:
            List of template keys

        Example:
            >>> templates_list = await templates.list_templates()
            >>> # ['meeting-notes.md', 'action-items.md', 'project-specs/api-design.md']
        """
        objects = await self.backend.list_objects(
            bucket=self.bucket, prefix=prefix, recursive=True
        )
        return [obj.key for obj in objects]

    async def create_template(
        self, key: str, content: str | bytes, content_type: str = "text/markdown"
    ) -> None:
        """
        Create or update a template.

        Args:
            key: Template key (e.g., "meeting-notes.md")
            content: Template content
            content_type: MIME type (default: text/markdown)

        Example:
            >>> await templates.create_template(
            ...     "meeting-notes.md",
            ...     '''# Meeting: {{ meeting.title }}
            ...     Date: {{ meeting.date }}
            ...     '''
            ... )
        """
        if isinstance(content, str):
            content = content.encode("utf-8")

        await self.backend.put_object(
            bucket=self.bucket, key=key, data=content, content_type=content_type
        )

    async def delete_template(self, key: str) -> bool:
        """
        Delete a template.

        Args:
            key: Template key

        Returns:
            True if deleted, False if didn't exist
        """
        return await self.backend.delete_object(self.bucket, key)
