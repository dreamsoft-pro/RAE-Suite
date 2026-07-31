Co jest realnie zaimplementowane

Kod zawiera między innymi:

maszynę stanów zadania i rejestrowanie przejść;
klasyfikację ryzyka oraz decyzje polityk;
kontrakty możliwości dla Phoenix, Hive, Quality i OpenClaw;
filtrowanie kontekstu według poziomu zaufania;
consensus dla operacji wysokiego ryzyka;
izolację przez Git worktree;
obsługę zadań wsadowych;
zdalne wykonywanie przez SSH z lokalnym fallbackiem;
eskalację do Hermesa (a trzeba dodać lub/i opencode);
GitOps;
quality gate;
automatyczną próbę naprawy po naruszeniu zasad architektury.

Ale nie wszystkie „zaawansowane” elementy mają jeszcze głębię sugerowaną przez nazwy

Przykładem jest CognitivePlanner. Klasa rzeczywiście zawiera strukturę drzewa, UCT, adaptacyjną liczbę iteracji i ocenę kroków. Natomiast generowanie hipotez jest obecnie oparte głównie na słowach kluczowych i kilku statycznych zestawach wariantów. Ocena podejścia również używa ręcznie zapisanych heurystyk tekstowych.

Czyli:

mechanizm planera istnieje;
ale nie jest jeszcze pełnym planowaniem opartym na stanie repozytorium, wynikach narzędzi i rzeczywistych symulacjach zmian;
obecne „MCTS/ToT” jest częściowo właściwą strukturą, a częściowo warstwą heurystyczną.

Podobnie ModelRouter ma prawdziwy model danych dla kosztu, jakości, opóźnienia, możliwości narzędzi i maksymalnego ryzyka, ale faktyczny routing sprowadza się obecnie do trzech stałych reguł zależnych od klasy ryzyka. Parametr expected_tokens nie wpływa na wybór modelu, mimo że dokumentacja klasy mówi o routingu kosztowym.

Rejestr modeli również jest statyczny i zawiera profile modeli starszych generacji, więc nie odzwierciedla prawdopodobnie używanych obecnie integracji z OpenRouter, Qwen, DeepSeek, Google, Anthropic i OpenAI.

Korekta mojego poprzedniego wniosku

Nie powinienem był powiedzieć po prostu:

„Nie gonić za nowinkami, tylko stabilizować”.

Lepszy wniosek brzmi:

RAE nie potrzebuje kolejnych powierzchownych modułów, ale potrzebuje nowocześniejszych mechanizmów wewnątrz istniejących modułów.

To istotna różnica.

Nie chodzi o zatrzymanie rozwoju. Chodzi o pogłębianie tego, co już powstało:

zamienić heurystyczny planner na planner pracujący na realnym grafie zależności, kodzie, testach i wynikach wykonania;
zamienić statyczny ModelRouter na routing oparty na historycznych wynikach RAE-Lab;
podłączyć Quality Tribunal do rzeczywistych modeli i kalibrowanych strategii głosowania;
zamienić domyślne „SUCCESS” na sukces potwierdzony artefaktem i testami;
połączyć risk classification z konkretnym zakresem diffu i planowanymi narzędziami;
egzekwować limity z CapabilityContract, a nie tylko je deklarować;
rozdzielić właściwą symulację dry-run od samego wpisania przejścia stanu;
opierać naprawy Phoenix na realnym raporcie jakości, a nie zastępczym komunikacie.

Szczególnie ważne: w obecnym kernelu domyślna ścieżka wykonania ustawia SUCCESS, nawet gdy nie wykonuje żadnej konkretnej operacji. To sugeruje, że najważniejszym kierunkiem nie jest dokładanie nowych agentów, ale domknięcie semantyki wykonania i dowodów sukcesu.

Moja poprawiona ocena strategiczna:

nie wymieniać stacku technologicznego RAE;
nie zamrażać rozwoju funkcjonalnego;
nie mnożyć kolejnych nazwanych warstw bez spięcia ich z runtime;
agresywnie wdrażać nowinki, które pogłębiają planner, routing, pamięć, evals i wykonanie;
odrzucać nowinki, które tylko dodają kolejnego agenta, framework albo protokół bez poprawy wyników.
