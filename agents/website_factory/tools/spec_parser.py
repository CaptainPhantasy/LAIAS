"""
================================================================================
            WEBSITE FACTORY — SPEC PARSER
            "Turns the designer's markdown into a machine-readable contract."
================================================================================

Reads the output of the indiana_sewer_scope_designer (or any web design team
flow) and extracts structured data that the builder agents can consume
deterministically.

The spec is the single source of truth. Every builder reads from this.
Nobody improvises.

Author: LAIAS
Version: 1.0.0
================================================================================
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


# =============================================================================
# PARSED SPEC MODELS
# =============================================================================

class ColorToken(BaseModel):
    """A single color token from the design system."""
    name: str
    hex_value: str
    usage: str = ""

class TypographySpec(BaseModel):
    """Typography specification."""
    heading_font: str = "Plus Jakarta Sans"
    body_font: str = "Inter"
    scale: Dict[str, str] = Field(default_factory=dict)  # h1 -> "3rem", etc.

class SpacingSpec(BaseModel):
    """Spacing specification."""
    base_unit: int = 8  # px
    scale: Dict[str, str] = Field(default_factory=dict)  # xs -> "4px", etc.

class ComponentSpec(BaseModel):
    """Specification for a single UI component."""
    name: str
    variants: List[str] = Field(default_factory=list)
    props: Dict[str, Any] = Field(default_factory=dict)
    styles: Dict[str, str] = Field(default_factory=dict)

class PageSpec(BaseModel):
    """Specification for a single page."""
    model_config = {"populate_by_name": True}

    name: str
    path: str
    title: str = ""
    meta_description: str = ""
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    page_copy: Dict[str, str] = Field(
        default_factory=dict, alias="copy"
    )  # section_name -> copy text
    cta_primary: str = ""
    cta_secondary: str = ""

class SiteSpec(BaseModel):
    """
    Complete parsed specification — the machine-readable contract.
    This is what every builder agent reads. Nobody touches the raw markdown.
    """
    # Identity
    project_name: str
    spec_source: str  # path to original markdown file

    # Design System
    colors: List[ColorToken] = Field(default_factory=list)
    typography: TypographySpec = Field(default_factory=TypographySpec)
    spacing: SpacingSpec = Field(default_factory=SpacingSpec)
    components: List[ComponentSpec] = Field(default_factory=list)

    # Pages
    pages: List[PageSpec] = Field(default_factory=list)

    # Site-wide
    site_name: str = ""
    tagline: str = ""
    primary_cta: str = ""
    nav_links: List[str] = Field(default_factory=list)

    # Tech stack (from technical architect section)
    framework: str = "Next.js 14"
    styling: str = "Tailwind CSS 3"
    deployment: str = "Vercel"

    # Raw sections (fallback for anything not parsed)
    raw_sections: Dict[str, str] = Field(default_factory=dict)


# =============================================================================
# PARSER
# =============================================================================

class SpecParser:
    """
    Parses a website specification markdown file into a SiteSpec.

    The designer outputs a markdown file with clearly labeled sections.
    This parser is intentionally lenient — it extracts what it can and
    falls back to raw text for anything it can't parse structurally.
    The agents reading the spec can always fall back to raw_sections.
    """

    def __init__(self, spec_path: str):
        self.spec_path = Path(spec_path)
        if not self.spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")

        self.raw_content = self.spec_path.read_text()
        logger.info(
            "Spec file loaded", path=str(self.spec_path), size=len(self.raw_content)
        )

    def parse(self) -> SiteSpec:
        """Parse the spec file and return a SiteSpec."""
        logger.info("Parsing specification")

        spec = SiteSpec(
            project_name=self._extract_project_name(),
            spec_source=str(self.spec_path),
        )

        # Extract top-level sections
        sections = self._split_into_sections()
        spec.raw_sections = sections

        # Parse structured data from sections
        spec.colors = self._parse_colors(sections)
        spec.typography = self._parse_typography(sections)
        spec.spacing = self._parse_spacing(sections)
        spec.pages = self._parse_pages(sections)
        spec.nav_links = self._parse_nav_links(sections)
        spec.site_name = self._extract_site_name(sections)
        spec.tagline = self._extract_tagline(sections)
        spec.primary_cta = self._extract_primary_cta(sections)
        spec.framework, spec.styling, spec.deployment = self._parse_tech_stack(sections)

        logger.info(
            "Spec parsed successfully",
            colors=len(spec.colors),
            pages=len(spec.pages),
            nav_links=len(spec.nav_links),
        )

        return spec

    # =========================================================================
    # SECTION SPLITTING
    # =========================================================================

    def _split_into_sections(self) -> Dict[str, str]:
        """Split markdown into top-level sections by ## headers."""
        sections: Dict[str, str] = {}
        current_section = "preamble"
        current_content: List[str] = []

        for line in self.raw_content.split("\n"):
            if line.startswith("## "):
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[3:].strip().lower().replace(" ", "_")
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    # =========================================================================
    # PROJECT NAME
    # =========================================================================

    def _extract_project_name(self) -> str:
        """Extract project name from the # title."""
        match = re.search(r"^#\s+(.+)$", self.raw_content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return self.spec_path.stem.replace("_", " ").title()

    # =========================================================================
    # COLORS
    # =========================================================================

    def _parse_colors(self, sections: Dict[str, str]) -> List[ColorToken]:
        """Extract color tokens from design system section."""
        colors: List[ColorToken] = []

        color_text = ""
        for key in [
            "visual_design_system",
            "part_3:_visual_design_system",
            "design_system",
            "color_palette",
        ]:
            if key in sections:
                color_text = sections[key]
                break

        if not color_text:
            color_text = self.raw_content

        hex_pattern = re.compile(
            r"(?:[-–•*]\s*)?([A-Za-z][A-Za-z0-9\s\-_/]+?):\s*(#[0-9A-Fa-f]{6})\b(?:\s*[-–(]?\s*([^#\n]*))?",
            re.MULTILINE,
        )

        seen_hex = set()
        for match in hex_pattern.finditer(color_text):
            name = match.group(1).strip()
            hex_val = match.group(2).strip()
            usage = (match.group(3) or "").strip().rstrip(")")

            if hex_val in seen_hex or len(name) > 50:
                continue

            seen_hex.add(hex_val)
            colors.append(ColorToken(name=name, hex_value=hex_val, usage=usage))

        if not colors:
            colors = self._default_colors()

        return colors

    def _default_colors(self) -> List[ColorToken]:
        """Return sensible defaults if no colors found in spec."""
        return [
            ColorToken(name="Primary 900", hex_value="#0c4a6e", usage="dark backgrounds"),
            ColorToken(name="Primary 700", hex_value="#0369a1", usage="brand primary"),
            ColorToken(name="Primary 500", hex_value="#0ea5e9", usage="links, accents"),
            ColorToken(name="Accent 500", hex_value="#f97316", usage="CTAs, buttons"),
            ColorToken(name="Gray 900", hex_value="#111827", usage="headings"),
            ColorToken(name="Gray 700", hex_value="#374151", usage="body text"),
            ColorToken(name="Gray 100", hex_value="#f3f4f6", usage="backgrounds"),
            ColorToken(name="White", hex_value="#ffffff", usage="backgrounds"),
        ]

    # =========================================================================
    # TYPOGRAPHY
    # =========================================================================

    def _parse_typography(self, sections: Dict[str, str]) -> TypographySpec:
        """Extract typography spec."""
        spec = TypographySpec()

        text = ""
        for key in ["visual_design_system", "typography_system", "typography"]:
            if key in sections:
                text = sections[key]
                break

        if not text:
            return spec

        heading_match = re.search(
            r"heading\s+font[:\s]+([A-Za-z][A-Za-z0-9 \-]+?)(?:\n|,|\()",
            text,
            re.IGNORECASE,
        )
        if heading_match:
            spec.heading_font = heading_match.group(1).strip()

        body_match = re.search(
            r"body\s+font[:\s]+([A-Za-z][A-Za-z0-9 \-]+?)(?:\n|,|\()",
            text,
            re.IGNORECASE,
        )
        if body_match:
            spec.body_font = body_match.group(1).strip()

        scale_pattern = re.compile(
            r"(h[1-6]|body|caption|small)[:\s]+([\d.]+(?:rem|px|em))", re.IGNORECASE
        )
        for match in scale_pattern.finditer(text):
            spec.scale[match.group(1).lower()] = match.group(2)

        return spec

    # =========================================================================
    # SPACING
    # =========================================================================

    def _parse_spacing(self, sections: Dict[str, str]) -> SpacingSpec:
        """Extract spacing specification."""
        spec = SpacingSpec()

        text = ""
        for key in ["visual_design_system", "spacing_system", "spacing"]:
            if key in sections:
                text = sections[key]
                break

        if not text:
            return spec

        base_match = re.search(r"base\s+unit[:\s]+(\d+)\s*px", text, re.IGNORECASE)
        if base_match:
            spec.base_unit = int(base_match.group(1))

        scale_pattern = re.compile(
            r"(xs|sm|md|lg|xl|2xl|3xl)[:\s]+([\d.]+(?:rem|px))", re.IGNORECASE
        )
        for match in scale_pattern.finditer(text):
            spec.scale[match.group(1).lower()] = match.group(2)

        return spec

    # =========================================================================
    # PAGES & COPY
    # =========================================================================

    def _parse_pages(self, sections: Dict[str, str]) -> List[PageSpec]:
        """Extract strictly formatted pages and their content copy."""
        pages: List[PageSpec] = []
        
        # Pattern strictly enforces: "### Some Name (/some-path)"
        # Group 1 = Name, Group 2 = Path
        pattern = re.compile(r'^###\s+(.*?)\s*\((/[^\)]*)\)', re.MULTILINE)
        
        # We search the entire raw content to ensure we don't miss pages due to sectioning issues
        matches = list(pattern.finditer(self.raw_content))
        seen_paths = set()
        
        for i, match in enumerate(matches):
            name = match.group(1).strip()
            path = match.group(2).strip()
            
            # Prevent duplicate page extraction
            if path in seen_paths:
                continue
            seen_paths.add(path)
            
            # Content is everything from the end of this header 
            # to the start of the next page header (or EOF)
            start_idx = match.end()
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(self.raw_content)
            
            # Extract and clean the actual page copy
            raw_page_copy = self.raw_content[start_idx:end_idx].strip()
            
            copy_dict: Dict[str, str] = {
                "full_section": raw_page_copy
            }
            
            # Attempt to pluck out a hero headline if one exists in the copy block
            hero_match = re.search(r"(?:hero|headline)[:\s]+(.*?)(?:\n|$)", raw_page_copy, re.IGNORECASE)
            if hero_match:
                copy_dict["hero_headline"] = hero_match.group(1).strip()
                
            cta = self._extract_page_cta(name, sections)
            
            pages.append(PageSpec(
                name=name,
                path=path,
                title=name.title(),
                copy=copy_dict,
                cta_primary=cta
            ))
            
        return pages

    def _extract_page_cta(self, page_name: str, sections: Dict[str, str]) -> str:
        """Extract primary CTA for a page."""
        copy_text = sections.get(
            "part_4:_content_&_copy", sections.get("conversion_copy", "")
        )

        cta_match = re.search(
            r"(?:cta|button)[:\s]+[\"']?([A-Za-z][A-Za-z0-9\s]+)[\"']?",
            copy_text,
            re.IGNORECASE,
        )
        if cta_match:
            return cta_match.group(1).strip()

        return "Get Started"

    # =========================================================================
    # NAVIGATION
    # =========================================================================

    def _parse_nav_links(self, sections: Dict[str, str]) -> List[str]:
        """Extract navigation links."""
        nav_text = ""
        for key in [
            "part_2:_user_experience",
            "information_architecture",
            "navigation",
        ]:
            if key in sections:
                nav_text = sections[key]
                break

        if not nav_text:
            return ["Services", "Pricing", "About", "Contact"]

        nav_match = re.search(
            r"(?:main\s+navigation|nav\s+links?)[:\s]+(.*?)(?=\n\n|\Z)",
            nav_text,
            re.DOTALL | re.IGNORECASE,
        )
        if nav_match:
            items_text = nav_match.group(1)
            items = re.findall(
                r"[-*]\s+([A-Za-z][A-Za-z0-9\s]+?)(?:\s*[-–/]|$)",
                items_text,
                re.MULTILINE,
            )
            if items:
                return [i.strip() for i in items[:8]]

        return ["Services", "Pricing", "About", "Contact"]

    # =========================================================================
    # SITE-WIDE FIELDS
    # =========================================================================

    def _extract_site_name(self, sections: Dict[str, str]) -> str:
        """Extract the site/company name."""
        title_match = re.search(
            r"^#\s+(.+?)(?:\s*-\s*Complete Specification)?$",
            self.raw_content,
            re.MULTILINE,
        )
        if title_match:
            name = title_match.group(1)
            name = re.sub(
                r"\s*[-–]\s*.*specification.*", "", name, flags=re.IGNORECASE
            ).strip()
            return name
        return "Website"

    def _extract_tagline(self, sections: Dict[str, str]) -> str:
        """Extract the tagline."""
        for section_text in sections.values():
            tagline_match = re.search(
                r"tagline[:\s]+[\"']?(.+?)[\"']?(?:\n|$)", section_text, re.IGNORECASE
            )
            if tagline_match:
                return tagline_match.group(1).strip()
        return ""

    def _extract_primary_cta(self, sections: Dict[str, str]) -> str:
        """Extract the site-wide primary CTA."""
        for section_text in sections.values():
            cta_match = re.search(
                r"primary\s+cta[:\s]+[\"']?([A-Za-z][A-Za-z0-9\s]+)[\"']?",
                section_text,
                re.IGNORECASE,
            )
            if cta_match:
                return cta_match.group(1).strip()
        return "Book Inspection"

    def _parse_tech_stack(self, sections: Dict[str, str]) -> tuple[str, str, str]:
        """Extract tech stack choices."""
        tech_text = ""
        for key in [
            "part_5:_technical_implementation",
            "technical_architecture",
            "technology_stack",
        ]:
            if key in sections:
                tech_text = sections[key]
                break

        framework = "Next.js 14"
        styling = "Tailwind CSS 3"
        deployment = "Vercel"

        if not tech_text:
            return framework, styling, deployment

        fw_match = re.search(
            r"(?:framework|frontend)[:\s]+([^\n,]+)", tech_text, re.IGNORECASE
        )
        if fw_match:
            framework = fw_match.group(1).strip()

        style_match = re.search(
            r"(?:styling|css)[:\s]+([^\n,]+)", tech_text, re.IGNORECASE
        )
        if style_match:
            styling = style_match.group(1).strip()

        deploy_match = re.search(
            r"(?:hosting|deployment|platform)[:\s]+([^\n,]+)", tech_text, re.IGNORECASE
        )
        if deploy_match:
            deployment = deploy_match.group(1).strip()

        return framework, styling, deployment

    # =========================================================================
    # SAVE PARSED SPEC
    # =========================================================================

    def save_parsed_spec(self, spec: SiteSpec, output_path: str) -> str:
        """Save the parsed spec as JSON for agents to read."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(spec.model_dump_json(indent=2))
        logger.info("Parsed spec saved", path=str(output))
        return str(output)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def parse_spec(spec_path: str, output_path: Optional[str] = None) -> SiteSpec:
    """
    Parse a spec file and optionally save the result.
    """
    parser = SpecParser(spec_path)
    spec = parser.parse()

    if output_path:
        parser.save_parsed_spec(spec, output_path)

    return spec


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Parse website specification")
    parser.add_argument("spec", help="Path to spec markdown file")
    parser.add_argument("--output", "-o", help="Save parsed spec as JSON")
    parser.add_argument("--summary", "-s", action="store_true", help="Print summary")

    args = parser.parse_args()

    spec = parse_spec(args.spec, args.output)

    if args.summary or not args.output:
        print(f"\n{'=' * 60}")
        print(f"PARSED SPEC: {spec.project_name}")
        print(f"{'=' * 60}")
        print(f"  Site name   : {spec.site_name}")
        print(f"  Tagline     : {spec.tagline}")
        print(f"  Primary CTA : {spec.primary_cta}")
        print(f"  Framework   : {spec.framework}")
        print(f"  Styling     : {spec.styling}")
        print(f"  Colors      : {len(spec.colors)}")
        print(f"  Pages       : {len(spec.pages)}")
        print(f"  Nav links   : {spec.nav_links}")
        print(f"\n  PAGES:")
        for page in spec.pages:
            copy_preview = page.page_copy.get("full_section", "")[:40].replace('\n', ' ')
            has_copy = "✅ Copy found" if copy_preview else "❌ EMPTY"
            print(f"    {page.path:20s} -> {page.name} [{has_copy}]")
        print(f"\n  COLORS:")
        for color in spec.colors[:8]:
            print(f"    {color.hex_value}  {color.name}")
        print(f"{'=' * 60}\n")