#!/bin/bash
cd `dirname $0`
# python -m venv .venv
source .venv/bin/activate
# pip install -r requirements.txt
python3 -m flask run --host=0.0.0.0 --port 8080
