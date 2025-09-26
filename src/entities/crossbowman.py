from components.attack import Attack
from components.health import Health
from components.position import Position
from components.velocity import Velocity
from components.cost import Cost
from components.sprite import Sprite
from components.selection import Selection
from components.collider import Collider
from config.constants import Animation, Direction
from core.config import Config
from core.entity import Entity
from components.stats import UnitType
from components.team import Team, PLAYER_1_TEAM

from config.unit_stats import UNIT_STATS


class Crossbowman(Entity):

    def __init__(self):
        health = Health(90)
        health.remaining = 40
        super().__init__(
            components=[
                Attack(damage=20, range=3, attack_speed=2.0),
                health,
                Velocity(x=0, y=0, speed=80),
                Position(x=10, y=10),
                Cost(amount=425),
                Selection(),
                Collider(Config.TILE_SIZE(), Config.TILE_SIZE(), "player"),
                Team(PLAYER_1_TEAM),
                UnitType("piglin_crossbow", UNIT_STATS["piglin_crossbow"]["name"]),
                Sprite(
                    "assets/sprites/spritesheet-piglin.png",
                    24,
                    24,
                    {
                        Animation.IDLE: {
                            Direction.DOWN: [1, 5],
                            Direction.UP: [3, 7],
                            Direction.LEFT: [2, 6],
                            Direction.RIGHT: [0, 4],
                        },
                        Animation.WALK: {
                            Direction.DOWN: [1, 10, 1, 11],
                            Direction.UP: [3, 14, 3, 15],
                            Direction.LEFT: [2, 12, 2, 13],
                            Direction.RIGHT: [0, 8, 0, 9],
                        },
                    },
                    0.2,
                ),
            ]
        )
