.PHONEY: lint, lint_templates, todos

lint:
	pylint *.py

lint_templates:
	pylint templates/*.py

todos:
	pylint -d all -e fixme *.py
