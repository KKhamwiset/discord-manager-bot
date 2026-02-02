#!/bin/bash

cd /app/api
python app.py &

cd /app/dashboard
node server.js &

python main.py
