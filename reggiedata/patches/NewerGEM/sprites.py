# Newer Super Mario Bros. Wii
# Custom Reggie! Next sprites.py Module
# By Kamek64, MalStar1000, RoadrunnerWMC


from PyQt5 import QtCore, QtGui
Qt = QtCore.Qt

import spritelib as SLib
import sprites_common as common

ImageCache = SLib.ImageCache

################################################################################
################################################################################
################################################################################


class SpriteImage_LiftWheelGEM(SLib.SpriteImage_StaticMultiple):  # 52
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache["TestLift00"]
        )
    @staticmethod
    def loadImages():
        if 'TestLift00' in ImageCache: return
        SLib.loadIfNotInImageCache('TestLift00', 'test_lift_t00_yellow_black_blocks.png')
        SLib.loadIfNotInImageCache('TestLift01', 'test_lift_t01_beach_bridge.png')
        SLib.loadIfNotInImageCache('TestLift02', 'test_lift_t02_bone_platform.png')
        SLib.loadIfNotInImageCache('TestLift03', 'test_lift_t03_ice_blocks.png')
        SLib.loadIfNotInImageCache('TestLift04', 'test_lift_t04_silver_platform.png')
        SLib.loadIfNotInImageCache('TestLift05', 'test_lift_t05_golden_platform.png')
        

    def dataChanged(self):
    
        model = (self.parent.spritedata[2] & 0xF) % 7
        print(model)
        self.image = ImageCache['TestLift%02d' % model]

        super().dataChanged()





ImageClasses = {
    52: SpriteImage_LiftWheelGEM,

}
