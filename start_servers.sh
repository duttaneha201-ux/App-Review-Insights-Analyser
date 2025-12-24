#!/bin/bash

echo "Starting App Review Insights Servers..."
echo ""

# Start backend API server in background
echo "Starting Backend API Server (port 8000)..."
python run_api_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend dev server
echo "Starting Frontend Dev Server (port 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "Servers starting..."
echo "========================================"
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait








