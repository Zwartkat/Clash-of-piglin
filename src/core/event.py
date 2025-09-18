from abc import ABC, abstractmethod


class Event(ABC):
    """
    Base class for all event types.
    """

    @abstractmethod
    def info(self) -> str:
        """Informations to debug/log"""
        pass
