#!/bin/bash
# Development server launcher for fin-infra-template

# Default port
PORT=${API_PORT:-8001}

echo "🚀 Starting fin-infra-template server on port $PORT..."
echo "📖 OpenAPI docs: http://localhost:$PORT/docs"
echo "📊 Metrics: http://localhost:$PORT/metrics"
echo "🏥 Health: http://localhost:$PORT/_health"
echo ""

# Run with uvicorn
poetry run uvicorn fin_infra_template.main:app --reload --host 0.0.0.0 --port $PORT
