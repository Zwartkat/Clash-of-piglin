UNIT_STATS = {
    "piglin_sword": {
        "name": "Piglin Épéiste",
        "health": 100,
        "attack": {"damage": 10, "range": 100,"attack_speed" : 1},
        "speed": 80,
        "collision_type": "player",
        "size": {"width": 20, "height": 20},
        "cost": 150,
        "description": "Guerrier piglin au corps à corps, résistant mais lent",
    },
    "piglin_crossbow": {
        "name": "Piglin Arbalétrier",
        "health": 75,
        "attack": {"damage": 10, "range": 100,"attack_speed" : 1},
        "speed": 100,
        "collision_type": "player",
        "size": {"width": 18, "height": 18},
        "cost": 120,
        "description": "Archer piglin, rapide mais fragile",
    },
    "ghast": {
        "name": "Ghast",
        "health": 150,
        "attack": {"damage": 10, "range": 100,"attack_speed" : 1},
        "speed": 300,
        "collision_type": "flying",
        "size": {"width": 32, "height": 32},
        "description": "Créature volante du Nether",
    },
}

UNIT_COLORS = {
    "piglin_sword": (200, 100, 100),
    "piglin_crossbow": (100, 200, 100),
    "ghast": (150, 150, 200),
}
