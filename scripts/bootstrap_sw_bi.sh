#!/bin/bash
# 🚀 RAE BI BOOTSTRAP - ScreenWatcher Evolution (Node 1)
NODE_IP="100.68.166.117"
NODE_USER="operator"

echo "🛡️  Initializing ScreenWatcher BI in HARD FRAMES mode..."

# 1. Stop conflicting Modernization containers if running
ssh ${NODE_USER}@${NODE_IP} "cd ~/dreamsoft_factory && docker compose down" 2>/dev/null

# 2. Start Full RAE Suite with Hard Frames profile
echo "🏗️  Starting RAE Suite (Hard Frames)..."
ssh ${NODE_USER}@${NODE_IP} "cd ~/RAE-Suite && docker compose --profile hard-frames up -d"

# 3. Start ScreenWatcher + Metabase
echo "📊 Starting ScreenWatcher & Metabase (Standalone Container)..."
echo "🚀 Starting Apache Superset (Commercial-Ready BI)..."
ssh ${NODE_USER}@${NODE_IP} "cd ~/screenwatcher_project && docker compose up -d"

# 4. Context Injection via RAE V2 API
echo "🧠 Injecting BI Mission Context..."
ssh ${NODE_USER}@${NODE_IP} "docker exec rae-api-dev curl -s -X POST http://localhost:8000/v2/memories/ \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' \
  -d '{
    \"project\": \"screenwatcher_bi_evolution\",
    \"layer\": \"working\",
    \"content\": \"MISSION BOOTSTRAP: Hard Frames Active. Focus: NoCode BI & Semantic Layer.\",
    \"human_label\": \"Silicon Oracle BI Mission\"
  }'"

echo "✅ ScreenWatcher BI is LIVE at http://${NODE_IP}:3001 (Metabase) and http://${NODE_IP}:8088 (Superset)"
