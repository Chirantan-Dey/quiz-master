#!/bin/bash

if [ ! -d ".venv" ]; then
    uv venv .venv
fi

source .venv/bin/activate
uv pip install -r requirements.txt