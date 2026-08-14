import globals_
import spritelib as SLib
from src.data import archive
from src.data.level.abstract_level import AbstractLevel
from src.data.level.area import Area


class NSMBWLevel(AbstractLevel):
    """
    Class for a level from New Super Mario Bros. Wii
    """

    def __init__(self):
        """
        Initializes the level with default settings
        """
        super().__init__()
        self.new(False)

    def new(self, load=True):
        """
        Creates a completely new level
        """
        # Create area objects
        self.areas = []

        new_area = Area(1)

        if load:
            new_area.load_defaults()

        globals_.Area = new_area
        SLib.Area = new_area

        self.areas.append(new_area)

    def load(self, data, areaToLoad):
        """
        Loads a NSMBW level from bytes data.
        """
        super().load(data, areaToLoad)

        arc = archive.U8.load(data)

        if "course" not in arc:
            return False

        # Sort the area data
        areaData = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        for name, val in arc.files:
            if val is None: continue
            name = name.replace('\\', '/').split('/')[-1]

            if not name.startswith('course'): continue
            if not name.endswith('.bin'): continue
            if '_bgdatL' in name:
                # It's a layer file
                if len(name) != 19: continue
                try:
                    thisArea = int(name[6])
                    laynum = int(name[14])
                except ValueError:
                    continue
                if not (0 < thisArea < 5): continue

                areaData[thisArea - 1][laynum + 1] = val
            else:
                # It's the course file
                if len(name) != 11: continue
                try:
                    thisArea = int(name[6])
                except ValueError:
                    continue
                if not (0 < thisArea < 5): continue

                areaData[thisArea - 1][0] = val

        # Create area objects
        self.areas = []
        for i, d in enumerate(areaData, 1):
            course, L0, L1, L2 = d

            if course is None:
                continue

            new_area = Area(i)
            new_area.set_data(course, L0, L1, L2)
            self.areas.append(new_area)

        self.areas[areaToLoad - 1].load()
        globals_.Area = self.areas[areaToLoad - 1]
        SLib.Area = self.areas[areaToLoad - 1]

        return True

    def save(self):
        """
        Save the level back to a file
        """

        # Make a new archive
        newArchive = archive.U8()

        # Create a folder within the archive
        newArchive['course'] = None

        # Go through the areas, save them and add them back to the archive
        for i, area in enumerate(self.areas):
            assert area.areanum == i + 1, (area.areanum, i + 1)

            course, L0, L1, L2 = area.save()

            # Layers 0 and 2 are optional, but the game assumes that the course
            # file and layer 1 will always exist (see dBg_c::CheckExistLayer())
            newArchive['course/course%d.bin' % area.areanum] = course
            newArchive['course/course%d_bgdatL1.bin' % area.areanum] = L1

            if L0 is not None:
                newArchive['course/course%d_bgdatL0.bin' % area.areanum] = L0

            if L2 is not None:
                newArchive['course/course%d_bgdatL2.bin' % area.areanum] = L2

        # return the U8 archive data
        return newArchive._dump()

    def appendArea(self, course_new, L0_new, L1_new, L2_new):
        """
        Creates a new area and adds it to the current level.
        """
        # Add new area
        new_area = Area(len(self.areas) + 1)
        new_area.set_data(course_new, L0_new, L1_new, L2_new)
        self.areas.append(new_area)

    def changeArea(self, number):
        """
        Changes the current area to the specified area in the loaded level
        archive. Note that number is 1-based, not 0-based.
        """
        current_num = globals_.Area.areanum

        # self.areas[current_num - 1] should be unloaded.
        self.areas[current_num - 1].unload()

        # Set the globals properly
        globals_.Area = self.areas[number - 1]
        SLib.Area = self.areas[number - 1]

        # self.areas[number - 1] should be loaded.
        self.areas[number - 1].load()

        return True
