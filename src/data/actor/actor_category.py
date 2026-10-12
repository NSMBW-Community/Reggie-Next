from PyQt6 import QtWidgets


class ActorSubCategory:
    """Object representation of a actor subcategory."""

    def __init__(self, name: str | None, actor_ids: list[int]) -> None:
        self.name = name
        self.actor_ids = actor_ids


class ActorCategory:
    """Object representation of a top-level actor category."""

    def __init__(
        self,
        name: str | None,
        sub_categories: list[ActorSubCategory],
        nodes: list[QtWidgets.QTreeWidgetItem],
    ) -> None:
        self.name = name
        self.sub_categories = sub_categories
        self.nodes = nodes
