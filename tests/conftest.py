"""Ce paquet ne contient aucun environnement : les tests en enregistrent un,
l'exemple pierre-feuille-ciseaux de la documentation (`tests/rps.py`), dans
un registre isolé — sans dépendre de ce qui est installé à côté."""

import sys
from pathlib import Path

import pytest

from frondori_engine import registry

sys.path.insert(0, str(Path(__file__).parent))

from rps import RockPaperScissorsEnv  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    monkeypatch.setattr(registry, "_registry", {})
    # Découverte des paquets installés désactivée par défaut ; les tests de
    # découverte la réactivent avec de faux entry points.
    monkeypatch.setattr(registry, "_discovered", True)
    registry.register("rps-v0", RockPaperScissorsEnv)
