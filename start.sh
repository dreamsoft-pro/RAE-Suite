#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "🚀 Starting RAE Suite v3 Ultra (Silicon Oracle)..."
docker compose up -d

echo "⏳ Waiting for RAE Memory API to be ready..."
until curl -s http://localhost:8000/health > /dev/null; do
    sleep 2
    echo -n "."
done

echo -e "\n✅ RAE Memory API is ONLINE."
echo "🔄 Running Database Migrations..."
docker exec rae-memory-v3 alembic upgrade head

echo "✨ RAE Suite v3 Ultra is fully operational!"
docker ps --filter "name=v3"
