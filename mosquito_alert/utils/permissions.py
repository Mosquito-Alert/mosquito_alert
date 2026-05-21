from dataclasses import dataclass


@dataclass(frozen=True)
class CRUDPermission:
    add: bool = False
    change: bool = False
    view: bool = False
    delete: bool = False
