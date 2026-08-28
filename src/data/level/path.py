from PyQt6 import QtCore, QtWidgets

import globals_
from src.data.level.abstract_path import AbstractPath
from src.data.level.items.path import PathItem
from src.data.level.items.path_editor_line import PathEditorLineItem


class Path(AbstractPath):
    """
    Class that manages a path and the line that connects the nodes.
    """

    class NodeData:
        """
        A simple class to store the data belonging to a node.
        """
        def __init__(self, speed, accel, delay):
            self.speed = speed
            self.accel = accel
            self.delay = delay

    def __init__(self, path_id, scene, loops = False):
        super().__init__()
        self._id = path_id
        self._scene = scene
        self._loops = loops
        self._node_data = []
        self._line_item = PathEditorLineItem(self)
        self._has_line = False

    def add_to_scene(self):
        """
        This adds all nodes to the scene. This function mainly exists to keep
        the API of this class similar to the LevelItem classes.
        """
        for node in self._nodes:
            self._scene.addItem(node)

        if not self._has_line:
            self._scene.addItem(self._line_item)
            self._has_line = True

    def set_id(self, new_id):
        """
        Changes the path's id and returns whether the path's id changed.
        """
        if self._id == new_id:
            return False

        self._id = new_id

        for node in self._nodes:
            node.set_path_id(new_id)

        return True

    def set_node_data(self, node, speed=None, accel=None, delay=None):
        """
        This function can change the speed, accel and delay values associated
        with a specific node. It only changes the parameters that are given, and
        returns whether a change was made.
        """
        data = self._node_data[self.get_index(node)]

        old_data = (data.speed, data.accel, data.delay)

        if speed is not None:
            data.speed = speed
        if accel is not None:
            data.accel = accel
        if delay is not None:
            data.delay = delay

        return (data.speed, data.accel, data.delay) != old_data

    def set_loops(self, value):
        """
        Changes whether the path loops or not. Returns True if the value was
        changed.
        """
        if self._loops == value:
            return False

        self._loops = value
        self._line_item.update_path()

        return True

    def set_freeze(self, frozen):
        """
        (Un)freezes this path, based on the boolean argument. Passing True causes
        all nodes to not be selectable or movable. Passing False does the opposite.
        """
        flag1 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable

        for node in self._nodes:
            node.setFlag(flag1, not frozen)
            node.setFlag(flag2, not frozen)

    def setVisible(self, value):
        """
        Shows or hides the path.
        """
        for node in self._nodes:
            node.setVisible(value)

        self._line_item.setVisible(value)

    def get_loops(self):
        return self._loops

    def get_index(self, node):
        return self._nodes.index(node)

    def get_node_data(self, index):
        """
        Returns a tuple containing the data required for the binary representation
        of the node at the specified index: x, y, speed, accel, delay.
        """
        node = self._nodes[index]
        data = self._node_data[index]

        return node.objx, node.objy, data.speed, data.accel, data.delay

    def get_points(self):
        """
        Returns a list of the positions of the nodes of this path. If this path
        loops, the first node's position is also the last position in the list.
        """
        points = []

        for node in self._nodes:
            points.append(QtCore.QPointF(node.objx, node.objy) * 1.5)

        if self._loops and points:
            points.append(points[0])

        return points

    def get_data_for_node(self, node_id):
        data = self._node_data[node_id]
        return data.speed, data.accel, data.delay

    def add_node(self, x, y, speed = 0.5, accel = 0.00498, delay = 0, index = None, add_to_list = True, add_to_scene = True):
        """
        Adds a node to the path at the specified position. If no index is given,
        the node is appended to the end of the path.
        """
        if globals_.mainWindow is None:
            return

        if index is None:
            index = len(self._nodes)

        node = PathItem(x, y, self._id, index, self)

        self._nodes.insert(index, node)
        self._node_data.insert(index, Path.NodeData(speed, accel, delay))

        if add_to_scene:
            self._scene.addItem(node)

        if add_to_list:
            node.positionChanged = globals_.mainWindow.HandlePathPosChange
            globals_.mainWindow.pathList.addItem(node.listitem)

        # Update ids of all nodes after the newly created node
        for new_id, later_node in enumerate(self._nodes[index + 1:], index + 1):
            later_node.update_id(new_id)

        # Update line item
        if not self._has_line:
            self._scene.addItem(self._line_item)
            self._has_line = True

        self._line_item.update_path()

        return node

    def remove_node(self, index):
        """
        Removes the node at a given index. Returns whether the path is empty after
        this node has been removed.
        """
        node = self._nodes[index]
        if globals_.mainWindow is None:
            return

        # Hacky stuff
        plist = globals_.mainWindow.pathList

        globals_.mainWindow.UpdateFlag = True
        plist.takeItem(plist.row(node.listitem))
        globals_.mainWindow.UpdateFlag = False

        sel_model = plist.selectionModel()
        if sel_model is not None:
            sel_model.clearSelection()

        # Remove node from internal lists
        del self._nodes[index]
        del self._node_data[index]

        # Update ids of later nodes
        for new_id, later_node in enumerate(self._nodes[index:], index):
            later_node.nodeid = new_id
            later_node.update()

        # Update line item
        self._line_item.update_path()

        return len(self._nodes) == 0

    def move_node(self, node, new_id):
        """
        This function moves a given node to a new position in the path. All items
        between the original position of the given node and the new id are shifted
        by 1 position.
        """
        old_id = self.get_index(node)

        if old_id == new_id:
            return

        node_data = self._node_data[old_id]

        if old_id < new_id:
            # Move all nodes [old_id: new_id] one position back
            self._nodes[old_id:new_id] = self._nodes[old_id + 1:new_id + 1]
            self._node_data[old_id:new_id] = self._node_data[old_id + 1:new_id + 1]
        else:
            # Move all nodes [new_id: old_id] one position forward
            self._nodes[new_id + 1:old_id + 1] = self._nodes[new_id:old_id]
            self._node_data[new_id + 1:old_id + 1] = self._node_data[new_id:old_id]

        # Move node to position new_id
        self._nodes[new_id] = node
        self._node_data[new_id] = node_data

        # Update all the nodes that moved, and the line item
        for new_id, node in enumerate(self._nodes):
            node.update_id(new_id)

        self._line_item.update_path()

    def node_moved(self, node):
        self._line_item.update_path()

    def __len__(self):
        """
        Returns the number of nodes.
        """
        return len(self._nodes)
