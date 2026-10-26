# Schemat kluczy i18n

Plik jest **generowany**: `python3 src/validate.py --write-schema-doc` z `i18n/_schema.json`. Źródłem prawdy o strukturze jest `i18n/pl.json`
(język bazowy). Każdy `i18n/<kod>.json` musi mieć **dokładnie te same klucze**, te same typy i te same długości list. Walidacja: `python3 src/validate.py`.

Kod języka = nazwa pliku (`cs.json` → `/cs/`; polski jest pod `/`). Kody UE: bg, hr, cs, da, nl, en, et, fi, fr, de, el, hu, ga, it, lv, lt, mt, pl, pt (pt-PT), ro, sk, sl, es, sv.
Dodanie języka = dodanie pliku `i18n/<kod>.json` (oraz opcjonalnie zrzutów w `site-screens/<kod>/`; zero pracy w HTML) i uruchomienie `python3 src/build.py`.

## Zasady

- **Limity** to maksymalna liczba znaków (po przetłumaczeniu). Walidator przerywa przy przekroczeniu. Teksty w językach długich (DE, FI, HU, EL, BG) układ znosi (łamanie/dzielenie wyrazów),
  ale trzymaj się limitów – wizualnie sprawdzone przy 320 px.
- **Mini-znaczniki** (jedyne dozwolone, HTML jest zabroniony): `\n` = nowa linia (w nagłówkach `<br>`); `*tekst*` = akcent kolorem (tylko w kluczach „title”, w `hero.title` dokładnie jedna para);
  `**tekst**` = pogrubienie; `[[etykieta|nazwa]]` = link, gdzie nazwa to jedna z: `support`, `privacy`, `email`, `notify`, `icloud`, `plans`. Tłumacz tylko etykietę – nazwy i liczba znaczników mają być jak w pl.json.
- **Nie tłumaczymy**: „Basket+”, „Basket+ Free/Plus” (nazwy planów: tłumaczone mogą być tylko słowa Free/Plus, jeśli tak robi aplikacja – domyślnie zostają), „App Store”, „iCloud”, „Google AdMob”, adresu hello@basketplus.app.
- **Brak cen**: nie wpisuj kwot ani nazw walut. Cena i okres próbny są widoczne w aplikacji/App Store.
- **Fakty o produkcie** (reklamy, iCloud, Free/Plus, dostępność) są sprawdzone z kodem aplikacji – nie rozszerzaj ich i nie dodawaj funkcji ani liczb. W szczególności: nie wymieniaj modeli Garmin, nie podawaj dat premiery w kolejnych krajach.
- **Dostępność**: aplikacja jest w App Store; przycisk „Pobierz w App Store” prowadzi do `https://apps.apple.com/app/id6816518437` (Apple przekierowuje do sklepu kraju użytkownika) i towarzyszy mu kod QR. Strona nie wymienia krajów ani dat. Klucze `availability.*` są opcjonalne (wyłączona flaga `AVAILABILITY_NOTICE` w `src/build.py`).
- **Polityka prywatności i wsparcie** są tylko po polsku i angielsku (nie tłumaczymy polityki). Stopka dodaje odpowiednią informację (`footer.docs_note`).
- `alt` zrzutów opisują, co widać; nie pisz „zrzut ekranu” na początku. Dane na zrzutach to dane przykładowe – nie nazywaj ich „prawdziwymi”.
- Każdy tekst niepusty; stringi nie mogą zawierać `{{`, `{%` ani znaczników HTML.


## Klucze

Kolumna „Lista” oznacza liczbę elementów tablicy (identyczna we wszystkich językach). `*` w kluczu = każdy element tablicy.

| Klucz | Limit znaków | Kontekst / uwagi | Wzór (pl) |
|---|---|---|---|
| **meta** | | | |
| `meta.html_lang` | 8 | Wartość atrybutu <html lang>. BCP 47: np. cs, de, pt-PT. Nie tłumaczyć. | pl |
| `meta.hreflang` | 8 | Wartość hreflang w <link rel=alternate> i sitemap. Zwykle jak html_lang (dla portugalskiego: pt-PT). | pl |
| `meta.og_locale` | 8 | og:locale w formacie jezyk_KRAJ, np. cs_CZ, de_DE, pt_PT, ga_IE. | pl_PL |
| `meta.native_name` | 24 | Nazwa języka w nim samym (endonim), np. Čeština, Deutsch. Widoczna w przełączniku języka (lang= ustawiane automatycznie). | Polski |
| `meta.short` | 4 | Skrót w przycisku przełącznika języka (2-3 litery wielkimi), np. CS, DE. | PL |
| **seo** | | | |
| `seo.title` | 60 | <title> strony i og:title bazowo. TWARDY limit 60 znaków. Wzór: 'Basket+ – <fraza użytkownika: wspólna lista zakupów na iPhone>'. Unikalny w każdym języku. | Basket+ – wspólna lista zakupów na iPhone |
| `seo.description` | 160 | meta description. TWARDY limit 160 znaków; ~120-160. Fraza 'aplikacja do wspólnych list zakupów na iPhone', zachęta do działania, wzmianka o Free i Plus. Unikalny. | Basket+ to aplikacja do wspólnych list zakupów na iPhone. Planuj za… |
| `seo.og_title` | 70 | og:title i twitter:title (może być identyczny z seo.title). | Basket+ – wspólna lista zakupów na iPhone |
| `seo.og_description` | 200 | og:description i twitter:description (podgląd przy udostępnianiu linku). Zakończ zachętą do pobrania z App Store. | Aplikacja do list zakupów: wspólne listy, paragony i rozliczanie ws… |
| `seo.og_image_alt` | 120 | Tekst alternatywny grafiki og-image (og:image:alt). | Basket+ – aplikacja do wspólnych list zakupów na iPhone |
| `seo.app_description` | 250 | Opis aplikacji w JSON-LD (SoftwareApplication.description). Zwykły tekst, bez znaczników, bez obietnic cen/ocen. | Aplikacja do list zakupów na iPhone’a: wspólna lista zakupów, czat,… |
| **ui** | | | |
| `ui.skip_link` | 40 | Link 'przejdź do treści' (widoczny po fokusie klawiatury). | Przejdź do treści |
| `ui.brand_aria` | 50 | aria-label logo w nagłówku (link do strony głównej tego języka). Zaczynaj od 'Basket+'. | Basket+ – strona główna |
| `ui.nav_aria` | 40 | aria-label głównej nawigacji. | Główna nawigacja |
| `ui.nav_features` | 18 | Pozycja menu -> sekcja funkcji (#features). | Możliwości |
| `ui.nav_icloud` | 18 | Pozycja menu -> sekcja iCloud i udostępnianie (#icloud). W większości języków zostaje 'iCloud'. | iCloud |
| `ui.nav_plans` | 18 | Pozycja menu -> sekcja Free i Plus (#plus). | Free i Plus |
| `ui.nav_faq` | 14 | Pozycja menu -> FAQ. | FAQ |
| `ui.nav_support` | 20 | Pozycja menu -> strona wsparcia (jest tylko po polsku/angielsku; link ma hreflang=en). | Wsparcie |
| `ui.lang_menu_aria` | 50 | aria-label przycisku otwierającego listę języków. | Wybierz język strony |
| `ui.lang_list_aria` | 40 | aria-label listy języków w stopce. | Języki strony |
| **hero** | | | |
| `hero.eyebrow` | 50 | Status nad nagłówkiem: aplikacja jest dostępna w App Store (bez wymieniania krajów). | Dostępna w App Store |
| `hero.title` | 46 | H1. Dwie linie rozdzielone \n; druga w *gwiazdkach* = akcent kolorem (dokładnie jedna para *…*). Max ~22 znaki na linię. | Zakupy, które↵*układają się same.* |
| `hero.lead` | 230 | Akapit pod H1. Powinien zawierać naturalnie frazy: 'aplikacja do list zakupów', 'wspólna lista zakupów', 'lista zakupów na iPhone', 'rozliczanie wspólnych zakupów'. | Basket+ to aplikacja do list zakupów na iPhone’a: wspólna lista zak… |
| `hero.store_small` | 22 | Mała etykieta nad 'App Store' w przycisku (EN: 'Download on the'). Samo 'App Store' nie jest tłumaczone. | Pobierz w |
| `hero.store_aria` | 64 | aria-label przycisku App Store. MUSI zaczynać się od widocznego tekstu przycisku (store_small + 'App Store'), np. 'Pobierz w App Store – Basket+'. | Pobierz w App Store – Basket+ |
| `hero.qr_label` | 30 | Podpis pod kodem QR. | Zeskanuj telefonem |
| `hero.qr_aria` | 72 | aria-label linku z kodem QR. Zacznij od widocznego podpisu qr_label. | Zeskanuj telefonem – Basket+ w App Store |
| `hero.qr_alt` | 80 | Alt obrazu kodu QR. | Kod QR prowadzący do Basket+ w App Store |
| `hero.see_how` | 32 | Link tekstowy przewijający do funkcji (po nim jest dekoracyjna strzałka). | Zobacz, jak działa |
| `hero.platform_note` | 80 | Uwaga pod przyciskami: iPhone, iPad, Apple Watch. | Projektowane dla iPhone’a, iPada i Apple Watch. |
| `hero.visual_aria` | 50 | aria-label grupy z ekranem aplikacji. | Ekran aplikacji Basket+ |
| `hero.alt` | 130 | Alt zrzutu ekranu głównego (opisz co widać: maskotka, wydarzenia, listy). | Ekran główny Basket+ z maskotką, wydarzeniami i listami zakupów |
| `hero.note_top` | 34 | Dekoracyjna plakietka (aria-hidden) przy zrzucie. | Gotowe na wspólne zakupy |
| `hero.note_bottom` | 30 | Dekoracyjna plakietka (aria-hidden) przy zrzucie. | Dodawaj po swojemu |
| **availability** | | | |
| `availability.title` | 24 | (OPCJONALNE – używane tylko przy fladze availability_notice w build.py, domyślnie wyłączonej; nie trzeba tłumaczyć) Nagłówek bloku o dostępności (pod przyciskami App Store). | Dostępność |
| `availability.text` | 180 | (OPCJONALNE – używane tylko przy fladze availability_notice w build.py, domyślnie wyłączonej; nie trzeba tłumaczyć) FAKT: dziś aplikacja jest w App Store w Polsce; w innych krajach 'wkrótce' BEZ konkretnej daty. | Dziś Basket+ jest w App Store w Polsce. W kolejnych krajach pojawi … |
| `availability.store_hint` | 130 | (OPCJONALNE – używane tylko przy fladze availability_notice w build.py, domyślnie wyłączonej; nie trzeba tłumaczyć) Wyjaśnienie, że komunikat sklepu 'niedostępne' oznacza brak aplikacji w kraju użytkownika. | Jeśli App Store pokazuje „niedostępne”, aplikacji nie ma jeszcze w … |
| `availability.notify_text` | 150 | (OPCJONALNE – używane tylko przy fladze availability_notice w build.py, domyślnie wyłączonej; nie trzeba tłumaczyć) Zachęta do wysłania e-maila. MUSI zawierać: odpowiadamy ręcznie; niczego nie zapisujemy/nie zbieramy na stronie (brak formularzy). | Czekasz na swój kraj? Napisz do nas – odpowiadamy ręcznie i niczego… |
| `availability.notify_link` | 45 | (OPCJONALNE – używane tylko przy fladze availability_notice w build.py, domyślnie wyłączonej; nie trzeba tłumaczyć) Tekst linku mailto (hello@basketplus.app). | Daj znać, że czekasz |
| `availability.mail_subject` | 70 | (OPCJONALNE – używane tylko przy fladze availability_notice w build.py, domyślnie wyłączonej; nie trzeba tłumaczyć) Gotowy temat wiadomości (w języku strony). Bez znaków specjalnych poza interpunkcją. | Basket+ w moim kraju |
| `availability.mail_body` | 300 | (OPCJONALNE – używane tylko przy fladze availability_notice w build.py, domyślnie wyłączonej; nie trzeba tłumaczyć) Gotowa treść wiadomości: powitanie, '…chcę korzystać z Basket+ w tym kraju: ' (użytkownik dopisuje kraj), pozdrowienie. Użyj \n dla nowych linii. | Dzień dobry,↵↵chcę korzystać z Basket+ w tym kraju: ↵↵Pozdrawiam |
| `availability.short` | 90 | (OPCJONALNE – używane tylko przy fladze availability_notice w build.py, domyślnie wyłączonej; nie trzeba tłumaczyć) Jednozdaniowa wersja informacji o dostępności (sekcja końcowa). | Dziś w App Store w Polsce, w innych krajach wkrótce. |
| **trust** | | | |
| `trust.aria` | 40 | aria-label paska z trzema faktami. | Najważniejsze informacje |
| `trust.items.*.title` | 28 | Pogrubiony fakt. 1: bez konta Basket+; 2: 24 języki aplikacji; 3: natywnie dla Apple. Zachowaj kolejność i liczbę (3). Lista: 3 el. | Bez konta Basket+ |
| `trust.items.*.text` | 50 | Druga linia faktu. 1: działa lokalnie, iCloud synchronizuje; 2: dla domów bez granic; 3: także widżety i zegarek. Lista: 3 el. | Działa lokalnie, iCloud synchronizuje |
| **lists** | | | |
| `lists.label` | 34 | Etykieta sekcji. Zachowaj numerację '01 · '. | 01 · Listy zakupów |
| `lists.title` | 46 | H2, dwie linie (\n). | Mniej stukania.↵Więcej kupowania. |
| `lists.text` | 300 | Opis list zakupów. Naturalnie fraza 'lista zakupów na iPhone'. | Lista zakupów na iPhone’a, którą wypełnisz tak, jak myślisz: wpisz … |
| `lists.bullets.*` | 70 | Punkty listy (3 pozycje). Lista: 3 el. | Szybkie dodawanie produktów i wielu pozycji naraz |
| `lists.alt` | 130 | Alt zrzutu szczegółu listy. | Lista zakupów Basket+ z kategoriami, ilościami i wspólnym postępem |
| `lists.ticket1_name` | 18 | Dekoracyjna etykieta (aria-hidden): nazwa produktu 1, np. pomidory. | pomidory |
| `lists.ticket1_qty` | 10 | Ilość produktu 1, np. '4 szt.'. | 4 szt. |
| `lists.ticket2_name` | 18 | Nazwa produktu 2, np. makaron. | makaron |
| `lists.ticket2_qty` | 10 | Ilość produktu 2, np. '2 op.'. | 2 op. |
| **sharing** | | | |
| `sharing.label` | 34 | Etykieta sekcji '02 · …'. | 02 · Wspólne zakupy |
| `sharing.title` | 46 | H2, dwie linie (\n). | Jedna lista.↵Wszyscy na bieżąco. |
| `sharing.text` | 430 | Opis wspólnych list. Fraza 'wspólna lista zakupów'. Musi zawierać znacznik linku [[etykieta\|icloud]] do sekcji warunków udostępniania. FAKT: zwykłe udostępnianie i czat list są w Free. | Wspólna lista zakupów: udostępnij listę przez iCloud, zobacz zmiany… |
| `sharing.badge` | 44 | Plakietka: udostępnianie i czat list są w Free. | Udostępnianie i czat list: Free |
| `sharing.alt` | 130 | Alt zrzutu czatu na liście. | Rozmowa na bezpłatnej, współdzielonej liście Basket+ |
| `sharing.pill_sent` | 14 | Dekoracyjna etykieta (aria-hidden) 'Wysłano'. | Wysłano |
| `sharing.pill_received` | 14 | Dekoracyjna etykieta (aria-hidden) 'Odebrano'. | Odebrano |
| **events** | | | |
| `events.label` | 34 | Etykieta sekcji '03 · … · Plus'. | 03 · Wydarzenia · Plus |
| `events.title` | 62 | H2 (może być bez \n). | Plan, który nie ginie w wiadomościach. |
| `events.text` | 300 | Opis wydarzeń. FAKT: każdy uczestnik wydarzenia potrzebuje własnego Plus. | Wyjazd, przyjęcie czy rodzinne święta. Połącz listy w jedno wydarze… |
| `events.chip` | 24 | Plakietka 'Basket+ Plus'. | Basket+ Plus |
| `events.alt` | 130 | Alt zrzutu wydarzenia. | Ekran wydarzenia Basket+ Plus z trzema listami i rozliczeniami |
| `events.cal_month` | 4 | Skrót miesiąca na dekoracyjnej karcie kalendarza (WIELKIMI), np. PAŹ / OCT. | PAŹ |
| `events.cal_day` | 2 | Dzień na karcie kalendarza (zwykle 24). | 24 |
| `events.cal_title` | 26 | Przykładowa nazwa wydarzenia na karcie (dekoracja). | Weekend w górach |
| `events.cal_meta` | 28 | Podtytuł karty: liczba list i osób (przykład). | 3 listy · 4 osoby |
| **analytics** | | | |
| `analytics.label` | 40 | Etykieta sekcji '04 · … · Plus'. | 04 · Paragony i raporty · Plus |
| `analytics.title` | 50 | H2. | Wydatki przestają być zagadką. |
| `analytics.text` | 260 | Opis paragonów i raportów. Fraza 'rozliczanie wspólnych zakupów'. | Zachowuj paragony, analizuj kategorie i sklepy, obserwuj trendy ora… |
| `analytics.alt_report` | 130 | Alt zrzutu raportu 6 miesięcy. | Raport Basket+ Plus pokazujący wydatki z ostatnich sześciu miesięcy |
| `analytics.alt_receipts` | 130 | Alt zrzutu historii paragonów. | Historia paragonów Basket+ Plus z datami, sklepami i kwotami |
| `analytics.caption_title` | 34 | Podpis na zrzutach (tytuł). | 6 miesięcy w jednym widoku |
| `analytics.caption_note` | 50 | Podpis: dane na zrzutach są przykładowe (EN: 'Sample data shown in the app'). NIE pisać 'prawdziwe/real'. | Przykładowe dane przedstawione w aplikacji |
| **plans** | | | |
| `plans.label` | 30 | Etykieta sekcji Free i Plus. | Basket+ Free i Plus |
| `plans.title` | 58 | H2, dwie linie (\n). | Zacznij od listy.↵Rozwiń, kiedy potrzebujesz. |
| `plans.text` | 220 | Wstęp sekcji. | Zwykłe wspólne listy pozostają dostępne bez subskrypcji. Plus dodaj… |
| `plans.free_kicker` | 26 | Mały nadtytuł karty Free. | Na co dzień |
| `plans.free_name` | 24 | Nazwa planu: 'Basket+ Free'. | Basket+ Free |
| `plans.free_items.*` | 40 | Punkty planu Free (3). Lista: 3 el. | Listy zakupów |
| `plans.free_ads` | 60 | Informacja w karcie Free, że plan zawiera reklamy (opis poniżej). | Zawiera dyskretne reklamy – opis poniżej. |
| `plans.plus_kicker` | 26 | Mały nadtytuł karty Plus. | Więcej organizacji |
| `plans.plus_name` | 24 | Nazwa planu: 'Basket+ Plus'. | Basket+ Plus |
| `plans.plus_items.*` | 40 | Punkty planu Plus (5). Ostatni = brak reklam. Lista: 5 el. | Wszystko z wersji Free |
| `plans.price_note` | 300 | Cena NIE jest podawana na stronie (decyzja otwarta). Napisz: cena i ewentualny okres próbny widoczne w aplikacji i App Store przed zakupem; subskrypcja dotyczy konta Apple, które ją wykupiło. NIE wpisywać kwot. | Cena i ewentualny okres próbny są widoczne w aplikacji oraz w App S… |
| `plans.ads_title` | 40 | Nagłówek bloku o reklamach w Free. | Reklamy w wersji Free |
| `plans.ads_items.*` | 270 | 4 punkty (kolejność ma znaczenie): 1) natywne reklamy Google AdMob w dwóch miejscach: ekran główny i Wydatki, nie na listach/czacie; 2) personalizacja wyłączona, ale Google może używać identyfikatorów do pomiaru i ograniczania częstotliwości; 3) tam gdzie wymaga prawo (EOG, UK, Szwajcaria) reklamy nie ładują się bez zgody, iPhone może zapytać o śledzenie, odmowa nie blokuje aplikacji; 4) w Plus reklamy znikają. FAKTY zweryfikowane z kodem aplikacji. Lista: 4 el. | Dyskretne reklamy natywne Google AdMob pojawiają się w dwóch miejsc… |
| `plans.ads_more` | 80 | Zdanie z linkiem [[etykieta\|privacy]] do polityki prywatności. | Szczegóły: [[polityka prywatności\|privacy]]. |
| `plans.group_title` | 50 | Nagłówek przykładu grupy Free + Plus. | Przykład: grupa z Free i Plus |
| `plans.group_intro` | 100 | Założenie przykładu: jedna osoba ma Plus, pozostałe Free. | Jedna osoba ma Plus, pozostałe korzystają z Free. Co mogą razem? |
| `plans.group_rows.*.what` | 40 | Wiersz przykładu: 1 zwykła wspólna lista; 2 wydarzenie; 3 paragony/raporty/rozliczenia; 4 gdy Plus wygaśnie. Zachowaj 4 wiersze w tej kolejności. Lista: 4 el. | Zwykła wspólna lista |
| `plans.group_rows.*.result` | 270 | Co dzieje się w danej sytuacji. FAKTY (docs/plus-model.md): wydarzenie wymaga własnego Plus każdego uczestnika, Plus innej osoby niczego nie odblokowuje; po wygaśnięciu Plus dane zostają, wydarzenie tylko do odczytu, można je opuścić. Lista: 4 el. | Wszyscy dodają i odhaczają produkty oraz piszą na czacie listy. Plu… |
| **icloud** | | | |
| `icloud.label` | 34 | Etykieta sekcji o iCloud (#icloud). | iCloud i udostępnianie |
| `icloud.title` | 62 | H2, dwie linie (\n). | Bez konta Basket+.↵Z iCloud, gdy go chcesz. |
| `icloud.text` | 80 | Podtytuł: co działa bez iCloud, a co go wymaga. | Co działa bez iCloud, a co go wymaga. |
| `icloud.cards.*.title` | 34 | 4 karty: brak konta Basket+; z iCloud; bez iCloud; warunki udostępniania. Zachowaj kolejność. Lista: 4 el. | Brak konta Basket+ |
| `icloud.cards.*.text` | 270 | Treść karty. FAKTY: brak konta; synchronizacja/udostępnianie przez iCloud (zaproszenia Apple); bez iCloud (lub wyłączony Basket+ w ustawieniach iCloud) aplikacja działa lokalnie; obie strony potrzebują iCloud i Basket+; zwykła lista także dla Free, wydarzenie wymaga własnego Plus. Lista: 4 el. | Nie zakładasz konta ani się nie logujesz. Nie prowadzimy własnej ba… |
| **faq** | | | |
| `faq.label` | 12 | Etykieta sekcji FAQ. | FAQ |
| `faq.title` | 40 | H2 sekcji FAQ. | Krótko i konkretnie. |
| `faq.items.*.q` | 92 | Pytanie FAQ (10 pozycji, ta sama kolejność; trafia do JSON-LD FAQPage). Lista: 10 el. | Czy do korzystania z Basket+ potrzebuję konta? |
| `faq.items.*.a` | 340 | Odpowiedź FAQ (trafia do JSON-LD jako zwykły tekst). Znaczniki: [[etykieta\|privacy]], [[etykieta\|support]], [[etykieta\|email]] – ta sama liczba i nazwy jak w pl.json. Lista: 10 el. | Nie. Basket+ nie wymaga zakładania konta ani logowania. Synchroniza… |
| **closing** | | | |
| `closing.eyebrow` | 50 | Status nad hasłem końcowym: dostępna teraz (bez wymieniania krajów). | Dostępna teraz |
| `closing.title` | 62 | H2 końcowe, dwie linie (\n). | Miejsce na zakupy.↵I spokój wokół nich. |
| `closing.icon_alt` | 50 | Alt ikony aplikacji. | Ikona aplikacji Basket+ |
| **footer** | | | |
| `footer.tagline` | 40 | Hasło w stopce. | Zakupy ogarnięte razem. |
| `footer.col_app` | 20 | Nagłówek kolumny: aplikacja. | Aplikacja |
| `footer.col_help` | 20 | Nagłówek kolumny: pomoc. | Pomoc |
| `footer.col_docs` | 20 | Nagłówek kolumny: dokumenty. | Dokumenty |
| `footer.col_lang` | 20 | Nagłówek listy języków. | Języki |
| `footer.support` | 30 | Link do strony wsparcia (PL/EN). | Wsparcie i kontakt |
| `footer.privacy` | 30 | Link do polityki prywatności (PL/EN) – NIE tłumaczymy samej polityki. | Polityka prywatności |
| `footer.terms` | 30 | Link do warunków Apple (EULA). | Warunki korzystania |
| `footer.docs_note` | 120 | Informacja pod kolumnami: wsparcie i polityka prywatności są dostępne po polsku i angielsku (pokazywana na stronach innych niż pl/en). | Wsparcie i polityka prywatności są dostępne po polsku i angielsku. |
| `footer.copyright` | 90 | Linia praw autorskich: © 2026 Basket+. Aplikacja tworzona niezależnie w Polsce. | © 2026 Basket+. Aplikacja tworzona niezależnie w Polsce. |

## Słownik i wyrażenia wymagające szczególnej uwagi

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
