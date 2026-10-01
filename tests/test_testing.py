"""Les vérifications du contrat, telles que les paquets d'environnement les
utilisent : elles passent sur un environnement conforme, et attrapent les
erreurs courantes avec un message utile."""

import numpy as np
import pytest
from gymnasium import spaces

import frondori_engine
from frondori_engine.testing import (
    check_environment,
    check_metadata,
    check_observations_fit_their_space,
    check_pettingzoo_api,
)
from rps import RockPaperScissorsEnv


def test_a_conforming_environment_passes_the_whole_contract():
    check_environment("rps-v0")


class SpacesRecreatedOnEveryCall(RockPaperScissorsEnv):
    def action_space(self, agent):
        return spaces.Discrete(4)


class ObservationOutOfItsSpace(RockPaperScissorsEnv):
    def _observations(self):
        observations = super()._observations()
        for observation in observations.values():
            observation["rounds_left"] = 1000
        return observations


class EloWithThreeAgents(RockPaperScissorsEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.possible_agents = ["player_0", "player_1", "player_2"]


class NoBudget(RockPaperScissorsEnv):
    metadata = {**RockPaperScissorsEnv.metadata, "compute_budget_ms": None}


@pytest.mark.parametrize(
    ("broken", "check", "message"),
    [
        (SpacesRecreatedOnEveryCall, check_pettingzoo_api, "same space object"),
        (ObservationOutOfItsSpace, check_observations_fit_their_space, "sort de son observation_space"),
        (EloWithThreeAgents, check_metadata, "duel"),
        (NoBudget, check_metadata, "compute_budget_ms"),
    ],
)
def test_common_mistakes_are_caught(broken, check, message):
    frondori_engine.register("broken-v0", broken)

    with pytest.raises(AssertionError, match=message):
        check("broken-v0")


def test_the_neutral_action_is_the_zero_of_the_action_space():
    from frondori_engine import wire

    assert wire.neutral_action(spaces.Discrete(4)) == 0
    box = wire.neutral_action(spaces.Box(-1, 1, shape=(2, 3), dtype=np.float32))
    assert box.shape == (2, 3) and not box.any()
