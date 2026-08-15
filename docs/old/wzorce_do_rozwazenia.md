#wzorce_do_rozwazenia.md

11 wzorców sztucznej inteligencji w produkcji, które starsi inżynierowie po cichu wdrażają w 2026 r. (część 1)
Przewodnik po mało efektownych mechanizmach stojących za systemami sztucznej inteligencji, które faktycznie przetrwają kontakt z użytkownikami.






Większość treści dotyczących inżynierii AI nadal traktuje LLM jak autouzupełnianie na sterydach z 2023 roku. Ale czy zespoły faktycznie wprowadzają niezawodne systemy AI w 2026 roku? Myślą zupełnie inaczej, obsesyjnie skupiając się na ekonomii kontekstu, powtarzalności trajektorii i mało efektownej mechanice zapominania. Oto 22 wzorce, które zaobserwowałem, odróżniają dema od systemów, które nie zawodzą w niedzielę o 3 nad ranem.

Dlaczego to ma znaczenie w 2026 roku
Na początku tego roku dominujący koszt wykorzystania sztucznej inteligencji po cichu się zmienił. Kiedyś były to dolary przeznaczane na wnioskowanie. Teraz to koordynacja inżynieryjna. Interfejsy API modeli stały się tańsze, opóźnienia skróciły się, multimodalność stała się standardem, ale to systemy oparte na modelach marnują czas firm. Każdy zespół, z którym pracowałem w tym roku, ma swoją historię: pętlę agentów, która nie chciała się zatrzymać, semantyczną pamięć podręczną, która zatruwała dane wyjściowe przez tydzień, zanim ktokolwiek to zauważył, dopracowanie, które nie trafiło do dystrybucji, ponieważ dostawca podmienił model pod tym samym aliasem.

Poniższe schematy nie są teoretyczne. Każdy z nich wynika z problemu produkcyjnego, który sam przeżyłem lub obserwowałem u kolegi. Jeśli masz już za sobą fazę „wow, to działa” i zastanawiasz się „dlaczego to w ogóle tak działa ?”, to te schematy są dla Ciebie.

Aby zapoznać się z podstawowym kontekstem architektury, zobacz RAG vs MCP: różnice architektoniczne, które każdy programista AI musi zrozumieć .

Spis treści
Hierarchiczne przycinanie kontekstu
Spekulatywne wykonanie narzędzia
Osadzanie wykrywania dryfu
Trasowanie uwzględniające budżet tokenów
Ocena modelu cienia
Prawdopodobne unieważnienie pamięci podręcznej
Destylacja na zimno
Kompozycja funkcji strumieniowej
Debugowanie odtwarzania trajektorii
Głębokość wyszukiwania adaptacyjnego
Szablony komunikatów federacyjnych
1. Hierarchiczne przycinanie kontekstu
Okna kontekstowe stały się większe, ale jakość uwagi nie skalowała się wraz z nimi. Umieszczenie 200 tys. tokenów w żądaniu nadal pogarsza rozpoznawalność faktów ukrytych w kontekście, a Ty płacisz tokenami, których nie potrzebujesz. Hierarchiczne przycinanie traktuje kontekst jako drzewo ważności: reguły systemowe u korzenia, bieżąca zmiana u liścia, z podsumowanymi gałęziami pomiędzy. Każdy węzeł ma budżet i wynik świeżości, a w momencie żądania przechodzisz przez drzewo, zagęszczając gałęzie, których stosunek tokenów do informacji wygląda źle. Odblokowanie nie jest mniejszym kontekstem — to ten sam kontekst z gęstszym sygnałem na token.

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 1 — Hierarchiczne przycinanie kontekstu. Kontekst ma strukturę drzewa. Reguły systemowe znajdują się u podstawy, profil i pamięć poniżej, podsumowania tematów pośrodku, a surowe, ostatnie zmiany na liściach. W momencie żądania globalny budżet tokenów jest alokowany odgórnie, utrzymując gałęzie o dużej gęstości w stanie pełnym i kompresując pozostałe. Pasek u dołu pokazuje, jak 12 000 tokenów jest partycjonowanych na warstwy.
z klas danych import dataclass, pole 
z typing import Callable, List, Optional 

@dataclass 
class ContextNode: 
    etykieta: str
     surowy: str
     dzieci: Lista[ "ContextNode" ] = pole (default_factory=list) 
    ważność: float = 1.0
     podsumowanie: Opcjonalne[ str ] = Brak

     def tokeny ( self , force_raw: bool = False) -> int: 
        tekst = self .raw if (force_raw lub self .summary jest None ) else  self .summary 
        return  max ( 1 , len (tekst) // 4)

 def prune (węzeł: ContextNode, budżet: int, podsumowanie: Callable[[ str , int], str ]) ->  str : 
    jeśli węzeł. tokens () <= budżet: 
        zwraca node.summary lub node.raw 
    ranked = posortowane (node.children, 
                    key=lambda c: c.importance / c. tokens (), 
                    reverse=True) 
    zachowane, użyte = [], 0 
    dla  dziecka  w ranked: 
        share = max ( int (budget * child.importance), 200 ) 
        zachowane. append ( prune (child, share, summary)) 
        użyte += share 
        jeśli użyte >= budżet: 
            przerywane
     merged = "\n" . join (zachowane) 
    zwracane merged jeśli  len (scalone) // 4 <= budżet w przeciwnym razie summary(scalone, budżet)
Przykład
Widziałeś to już w akcji, jeśli korzystałeś z nowoczesnego asystenta kodowania w dużym repozytorium. Nie wrzuca on po prostu każdego pliku do kontekstu, co byłoby szaleństwem. Zamiast tego buduje drzewo: repozytorium → pakiet → plik → symbol. Podsumowuje każdy poziom z wyprzedzeniem i rozwija tylko gałęzie, które faktycznie edytujesz. Wiesz, dlaczego @-wspominanie pliku nadal wydaje się szybkie w przypadku monorepozytorium z milionem wierszy? Ponieważ drzewo zostało podsumowane wiele godzin temu, gdy nie patrzyłeś.

Więcej informacji na temat wpływu strategii dzielenia na fragmenty na jakość wyszukiwania można znaleźć w artykule Strategie dzielenia na fragmenty w systemach RAG: wnioski z ponad 80 wywiadów GenAI .

Przewodnik po wdrożeniu
Najpierw zdecyduj, jakie są typy węzłów, takie jak reguły systemowe, profil użytkownika, tematy, tury i nadaj im przybliżoną wagę na początek. Nie zastanawiaj się za dużo.
Następnie skonfiguruj zadanie offline, które będzie uruchamiane co jakiś czas i ponownie kompresuje każdą gałąź, w której surowe tokeny przekraczają czterokrotnie jej budżet sumaryczny. To jest idealne rozwiązanie, które znalazłem.
W momencie żądania otrzymujesz globalny budżet tokenów, zaczynasz od 12 tys. i poruszasz się od góry do dołu, zachłannie wciągając najpierw gałęzie o największej gęstości ważności. Tak, zachłannie. To działa.
Rejestruj, co zostało usunięte przy każdym żądaniu. Po dniu lub dwóch pojawią się wzorce. Wtedy dostosujesz swoje wagi ważności do faktycznej dokładności wyszukiwania, a nie do przeczuć.
Jeszcze jedno: stwórz ścieżkę rehydratacji. Jeśli w turze pojawi się temat, który wcześniej wyciąłeś, zamień podsumowanie z powrotem na wersję surową i usuń coś innego, żeby zmieścić się w budżecie. To jak usuwanie zawartości pamięci podręcznej, tylko głupsze i w porządku.
2. Spekulatywne wykonanie narzędzia
Oto coś, co eliminuje opóźnienia: agent planuje, dzwoni do narzędzia, a potem planuje ponownie . To dwa lub trzy kolejne cykle.

Zamiast tego spróbuj spekulatywnego wykonania. Uruchom równolegle dwa lub trzy najbardziej prawdopodobne narzędzia, zanim model w ogóle zdecyduje, którego z nich użyć. Następnie po prostu odrzuć te, których nie wybrał.

Tak, marnujesz trochę mocy obliczeniowej na połączenia, których nie potrzebujesz. Ale kompromisem jest ogromny spadek odczuwalnego opóźnienia dla użytkownika. Całkowicie warto.

To rozwiązanie sprawdza się, gdy opóźnienie narzędzia jest wysokie w porównaniu z czasem przetwarzania modelu – na przykład w przypadku wyszukiwania, plików, interfejsów API kalendarza. Działa również najlepiej, gdy nieużywane wywołanie jest tanie lub nieszkodliwe: tylko do odczytu, idempotentne, buforowalne. Czy narzędzie może wysłać e-mail lub naliczyć kredyty? Nie spekuluj na ten temat.

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 2 — Spekulatywne wykonywanie narzędzi. Moduł kształtowania intencji ocenia narzędzia kandydatów i uruchamia trzy najlepsze równolegle, zanim planista zatwierdzi zmiany. Zanim Kalendarz wygra, jego wynik jest już „gorący”; pozostałe dwa są buforowane lub usuwane. Oś czasu na dole porównuje szeregowe (810 ms) ze spekulatywnymi (490 ms), co oznacza 40% redukcję opóźnienia, którą udało się uzyskać dzięki dwóm dodatkowym wywołaniom tylko do odczytu. (Obraz wygenerowany przy użyciu sztucznej inteligencji).
import asyncio 
z typing import Awaitable, Callable, Dict, Any 

async def speculative_dispatch ( 
    intent : str, 
    tool_scores : Dict[str, float ], 
    tools : Dict[str, Callable[[str], Awaitable[Any]]], 
    k : int = 3 , 
) -> Dict[str, Any]: 
    top = sorted (tool_scores. items (), key=lambda x : -x[ 1 ])[:k] 
    tasks = {name: asyncio. create_task (tools[name](intent)) for name, _ in top} 
    results: Dict[str, Any] = {} 
    for name, task in tasks. items (): 
        try : 
            results[name] = wait asyncio. wait_for (task, timeout= 2.0 ) 
        except (asyncio.TimeoutError, Exception ) as e: 
            results[name] = { "_error" : str (e)} 
    return results 

# planista może teraz wybrać zwycięzcę spośród wyników bez czekania na drugą turę
Przykład
Prawdopodobnie czułeś to, nie zdając sobie z tego sprawy. Asystenci głosowi i narzędzia typu „copilot” z „szybkim pasem” robią to cały czas.

Załóżmy, że pytasz asystenta kalendarza: „Czy mam jutro czas na lunch z Mayą?”. System nie czeka, aż modelka opracuje plan. Spekulująco pobiera z Twojej skrzynki odbiorczej wszystkie dane z kalendarza, status wolny/zajęty i kilka ostatnich wzmianek Mayi, jednocześnie i równolegle.

Zanim model zdecyduje, którego wyniku narzędzia faktycznie potrzebuje? Te dane są już ciepłe w pamięci. To jak magia. To po prostu sprytne zgadywanie.

Przewodnik po wdrożeniu
Zacznij od czegoś prostego: oznacz każde narzędzie jego zachowaniem idempotentnym, tylko do odczytu lub powodującym skutki uboczne. Spekuluj tylko o pierwszych dwóch. Nigdy nie zgaduj, co do czegoś, co wysyła e-maila lub zapisuje dane do bazy danych.
Następnie wytrenuj mały klasyfikator lub po prostu odczytaj logity z modelu routingu, aby uzyskać prawdopodobieństwo użycia narzędzi dla danego komunikatu użytkownika. Nie musi być idealnie.
Uruchamiaj narzędzia z listy top-k spekulacyjnie. Ustaw ścisłe limity czasowe dla każdego narzędzia i globalny limit budżetowy. Trzy równoczesne wywołania zazwyczaj wystarczą.
Buforuj wyniki spekulacyjne z krótkimi TTL. Nawet jeśli model nieznacznie zmieni zdanie, niemalże błędne ponowne planowanie może nadal wykorzystać dane.
Na koniec śledź wskaźnik trafności spekulacji jako pierwszorzędny wskaźnik. Jeśli masz poniżej 50%, albo Twoje k jest za wysokie, albo klasyfikator źle zgaduje. Napraw to, zanim dodasz więcej złożoności.
3. Osadzanie wykrywania dryfu
Wyjaśnijmy sobie jedno: magazyny wektorów to nie bazy danych. To artefakty statystyczne. Ich geometria zależy wyłącznie od modelu osadzania, który je wygenerował.

Co się więc stanie, gdy ten model zostanie po cichu zaktualizowany? Albo gdy zmieni się dystrybucja danych? Albo dodasz nową zawartość, która w niczym nie przypomina starej? Twój indeks zacznie cię okłamywać. Najpierw po cichu, a potem nagle.

Wykrywanie dryfu traktuje osadzenia jak każdą inną funkcję uczenia maszynowego. Śledź centroidy, wariancje i histogramy odległości parami w czasie. Ustaw obwiednię. Ostrzegaj, gdy elementy wykroczą poza nią.

Nie dążysz do perfekcji. Próbujesz złapać dzień, w którym wskaźnik odtwarzania spadnie o 30%, zanim użytkownicy zaczną narzekać.

Aby uzyskać szerszą odpowiedź na pytanie, kiedy zasoby wektorowe są w ogóle odpowiednimi prymitywami, zobacz: „ Przestań wybierać między wektorem a grafem. Real Production AI Needs Three Databases” .

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 3 — Wykrywanie dryfu osadzania. Próbka ostatnich osadzania jest porównywana z 30-dniową bazą za pomocą testów PSI i KS. Gdy sygnał dryfu przekroczy próg alarmowy, system powiadamia o wezwaniu, zanim przywołanie pobierania zostanie przerwane. Detektor traktuje osadzanie jak każdą inną funkcję uczenia maszynowego: śledzone, dystrybucyjne i podlegające alertom.
import numpy jako np. 
z scipy.stats import ks_2samp 

def population_stability_index ( oczekiwano : np.ndarray, rzeczywisto : np.ndarray, bins : int = 10 ) -> float : 
    hist_e, edge = np. histogram (oczekiwano, bins=bins) 
    hist_a, _ = np. histogram (rzeczywisto, bins=edges) 
    pe = hist_e / max (hist_e. sum (), 1 ) 
    pa = hist_a / max (hist_a. sum (), 1 ) 
    pe = np. clip (pe, 1e-6 , None) 
    pa = np. clip (pa, 1e-6 , None) 
    return  float (np. sum ((pa - pe) * np. log (pa / pe))) 

def drift_signal ( baseline : np.ndarray, recent : np.ndarray) -> dict: 
    # rzutuj na skalar przez normę; w praktyce wykonuj rzutowanie na wymiar lub PCA
     b_norms = np.linalg. norm (baseline, axis= 1 ) 
    r_norms = np.linalg. norm (recent, axis= 1 ) 
    psi = population_stability_index (b_norms, r_norms) 
    ks_stat, p = ks_2samp (b_norms, r_norms) 
    return { "psi" : psi, "ks_stat" : ks_stat, "p_value" : p}
Przykład
Zespół ds. wyszukiwania klientów, z którym współpracowałem, wysłał kiedyś w piątek „drobną” zmianę w modelu osadzania. Wydawało się to niegroźne.

Wskaźnik zapamiętania zapytań z długiego ogona spadł o około 18%. Nikt tego nie zauważył do poniedziałku. Dlaczego? Ponieważ ich wskaźniki trafności były generowane w trybie cotygodniowego zadania wsadowego. Mieli więc cały weekend złych wyników wyszukiwania, zanim ktokolwiek podniósł alarm.

Przeprowadzone w ten weekend testy wykrywające dryf pojazdu pozwoliłyby na wykrycie zdarzenia w czasie krótszym niż cztery godziny.

Przewodnik po wdrożeniu
Oto lżejsza wersja, która mogłaby ich uratować:

Najpierw przetestuj 1–5% przychodzących osadzeń w magazynie z ruchomymi oknami. Parquet w pamięci obiektów jest w porządku. Nie przesadzaj z inżynierią.
Zachowaj dwa okna: okno bazowe (np. 30 dni) i okno aktualne (24 godziny).
Raz na godzinę obliczaj PSI dla każdego wymiaru i testu KS na podstawie przewidywanych norm. To wszystko.
Powiadom kogoś, jeśli PSI > 0,25 lub wartość p w KS spadnie poniżej progu. Nie powiadamiaj o wszystkim, tylko o tych, które rzeczywiście śmierdzą.
Najważniejsze: powiąż alert z podręcznikiem, który zawiera „sprawdź, czy wersja modelu osadzenia została wdrożona po cichu”. Mówię poważnie. To jest główna przyczyna w 80% przypadków. Zajmij się tym na początku.
4. Trasowanie uwzględniające budżet tokenów
Nie każde zapytanie zasługuje na Twój najlepszy model. Wiesz o tym. Niektóre zapytania wymagają wnioskowania na poziomie o3. Inne po prostu potrzebują szybkiej i taniej odpowiedzi.

Ale routing oparty wyłącznie na intencji pozostawia pieniądze na lodzie. Dlaczego? Ponieważ intencja nie określa, jak długi będzie wynik. A długość wyniku to połowa równania kosztów.

Routing token-budżet ocenia zarówno koszt wejściowy , jak i przewidywany koszt wyjściowy. Następnie wybiera najtańszy model, który nadal może osiągnąć cel jakościowy dla tego celu.

Najtrudniejszą częścią jest kalibracja przewidywanej długości danych wyjściowych. Używamy małego modelu regresji dla osadzeń intencji. Jeśli niedoszacowasz długości, będziesz kierować trudne zapytania do tanich modeli i matryc jakościowych. Przeszacowasz? Tracisz pieniądze na drogie modele dla łatwych pytań. Jeśli zrobisz to dobrze, będziesz szybki i oszczędny.

Ta sama dyscyplina kosztowa ma zastosowanie w przypadku infrastruktury danych. Zobacz: „ Odziedziczyłem rachunek w wysokości 140 tys. dolarów w formie płatka śniegu: trzy miesiące później wynosił 38 tys. dolarów”, a ten sam schemat zastosowano w przypadku obliczeń.

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 4 — Routing uwzględniający budżet tokena. Router szacuje zarówno koszt wejściowy, jak i przewidywaną długość wyjściową, a następnie wybiera najtańszy model, który spełnia cel jakościowy (SLO). W tym przypadku najtańszy model nie osiąga minimalnego poziomu 0,80, a model premium jest przesadą, więc wygrywa model średni. W przypadku 100 żądań, ten routing pozwala zaoszczędzić 93% w porównaniu z modelem wyłącznie premium i 49% w porównaniu z modelem wyłącznie średnim, przy zachowaniu jakości. (Obraz wygenerowany za pomocą sztucznej inteligencji).
z klas danych importuj klasę danych 
z typowania importuj listę 

@dataclass
 class Model : 
    name : str 
    cost_ in : float # $ na 1 tys. tokenów wejściowych 
    cost_ out : float 
    quality : float # 0 .. 1 skalibrowane względem wstrzymanego eval 

def expected_cost( model : Model, tokens_ in : int, tokens_out_ est : int) -> float : 
    return (tokens_in / 1000 ) * model.cost_in + (tokens_out_est / 1000 ) * model.cost_out 

def route( models : List[Model], tokens_ in : int, tokens_out_ est : int, quality_ floor : float): 
    eligible = [m dla m w modelach jeśli m.quality >= quality_floor] 
    jeśli nie  eligible : 
        eligible = [max(modele, klucz=lambda m : m.quality)] 
    return min(eligible, klucz=lambda m : oczekiwany_koszt(m, tokeny_przychodzące, tokeny_wychodzące_najbardziej))
Przykład
Można to zaobserwować cały czas w przypadku botów odwodzących uwagę klientów.

Weźmy „gdzie jest mój pakiet”. To może 30 tokenów wejściowych, 80 tokenów wyjściowych. Niska niejednoznaczność. Mały, tani model obsługuje to za ułamki centa. Gotowe.

Porównajmy to teraz z wieloakapitową eskalacją dotyczącą uszkodzonej przesyłki międzynarodowej z załącznikami. Zupełnie inna bajka. To wymaga ponad 600 tokenów rozumowania i znacznie większego modelu.

Router nie zgaduje. Analizuje przewidywaną długość sygnału wyjściowego i odpowiednio wyznacza trasy. Ten sam cel (obsługa klienta), zupełnie inne koszty. O to właśnie chodzi.

Przewodnik po wdrożeniu
Zbuduj zestaw kalibracyjny: 2000 reprezentatywnych żądań z etykietami o jakości modelu.
Wytrenuj mały regresor na (intent_embedding, input_length) → expected_output_length.
Zdefiniuj piętra jakościowe dla każdej klasy intencji (np. fakturowanie = 0,85, FAQ = 0,65).
Przekieruj każde żądanie i zapisz wybrany model oraz rzeczywistą długość danych wyjściowych.
Dopasowuj regresor co tydzień; dokładność wyznaczania tras maleje w miarę zmiany zachowania użytkownika.
5. Ocena modelu cienia
Testowanie A/B nowego modelu na rzeczywistym ruchu jest przerażające i powolne. Co jeśli pojawi się coś żenującego? A co jeśli po prostu będzie wolniejsze?

Ewaluacja cienia rozwiązuje ten problem. Uruchamiasz model kandydata na kopii rzeczywistego ruchu, tych samych danych wejściowych, wszystkiego identycznego, ale nigdy nie pokazujesz jego wyników użytkownikom. Następnie porównujesz jego reakcje z tym, co faktycznie zrobiło środowisko produkcyjne.

Otrzymujesz dane ze świata rzeczywistego bez ryzyka. Bez rozgniewanych klientów, bez powiadomień na pagerze.

Najtrudniej jest zdefiniować „zgodność”. Dokładne dopasowanie ciągu znaków jest bezużyteczne w przypadku wyników generatywnych. Dlatego korzysta się z oceny LLM lub oceny podobieństwa semantycznego, z dodatkowymi, wyrywkowymi kontrolami przeprowadzanymi przez człowieka. Nie jest to idealne rozwiązanie, ale jest o wiele lepsze niż ślepe zaufanie.

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 5 — Ocena modelu cienia. Wycinek ruchu na żywo jest rozwidlany. Produkcja obsługuje użytkownika normalnie; kandydat cienia uruchamia to samo żądanie w trybie „odpal i zapomnij”. Porównywarka ocenia zgodność semantyczną, opóźnienie i wskaźnik odrzuceń. Gdy wskaźnik wygranych utrzymuje się powyżej progu 60% dla wszystkich klas intencji przez wystarczającą liczbę próbek, kandydat jest gotowy do wysłania. Zerowe ryzyko dla użytkownika. (Obraz wygenerowany za pomocą sztucznej inteligencji).
import asyncio 
z typing import  Callable , Awaitable, Any 

async  def  shadow_call ( 
    prod_fn: Callable [[ str ], Awaitable[ str ]], 
    shadow_fn: Callable [[ str ], Awaitable[ str ]], 
    judge_fn: Callable [[ str , str , str ], Awaitable[ float ]], 
    prompt: str , 
    log,
 ): 
    prod_task = asyncio.create_task(prod_fn(prompt)) 
    shadow_task = asyncio.create_task(shadow_fn(prompt)) 
    prod = wait prod_task 

    async  def  evaluate (): 
        try : 
            shadow = wait asyncio.wait_for(shadow_task, timeout= 10.0 ) 
            score = wait judge_fn(prompt, prod, shadow) 
            log({ "prompt" : prompt, "prod" : prod, "shadow" : shadow, "score" : score}) 
        except Exception as e: 
            log({ "prompt" : prompt, "shadow_error" : str (e)}) 

    asyncio.create_task(evaluate()) 
    return prod
Przykład
Oto coś, czego duzi dostawcy interfejsów API nie reklamują: zanim dodadzą nową wersję modelu do domyślnego aliasu, najprawdopodobniej od kilku tygodni uruchamiają ją jako kopię bieżącego aliasu domyślnego.

Wewnętrzne pulpity nawigacyjne są wypełnione porównaniami zgodności semantycznej, opóźnieniami na p95 i p99, wskaźnikami odrzuceń, a nawet danymi z downstreamu, takimi jak wskaźniki ponownych prób użytkowników. Monitorują to wszystko.

Dopiero gdy cień wydaje się twardy jak skała, w końcu zmieniają pseudonim. Bez dramatów, bez niespodzianek. Po prostu nudna, ostrożna weryfikacja.

Przewodnik po wdrożeniu
Dodaj klienta cienia do warstwy wnioskowania z częstotliwością próbkowania (zacznij od 5%).
Wywołanie shadow call należy uruchomić i zapomnieć, aby nigdy nie blokowało ścieżki użytkownika.
Zbuduj sędziego: mały egzamin LLM z oceną „udzielał odpowiedzi zarówno w formie symulacji, jak i symulacji” w skali 1–5, a także dokładne dopasowanie w przypadku pól strukturalnych.
Wyświetl pulpit nawigacyjny ze wskaźnikiem wygranych, różnicą opóźnień i różnicą odmów.
Awansuj cień do poziomu kandydata dopiero po zebraniu co najmniej 50 tys. próbek i stabilnych zwycięstwach we wszystkich klasach intencji.
6. Unieważnienie pamięci podręcznej metodą probabilistyczną
Semantyczne pamięci podręczne są wspaniałe. Dopóki nie przestaną.

Zapisana w pamięci podręcznej odpowiedź na pytanie „Jaka jest nasza polityka zwrotów?” jest w porządku przez miesiąc. To praktycznie nic nie zmienia. Ale pytanie „Czy nowe ceny już obowiązują?” jest trujące po godzinie, jeśli się go nie spłucze.

Unieważnianie probabilistyczne nadaje każdemu wpisowi w pamięci podręcznej wartość TTL zależną od zawartości, opartą na rzeczywistej zmienności obiektu. Następnie, od czasu do czasu, ponownie oblicza odpowiedź w ramach TTL, aby wcześnie wykryć dryft.

Płacisz niewielki podatek od przeliczania. W zamian możesz agresywnie buforować, unikając przypadkowego podawania nieaktualnych, szkodliwych odpowiedzi. Warto.

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 6 — Probabilistyczne unieważnianie pamięci podręcznej. Każda odpowiedź w pamięci podręcznej jest klasyfikowana według zmienności, która ustala TTL. W ramach TTL, każde trafienie powoduje rzut małą kostką (tutaj p = 0,04) w celu cichego ponownego obliczenia. Jeśli nowa odpowiedź różni się, system usuwa całe sąsiedztwo semantyczne, a nie tylko klucz. Rezultat: agresywne buforowanie bez nieaktualności, około 4 razy tańsze niż buforowanie bez buforowania przy tej samej świeżości. (Rysunek wygenerowany za pomocą sztucznej inteligencji).
import random , time

 def adaptive_ttl(volatility: float) -> int: 
    # zmienność w  0. .1 , TTL w sekundach 
    return int( 60 + ( 1 - volatility) * 86400 * 7 ) # 1  min .. ~ 1 tydzień 

def cache_get_or_compute(cache, key, compute, volatility): 
    entry = cache.get(key) 
    if entry and entry[ "expires" ] > time . time (): 
        # ponowna walidacja probabilistyczna 
        revalidate_prob = volatility * 0.05 
        if  random . random () < revalidate_prob: 
            fresh = compute() 
            if fresh != entry[ "value" ]: 
                cache.evict_family(key) # usuń powiązane wpisy 
                cache.set(key, { "value" : fresh, 
                                "expires" : time . time () + adaptive_ttl(volatility)}) 
                return fresh 
        return entry[ "value" ] 
    fresh = compute() 
    cache.set(key, { "value" : fresh, "expires" : time . time () + adaptive_ttl(volatility)}) 
    return fresh
Przykład
Znany mi chatbot cenowy robi to dobrze. Buforuje „ile kosztuje plan X” z długim TTL. Stabilny, prawie bez zmian.

Ale „czy w ten weekend jest jakaś wyprzedaż”? To ma krótki TTL i wysokie prawdopodobieństwo ponownej walidacji. Zmienne.

Kiedy wyprzedaż faktycznie się rozpoczyna, sondy probabilistyczne wychwytują zmianę w ciągu kilku minut. Następnie uruchamia się schemat eksmisji rodziny, a powiązane zapytania, takie jak „jakieś zniżki teraz?”, również zostają odświeżone, a nie tylko te konkretne.

Przewodnik po wdrożeniu
Zbuduj klasyfikator zmienności: mały model, który każdemu zapytaniu przypisuje ocenę 0–1 w zależności od tego, „jak bardzo wrażliwa na czas jest ta odpowiedź”.
Ustaw TTL jako funkcję monotoniczną zmienności, wysokiej zmienności, krótkiego TTL.
Po trafieniu na pamięć podręczną należy pobrać próbkę probabilistycznie na podstawie zmienności, aby wykonać ponowne obliczenia w trybie cichym.
W przypadku niezgodności usuń klaster wpisów w pamięci podręcznej, które mają wspólnych semantycznych sąsiadów, a nie tylko jeden klucz.
Podstawowym celem pomiaru poziomu aktywności jest śledzenie współczynnika zatrucia pamięci podręcznej i niezgodności na trafienie.
7. Destylacja na zimno
W każdym produkcie AI 80% ruchu przechodzi przez 20% możliwości. Reszta, długi ogon, jest praktycznie nieużywana.

Ale te rzadkie umiejętności wciąż muszą działać. Nie można ich po prostu porzucić. Jeśli zostawisz je w swoim dużym, drogim modelu, wydasz pieniądze na funkcje, które prawie nigdy nie działają.

Destylacja na ścieżce zimnej rozwiązuje ten problem. Kompresujesz te rzadko używane umiejętności do małego specjalisty. Dopracowujesz, kwantyzujesz, zmniejszasz koszty. Następnie kierujesz tam ruch na ścieżce zimnej.

Twój duży model obsługuje nowość i złożone przypadki brzegowe. Mały specjalista zajmuje się długim ogonem.

Rezultat? Obniżasz rachunek za wnioskowanie. Jakość na tych zimnych ścieżkach ledwo się zmienia, ponieważ rzadkie rzeczy okazały się na tyle powtarzalne, że można je było skompresować.

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 7 — Destylacja na ścieżce zimnej. Ruch podąża za krzywą Zipfa. 80% wolumenu znajduje się w 20% możliwości; długi ogon pokrywa większość powierzchni. Gorący ruch trafia do dużego modelu. Zimny ​​ruch trafia do specjalisty 4B int8, z bramką zaufania, która w razie potrzeby się cofa. Czteroetapowy proces offline (przechwytywanie, filtrowanie, SFT, kwantyzacja) tworzy specjalistę. Rezultat: 94% taniej na zimne żądanie, 68% niższy p95, tylko 1,3% spadek jakości. (Obraz wygenerowany za pomocą sztucznej inteligencji).
# przygotowanie danych: zbieranie śladów ścieżki zimnej z dużego modelu, a następnie dostrajanie małego modelu

 import json 
from datasets import Dataset 

def build_distillation_set ( trace_path : str) -> Dataset: 
    examples = [] 
    with open ( trace_path ) as f: 
        for line in f: 
            row = json. loadings ( line) 
            if row. get ( "path" ) == "cold"  and row. get ( "quality" ) >= 0.85 : 
                examples. append ( { 
                    "input" : row[ "prompt" ], 
                    "output" : row[ "completion" ], 
                }) 
    return Dataset. from_list (przykłady) 

# trenuj pseudokod 
# trainer = SFTTrainer(model=small_model, train_dataset=build_distillation_set("traces.jsonl")) 
# trainer.train() 
# kwantyzuj do int8, wdróż za routerem, który wysyła tutaj intencje ścieżki zimnej
Przykład
Weźmy na przykład asystentów ds. segregacji e-maili. Znasz te pytania: „Czy to prośba o spotkanie? Oferta handlowa? Pilny problem klienta?”. Tego typu klasyfikacja jest bardzo trudna do ujednolicenia.

Duży model wyszkolił klasyfikator.Następnie klasyfikator działa na procesorze za ułamek kosztów i obsługuje 90% poczty przychodzącej. Model rozszerzony? Zarezerwowany dla tych chaotycznych, niejednoznacznych 10%, które wymagają rzetelnego uzasadnienia.

Przewodnik po wdrożeniu
Oto jak to zrobić:

Najpierw zinstrumentuj ruch w swoim dużym modelu za pomocą etykiet intencji i wskaźników jakości. Musisz wiedzieć, co się faktycznie dzieje.
Następnie zidentyfikuj ścieżki „zimne”. Szukaj intencji, w których wolumen jest niski, ale jakość jest spójna. To są Twoje cele.
Zbierz od 5000 do 50 000 wysokiej jakości uzupełnień na ścieżkę zimną. Wykorzystaj to jako dane treningowe.
Dopracuj mały model bazowy, obejmujący od 3 do 8 miliardów parametrów. Następnie agresywnie go skwantyzuj. Zrób to tanio i szybko.
Na koniec dodaj bramkę zaufania. Jeśli mały specjalista nie jest pewien swojej odpowiedzi, wróć do dużego modelu. To zapewni Ci bezpieczeństwo bez konieczności uruchamiania dużego modelu przy każdym żądaniu.
8. Kompozycja funkcji strumieniowych
Wyobraź sobie, że Twój proces wykonuje trzy czynności pod rząd. LLM A tworzy plan. Następnie LLM B wykonuje krok pierwszy. Następnie LLM C podsumowuje wynik. Płacisz pełną cenę za każdy kolejny krok.

Strumieniowanie kompozycji to zmienia. Gdy tylko tokeny LLM A zaczną wypływać, LLM B zaczyna je konsumować. Nie czeka na cały plan. Potrzebuje tylko fragmentu, który jest wystarczająco stabilny, aby go przeanalizować.

Kluczem jest traktowanie każdego etapu LLM jako transformatora strumieniowego, a nie funkcji wsadowej. Jeśli zrobisz to poprawnie, całkowity czas zegara ściennego będzie zbliżony do opóźnienia najwolniejszego etapu, a nie sumy opóźnień wszystkich trzech.

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 8 — Kompozycja funkcji strumieniowej. Trzy etapy LLM narysowane jako równoległe linie metra na wspólnej osi czasu. Każda stacja to emisja tokenów; linie przerywane to przekazania. Executor rozpoczyna się przed zakończeniem Planera, a Summarizer rozpoczyna się przed zakończeniem Executora. Całkowity zegar ścienny zbliża się do najwolniejszego etapu, a nie do sumy. 35% szybciej, z czasem do pierwszego tokena około 4 razy krótszym. (Obraz wygenerowany za pomocą sztucznej inteligencji).
import asyncio 
z typing import AsyncIterator 

async  def  parse_stable_chunks ( stream: AsyncIterator[ str ], delimiter: str = "\n" ): 
    buf = "" 
    async  for chunk in stream: 
        buf += chunk 
        while delimiter in buf: 
            line, buf = buf.split(delimiter, 1 ) 
            yield line 
    if buf: 
        yield buf 

async  def  compose ( stage_a, stage_b, prompt ): 
    a_stream = stage_a(prompt)               # zwraca asynchroniczny iter tokenów 
    async  for plan_step in parse_stable_chunks(a_stream): 
        async  for out_token in stage_b(plan_step): 
            yield out_token
Przykład
Systemy tłumaczeń w czasie rzeczywistym już to robią. Strumień mowy na tekst przesyła wiersz po wierszu do modelu tłumaczenia. Nie czeka na pełny zapis.

Pewnie zauważyłeś ten efekt. Przetłumaczone napisy opóźniają się o jakieś 800 milisekund, a nie 5 sekund. Tak działa kompozycja strumieniowa.

Przewodnik po wdrożeniu
Oto jak to zrobić.

Najpierw zaplanuj etapy swojego potoku. Znajdź naturalną granicę „stabilności parsowania” między nimi. Mogą to być klucze JSON, podziały wiersza lub zakończenia zdań.
Opakuj każdy etap w interfejs generatora asynchronicznego. Dzięki temu możesz przesyłać tokeny w miarę ich pojawiania się.
Zbuduj chunker, który będzie emitował dane natychmiast po osiągnięciu stabilnej granicy. Nie czekaj na całość.
Dodaj warstwę buforującą dla etapów wymagających przewidywania przyszłości. Niektóre modele tłumaczeń wymagają pełnych zdań, aby działać poprawnie.
Na koniec mierz czas do pierwszego tokena, a nie tylko całkowite opóźnienie. To właśnie tam znajdziesz prawdziwe korzyści.
9. Debugowanie odtwarzania trajektorii
Agenci podejmują decyzje sekwencyjnie. Gdy coś pójdzie nie tak, samo przejrzenie logów rzadko wystarcza. Trzeba cofnąć się w czasie i odtworzyć kroki agenta jak film.

Funkcja odtwarzania trajektorii traktuje każde uruchomienie agenta jako deterministyczne nagranie. Rejestrujesz dane wejściowe modelu, dane wejściowe narzędzia, ziarna generatora liczb losowych (RNG) i znaczniki czasu. Następnie możesz odtworzyć uruchomienie offline i interweniować w dowolnym momencie. Zmienić dane wyjściowe narzędzia. Sprawdzić, czy agent się przywróci.

Problem w tym, że modele LLM są niedeterministyczne, nawet w temperaturze zero. Prawdziwe odtwarzanie wymaga albo tworzenia migawek wyników modelu w momencie ich wystąpienia, albo akceptowania reprodukcji rozmytej. Większość zespołów tworzy migawki. To dodatkowa przestrzeń dyskowa, ale oszczędza godziny debugowania.

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 9 — Debugowanie odtwarzania trajektorii. Lewy panel: przebieg agenta na żywo zarejestrowany krok po kroku. Krok 04 zamówił niewłaściwy kod SKU, ale kolejne kroki były nadal wykonywane. Prawy panel: sesja odtwarzania. Inżynier modyfikuje odpowiedź narzędzia kroku 04 i uruchamia go ponownie, izolując przyczynę problemu jako częściowy kod JSON w match_sku. Interfejs wiersza poleceń ( trajctlCLI) na dole pokazuje powierzchnię roboczą: ładowanie, inspekcja, rozwidlenie, różnicowanie. (Obraz wygenerowany za pomocą sztucznej inteligencji).
import json, time, uuid 

class  Recorder : 
    def  __init__ ( self, path ): 
        self.path = path 
        self.run_id = str (uuid.uuid4()) 
        self.steps = [] 

    def  record ( self, step_type, inputs, outputs ): 
        self.steps.append({ 
            "ts" : time.time(), 
            "type" : step_type, 
            "inputs" : inputs, 
            "outputs" : outputs, 
        }) 

    def  flush ( self ): 
        with  open ( f" {self.path} / {self.run_id} .jsonl" , "w" ) as f: 
            for step in self.steps: 
                f.write(json.dumps(step) + "\n" ) 

class  Replayer : 
    def  __init__ ( self, path ): 
        self.steps = [json.loads(l) for l in  open (path)] 

    def  step ( self, idx, override= None ): 
        zwróć override, jeśli override nie jest  None , w przeciwnym razie self.steps[idx][ "outputs" ]  
Przykład
Jeden z moich znajomych miał agenta, który zamówił niewłaściwy kod SKU. Dlaczego? Błędnie przeanalizował częściową odpowiedź narzędzia JSON.

Zamiast zgadywać, odtworzyli całą trajektorię. Zmutowali odpowiedź narzędzia na poprawiony kod JSON i ponownie uruchomili agenta. Agent postąpił właściwie. To dało im pewność, że mogą wprowadzić niewielką poprawkę stabilności JSON zamiast przepisywać całego agenta.

Przewodnik po wdrożeniu
Oto jak zbudować funkcję odtwarzania trajektorii.

Najpierw zinstrumentuj każde wywołanie modelu i narzędzia. Rejestruj dane wejściowe, wyjściowe i indeks kroku. Będziesz potrzebować wszystkiego.
Przechwyć również źródła losowości. Temperatura próbkowania, ziarna, ponowne próby. Bez nich Twoje powtórki nie będą stabilne.
Przechowuj trajektorie w formacie JSONL, używając identyfikatora uruchomienia. Są one bardzo dobrze skompresowane, więc nie musisz martwić się o miejsce na dane.
Zbuduj interfejs wiersza poleceń (CLI) lub pomocnika notatnika, który wczytuje trajektorię i pozwala modyfikować dowolny krok. Zmień dane wyjściowe narzędzia. Edytuj odpowiedź modelu. Zobacz, co się stanie.
Na koniec dodaj tryb „rozwidlenia z kroku N”. Odtwarza on kroki od 0 do N dokładnie tak, jak się wydarzyły, a następnie pozwala agentowi działać na żywo od tego momentu. Idealne do testowania poprawek.
10. Głębokość wyszukiwania adaptacyjnego
Stałe pobieranie top_k równe 5 to relikt. Miało to sens, gdy nie wiedzieliśmy lepiej, ale dziś to po prostu marnowanie okazji.

Niektóre zapytania są jednoznaczne. Potrzebują dokładnie dwóch fragmentów. Inne są niejasne i chaotyczne. Tym przydałoby się dwadzieścia.

Adaptacyjne pobieranie odczytuje zapytanie, przewiduje jego poziom trudności i dynamicznie wybiera k. Ale oto równie ważna część: rozszerza lub zawęża również głębokość ponownego rankingu w oparciu o obserwowany rozkład wyników.

Jeśli wynik najlepszego hitu znacznie przewyższa resztę, to już po tobie. Zatrzymaj się jak najszybciej.

Jeśli wszystkie wyniki są zgrupowane, model osadzania działa w trybie zabezpieczającym. Nie wie, co się stanie. To sygnał, żeby przyciągnąć więcej kandydatów.

Aby dowiedzieć się więcej na temat decyzji dotyczących dzielenia na fragmenty, które determinują wygląd tych wyników, zapoznaj się z artykułem Strategie dzielenia na fragmenty w systemach RAG: wnioski z ponad 80 wywiadów GenAI .

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 10 — Głębokość wyszukiwania adaptacyjnego. Stała top_k=5to relikt. Retrieval pobiera pulę kandydatów liczącą 20, a następnie odczytuje rozkład wyników. Duża różnica między szczytem a resztą? Zachowaj 3, pomiń ponowne klasyfikowanie. Ciasne skupisko? Rozszerz do 50 i ponownie klasyfikowaj. Ten sam retrieval, dwie różne głębokości wybrane przez dane. W 300 zapytaniach: +25% odtworzenia, o 30% niższy koszt, zero nowej infrastruktury. (Obraz wygenerowany za pomocą sztucznej inteligencji).
import numpy as np 

def adaptive_k ( scores : list [ float ], min_k : int = 3 , max_k : int = 30 ) -> int : 
    if not scores: 
        return min_k 
    s = np. array ( sorted (scores, reverse=True)) 
    gaps = s[:- 1 ] - s[ 1 :] 
    # znajdź pierwszą dużą przerwę; wszystko przed nią jest zbiorem „pewnym”
     próg = przerwy. średnia () + przerwy. std () 
    dla i, g w enumerate (przerwy): 
        jeśli g > próg i i + 1 >= min_k: 
            return  min (i + 1 , max_k) 
    return  min ( len (s), max_k)
Przykład
Asystent ds. badań prawnych wyszukuje trzy przepisy w odpowiedzi na dobrze sformułowane pytanie dotyczące konkretnego paragrafu, ale rozszerza je do dwudziestu w przypadku niejasnego pytania „co prawo mówi o zakazie konkurencji pracowników w Kalifornii”. Ten sam wyszukiwacz, różna głębokość, diametralnie różna jakość odpowiedzi.

Przewodnik po wdrożeniu
Zawsze wykorzystuj większą ilość ryb niż zamierzasz użyć (np. 50).
Oblicz statystyki różnicy wyników i wybierz naturalne odcięcie.
Dodaj twardą podłogę i sufit, kaby zapobiec przypadkom patologicznym.
Jeśli posiadasz narzędzie do rerankingu, uruchom je tylko na adaptacyjnym zestawie top, a nie na wszystkich 50.
Rejestruj (query, chosen_k, downstream_quality)i dostosowuj próg odstępu w trybie offline.
11. Szablony komunikatów federacyjnych
Kiedy dziesięć zespołów pisze polecenia, powstaje dziesięć różnych wersji „bądź pomocny i unikaj krzywdy”. Rozchodzą się one od siebie. Zasady bezpieczeństwa w jednym zespole są bardziej rygorystyczne niż w drugim. Ton jest różny. To jeden wielki bałagan.

Szablony komunikatów federacyjnych traktują komunikaty jak kod. Są współdzielone, wersjonowane, komponowalne i centralnie zarządzane dla bezpieczeństwa i tonu. Zespoły nadal mogą je jednak dostosowywać lokalnie.

Architektura przypomina konfigurację mikrousług. Mamy warstwę bazową, którą dziedziczą wszyscy. Następnie nakładkę organizacji. Następnie nakładkę zespołu. Na końcu deltę poszczególnych funkcji. Etap kompilacji spłaszcza je wszystkie w momencie wdrożenia. Bez niespodzianek w czasie wykonywania.

Naciśnij Enter lub kliknij, aby zobaczyć obraz w pełnym rozmiarze

Rysunek 11 — Szablony komunikatów federacyjnych. Komunikaty są traktowane jak konfiguracja warstwowa. Zablokowana warstwa bazowa (bezpieczeństwo, reguły odmowy) stanowi fundament. Organizacja nadaje ton i głos marki. Zespół koduje reguły domeny. Funkcja stosuje deltę dla każdej funkcjonalności. Krok kompilacji spłaszcza wszystkie cztery do jednego artefaktu z haszowaną zawartością, z kolorowymi paskami wskazującymi, z której warstwy pochodzi każdy wiersz. Gdy łata zabezpieczenia bazy w celu wykonania nowego jailbreaku, każda aplikacja podrzędna dziedziczy poprawkę przy kolejnym wdrożeniu. (Obraz wygenerowany za pomocą sztucznej inteligencji).
z klas danych importuj  klasę danych z importu listy typów @dataclass class PromptLayer : nazwa: str     zawartość: str     wersja: str def flatten(layers: List[PromptLayer]) -> str:     # najpierw baza, na końcu najbardziej szczegółowe; późniejsze warstwy mogą nadpisywać sekcje za pomocą tagów     sections = {} dla warstwy w warstwach: dla fragmentu w layer.content.split( "\n##" ): jeśli nie chunk.strip(): kontynuuj             nagłówek, _, ciało = chunk.partition( "\n" )             sections[header.strip()] = ciało.strip() return "\n\n" .join(f "## {k}\n{v}" dla k, v w sections.items())
   


 
     






    
        
            
                


      
Przykład
Wiele korporacyjnych platform AI już to robi, nie nazywając tego wyszukanymi nazwami. Publikują „monit platformy”, z którego dziedziczą wszystkie ich wewnętrzne aplikacje.

Gdy zespół ds. bezpieczeństwa aktualizuje warstwę bazową, aby obsłużyć nowy wzorzec jailbreaku, każda aplikacja podrzędna automatycznie otrzymuje poprawkę przy kolejnym wdrożeniu. Koniec z przeszukiwaniem czterdziestu repozytoriów w poszukiwaniu tego, kto co skopiował.

Przewodnik po wdrożeniu
Oto jak to skonfigurować.

Wybierz format warstwowy. YAML z nazwanymi sekcjami działa naprawdę dobrze. Przechowuj wszystko w Gicie.
Zbuduj narzędzie do spłaszczania, które deterministycznie rozdziela warstwy i generuje pojedynczy ciąg znaków z hashem zawartości. Użyjesz tego hasha do wykrywania zmian.
Wprowadzaj zmiany w bramkach poprzez przegląd pull requestów. Wymagaj konkretnych recenzentów dla warstw krytycznych dla bezpieczeństwa. Nie pozwól nikomu przemycić zmiany poza procedurą zgodności.
Twórz migawkę spłaszczonego monitu przy każdym wdrożeniu. W ten sposób możesz porównywać wersje i natychmiast przywracać je, jeśli coś się zepsuje.
Na koniec dodaj bramkę ewaluacyjną. Każda zmiana w monicie musi zostać przeprowadzona w oparciu o zestaw regresji przed scaleniem. Zestaw powinien wykrywać typowe tryby awarii, takie jak próby jailbreaku lub niezgodność z marką.
Co nadchodzi w części 2
11 powyższych wzorców to fundamenty. Jeśli je dobrze opanujesz, Twój system sztucznej inteligencji (AI) w produkcji będzie miał realną szansę.

Część 2 obejmuje zestaw zaawansowany: wzorce, które zespoły przyjmują, gdy podstawy są już solidne.

Pętle agentów uwzględniające ciśnienie zwrotne. Zapobieganie wzajemnemu spalaniu się systemów wieloagentowych pod obciążeniem.
Mapowanie powierzchni halucynacji. Dokładna wiedza o położeniu modelu, zanim dowiedzą się o tym użytkownicy.
Wyniki oznaczone pochodzeniem. Każde roszczenie można prześledzić do jego fragmentu źródłowego.
Głosowanie wielomodelowe oparte na kworum. Kiedy konsensus wygrywa z zaufaniem w modelu jednomodelowym.
Generowanie zakotwiczone w schemacie. Ustrukturyzowane wyniki, które są parsowane za każdym razem.
Kompaktowanie pamięci oparte na rozpadzie. Pozwalanie pamięci agenta zapomnieć łagodnie, a nie katastrofalnie.
