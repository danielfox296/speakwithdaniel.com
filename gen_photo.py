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
# Daniel's cull, 2026-08-13: 71 keepers of the original 109.
# photo-039 dropped 2026-08-13: same negative as the Flat State comp shipping
# as fs-04 (camera frame 7718 imported twice); the series treatment stays.
FACES = [13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 28, 29, 31, 32, 33, 37,
         42, 44, 51, 56, 65, 70]
FIGURES = [1, 3, 8, 26, 27, 43, 45, 49, 52, 54, 58, 59, 62, 63, 67, 73, 74,
           75, 77, 78]
STAGE = [10, 11, 46, 47, 48, 64, 68, 72, 79, 81]
FLATSTATE = [4, 7, 8, 9, 12, 14, 15]
POSTERS = ["valentine", "adopt-an-area", "art-of-the-cocktail", "documentary-night",
           "monday-brunch", "posh-the-halls-porch-doors1", "rise-and-shine-breakfast",
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
    kept = set(FACES + FIGURES + STAGE)
    for p in sorted((SRC / "photo").glob("photo-*")):
        if int(p.stem.split("-")[1]) not in kept:
            continue  # culled 2026-08-13; source stays staged, repo stays lean
        prep(p, OUT / "photo" / (p.stem + ".jpg"), max_w=1400,
             crop=CROP_BOTTOM.get(p.name))
    for i, p in enumerate(sorted((SRC / "flatstate").glob("*")), 1):
        if i in FLATSTATE:
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


# Seeded scatter (2026-08-13, replacing fixed cycles): repeating cycles kept
# landing tiles flush on shared grid lines, which read as accidental alignment.
# Each tile now draws column, span, stagger, and sub-column jitter (--jx) from
# a seeded PRNG, with rejection rules so no tile repeats a left or right edge
# seen among its recent neighbors. Deterministic per (seed, count).
import random


def scatter(n, seed, spans, giant_min=None, giant_gap=5):
    # pixel model at the canonical 1120px container: 12 tracks, 20px gaps
    PITCH, GAP, REM = 90.8, 20, 16
    rng = random.Random(seed)
    out, lefts, rights, dys = [], [], [], []
    since_giant = giant_gap  # allow an early giant
    for i in range(n):
        for _ in range(80):
            if giant_min and since_giant >= giant_gap:
                cs = rng.choice([s for s in spans if s >= giant_min])
            else:
                cs = rng.choice(spans)
            c = rng.randint(1, 13 - cs)
            dy = round(rng.uniform(-3, 7), 1)
            jx = round(rng.uniform(-3.5, 3.5), 1)
            px_l = (c - 1) * PITCH + jx * REM
            px_r = px_l + cs * PITCH - GAP
            if any(abs(px_l - p) < 10 for p in lefts[-5:]):
                continue
            if any(abs(px_r - p) < 10 for p in rights[-5:]):
                continue
            if any(abs(dy - p) < 1.2 for p in dys[-3:]):
                continue
            break
        px_l = (c - 1) * PITCH + jx * REM
        lefts.append(px_l); rights.append(px_l + cs * PITCH - GAP); dys.append(dy)
        if giant_min and cs >= giant_min:
            since_giant = 0
        else:
            since_giant += 1
        z = rng.randint(1, 4)
        d = round(rng.uniform(0.2, 0.85), 2)
        out.append((c, cs, dy, jx, z, d))
    return out


def frame_class(f: str) -> str:
    try:
        with Image.open(OUT / f.replace("img/work/", "").replace("photo/", "photo/", 1)) as im:
            w, h = im.size
    except Exception:
        return "frame"
    if h > w * 1.15:
        return "frame tall"
    if w > h * 1.4:
        return "frame wide"
    return "frame"


def figures_html(files, alts, places, indent="      ") -> str:
    rows = []
    for (f, alt), (c, cs, dy, jx, z, d) in zip(zip(files, alts), places):
        fc = frame_class(f)
        rows.append(
            f'{indent}<figure style="--c:{c};--cs:{cs};--dy:{dy}rem;--jx:{jx}rem;--z:{z};--d:{d}">\n'
            f'{indent}  <a class="shot" href="img/work/{f}"><span class="{fc}"><img src="img/work/{f}" alt="{alt}" loading="lazy"></span></a>\n'
            f'{indent}</figure>')
    return "\n".join(rows)


def emit() -> None:
    posters_figs = figures_html([f"posters/{n}.jpg" for n in POSTERS],
                                ["Event poster" for _ in POSTERS],
                                scatter(len(POSTERS), seed=41, spans=[3, 3, 4, 4, 5, 6]))
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

    all_photos = ([f"photo/photo-{n:03d}.jpg" for n in FIGURES]
                  + [f"photo/photo-{n:03d}.jpg" for n in FACES]
                  + [f"photo/fs-{n:02d}.jpg" for n in FLATSTATE]
                  + [f"photo/photo-{n:03d}.jpg" for n in STAGE])
    photography = f"""<section class="case case--photo">
  <div class="shell">
    <header class="case-head">
      <h2>Photography</h2>
      <p class="case-meta">Portraits · Series · Places</p>
      <p class="case-note">A portrait practice ran alongside the design work: business walls, artists and their records, dancers, the occasional wedding. Shot, edited, and finished by me, start to end.</p>
    </header>
    <div class="grid">
      <figure class="ghost" aria-hidden="true" style="--gx:16%;--gy:3%;--gw:60%;--d:0.08">
        <img src="img/work/photo/fs-12.jpg" alt="" loading="lazy">
      </figure>
      <figure class="ghost" aria-hidden="true" style="--gx:30%;--gy:55%;--gw:55%;--d:0.11">
        <img src="img/work/photo/photo-075.jpg" alt="" loading="lazy">
      </figure>
{figures_html(all_photos, ["Photograph" for _ in all_photos], scatter(len(all_photos), seed=7, spans=[2, 2, 3, 3, 3, 4, 4, 6, 7, 8], giant_min=6, giant_gap=5))}
    </div>
  </div>
</section>
"""
    (ROOT / "_src/pages/index/sections/08b-photography.html").write_text(photography)
    print("emitted 05-posters.html, 07b-photography.html")


if __name__ == "__main__":
    prep_all()
    emit()
    n = len(list((OUT / "photo").glob("*.jpg"))) + len(list((OUT / "posters").glob("*.jpg")))
    print(f"prepped {n} photo/poster assets")
