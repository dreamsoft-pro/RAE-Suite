 Wszystkie etapy wdrożenia RAE-Suite v2.9 na chmurze produkcyjnej zostały pomyślnie zaplanowane, wdrożone i zweryfikowane.                                                          
  ──────                                                                                                                                                                             
  ### 🌐 1. Podsumowanie Wdrożenia i Dostępne Adresy                                                                                                                                 
                                                                                                                                                                                     
   Komponent                                 │ Adres URL / Endpoint                      │ Protokół & Zabezpieczenie                     │ Status
  ───────────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────────┼───────────────────────────────────────────
   Web Portal & Dashboard                    │ https://rae.dreamsoft.pro[1]              │ Let's Encrypt TLS (HTTPS) + Keycloak PKCE SSO │ 🟢 100% LIVE
   Health Check                              │ https://rae.dreamsoft.pro/health[2]       │ Public / Monitoring                           │ 🟢 Healthy (v2.9.0)
   OpenAPI / Swagger                         │ https://rae.dreamsoft.pro/docs[3]         │ HTTP Bearer / API Key                         │ 🟢 Dostępny
   Memory API (v2)                           │ https://rae.dreamsoft.pro/v2/memories/    │ X-API-Key / Keycloak Bearer JWT               │ 🟢 Dostępny
   MCP SSE Supervisor                        │ https://rae.dreamsoft.pro/sse / /mcp      │ MCP Protocol / Streamable HTTP SSE            │ 🟢 Dostępny                               
                                                                                                                                                                                     
  [1]: https://rae.dreamsoft.pro https://rae.dreamsoft.pro                                                                                                                           
  [2]: https://rae.dreamsoft.pro/health https://rae.dreamsoft.pro/health                                                                                                             
  [3]: https://rae.dreamsoft.pro/docs https://rae.dreamsoft.pro/docs                                                                                                                 
  ──────                                                                                                                                                                             
  ### 🔑 2. Dane Uwierzytelniania (Keycloak SSO)                                                                                                                                     
                                                                                                                                                                                     
  • Keycloak Auth Server: https://auth.cloud.printworks.pl                                                                                                                           
  • Realm: master                                                                                                                                                                    
  • Użytkownik: lesniowskig@gmail.com (login również grzegorz)                                                                                                                       
  • Hasło: 042121LMlmlmRae!@#$                                                                                                                                                       
  • Konfiguracja Klientów OIDC:                                                                                                                                                      
      • rae-portal: Klient publiczny (PKCE S256), przekierowania do https://rae.dreamsoft.pro/callback.                                                                              
      • rae-memory-api: Klient Bearer-only do walidacji tokenów JWT.                                                                                                                 
  • Dodawanie nowych użytkowników: W panelu Keycloak (https://auth.cloud.printworks.pl/admin/master/console/) możesz w dowolnym momencie ręcznie dodawać użytkowników, nadawać im    
  role lub przypisywać do organizacji.                                                                                                                                               
  ──────                                                                                                                                                                             
  ### 📦 3. Migracja Danych z Laptopa do Chmury                                                                                                                                      
                                                                                                                                                                                     
  • Baza Relacyjna & Wektorowa PostgreSQL (pgvector):                                                                                                                                
      • Wszystkie 493 wspomnienia, powiązania grafowe, audyty ISO 42001/27001 oraz konfiguracje tenantów zostały pomyślnie wyeksportowane z lokalnego kontenera i zaimportowane do   
      klastra (rae-postgres na wolumenie Ceph RBD SSD).                                                                                                                              
  • Baza Wektorowa Qdrant:                                                                                                                                                           
      • Snapshot kolekcji memories (wielowektorowe przestrzenie dense:384 oraz nomic:768) został przesłany i odzyskany w chmurowym zasobie rae-qdrant.                               
  
  ──────
  ### 🤖 4. Odciążenie Zasobów Chmury & Integracja Modeli Zewnętrznych (Node1, Node3, Laptop)
  
  Zgodnie z wymogiem braku GPU na węzłach chmurowych:
  
  1. Chmura: Działa w trybie Zero-GPU (ultralekkie zużycie RAM/CPU, brak ciężkich modeli ML w kontenerach).
  2. Infrastruktura Obliczeniowa (cluster.yaml):
      • Node 1 (Lumina - GPU RTX 4080): 100.68.166.117 (zadań ciężkich i benchmarków).
      • Node 3 (Piotrek - Ollama 128GB RAM): 100.109.20.121:11434 / http://172.30.15.11:11434.
      • Laptop (Grzegorz - Local LLM): http://100.77.51.15:11434.
  
  ──────
  ### ⚙️ 5. Konfiguracja Agentów AI (Laptop / Inne Urządzenia)
  
  Aby Antigravity, Claude, Cursor, VS Code lub agenci zewnętrzni łączyli się z chmurą:
  
    RAE_API_URL=https://rae.dreamsoft.pro
    RAE_API_KEY=rae_master_secret_key_cloud_2026
    RAE_TENANT_ID=53717286-fe94-4c8f-baf9-c4d2758eb672
    RAE_PROJECT_NAME=dreamsoft_factory
  
  #### Przykładowy test połączenia MCP / API z dowolnego urządzenia:
  
    import httpx
  
    headers = {
        "X-API-Key": "rae_master_secret_key_cloud_2026",
        "X-Tenant-Id": "53717286-fe94-4c8f-baf9-c4d2758eb672",
    }
  
    response = httpx.get(
        "https://rae.dreamsoft.pro/v2/memories/?project=dreamsoft_factory&limit=5",
        headers=headers,
    )
    print("Status:", response.status_code, "Memories count:", len(response.json().get("results", [])))


