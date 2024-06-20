#!/bin/sh
export FLASK_APP=./python/index.py
pipenv run flask --debug run -h 0.0.0.0 --port 5931
