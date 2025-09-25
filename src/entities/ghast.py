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


class Ghast(Entity):

    def __init__(self):
        super().__init__(
            components=[
                Attack(damage=40, range=5, attack_speed=2.5),
                Health(health=70),
                Velocity(x=0, y=0, speed=40),
                Fly(),
                Position(x=0, y=0),
                Cost(amount=820),
                Selection(),
                Collider(24, 24, "player"),
                Team(PLAYER_1_TEAM),
                UnitType("ghast", UNIT_STATS["ghast"]["name"]),
                Sprite(
                    "assets/sprites/spritesheet-ghast.png",
                    24,
                    24,
                    {
                        Animation.IDLE: {
                            Direction.DOWN: [0],
                            Direction.UP: [2],
                            Direction.LEFT: [3],
                            Direction.RIGHT: [1],
                        }
                    },
                    0.05,
                ),
            ]
        )
