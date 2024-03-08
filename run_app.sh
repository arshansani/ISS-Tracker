#!/bin/bash
# navigate to the application directory and start the main application
cd /code
export FLASK_APP=iss_tracker.py
export FLASK_ENV=development
flask run --host=0.0.0.0