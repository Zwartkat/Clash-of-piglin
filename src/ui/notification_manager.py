from core.accessors import get_event_bus
from events.spawn_unit_event import SpawnUnitEvent
from ui.notification import Notification


class NotificationManager:
    def __init__(self):
        self.notifications: list[Notification] = []
        get_event_bus().subscribe(SpawnUnitEvent, self.spawn_entity_notification)

    def spawn_entity_notification(self, event: SpawnUnitEvent):
        self.push(
            f"Apparition de {event.entity_type.value} pour le joueur {event.team.team_id}",
            3500,
        )

    def push(
        self, text: str, duration: int = 2500, color: tuple[int] = (255, 255, 255)
    ):
        """Ajoute une notification à afficher"""
        self.notifications.append(Notification(text, duration, color))

    def draw(self, surface):
        """Dessine toutes les notifications encore actives"""
        for i, notif in enumerate(self.notifications[:]):
            if not notif.draw(surface, i):
                self.notifications.remove(notif)
