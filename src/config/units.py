from components.unit import Unit
from enums.entity_type import *

from core.entity import Entity

from core.config import Config

from enums.animation import *
from enums.orientation import *
from enums.direction import *
from enums.unit_type import UnitType

from components.description import Description
from components.attack import Attack
from components.health import Health
from components.position import Position
from components.velocity import Velocity
from components.cost import Cost
from components.fly import Fly
from components.collider import Collider
from components.sprite import Sprite
from components.structure import Structure
from components.selection import Selection
from components.team import Team, PLAYER_1_TEAM

UNITS = {
    EntityType.CROSSBOWMAN: Entity(
        components=[
            Unit(EntityType.CROSSBOWMAN, UnitType.WALK),
            Description("Piglin Arbalétrier", "Guerrier d'attaque à distance"),
            Attack(damage=20, range=Config.TILE_SIZE() * 3, attack_speed=2.0),
            Health(90),
            Velocity(x=0, y=0, speed=80),
            Position(x=10, y=10),
            Cost(amount=425),
            Selection(),
            Collider(Config.TILE_SIZE() - 2, Config.TILE_SIZE() - 2),
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
    ),
    EntityType.BRUTE: Entity(
        components=[
            Unit(EntityType.BRUTE, UnitType.WALK),
            Description("Piglin Brute", "Unité de corps à corps"),
            Attack(damage=15, range=Config.TILE_SIZE(), attack_speed=1.0),
            Health(health=100),
            Velocity(x=0, y=0, speed=20),
            Cost(amount=350),
            Selection(),
            Collider(Config.TILE_SIZE(), Config.TILE_SIZE()),
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
                    },
                    Animation.WALK: {
                        Direction.DOWN: [1],
                        Direction.UP: [3],
                        Direction.LEFT: [2],
                        Direction.RIGHT: [0],
                    },
                },
                0.5,
            ),
        ]
    ),
    EntityType.GHAST: Entity(
        components=[
            Unit(EntityType.GHAST, UnitType.FLY),
            Description("Ghast", "Unité à distance ne ciblant que les structures"),
            Attack(damage=40, range=5, attack_speed=2.5),
            Health(health=70),
            Velocity(x=0, y=0, speed=40),
            Fly(),
            Cost(amount=820),
            Selection(),
            Collider(Config.TILE_SIZE(), Config.TILE_SIZE()),
            Team(PLAYER_1_TEAM),
            Sprite(
                "assets/sprites/spritesheet-ghast.png",
                24,
                24,
                {
                    Animation.IDLE: {
                        Direction.DOWN: [0, 4],
                        Direction.UP: [2, 6],
                        Direction.LEFT: [3, 7],
                        Direction.RIGHT: [1, 5],
                    },
                    Animation.WALK: {
                        Direction.DOWN: [0, 8],
                        Direction.UP: [2, 10],
                        Direction.LEFT: [3, 11],
                        Direction.RIGHT: [1, 9],
                    },
                },
                0.5,
            ),
        ]
    ),
}
