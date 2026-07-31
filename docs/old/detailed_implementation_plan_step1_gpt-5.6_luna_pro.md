<!-- Plan po Kroku 1: GPT-5.6 Luna Pro (openai/gpt-5.6-luna-pro) -->

# Audyt logiki domenowej RAE-Suite

## 0. Zakres i ograniczenia audytu

Audyt opiera się wyłącznie na przedstawionej wersji planu. Nie można potwierdzić pełnej zgodności z `docs/rozwoj-RAE-part-1.md`, ponieważ treść tego dokumentu nie została dołączona, a część nazw w planie jest zastąpiona przez `[PERSON_NAME]` lub `[ADDRESS]`.

Wnioski poniżej wskazują:

- niespójności widoczne w aktualnym planie,
- brakujące pojęcia domenowe,
- niepełne przejścia maszyny stanów,
- niewystarczającą semantykę DTO,
- rekomendowaną wersję rozszerzoną planu.

---

# 1. Ocena ogólna

Plan poprawnie identyfikuje główne problemy:

- fałszywy `SUCCESS`,
- deklaratywne, a nie egzekwowane `CapabilityContract`,
- zbyt statyczny `ModelRouter`,
- niedojrzały `CognitivePlanner`,
- brak pełnej pętli: planowanie → wykonanie → dowód → walidacja → eskalacja,
- potrzebę event sourcingu i replay.

Jednocześnie obecny model jest jeszcze bardziej **listą komponentów i zadań implementacyjnych** niż spójnym modelem domenowym. Brakuje jednoznacznego rozdzielenia:

1. intencji wykonania,
2. planu wykonania,
3. autoryzacji,
4. fizycznego wykonania,
5. dowodu wykonania,
6. weryfikacji dowodu,
7. decyzji końcowej,
8. kompensacji lub eskalacji.

Najpoważniejszy problem polega na tym, że `ExecutionReceipt` jest traktowany jako artefakt techniczny, podczas gdy powinien być **niezmiennym dowodem domenowym**, na podstawie którego dopiero można nadać zadaniu stan `VERIFIED_SUCCESS`.

---

# 2. Lista dostrzeżonych luk i rekomendacji

## 2.1. Brak rozdzielenia stanu zadania od stanu wykonania

W planie występuje `SUCCESS`, ale nie ma jasności, czy oznacza on:

- zakończenie procesu agenta,
- zakończenie kroku,
- poprawne wykonanie narzędzia,
- przejście testów,
- zaakceptowanie wyniku przez Quality Gate,
- podpisanie i zweryfikowanie `ExecutionReceipt`.

Rekomendacja: rozdzielić co najmniej trzy poziomy:

```text
Task lifecycle
  CREATED → PLANNED → AUTHORIZED → EXECUTING → VERIFIED_SUCCESS

Step lifecycle
  PENDING → DISPATCHED → RUNNING → OBSERVED → VERIFIED / FAILED

Decision lifecycle
  PROPOSED → EVALUATED → ACCEPTED / REJECTED / ESCALATED
```

Nie należy używać jednego `SUCCESS` dla wszystkich tych znaczeń.

---

## 2.2. `SUCCESS` nie może być nadawany na podstawie samego exit code

`exit_code = 0` nie dowodzi, że:

- wykonano właściwe polecenie,
- wykonano je w odpowiednim workspace,
- testy objęły oczekiwany zakres,
- artefakty pochodzą z tego samego wykonania,
- nie przekroczono uprawnień lub zasobów,
- diff odpowiada badanemu commitowi,
- wynik jest aktualny względem wersji repozytorium.

Rekomendacja: uznać `exit_code` za jeden z faktów obserwacyjnych, a nie za warunek wystarczający.

Minimalna reguła:

```text
VERIFIED_SUCCESS =
  execution completed
  AND command provenance is valid
  AND workspace/base revision is valid
  AND capability policy was enforced
  AND required checks passed
  AND artifacts are content-addressed
  AND receipt signature/hash is valid
  AND Quality Gate accepted the result
```

---

## 2.3. `ExecutionReceipt` nie zawiera pełnej semantyki dowodu

Obecne DTO jest dobrym szkicem, ale nie wystarcza do audytowalnego wykonania.

Brakuje między innymi:

- wersji bazowej repozytorium,
- commit hash i workspace identity,
- canonical hash polecenia oraz parametrów,
- identyfikatora wykonawcy/runtime,
- wersji obrazu kontenera lub środowiska,
- faktycznych limitów i faktycznego zużycia zasobów,
- zakresu testów i ich kompletności,
- listy artefaktów z hashami, rozmiarami i typami,
- informacji o cache,
- informacji o retry,
- resultu Quality Gate,
- naruszeń polityki,
- podpisu lub mechanizmu integralności,
- czasu rozpoczęcia i zakończenia,
- przyczyny niepowodzenia,
- korelacji z eventami i trace.

Dodatkowo `git_diff_hash` jest niejednoznaczny. Należy określić, czy hash dotyczy:

- patcha względem `base_commit`,
- drzewa plików,
- finalnego commita,
- listy zmienionych plików,
- kanonicznego serializowanego diffu.

Rekomendacja: hash powinien być obliczany nad jednoznacznie zdefiniowaną reprezentacją kanoniczną.

---

## 2.4. `capability_compliance: true` jest zbyt słabym polem

Boolean nie pozwala ustalić:

- jakie ograniczenia obowiązywały,
- które operacje podlegały kontroli,
- czy kontrola była pre- czy post-execution,
- jakie były limity,
- jakie było faktyczne zużycie,
- czy wystąpiło naruszenie,
- czy ograniczenie zostało wymuszone przez sandbox,
- czy wynik jest wiarygodny mimo naruszenia.

Rekomendacja: zastąpić boolean strukturą:

```json
{
  "policy_id": "cap-policy-v3",
  "contract_version": "openclaw-2.1",
  "required_capabilities": ["repo.read", "repo.write", "test.execute"],
  "granted_capabilities": ["repo.read", "repo.write", "test.execute"],
  "enforcement_mode": "HARD",
  "limit_observations": [],
  "compliance_status": "COMPLIANT"
}
```

---

## 2.5. Brak rozróżnienia `FAILED`, `BLOCKED`, `REJECTED`, `CANCELLED` i `ABORTED`

Są to różne sytuacje domenowe:

- `FAILED` — wykonanie wystartowało, ale zakończyło się błędem,
- `BLOCKED` — wykonanie nie mogło wystartować z powodu polityki, braku uprawnień lub zasobów,
- `REJECTED` — plan lub wynik został odrzucony przez politykę albo Quality Gate,
- `CANCELLED` — użytkownik/system anulował zadanie,
- `ABORTED` — wykonanie przerwano awaryjnie,
- `EXPIRED` — przekroczono deadline lub TTL,
- `PARTIALLY_COMPLETED` — część planu została wykonana, ale całość nie została potwierdzona.

Bez tych stanów system będzie zmuszony kodować różne znaczenia w jednym `FAILED`.

---

## 2.6. Brak stanów oczekiwania

W systemie agentowym wykonanie często nie kończy się od razu. Potrzebne są stany:

- `WAITING_FOR_APPROVAL`,
- `WAITING_FOR_RESOURCE`,
- `WAITING_FOR_DEPENDENCY`,
- `WAITING_FOR_TOOL`,
- `WAITING_FOR_HUMAN`,
- `PAUSED`.

Bez nich retry i wznowienie będą mylone z ponownym uruchomieniem.

---

## 2.7. Ryzyko jest klasyfikowane zbyt statycznie

Plan słusznie przewiduje dynamiczną klasyfikację ryzyka, ale umieszcza ją dopiero w P2. To zbyt późno.

Ryzyko jest potrzebne już przed:

- wyborem modelu,
- autoryzacją planu,
- przyznaniem capability,
- uruchomieniem narzędzia,
- zatwierdzeniem automatycznej naprawy.

Ponadto ryzyko nie powinno być tylko wartością `LOW/MEDIUM/HIGH`. Potrzebne są:

- wynik ryzyka,
- klasyfikacja,
- powody,
- wersja polityki,
- źródła danych,
- confidence,
- zakres obowiązywania,
- moment ponownej oceny.

Ryzyko powinno być monotonicznie podwyższane, gdy plan zyskuje nowe skutki uboczne, ale jego obniżenie powinno wymagać jawnej rekalkulacji i nowej autoryzacji.

---

## 2.8. Brak rozróżnienia ryzyka planu, kroku i operacji

Przykład:

- całe zadanie: `MEDIUM`,
- krok modyfikujący konfigurację produkcyjną: `CRITICAL`,
- polecenie `git diff`: `LOW`.

Jedna klasyfikacja na poziomie zadania jest niewystarczająca.

Rekomendacja:

```text
task risk
plan risk
step risk
tool operation risk
residual risk after controls
```

Efektywne ryzyko wykonania powinno być co najmniej:

```text
effective_risk =
  max(task_risk, plan_risk, step_risk, operation_risk)
```

z możliwością podwyższenia przez reguły typu „always critical”.

---

## 2.9. Model routingu nie opisuje pełnej decyzji

`ModelRoutingDecision` zawiera wybrany model, fallback i koszt, ale nie zapisuje, dlaczego inne modele zostały odrzucone oraz jakie ograniczenia obowiązywały.

Brakuje:

- listy kandydatów,
- wyników kandydatów,
- funkcji scoringowej i jej wersji,
- confidence,
- wymaganych narzędzi,
- ograniczeń bezpieczeństwa i prywatności,
- lokalizacji danych,
- wymaganej latencji,
- budżetu całkowitego,
- maksymalnej liczby retry,
- reguły fallbacku,
- powodów odrzucenia,
- wersji metryk z RAE-Lab,
- faktycznego modelu użytego po wykonaniu,
- informacji o zmianie routingu w trakcie zadania.

Należy odróżnić:

```text
RoutingDecision — decyzja przed wywołaniem modelu
ModelInvocationReceipt — dowód faktycznego wywołania
```

Wybrany model może nie być modelem faktycznie użytym, np. wskutek timeoutu, fallbacku lub awarii dostawcy.

---

## 2.10. Brak budżetu i polityki kosztowej jako obiektu domenowego

`estimated_cost_usd` nie wystarcza. System potrzebuje:

- budget per task,
- budget per step,
- budget per tenant/project,
- budget for retries,
- budget for escalation,
- actual cost,
- reservation,
- refund/unused budget,
- policy on exceeding budget.

W przeciwnym razie router może podjąć lokalnie poprawną decyzję, która przekroczy globalny budżet zadania.

---

## 2.11. Capability Contract nie jest jeszcze kontraktem egzekwowalnym

Samo egzekwowanie limitów w `ToolGateway` nie rozwiązuje całego problemu. Trzeba zdefiniować:

- kto nadaje capability,
- na jaki czas,
- dla jakiego taska, stepu i workspace,
- czy capability można delegować,
- czy jest revocable,
- jakie są warunki użycia,
- jak wygląda odmowa,
- jak zapisuje się dowód odmowy,
- czy narzędzia są transakcyjne lub kompensowalne.

Capability powinno być związane z konkretnym kontekstem:

```text
tenant_id
project_id
task_id
plan_id
step_id
workspace_id
principal_id
policy_version
expiry
```

---

## 2.12. Brak ochrony przed TOCTOU

Jeżeli plan i autoryzacja są tworzone w jednym stanie repozytorium, a wykonanie odbywa się później, repozytorium lub polityka mogą się zmienić.

Należy sprawdzać przed wykonaniem:

- czy `base_commit` nadal obowiązuje,
- czy plan nie został zmodyfikowany,
- czy capability nadal jest ważne,
- czy polityka nie zmieniła wersji,
- czy ryzyko nie wzrosło,
- czy workspace nie został zmieniony przez inny proces.

---

## 2.13. Brak idempotencji na poziomie operacji

Klucz P3:

```text
tenant_id + project_id + trace_id + step_id + action + input_hash
```

jest dobrym kierunkiem, ale prawdopodobnie niewystarczającym.

Należy uwzględnić co najmniej:

- `workspace_id`,
- `tool_version`,
- `policy_version`,
- `base_revision`,
- `attempt_no`,
- `idempotency_key`,
- typ operacji,
- semantykę efektu ubocznego.

Idempotencja odczytu jest prostsza niż idempotencja zapisu. Dla operacji nieodwracalnych wymagany jest mechanizm:

- deduplikacji,
- lease,
- fencing token,
- kompensacji,
- albo jawnego `non_idempotent=true`.

---

## 2.14. Brak modelu kompensacji

Jeżeli plan wykonuje kilka operacji i krok 4 kończy się błędem, system musi wiedzieć:

- czy cofnąć kroki 1–3,
- czy pozostawić częściowy rezultat,
- czy utworzyć rollback plan,
- czy wymagać akceptacji człowieka,
- czy rollback sam wymaga nowej autoryzacji.

Wymagany jest model `CompensationPlan` lub przynajmniej relacja:

```text
ExecutionStep → compensating_step
```

---

## 2.15. Quality Gate i Quality Tribunal nie mają jasno zdefiniowanego autorytetu

Nie jest określone:

- czy Tribunal może nadać `VERIFIED_SUCCESS`,
- czy tylko rekomenduje decyzję,
- czy są testy obowiązkowe niezależnie od głosowania,
- jak traktowane są sprzeczne wyniki,
- czy jeden model może zawetować wynik,
- jaki jest próg quorum,
- co dzieje się przy braku quorum,
- czy Tribunal może zaakceptować wynik z ostrzeżeniami,
- jak kalibrowane są wagi modeli.

Rekomendacja: Tribunal powinien być **dowodem walidacyjnym**, ale nie powinien omijać twardych invariantów wykonania. Żaden consensus LLM nie może zastąpić nieudanego testu obowiązkowego ani naruszenia capability.

---

## 2.16. Phoenix Auto-Repair może tworzyć nieograniczoną pętlę

Brakuje:

- maksymalnej liczby iteracji,
- budżetu napraw,
- wzrostu ryzyka po każdej iteracji,
- warunku stagnacji,
- wykrywania regresji,
- odróżnienia nowego problemu od tego samego problemu,
- konieczności ponownej autoryzacji po zmianie zakresu.

Każda automatyczna naprawa powinna tworzyć nową wersję planu lub nowy `repair_attempt`, a nie nadpisywać poprzedni dowód.

---

# 3. Spójność modelu, maszyny stanów i ryzyka

## 3.1. Ocena zgodności z `rozwoj-RAE-part-1.md`

Na podstawie samego planu nie można potwierdzić pełnej zgodności z dokumentem źródłowym. Można jednak wskazać następujące warunki, które muszą być spełnione:

| Obszar | Stan w planie | Ocena |
|---|---|---|
| MAES / MinimumAuditableEvent | Wspomniane, ale bez pełnego kontraktu | Niepełne |
| Task State Machine | Wspomniana, brak jawnego diagramu i guardów | Niepełne |
| Risk Classification | Jest, ale dynamiczna wersja dopiero w P2 | Niespójne czasowo |
| Capability Contracts | Są deklaratywne, plan przewiduje hard enforcement | Kierunek poprawny |
| Execution Proof | `ExecutionReceipt` jest zbyt ub