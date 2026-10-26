#!/usr/bin/env python3
"""Generator wielojęzycznej strony Basket+ (czysty Python 3, stdlib).

    python3 src/build.py            # buduje do korzenia repo
    python3 src/build.py --out DIR  # buduje do innego katalogu (testy)
    python3 src/build.py --i18n DIR # inny katalog z tłumaczeniami (testy)

Wejście:  i18n/<kod>.json  +  src/templates/*.html  +  (opcjonalnie) site-screens/<kod>/*.jpg
Wyjście:  index.html (pl), <kod>/index.html (pozostałe), en.html i cz/index.html (przekierowania),
          sitemap.xml, assets/screens/<kod>/* (kopie zrzutów + warianty AVIF/WebP).
Polskie strony support*.html i privacy.html są ręczne – build ich nie zmienia (tylko je mapuje w sitemapie).
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tmpl  # noqa: E402

try:
    import images  # noqa: E402
except Exception:  # pragma: no cover
    images = None

ROOT = os.path.dirname(HERE)
SITE = "https://basketplus.app"
STORE_URL = "https://apps.apple.com/app/id6816518437"
EMAIL = "hello@basketplus.app"
DEFAULT_LANG = "pl"
X_DEFAULT_LANG = "en"
ORDER = "pl en bg hr cs da nl et fi fr de el hu ga it lv lt mt pt ro sk sl es sv".split()
SCREEN_NAMES = ["dashboard-real", "event-organization", "list-chat", "list-detail", "receipt-history", "reports-6m"]
DEFAULT_SCREENS_SRC = "/Users/jacekwodecki/Desktop/Basket+/site-screens"
# stare / alternatywne adresy -> język docelowy
ALIASES = {"cz": "cs"}
STATIC_PAGES = {
    "support": "/support.html",
    "support_en": "/support-en.html",
    "privacy": "/privacy.html",
}

APPLE_LOGO = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M16.7 12.9c0-2.6 2.1-3.9 2.2-4-1.2-1.8-3.1-2-3.8-2-1.6-.2-3.2 1-4 1-.9 0-2.3-1-3.7-1-1.9 0-3.6 1.1-4.6 2.8-2 3.4-.5 8.4 1.4 11.2.9 1.4 2 2.9 3.5 2.8 1.4-.1 1.9-.9 3.7-.9 1.7 0 2.2.9 3.7.9 1.5 0 2.5-1.4 3.4-2.7 1.1-1.6 1.5-3.1 1.5-3.2-.1 0-3.3-1.3-3.3-4.9ZM14.1 5.2c.8-1 1.4-2.4 1.2-3.7-1.2.1-2.7.8-3.6 1.8-.8.9-1.5 2.3-1.3 3.6 1.4.1 2.8-.7 3.7-1.7Z"/></svg>')

# nazwa zrzutu -> (klucz z alt-em, atrybut sizes, czy ładować od razu)
PICTURES = {
    "hero": ("dashboard-real", "hero.alt", "(max-width: 620px) 58vw, 300px", True),
    "lists": ("list-detail", "lists.alt", "(max-width: 620px) 55vw, 280px", False),
    "sharing": ("list-chat", "sharing.alt", "(max-width: 620px) 55vw, 280px", False),
    "events": ("event-organization", "events.alt", "(max-width: 620px) 55vw, 280px", False),
    "report": ("reports-6m", "analytics.alt_report", "(max-width: 620px) 45vw, 300px", False),
    "receipts": ("receipt-history", "analytics.alt_receipts", "(max-width: 620px) 38vw, 250px", False),
}


def get_path(d, path):
    for p in path.split("."):
        d = d[p]
    return d


def lang_url(code):
    return "/" if code == DEFAULT_LANG else "/%s/" % code


def lang_out_path(code):
    return "index.html" if code == DEFAULT_LANG else os.path.join(code, "index.html")


def load_langs(i18n_dir):
    langs = {}
    for fn in os.listdir(i18n_dir):
        if fn.endswith(".json") and not fn.startswith("_"):
            code = fn[:-5]
            with open(os.path.join(i18n_dir, fn), encoding="utf-8") as f:
                langs[code] = json.load(f)
            langs[code]["meta"]["code"] = code
    codes = sorted(langs, key=lambda c: (ORDER.index(c) if c in ORDER else 999, c))
    return codes, langs


def jpeg_size(path):
    with open(path, "rb") as f:
        data = f.read()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    raise ValueError("nie znaleziono rozmiaru JPEG: " + path)


class Builder:
    def __init__(self, out, i18n_dir, screens_src):
        self.out = out
        self.i18n_dir = i18n_dir
        self.screens_src = screens_src
        self.codes, self.langs = load_langs(i18n_dir)
        if DEFAULT_LANG not in self.langs:
            raise SystemExit("Brak i18n/%s.json (język domyślny)" % DEFAULT_LANG)
        self.home = {
            "home": open(os.path.join(HERE, "templates", "home.html"), encoding="utf-8").read(),
            "redirect": open(os.path.join(HERE, "templates", "redirect.html"), encoding="utf-8").read(),
        }
        with open(os.path.join(ROOT, "style.css"), "rb") as f:
            self.css_version = hashlib.sha1(f.read()).hexdigest()[:8]
        self.written = []

    # ---- pliki ----
    def write(self, rel, text):
        path = os.path.join(self.out, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                if f.read() == text:
                    return
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        self.written.append(rel)

    # ---- zrzuty ----
    def screens_base(self, code):
        """Zwraca (url_bazowy, ścieżka_pliku) dla każdej nazwy zrzutu dla danego języka."""
        res = {}
        assets = os.path.join(self.out, "assets", "screens")
        if code == "pl":
            return {n: ("/assets/screens/%s" % n, os.path.join(assets, n + ".jpg")) for n in SCREEN_NAMES}
        if code == "en":
            return {n: ("/assets/screens/%s-en" % n, os.path.join(assets, n + "-en.jpg")) for n in SCREEN_NAMES}
        src = os.path.join(self.screens_src, code)
        have = os.path.isdir(src) and all(os.path.exists(os.path.join(src, n + ".jpg")) for n in SCREEN_NAMES)
        if not have:
            return self.screens_base("en")
        dst = os.path.join(assets, code)
        os.makedirs(dst, exist_ok=True)
        for n in SCREEN_NAMES:
            a, b = os.path.join(src, n + ".jpg"), os.path.join(dst, n + ".jpg")
            if not os.path.exists(b) or open(a, "rb").read() != open(b, "rb").read():
                shutil.copyfile(a, b)
            res[n] = ("/assets/screens/%s/%s" % (code, n), b)
        return res

    def picture(self, base, jpg, alt, sizes, eager):
        w, h = jpeg_size(jpg)
        if images and images.available():
            if not images.variants_exist(jpg):
                images.make_variants(jpg)
        attrs = 'width="%d" height="%d" alt="%s" sizes="%s"' % (w, h, tmpl.esc(alt), sizes)
        attrs += ' fetchpriority="high" decoding="async"' if eager else ' loading="lazy" decoding="async"'
        if images and images.variants_exist(jpg):
            def ss(ext):
                return "%s-276.%s 276w, %s-552.%s 552w" % (base, ext, base, ext)
            jpg_ss = "%s-276.jpg 276w, %s.jpg 552w" % (base, base)
            return ('<picture><source type="image/avif" srcset="%s" sizes="%s">'
                    '<source type="image/webp" srcset="%s" sizes="%s">'
                    '<img src="%s.jpg" srcset="%s" %s></picture>') % (ss("avif"), sizes, ss("webp"), sizes, base, jpg_ss, attrs)
        return '<img src="%s.jpg" %s>' % (base, attrs)

    # ---- kontekst strony ----
    def lastmod(self, paths):
        """Data ostatniej zmiany: z gita (commit), a dla niezacommitowanych zmian - dziś."""
        try:
            rel = [os.path.relpath(p, ROOT) for p in paths if os.path.exists(p)]
            dirty = subprocess.run(["git", "status", "--porcelain", "--"] + rel, cwd=ROOT, capture_output=True, text=True).stdout.strip()
            if dirty:
                return datetime.date.today().isoformat()
            r = subprocess.run(["git", "log", "-1", "--format=%cs", "--"] + rel, cwd=ROOT, capture_output=True, text=True).stdout.strip()
            if r:
                return r
        except Exception:
            pass
        return datetime.date.today().isoformat()

    def page_ctx(self, code):
        t = json.loads(json.dumps(self.langs[code]))  # kopia
        meta = t["meta"]
        canonical = SITE + lang_url(code)
        mail_notify = "mailto:%s?subject=%s&body=%s" % (
            EMAIL,
            urlquote(t["availability"]["mail_subject"]),
            urlquote(t["availability"]["mail_body"]))
        support = "/support.html" if code == "pl" else "/support-en.html"
        privacy = "/privacy.html" if code == "pl" else "/privacy.html#en"
        langs = [{
            "code": c, "url": lang_url(c), "native_name": self.langs[c]["meta"]["native_name"],
            "html_lang": self.langs[c]["meta"]["html_lang"], "hreflang": self.langs[c]["meta"]["hreflang"],
            "current": c == code,
        } for c in self.codes]
        alternates = [{"hreflang": self.langs[c]["meta"]["hreflang"], "url": SITE + lang_url(c)} for c in self.codes]
        xdef = X_DEFAULT_LANG if X_DEFAULT_LANG in self.langs else DEFAULT_LANG
        links = {
            "support": support, "privacy": privacy, "email": "mailto:" + EMAIL,
            "notify": tmpl.esc(mail_notify), "icloud": "#icloud", "plans": "#plus",
        }
        # <a href> w rich() jest już wstawiane jako gotowy HTML, więc notify ma zescapowane &.
        sb = self.screens_base(code)
        pic = {}
        for key, (name, altkey, sizes, eager) in PICTURES.items():
            base, jpg = sb[name]
            pic[key] = self.picture(base, jpg, get_path(t, altkey), sizes, eager)
        ctx = dict(t)
        ctx["links"] = links
        ctx["page"] = {
            "canonical": canonical, "home_url": lang_url(code), "alternates": alternates,
            "x_default": SITE + lang_url(xdef),
            "og_alternates": [self.langs[c]["meta"]["og_locale"] for c in self.codes if c != code],
            "og_image": SITE + "/assets/og-image.jpg", "css_version": self.css_version,
            "jsonld": jsonld(t, canonical, code, links),
            "langs": langs, "store_url": STORE_URL, "apple_logo": APPLE_LOGO,
            "support_url": support, "privacy_url": privacy,
            "support_foreign": code not in ("pl", "en"), "show_docs_note": code not in ("pl", "en"),
            "mail_notify": mail_notify, "pic": pic,
        }
        return ctx

    def build_langs(self):
        for code in self.codes:
            html_out = tmpl.render(self.home["home"], self.page_ctx(code))
            self.write(lang_out_path(code), html_out)

    def redirect(self, rel, target_code, noindex, lang):
        target_path = lang_url(target_code)
        ctx = {"page": {"lang": lang, "target": SITE + target_path, "target_path": target_path, "noindex": noindex}, "links": {}}
        self.write(rel, tmpl.render(self.home["redirect"], ctx))

    def build_redirects(self):
        if "en" in self.langs:
            self.redirect("en.html", "en", False, "en")
        for alias, target in ALIASES.items():
            if target in self.langs:
                self.redirect(os.path.join(alias, "index.html"), target, True, target)
            else:
                print("UWAGA: pomijam /%s/ (brak i18n/%s.json) - przekierowanie powstanie po dodaniu języka." % (alias, target))

    def build_sitemap(self):
        tpl_files = [os.path.join(HERE, "templates", "home.html"), os.path.join(ROOT, "style.css"), os.path.join(HERE, "build.py")]
        urls = []
        for code in self.codes:
            lm = self.lastmod([os.path.join(self.i18n_dir, code + ".json")] + tpl_files)
            alts = [(self.langs[c]["meta"]["hreflang"], SITE + lang_url(c)) for c in self.codes]
            xdef = X_DEFAULT_LANG if X_DEFAULT_LANG in self.langs else DEFAULT_LANG
            alts.append(("x-default", SITE + lang_url(xdef)))
            urls.append((SITE + lang_url(code), lm, alts))
        sup_alts = [("pl", SITE + "/support.html"), ("en", SITE + "/support-en.html"), ("x-default", SITE + "/support-en.html")]
        for fn, alts in (("support.html", sup_alts), ("support-en.html", sup_alts), ("privacy.html", [])):
            urls.append((SITE + "/" + fn, self.lastmod([os.path.join(ROOT, fn)]), alts))
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
        for loc, lm, alts in urls:
            lines.append("  <url>")
            lines.append("    <loc>%s</loc>" % loc)
            lines.append("    <lastmod>%s</lastmod>" % lm)
            for hl, href in alts:
                lines.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (hl, href))
            lines.append("  </url>")
        lines.append("</urlset>")
        self.write("sitemap.xml", "\n".join(lines) + "\n")

    def run(self):
        self.build_langs()
        self.build_redirects()
        self.build_sitemap()
        print("Zbudowano %d języków (%s); zmienione pliki: %d" % (len(self.codes), ", ".join(self.codes), len(self.written)))
        for w in self.written:
            print("  ", w)


def urlquote(s):
    from urllib.parse import quote
    return quote(s, safe="")


def plain(text):
    """Tekst bez mini-znaczników - do JSON-LD (musi odpowiadać widocznej treści)."""
    text = re.sub(r"\[\[(.+?)\|[a-z_]+\]\]", r"\1", text)
    return re.sub(r"\*+", "", text)


def jsonld(t, canonical, code, links):
    meta = t["meta"]
    graph = [
        {
            "@type": "SoftwareApplication",
            "@id": canonical + "#app",
            "name": "Basket+",
            "description": t["seo"]["app_description"],
            "applicationCategory": "ShoppingApplication",
            "operatingSystem": "iOS",
            "url": canonical,
            "image": SITE + "/assets/app-icon.png",
            "downloadUrl": STORE_URL,
            "softwareHelp": SITE + links["support"],
            "inLanguage": meta["html_lang"],
        },
        {
            "@type": "FAQPage",
            "@id": canonical + "#faq",
            "inLanguage": meta["html_lang"],
            "mainEntity": [
                {"@type": "Question", "name": it["q"], "acceptedAnswer": {"@type": "Answer", "text": plain(it["a"])}}
                for it in t["faq"]["items"]
            ],
        },
    ]
    data = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(data, ensure_ascii=False, indent=2).replace("<", "\\u003c")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=ROOT)
    ap.add_argument("--i18n", default=os.path.join(ROOT, "i18n"))
    ap.add_argument("--screens-src", default=os.environ.get("BASKET_SCREENS_SRC", DEFAULT_SCREENS_SRC))
    a = ap.parse_args()
    if a.out != ROOT:
        # wersja testowa: skopiuj statyczne zasoby, żeby wynik dało się serwować
        os.makedirs(a.out, exist_ok=True)
        for item in ("assets", "style.css", "site.webmanifest", "robots.txt", "support.html", "support-en.html", "privacy.html"):
            s, d = os.path.join(ROOT, item), os.path.join(a.out, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            elif os.path.exists(s):
                shutil.copyfile(s, d)
    Builder(a.out, a.i18n, a.screens_src).run()


if __name__ == "__main__":
    main()
