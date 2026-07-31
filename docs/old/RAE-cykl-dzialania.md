Antigravity jako agent wykonawczy jest obecnie racjonalnym wyborem.

OpenCode przestaje być konieczny jako główna warstwa orkiestracji. Nadal pozostaje wartościowy jako:

alternatywny executor,
narzędzie do niezależnego odtworzenia zadania,
środowisko dla modeli nieobsługiwanych przez Antigravity,
kontrolna implementacja w testach porównawczych,
fallback przy awarii lub regresji Antigravity.
Twój obecny cykl
Antigravity → pisze
DeepSeek R1 → recenzuje
Kimi K3 → zatwierdza

To jest już znacznie lepszy układ niż:

Antigravity → pisze
DeepSeek → recenzuje
Antigravity → zatwierdza własną pracę

Usunąłeś najważniejszy problem: autor nie jest ostatnim sędzią własnej implementacji.

Jednak do pełnej zgodności z planem RAE trzy etapy nie powinny być jedynie trzema kolejnymi promptami. Powinny stanowić role działające na odrębnych, kryptograficznie związanych artefaktach.

1. Antigravity powinien dostarczać pakiet wykonawczy

Poza kodem powinien zwracać:

{
  "task_id": "...",
  "plan_hash": "sha256:...",
  "base_commit": "...",
  "diff_hash": "sha256:...",
  "changed_files": [],
  "commands_executed": [],
  "tests_executed": [],
  "test_results": {},
  "unresolved_risks": [],
  "environment_fingerprint_before": "...",
  "environment_fingerprint_after": "..."
}

Plan wymaga wiązania zatwierdzeń z identyfikatorem zadania, hashem planu, hashem diffu oraz wersjami polityki. Zmiana diffu lub środowiska powinna automatycznie unieważniać wcześniejsze recenzje.

To oznacza, że po poprawce wykonanej przez Antigravity:

stare zatwierdzenie DeepSeek i Kimi przestaje obowiązywać.

Nie można zatwierdzić diffu A, następnie zmienić go na diff B i zachować decyzji dotyczącej A.

2. DeepSeek R1 jako recenzent — tak, ale nie jako jedyne źródło prawdy

DeepSeek R1 dobrze pasuje do:

wykrywania błędów logicznych,
analizy współbieżności,
sprawdzania przypadków brzegowych,
kwestionowania założeń implementacji,
porównania implementacji z wymaganiami,
generowania kontrprzykładów.

Nie powinien jednak oceniać wyłącznie opisu Antigravity. Musi otrzymać:

oryginalne zadanie,
obowiązującą wersję planu,
rzeczywisty diff,
wybrane pliki kontekstowe,
wyniki CI,
raport testów,
wyniki SonarQube,
wyniki testów mutacyjnych,
listę niezaliczonych i pominiętych kontroli.

Plan słusznie wymaga niezależnych pakietów dowodowych i zabrania przenikania dowodów lub opinii między sędziami.

DeepSeek nie powinien widzieć opinii Kimi, a Kimi nie powinien bezrefleksyjnie bazować na narracyjnym podsumowaniu DeepSeek.

3. Kimi K3 nie powinien „zatwierdzać kodu” w znaczeniu absolutnym

Kimi powinien zatwierdzać konkretną decyzję na podstawie pakietu dowodowego:

APPROVE
REJECT
REQUEST_CHANGES
INSUFFICIENT_EVIDENCE
ESCALATE

Najważniejszy stan to:

INSUFFICIENT_EVIDENCE

Bez niego model będzie często odczuwał presję, aby wybrać pomiędzy zatwierdzeniem i odrzuceniem nawet wtedy, gdy nie uruchomiono istotnego testu.

Plan przewiduje podejście fail-closed: brak wymaganych dowodów lub brak obowiązkowego sędziego ma skutkować odrzuceniem, a nie zatwierdzeniem w trybie domniemania poprawności.

Dlatego Kimi powinien zatwierdzić zmianę tylko wtedy, gdy:

wszystkie obowiązkowe bramki deterministyczne przeszły,
hash diffu zgadza się z recenzowanym artefaktem,
DeepSeek nie pozostawił nierozwiązanych problemów blokujących,
testy pokrywają krytyczne zachowanie,
zmiana testów nie osłabia ich skuteczności,
nie nastąpił drift środowiska lub polityki,
nie przekroczono budżetu ryzyka.
4. Kolejność powinna być trochę inna

Nie rekomenduję dosłownie:

Antigravity → DeepSeek → Kimi

Lepsza wersja:

1. RAE: walidacja zadania, polityki, kontraktów i uprawnień
2. Antigravity: analiza i implementacja
3. Deterministyczne bramki:
   - lint
   - type checking
   - unit tests
   - integration tests
   - SonarQube
   - security scanning
   - mutation testing
   - OpenAPI/buf compatibility
   - AST diff testów
4. DeepSeek R1: niezależny adversarial review
5. Antigravity: poprawki wynikające z review
6. Powtórzenie wszystkich deterministycznych bramek
7. DeepSeek lub drugi reviewer: weryfikacja poprawionego diffu
8. Kimi K3: decyzja końcowa
9. RAE: podpisanie zatwierdzenia powiązanego z finalnym diff_hash

Plan jednoznacznie ustanawia zasadę RAE-First: kontrole deterministyczne powinny następować przed kosztownym osądem modeli, a deterministyczne odrzucenie nie powinno generować wywołań trybunału LLM.

To zarówno poprawia jakość, jak i ogranicza koszty.

Najważniejsza wada obecnego układu

Antigravity, DeepSeek R1 i Kimi K3 nadal mogą popełnić ten sam skorelowany błąd, szczególnie gdy:

wymaganie jest źle sformułowane,
diff wygląda logicznie, ale nie odpowiada rzeczywistemu zachowaniu aplikacji,
testy zostały napisane przez autora pod jego własne założenia,
wszystkie modele opierają się na tym samym błędnym podsumowaniu,
modele widzą wcześniejsze opinie i zakotwiczają się na nich,
brakuje testów uruchamianych na rzeczywistym środowisku.

Dlatego modele nie powinny głosować nad „tym, czy kod wygląda dobrze”. Powinny oceniać różne wymiary.

Zalecany podział odpowiedzialności

Antigravity — executor

implementacja,
uruchomienie środowiska,
testy browser/E2E,
przygotowanie artefaktów,
poprawki.

DeepSeek R1 — adversarial reviewer

znajdowanie kontrprzykładów,
logika i edge cases,
współbieżność,
transakcje,
bezpieczeństwo,
zgodność z wymaganiami,
próby obalenia poprawności.

Kimi K3 — approval judge

weryfikacja kompletności dowodów,
kontrola zgodności z planem,
rozstrzyganie uwag recenzenta,
klasyfikacja ryzyka,
decyzja końcowa.

RAE — ostateczny autorytet

uprawnienia,
wersje polityk,
hashe,
quorum,
fail-closed,
idempotencja,
zapis decyzji,
unieważnienie zatwierdzenia przy dryfie.

Plan prawidłowo zakłada, że kontrakty i walidacja muszą poprzedzać efekty uboczne oraz wykonanie spekulatywne.

Czy nadal warto używać OpenCode?

Tak, ale niekoniecznie w głównej ścieżce.

Największą wartość da jako czwarty, opcjonalny element kontrolny:

1. Shadow execution

Dla np. 5–10% zadań:

Antigravity wykonuje implementację produkcyjną
OpenCode niezależnie przygotowuje plan lub alternatywny patch
RAE porównuje oba rozwiązania

Pozwoli to sprawdzić:

który executor generuje mniejsze diffy,
który powoduje mniej regresji,
który lepiej realizuje wymagania,
który wymaga mniej rund poprawek,
który generuje wyższe pokrycie testów,
którego zmiany mają niższą Cognitive Complexity.
2. Fallback executor

Gdy Antigravity:

wpadnie w pętlę,
nie potrafi naprawić testów,
przekracza budżet,
generuje zbyt szeroki diff,
kilkukrotnie wraca z tym samym błędem,

RAE może skierować zadanie do OpenCode z innym modelem.

3. Niezależny reviewer bez dostępu do historii

OpenCode może uruchomić model recenzujący tylko na:

wymaganiu,
finalnym diffie,
minimalnym kontekście repozytorium,
wynikach testów.

Bez historii dyskusji między Antigravity, DeepSeek i Kimi.
