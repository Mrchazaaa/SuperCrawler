from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.packaging]


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_URL = "https://charliehowlett.com"


def _run_command(*args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_success(command_result: subprocess.CompletedProcess[str]) -> None:
    assert command_result.returncode == 0, (
        f"command failed with exit code {command_result.returncode}\n"
        f"stdout:\n{command_result.stdout}\n"
        f"stderr:\n{command_result.stderr}"
    )


def _assert_crawl_results(payload: dict[str, object], url: str) -> None:
    assert payload["configuration"]["url"] == url
    assert payload["results"]
    assert payload["results"][0]["url"] == url
    assert payload["results"][0]["status"] in {"success", "failure"}

    if payload["results"][0]["status"] == "failure":
        assert payload["results"][0]["error"]


def _venv_executable(venv_dir: Path, executable_name: str) -> Path:
    scripts_dir = "Scripts" if os.name == "nt" else "bin"
    return venv_dir / scripts_dir / executable_name


def test_pip_install_exposes_console_script(tmp_path: Path) -> None:
    venv_dir = tmp_path / "venv"

    create_venv = _run_command(sys.executable, "-m", "venv", str(venv_dir), cwd=PROJECT_ROOT)
    _assert_success(create_venv)

    pip = _venv_executable(venv_dir, "pip")
    install = _run_command(str(pip), "install", ".", cwd=PROJECT_ROOT)
    _assert_success(install)

    cli = _venv_executable(venv_dir, "supercrawler")
    crawl = _run_command(str(cli), TARGET_URL, cwd=PROJECT_ROOT)
    _assert_success(crawl)

    payload = json.loads(crawl.stdout)
    _assert_crawl_results(payload, TARGET_URL)


def test_poetry_install_makes_package_importable() -> None:
    install = _run_command("poetry", "install", cwd=PROJECT_ROOT)
    _assert_success(install)

    import_and_run = _run_command(
        "poetry",
        "run",
        "python",
        "-c",
        (
            "import json; "
            "from supercrawler import explore_domain; "
            f"results = explore_domain({TARGET_URL!r}); "
            "print(json.dumps([{"
            "'url': result.url, "
            "'status': result.status, "
            "'error': result.error"
            "} for result in results]))"
        ),
        cwd=PROJECT_ROOT,
    )
    _assert_success(import_and_run)

    results = json.loads(import_and_run.stdout)
    assert results
    assert results[0]["url"] == TARGET_URL
    assert results[0]["status"] in {"success", "failure"}

    if results[0]["status"] == "failure":
        assert results[0]["error"]


def test_source_entrypoint_runs_via_poetry() -> None:
    crawl = _run_command("poetry", "run", "python", "main.py", TARGET_URL, cwd=PROJECT_ROOT)
    _assert_success(crawl)

    payload = json.loads(crawl.stdout)
    _assert_crawl_results(payload, TARGET_URL)
