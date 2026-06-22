#!/bin/bash

cd service
# source .venv/bin/activate


#fastapi dev app/main.py #dev mode
uv run fastapi dev app/main.py
#uvicorn app.main:app --reload #for production
