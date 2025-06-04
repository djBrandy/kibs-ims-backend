#!/bin/bash
export FLASK_APP=wsgi.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Retry mechanism for database connection
MAX_RETRIES=5
RETRY_DELAY=5

for i in $(seq 1 $MAX_RETRIES); do
    echo "Starting Flask app (attempt $i of $MAX_RETRIES)..."
    flask run --host=0.0.0.0 --port=5000
    
    # If exit code is 0 (clean exit), break the loop
    if [ $? -eq 0 ]; then
        break
    fi
    
    echo "Flask app crashed. Restarting in $RETRY_DELAY seconds..."
    sleep $RETRY_DELAY
done