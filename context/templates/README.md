# Research Templates

This directory contains Jinja2 templates for generating documentation from research insights.

## Templates

- **paper_insight.template.md** - Template for individual paper insights
- **HACKATHON_RESOURCES.template.md** - Template for the main hackathon resources document
- **track_summary.template.md** - Template for per-track summaries
- **detection_method.template.md** - Template for detection method documentation

## Template Variables

Templates use Jinja2 syntax with variables populated from:
- Paper metadata (title, authors, year, DOI, etc.)
- Extracted insights (findings, methods, examples, etc.)
- Cross-references (related papers, conflicting findings, etc.)

## Rendering

Templates can be rendered using:
- Python scripts with Jinja2 library
- UER's template rendering system (when implemented)
- Manual substitution for quick iterations

## Benefits

- Consistency across documentation
- Easy updates when new papers are added
- Automated generation of cross-references
- Version control for document structure
