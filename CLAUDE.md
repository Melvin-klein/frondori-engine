# frondori-engine — le contrat commun des environnements Frondori

Paquet Python pur, SANS aucun environnement : chaque environnement est un
paquet à part (`frondori-football`, `frondori-kitchen`...), dans son propre
dépôt, qui dépend de celui-ci et se déclare par un entry point :

```toml
[project.entry-points."frondori.environments"]
"kitchen-v0" = "frondori_kitchen:KitchenEnv"
```

`registry.py` découvre les paquets installés au premier `make` /
`registered_ids` (`importlib.metadata.entry_points`), importe chaque classe
seulement à la création (lister ne charge aucun moteur), et refuse deux
paquets qui déclarent le même identifiant. `register()` reste disponible pour
un environnement en cours d'écriture. Le serveur (`frondori-server`) utilise
le worker de ce paquet ; le SDK (`frondori-sdk-python`, `local=True`) utilise
le registre et `wire`.

**Le contrat commun, c'est PettingZoo** (`ParallelEnv`, spaces Gymnasium).
Tout environnement :
- est enregistré sous un identifiant versionné `nom-vN` (`registry.py`).
  Changer des règles = publier `nom-v(N+1)`, jamais modifier `nom-vN`
  (reproductibilité des résultats, replays et classements) ;
- déclare sa cadence en compétition dans `metadata["render_fps"]` (pas par
  seconde : 30 pour le football, 5 pour la cuisine) — un PLANCHER de durée
  par pas, les matchs se jouant en pas-à-pas (cf. `match_runner`) ;
- déclare son budget de calcul par action, `metadata["compute_budget_ms"]`
  (30 ms au football, 200 ms en cuisine) ;
- déclare `metadata["title"]`, `metadata["description"]` (affichés par le
  site), `metadata["documentation"]` (ses règles, en anglais et en Markdown
  simple : publiées avec le catalogue et affichées par la page
  Documentation > Environments du site) et `metadata["ranking"]` : `"elo"` (duel à 2 agents uniquement — le
  vainqueur est l'agent au meilleur retour) ou `"mean_return"` (retour moyen
  par match). Vérifié par le contrat et par `worker._describe` ;
- peut renvoyer dans ses infos une clé `score` : convention que le site
  affiche comme score du match (le football y met ses buts marqués) ; à
  défaut, le site affiche le retour. Toutes les infos numériques finales
  apparaissent dans les statistiques de la page de match ;
- se rend via `render_mode="scene"` : primitives génériques rect/cercle/texte
  en JSON (`scene.py`), qu'un seul afficheur dessine pour tous les jeux ;
- doit être conçu pour que l'élément « zéro » de son `action_space` soit une
  action sans effet : c'est l'action neutre jouée quand un agent ne répond
  pas à temps ou envoie une action invalide (`wire.neutral_action`) ;
- est vérifié par `frondori_engine.testing.check_environment(id)`, que
  chaque paquet d'environnement appelle dans ses propres tests. **Piège** : le `parallel_api_test` officiel ne vérifie PAS
  l'appartenance des observations à leur space (constaté avec un contrôle
  négatif) — d'où le test explicite.

Ajouter un environnement = un nouveau paquet (dépôt) avec son entry point
(guide complet, avec un exemple vérifié : Documentation > Create an
Environment sur le site ; c'est aussi `tests/rps.py`, l'environnement de test
de ce paquet). **Piège** : `observation_space(agent)` et
`action_space(agent)` doivent renvoyer le MÊME objet à chaque appel (le
`parallel_api_test` de PettingZoo le vérifie) — créer les spaces dans
`__init__`. Rien à changer dans `protocol`, `server` ni le SDK.

**Worker** (`worker.py`) : piloté par le serveur sur stdin/stdout, trames
MessagePack préfixées de leur taille (4 octets big-endian). Commandes
`describe` (catalogue, appelée une fois au démarrage du serveur), `start`,
`step`. Il valide chaque action contre l'`action_space` (un agent n'est pas
de confiance) et redirige tout `print` d'un environnement vers stderr pour
ne pas corrompre le protocole. `wire.py` fixe le format des spaces et des
valeurs sur le fil — le SDK en implémente l'autre moitié : toute
modification doit y être reportée.

## Tests

`python -m pytest` : registre (dont la découverte par entry points, simulée),
vérifications du contrat (y compris qu'elles attrapent les erreurs
courantes), worker en vrai sous-processus. Aucun test ne dépend d'un
environnement installé : ils jouent `tests/rps.py`, enregistré à la main
dans un registre isolé (`conftest.py`).

## Convention

Commentaires et docstrings en français ; métadonnées affichées par le site
(`title`, `description`, `documentation`) en anglais.
