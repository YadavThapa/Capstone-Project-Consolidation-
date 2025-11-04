#!/bin/bash
# Unix/Linux/macOS Shell Script to Start Django Server
# Run: chmod +x start-server.sh && ./start-server.sh

echo "=========================================================="
echo "   DJANGO NEWS APPLICATION - STARTING SERVER"
echo "=========================================================="
echo

# Check if database exists
if [ ! -f "db.sqlite3" ]; then
    echo "⚠️  WARNING: Database not found!"
    echo "Please run setup-unix.sh first"
    echo
    exit 1
fi

echo "🚀 Starting Django development server..."
echo
echo "🌍 The website will be available at:"
echo "   http://127.0.0.1:8000/"
echo
echo "⏹️  Press Ctrl+C to stop the server"
echo "=========================================================="
echo

# Start the server
python3 manage.py runserver

echo
echo "🛑 Server stopped."