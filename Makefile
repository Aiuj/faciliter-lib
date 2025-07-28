.PHONY: install test lint clean

install:
	uv pip install -e .[dev]

test:
	pytest tests/ --disable-warnings -q

lint:
	ruff faciliter_lib tests

clean:
	find . -type d -name '__pycache__' -exec rm -r {} +
