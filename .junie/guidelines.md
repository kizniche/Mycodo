# Project Guidelines

## Project Overview
This repository contains Mycodo, a Python-based automation and monitoring system with a Flask web interface. The codebase includes controllers, devices, inputs, outputs, functions, widgets, and a web UI for configuration and monitoring. Documentation and Docker-related assets are also provided.

## Repository Layout (high-level)
- alembic_db/: Database migration management (alembic setup and versions)
- docker/: Docker compose assets and service configs (grafana, influxdb, nginx, telegraf)
- docs/ and docs_templates/: Project documentation and assets
- install/: Installation helpers
- mycodo/:
  - actions/, controllers/: Core automation/interaction logic
  - databases/, databases/models/: Database layer and models
  - devices/: Hardware integration code
  - functions/, inputs/, outputs/: Extensible building blocks of the automation system
  - mycodo_flask/: Flask app (API, templates, static, forms, translations, utils)
  - scripts/: Helper scripts
  - tests/: Automated tests (software tests, factories, manual tests)
  - user_python_code/, user_scripts/: User-extensible code areas
  - utils/, widgets/: Utilities and UI widgets (with custom/ examples)
- README.rst, CHANGELOG.md, LICENSE.txt: Project metadata
- mkdocs.yml: Docs configuration
- release-checklist.md: Release process notes

## How Junie should work on this project
- Make minimal, focused changes to satisfy the specific issue.
- Prefer editing existing modules over large refactors unless required.
- Keep user informed each step, including a plan, next step, and summary of changes.

## Running Tests
- Test framework: pytest (standard Python layout observed under mycodo/tests).
- Typical command from repo root:
  - python -m pytest -q mycodo/tests/software_tests
- If a change affects the Flask layer, prefer running the relevant sub-suite under mycodo/tests/software_tests/test_mycodo_flask.
- Add or adjust tests only when necessary to cover new behavior or bugfixes.

## Build/Run Notes
- This is a Python project; building is not typically required to validate code changes.
- Running the full application or Docker stack is not required for most code changes associated with issues like documentation, small bug fixes, or internal logic adjustments.
- For issues that explicitly involve Docker services (Grafana/InfluxDB/NGINX/Telegraf), consult docker/ and the project README for environment details before attempting to run.

## Code Style & Conventions
- Follow PEP 8 for Python code style and maintain readable, self-documenting code.
- Keep functions small and focused; add docstrings for non-trivial functions/classes.
- Maintain existing patterns and naming conventions found in the touched files.
- Favor type hints where they are already used; otherwise, do not introduce sweeping typing changes.
- Include meaningful commit messages and changelog updates when required by the issue.

## When Submitting a Fix
- Explain what changed and why, referencing the issue.
- Note any edge cases considered and how they are handled.
- If tests were run, state which suites were executed and summarize results.
