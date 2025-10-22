from typing import Dict, Any
from core.debugger import Debugger
from enums.data_bus_key import DataBusKey


class DataBus:
    def __init__(self):
        self._store: Dict[DataBusKey, Any] = {}
        self.register(DataBusKey.DEBUGGER, Debugger(enabled=False))

    def register(self, key: DataBusKey, instance: Any):
        self._store[key] = instance
        self.get_debugger().log(f"{key} enregistré dans DataBus")

    def get(self, key: DataBusKey) -> Any:
        try:
            if self.has(key) is False:
                raise RuntimeError(f"{key} non enregistré dans DataBus")
            return self._store[key]
        except:
            self.get_debugger().error(f"{key} non trouvé dans DataBus")
            return None

    def has(self, key: DataBusKey) -> bool:
        return key in self._store

    def replace(self, key: DataBusKey, instance: Any):
        if self.has(key):
            self._store[key] = instance
            self.get_debugger().log(f"{key} remplacé dans DataBus")
        else:
            self.get_debugger().error(
                f"{key} non trouvé dans DataBus pour le remplacer"
            )

    def get_debugger(self) -> Debugger:
        if self.has(DataBusKey.DEBUGGER) is False:
            raise RuntimeError("DEBUGGER non enregistré dans DataBus")
        return self.get(DataBusKey.DEBUGGER)


DATA_BUS = DataBus()
