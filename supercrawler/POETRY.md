# Poetry

Poetry manages your project dependencies and creates a virtual environment for you.

## Install Poetry

If Poetry is not installed yet:

```bash
pipx install poetry
```

Check it:

```bash
poetry --version
```

## Start A Project

Create a new Poetry project:

```bash
poetry init
```

This creates a `pyproject.toml` file.

## Install Dependencies

Add a package:

```bash
poetry add requests
```

Add a dev dependency:

```bash
poetry add --group dev pytest
```

Install everything from `pyproject.toml` and `poetry.lock`:

```bash
poetry install
```

## Use The Environment

Run a command inside Poetry's environment:

```bash
poetry run python
poetry run pytest
```

Open a shell inside the environment:

```bash
poetry shell
```

## Useful Checks

See the environment path:

```bash
poetry env info
```

See installed dependencies:

```bash
poetry show
```

## Lock File

Poetry uses:

- `pyproject.toml` for declared dependencies
- `poetry.lock` for exact locked versions

Commit both files to git.

## Typical Workflow

```bash
poetry install
poetry add <package>
poetry run python your_script.py
```

poetry run python main.py https://example.com