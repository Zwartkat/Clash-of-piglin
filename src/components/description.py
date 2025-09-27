from dataclasses import dataclass

from core.component import Component


@dataclass(frozen=True)
class Description(Component):
    name: str
    description: str
