.PHONY: clean lint requirements test test_environment

PYTHON_INTERPRETER ?= python3

## Install Python dependencies
requirements: test_environment
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt

## Delete compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint source package
lint:
	flake8 src tests

## Run tests
test:
	pytest tests

## Check Python environment
test_environment:
	$(PYTHON_INTERPRETER) test_environment.py

