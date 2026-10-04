from PyQt6 import QtCore

from ui.widgets.level_scene import LevelScene


class AbstractPath:
    """
    Abstract base class for the path manager. Provides only necessary fields and methods.
    Mainly used for instance checks while preventing circular imports.
    """

    def __init__(self, path_id: int, scene: LevelScene, loops: bool = False) -> None:
        self._nodes = []
        self._node_data = []
        self._id = path_id
        self._scene = scene
        self._loops = loops

    def __len__(self) -> int:
        """
        Returns the number of nodes.
        """
        return len(self._nodes)

    def get_index(self, node) -> int:
        """
        Returns the index of a node.
        """
        return self._nodes.index(node)

    def get_node_data(self, index: int) -> tuple[int, int, float, float, float]:
        """
        Returns a tuple containing the data required for the binary representation
        of the node at the specified index: x, y, speed, accel, delay.
        """
        node = self._nodes[index]
        data = self._node_data[index]

        return node.objx, node.objy, data.speed, data.accel, data.delay


    def get_points(self) -> list[QtCore.QPointF]:
        """
        Returns a list of the positions of the nodes of this path. If this path
        loops, the first node's position is also the last position in the list.
        """

        return []

    def remove_node(self, index: int) -> bool:
        """
        Removes the node at a given index. Returns whether the path is empty after
        this node has been removed.
        """
        return True

    def node_moved(self, node) -> None:
        """
        Called when a path node is moved.
        """
