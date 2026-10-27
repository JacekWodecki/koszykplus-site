# Strona Basket+ (basketplus.app)

Statyczna, wielojęzyczna strona na GitHub Pages. Źródłem prawdy są **tłumaczenia w `i18n/<kod>.json`** i jeden szablon
`src/templates/home.html`; `python3 src/build.py` generuje gotowe pliki do korzenia repo (GitHub Pages serwuje je bez kroku budowania,
wynik jest commitowany). Bez zależności (Python 3 stdlib); Pillow jest opcjonalny (tylko warianty obrazów AVIF/WebP).

## Struktura

| Ścieżka | Rola |
|---|---|
| `i18n/<kod>.json` | wszystkie teksty języka (nawigacja, sekcje, FAQ, title/description/og, alt-y, aria) |
| `i18n/SCHEMA.md` | lista kluczy z kontekstem, limitami długości, słownikiem i frazami SEO (generowany z `i18n/_schema.json`) |
| `src/build.py`, `src/tmpl.py` | generator i mini-szablony |
| `src/validate.py` | walidator (jedyna bramka jakości przed commitem) |
| `src/images.py` | warianty responsywne zrzutów (AVIF/WebP/JPG 276 i 552 px) |
| `index.html` (pl), `<kod>/index.html` | **generowane** – nie edytować ręcznie |
| `en.html` | generowane przekierowanie ze starego adresu do `/en/` |
| `support.html`, `support-en.html`, `privacy.html` | ręczne, adresy **nie zmieniać** (używa ich App Store Connect i Garmin) |
| `app-ads.txt`, `CNAME`, `.nojekyll` | nie ruszać (`.nojekyll` wyłącza Jekylla na GitHub Pages; bez niego build pada na `{{` w `i18n/SCHEMA.md`, walidator tego pilnuje) |

URL-e: polski pod `/`, pozostałe pod `/<kod>/` (kody UE: bg hr cs da nl en et fi fr de el hu ga it lv lt mt pl pt ro sk sl es sv; portugalski: `/pt/`, hreflang `pt-PT`).

## Dodanie języka (bez pracy w HTML)

1. Skopiuj `i18n/en.json` do `i18n/<kod>.json` i przetłumacz wartości (nie klucze). Zasady, limity znaków, słownik i frazy SEO: `i18n/SCHEMA.md`.
   Ustaw w `meta`: `html_lang`, `hreflang` (dla pt: `pt-PT`), `og_locale` (np. `cs_CZ`), `native_name`, `short`.
2. (Opcjonalnie) wrzuć 6 zrzutów `dashboard-real, event-organization, list-chat, list-detail, receipt-history, reports-6m` (`.jpg`, 552×1200)
   do `/Users/jacekwodecki/Desktop/Basket+/site-screens/<kod>/`. Build skopiuje je do `assets/screens/<kod>/` i wygeneruje warianty;
   bez kompletu sześciu zrzutów strona używa angielskich (fallback). Inna lokalizacja: `--screens-src DIR` lub `BASKET_SCREENS_SRC`.
3. `python3 src/build.py` – generuje `<kod>/index.html`, odświeża przełączniki języków, hreflang we wszystkich wersjach, `sitemap.xml`.
4. `python3 src/validate.py` – musi zakończyć się „błędy: 0”.
5. Commit (pliki `i18n/`, wygenerowane strony, `sitemap.xml`, `assets/screens/<kod>/`).

Walidator sprawdza m.in.: komplet i typy kluczy względem `pl.json`, limity (title ≤ 60, description ≤ 160, pozostałe w `_schema.json`), znaczniki `[[link|nazwa]]`/`*akcent*`,
puste teksty, unikalność title/description, `<html lang>`, jedno H1, canonical, wzajemne hreflang + x-default, martwe linki i kotwice, alt/width/height obrazów, lazy/fetchpriority,
poprawność JSON-LD i zgodność FAQPage z widoczną treścią, `sitemap.xml` (alternates, lastmod, brak przekierowań/noindex), `robots.txt` oraz czy wynik w repo jest zgodny z czystym buildem.

## Opcje builda

- `AVAILABILITY_NOTICE` w `src/build.py` (lub `BASKET_AVAILABILITY_NOTICE=1`): opcjonalny blok „dostępność w krajach” z mailto – **domyślnie wyłączony**, nic nie jest widoczne. Wymaga kluczy `availability.*` w JSON.
- `ALIASES` w `src/build.py`: dodatkowe przekierowania `/<alias>/` → `/<kod>/` (domyślnie puste).
- `--out DIR`, `--i18n DIR`: build do innego katalogu / z innymi tłumaczeniami (testy).

## Zasady

Bez zewnętrznych skryptów, czcionek z CDN, formularzy i śledzenia. Jedyny własny skrypt to `assets/site.js` (otwieranie pytania FAQ z adresu, Esc zamyka menu języków; strona działa bez niego).
Polityka prywatności i wsparcie są tylko po polsku i angielsku; strony językowe linkują do nich z informacją.

## Indeksowanie i SEO (uwagi)

- GitHub Pages zwraca HTTP 200 i nie pozwala ustawić nagłówka `X-Robots-Tag` ani przekierowań 301. Sterujemy więc meta `robots` (`index, follow`), `canonical` i `robots.txt` (Allow + Sitemap).
  `/index.html` i `/` to ta sama treść; canonical zawsze wskazuje `/` (analogicznie `/<kod>/`).
- JSON-LD: `SoftwareApplication` (bez cen i ocen) i `FAQPage` zgodny z widoczną treścią. Nie obiecuje to rich results – Google ogranicza FAQ do wybranych witryn.
- Obrazy: `<picture>` AVIF → WebP → JPG, `srcset`/`sizes`, `width/height`, lazy poniżej pierwszego ekranu, `fetchpriority="high"` na zrzucie LCP. Czcionki systemowe (brak ładowania fontów).

## Google Search Console – kroki dla właściciela (nie wykonane przez agenta)

1. Wejdź na <https://search.google.com/search-console>, dodaj usługę typu **Domena** `basketplus.app` i zweryfikuj rekordem DNS TXT u rejestratora (dla GitHub Pages bez zmiany CNAME/A).
2. Sitemaps → dodaj `https://basketplus.app/sitemap.xml` (ma alternates hreflang dla wszystkich języków).
3. Inspekcja adresu URL → sprawdź `https://basketplus.app/` i `https://basketplus.app/en/` → „Poproś o zindeksowanie”.
4. Po kilku dniach: raport „Strony” (czy kanoniczne = oczekiwane, brak „Duplikat, Google wybrało inną kanoniczną”), „Podstawowe wskaźniki internetowe” (dane terenowe), „Ulepszenia” (Dane strukturalne).
5. Po dodaniu każdego nowego języka: build, validate, push – sitemapa odświeży się sama; opcjonalnie ponów inspekcję nowego `/<kod>/`.
