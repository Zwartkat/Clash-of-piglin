import esper
from core.entity import Entity
from core.event_bus import EventBus
from events.death_event import DeathEvent
from components.team import Team
from components.attack import Attack
from components.health import Health
#from components.target import Target
from components.position import Position
from core.iterator_system import IteratingProcessor


class CombatSystem(IteratingProcessor):
    def __init__(self, event_bus):
        super().__init__(Attack, Entity, Position, Team)
        self.event_bus = event_bus

    def can_attack(self, ent, dt, attack, target, pos) -> bool:
        target_pos = esper.component_for_entity(target, Position)
        distance_squared = ((target_pos.x - pos.x)**2) + ((target_pos.y - pos.y)**2)
        if (attack.last_attack + attack.attack_speed <= dt) and distance_squared <= attack.range**2:
            return True
        else:
            return False

    def process_entity(self, ent, dt, attack, target, pos, team) -> None:
        if self.can_attack(ent, dt, attack, target, pos):
            target_health = esper.component_for_entity(target, Health)
            target_health.remaining -= attack.damage
            attack.last_attack = dt
            if target_health.remaining <= 0:
                target_health.remaining = 0
                self.event_bus.emit(DeathEvent(team, target))

