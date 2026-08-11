#!/usr/bin/env python3
"""Regenerate img/work/ from ../sources/. Manifest-driven; rerunnable.

Sources stay outside the repo (originals + provenance in ../sources/); this
script emits web-ready JPEGs. PDFs render via pdftoppm (poppler). Screenshot
filenames carry macOS narrow no-break spaces, so entries match by prefix
instead of exact name.
"""
import pathlib
import subprocess
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).parent
SOURCES = ROOT.parent / "sources"
LOCAL = SOURCES / "local"
PULLED = SOURCES / "skreened-archive" / "pulled"
OUT = ROOT / "img" / "work"

MAX_W = 1600
CROP_TOP = 2600  # era full-page screenshots: keep the top of the page
QUALITY = 84


def find(base: pathlib.Path, sub: str, prefix: str) -> pathlib.Path:
    hits = [p for p in (base / sub).iterdir() if p.name.startswith(prefix)]
    if len(hits) != 1:
        sys.exit(f"expected 1 match for {sub}/{prefix}*, got {len(hits)}")
    return hits[0]


# (case, out-name, source, options)
M = [
    # Skreened: brand sheet + campaigns are local; storefront eras + engine from archive
    ("skreened", "01-brand-sheet.jpg", find(LOCAL, "Older Design Projects", "2.jpg"), {}),
    ("skreened", "02-campaign-tiles.jpg", find(LOCAL, "Older Design Projects", "3.jpg"), {}),
    ("skreened", "03-storefront-2011.jpg", PULLED / "era-2011.png", {"crop_top": CROP_TOP}),
    ("skreened", "04-storefront-2013.jpg", PULLED / "era-2013.png", {"crop_top": CROP_TOP}),
    ("skreened", "05-storefront-2015.jpg", PULLED / "era-2015.png", {"crop_top": CROP_TOP}),
    ("skreened", "06-holiday-campaign.jpg", PULLED / "marketing-holiday-home.jpg", {}),
    ("skreened", "07-engine-output.jpg", PULLED / "engine-preview-output.jpg", {}),
    ("skreened", "10-template-tee.jpg", PULLED / "engine-template-tee-white.jpg", {}),
    ("skreened", "11-template-tee-f.jpg", PULLED / "engine-template-tee-grass-f.jpg", {}),
    ("skreened", "12-template-crop.jpg", PULLED / "engine-template-crop-f.jpg", {}),
    ("skreened", "13-template-onepiece.jpg", PULLED / "engine-template-onepiece.jpg", {}),
    ("skreened", "14-template-tote.jpg", PULLED / "engine-template-tote.jpg", {}),
    ("skreened", "15-template-model.jpg", PULLED / "engine-template-model.jpg", {}),
    # Dizzy Charlie's: posters + print
    ("dizzy", "01-poster-high-note.jpg", find(LOCAL, "Dizzy Charlies", "Screenshot 2026-07-23 at 10.53.08"), {}),
    ("dizzy", "02-poster-sun-sets.jpg", find(LOCAL, "Dizzy Charlies", "Screenshot 2026-07-23 at 10.53.21"), {}),
    ("dizzy", "03-poster-winter.jpg", find(LOCAL, "Dizzy Charlies", "Screenshot 2026-07-23 at 10.50.04"), {}),
    ("dizzy", "04-poster-kids.jpg", find(LOCAL, "Dizzy Charlies", "Screenshot 2026-07-23 at 10.51.07"), {}),
    ("dizzy", "05-poster-cocktail.jpg", find(LOCAL, "Dizzy Charlies", "a little friendly"), {}),
    ("dizzy", "06-fundraiser-packet.jpg", find(LOCAL, "Dizzy Charlies", "Downtown Summer"), {"pdf_page": 1}),
    ("dizzy", "07-booklet.jpg", find(LOCAL, "Dizzy Charlies", "booklet"), {"pdf_page": 1}),
    # Unfold Fest
    ("unfold", "01-mark.jpg", find(LOCAL, "unfold fest", "Screenshot 2026-07-23 at 11.20.56"), {}),
    ("unfold", "02-photo-treatment.jpg", find(LOCAL, "unfold fest", "Screenshot 2026-07-23 at 11.20.47"), {}),
    ("unfold", "03-costa-rica.jpg", find(LOCAL, "unfold fest", "Screenshot 2026-07-23 at 11.21.17"), {}),
    ("unfold", "04-unfoldcast.jpg", find(LOCAL, "unfold fest", "Screenshot 2026-07-23 at 11.22.41"), {}),
    # Brothers Drake labels
    ("drake", "01-labels.jpg", find(LOCAL, "Older Design Projects", "10.jpg"), {}),
    # Sarah Banker
    ("banker", "01-friends.jpg", find(LOCAL, "various", "Screenshot 2026-07-23 at 11.10.42"), {}),
    ("banker", "02-cockadoodledoo.jpg", find(LOCAL, "various", "Screenshot 2026-07-23 at 11.12.51"), {}),
    ("banker", "03-artist.jpg", find(LOCAL, "various", "Screenshot 2026-07-23 at 11.08.25"), {}),
    # Identity work
    ("cagent", "01-studies.jpg", find(LOCAL, "Cagent", "Screenshot 2024-12-20"), {}),
    ("cagent", "02-lockup.jpg", find(LOCAL, "Cagent", "Screenshot 2026-07-23 at 10.43.03"), {}),
    ("cory", "01-card-dark.jpg", find(LOCAL, "Cory and Company", "Screenshot 2026-07-23 at 11.01.00"), {}),
    ("cory", "02-card-light.jpg", find(LOCAL, "Cory and Company", "Screenshot 2026-07-23 at 11.01.22"), {}),
    ("cory", "03-yard-sign.jpg", find(LOCAL, "Cory and Company", "Screenshot 2026-07-23 at 11.03.40"), {}),
    ("peptides", "01-board.jpg", find(LOCAL, "First Person Peptides", "Artboard 1 copy.pdf"), {"pdf_page": 1}),
    ("peptides", "02-board.jpg", find(LOCAL, "First Person Peptides", "Artboard 1 copy 2"), {"pdf_page": 1}),
    # Earlier pieces
    ("earlier", "01-acada.jpg", find(LOCAL, "Older Design Projects", "11.jpg"), {}),
    ("earlier", "02-clipcake.jpg", find(LOCAL, "Older Design Projects", "8.jpg"), {}),
    ("earlier", "03-gramercy.jpg", find(LOCAL, "Older Design Projects", "5.jpg"), {}),
]


def render_pdf(src: pathlib.Path, page: int, tmp: pathlib.Path) -> pathlib.Path:
    subprocess.run(
        ["pdftoppm", "-jpeg", "-r", "200", "-f", str(page), "-l", str(page),
         "-singlefile", str(src), str(tmp / "pdfpage")],
        check=True, capture_output=True,
    )
    return tmp / "pdfpage.jpg"


def main() -> None:
    tmp = ROOT / ".prep-tmp"
    tmp.mkdir(exist_ok=True)
    for case, name, src, opts in M:
        dest_dir = OUT / case
        dest_dir.mkdir(parents=True, exist_ok=True)
        path = render_pdf(src, opts["pdf_page"], tmp) if "pdf_page" in opts else src
        im = Image.open(path).convert("RGB")
        if "crop_top" in opts and im.height > opts["crop_top"]:
            im = im.crop((0, 0, im.width, opts["crop_top"]))
        if im.width > MAX_W:
            im = im.resize((MAX_W, int(im.height * MAX_W / im.width)), Image.LANCZOS)
        out = dest_dir / name
        im.save(out, "JPEG", quality=QUALITY, optimize=True)
        print(f"  {case}/{name}  {im.width}x{im.height}  {out.stat().st_size // 1024}KB")
    # provenance rides with the pulled assets
    src_md = SOURCES / "skreened-archive" / "SOURCES.md"
    if src_md.exists():
        (OUT / "skreened" / "SOURCES.md").write_text(src_md.read_text(), encoding="utf-8")
    for leftover in tmp.iterdir():
        leftover.unlink()
    tmp.rmdir()
    print("done")


if __name__ == "__main__":
    main()
