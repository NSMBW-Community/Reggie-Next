from PyQt6 import QtCore

from data.actor.actorfield.actor_field import ActorField


class ListActorField(ActorField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        model: QtCore.QAbstractItemModel,
        idtype: str | None,
    ) -> None:
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.model = model
        self.idtype = idtype
