.PHONY: install lint typecheck test build docker clean

install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy .

test:
	pytest

build:
	python -m pip wheel --no-deps -w dist .

docker:
	docker build -t python-selenium-outlook .

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
