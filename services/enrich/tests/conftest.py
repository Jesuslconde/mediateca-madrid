from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

FIXTURES = ROOT / "fixtures"


@pytest.fixture
def dvd_fixture() -> Path:
    return FIXTURES / "detail_dvd.html"


@pytest.fixture
def bluray_fixture() -> Path:
    return FIXTURES / "detail_bluray.html"


@pytest.fixture
def search_results_fixture() -> Path:
    return FIXTURES / "search_results.html"


@pytest.fixture
def aragon_search_fixture() -> Path:
    return FIXTURES / "aragon" / "search_results.html"


@pytest.fixture
def valencia_search_fixture() -> Path:
    return FIXTURES / "valencia" / "search_results.html"


@pytest.fixture
def pais_vasco_search_fixture() -> Path:
    return FIXTURES / "pais-vasco" / "search_results.html"


@pytest.fixture
def ccbip_novedades_fixture() -> Path:
    return FIXTURES / "ccbip" / "novedades.html"


@pytest.fixture
def ccbip_detail_fixture() -> Path:
    return FIXTURES / "ccbip" / "detail_007.html"
