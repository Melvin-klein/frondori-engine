"""Le contrat commun des environnements de recherche Frondori.

Ce paquet ne contient AUCUN environnement : chacun est un paquet à part,
installé selon ses besoins, et découvert automatiquement :

    pip install frondori-engine frondori-kitchen

    import frondori_engine

    print(frondori_engine.registered_ids())     # ['kitchen-v0']
    env = frondori_engine.make("kitchen-v0")
    observations, infos = env.reset(seed=42)
    while env.agents:
        actions = {agent: env.action_space(agent).sample() for agent in env.agents}
        observations, rewards, terminations, truncations, infos = env.step(actions)

Il fournit ce que tous partagent : le registre (`make`, `register`), le
format des scènes (`scene`), celui des spaces et des valeurs sur le réseau
(`wire`), le worker qui exécute un environnement pour le serveur de
compétition (`worker`) et les tests du contrat (`testing`).
"""

from frondori_engine.registry import ENTRY_POINT_GROUP, EnvSpec, get_spec, make, register, registered_ids

__all__ = ["ENTRY_POINT_GROUP", "EnvSpec", "get_spec", "make", "register", "registered_ids"]
