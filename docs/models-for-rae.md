zmieniłbym Twoją dziewiątkę na dokładnie 3 stopnie

Każdy stopień ma 3 modele. Żadnej czwartej warstwy.

Stopień	Model	OpenRouter input/output	Rola
I	GLM 5.3 Flash	$0.075 / $0.25	podstawowy coder
I	DeepSeek V4 Flash	$0.05 / $0.16	drugi niezależny coder
I	MiMo V2.5	$0.119 / $0.238	trzeci coder / alternatywne rozwiązanie
II	DeepSeek V4 Pro 0813	$0.66 / $1.98	mocny reviewer/fixer
II	GLM 5.3	$1.17 / $3.96	architektura, trudniejsze refaktoryzacje
II	Kimi K2.7 Code	$0.66 / $3.40	długie zadania coding-agent
III	GPT-5.6 Sol	obecnie od ok. $2 / $10	finalny reviewer / trudne błędy
III	Kimi K3	$2.55 / $12.75	duże repo, long-horizon coding
III	Claude Sonnet 5	$2 / $10	niezależny finalny reviewer

Ceny są bieżące i część jest promocyjna.

STOPIEŃ I — tanie wykonanie

Tu liczy się przede wszystkim bardzo wysoki quality/$.

1. GLM 5.3 Flash

To jest obecnie fenomenalny model codingowy za tę cenę. Z.ai podaje:

Terminal Bench 2.1 — 84.3
DeepSWE — 63.4
NL2Repo — 56.3

i koszt zaledwie $0.075 / $0.25.

2. DeepSeek V4 Flash

Jeszcze tańszy:

$0.05 / $0.16

przy Terminal Bench 2.1 około 82.7. DeepSeek specjalnie dostroił go do agentów codingowych i formatu Codex.

3. MiMo V2.5

Cena około:

$0.119 / $0.238

i 1M kontekstu. Co ciekawe, w aktualnych danych OpenRouter dotyczących użycia do programowania jest obecnie #2, pomiędzy GLM 5.3 Flash i DeepSeek V4 Flash.

To jest absurdalnie tani pierwszy stopień.

STOPIEŃ II — właściwa analiza i review

Tutaj modele dostają już:

patch,
kod źródłowy,
wyniki testów,
uwagi stopnia I,

i mają szukać błędów, poprawiać rozwiązanie oraz kwestionować decyzje poprzednich modeli.

1. DeepSeek V4 Pro 0813

To według mnie jeden z największych bargainów całego OpenRoutera.

Cena:

$0.66 / $1.98

a DeepSeek dla obecnej wersji GA podaje:

Terminal Bench 2.1: 87.9

oraz bardzo dobre wyniki w zadaniach repo/agent.

Przy tej cenie używałbym go bardzo dużo.

2. GLM 5.3

Nie Flash, tylko pełny:

$1.17 / $3.96

Z.ai pozycjonuje go bezpośrednio pod complex software engineering i long-horizon agent tasks, a 5.3 poprawia coding względem bardzo dobrego GLM 5.2.

3. Kimi K2.7 Code

I tutaj ważna korekta.

K2.7 Code zamiast K2.6.

Moonshot podaje względem K2.6:

Kimi Code Bench: 50.9 → 62.0
ProgramBench: 48.3 → 53.6
MLS Bench Lite: 26.7 → 35.1
około 30% mniej reasoning tokens

czyli jest jednocześnie lepszy i efektywniejszy w kodowaniu.

STOPIEŃ III — finalny arbitraż

I tutaj właśnie wrzuciłbym Kimi K3.

Nie marnowałbym tych modeli na poprawianie prostego CRUD-a. Ich zadaniem powinno być rozstrzyganie sytuacji, kiedy wcześniejsze modele się nie zgadzają albo zmiana jest duża/riskowna.

🥇 GPT-5.6 Sol

Dla czystego codingu nadal dałbym go minimalnie na pierwszym miejscu tej warstwy.

Ma bardzo mocny profil:

Terminal Bench 2.1: 88.8
DeepSWE: około 73
ogromny kontekst,
bardzo dobre wieloetapowe operacje terminalowe.

OpenRouter aktualnie pokazuje go od około $2 / $10 w promocyjnym routingu.

🥈 Kimi K3

Tu poprawiam poprzednią rekomendację zdecydowanie.

Dla Twojego zastosowania K3 jest modelem III stopnia, nie niszowym dodatkiem.

Jego najmocniejsze strony idealnie pokrywają się z RAE/Dreamsoft:

duże repo → wiele plików → terminal → test → błąd → poprawka → kolejny test → dalsza iteracja.

OpenRouter opisuje go dokładnie jako szczególnie mocnego w:

large repositories, tools, debugging, logs, tests, runtime feedback

Ma też 1,048,576 tokenów kontekstu.

🥉 Claude Sonnet 5

Tu też zmieniam poprzednią rekomendację — nie Sonnet 4.6.

Sonnet 5 kosztuje obecnie:

$2 / $10

czyli nawet mniej niż K3, a Anthropic mocno poprawił w nim coding i agentic workflows.

Co ciekawe, wspólne zestawienia Artificial Analysis dają:

Sonnet 5 Coding Index: 71.5
Kimi K3: 76.2

więc K3 jest surowo mocniejszy, ale Sonnet 5 pozostaje bardzo wartościowym niezależnym recenzentem.

Dlaczego nie Claude Opus 5?

Bo pytałeś o jakość/cena, a nie tylko jakość.

Opus 5 kosztuje:

$5 / $25

przy Sonnet 5:

$2 / $10.

Do permanentnego używania w systemie 3-stopniowym nie widzę wystarczającego uzasadnienia ekonomicznego.

Jak widzę Twoją architekturę

Najbardziej sensowny mechanizm byłby bardzo prosty:

STOPIEŃ I — GENERATE

GLM 5.3 Flash
DeepSeek V4 Flash
MiMo V2.5

↓ wyniki + diff + testy

STOPIEŃ II — REVIEW / REPAIR

DeepSeek V4 Pro 0813
GLM 5.3
Kimi K2.7 Code

↓ poprawiona wersja + wykryte problemy + testy

STOPIEŃ III — JUDGE

GPT-5.6 Sol
Kimi K3
Claude Sonnet 5

↓ finalny consensus

dopiero wtedy merge / acceptance.

To jest dokładnie 3-stopniowa hierarchia, a nie „worker pool + reviewer pool” z jakimiś dodatkowymi wyjątkami.

I jest jeszcze jeden bardzo ważny element: modele w kolejnych stopniach pochodzą z różnych rodzin. Nie chciałbym mieć np. trzech wariantów Qwen albo trzech wariantów DeepSeek oceniających siebie nawzajem, bo mogą dzielić te same błędy.

Moja aktualna 9-ka tylko do kodowania

I: GLM-5.3-Flash → DeepSeek-V4-Flash → MiMo-V2.5
II: DeepSeek-V4-Pro-0813 → GLM-5.3 → Kimi-K2.7-Code
III: GPT-5.6-Sol → Kimi-K3 → Claude-Sonnet-5

I tak — Kimi K3 zdecydowanie powinien być w najwyższym stopniu. W poprzedniej odpowiedzi umieszczenie K2.6 zamiast K3/K2.7 Code było zbyt konserwatywne, szczególnie że interesuje Cię wyłącznie software engineering.
