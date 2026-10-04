from importlib.metadata import EntryPoint

import pytest

import frondori_engine
from frondori_engine import registry
from rps import RockPaperScissorsEnv


def test_make_passes_kwargs_to_the_environment():
    env = frondori_engine.make("rps-v0", rounds=3)
    env.reset()

    for _ in range(3):
        *_, truncations, _ = env.step({agent: 1 for agent in env.agents})

    assert all(truncations.values())
    assert env.agents == []


def test_unknown_environment_lists_available_ones():
    with pytest.raises(KeyError, match="rps-v0"):
        frondori_engine.make("chess-v0")


@pytest.mark.parametrize("bad_id", ["rps", "Rps-v0", "rps-v", "rps_v0"])
def test_ids_must_be_versioned(bad_id):
    with pytest.raises(ValueError, match="name-vN"):
        frondori_engine.register(bad_id, RockPaperScissorsEnv)


def test_an_id_cannot_be_registered_twice():
    with pytest.raises(ValueError, match="already registered"):
        frondori_engine.register("rps-v0", RockPaperScissorsEnv)


def fake_entry_points(*entries):
    return lambda group: [EntryPoint(name, value, group) for name, value in entries if group == registry.ENTRY_POINT_GROUP]


def test_installed_environments_are_discovered(monkeypatch):
    monkeypatch.setattr(registry, "_registry", {})
    monkeypatch.setattr(registry, "_discovered", False)
    monkeypatch.setattr(registry, "entry_points", fake_entry_points(("game-v0", "rps:RockPaperScissorsEnv")))

    assert frondori_engine.registered_ids() == ["game-v0"]
    env = frondori_engine.make("game-v0", rounds=2)
    assert isinstance(env, RockPaperScissorsEnv) and env.rounds == 2


def test_an_environment_class_is_only_imported_when_created(monkeypatch):
    # Lister le catalogue ne doit charger aucun moteur.
    monkeypatch.setattr(registry, "_registry", {})
    monkeypatch.setattr(registry, "_discovered", False)
    monkeypatch.setattr(registry, "entry_points", fake_entry_points(("broken-v0", "no_such_module:Env")))

    assert frondori_engine.registered_ids() == ["broken-v0"]
    with pytest.raises(ModuleNotFoundError):
        frondori_engine.make("broken-v0")


def test_two_packages_declaring_the_same_id_is_an_error(monkeypatch):
    monkeypatch.setattr(registry, "_registry", {})
    monkeypatch.setattr(registry, "_discovered", False)
    monkeypatch.setattr(
        registry,
        "entry_points",
        fake_entry_points(("game-v0", "rps:RockPaperScissorsEnv"), ("game-v0", "rps:RockPaperScissorsEnv")),
    )

    with pytest.raises(ValueError, match="already registered"):
        frondori_engine.registered_ids()
