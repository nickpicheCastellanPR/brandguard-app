#!/bin/bash
# start.sh — Launch webhook receiver + Streamlit in the same container

echo "Starting Lemon Squeezy webhook handler on port 8001..."
uvicorn webhook_handler:app --host 0.0.0.0 --port 8001 &

echo "Starting Streamlit on port 8501..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
