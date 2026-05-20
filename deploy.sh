#!/bin/bash
# Coven Traders — Quick Deploy Script

echo "🐾 COVEN TRADERS DEPLOY"
echo "========================"

# 1. Check env
echo "[1/5] Checking environment..."
python3 --version && node --version && npm --version || exit 1

# 2. Install Python deps
echo "[2/5] Installing Python dependencies..."
pip install -q fastapi uvicorn redis websockets pandas numpy ta-lib 2>/dev/null || true

# 3. Install Node deps
echo "[3/5] Installing Node dependencies..."
cd game-frontend && npm install 2>/dev/null && cd ..
cd contracts && npm install 2>/dev/null && cd ..

# 4. Start Redis (if not running)
echo "[4/5] Starting Redis..."
redis-cli ping 2>/dev/null || redis-server --daemonize yes

# 5. Start services
echo "[5/5] Starting services..."
echo "  → Signal Aggregator: python -m signal-aggregator.main"
echo "  → Idle Engine: python -m idle-engine.calculator"
echo "  → Coaching API: uvicorn agent-coaching.api:app --port 8001"
echo "  → Game Frontend: cd game-frontend && npm run dev"
echo ""
echo "🚀 Ready to conquer the Fracture."
