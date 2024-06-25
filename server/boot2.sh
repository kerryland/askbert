#!/bin/sh

export HF_HOME=cache
export FLASK_APP=python
export FLASK_ENV=development
pipenv run flask --debug run -h 0.0.0.0 --port 5931
