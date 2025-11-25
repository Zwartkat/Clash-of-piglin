from ai.world_perception import WorldPerception
from components.ai_controller import AIController
from components.base.team import Team
from core.accessors import get_ai_mapping, get_debugger, get_map, get_world_perception
from core.ecs.iterator_system import IteratingProcessor
from enums.entity.entity_type import EntityType

# from systems.ai_system import AiSystem as individual_ai_system


class AiSystem(IteratingProcessor):

    def __init__(self):
        super().__init__(EntityType, AIController, Team)
        self.world_perception = get_world_perception()
        self.ai_mapping = get_ai_mapping()
        self.debugger = get_debugger()

    def process_entity(
        self, ent, dt, ent_type: EntityType, ctrl: AIController, team: Team
    ):
        if ent_type != EntityType.BASTION:
            ai_key = self.ai_mapping[ent_type][team.team_id]

            if not ai_key:
                self.debugger.error(
                    f"{ent} >> Aucune IA trouvée pour {ent_type.name}, team {team.team_id}"
                )
                return

            if ai_key not in ["ADMA", "JEVA", "MAPI"]:
                return

        if ctrl.state:
            ctrl.state.update(dt)
        if ctrl.brain:
            ctrl.brain.decide()
