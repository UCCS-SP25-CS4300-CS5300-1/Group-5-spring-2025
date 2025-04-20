#!/bin/bash

echo "Running isort (import sorter)..."
isort . \
  --skip camp_mate_venv \
  --skip migrations \
  --skip db.sqlite3 \
  --skip Dockerfile \
  --skip __pycache__

echo "Running black (code formatter)..."
black . \
  --exclude "(camp_mate_venv|migrations|db.sqlite3|Dockerfile|__pycache__)"


