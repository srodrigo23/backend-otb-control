#!/bin/bash

cd backend
source .venv/bin/activate


fastapi dev app/main.py #dev mode
#uvicorn app.main:app --reload #for production
