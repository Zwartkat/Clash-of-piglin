from components.attack import Attack
from components.collider import Collider
from components.health import Health
from components.selection import Selection
from components.sprite import Sprite
from components.stats import UnitType
from components.team import PLAYER_1_TEAM, Team
from components.velocity import Velocity
from components.fly import Fly
from components.position import Position
from components.cost import Cost
from config.constants import Animation, Direction
from config.unit_stats import UNIT_STATS
from core.entity import Entity


class Brute(Entity):

    def __init__(self):
        super().__init__(
            components=[
                Attack(damage=15, range=1, attack_speed=1.0),
                Health(health=100),
                Velocity(x=0, y=0, speed=20),
                Position(x=60, y=200),
                Cost(amount=350),
                Selection(),
                Collider(24, 24, "player"),
                Team(PLAYER_1_TEAM),
                UnitType("piglin_sword", UNIT_STATS["piglin_sword"]["name"]),
                Sprite(
                    "assets/sprites/spritesheet-brute.png",
                    24,
                    24,
                    {
                        Animation.IDLE: {
                            Direction.DOWN: [1],
                            Direction.UP: [3],
                            Direction.LEFT: [2],
                            Direction.RIGHT: [0],
                        }
                    },
                    0.5,
                ),
            ]
        )
