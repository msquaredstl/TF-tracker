# Agent Guidelines

These guidelines ensure consistent, high-quality contributions to the **Transformers Tracker** project.  
They apply to all contributors — human or AI — working within this repository.

---

## 🧭 Development Workflow

- Use feature branches for all new work: `feature/<short-description>` or `fix/<issue-id>`.
- Keep commits atomic — one logical change per commit.
- Use clear, imperative commit messages (e.g., “Add API endpoint for figure search”).
- Open draft PRs early for visibility; mark them **Ready for Review** once tests and docs are updated.
- When modifying routes, models, or serializers:
  - Add or update tests to cover new behavior.
  - Ensure migrations are created and committed (use `python manage.py makemigrations` and `migrate`).
  - Update documentation or docstrings to reflect any new commands or environment variables.
- Avoid adding dependencies unless necessary; explain all new requirements in the PR description.

---

## 🧱 Repository Structure

- `app/` — Core application code, including database helpers (`app/db`), import pipelines (`app/importers`), templates, static assets, and the CLI entry point (`app/main.py`).
- `attributes/` — Source CSVs for figure metadata such as categories, factions, and vendors.
- `seeds/` — Seed configuration files (e.g., `seed.yaml`) used to bootstrap the database.
- `tests/` — Pytest suite covering models, importers, and CLI behaviour.
- `docs/` — Project documentation and architecture notes.
- `README.md` — High-level project overview and getting-started instructions.
- `requirements.txt` — Python dependencies for the application and tooling.

---

## 🐍 Python & Django Style

- Follow [Black](https://black.readthedocs.io/) formatting (88-char line length).
- Use [isort](https://pycqa.github.io/isort/) for import organization.
- Run [ruff](https://docs.astral.sh/ruff/) for linting.
- Use [mypy](https://mypy.readthedocs.io/) for type checking when practical.
- Avoid wildcard imports; prefer explicit imports from within the `app` package.
- Use consistent docstring style (Google or PEP 257).
- Keep functions and methods typed when possible:
  ```python
  def get_figure_by_id(figure_id: int) -> Figure:
      ...
  ```

## Import & Formatting Policy (No-Churn)

- **Do not change import order or shape** unless required by a linter or formatter, or when adding/removing actual usage.
- **Never add unused imports.** Every imported symbol must be referenced in the file (ruff F401 enforced).
- **No cosmetic-only PRs.** Pure formatting commits must be labeled `chore: format` and contain no logic changes.
- **Respect tool output.** Imports and formatting are governed by `ruff`, `isort`, and `black`. Do not manually reorder them.
- **Run these tools in order:**  
  `ruff --fix . && isort . && black .`
- **Module-specific rule:** High-churn files like `app/importers/import_csv.py` should not have import blocks modified unless the change is necessary for functional reasons.

---

## 🧪 Testing (Django + API)

### General Guidelines
- Use **pytest** with the **pytest-django** plugin.
- Run all tests before submitting a PR:  
  ```bash
  pytest --reuse-db --cov=app --maxfail=1
  ```
- Place tests next to related modules (e.g., `tests/test_models.py`, `tests/test_views.py`).
- Use **fixtures** or **factory_boy** for creating test data — do not manually instantiate models inside tests.
- Include both “happy path” and “edge case” coverage for each new feature.

### Django Testing Standards
- For model changes:
  - Test save(), delete(), and custom manager/queryset behavior.
  - Verify migrations apply cleanly (`python manage.py migrate --check`).
- For views and APIs:
  - Use Django’s `Client` or DRF’s `APIClient` for integration testing.
  - Verify authentication, permissions, and serialization.
- For templates and frontend logic:
  - Use Django’s `assertTemplateUsed` and context checks.
  - For JS-dependent behavior, consider mocking or isolating in a separate test layer.

### FastAPI / Hybrid Layer
- When adding or modifying FastAPI endpoints:
  - Add route tests under `tests/test_api_routes.py`.
  - Use `TestClient` from FastAPI for request/response validation.
  - Confirm JSON schema responses align with Django serializers or Pydantic models.

---

## 🗃 Database and Seed Data

- All schema changes must use Django migrations; **never** edit existing migration files.
- Seed scripts must be **idempotent** — re-running should not create duplicates or inconsistent state.
- Place reusable import or setup logic in `scripts/` and ensure it can run in any environment (dev, staging, prod).
- If migrations introduce breaking changes, include clear upgrade instructions in your PR description.
- Reflect any model or relationship changes in the Mermaid ER diagram at [`schema.mmd`](./schema.mmd); regenerate exported assets if you maintain them separately.

---

## 🧩 Documentation

- Update README or files under `docs/` when adding:
  - New commands, endpoints, or environment variables.
  - Major model or schema changes.
  - Setup steps for local or CI environments.
- Include inline docstrings for complex logic or domain-specific code (e.g., figure rarity scoring, series taxonomy).

---

## 🤖 AI Agent Conduct

- Generate only valid, runnable Python/Django code.
- Maintain compliance with the style, testing, and workflow rules above.
- Prefer readability and maintainability over brevity.
- When introducing new files or refactoring existing ones:
  - Maintain backward compatibility where possible.
  - Preserve or improve test coverage.
  - Include a one-line summary at the top of the PR explaining the purpose and scope of the change.

---

## ✅ Pre-Commit Checklist

Before committing:
- [ ] Run: `ruff --fix . && isort . && black .`
- [ ] Run `ruff check .`
- [ ] Run `pytest` and confirm all tests pass
- [ ] Verify migrations: `python manage.py makemigrations --check`
- [ ] Update docs or inline comments if necessary
- [ ] Check for unused imports or dead code

---

## 📝 Pull Request Notes

- Summarize what’s new and why it matters.
- Highlight any new:
  - Commands or scripts
  - Environment variables
  - Database migrations
- Note if manual setup, seeding, or testing steps are required for reviewers.
- Tag reviewers familiar with the affected area of the codebase.

---

## 🚀 Suggested Improvements for This Guide

- Add a short “Local Setup” checklist (Python version, virtualenv, `poetry` or `pip` usage) to help newcomers ramp up faster.
- Document expected environment variables and sample `.env` configuration to reduce onboarding friction.
- Capture data model overviews in `docs/` (diagram or table) and link them here for quick discovery.
- Provide coverage expectations or quality gates (e.g., minimum coverage percentage, lint severity policy) so contributors know the target bar.

---

_This document evolves with the project. Keep it current as tooling and architecture mature._

