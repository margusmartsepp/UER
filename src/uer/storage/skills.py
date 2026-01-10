"""
Skills manager for Claude Skills API compliance.

Handles creating, retrieving, and exporting skills in a format compatible
with Claude Skills API while also supporting cross-LLM usage.
"""

import json
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .base import StorageBackend, ObjectMetadata


class SkillMetadata(BaseModel):
    """Metadata for a skill."""

    name: str
    display_title: str
    created_at: datetime
    updated_at: datetime
    file_count: int
    description: str | None = None


class Skill(BaseModel):
    """Complete skill with all files."""

    name: str
    display_title: str
    files: dict[str, str]  # filename -> content
    metadata: SkillMetadata


class SkillsManager:
    """
    Manage Claude Skills in S3 storage.

    Skills are stored as:
    s3://uer-skills/{skill-name}/SKILL.md
    s3://uer-skills/{skill-name}/scripts/analyze.py
    s3://uer-skills/{skill-name}/.metadata.json
    """

    def __init__(self, backend: StorageBackend):
        """
        Initialize skills manager.

        Args:
            backend: Storage backend to use
        """
        self.backend = backend
        self.bucket = "uer-skills"

    async def create_skill(
        self,
        name: str,
        display_title: str,
        files: dict[str, bytes | str],
        description: str | None = None,
    ) -> SkillMetadata:
        """
        Create skill in storage.

        Args:
            name: Skill identifier (slug, e.g., "financial-analysis")
            display_title: Human-readable title (e.g., "Financial Analysis")
            files: {"SKILL.md": content, "scripts/analyze.py": content, ...}
            description: Optional description

        Returns:
            SkillMetadata

        Raises:
            ValueError: If SKILL.md is missing from files

        Example:
            >>> metadata = await skills.create_skill(
            ...     name="financial-analysis",
            ...     display_title="Financial Analysis",
            ...     files={
            ...         "SKILL.md": skill_md_content,
            ...         "scripts/analyze.py": script_content
            ...     }
            ... )
        """
        # Validate SKILL.md exists
        if "SKILL.md" not in files:
            raise ValueError("SKILL.md is required in files")

        # Store all files under skill prefix
        for filename, content in files.items():
            # Convert string to bytes if needed
            if isinstance(content, str):
                content = content.encode("utf-8")

            key = f"{name}/{filename}"
            await self.backend.put_object(
                bucket=self.bucket,
                key=key,
                data=content,
                content_type=self._get_content_type(filename),
            )

        # Create and store metadata
        now = datetime.utcnow()
        metadata = SkillMetadata(
            name=name,
            display_title=display_title,
            created_at=now,
            updated_at=now,
            file_count=len(files),
            description=description or self._extract_description(files.get("SKILL.md", b"")),
        )

        await self.backend.put_object(
            bucket=self.bucket,
            key=f"{name}/.metadata.json",
            data=metadata.model_dump_json().encode(),
            content_type="application/json",
        )

        return metadata

    async def get_skill(self, name: str) -> Skill:
        """
        Retrieve complete skill with all files.

        Args:
            name: Skill identifier

        Returns:
            Skill with all files

        Example:
            >>> skill = await skills.get_skill("financial-analysis")
            >>> print(skill.files["SKILL.md"])
        """
        # List all files in skill
        files_meta = await self.backend.list_objects(
            bucket=self.bucket, prefix=f"{name}/", recursive=True
        )

        # Load all files
        files = {}
        metadata_json = None

        for file_meta in files_meta:
            # Skip metadata file
            if file_meta.key.endswith(".metadata.json"):
                data, _ = await self.backend.get_object(self.bucket, file_meta.key)
                metadata_json = data.decode("utf-8")
                continue

            # Load file content
            data, _ = await self.backend.get_object(self.bucket, file_meta.key)
            filename = file_meta.key.replace(f"{name}/", "")
            files[filename] = data.decode("utf-8")

        # Parse metadata
        if metadata_json:
            metadata = SkillMetadata.model_validate_json(metadata_json)
        else:
            # Create default metadata if missing
            metadata = SkillMetadata(
                name=name,
                display_title=name.replace("-", " ").title(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                file_count=len(files),
            )

        return Skill(
            name=name, display_title=metadata.display_title, files=files, metadata=metadata
        )

    async def list_skills(self) -> list[SkillMetadata]:
        """
        List all available skills.

        Returns:
            List of SkillMetadata

        Example:
            >>> skills_list = await skills.list_skills()
            >>> for skill in skills_list:
            ...     print(f"{skill.name}: {skill.display_title}")
        """
        # List top-level objects (skills are directories)
        objects = await self.backend.list_objects(
            bucket=self.bucket, prefix="", recursive=False
        )

        # Extract unique skill names from object keys
        skill_names = set()
        for obj in objects:
            # Extract first path component (skill name)
            parts = obj.key.split("/")
            if parts:
                skill_names.add(parts[0])

        # Load metadata for each skill
        skills_list = []
        for skill_name in skill_names:
            try:
                # Try to load metadata file
                data, _ = await self.backend.get_object(
                    self.bucket, f"{skill_name}/.metadata.json"
                )
                metadata = SkillMetadata.model_validate_json(data.decode("utf-8"))
                skills_list.append(metadata)
            except Exception:
                # If metadata missing, create default
                skills_list.append(
                    SkillMetadata(
                        name=skill_name,
                        display_title=skill_name.replace("-", " ").title(),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        file_count=0,
                    )
                )

        return skills_list

    async def export_for_api(self, name: str) -> dict:
        """
        Export skill for Claude Skills API POST /v1/skills.

        Args:
            name: Skill identifier

        Returns:
            Dict with format: {"display_title": "...", "files": [...]}

        Example:
            >>> export = await skills.export_for_api("financial-analysis")
            >>> # Use with Claude API:
            >>> client.beta.skills.create(
            ...     display_title=export["display_title"],
            ...     files=export["files"],
            ...     betas=["skills-2025-10-02"]
            ... )
        """
        skill = await self.get_skill(name)

        # Convert files to Claude API format
        files = []
        for filename, content in skill.files.items():
            files.append({"filename": filename, "content": content.encode("utf-8")})

        return {"display_title": skill.display_title, "files": files}

    async def to_system_prompt(self, name: str) -> str:
        """
        Convert skill to system prompt for non-Claude LLMs.

        Parses SKILL.md and creates a comprehensive system prompt that
        can be used with GPT, Gemini, or other LLMs.

        Args:
            name: Skill identifier

        Returns:
            System prompt string

        Example:
            >>> prompt = await skills.to_system_prompt("financial-analysis")
            >>> response = await llm_call(
            ...     model="openai/gpt-5.2",
            ...     messages=[
            ...         {"role": "system", "content": prompt},
            ...         {"role": "user", "content": "Analyze this report..."}
            ...     ]
            ... )
        """
        skill = await self.get_skill(name)

        # Parse SKILL.md
        skill_md = skill.files.get("SKILL.md", "")
        yaml_frontmatter, instructions = self._parse_skill_md(skill_md)

        # Build system prompt
        prompt = f"""# Skill: {yaml_frontmatter.get('name', name)}

{yaml_frontmatter.get('description', '')}

{instructions}

## Available Resources

"""

        # Add other files as context
        for filename, content in skill.files.items():
            if filename == "SKILL.md":
                continue

            if filename.endswith(".py"):
                prompt += f"\n### {filename}\n\n```python\n{content}\n```\n"
            elif filename.endswith(".js"):
                prompt += f"\n### {filename}\n\n```javascript\n{content}\n```\n"
            elif filename.endswith(".md"):
                prompt += f"\n### {filename}\n\n{content}\n"
            else:
                prompt += f"\n### {filename}\n\nFile available: {filename}\n"

        prompt += f"\n\nYou are now using the {yaml_frontmatter.get('name', name)} skill.\n"

        return prompt

    def _parse_skill_md(self, content: str | bytes) -> tuple[dict, str]:
        """
        Parse SKILL.md YAML frontmatter and instructions.

        Args:
            content: SKILL.md content

        Returns:
            Tuple of (yaml_frontmatter, instructions)
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        # Extract YAML frontmatter
        yaml_pattern = r"^---\n(.*?)\n---\n(.*)$"
        match = re.match(yaml_pattern, content, re.DOTALL)

        if match:
            yaml_text = match.group(1)
            instructions = match.group(2).strip()

            # Simple YAML parsing (key: value)
            yaml_data = {}
            for line in yaml_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    yaml_data[key.strip()] = value.strip()

            return yaml_data, instructions
        else:
            # No YAML frontmatter
            return {}, content.strip()

    def _extract_description(self, content: str | bytes) -> str:
        """Extract description from SKILL.md for metadata."""
        yaml_data, _ = self._parse_skill_md(content)
        return yaml_data.get("description", "")

    def _get_content_type(self, filename: str) -> str:
        """Infer content type from filename."""
        if filename.endswith(".md"):
            return "text/markdown"
        elif filename.endswith(".py"):
            return "text/x-python"
        elif filename.endswith(".js"):
            return "text/javascript"
        elif filename.endswith(".json"):
            return "application/json"
        elif filename.endswith(".yaml") or filename.endswith(".yml"):
            return "text/yaml"
        else:
            return "application/octet-stream"
