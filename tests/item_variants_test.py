from typing import List, Optional, Sequence

import pytest

from minerl.herobraine.env_spec import EnvSpec
from minerl.herobraine.env_specs import basalt_specs
from minerl.herobraine.hero import handlers


def inventory_spec_to_item_ids(inv_spec: Sequence[dict]) -> List[str]:
    result = []
    for d in inv_spec:
        item_type = d.get("type")
        metadata = d.get("metadata")
        item_id = utils.encode_item_with_metadata(item_type, metadata)
        result.append(item_id)
    return result


class VariantsTestEnvSpec(EnvSpec):
    def __init__(
            self,
            inventory_start_spec: Sequence[dict],
            equip_act_item_ids: Optional[Sequence[dict]] = None,
            equip_obs_item_ids: Optional[Sequence[dict]] = None,
            inventory_obs_item_ids: Optional[Sequence[dict]] = None,
            name: str ="VariantsTestEnvSpec",
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
        super().__init__(name=name)
        self.inventory_start_spec = inventory_start_spec
        inferred_item_ids = inventory_spec_to_item_ids(inventory_start_spec)
        if equip_act_item_ids is None:
            equip_act_item_ids = inferred_item_ids
        if equip_obs_item_ids is None:
            equip_obs_item_ids = inferred_item_ids
        if inventory_obs_spec is None:
            inventory_obs_spec = inferred_item_ids
        self.equip_act_item_ids = equip_act_item_ids
        self.equip_obs_item_ids = equip_obs_item_ids
        self.inventory_obs_item_ids = inventory_obs_item_ids

    def create_agent_start(self) -> List[handlers.Handler]:
        return [handlers.InventoryAgentStart(self.inventory_start_spec)]

    def create_observables(self) -> List[handlers.TranslationHandler]:
        return []

    def create_actionables(self) -> List[handlers.TranslationHandler]:
        return []

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


VILLAGE_ENV_SPEC = VariantsTestEnvSpec(basalt_specs.MAKE_HOUSE_VILLAGE_ITEMS)


def test_smoke_make_village_variants_env():
    def check_inventory(inv_obs):
        assert inv_obs.shape = (len(basalt_spec.MAKE_HOUSE_VILLAGE_ITEMS),)
        for i, d in enumerate(basalt_spec.MAKE_HOUSE_VILLAGE_ITEMS):
            item_id = util.encode_item_with_metadata(
                d["type"], d.get("metadata"))
            quantity = d["quantity"]
            assert inv_obs[i] == quantity

    with VILLAGE_ENV_SPEC.make() as env:
        obs = env.reset()


def test_equip_obs_handler():
    pass


def test_equip_act_handler():
    pass


def test_inventory_obs_handler():
    pass
