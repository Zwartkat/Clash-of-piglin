from components.position import Position
from components.velocity import Velocity
from components.collider import Collider
from components.team import Team
from components.attack import Attack
from components.selection import Selection
from components.effects import OnTerrain
from components.health import Health
from components.stats import UnitType
from config.unit_stats import UNIT_STATS
from systems.entity_factory import EntityFactory


class UnitFactory:
    @staticmethod
    def create_unit(unit_type, x, y, team_id):
        stats = UNIT_STATS.get(unit_type)
        if not stats:
            raise ValueError(f"Unknown unit type: {unit_type}")

        velocity_component = Velocity(x=0, y=0, speed=stats["speed"])

        components = [
            Position(x, y),
            velocity_component,  # ← AJOUTER ICI !
            Collider(
                width=stats["size"]["width"],
                height=stats["size"]["height"],
                collision_type=stats["collision_type"],
            ),
            Team(team_id),
            Health(stats["health"]),
            Attack(
                damage=stats["attack"]["damage"],
                range=stats["attack"]["range"],
                attack_speed=stats["attack"]["attack_speed"],
                last_attack=0,
            ),
            UnitType(unit_type, stats["name"]),
            OnTerrain(),
            Selection(False),
        ]

        entity = EntityFactory.create(*components)

        return entity

    @staticmethod
    def create_squad(unit_type, positions, team_id):
        entities = []
        for x, y in positions:
            entity = UnitFactory.create_unit(unit_type, x, y, team_id)
            entities.append(entity)
        return entities

    @staticmethod
    def get_unit_cost(unit_type):
        stats = UNIT_STATS.get(unit_type, {})
        return stats.get("cost", 0)
