TERRAIN_PROPERTIES = {
    "Netherrack": {
        "walkable": True,
        "movement_speed_modifier": 1.0,
        "description": "Terrain standard du Nether",
    },
    "Blue_netherrack": {
        "walkable": True,
        "movement_speed_modifier": 1.0,
        "description": "Terrain mystique, pas d'effet spécial",
    },
    "Red_netherrack": {
        "walkable": True,
        "movement_speed_modifier": 1.0,
        "description": "Terrain instable, ralentit les unités",
    },
    "Lava": {
        "walkable": False,
        "movement_speed_modifier": 0.0,
        "description": "Lave mortelle, bloque le passage",
    },
    "Soulsand": {
        "walkable": True,
        "movement_speed_modifier": 0.3,
        "description": "Sable des âmes, ralentit considérablement",
    },
}

COLLISION_TYPE_RULES = {
    "player": {
        "can_cross": {
            "Lava": False,
            "Netherrack": True,
            "Blue_netherrack": True,
            "Red_netherrack": True,
            "Soulsand": True,
        },
        "speed_bonus": 1.0,
    },
    "enemy": {
        "can_cross": {
            "Lava": False,
            "Netherrack": True,
            "Blue_netherrack": True,
            "Red_netherrack": True,
            "Soulsand": True,
        },
        "speed_bonus": 1.0,
    },
    "flying": {
        "can_cross": {
            "Lava": True,
            "Netherrack": True,
            "Blue_netherrack": True,
            "Red_netherrack": True,
            "Soulsand": True,
        },
        "speed_bonus": 1.0,
    },
}

COLLISION_CONFIG = {
    "enable_terrain_collision": True,
    "enable_map_borders": True,
    "enable_entity_collision": True,
    "map_border_buffer": 16,
}
