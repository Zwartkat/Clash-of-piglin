from dataclasses import dataclass

from core.ecs.component import Component


@dataclass(frozen=True)
class Description(Component):
    name: str
    description: str
