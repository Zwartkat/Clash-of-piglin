from components.gameplay.fly import Fly
from components.gameplay.target import Target
from config.layer import ENTITY_LAYER
from enums.entity.entity_type import *

from core.ecs.entity import Entity

from core.config import Config

from enums.entity.animation import *
from enums.entity.orientation import *
from enums.entity.direction import *
from enums.entity.unit_type import UnitType

from components.base.description import Description
from components.base.ai_flag import Ai_flag
from components.gameplay.structure import Structure
from components.gameplay.attack import Attack
from components.base.health import Health
from components.base.position import Position
from components.base.velocity import Velocity
from components.base.cost import Cost
from components.gameplay.collider import Collider
from components.rendering.sprite import Sprite
from components.gameplay.selection import Selection
from components.base.team import Team, PLAYER_1_TEAM

UNITS = {
    EntityType.CROSSBOWMAN: Entity(
        components=[
            EntityType.CROSSBOWMAN,
            UnitType.WALK,
            Description("Piglin Arbalétrier", "Guerrier d'attaque à distance"),
            Attack(damage=15, range=3, attack_speed=5.0),
            Health(90),
            Velocity(x=0, y=0, speed=1),
            Position(x=10, y=10),
            Cost(amount=500),
            Selection(),
            Ai_flag(),
            Collider(Config.TILE_SIZE() - 2, Config.TILE_SIZE() - 2),
            Sprite(
                "assets/sprites/spritesheet-piglin.png",
                128,
                128,
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
                        Direction.DOWN: [17],
                        Direction.UP: [19],
                        Direction.LEFT: [18],
                        Direction.RIGHT: [16],
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
            Attack(damage=10, range=1, attack_speed=1),
            Health(100),
            Velocity(x=0, y=0, speed=2.5),
            Cost(amount=350),
            Selection(),
            Collider(Config.TILE_SIZE(), Config.TILE_SIZE()),
            Target(allow_targets=[UnitType.WALK, UnitType.STRUCTURE]),
            Sprite(
                "assets/sprites/spritesheet-brute.png",
                128,
                128,
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
                        Direction.DOWN: [18, 19],
                        Direction.UP: [22, 23],
                        Direction.LEFT: [2, 20, 21],
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
            Attack(damage=40, range=2, attack_speed=3),
            Health(70),
            Velocity(x=0, y=0, speed=0.5),
            Cost(amount=620),
            Selection(),
            Collider(Config.TILE_SIZE(), Config.TILE_SIZE()),
            Fly(),
            Target(),
            Sprite(
                "assets/sprites/spritesheet-ghast.png",
                128,
                128,
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
                    Animation.ATTACK: {
                        Direction.DOWN: [0, 12],
                        Direction.UP: [2],
                        Direction.LEFT: [3, 14],
                        Direction.RIGHT: [1, 13],
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
            Structure(),
            Description("Bastion", "Base d'un joueur à défendre"),
            Health(3000),
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
