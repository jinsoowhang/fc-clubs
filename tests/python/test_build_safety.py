import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from fc_clubs.build import build
from fc_clubs.errors import PipelineError
from fc_clubs.storage import Warehouse


def test_failed_dbt_build_preserves_original_and_discards_diagnostics(tmp_path, monkeypatch):
    database = tmp_path / "warehouse.duckdb"
    with Warehouse(database, "demo"):
        pass
    original = database.read_bytes()
    module = importlib.import_module("fc_clubs.build")
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=1,
            stdout="PRIVATE_DIAGNOSTIC",
            stderr="PRIVATE_DIAGNOSTIC",
        ),
    )
    with pytest.raises(PipelineError, match="^dbt_build_failed$"):
        build(Path(__file__).resolve().parents[2], database)
    assert database.read_bytes() == original
    assert not database.with_suffix(".replacement").exists()
