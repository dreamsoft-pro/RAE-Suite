#!/bin/bash
# 🚀 RAE MODERNIZATION BOOTSTRAP - Operacja Lustro (Node 1)
NODE_IP="100.68.166.117"
NODE_USER="operator"

echo "🛡️  Initializing Operacja Lustro in HARD FRAMES mode..."

# 1. Stop conflicting ScreenWatcher containers if running
ssh ${NODE_USER}@${NODE_IP} "cd ~/screenwatcher_project && docker compose down" 2>/dev/null

# 2. Start Full RAE Suite with Hard Frames profile
echo "🏗️  Starting RAE Suite (Hard Frames)..."
ssh ${NODE_USER}@${NODE_IP} "cd ~/RAE-Suite && docker compose --profile hard-frames up -d"

# 3. Start Dreamsoft Modernization Stack
echo "💎 Starting Dreamsoft Modernization Stack..."
# Note: Assuming Dreamsoft is configured to not conflict or we manage its ports here.
ssh ${NODE_USER}@${NODE_IP} "cd ~/dreamsoft_factory && docker compose up -d"

# 4. Context Injection via RAE V2 API
echo "🧠 Injecting Modernization Mission Context..."
ssh ${NODE_USER}@${NODE_IP} "docker exec rae-api-dev curl -s -X POST http://localhost:8000/v2/memories/ \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: 53717286-fe94-4c8f-baf9-c4d2758eb672' \
  -d '{
    \"project\": \"dreamsoft_modernization\",
    \"layer\": \"working\",
    \"content\": \"MISSION BOOTSTRAP: Hard Frames Active. Focus: AngularJS to Next.js Migration, Code Quality & Audit.\",
    \"human_label\": \"Operacja Lustro Mission\"
  }'"

echo "✅ Operacja Lustro is LIVE on Node 1."
