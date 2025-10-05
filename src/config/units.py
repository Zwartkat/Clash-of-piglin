from components.fly import Fly
from config.layer import ENTITY_LAYER
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
from components.collider import Collider
from components.sprite import Sprite
from components.selection import Selection
from components.team import Team, PLAYER_1_TEAM

UNITS = {
    EntityType.CROSSBOWMAN: Entity(
        components=[
            EntityType.CROSSBOWMAN,
            UnitType.WALK,
            Description("Piglin Arbalétrier", "Guerrier d'attaque à distance"),
            Attack(damage=20, range=3, attack_speed=2.0),
            Health(90),
            Velocity(x=0, y=0, speed=2),
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
                1,
                sprite_size=(32, 32),
                priority=ENTITY_LAYER[UnitType.WALK],
            ),
        ]
    ),
    EntityType.BRUTE: Entity(
        components=[
            EntityType.BRUTE,
            UnitType.WALK,
            Description("Piglin Brute", "Unité de corps à corps"),
            Attack(damage=15, range=1, attack_speed=1.0),
            Health(100),
            Velocity(x=0, y=0, speed=3),
            Cost(amount=350),
            Selection(),
            Collider(Config.TILE_SIZE(), Config.TILE_SIZE()),
            Sprite(
                "assets/sprites/spritesheet-brute.png",
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
                    Animation.ATTACK: {
                        Direction.DOWN: [0],
                        Direction.UP: [0],
                        Direction.LEFT: [0],
                        Direction.RIGHT: [0, 16, 17],
                    },
                },
                1,
                sprite_size=(32, 32),
                priority=ENTITY_LAYER[UnitType.WALK],
            ),
        ]
    ),
    EntityType.GHAST: Entity(
        components=[
            EntityType.GHAST,
            UnitType.FLY,
            Description("Ghast", "Unité à distance ne ciblant que les structures"),
            Attack(damage=40, range=5, attack_speed=5),
            Health(700),
            Velocity(x=0, y=0, speed=2),
            Cost(amount=820),
            Selection(),
            Collider(Config.TILE_SIZE(), Config.TILE_SIZE()),
            Fly(),
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
                1,
                sprite_size=(32, 32),
                priority=ENTITY_LAYER[UnitType.FLY],
            ),
        ]
    ),
    EntityType.BASTION: Entity(
        components=[
            EntityType.BASTION,
            UnitType.STRUCTURE,
            Description("Bastion", "Base d'un joueur à défendre"),
            Health(1000),
            Sprite(
                "assets/sprites/spritesheet-bastion.png",
                500,
                500,
                {Animation.NONE: {Direction.NONE: [0]}},
                1000,
                sprite_size=(64, 64),
                priority=ENTITY_LAYER[UnitType.STRUCTURE],
                default_animation=Animation.NONE,
                default_direction=Direction.NONE,
            ),
        ]
    ),
}
