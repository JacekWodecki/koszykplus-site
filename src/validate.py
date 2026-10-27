#!/usr/bin/env python3
"""Walidator strony Basket+ (stdlib). Kod wyjścia != 0 przy jakimkolwiek błędzie.

    python3 src/build.py && python3 src/validate.py
    python3 src/validate.py --write-schema-doc   # odświeża i18n/SCHEMA.md z i18n/_schema.json
    python3 src/validate.py --skip-fresh         # bez porównania z czystym buildem

Sprawdza: komplet i typy kluczy we wszystkich i18n/*.json względem pl.json, limity długości (title <= 60,
description <= 160 i pozostałe z i18n/_schema.json), znaczniki [[link|nazwa]] / *akcent*, brak pustych tekstów,
unikalność title/description, a w wygenerowanych stronach: <html lang>, jedno H1, canonical, wzajemne hreflang
(+ x-default), linki wewnętrzne i kotwice, alt/width/height obrazów, poprawność JSON-LD i zgodność FAQPage
z widoczną treścią, sitemap.xml (komplet, alternates, brak przekierowań/noindex) oraz aktualność wyniku buildu.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build  # noqa: E402

ROOT = build.ROOT
SITE = build.SITE
errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


# ---------- płaskie klucze ----------
def flatten(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, prefix + k + "."))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(flatten(v, prefix + str(i) + "."))
    else:
        out[prefix[:-1]] = d
    return out


def schema_for(path, schema):
    generic = re.sub(r"\.\d+(?=\.|$)", ".*", path)
    return schema.get(generic)


LINK_TOK = re.compile(r"\[\[.+?\|([a-z_]+)\]\]")


def tokens(text):
    return sorted(LINK_TOK.findall(text)), text.count("*") // 2, text.count("\n")


# ---------- i18n ----------
def check_i18n(i18n_dir):
    schema = json.load(open(os.path.join(i18n_dir, "_schema.json"), encoding="utf-8"))
    codes, langs = build.load_langs(i18n_dir)
    ref = flatten(langs[build.DEFAULT_LANG])
    # każdy klucz referencyjny ma wpis w schemacie
    for key in ref:
        if key.startswith("meta.code"):
            continue
        if schema_for(key, schema) is None:
            err("schemat: brak opisu klucza %s w i18n/_schema.json" % key)
    titles, descs = {}, {}
    for code in codes:
        flat = flatten(langs[code])
        flat.pop("meta.code", None)
        refk = {k: v for k, v in ref.items() if k != "meta.code"}
        for key in refk:
            if key.startswith("availability.") and not build.AVAILABILITY_NOTICE:
                continue
            if key not in flat:
                err("%s: brak klucza %s" % (code, key))
        for key in flat:
            if key not in refk:
                err("%s: nadmiarowy klucz %s" % (code, key))
        for key, val in flat.items():
            if key not in refk:
                continue
            if type(val) is not type(refk[key]):
                err("%s: zły typ w %s" % (code, key))
                continue
            if not isinstance(val, str):
                err("%s: %s nie jest tekstem" % (code, key))
                continue
            if not val.strip():
                err("%s: pusty tekst %s" % (code, key))
                continue
            sc = schema_for(key, schema) or {}
            if "max" in sc and len(val) > sc["max"]:
                err("%s: %s ma %d znaków (limit %d)" % (code, key, len(val), sc["max"]))
            if code != build.DEFAULT_LANG and not key.startswith("meta.") and tokens(val)[:2] != tokens(refk[key])[:2]:
                err("%s: %s ma inne znaczniki ([[link|nazwa]] / *akcent*) niż pl.json: %s vs %s" % (code, key, tokens(val)[:2], tokens(refk[key])[:2]))
            if sc.get("lines") and val.count("\n") != sc["lines"] - 1 and code != build.DEFAULT_LANG:
                warn("%s: %s powinien mieć %d linie (\\n)" % (code, key, sc["lines"]))
            if sc.get("markup") == "title" and key == "hero.title" and val.count("*") != 2:
                err("%s: hero.title wymaga dokładnie jednej pary *akcent*" % code)
            if re.search(r"\{\{|\{%|<[a-z/]", val):
                err("%s: %s zawiera znaczniki szablonu/HTML" % (code, key))
            if code != build.DEFAULT_LANG and code != "en" and val == refk[key] and len(val) >= 25 and not key.startswith("meta."):
                warn("%s: %s identyczny z pl.json (nieprzetłumaczone?)" % (code, key))
        meta = langs[code]["meta"]
        if meta["html_lang"] and not re.match(r"^[a-z]{2,3}(-[A-Z]{2})?$", meta["html_lang"]):
            err("%s: zły html_lang %r" % (code, meta["html_lang"]))
        if not re.match(r"^[a-z]{2,3}_[A-Z]{2}$", meta["og_locale"]):
            err("%s: zły og_locale %r" % (code, meta["og_locale"]))
        if code == "pt" and meta["hreflang"] != "pt-PT":
            err("pt: hreflang musi być pt-PT")
        if code != "pt" and meta["hreflang"] != code:
            err("%s: hreflang powinien być %s" % (code, code))
        t, d = langs[code]["seo"]["title"], langs[code]["seo"]["description"]
        if t in titles:
            err("%s: title identyczny jak w %s" % (code, titles[t]))
        if d in descs:
            err("%s: description identyczny jak w %s" % (code, descs[d]))
        titles[t], descs[d] = code, code
        if "Basket+" not in t:
            err("%s: title bez nazwy Basket+" % code)
        # przycisk App Store: aria-label zaczyna się od widocznego tekstu
        h = langs[code]["hero"]
        if not h["store_aria"].lower().startswith((h["store_small"] + " App Store").lower()):
            err("%s: hero.store_aria powinien zaczynać się od '%s App Store'" % (code, h["store_small"]))
        # cena nie może się pojawić
        for key, val in flat.items():
            if re.search(r"\d+[.,]\d{2}\s*(zł|PLN|€|EUR|\$|USD)|(€|\$)\s*\d", str(val)):
                err("%s: %s zawiera cenę (cena nie jest podawana na stronie)" % (code, key))
        # zakazane sformułowania o danych
        if re.search(r"(?i)prawdziw|\breal\b|authentic", langs[code]["analytics"]["caption_note"]) and code in ("pl", "en"):
            err("%s: caption_note nie może twierdzić, że dane są prawdziwe" % code)
    return codes, langs


# ---------- HTML ----------
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.h = {}
        self.ids = set()
        self.links = []   # (tag, attr, url)
        self.imgs = []
        self.metas = []
        self.linkrels = []
        self.ld = []
        self.title = ""
        self.html_lang = None
        self._in = None
        self._buf = ""
        self.details = []
        self.summary_text = []
        self._stack = []
        self.faq_pairs = []
        self._cur_q = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if "id" in a:
            if a["id"] in self.ids:
                err_dups.append(a["id"])
            self.ids.add(a["id"])
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag in ("h1", "h2", "h3", "h4"):
            self.h[tag] = self.h.get(tag, 0) + 1
        if tag == "a" and "href" in a:
            self.links.append(("a", "href", a["href"]))
        if tag == "img":
            self.imgs.append(a)
            if "src" in a:
                self.links.append(("img", "src", a["src"]))
        if tag == "source" and "srcset" in a:
            for part in a["srcset"].split(","):
                self.links.append(("source", "srcset", part.strip().split()[0]))
        if tag == "img" and "srcset" in a:
            for part in a["srcset"].split(","):
                self.links.append(("img", "srcset", part.strip().split()[0]))
        if tag == "meta":
            self.metas.append(a)
        if tag == "link":
            self.linkrels.append(a)
            if a.get("rel") in ("stylesheet", "icon", "apple-touch-icon", "manifest"):
                self.links.append(("link", "href", a["href"]))
        if tag == "script":
            if a.get("type") == "application/ld+json":
                self._in, self._buf = "ld", ""
            elif "src" in a:
                self.links.append(("script", "src", a["src"]))
        if tag == "title":
            self._in, self._buf = "title", ""
        if tag == "summary":
            self._in, self._buf = "summary", ""
        if tag == "details":
            self._stack.append("details")
        if tag == "p" and self._stack and self._stack[-1] == "details" and self._cur_q is not None:
            self._in, self._buf = "answer", ""

    def handle_endtag(self, tag):
        if tag == "script" and self._in == "ld":
            self.ld.append(self._buf)
            self._in = None
        elif tag == "title" and self._in == "title":
            self.title = self._buf.strip()
            self._in = None
        elif tag == "summary" and self._in == "summary":
            self._cur_q = " ".join(self._buf.split())
            self._in = None
        elif tag == "p" and self._in == "answer":
            self.faq_pairs.append((self._cur_q, " ".join(self._buf.split())))
            self._cur_q = None
            self._in = None
        elif tag == "details" and self._stack:
            self._stack.pop()

    def handle_data(self, data):
        if self._in:
            self._buf += data


err_dups = []


def parse(path):
    p = Page()
    p.feed(open(path, encoding="utf-8").read())
    return p


def meta(p, key, attr="name"):
    for m in p.metas:
        if m.get(attr) == key:
            return m.get("content")
    return None


def resolve_local(url, base_dir):
    """Zwraca (ścieżka_pliku, kotwica) dla linku wewnętrznego lub None dla zewnętrznego."""
    if re.match(r"^(https?:|mailto:|tel:|data:)", url):
        if url.startswith(build.SITE):
            url = url[len(build.SITE):] or "/"
        else:
            return None
    url, _, frag = url.partition("#")
    url = url.split("?")[0]
    if url == "":
        return None if frag == "" else ("", frag)
    path = os.path.join(ROOT, url.lstrip("/")) if url.startswith("/") else os.path.join(base_dir, url)
    if os.path.isdir(path) or url.endswith("/"):
        path = os.path.join(path, "index.html")
    return path, frag


def check_pages(codes, langs):
    pages = {}
    for code in codes:
        rel = build.lang_out_path(code)
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            err("%s: brak wygenerowanej strony %s (uruchom src/build.py)" % (code, rel))
            continue
        err_dups.clear()
        p = parse(path)
        pages[code] = p
        if err_dups:
            err("%s: zdublowane id: %s" % (code, ", ".join(sorted(set(err_dups)))))
        L = langs[code]
        if p.html_lang != L["meta"]["html_lang"]:
            err("%s: <html lang>=%s" % (code, p.html_lang))
        if p.h.get("h1") != 1:
            err("%s: liczba H1 = %s (ma być 1)" % (code, p.h.get("h1")))
        if not p.h.get("h2"):
            err("%s: brak H2" % code)
        if p.title != L["seo"]["title"]:
            err("%s: <title> różni się od seo.title" % code)
        if meta(p, "description") != L["seo"]["description"]:
            err("%s: meta description różni się od seo.description" % code)
        robots = meta(p, "robots") or ""
        if "noindex" in robots:
            err("%s: strona ma noindex" % code)
        expected = SITE + build.lang_url(code)
        canon = [l["href"] for l in p.linkrels if l.get("rel") == "canonical"]
        if canon != [expected]:
            err("%s: canonical=%s (oczekiwano %s)" % (code, canon, expected))
        if meta(p, "og:url", "property") != expected:
            err("%s: og:url != canonical" % code)
        for prop in ("og:title", "og:description", "og:image", "og:locale", "og:type"):
            if not meta(p, prop, "property"):
                err("%s: brak %s" % (code, prop))
        for nm in ("twitter:card", "twitter:title", "twitter:description", "twitter:image"):
            if not meta(p, nm):
                err("%s: brak %s" % (code, nm))
        if meta(p, "og:locale", "property") != L["meta"]["og_locale"]:
            err("%s: og:locale" % code)
        # hreflang
        alts = {l["hreflang"]: l["href"] for l in p.linkrels if l.get("rel") == "alternate" and l.get("hreflang")}
        want = {langs[c]["meta"]["hreflang"]: SITE + build.lang_url(c) for c in codes}
        xdef = build.X_DEFAULT_LANG if build.X_DEFAULT_LANG in langs else build.DEFAULT_LANG
        want["x-default"] = SITE + build.lang_url(xdef)
        if alts != want:
            err("%s: hreflang niezgodny: %s" % (code, {k: (alts.get(k), want.get(k)) for k in set(alts) | set(want) if alts.get(k) != want.get(k)}))
        # obrazy
        for im in p.imgs:
            if "alt" not in im:
                err("%s: <img %s> bez atrybutu alt" % (code, im.get("src")))
            if not (im.get("width") and im.get("height")):
                err("%s: <img %s> bez width/height" % (code, im.get("src")))
            if im.get("alt") == "" and im.get("src", "").endswith(".jpg"):
                err("%s: zrzut %s ma pusty alt" % (code, im.get("src")))
        hero = [im for im in p.imgs if "dashboard-real" in im.get("src", "")]
        if not hero or hero[0].get("fetchpriority") != "high" or hero[0].get("loading") == "lazy":
            err("%s: obraz LCP (hero) powinien mieć fetchpriority=high i nie być lazy" % code)
        for im in p.imgs:
            if "dashboard-real" not in im.get("src", "") and im.get("src", "").endswith(".jpg") and im.get("loading") != "lazy":
                err("%s: obraz poniżej pierwszego ekranu bez loading=lazy: %s" % (code, im["src"]))
        # JSON-LD
        if len(p.ld) != 1:
            err("%s: oczekiwano 1 bloku JSON-LD, jest %d" % (code, len(p.ld)))
        else:
            try:
                data = json.loads(p.ld[0])
                types = [g.get("@type") for g in data.get("@graph", [])]
                if types != ["SoftwareApplication", "FAQPage"]:
                    err("%s: JSON-LD typy %s" % (code, types))
                app = data["@graph"][0]
                for k in ("name", "applicationCategory", "operatingSystem", "description", "url"):
                    if not app.get(k):
                        err("%s: SoftwareApplication bez %s" % (code, k))
                if any(k in app for k in ("offers", "aggregateRating", "review")):
                    err("%s: JSON-LD zawiera offers/ocenę (zakazane - nie wymyślamy)" % code)
                faq = data["@graph"][1]
                got = [(q["name"], q["acceptedAnswer"]["text"]) for q in faq["mainEntity"]]
                vis = p.faq_pairs
                if len(got) != len(vis):
                    err("%s: FAQPage ma %d pytań, strona %d" % (code, len(got), len(vis)))
                for (gq, ga), (vq, va) in zip(got, vis):
                    if gq != vq:
                        err("%s: FAQPage pytanie nie zgadza się z widocznym: %r" % (code, gq))
                    if " ".join(ga.split()) != va:
                        err("%s: FAQPage odpowiedź nie zgadza się z widoczną: %r" % (code, gq))
            except Exception as e:  # noqa: BLE001
                err("%s: niepoprawny JSON-LD: %s" % (code, e))
        # linki wewnętrzne
        base_dir = os.path.dirname(path)
        for tag, attr, url in p.links:
            r = resolve_local(url, base_dir)
            if r is None:
                continue
            target, frag = r
            if target == "":
                if frag and frag not in p.ids:
                    err("%s: kotwica #%s nie istnieje" % (code, frag))
                continue
            if not os.path.exists(target):
                err("%s: martwy link %s=%s" % (code, attr, url))
                continue
            if frag and target.endswith(".html"):
                tp = pages.get(code) if target == path else parse(target)
                if frag not in tp.ids and not (target.endswith("privacy.html")):
                    err("%s: brak kotwicy #%s w %s" % (code, frag, url))
        # język w przełączniku: lang na linkach
        for tag, attr, url in p.links:
            pass
    # wzajemność hreflang: zbiór alternatyw identyczny na każdej stronie i wskazuje self-canonical
    return pages


def check_redirects(codes, langs):
    if "en" in langs:
        p = parse(os.path.join(ROOT, "en.html"))
        canon = [l["href"] for l in p.linkrels if l.get("rel") == "canonical"]
        if canon != [SITE + "/en/"]:
            err("en.html: canonical powinien wskazywać /en/")
        if not any(m.get("http-equiv") == "refresh" and "/en/" in m.get("content", "") for m in p.metas):
            err("en.html: brak meta refresh -> /en/")
    if False:
        path = os.path.join(ROOT, "cz", "index.html")
        if not os.path.exists(path):
            err("brak cz/index.html (przekierowanie do /cs/)")
        else:
            p = parse(path)
            if [l["href"] for l in p.linkrels if l.get("rel") == "canonical"] != [SITE + "/cs/"]:
                err("cz/index.html: canonical powinien wskazywać /cs/")
            if "noindex" not in (meta(p, "robots") or ""):
                err("cz/index.html: brak noindex")


def check_sitemap(codes, langs):
    path = os.path.join(ROOT, "sitemap.xml")
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        err("sitemap.xml: niepoprawny XML: %s" % e)
        return
    urls = {}
    for u in tree.getroot().findall("s:url", ns):
        loc = u.find("s:loc", ns).text
        lm = u.find("s:lastmod", ns)
        if lm is None or not re.match(r"^\d{4}-\d{2}-\d{2}$", lm.text or ""):
            err("sitemap: %s bez poprawnego lastmod" % loc)
        urls[loc] = {a.get("hreflang"): a.get("href") for a in u.findall("x:link", ns)}
    for code in codes:
        loc = SITE + build.lang_url(code)
        if loc not in urls:
            err("sitemap: brak %s" % loc)
            continue
        want = {langs[c]["meta"]["hreflang"]: SITE + build.lang_url(c) for c in codes}
        xdef = build.X_DEFAULT_LANG if build.X_DEFAULT_LANG in langs else build.DEFAULT_LANG
        want["x-default"] = SITE + build.lang_url(xdef)
        if urls[loc] != want:
            err("sitemap: alternates dla %s niekompletne" % loc)
    for loc in urls:
        rel = loc[len(SITE):]
        target = os.path.join(ROOT, rel.lstrip("/"))
        if rel.endswith("/"):
            target = os.path.join(target, "index.html")
        if not os.path.exists(target):
            err("sitemap: %s nie istnieje w repo" % loc)
            continue
        txt = open(target, encoding="utf-8").read()
        if re.search(r'http-equiv="refresh"|name="robots" content="[^"]*noindex', txt):
            err("sitemap: %s to przekierowanie/noindex" % loc)
    for must in ("/support.html", "/support-en.html", "/privacy.html"):
        if SITE + must not in urls:
            err("sitemap: brak %s" % must)
    if not os.path.exists(os.path.join(ROOT, ".nojekyll")):
        err(".nojekyll: brak pliku (GitHub Pages uruchomi Jekylla, który psuje build na {{ w i18n/SCHEMA.md)")
    robots = open(os.path.join(ROOT, "robots.txt"), encoding="utf-8").read()
    if "Sitemap: %s/sitemap.xml" % SITE not in robots:
        err("robots.txt: brak linii Sitemap")
    # grupy robots.txt: blokada całości jest dozwolona tylko dla botów trenujących AI, nie dla "*", Googlebota ani Binga
    groups, agents, rules = [], [], []
    for line in robots.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if rules:
                groups.append((agents, rules)); agents, rules = [], []
            agents.append(v.lower())
        elif k in ("allow", "disallow"):
            rules.append((k, v))
    if agents:
        groups.append((agents, rules))
    for ags, rls in groups:
        if ("disallow", "/") in rls:
            for ok_bot in ("*", "googlebot", "bingbot", "applebot", "oai-searchbot", "chatgpt-user", "claude-searchbot", "claude-user", "perplexitybot", "duckassistbot"):
                if ok_bot in ags:
                    err("robots.txt: blokuje całą stronę dla %s" % ok_bot)
    if not any("*" in ags and ("allow", "/") in rls for ags, rls in groups):
        err("robots.txt: brak Allow: / dla *")


def check_fresh(i18n_dir):
    """Wynik builda w repo musi być zgodny z czystym buildem."""
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, os.path.join(HERE, "build.py"), "--out", tmp, "--i18n", i18n_dir], capture_output=True, text=True)
        if r.returncode != 0:
            err("build nie przechodzi: " + r.stderr[-400:])
            return
        for dp, _, fns in os.walk(tmp):
            for fn in fns:
                if fn.endswith(".html") or fn == "sitemap.xml":
                    rel = os.path.relpath(os.path.join(dp, fn), tmp)
                    if rel in ("support.html", "support-en.html", "privacy.html"):
                        continue
                    a = open(os.path.join(tmp, rel), encoding="utf-8").read()
                    b_path = os.path.join(ROOT, rel)
                    if not os.path.exists(b_path):
                        err("nieaktualny wynik: brak %s (uruchom src/build.py)" % rel)
                    elif a != open(b_path, encoding="utf-8").read():
                        err("nieaktualny wynik: %s różni się od czystego builda (uruchom src/build.py)" % rel)


def check_static_pages():
    for fn in ("support.html", "support-en.html"):
        p = parse(os.path.join(ROOT, fn))
        if p.h.get("h1") != 1:
            err("%s: liczba H1 != 1" % fn)
        base = os.path.dirname(os.path.join(ROOT, fn))
        for tag, attr, url in p.links:
            r = resolve_local(url, base)
            if r and r[0] and not os.path.exists(r[0]):
                err("%s: martwy link %s" % (fn, url))
            elif r and r[0].endswith(".html") and r[1] and not r[0].endswith("privacy.html"):
                t = parse(r[0])
                if r[1] not in t.ids:
                    err("%s: brak kotwicy %s" % (fn, url))
        if not any(l.get("rel") == "canonical" for l in p.linkrels):
            err("%s: brak canonical" % fn)


# ---------- dokumentacja schematu ----------
PHRASES = """## Słownik i wyrażenia wymagające szczególnej uwagi

Tłumacz naturalnym językiem (nie kalką z polskiego/angielskiego), konsekwentnie w całym pliku:

| Pojęcie | Zasada |
|---|---|
| Basket+, Basket+ Free, Basket+ Plus | nazwy własne – bez tłumaczenia i bez odmiany; „Plus” i „Free” zostają jak w nazwie planu |
| iCloud, CloudKit, App Store, Apple Watch, iPhone, iPad, CarPlay, Google AdMob | nazwy własne – bez tłumaczenia; odmieniaj tylko jeśli język tego wymaga (np. fiński: iCloudissa) |
| „wspólna lista” / „udostępnianie” | używaj terminologii z aplikacji i systemu Apple w danym języku (shared list / Share) |
| „wydarzenie” (Events) | funkcja Plus: grupowanie list wokół jednego zdarzenia (wyjazd, impreza), NIE „wydarzenie kalendarza” |
| „rozliczanie wydatków” | dzielenie kosztów i zwroty między osobami (settling up), nie „księgowość” |
| „reklamy natywne” | reklamy dopasowane wyglądem do aplikacji (native ads), nie „banery” |
| „zgoda na śledzenie” | systemowe pytanie Apple (App Tracking Transparency) – użyj oficjalnego tłumaczenia Apple |
| „EOG” | Europejski Obszar Gospodarczy (EEA) |
| „konto Apple” | Apple Account – użyj aktualnej nazwy Apple w danym języku |

Szczególnie uważaj na (błędne tłumaczenie zmieniłoby fakty prawne/produktowe):
- `plans.ads_items.*` i `faq.items.5.a` – opis reklam: personalizacja wyłączona, ale **nie** „brak identyfikatorów”; zgoda tam, gdzie wymaga prawa; w Plus brak reklam;
- `plans.group_rows.*.result` i `icloud.cards.*.text` – kto potrzebuje Plus i iCloud (każdy uczestnik wydarzenia ma **własny** Plus; zwykła lista działa w Free);
- `plans.price_note`, `faq.items.6.a` – bez kwot; cena i okres próbny są w aplikacji/App Store;
- `analytics.caption_note` – dane na zrzutach to **przykłady**, nie „prawdziwe dane”;
- `hero.title`, `*.title` – gra słów/rytm: nie tłumacz dosłownie, oddaj sens „zakupy układają się same” i „mniej stukania, więcej kupowania”;
- `trust.items.*` – „bez konta Basket+” (nie „bez konta w ogóle” – iCloud/Apple Account jest używane do synchronizacji).

## Frazy dla tłumaczy (SEO)

Teksty mają brzmieć naturalnie w danym języku, ale **title, description, hero.lead, lists.text, sharing.text i analytics.text**
powinny zawierać (w naturalnej formie, nie jako upychanie słów kluczowych) odpowiedniki fraz, których szukają użytkownicy:

| Intencja | PL (wzorzec) | EN (wzorzec) |
|---|---|---|
| aplikacja do list zakupów | aplikacja do list zakupów | shopping list app |
| wspólna lista zakupów | wspólna lista zakupów | shared shopping list |
| lista zakupów na iPhone | lista zakupów na iPhone | shopping list for iPhone |
| rozliczanie wspólnych zakupów | rozliczanie wspólnych zakupów | splitting shared purchases / shared expenses |

Wskazówki: sprawdź, jak rodzimy użytkownik nazywa „listę zakupów” (np. DE: *Einkaufsliste*, FR: *liste de courses*, ES: *lista de la compra*,
IT: *lista della spesa*, NL: *boodschappenlijst*, SV: *inköpslista*, CS: *nákupní seznam*). Nazwa „Basket+” i „App Store” zostają bez tłumaczenia.
`seo.title` ma zaczynać się od „Basket+ –” i mieścić się w 60 znakach; `seo.description` w 160 (twarde limity walidatora).
"""

INTRO = """# Schemat kluczy i18n

Plik jest **generowany**: `python3 src/validate.py --write-schema-doc` z `i18n/_schema.json`. Źródłem prawdy o strukturze jest `i18n/pl.json`
(język bazowy). Każdy `i18n/<kod>.json` musi mieć **dokładnie te same klucze**, te same typy i te same długości list. Walidacja: `python3 src/validate.py`.

Kod języka = nazwa pliku (`cs.json` → `/cs/`; polski jest pod `/`). Kody UE: bg, hr, cs, da, nl, en, et, fi, fr, de, el, hu, ga, it, lv, lt, mt, pl, pt (pt-PT), ro, sk, sl, es, sv.
Dodanie języka = dodanie pliku `i18n/<kod>.json` (oraz opcjonalnie zrzutów w `site-screens/<kod>/`; zero pracy w HTML) i uruchomienie `python3 src/build.py`.

## Zasady

- **Limity** to maksymalna liczba znaków (po przetłumaczeniu). Walidator przerywa przy przekroczeniu. Teksty w językach długich (DE, FI, HU, EL, BG) układ znosi (łamanie/dzielenie wyrazów),
  ale trzymaj się limitów – wizualnie sprawdzone przy 320 px.
- **Mini-znaczniki** (jedyne dozwolone, HTML jest zabroniony): `\\n` = nowa linia (w nagłówkach `<br>`); `*tekst*` = akcent kolorem (tylko w kluczach „title”, w `hero.title` dokładnie jedna para);
  `**tekst**` = pogrubienie; `[[etykieta|nazwa]]` = link, gdzie nazwa to jedna z: `support`, `privacy`, `email`, `notify`, `icloud`, `plans`. Tłumacz tylko etykietę – nazwy i liczba znaczników mają być jak w pl.json.
- **Nie tłumaczymy**: „Basket+”, „Basket+ Free/Plus” (nazwy planów: tłumaczone mogą być tylko słowa Free/Plus, jeśli tak robi aplikacja – domyślnie zostają), „App Store”, „iCloud”, „Google AdMob”, adresu hello@basketplus.app.
- **Brak cen**: nie wpisuj kwot ani nazw walut. Cena i okres próbny są widoczne w aplikacji/App Store.
- **Fakty o produkcie** (reklamy, iCloud, Free/Plus, dostępność) są sprawdzone z kodem aplikacji – nie rozszerzaj ich i nie dodawaj funkcji ani liczb. W szczególności: nie wymieniaj modeli Garmin, nie podawaj dat premiery w kolejnych krajach.
- **Dostępność**: aplikacja jest w App Store; przycisk „Pobierz w App Store” prowadzi do `https://apps.apple.com/app/id6816518437` (Apple przekierowuje do sklepu kraju użytkownika) i towarzyszy mu kod QR. Strona nie wymienia krajów ani dat. Klucze `availability.*` są opcjonalne (wyłączona flaga `AVAILABILITY_NOTICE` w `src/build.py`).
- **Polityka prywatności i wsparcie** są tylko po polsku i angielsku (nie tłumaczymy polityki). Stopka dodaje odpowiednią informację (`footer.docs_note`).
- `alt` zrzutów opisują, co widać; nie pisz „zrzut ekranu” na początku. Dane na zrzutach to dane przykładowe – nie nazywaj ich „prawdziwymi”.
- Każdy tekst niepusty; stringi nie mogą zawierać `{{`, `{%` ani znaczników HTML.

"""


def write_schema_doc(i18n_dir):
    schema = json.load(open(os.path.join(i18n_dir, "_schema.json"), encoding="utf-8"))
    langs = build.load_langs(i18n_dir)[1]
    pl = langs[build.DEFAULT_LANG]
    en = langs.get("en", {})
    lines = [INTRO, "## Klucze\n",
             "Kolumna „Lista” oznacza liczbę elementów tablicy (identyczna we wszystkich językach). `*` w kluczu = każdy element tablicy.\n",
             "| Klucz | Limit znaków | Kontekst / uwagi | Wzór (pl) |", "|---|---|---|---|"]
    section = None
    for key, sc in schema.items():
        top = key.split(".")[0]
        if top != section:
            section = top
            lines.append("| **%s** | | | |" % top)
        example = ""
        try:
            node = pl
            for part in key.split("."):
                if part == "*":
                    node = node[0]
                else:
                    node = node[part]
            example = str(node).replace("\n", "↵").replace("|", "\\|")
            if len(example) > 70:
                example = example[:67] + "…"
            if isinstance(node, list):
                example = "(lista)"
        except Exception:  # noqa: BLE001
            pass
        count = ""
        parts = key.split(".")
        if parts[-1] == "*" or ".*." in key:
            node = pl
            for part in parts:
                if part == "*":
                    break
                node = node[part]
            count = " Lista: %d el." % len(node)
        lines.append("| `%s` | %s | %s%s | %s |" % (key, sc.get("max", ""), sc["ctx"].replace("|", "\\|"), count, example))
    lines.append("")
    lines.append(PHRASES)
    open(os.path.join(i18n_dir, "SCHEMA.md"), "w", encoding="utf-8").write("\n".join(lines))
    print("Zapisano i18n/SCHEMA.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--i18n", default=os.path.join(ROOT, "i18n"))
    ap.add_argument("--skip-fresh", action="store_true")
    ap.add_argument("--write-schema-doc", action="store_true")
    a = ap.parse_args()
    if a.write_schema_doc:
        write_schema_doc(a.i18n)
        return
    codes, langs = check_i18n(a.i18n)
    pages = check_pages(codes, langs)
    check_redirects(codes, langs)
    check_static_pages()
    check_sitemap(codes, langs)
    if not a.skip_fresh:
        check_fresh(a.i18n)
    for w in warnings:
        print("OSTRZEŻENIE:", w)
    for e in errors:
        print("BŁĄD:", e)
    print("\nJęzyki: %s | błędy: %d | ostrzeżenia: %d" % (", ".join(codes), len(errors), len(warnings)))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
