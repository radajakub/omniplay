.PHONY: lint format check fix

# Check lint and formatting (same checks as CI)
lint:
	uv run ruff check .
	uv run ruff format --check .
	npx --yes prettier@3.9.6 --check .

# Alias for lint
check: lint

# Autofix lint issues and reformat
format:
	uv run ruff check --fix .
	uv run ruff format .
	npx --yes prettier@3.9.6 --write .

# Alias for format
fix: format
