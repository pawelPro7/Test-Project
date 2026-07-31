# ⚽ Analiza Meczowa — panel Streamlit

Aplikacja Streamlit do analizy statystyk meczowych (styl danych Impect/PXT — packing, possession value, strefy boiska) z podziałem na zawodnika, drużynę, mapy cieplne i porównania.

## Szybki start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Aplikacja otworzy się pod `http://localhost:8501`. Dane wczytywane są z folderu `data/` przy starcie — wystarczy podmienić pliki CSV i odświeżyć stronę (cache czyści się automatycznie po zmianie zawartości pliku).

## Ważne: skąd wzięły się dane w `data/`

Z przesłanych plików udało się potwierdzić **realną strukturę tylko dla `playermatchstats.csv`** (616 kolumn) — `physical.csv` i `events.csv` w Twoich plikach były bajt-w-bajt identyczne z `playermatchstats.csv`, więc ich prawdziwej struktury nie znamy. Schematy tych dwóch plików, których używa ta aplikacja, są **rozsądnym założeniem** opartym na typowym eksporcie danych fizycznych i zdarzeń meczowych (dystans, sprinty, prędkość / typ zdarzenia, współrzędne x-y, xG) — nie potwierdzeniem.

Żeby aplikacja nie wysypywała się przy podmianie na Twoje prawdziwe pliki, wczytywanie danych w `utils/data_loader.py` jest **defensywne**:
- kolumny są dopasowywane po nazwie bez rozróżniania wielkości liter, z listy alternatywnych nazw (`PHYSICAL_COLUMN_CANDIDATES`, `EVENTS_COLUMN_CANDIDATES`),
- brakujący plik lub brakująca kolumna nie wywala aplikacji — sekcja, która ich potrzebuje, po prostu się chowa lub pokazuje komunikat zamiast błędu.

Jeśli Twój prawdziwy `physical.csv` / `events.csv` używa innych nazw kolumn niż te na liście, dopisz je do odpowiedniego słownika w `utils/data_loader.py` (na górze pliku) — reszta aplikacji zadziała bez zmian.

## Ważne: dane w `playermatchstats.csv` to w większości dane demonstracyjne

W przesłanym pliku był dokładnie **jeden prawdziwy wiersz** danych: zawodnik Phil Neumann (Birmingham City, mecz 206530, Championship, 2025-08-08). Ten wiersz jest zachowany w `data/playermatchstats.csv` bez zmian.

Żeby aplikacja miała co pokazywać (rankingi, porównania, mapy cieplne drużyn), doszedł do niego **w pełni fikcyjny** zestaw danych demo: 4 wymyślone drużyny, po 7 wymyślonych zawodników, 6 meczów. Żadna z tych drużyn ani żaden z tych zawodników nie istnieje naprawdę — to celowa decyzja, żeby nie generować statystyk przypisanych prawdziwym, możliwym do zidentyfikowania osobom. Wartości liczbowe są wygenerowane tak, by trzymać się realistycznych zakresów dla danej pozycji (np. bramkarz nie ma strzałów, środkowy obrońca ma dużo pojedynków powietrznych), ale to nadal dane syntetyczne, a nie wynik meczów.

Dane demo generuje `scripts/generate_demo_data.py` (ziarno losowe ustawione na stałe, więc wynik jest powtarzalny). Żeby wygenerować je ponownie lub zmienić liczbę drużyn/zawodników/meczów, edytuj stałe na górze tego skryptu i uruchom go ponownie z folderu głównego projektu:

```bash
python scripts/generate_demo_data.py
```

**Żeby zobaczyć w aplikacji tylko prawdziwe dane** — podmień pliki w `data/` na własne, pełne eksporty (wszystkie mecze/zawodnicy, nie pojedynczy wiersz).

## Struktura projektu

```
app.py                      punkt wejścia — konfiguracja strony, nawigacja, globalny CSS
data/
  playermatchstats.csv      1 prawdziwy wiersz + dane demo (616 kolumn)
  physical.csv              dane fizyczne — schemat założony, patrz wyżej
  events.csv                zdarzenia meczowe z współrzędnymi x/y — schemat założony
views/
  home.py                   przegląd ligi: KPI, liderzy statystyk, ostatnie wyniki
  player.py                 kartoteka zawodnika: KPI, radar percentylowy, mapa stref, forma, fizyczność
  team.py                   kartoteka drużyny: KPI, ranking zawodników, mapa stref drużyny, pełny skład
  heatmaps.py                mapy stref (playermatchstats) + prawdziwe mapy zdarzeń i strzałów (events.csv)
  comparison.py              porównanie 2–4 zawodników: radar nałożony + tabela zestawcza
utils/
  data_loader.py             wczytywanie i cache'owanie danych, dopasowywanie kolumn, agregacje
  styling.py                  paleta kolorów, CSS, komponenty (KPI card, nagłówek strony)
  viz.py                      wykresy Plotly: boisko, mapy cieplne stref, mapa zdarzeń, mapa strzałów, radar
scripts/
  generate_demo_data.py       generator danych demo (opisany wyżej)
  reference_real_row.csv      zachowany oryginalny wiersz — używany przez generator, nie przez aplikację
.streamlit/config.toml        motyw Streamlit dopasowany do palety aplikacji
```

## Uwaga o mapach stref

Mapy cieplne stref (np. w zakładce „Mapy cieplne” lub na kartotece zawodnika) są zbudowane z dwóch **osobnych rozkładów brzegowych**, które raportuje `playermatchstats.csv` — dotknięcia wg strefy boiska (5 stref) i dotknięcia wg korytarza (5 korytarzy) są osobnymi grupami kolumn, nie jedną wspólną tabelą 5×5. Siatka 5×5 pokazana w aplikacji to iloczyn tych dwóch rozkładów — **przybliżenie**, nie dokładny rozkład wspólny. Aplikacja zawsze to zaznacza w podpisie pod wykresem.

Mapa zdarzeń i mapa strzałów w zakładce „Mapy cieplne” (dolna sekcja) korzystają natomiast z prawdziwych współrzędnych x/y z `events.csv`, więc nie mają tego ograniczenia — o ile Twój plik faktycznie zawiera taką kolumnę.
