from core.component import Component
from typing import Type


class Entity:
    """
    Base class for all entities in the ECS architecture.

    _components: A list of components attached to the entity.
    """

    _components: list[Component]

    def __init__(self, components: list[Component]):
        """Initialize an entity with a list of components.

        Args:
            components (list[Component]): The components to attach to the entity.
        """
        self._components = components

    def add_component(self, component: Component):
        """Add a component to the entity.

        Args:
            component (Component): The component to add.
        """
        self._components.append(component)

    def remove_component(self, component: Component):
        """Remove a component from the entity.

        Args:
            component (Component): The component to remove.
        """
        self._components.remove(component)

    def get_component(self, componentType: Type) -> Component | None:
        """Get a component of a specific type from the entity.

        Args:
            componentType (Type): The type of the component to get.

        Returns:
            Component|None: The component if found, None otherwise.
        """
        for component in self._components:
            if isinstance(component, componentType):
                return component
        return None

    def get_all_components(self) -> list[Component]:
        """Get all components attached to the entity.

        Returns:
            list[Component]: The list of components.
        """
        return self._components
