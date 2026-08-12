#!/usr/bin/env python3
"""Photography + posters machinery: prep images from ../sources/photo/picks
and emit the two photo-heavy sections (05-posters, 07b-photography) with
deterministic scatter placements. Rerunnable; edit GROUPS/CROP here and
rerun. Daniel picked every frame himself (2026-08-13 picker paste); the
grouping and placement are the build's job, the curation is his.

Watermark rule: photo-042 and photo-060 carry a corner studio mark in the
source; they ship with the bottom cropped. The studio name never appears
in repo filenames, alt text, or captions.
"""
import pathlib
import re
from PIL import Image

ROOT = pathlib.Path(__file__).parent
SRC = ROOT.parent / "sources" / "photo" / "picks"
OUT = ROOT / "img" / "work"

CROP_BOTTOM = {"photo-042.jpg": 0.925, "photo-060.jpg": 0.925}

# sub-case groups by imported photo number
FACES = [5, 6, 7, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 28, 29,
         30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 44, 50, 51, 56,
         57, 65, 69, 70]
FIGURES = [1, 2, 3, 4, 8, 9, 25, 26, 27, 43, 45, 49, 52, 54, 55, 58, 59, 61,
           62, 63, 66, 67, 71, 73, 74, 75, 76, 77, 78]
STAGE = [10, 11, 46, 47, 48, 53, 64, 68, 72, 79, 80, 81, 82]
POSTERS = ["valentine", "adopt-an-area", "art-of-the-cocktail", "documentary-night",
           "may-poster", "monday-brunch", "osu-v-michigan-party",
           "posh-the-halls-porch-doors1", "rise-and-shine-breakfast",
           "sipandsketch2", "terrarium-final", "visioning-flyer", "wine-down"]


def prep(src: pathlib.Path, dst: pathlib.Path, max_w=1600, crop=None) -> None:
    im = Image.open(src).convert("RGB")
    if crop:
        im = im.crop((0, 0, im.width, int(im.height * crop)))
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "JPEG", quality=82, optimize=True)


def prep_all() -> None:
    for p in sorted((SRC / "photo").glob("photo-*")):
        prep(p, OUT / "photo" / (p.stem + ".jpg"), max_w=1400,
             crop=CROP_BOTTOM.get(p.name))
    for i, p in enumerate(sorted((SRC / "flatstate").glob("*")), 1):
        prep(p, OUT / "photo" / f"fs-{i:02d}.jpg", max_w=1400)
    for name in POSTERS:
        prep(SRC / "design" / f"{name}.jpg", OUT / "posters" / f"{name}.jpg")
    # design artifacts routed to existing sections
    for name, dst in [
        ("fb-nonfan", "skreened/20-campaign-banner.jpg"),
        ("hoiday-hop-flyers", "skreened/21-popup-flyer.jpg"),
        ("skreened-logo-sticker", "skreened/22-sticker.jpg"),
        ("staycation1-web-banner", "skreened/23-merch-banner.jpg"),
        ("slideshow_1", "skreened/24-artist-lockup.jpg"),
        ("ryan_front", "earlier/04-clipcake-card.jpg"),
        ("shared-back", "earlier/05-clipcake-back.jpg"),
        ("standard-template", "earlier/06-clipcake-web.jpg"),
    ]:
        prep(SRC / "design" / f"{name}.jpg", OUT / dst)


# deterministic scatter cycles: (col, span, dy_rem, z, d)
CYCLE = [(1, 3, 0, 2, 0.3), (5, 4, 2, 1, 0.55), (10, 3, -1, 3, 0.7),
         (2, 4, 3, 2, 0.4), (7, 3, -2, 1, 0.25), (10, 3, 2, 2, 0.6),
         (1, 3, 1, 1, 0.5), (4, 3, -1, 3, 0.75), (8, 4, 2, 2, 0.35),
         (3, 4, 2, 1, 0.65), (9, 3, -2, 2, 0.45), (1, 4, 1, 3, 0.2)]


def figures_html(files, alts, indent="      ") -> str:
    rows = []
    for i, (f, alt) in enumerate(zip(files, alts)):
        c, cs, dy, z, d = CYCLE[i % len(CYCLE)]
        rows.append(
            f'{indent}<figure style="--c:{c};--cs:{cs};--dy:{dy}rem;--z:{z};--d:{d}">\n'
            f'{indent}  <a class="shot" href="img/work/{f}"><span class="frame"><img src="img/work/{f}" alt="{alt}" loading="lazy"></span></a>\n'
            f'{indent}</figure>')
    return "\n".join(rows)


def emit() -> None:
    posters_figs = figures_html([f"posters/{n}.jpg" for n in POSTERS],
                                ["Event poster" for _ in POSTERS])
    posters = f"""<section class="case case--posters">
  <div class="shell">
    <header class="case-head">
      <h2>Clubhouse posters</h2>
      <p class="case-meta">Residential community · Event series · Print</p>
      <p class="case-note">A year of events for a residential community, every poster designed from scratch: brunches, tastings, tailgates, sketch nights, a terrarium build. The work was making a calendar feel like a place.</p>
    </header>
    <div class="grid">
      <figure class="ghost" aria-hidden="true" style="--gx:20%;--gy:8%;--gw:58%;--d:0.09">
        <img src="img/work/posters/wine-down.jpg" alt="" loading="lazy">
      </figure>
{posters_figs}
    </div>
  </div>
</section>
"""
    (ROOT / "_src/pages/index/sections/05-posters.html").write_text(posters)

    def sub(title, note, nums, prefix="photo-"):
        files = [f"photo/{prefix}{n:03d}.jpg" for n in nums] if prefix == "photo-" \
            else [f"photo/fs-{n:02d}.jpg" for n in nums]
        alts = ["Portrait photograph" for _ in nums]
        return f"""    <div class="sub-case">
      <header class="case-head">
        <h3>{title}</h3>
        <p class="case-note">{note}</p>
      </header>
      <div class="grid">
{figures_html(files, alts)}
      </div>
    </div>"""

    photography = f"""<section class="case case--photo">
  <div class="shell">
    <header class="case-head">
      <h2>Photography</h2>
      <p class="case-meta">Portraits · Series · Places</p>
      <p class="case-note">A portrait practice ran alongside the design work: business walls, artists and their records, dancers, the occasional wedding. Shot, edited, and finished by me, start to end.</p>
    </header>
    <div class="grid">
      <figure class="ghost" aria-hidden="true" style="--gx:16%;--gy:4%;--gw:60%;--d:0.08">
        <img src="img/work/photo/fs-11.jpg" alt="" loading="lazy">
      </figure>
{figures_html([f"photo/photo-{n:03d}.jpg" for n in FIGURES], ["Photograph" for _ in FIGURES])}
    </div>
{sub("Faces", "The headshot wall: owners, makers, and performers, most of them laughing before the third frame.", FACES)}
{sub("The Flat State series", "A standing studio portrait series, one subject at a time.", list(range(1, 16)), prefix="fs-")}
{sub("Stage and sound", "Musicians at work: studios, stages, windows, and the hour after the set.", STAGE)}
  </div>
</section>
"""
    (ROOT / "_src/pages/index/sections/07b-photography.html").write_text(photography)
    print("emitted 05-posters.html, 07b-photography.html")


if __name__ == "__main__":
    prep_all()
    emit()
    n = len(list((OUT / "photo").glob("*.jpg"))) + len(list((OUT / "posters").glob("*.jpg")))
    print(f"prepped {n} photo/poster assets")
