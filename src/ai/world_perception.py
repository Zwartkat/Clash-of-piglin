import math
import esper

from components.base.health import Health
from components.base.position import Position
from components.base.team import Team
from components.gameplay.target import Target
from core.accessors import get_player_manager
from enums.entity.entity_type import EntityType
from enums.entity.unit_type import UnitType


class WorldPerception:
    """
    Global perception system shared by all AI entities.

    This class gathers and precomputes world information such as positions, health,
    allies, enemies, and danger levels. It is updated once per frame and allows
    each AI to make decisions based on consistent, shared data.

    Attributes:
        tile_size (int): Size of one tile in the game world.
        vision_range (dict[EntityType, int]): Vision range for each entity type.
        positions (dict[int, Position]): Position components of all entities.
        teams (dict[int, Team]): Team components of all entities.
        healths (dict[int, Health]): Health components of all entities.
        unit_types (dict[int, UnitType]): Unit type components of all entities.
        entity_types (dict[int, EntityType]): Entity type components of all entities.
        neighbors (dict[int, dict[int, float]]): Mapping of nearby entities and their distances.
        health_ratios (dict[int, float]): Ratio of current to full health for each entity.
        danger_scores (dict[int, float]): Calculated danger level for each entity.
        nearest_enemy (dict[int, tuple[int, float]]): Closest enemy entity and its distance.
        nearest_ally (dict[int, tuple[int, float]]): Closest ally entity and its distance.
    """

    def __init__(self, tile_size: int, vision_range: dict[EntityType, int]):
        """
        Initializes the global perception system.

        Args:
            tile_size (int): The size of a single tile in the map.
            vision_range (dict[EntityType, int]): Vision range per entity type.
        """
        self.tile_size: int = tile_size
        self.vision_range: dict[EntityType, int] = vision_range

        # Components
        self.positions: dict[int, Position] = {}
        self.teams: dict[int, Team] = {}
        self.healths: dict[int, Health] = {}
        self.unit_types: dict[int, UnitType] = {}
        self.entity_types: dict[int, EntityType] = {}

        # Precomputed data
        self.neighbors: dict[int, dict[int, float]] = {}
        self.health_ratios: dict[int, float] = {}
        self.danger_scores: dict[int, float] = {}
        self.nearest_enemy: dict[int, tuple[int, float]] = {}
        self.nearest_ally: dict[int, tuple[int, float]] = {}

        self.DEFAULT_VIEW_RANGE = 5 * self.tile_size

        # Bases
        # team ->
        self.bases: dict[int, tuple[int, float]] = {
            1: (get_player_manager().players[1].bastion, 0.0),
            2: (get_player_manager().players[2].bastion, 0.0),
        }

    def update(self):
        """
        Updates the world perception for the current frame.

        This method collects all components, computes distances, health ratios,
        danger levels, and nearest entities. It should be called once per frame.
        """
        self._collect_components()
        self._compute_health_ratios()
        self._compute_distances()
        self._compute_danger_scores()
        self._compute_nearest_entities()
        self._compute_base_danger()

    def _get_vision_range(self, ent: int) -> int:
        """
        Returns the vision range for a given entity.

        Args:
            ent (int): The entity ID.

        Returns:
            int: The vision range (in world units).
        """
        ent_type: EntityType = self.entity_types[ent]
        return self.vision_range.get(ent_type, self.DEFAULT_VIEW_RANGE)

    def _collect_components(self):
        """
        Collects all necessary ECS components for perception.

        This function fetches positions, health, teams, unit types, and entity types
        from the ECS engine and stores them in dictionaries for faster lookup.
        """
        self.positions.clear()
        self.healths.clear()
        self.teams.clear()
        self.unit_types.clear()
        self.entity_types.clear()

        for ent, (pos, health, team, unit_type, ent_type) in esper.get_components(
            Position, Health, Team, UnitType, EntityType
        ):
            self.positions[ent] = pos
            self.healths[ent] = health
            self.teams[ent] = team
            self.unit_types[ent] = unit_type
            self.entity_types[ent] = ent_type

    def _compute_health_ratios(self):
        """
        Computes the health ratio (remaining / full) for each entity.

        The ratio is used to estimate how strong or weak an entity currently is.
        """
        self.health_ratios = {
            ent: health.remaining / max(1, health.full)
            for ent, health in self.healths.items()
        }

    def _compute_distances(self):
        """
        Computes pairwise distances between entities within their vision range.

        It only keeps distances for entities that are visible to each other,
        considering team affiliation and targeting rules.
        """
        self.neighbors.clear()
        for ent1, pos1 in self.positions.items():
            self.neighbors[ent1] = {}
            vision_range = self._get_vision_range(ent1)

            allow_target = None
            if esper.has_component(ent1, Target):
                allow_target = esper.component_for_entity(ent1, Target).allow_targets

            for ent2, pos2 in self.positions.items():
                if ent1 == ent2:
                    continue

                if (
                    self.teams[ent1].team_id != self.teams[ent2].team_id
                    and allow_target
                    and self.entity_types[ent2] not in allow_target
                    and self.unit_types[ent2] not in allow_target
                ):
                    continue

                if ent2 in self.neighbors and ent1 in self.neighbors[ent2]:
                    self.neighbors[ent1][ent2] = self.neighbors[ent2][ent1]

                dist = math.hypot(pos2.x - pos1.x, pos2.y - pos1.y)
                if dist <= vision_range:
                    self.neighbors[ent1][ent2] = dist

    def _compute_danger_scores(self):
        """
        Computes a danger score for each entity.

        The danger score represents the level of threat an entity faces based on:
          - The number and proximity of visible enemies
          - The enemies' remaining health
          - The entity’s own health ratio

        The result is a value between 0 and 1, where higher values mean higher danger.
        """
        self.danger_scores.clear()
        for ent, team in self.teams.items():
            score = 0.0
            num_threat = 0
            vision_range = self._get_vision_range(ent)
            for other_ent, dist in self.neighbors.get(ent, {}).items():
                other_team = self.teams[other_ent]
                if other_team.team_id == team.team_id:
                    continue
                health_ratio = self.health_ratios.get(other_ent, 1.0)
                threat = max(0.0, (1 - dist / vision_range) * (1 + (1 - health_ratio)))
                score += threat
                num_threat += 1
            self.danger_scores[ent] = (score / max(1, num_threat)) * 0.6 + (
                1 - self.health_ratios[ent]
            ) * 0.4

    def _compute_nearest_entities(self):
        """
        Finds the nearest ally and enemy for each entity.

        For every entity, this method searches through visible neighbors
        to determine which ally and which enemy are closest.
        The results are stored in `nearest_enemy` and `nearest_ally`.
        """
        self.nearest_enemy.clear()
        self.nearest_ally.clear()

        for ent, team in self.teams.items():
            nearest_enemy = None
            nearest_enemy_dist = float("inf")
            nearest_ally = None
            nearest_ally_dist = float("inf")

            for other_ent, dist in self.neighbors.get(ent, {}).items():
                other_team = self.teams[other_ent]
                if other_team.team_id != team.team_id:
                    if dist < nearest_enemy_dist:
                        nearest_enemy = other_ent
                        nearest_enemy_dist = dist
                else:
                    if dist < nearest_ally_dist:
                        nearest_ally = other_ent
                        nearest_ally_dist = dist

            if nearest_enemy is not None:
                self.nearest_enemy[ent] = (nearest_enemy, nearest_enemy_dist)
            if nearest_ally is not None:
                self.nearest_ally[ent] = (nearest_ally, nearest_ally_dist)

    def _compute_base_danger(self):
        max_dist = self.tile_size * 6  # portée de vigilance

        for team, (ent, prev_danger) in self.bases.items():
            danger = 0.0
            enemy_pressure = 0.0
            ally_support = 0

            # Analyse des entités autour de la base
            for ent_id, dist in self.neighbors.get(ent, {}).items():
                if dist > max_dist:
                    continue

                # Ennemis proches => pression
                if self.teams[ent_id].team_id != team:
                    enemy_pressure += (max_dist - dist) / max_dist

                # Alliés proches => soutien
                else:
                    ally_support += 1

            # Contribution principale : ennemis proches
            if enemy_pressure > 0:
                danger += min(1.0, enemy_pressure)

            # Santé de la base : plus elle est basse, plus le danger monte
            health_ratio = self.health_ratios.get(ent, 1.0)
            danger += (1.0 - health_ratio) * 0.5  # pondération douce

            # Pas d’alliés proches => petit bonus de danger
            if ally_support == 0 and enemy_pressure > 0:
                danger += 0.2

            # Lissage : ne pas avoir de variations brutales
            # On redescend progressivement si plus de menace
            decay_rate = 0.1
            print(danger)
            danger = (prev_danger * (1 - decay_rate)) + (danger * decay_rate)
            print(danger)
            # Clamp final entre 0 et 1
            danger = max(0.0, min(danger, 1.0))
            self.bases[team] = (ent, danger)
