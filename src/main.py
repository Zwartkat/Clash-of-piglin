import pygame
import esper

from events import event_bus
from events.event_move import EventMoveTo
from systems.mouvement_system import MovementSystem
from components.position import Position
from components.velocity import Velocity
from systems.player_move_system import PlayerMoveSystem

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Crée le monde Esper
world = esper
world.add_processor(MovementSystem())

# Crée l'entité et ses composants
entity = world.create_entity()
world.add_component(entity, Position(x=100, y=200))
world.add_component(entity, Velocity(x=0, y=0))

# Crée l'EventBus et le système de déplacement joueur
event_bus_instance = event_bus.EventBus()
player_move_system = PlayerMoveSystem(event_bus_instance)
world.add_processor(player_move_system)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            event_bus_instance.emit(EventMoveTo(entity, x, y))

    world.process(1/60)  # dt = 1/60 pour 60 FPS

    screen.fill((0, 0, 0))  # fond noir
    for ent, pos in world.get_component(Position):
        pygame.draw.circle(screen, (255, 0, 0), (int(pos.x), int(pos.y)), 10)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()