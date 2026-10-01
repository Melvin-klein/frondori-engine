"""Registre des environnements, sur le modèle de `gymnasium.make`.

Les environnements ne vivent PAS dans ce paquet : chacun est un paquet
Python indépendant (`frondori-football`, `frondori-kitchen`...), dans son
propre dépôt, qu'un chercheur installe seulement s'il l'intéresse. Un
paquet se déclare par un *entry point* du groupe `frondori.environments`,
dans son `pyproject.toml` :

    [project.entry-points."frondori.environments"]
    "kitchen-v0" = "frondori_kitchen:KitchenEnv"

Au premier appel à `make`/`registered_ids`, le registre découvre tous les
environnements installés (`importlib.metadata.entry_points`, le mécanisme
standard des plugins Python, celui de pytest ou de Gymnasium). Chaque classe
n'est importée qu'au moment de créer l'environnement : lister le catalogue
ne charge aucun moteur.

`register` reste disponible pour un environnement en cours d'écriture, pas
encore empaqueté.

Tout identifiant porte une version (`nom-vN`). Changer les règles d'un
environnement, c'est en publier une nouvelle version, jamais modifier
l'ancienne : un résultat, un replay ou un classement obtenu sur
`football-v0` doit rester comparable dans six mois.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib.metadata import EntryPoint, entry_points
from typing import Any, Callable

from pettingzoo import ParallelEnv

ENTRY_POINT_GROUP = "frondori.environments"

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*-v\d+$")


@dataclass(frozen=True)
class EnvSpec:
    id: str
    entry_point: Callable[..., ParallelEnv]
    kwargs: dict[str, Any] = field(default_factory=dict)
    # Paquet installable qui fournit l'environnement (ex. "frondori-kitchen"),
    # `None` pour un environnement enregistré à la main. Publié avec le
    # catalogue : le site en tire la commande d'installation.
    package: str | None = None


_registry: dict[str, EnvSpec] = {}
_discovered = False


def register(id: str, entry_point: Callable[..., ParallelEnv], package: str | None = None, **kwargs: Any) -> None:
    """Enregistre un environnement. `kwargs` : paramètres par défaut passés à
    `entry_point`, surchargeables au moment de `make`."""
    if not _ID_PATTERN.match(id):
        raise ValueError(f"identifiant invalide {id!r} : format attendu 'nom-vN' (ex. 'football-v0')")
    if id in _registry:
        raise ValueError(f"environnement {id!r} déjà enregistré ({_registry[id].package or 'register()'})")
    _registry[id] = EnvSpec(id=id, entry_point=entry_point, kwargs=kwargs, package=package)


def make(id: str, **kwargs: Any) -> ParallelEnv:
    try:
        spec = get_spec(id)
    except KeyError:
        known = ", ".join(registered_ids()) or "(aucun : installer un paquet d'environnement, ex. frondori-kitchen)"
        raise KeyError(f"environnement inconnu {id!r} ; disponibles : {known}") from None
    return spec.entry_point(**{**spec.kwargs, **kwargs})


def get_spec(id: str) -> EnvSpec:
    _discover()
    return _registry[id]


def registered_ids() -> list[str]:
    _discover()
    return sorted(_registry)


def _discover() -> None:
    """Enregistre les environnements des paquets installés, une seule fois.
    Deux paquets qui déclarent le même identifiant : erreur explicite plutôt
    qu'un choix silencieux de l'un des deux."""
    global _discovered
    if _discovered:
        return
    _discovered = True
    for entry in entry_points(group=ENTRY_POINT_GROUP):
        register(entry.name, _lazy(entry), package=entry.dist.name if entry.dist else None)


def _lazy(entry: EntryPoint) -> Callable[..., ParallelEnv]:
    # La classe n'est importée qu'à la création d'un environnement : lister
    # les environnements disponibles ne charge aucun moteur (le football
    # charge un module natif).
    def create(**kwargs: Any) -> ParallelEnv:
        return entry.load()(**kwargs)

    return create
