from enums.entity.entity_type import EntityType

IA_MAP = {
    EntityType.BRUTE: {1: "ADMA", 2: "ADMA"},
    EntityType.CROSSBOWMAN: {1: "SCPR", 2: "LOVA"},
    EntityType.GHAST: {1: "MAPI", 2: "JEVA"},
}

IA_MAP_JCJ = {
    EntityType.BRUTE: {1: "", 2: "ADMA"},
    EntityType.CROSSBOWMAN: {1: "", 2: "LOVA"},
    EntityType.GHAST: {1: "", 2: "JEVA"},
}
