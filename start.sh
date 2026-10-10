#!/bin/bash
# TrendView83 - Start both backend and frontend

set -e

echo "🚀 Starting TrendView83..."

# Check if backend deps are installed
if [ ! -d "backend/.venv" ] && [ ! -f "backend/requirements.txt" ]; then
    echo "❌ Backend not set up. Run setup first."
    exit 1
fi

# Check if frontend deps are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend not set up. Run setup first."
    exit 1
fi

# Start backend in background
echo "📡 Starting backend on http://localhost:8000..."
cd backend
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "🌐 Starting frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ TrendView83 is running!"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '👋 Stopped'; exit 0" INT
wait