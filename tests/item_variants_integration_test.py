from typing import List, Optional, Sequence

import numpy as np
import pytest

from minerl.herobraine.env_spec import EnvSpec
from minerl.herobraine.env_specs import basalt_specs
from minerl.herobraine.hero import handlers
from minerl.herobraine.hero.handlers import util


class VariantsTestEnvSpec(EnvSpec):
    def __init__(
            self,
            inventory_start_spec: Sequence[dict],
            equip_act_item_ids: Optional[Sequence[dict]] = None,
            equip_obs_item_ids: Optional[Sequence[dict]] = None,
            inventory_obs_item_ids: Optional[Sequence[dict]] = None,
            name: str = "VariantsTestEnvSpec",
    ):
        """
        Args:
            inventory_start_spec: A list of dicts with the keys "type" and "quantity".
                Optionally these dicts can have the key "metadata". `equip_act_spec`,
                `equip_obs_spec`, and `inventory_obs_spec` will be automatically generated
                from this argument if they are not provided.
            equip_act_spec: A list of dicts with the keys "type" and optionally "metadata".
                Any other keys are ignored.
            equip_obs_spec: A metadata of dicts with the keys "type" and optionally "metadata"
                Any other keys are ignored.
            inventory_obs_spec: A list of dicts with the keys "type" and optionally
                "variant". Any other keys are ignored.
        """
        self.inventory_start_spec = inventory_start_spec
        inferred_item_ids = util.inventory_start_spec_to_item_ids(inventory_start_spec)
        if equip_act_item_ids is None:
            equip_act_item_ids = inferred_item_ids
        if equip_obs_item_ids is None:
            equip_obs_item_ids = inferred_item_ids
        if inventory_obs_item_ids is None:
            inventory_obs_item_ids = inferred_item_ids
        self.equip_act_item_ids = equip_act_item_ids
        self.equip_obs_item_ids = equip_obs_item_ids
        self.inventory_obs_item_ids = inventory_obs_item_ids
        super().__init__(name=name)

    def create_agent_start(self) -> List[handlers.Handler]:
        return [handlers.SimpleInventoryAgentStart(self.inventory_start_spec)]

    def create_observables(self) -> List[handlers.TranslationHandler]:
        return [
            handlers.POVObservation([64, 64]),
            handlers.FlatInventoryObservation(self.inventory_obs_item_ids),
            handlers.EquippedItemObservation(self.equip_obs_item_ids),
        ]  # Required for Malmo to not error..

    def create_actionables(self) -> List[handlers.TranslationHandler]:
        return [
            handlers.EquipAction(self.equip_act_item_ids),
        ]

    def is_from_folder(self, folder: str) -> bool:
        return False

    def create_rewardables(self) -> List[handlers.TranslationHandler]:
        return []

    def create_agent_handlers(self) -> List[handlers.Handler]:
        return []

    def create_monitors(self) -> List[handlers.TranslationHandler]:
        return []

    def create_server_initial_conditions(self) -> List[handlers.Handler]:
        return [
            handlers.TimeInitialCondition(allow_passage_of_time=False),
            handlers.SpawningInitialCondition(allow_spawning=True),
        ]

    def create_server_decorators(self) -> List[handlers.Handler]:
        return []

    def create_server_world_generators(self) -> List[handlers.Handler]:
        return [handlers.DefaultWorldGenerator()]

    def create_server_quit_producers(self) -> List[handlers.Handler]:
        return [handlers.ServerQuitWhenAnyAgentFinishes()]

    def determine_success_from_rewards(self, rewards: list) -> bool:
        return False

    def get_docstring(self):
        return "Test EnvSpec"

    def check_observation_space(self):
        obs_spaces = self.create_observation_space().spaces

        equip_actual_keys = sorted(obs_spaces['equipped_items']['mainhand']['type'].values)
        equip_expected_keys = sorted(set(self.equip_obs_item_ids) | {'none', 'other'})
        assert equip_actual_keys == equip_expected_keys

        inv_actual_keys = sorted(obs_spaces['inventory'].spaces.keys())
        inv_expected_keys = sorted(
            util.inventory_start_spec_to_item_ids(self.inventory_start_spec))
        assert inv_actual_keys == inv_expected_keys

    def check_action_space(self):
        act_spaces = self.create_action_space().spaces

        equip_actual_keys = sorted(act_spaces['equip'].values)
        equip_expected_keys = sorted(set(self.equip_act_item_ids) | {'none', 'other'})
        assert equip_actual_keys == equip_expected_keys


SIMPLE_ENV_SPEC = VariantsTestEnvSpec(
    [
        dict(type="planks", metadata=0, quantity=1),
        dict(type="planks", metadata=1, quantity=1),
    ]
)
VILLAGE_ENV_SPEC = VariantsTestEnvSpec(basalt_specs.MAKE_HOUSE_VILLAGE_INVENTORY)

SPECS = [SIMPLE_ENV_SPEC, VILLAGE_ENV_SPEC]


@pytest.mark.parametrize("spec", SPECS)
class TestVariantEnvs:
    def test_spaces(self, spec: VariantsTestEnvSpec):
        spec.check_observation_space()
        spec.check_action_space()

    @pytest.mark.serial
    def test_starting_inventory(self, spec):
        with spec.make() as env:
            obs = env.reset()
            inv_obs = obs["inventory"]
            actual_keys = inv_obs.keys()
            expected_keys = util.inventory_start_spec_to_item_ids(spec.inventory_start_spec)
            assert sorted(actual_keys) == sorted(expected_keys)
            for i, d in enumerate(spec.inventory_start_spec):
                item_id = util.encode_item_with_metadata(d["type"], d.get("metadata"))
                quantity = d["quantity"]
                assert inv_obs[item_id] == quantity

    @pytest.mark.serial
    def test_randomized_equips(self, spec):
        with spec.make() as env:
            env.reset()

            # Choose equip from all items except special items 'none' and 'other'
            equip_choices = list(
                set(env.action_space['equip'].values).difference({'none', 'other'}))
            act = env.action_space.sample()
            for step in range(20):
                choice = equip_choices[np.random.randint(len(equip_choices))]
                act["equip"] = choice
                _ = env.step(act)

                # Equip action doesn't trigger for a few ticks, so run a few no-ops first.
                # If we looked at the observation returned by the call to step that
                # actually equips things, then we'd see that the observed mainhand item
                # has not actually been changed yet.
                for _ in range(3):
                    obs, rew, done, _ = env.step(env.action_space.no_op())

                mainhand_obs = obs['equipped_items']['mainhand']
                assert mainhand_obs['type'] == choice
                if done:
                    env.reset()
