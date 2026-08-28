 ### 🗺️ 1. Główne Schematy Przepływu Danych w RAE (Scenariusze Architektoniczne)                                                                                                    
                                                                                                                                                                                     
  W architekturze RAE-Suite zdefiniowane są 4 komplementarne scenariusze przepływu zadań:                                                                                            
                                                                                                                                                                                     
                              [ Zapytanie / Zadanie Agenta ]                                                                                                                         
                                            │                                                                                                                                        
                                            ▼                                                                                                                                        
                      ┌───────────────────────────────────────────┐                                                                                                                  
                      │      RAE Model Router & Risk Classifier   │                                                                                                                  
                      │  (Ocena ryzyka R1-R6, kosztu i opóźnienia)│                                                                                                                  
                      └─────────────────────┬─────────────────────┘                                                                                                                  
                                            │                                                                                                                                        
                 ┌──────────────────────────┴──────────────────────────┐                                                                                                             
                 ▼                                                     ▼                                                                                                             
       [ ZADANIA PROSTE / LOKALNE ]                          [ ZADANIA ZŁOŻONE / KRYTYCZNE ]                                                                                         
       • Koszt: $0.00                                        • Wnioskowanie, architektura, audyt                                                                                     
       • Klasa ryzyka: R1 - R3                               • Klasa ryzyka: R4 - R6                                                                                                 
       • Ekstrakcja, tagowanie, RAG, podsumowania            • Głosowanie konsensusem (Quality Tribunal)                                                                             
                 │                                                     │                                                                                                             
                 ▼                                                     ▼                                                                                                             
    ┌───────────────────────────────┐                 ┌─────────────────────────────────┐                                                                                            
    │     LOKALNE WĘZŁY GPU (Ollama)│                 │      CHMURA (OpenRouter API)    │                                                                                            
    │  • Node 1 (RTX 4080 SUPER)    │                 │  • DeepSeek-R1 (Reasoning)      │                                                                                            
    │  • Laptop Primary (GPU)       │                 │  • Claude 3.5 Sonnet / Opus     │                                                                                            
    │  Modele: Bielik 11B, Qwen 3.5 │                 │  • Gemini 3.7 Flash (Grounding) │                                                                                            
    └───────────────────────────────┘                 └─────────────────────────────────┘                                                                                            
                 │                                                     │                                                                                                             
                 └──────────────────────────┬──────────────────────────┘                                                                                                             
                                            ▼                                                                                                                                        
                           ┌─────────────────────────────────┐                                                                                                                       
                           │  Cloud RAE Memory Storage       │                                                                                                                       
                           │  (Zapis śladów i telemetrii)    │                                                                                                                       
                           └─────────────────────────────────┘                                                                                                                       
  ──────                                                                                                                                                                             
  #### 📌 Scenariusz A: Kaskadowy Router Kosztowo-Jakościowy (Pareto / Quantile-Budget Routing)                                                                                      
                                                                                                                                                                                     
  • Lokalizacja: model_router.py, models_mesh_registry.yaml.                                                                                                                         
  • Zasada działania:                                                                                                                                                                
      • Każde zadanie klasyfikowane jest pod kątem klasy ryzyka (RiskClass.R1 do RiskClass.R6) oraz estymowanego budżetu tokenów i limitu opóźnienia (p95).                          
      • Niskie ryzyko (R1-R3): Rutowane w 100% lokalnie na GPU (koszt = $0.00, opóźnienie < 200 ms).                                                                                 
      • Wysokie ryzyko (R4-R6): Zlecane do modeli reasoning w chmurze przez OpenRouter (deepseek/deepseek-r1, claude-3.5-sonnet, gemini-3.7-flash).                                  
      • Failover / Fallback: Jeśli chmura OpenRouter zgłasza błąd sieci lub przekroczy budżet, następuje automatyczny spadek do lokalnego modelu na Node 1 / Laptopie.               
                                                                                                                                                                                     
                                                                                                                                                                                     
  #### 📌 Scenariusz B: Hybrydowa Rada Konsensusu (Consensus Councils L2 & L3)                                                                                                       
                                                                                                                                                                                     
  • Lokalizacja: llm_config.yaml.                                                                                                                                                    
  • Zasada działania:                                                                                                                                                                
      • council_l2: Szybki konsensus hybrydowy: Bielik 11B (lokalny) + Qwen 3.5 9B (lokalny) + Gemini 3.7 Flash (chmura).                                                            
      • council_l3 (Quality Tribunal): Głosowanie większościowe 3 modeli dla krytycznych audytów kodu i umów: DeepSeek-R1 8B (Node 1) + DeepSeek-R1 Cloud + Claude 3.5 Sonnet.       
                                                                                                                                                                                     
                                                                                                                                                                                     
  #### 📌 Scenariusz C: Adaptacyjny Router Uczący się (Adaptive Reinforcement Router)                                                                                                
                                                                                                                                                                                     
  • Lokalizacja: adaptive_router.py.                                                                                                                                                 
  • Zasada działania:                                                                                                                                                                
      • Router monitoruje historyczny wskaźnik sukcesu (Success Rate) i czas wykonania dla poszczególnych domen zadań.                                                               
      • Automatycznie przenosi zadania z chmury do modeli lokalnych, gdy lokalny model osiąga wymaganą dokładność (oszczędność kosztów).                                             
  • reflection / low_cost (Zapis pamięci RAE): SpeakLeash/bielik-11b-v3.0-instruct:Q5_K_M lub qwen3.5:9b (Lokalnie).                                                                 
                                                                                                                                                                                     
                                                                                                                                                                                     
  #### 📌 Scenariusz D: Podział Zadań wg Ról Agentowych (Role-Based Assignment)                                                                                                      
                                                                                                                                                                                     
                                                                                                                                                                                     
  • legal_audit / evaluator (Audyt prawny i weryfikacja): Bielik 11B (Polskie prawo) + deepseek-r1:8b (Wnioskowanie).                                                                
  • code_generation / architecture: qwen3.5:9b (Lokalnie) / claude-3.5-sonnet (Chmura).                                                                                              
  ──────                                                                                                                                                                             
  ### 🔧 2. Wprowadzone Zmiany i Aktualizacje Nazw Modeli                                                                                                                            
  Zaktualizowano pliki konfiguracyjne, wprowadzając precyzyjne nazwy aktualnie zainstalowanych modeli:                                                                               
                                                                                                                                                                                     
      • Dodano: local/gemma4-12b (gemma4:12b)                                                                                                                                        
  1. **models_mesh_registry.yaml**:                                                                                                                                                  
      • Dodano: local/bielik-11b (SpeakLeash/bielik-11b-v3.0-instruct:Q5_K_M)                                                                                                        
      • Dodano: local/qwen-3.5-9b (qwen3.5:9b)                                                                                                                                       
      • Dodano: local/deepseek-r1-8b (deepseek-r1:8b)                                                                                                                                
  2. **model_router.py**:                                                                                                                                                            
      • Zaktualizowano domyślny rejestr modeli lokalnych i ich metryki opóźnień quantiles (p50/p95/p99).                                                                             
  3. **llm_profiles.yaml**:                                                                                                                                                          
      • Skonfigurowano profile: cheap_bulk, default, reasoning_legal, cloud_high_tier.                                                                                               
  4. **llm_config.yaml**:                                                                                                                                                            
      • Zaktualizowano strategie default, fast_local, legal_audit, reasoning, council_l2, council_l3.                                                                                
                                                                                                                                                                                     

