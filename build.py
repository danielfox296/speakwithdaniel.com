#!/usr/bin/env python3
"""speakwithdaniel.com static site generator.

Same idiom as daniel-fox.com / entuned / danielchristopherfox.com: edit `_src/`,
run `python3 build.py`, built HTML lands at the repo root. NEVER edit root *.html
by hand. Pure Python stdlib.
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "_src"
PAGES = SRC / "pages"
PARTIALS = SRC / "partials"
LAYOUTS = SRC / "layouts"

SITE_URL = "https://speakwithdaniel.com"

# Person schema for the designer surface. Deliberately quiet: no jobTitle, no links
# to the other properties. sameAs carries the confirmed LinkedIn profile only.
SCHEMA_ORG = {
    "@type": "Person",
    "name": "Daniel Fox",
    "url": SITE_URL,
    "sameAs": ["https://www.linkedin.com/in/danielcfox/"],
    "alumniOf": {"@type": "CollegeOrUniversity", "name": "The Ohio State University"},
    "knowsAbout": [
        "Brand identity design",
        "Packaging and print design",
        "Poster and campaign design",
        "Art direction",
        "E-commerce design",
        "Video production",
    ],
}


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def canonical_for(output: str) -> str:
    if output == "index.html":
        return f"{SITE_URL}/"
    return f"{SITE_URL}/{output}"


def build_schema(cfg: dict) -> str:
    schema = cfg.get("schema", SCHEMA_ORG)
    if not schema:
        return ""
    payload = {"@context": "https://schema.org", **schema}
    return (
        '<script type="application/ld+json">'
        + json.dumps(payload, ensure_ascii=False)
        + "</script>"
    )


def build_page(page_dir: pathlib.Path) -> dict:
    cfg = json.loads(read(page_dir / "config.json"))
    output = cfg["output"]

    sections = sorted((page_dir / "sections").glob("*.html"))
    content = "\n".join(read(s) for s in sections)

    out_html = read(LAYOUTS / "base.html")
    for token, value in {
        "{{title}}": html.escape(cfg["title"]),
        "{{meta_description}}": html.escape(cfg.get("meta_description", ""), quote=True),
        "{{canonical}}": canonical_for(output),
        "{{robots}}": cfg.get("robots", "index, follow"),
        "{{schema}}": build_schema(cfg),
        "{{header}}": read(PARTIALS / "header.html"),
        "{{content}}": content,
        "{{footer}}": read(PARTIALS / "footer.html"),
    }.items():
        out_html = out_html.replace(token, value)

    (ROOT / output).write_text(out_html, encoding="utf-8")
    return {"output": output, "cfg": cfg}


def write_sitemap(pages: list[dict]) -> None:
    urls = []
    for page in pages:
        if page["cfg"].get("robots", "").startswith("noindex"):
            continue
        urls.append(f"  <url><loc>{html.escape(canonical_for(page['output']))}</loc></url>")
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def main() -> None:
    built = []
    for page_dir in sorted(PAGES.iterdir()):
        if page_dir.is_dir() and (page_dir / "config.json").exists():
            built.append(build_page(page_dir))
            print(f"  built {built[-1]['output']}")
    write_sitemap(built)
    print(f"Done. {len(built)} pages + sitemap.xml")


if __name__ == "__main__":
    main()
