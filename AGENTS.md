# Agent Guidelines

These instructions apply to the entire repository.

## Development workflow
- Prefer small, focused changes with clear commit messages.
- When you add or modify FastAPI routes or SQLModel models, update or create tests that cover the new behavior.
- Keep importers and seed scripts idempotent; avoid logic that depends on side effects from previous runs.
- Update documentation (README, docs/, or in-line docstrings) when you change a command-line interface or environment variables.

## Python style
- Follow [Black](https://black.readthedocs.io/) formatting conventions (88 character default line length). Existing files may not be formatted yet, but new or modified code should be.
- Use type annotations for new function definitions when practical.
- Prefer explicit imports from inside `app` rather than relying on implicit package-level state.

## Testing
- Run `pytest` before submitting if your changes affect Python code, database models, or importers.
- Use factory or fixture patterns from `tests/` when adding new tests instead of ad-hoc setup inside test bodies.

## Pull request notes
- Summaries should call out any new commands, environment variables, or database migrations.
- Mention in the PR description if manual database setup or seed steps are required for reviewers.
