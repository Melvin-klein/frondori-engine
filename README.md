# frondori-engine

Le contrat commun des environnements de recherche de
[Frondori](https://frondori.ai), au format [PettingZoo](https://pettingzoo.farama.org/).

**Ce paquet ne contient aucun environnement.** Chacun est un paquet à part,
dans son propre dépôt, qu'on installe seulement s'il nous intéresse :

| Paquet | Environnement |
|---|---|
| `frondori-football` | `football-v0` — football 2D, duel (moteur Rust) |
| `frondori-kitchen` | `kitchen-v0` — cuisine coopérative |

## Installation

```bash
pip install frondori-engine frondori-kitchen
```

(Pas encore publiés sur PyPI : depuis un clone, `pip install -e .` dans
chaque dépôt.)

## Utilisation

```python
import frondori_engine

print(frondori_engine.registered_ids())     # les environnements installés
env = frondori_engine.make("kitchen-v0")    # un pettingzoo.ParallelEnv
observations, infos = env.reset(seed=42)

while env.agents:
    actions = {agent: env.action_space(agent).sample() for agent in env.agents}
    observations, rewards, terminations, truncations, infos = env.step(actions)
```

Sans serveur, sans réseau, sans token. Compatible avec l'écosystème qui parle
PettingZoo (RLlib, TorchRL, CleanRL, SuperSuit...). Pour jouer un match en
local dans les conditions de la compétition, ou contre d'autres agents sur
le serveur, voir le SDK (`frondori-sdk`) : `Agent(..., local=True)`.

## Ce que contient ce paquet

- `frondori_engine.make` / `registered_ids` / `register` : le registre. Les
  environnements installés sont découverts automatiquement par leur *entry
  point* (groupe `frondori.environments`).
- `frondori_engine.scene` : le format de rendu commun (`render_mode="scene"`).
- `frondori_engine.wire` : le format des spaces et des valeurs sur le réseau.
- `frondori_engine.worker` : exécute un environnement pour le serveur de
  compétition (un processus par match).
- `frondori_engine.testing` : les tests du contrat, à appeler depuis les
  tests de chaque environnement (`check_environment("mon-jeu-v0")`).

## Créer un environnement

Un paquet Python qui dépend de `frondori-engine` et se déclare dans son
`pyproject.toml` :

```toml
[project.entry-points."frondori.environments"]
"mon-jeu-v0" = "mon_paquet:MonJeuEnv"
```

Guide complet, avec un exemple vérifié : Documentation > Create an
Environment, sur le site. L'exemple de ce guide (`tests/rps.py`) sert aussi
d'environnement de test à ce paquet.

## Développer / tester

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
```
