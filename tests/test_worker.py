"""Le worker, testé comme le serveur l'utilise : un vrai sous-processus,
piloté en MessagePack par son entrée et sa sortie standard. Il joue
l'environnement d'exemple (`tests/rps.py`), enregistré avant de démarrer."""

import json
import struct
import subprocess
import sys
import textwrap
from pathlib import Path

import msgpack
import pytest

TESTS = Path(__file__).parent

BOOTSTRAP = textwrap.dedent(f"""
    import sys
    sys.path.insert(0, {str(TESTS)!r})
    import frondori_engine
    from rps import RockPaperScissorsEnv
    frondori_engine.register("rps-v0", RockPaperScissorsEnv, package="frondori-rps")
    {{extra}}
    from frondori_engine.worker import main
    main()
""")


class Worker:
    def __init__(self, extra: str = ""):
        self._process = subprocess.Popen(
            [sys.executable, "-c", BOOTSTRAP.replace("{extra}", textwrap.dedent(extra))],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

    def request(self, message: dict) -> dict:
        payload = msgpack.packb(message, use_bin_type=True)
        self._process.stdin.write(struct.pack(">I", len(payload)) + payload)
        self._process.stdin.flush()
        (size,) = struct.unpack(">I", self._process.stdout.read(4))
        return msgpack.unpackb(self._process.stdout.read(size), raw=False)

    def close(self) -> None:
        self._process.stdin.close()
        assert self._process.wait(timeout=10) == 0


@pytest.fixture
def worker():
    w = Worker()
    yield w
    w.close()


def test_describe_gives_what_the_server_and_the_website_need(worker):
    reply = worker.request({"cmd": "describe"})

    assert reply["ok"]
    rps = reply["environments"]["rps-v0"]
    assert rps["agents"] == ["player_0", "player_1"]
    assert rps["tick_rate"] == 10.0
    assert rps["ranking"] == "elo"
    assert rps["compute_budget_ms"] == 50.0
    assert rps["title"] == "Rock Paper Scissors"
    assert rps["documentation"]
    assert rps["package"] == "frondori-rps"
    assert rps["action_spaces"]["player_0"] == {"type": "discrete", "n": 4, "start": 0}
    assert rps["observation_spaces"]["player_0"]["type"] == "dict"


def test_an_episode_runs_through_the_worker(worker):
    start = worker.request({"cmd": "start", "env_id": "rps-v0", "seed": 0})

    assert start["ok"]
    assert start["agents"] == ["player_0", "player_1"]
    assert start["observations"]["player_0"] == {"opponent_last": 0, "rounds_left": 100}
    json.loads(start["scene"])

    # player_0 joue la pierre (1), player_1 n'a pas répondu à temps (nil).
    step = worker.request({"cmd": "step", "actions": {"player_0": 1, "player_1": None}})

    assert step["ok"]
    assert step["rejected"] == []
    assert step["rewards"] == {"player_0": 1.0, "player_1": -1.0}
    assert step["observations"]["player_1"]["opponent_last"] == 1
    assert step["infos"]["player_0"] == {"score": 1}


def test_invalid_actions_are_replaced_by_the_neutral_action(worker):
    worker.request({"cmd": "start", "env_id": "rps-v0", "seed": 0})

    step = worker.request({"cmd": "step", "actions": {"player_0": 42, "player_1": "n'importe quoi"}})

    assert step["ok"]
    assert sorted(step["rejected"]) == ["player_0", "player_1"]
    # Les deux ont "passé" (action neutre 0) : manche nulle.
    assert step["rewards"] == {"player_0": 0.0, "player_1": 0.0}


def test_an_error_is_reported_without_killing_the_worker(worker):
    reply = worker.request({"cmd": "start", "env_id": "chess-v0", "seed": 0})

    assert not reply["ok"]
    assert "chess-v0" in reply["error"]
    assert worker.request({"cmd": "describe"})["ok"]


def test_a_stray_print_in_an_environment_does_not_corrupt_the_protocol():
    worker = Worker("""
        class Noisy(RockPaperScissorsEnv):
            def reset(self, seed=None, options=None):
                print("un print oublié dans un environnement")
                return super().reset(seed=seed, options=options)

        frondori_engine.register("noisy-v0", Noisy)
    """)

    reply = worker.request({"cmd": "start", "env_id": "noisy-v0", "seed": 0})

    assert reply["ok"]
    worker.close()
