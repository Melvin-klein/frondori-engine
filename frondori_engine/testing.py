"""Les tests du contrat commun, réutilisables par chaque paquet
d'environnement dans ses propres tests :

    from frondori_engine.testing import check_environment

    def test_contract():
        check_environment("kitchen-v0")

Chaque vérification est aussi disponible seule (`check_*`). Elles lèvent
`AssertionError` (ou l'erreur de PettingZoo) au premier manquement, avec un
message qui dit quoi corriger.
"""

from __future__ import annotations

import json

from pettingzoo.test import parallel_api_test, parallel_seed_test

import frondori_engine
from frondori_engine import wire

RANKINGS = ("elo", "mean_return")
SHAPE_TYPES = {"rect", "circle", "text"}


def check_environment(env_id: str) -> None:
    """Tout le contrat : à appeler depuis les tests de chaque environnement."""
    check_pettingzoo_api(env_id)
    check_reproducible(env_id)
    check_observations_fit_their_space(env_id)
    check_metadata(env_id)
    check_spaces_can_be_sent(env_id)
    check_neutral_action(env_id)
    check_scene(env_id)


def check_pettingzoo_api(env_id: str) -> None:
    """Le test officiel de PettingZoo (API parallèle). Il exige notamment
    que `observation_space(agent)` renvoie le MÊME objet à chaque appel :
    créer les spaces une fois, dans `__init__`."""
    parallel_api_test(frondori_engine.make(env_id), num_cycles=300)


def check_reproducible(env_id: str) -> None:
    """Même seed + mêmes actions = même épisode."""
    parallel_seed_test(lambda: frondori_engine.make(env_id), num_cycles=100)


def check_observations_fit_their_space(env_id: str, steps: int = 500) -> None:
    # `parallel_api_test` ne le vérifie PAS (constaté : il laisse passer une
    # valeur hors bornes). Or c'est sur ces spaces que le serveur et les
    # agents s'appuient : vérifié ici explicitement.
    env = frondori_engine.make(env_id)
    observations, _ = env.reset(seed=0)
    for _ in range(steps):
        for agent, observation in observations.items():
            assert env.observation_space(agent).contains(observation), (
                f"{env_id} : l'observation de {agent} sort de son observation_space : {observation!r}"
            )
        if not env.agents:
            break
        observations, *_ = env.step({agent: env.action_space(agent).sample() for agent in env.agents})


def check_metadata(env_id: str) -> None:
    """Les métadonnées dont le serveur et le site ont besoin."""
    env = frondori_engine.make(env_id)
    metadata = env.metadata
    for key in ("title", "description", "documentation"):
        assert isinstance(metadata.get(key), str) and metadata[key].strip(), (
            f"{env_id} : metadata[{key!r}] (texte non vide) est requis"
        )
    assert (metadata.get("render_fps") or 0) > 0, f"{env_id} : metadata['render_fps'] (pas par seconde) est requis"
    assert (metadata.get("compute_budget_ms") or 0) > 0, (
        f"{env_id} : metadata['compute_budget_ms'] (temps de calcul par action, en ms) est requis"
    )
    assert metadata.get("ranking") in RANKINGS, f"{env_id} : metadata['ranking'] doit valoir l'un de {RANKINGS}"
    if metadata["ranking"] == "elo":
        assert len(env.possible_agents) == 2, f"{env_id} : un classement ELO n'a de sens qu'en duel (2 agents)"
    assert "scene" in metadata.get("render_modes", []), f"{env_id} : render_mode 'scene' est requis"


def check_spaces_can_be_sent(env_id: str) -> None:
    """Seuls Box, Discrete, MultiDiscrete et Dict passent sur le réseau."""
    env = frondori_engine.make(env_id)
    for agent in env.possible_agents:
        wire.space_to_spec(env.observation_space(agent))
        wire.space_to_spec(env.action_space(agent))


def check_neutral_action(env_id: str) -> None:
    """L'élément "zéro" de chaque action_space est une action valide : c'est
    celle que le serveur joue pour un agent dont l'action est invalide, trop
    lente ou absente (elle doit ne rien faire — ce que seul l'auteur de
    l'environnement peut garantir)."""
    env = frondori_engine.make(env_id)
    env.reset(seed=0)
    for agent in env.possible_agents:
        space = env.action_space(agent)
        assert space.contains(wire.neutral_action(space)), (
            f"{env_id} : l'action neutre de {agent} sort de son action_space"
        )
    env.step({agent: wire.neutral_action(env.action_space(agent)) for agent in env.agents})


def check_scene(env_id: str) -> None:
    """Le rendu générique : sérialisable en JSON, primitives connues."""
    env = frondori_engine.make(env_id, render_mode="scene")
    env.reset(seed=0)
    env.step({agent: env.action_space(agent).sample() for agent in env.agents})
    scene = env.render()

    json.dumps(scene)
    assert scene["width"] > 0 and scene["height"] > 0, f"{env_id} : la scène doit avoir une largeur et une hauteur"
    assert scene["shapes"], f"{env_id} : la scène est vide"
    unknown = {shape["type"] for shape in scene["shapes"]} - SHAPE_TYPES
    assert not unknown, f"{env_id} : primitives de scène inconnues {unknown} (attendu : {SHAPE_TYPES})"


__all__ = [
    "check_environment",
    "check_metadata",
    "check_neutral_action",
    "check_observations_fit_their_space",
    "check_pettingzoo_api",
    "check_reproducible",
    "check_scene",
    "check_spaces_can_be_sent",
]
