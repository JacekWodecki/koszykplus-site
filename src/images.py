"""Warianty responsywne zrzutów ekranu (opcjonalne; wymaga Pillow z WebP/AVIF).

Dla każdego `x.jpg` (552 px szer.) powstają: x-276.jpg, x-276.webp, x-552.webp, x-276.avif, x-552.avif.
`x.jpg` zostaje oryginałem i fallbackiem. Bez Pillow strona nadal działa (sam JPG, bez <picture>).
Uruchamiane automatycznie przez build.py; ponowne uruchomienie jest idempotentne (pomija aktualne pliki).
"""
import os

WIDTHS = (276, 552)
FORMATS = ("avif", "webp")


def available():
    try:
        from PIL import features
    except ImportError:
        return False
    return features.check("webp") and features.check("avif")


def variant_path(jpg_path, width, ext):
    return "%s-%d.%s" % (jpg_path[:-4], width, ext)


def make_variants(jpg_path):
    from PIL import Image
    src_mtime = os.path.getmtime(jpg_path)
    img = Image.open(jpg_path).convert("RGB")
    w0, h0 = img.size
    for width in WIDTHS:
        scaled = img if width >= w0 else img.resize((width, round(h0 * width / w0)), Image.LANCZOS)
        targets = [("webp", dict(quality=80, method=6)), ("avif", dict(quality=55, speed=4))]
        if width < w0:
            targets.append(("jpg", dict(quality=80, optimize=True, progressive=True)))
        for ext, opts in targets:
            out = variant_path(jpg_path, width, ext)
            if os.path.exists(out) and os.path.getmtime(out) >= src_mtime:
                continue
            scaled.save(out, {"jpg": "JPEG", "webp": "WEBP", "avif": "AVIF"}[ext], **opts)


def variants_exist(jpg_path):
    need = [variant_path(jpg_path, w, e) for w in WIDTHS for e in FORMATS]
    need.append(variant_path(jpg_path, WIDTHS[0], "jpg"))
    return all(os.path.exists(p) for p in need)


if __name__ == "__main__":
    import glob
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not available():
        raise SystemExit("Brak Pillow z obsługą WebP/AVIF - pomijam.")
    for p in sorted(glob.glob(os.path.join(root, "assets", "screens", "**", "*.jpg"), recursive=True)):
        if re.search(r"-\d+\.jpg$", p):
            continue
        make_variants(p)
        print("ok", os.path.relpath(p, root))
