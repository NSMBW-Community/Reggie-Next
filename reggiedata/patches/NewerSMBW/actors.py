# Newer Super Mario Bros. Wii
# Custom Reggie! Next sprites.py Module
# By Kamek64, MalStar1000, RoadrunnerWMC


from PyQt6 import QtCore, QtGui

import data.common.actors as common
import actorlib
from data import globals_

Qt = QtCore.Qt
ImageCache = actorlib.ImageCache

################################################################################
################################################################################
################################################################################

# Newer-specific base classes
class ActorImage_NewerSwitch(common.ActorImage_Switch):

    @staticmethod
    def loadImages():
        common.ActorImage_Switch.loadImages()

        if 'QSwitch2' not in ImageCache:
            for i in range(2, 5):
                p = actorlib.GetImage(f'q_switch{i}.png')

                if p is None:
                    # happens when the newer patch folder is not loaded yet
                    return

                ImageCache[f'QSwitch{i}'] = QtGui.QPixmap.fromImage(p)
                ImageCache[f'QSwitchU{i}'] = QtGui.QPixmap.fromImage(p.mirrored(True, True))

        if 'PSwitch2' not in ImageCache:
            for i in range(2, 5):
                p = actorlib.GetImage(f'P_switch{i}.png')
                ImageCache[f'PSwitch{i}'] = QtGui.QPixmap.fromImage(p)
                ImageCache[f'PSwitchU{i}'] = QtGui.QPixmap.fromImage(p.mirrored(True, True))

        if 'ESwitch2' not in ImageCache:
            for i in range(2, 5):
                p = actorlib.GetImage(f'e_switch{i}.png')
                ImageCache[f'ESwitch{i}'] = QtGui.QPixmap.fromImage(p)
                ImageCache[f'ESwitchU{i}'] = QtGui.QPixmap.fromImage(p.mirrored(True, True))

    def dataChanged(self):
        self.styleType = self.parent.spritedata[3] & 0xF

        self.yOffset = 0
        self.xOffset = 0

        if self.styleType == 1 or self.styleType > 4:
            self.styleType = 0

        # hack needed if data is changed before patch folder is loaded
        if 'QSwitch2' not in ImageCache:
            return

        super().dataChanged()

################################################################################
################################################################################
################################################################################

class ActorImage_Block(actorlib.ActorImage):  # 207, 208, 209, 221, 255, 256, 402, 403, 422, 423
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False

        rot_block_aux_image = actorlib.AuxiliaryImage(parent, 24, 24)
        rot_block_aux_image.setPos(0, 0)
        self.aux.append(rot_block_aux_image)

        rot_item_aux_image = actorlib.AuxiliaryImage(parent, 24, 24)
        rot_item_aux_image.setPos(0, 0)
        self.aux.append(rot_item_aux_image)

        self.tilenum = 1315
        self.contentsNybble = 5
        self.contentsOverride = None
        self.eightIsMushroom = False
        self.twelveIsMushroom = False
        self.rotates = False
        self.flipOverride = False
        self.transparent = False
        self.is_water_block = False

    def dataChanged(self):
        # SET CONTENTS
        # In the blocks.png file:
        # 0 = Empty, 1 = Coin, 2 = Mushroom, 3 = Fire Flower, 4 = Propeller, 5 = Penguin Suit,
        # 6 = Mini Shroom, 7 = Star, 8 = Continuous Star, 9 = Yoshi Egg, 10 = 10 Coins,
        # 11 = 1-up, 12 = Vine, 13 = Spring, 14 = Shroom/Coin, 15 = Ice Flower, 16 = Toad, 20 = Hammer
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage) or not isinstance(self.aux[1], actorlib.AuxiliaryImage):
            return

        if self.contentsOverride is not None:
            contents = self.contentsOverride
        else:
            contents = self.parent.spritedata[self.contentsNybble] & 0xF

        if contents == 2:  # Hammer
            contents = 20

        if contents == 12 and self.twelveIsMushroom:
            contents = 2  # 12 is a mushroom on some types
        if contents == 8 and self.eightIsMushroom:
            contents = 2  # same as above, but for type 8

        self.image = ImageCache[f'BlockContents{contents}']

        # SET UP ROTATION
        if self.rotates:
            transform = QtGui.QTransform()
            transform.translate(12, 12)

            angle = (self.parent.spritedata[4] & 0xF0) >> 4
            leftTilt = self.parent.spritedata[3] & 1

            angle *= (45.0 / 16.0)

            if leftTilt == 0:
                transform.rotate(angle)
            else:
                transform.rotate(360 - angle)

            transform.translate(-12, -12)
            self.transform = transform

            self.aux[0].image = actorlib.GetTile(self.tilenum).transformed(transform, QtCore.Qt.TransformationMode.SmoothTransformation)
            self.aux[0].setSize(self.aux[0].image.width(), self.aux[0].image.height())

            self.aux[1].image = ImageCache[f'BlockContents{contents}'].transformed(transform, QtCore.Qt.TransformationMode.SmoothTransformation)
            self.aux[1].setSize(self.aux[1].image.width(), self.aux[1].image.height())

            self.setSize((self.aux[0].image.width() / 1.5, self.aux[0].image.height() / 1.5))

        # Flip a switch override
        if self.flipOverride:
            flip = self.image.toImage().mirrored(True, True)
            self.image = self.image.fromImage(flip)

        # Sprite 433 scales the block by 1.5x
        if self.is_water_block:
            self.setOffset((-4, -4))
            self.setSize((36 / 1.5, 36 / 1.5))

    def paint(self, painter):
        if self.image is None or not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        if self.transparent:
            painter.setOpacity(0.5)
        else:
            painter.setOpacity(1.0)

        img_offs = 6 if self.is_water_block else 0
        scale = 36 if self.is_water_block else 24

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        if self.rotates:
            self.aux[0].image = actorlib.GetTile(self.tilenum).transformed(self.transform, QtCore.Qt.TransformationMode.SmoothTransformation)
            self.aux[0].setSize(self.aux[0].image.width(), self.aux[0].image.height())
        else:
            if self.tilenum < len(actorlib.Tiles):
                painter.drawPixmap(0, 0, actorlib.GetTile(self.tilenum).scaled(scale, scale))
            painter.drawPixmap(img_offs, img_offs, self.image)


class ActorImage_QBlock(ActorImage_Block):  # 207
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49


class ActorImage_QBlockUnused(ActorImage_Block):  # 208
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49
        self.eightIsMushroom = True
        self.twelveIsMushroom = True


class ActorImage_BrickBlock(ActorImage_Block):  # 209
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48


class ActorImage_RotatingQBlock(ActorImage_Block):  # 255
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49
        self.contentsNybble = 4
        self.twelveIsMushroom = True
        self.rotates = True


class ActorImage_RotatingBrickBlock(ActorImage_Block):  # 256
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48
        self.contentsNybble = 4
        self.twelveIsMushroom = True
        self.rotates = True


class ActorImage_NewerWoodCircle(actorlib.ActorImage_StaticMultiple):  # 286
    @staticmethod
    def loadImages():
        if 'WoodCircle0' in ImageCache:
            return
        for i in range(3):
            ImageCache[f'WoodCircle{i}'] = actorlib.GetPixmap(f'wood_circle_{i}.png')

        if 'GrayWoodCircle0' in ImageCache:
            return
        for i in range(3):
            ImageCache[f'GrayWoodCircle{i}'] = actorlib.GetPixmap(f'gray_wood_circle_{i}.png')

    def dataChanged(self):
        super().dataChanged()
        size = (self.parent.spritedata[5] & 0xF) % 3
        gray = self.parent.spritedata[2] & 1

        if gray:
            self.image = ImageCache[f'GrayWoodCircle{size}']
        else:
            self.image = ImageCache[f'WoodCircle{size}']

        if size > 2:
            size = 0
        self.dimensions = (
            (-24, -24, 64, 64),
            (-40, -40, 96, 96),
            (-56, -56, 128, 128),
        )[size]


class ActorImage_LineQBlock(ActorImage_Block):  # 402
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49
        self.twelveIsMushroom = True


class ActorImage_LineBrickBlock(ActorImage_Block):  # 403
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48


class ActorImage_StarCollectable(actorlib.ActorImage_Static):  # 12
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['StarCollectable'],
            (3, 3),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('StarCollectable', 'star_collectable.png')


class ActorImage_ClownCar(actorlib.ActorImage_Static):  # 13
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ClownCar'],
            (-20, -36),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ClownCar', 'clown_car.png')


class ActorImage_MusicBlock(actorlib.ActorImage_StaticMultiple): # 17
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (0, -45)

    @staticmethod
    def loadImages():
        if 'MusicBlock1' in ImageCache:
            return
        for i in range(8):
            ImageCache[f'MusicBlock{i + 1}'] = actorlib.GetPixmap(f'music_block_{i + 1}.png')

    def dataChanged(self):
        colour = (self.parent.spritedata[5] & 0xF) % 9

        if colour == 0:
            self.image = ImageCache['MusicBlock1']
        else:
            self.image = ImageCache[f'MusicBlock{colour}']

        super().dataChanged()


class ActorImage_DragonCoasterPiece(actorlib.ActorImage_StaticMultiple): # 18
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5
        )

        bone_piece_aux_image = actorlib.AuxiliaryImage(parent, 48, 29)
        self.aux.append(bone_piece_aux_image)

        self.xOffset = -16
        self.yOffset = -4

    @staticmethod
    def loadImages():
        if 'DragonHead' in ImageCache:
            return
        ImageCache['DragonHead'] = actorlib.GetPixmap('dragon_coaster_head.png')
        ImageCache['DragonBody'] = actorlib.GetPixmap('dragon_coaster_body.png')
        ImageCache['DragonTail'] = actorlib.GetPixmap('dragon_coaster_tail.png')

    def dataChanged(self):
        piece = self.parent.spritedata[5] & 3
        direction = (self.parent.spritedata[3] >> 4) & 1
        rotates = self.parent.spritedata[2] & 0x10

        sPiece = ("Head", "Body", "Tail")[piece]

        transform = QtGui.QTransform()
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        if direction == 1:
            transform.translate(12, 0)
            transform.scale(-1, 1)
            transform.translate(-12, 0)

        if rotates:
            angle = self.parent.spritedata[2] & 0xF

            if angle < 8:
                angle -= 8
                offs_x = 0
            else:
                angle -= 7
                offs_x = -4

            angle *= (180.0 / 16)

            transform.translate(24, 15)
            transform.rotate(angle)
            transform.translate(-24, -15)
            offs_y = -6
        else:
            # Reset angle
            offs_x = 0
            offs_y = 0
            transform.rotate(0)

        self.aux[0].image = ImageCache[f'Dragon{sPiece}'].transformed(transform, QtCore.Qt.TransformationMode.SmoothTransformation)
        self.aux[0].setSize(self.aux[0].image.width(), self.aux[0].image.height(), offs_x, offs_y)

        self.setSize((self.aux[0].image.width() / 1.5, self.aux[0].image.height() / 1.5))

    def paint(self, painter):
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
        super().paint(painter)


class ActorImage_SamuraiGuy(actorlib.ActorImage_Static):  # 19
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SamuraiGuy'],
            (-8, -13),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SamuraiGuy', 'samurai_guy.png')


class ActorImage_NewerGoomba(actorlib.ActorImage_StaticMultiple):  # 20
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Goomba', 'goomba.png')
        if 'Goomba1' in ImageCache:
            return
        for i in range(8):
            ImageCache[f'Goomba{i + 1}'] = actorlib.GetPixmap(f'goomba_{i + 1}.png')

    def dataChanged(self):

        color = (self.parent.spritedata[2] & 0xF) % 9

        if color == 0:
            self.image = ImageCache['Goomba']
            self.offset = (-1, -4)
        else:
            self.image = ImageCache[f'Goomba{color}']
            self.offset = (0, -4) if color not in (7, 8) else (0, -5)

        super().dataChanged()


class ActorImage_NewerParaGoomba(actorlib.ActorImage_StaticMultiple):  # 21
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ParaGoomba', 'para_goomba.png')
        if 'ParaGoomba1' in ImageCache:
            return
        for i in range(8):
            ImageCache[f'ParaGoomba{i + 1}'] = actorlib.GetPixmap(f'para_goomba_{i + 1}.png')

    def dataChanged(self):
        colour = (self.parent.spritedata[2] & 0xF) % 9
        self.offset = (-1, -10)

        if colour == 0:
            self.image = ImageCache['ParaGoomba']

        else:
            self.image = ImageCache[f'ParaGoomba{colour}']

        super().dataChanged()


class ActorImage_PumpkinGoomba(actorlib.ActorImage_StaticMultiple):  # 22
    def __init__(self, parent):
        super().__init__(parent)
        self.offset = (-4, -48)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PumpkinGoomba', 'pumpkin_goomba.png')
        actorlib.loadIfNotInImageCache('PumpkinParagoomba', 'pumpkin_paragoomba.png')

    def dataChanged(self):
        para = self.parent.spritedata[5] & 1
        self.image = ImageCache['PumpkinGoomba' if not para else 'PumpkinParagoomba']

        super().dataChanged()


class ActorImage_NewerBuzzyBeetle(actorlib.ActorImage_StaticMultiple):  # 24
    @staticmethod
    def loadImages():
        if "BuzzyBeetle" not in ImageCache:
            ImageCache["BuzzyBeetle"] = actorlib.GetPixmap('buzzy_beetle.png')
            ImageCache["BuzzyBeetleU"] = actorlib.GetPixmap('buzzy_beetle_u.png')
            ImageCache["BuzzyBeetleShell"] = actorlib.GetPixmap('buzzy_beetle_shell.png')
            ImageCache["BuzzyBeetleShellU"] = actorlib.GetPixmap('buzzy_beetle_shell_u.png')

        if "BuzzyBeetleblack" not in ImageCache:
            for colour in ("black", "blue", "green", "orange", "purple", "red", "yellow"):
                ImageCache[f'BuzzyBeetle{colour}'] = actorlib.GetPixmap(f'buzzy_beetle_{colour}.png')
                ImageCache[f'BuzzyBeetle{colour}U'] = actorlib.GetPixmap(f'buzzy_beetle_{colour}_u.png')
                ImageCache[f'BuzzyBeetle{colour}Shell'] = actorlib.GetPixmap(f'buzzy_beetle_{colour}_shell.png')
                ImageCache[f'BuzzyBeetle{colour}ShellU'] = actorlib.GetPixmap(f'buzzy_beetle_{colour}_shell_u.png')

    def dataChanged(self):

        orient = self.parent.spritedata[5] & 15
        colour = self.parent.spritedata[2] & 15
        if colour > 7:
            colour = 0

        colour = ("", "red", "orange", "yellow", "green", "blue", "purple", "black")[colour]
        if orient == 1:
            self.image = ImageCache[f'BuzzyBeetle{colour}U']
            self.yOffset = 0
        elif orient == 2:
            self.image = ImageCache[f'BuzzyBeetle{colour}Shell']
            self.yOffset = 2
        elif orient == 3:
            self.image = ImageCache[f'BuzzyBeetle{colour}ShellU']
            self.yOffset = 2
        else:
            self.image = ImageCache[f'BuzzyBeetle{colour}']
            self.yOffset = 0

        super().dataChanged()


class ActorImage_NewerSpiny(actorlib.ActorImage_StaticMultiple):  # 25
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Spiny', 'spiny.png')
        actorlib.loadIfNotInImageCache('SpinyShell', 'spiny_shell.png')
        actorlib.loadIfNotInImageCache('SpinyShellU', 'spiny_shell_u.png')
        actorlib.loadIfNotInImageCache('SpinyBall', 'spiny_ball.png')

        if 'Spinyorange' in ImageCache:
            return
        for colour in ("orange", "yellow", "green", "blue", "violet", "black", "sidestepper"):
            ImageCache[f'Spiny{colour}'] = actorlib.GetPixmap(f'spiny_{colour}.png')
            ImageCache[f'Spiny{colour}Shell'] = actorlib.GetPixmap(f'spiny_{colour}_shell.png')
            ImageCache[f'Spiny{colour}ShellU'] = actorlib.GetPixmap(f'spiny_{colour}_shell_u.png')

    def dataChanged(self):
        orient = self.parent.spritedata[5] & 15
        colour = self.parent.spritedata[2] & 15
        if colour > 7:
            colour = 0

        colour = ("", "orange", "yellow", "green", "blue", "violet", "black", "sidestepper")[colour]
        if orient == 1:
            self.image = ImageCache['SpinyBall']
            self.yOffset = 8
        elif orient == 2:
            self.image = ImageCache[f'Spiny{colour}Shell']
            self.yOffset = 1
        elif orient == 3:
            self.image = ImageCache[f'Spiny{colour}ShellU']
            self.yOffset = 2
        else:
            self.image = ImageCache[f'Spiny{colour}']
            self.yOffset = 0

        super().dataChanged()


class ActorImage_NewerUpsideDownSpiny(actorlib.ActorImage_StaticMultiple):  # 26
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SpinyU', 'spiny_u.png')
        if 'SpinyorangeU' not in ImageCache:
            for style in ("orange", "yellow", "green", "blue", "violet", "black", "sidestepper"):
                Spiny = actorlib.GetImage(f'spiny_{style}.png')

                if Spiny is None:
                    # slow patch folder is slow
                    return

                ImageCache[f'Spiny{style}U'] = QtGui.QPixmap.fromImage(Spiny.mirrored(False, True))

    def dataChanged(self):
        colour = self.parent.spritedata[2] & 15
        if colour > 7:
            colour = 0

        colour = ("", "orange", "yellow", "green", "blue", "violet", "black", "sidestepper")[colour]

        # slow patch folder is slow, 2
        if 'SpinyorangeU' not in ImageCache:
            return

        self.image = ImageCache[f'Spiny{colour}U']

        super().dataChanged()


class ActorImage_NewerQSwitch(ActorImage_NewerSwitch): # 40
    def __init__(self, parent):
        super().__init__(parent)
        self.switchType = "Q"


class ActorImage_NewerPSwitch(ActorImage_NewerSwitch): # 41
    def __init__(self, parent):
        super().__init__(parent)
        self.switchType = "P"


class ActorImage_NewerExcSwitch(ActorImage_NewerSwitch):  # 42
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.switchType = 'E'


class ActorImage_NewerQSwitchBlock(ActorImage_Block):  # 43
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48

    def dataChanged(self):
        upsideDown = self.parent.spritedata[5] & 1
        self.flipOverride = upsideDown
        midway = (self.parent.spritedata[2] >> 6) & 1
        self.transparent = midway

        color = self.parent.spritedata[3] & 3
        if color < 2:
            self.contentsOverride = 17
        else:
            self.contentsOverride = 21
        super().dataChanged()


class ActorImage_NewerExcSwitchBlock(ActorImage_Block):  # 45
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48

    def dataChanged(self):
        upsideDown = self.parent.spritedata[5] & 1
        self.flipOverride = upsideDown
        midway = (self.parent.spritedata[2] >> 6) & 1
        self.transparent = midway

        color = self.parent.spritedata[3] & 3
        if color < 2:
            self.contentsOverride = 19
        else:
            self.contentsOverride = 22
        super().dataChanged()


class ActorImage_NewerPodoboo(actorlib.ActorImage):  # 46
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False
        podobooAuxImage = actorlib.AuxiliaryImage(parent, 48, 48)
        podobooAuxImage.setPos(-6, -6)
        podobooAuxImage.hover = False
        self.aux.append(podobooAuxImage)
        self.dimensions = (-3, 5, 24, 24)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Podoboo0', 'podoboo.png')
        if 'Podoboo1' in ImageCache:
            return
        for i in range(1, 9):
            if i == 2:
                continue  # skip 2 since it's a duplicate
            ImageCache[f'Podoboo{i}'] = actorlib.GetPixmap(f'podoboo{i}.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        style = (self.parent.spritedata[2] & 0xF) % 9
        if style == 2:
            self.aux[0].image = ImageCache['Podoboo0']
        else:
            self.aux[0].image = ImageCache[f'Podoboo{style}']


class ActorImage_Thwomp(actorlib.ActorImage_StaticMultiple):  # 47
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Thwomp'],
            (-6, -6),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Thwomp', 'thwomp.png')
        actorlib.loadIfNotInImageCache('ThwompIce', 'thwomp_ice.png')

    def dataChanged(self):
        icy = self.parent.spritedata[2] & 1

        if icy:
            self.image = ImageCache['ThwompIce']
        else:
            self.image = ImageCache['Thwomp']


class ActorImage_GiantThwomp(actorlib.ActorImage_StaticMultiple):  # 48
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GiantThwomp'],
            (-8, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GiantThwomp', 'giant_thwomp.png')
        actorlib.loadIfNotInImageCache('GiantThwompIce', 'giant_thwomp_ice.png')

    def dataChanged(self):
        icy = self.parent.spritedata[2] & 1

        if icy:
            self.image = ImageCache['GiantThwompIce']
        else:
            self.image = ImageCache['GiantThwomp']


class ActorImage_FakeStarCoin(actorlib.ActorImage_Static):  # 49
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['FakeStarCoin'],
            (-8, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FakeStarCoin', 'starcoin_fake.png')


class ActorImage_NewerKoopa(actorlib.ActorImage_StaticMultiple):  # 57
    @staticmethod
    def loadImages():
        if 'KoopaG' not in ImageCache:
            ImageCache['KoopaG'] = actorlib.GetPixmap('koopa_green.png')
            ImageCache['KoopaR'] = actorlib.GetPixmap('koopa_red.png')
            ImageCache['KoopaShellG'] = actorlib.GetPixmap('koopa_green_shell.png')
            ImageCache['KoopaShellR'] = actorlib.GetPixmap('koopa_red_shell.png')

        if 'Koopa01' in ImageCache:
            return

        for flag in (0, 1):
            for style in range(1, 5):
                flag_style = f'{flag}{style}'
                ImageCache[f'Koopa{flag_style}'] = actorlib.GetPixmap(f'koopa_{flag_style}.png')

            for style in range(1, 4):
                flag_style = f'{flag}{style}'
                ImageCache[f'KoopaShell{flag_style}'] = actorlib.GetPixmap(f'koopa_shell_{flag_style}.png')

    def dataChanged(self):
        # get properties
        props = self.parent.spritedata[5]
        shell = (props >> 4) & 1 or (self.parent.spritedata[2] >> 4) != 0
        red = props & 1
        texhack = (self.parent.spritedata[2] & 0xF) % 5

        if not shell:

            if texhack == 0:
                self.offset = (-7, -15)
                self.image = ImageCache['KoopaG'] if not red else ImageCache['KoopaR']
            else:
                self.offset = (-5, -13)
                self.image = ImageCache[f'Koopa{red}{texhack}']
        else:
            del self.offset

            if texhack in (0, 4):
                self.image = ImageCache['KoopaShellG'] if not red else ImageCache['KoopaShellR']
            else:
                self.image = ImageCache[f'KoopaShell{red}{texhack}']

        super().dataChanged()


class ActorImage_NewerParaKoopa(actorlib.ActorImage_StaticMultiple):  # 58
    def __init__(self, parent):
        super().__init__(parent, 1.5, None, (-7, -12))
        self.aux.append(actorlib.AuxiliaryTrackObject(self.parent, 0, 0, 0))

    @staticmethod
    def loadImages():

        if 'ParaKoopaG' not in ImageCache:
            ImageCache['ParaKoopaG'] = actorlib.GetPixmap('parakoopa_green.png')
            ImageCache['ParaKoopaR'] = actorlib.GetPixmap('parakoopa_red.png')

        if 'KoopaShellG' not in ImageCache:
            ImageCache['KoopaShellG'] = actorlib.GetPixmap('koopa_green_shell.png')
            ImageCache['KoopaShellR'] = actorlib.GetPixmap('koopa_red_shell.png')

        if 'ParaKoopa01' not in ImageCache:
            for flag in (0, 1):
                for style in range(1, 5):
                    flag_style = f'{flag}{style}'
                    ImageCache[f'ParaKoopa{flag_style}'] = actorlib.GetPixmap(f'parakoopa_{flag_style}.png')

        if 'KoopaShell01' not in ImageCache:
            for flag in (0, 1):
                for style in range(1, 4):
                    flag_style = f'{flag}{style}'
                    ImageCache[f'KoopaShell{flag_style}'] = actorlib.GetPixmap(f'koopa_shell_{flag_style}.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        # get properties
        red = self.parent.spritedata[5] & 1
        mode = (self.parent.spritedata[5] >> 4) & 3
        texhack = (self.parent.spritedata[2] & 0xF) % 5

        if texhack == 0:
            if mode == 3:
                del self.offset
                self.image = ImageCache['KoopaShellG'] if not red else ImageCache['KoopaShellR']
            else:
                self.offset = (-7, -12)
                self.image = ImageCache['ParaKoopaG'] if not red else ImageCache['ParaKoopaR']
        else:
            if mode == 3:
                del self.offset
                if texhack == 4:
                    self.image = ImageCache['KoopaShellG'] if not red else ImageCache['KoopaShellR']
                else:
                    self.image = ImageCache[f'KoopaShell{red}{texhack}']
            else:
                self.offset = (-8, -12)
                self.image = ImageCache[f'ParaKoopa{red}{texhack}']

        if mode == 1 or mode == 2:

            turnImmediately = self.parent.spritedata[4] & 1 == 1
            track = self.aux[0]

            if mode == 1:
                track.direction = actorlib.AuxiliaryTrackObject.Horizontal
                track.setSize(9 * 16, 16)
                if turnImmediately:
                    track.setPos(self.width / 2, self.height / 2)
                else:
                    track.setPos(-4 * 24 + self.width / 2, self.height / 2)
            else:
                track.direction = actorlib.AuxiliaryTrackObject.Vertical
                track.setSize(16, 9 * 16)
                if turnImmediately:
                    track.setPos(self.width / 2, self.height / 2)
                else:
                    track.setPos(self.width / 2, -4 * 24 + self.height / 2)

        else:
            # hide the track
            self.aux[0].setSize(0, 0)

        super().dataChanged()


class ActorImage_NewerSpikeTop(actorlib.ActorImage_StaticMultiple):  # 60
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            offset = (0, -4)
        )

    @staticmethod
    def loadImages():
        if 'SpikeTop00' in ImageCache:
            return
        for style in ("", "_red", "_orange", "_yellow", "_green", "_hothead", "_purple", "_black"):
            SpikeTop = actorlib.GetImage(f'spiketop{style}.png')
            if SpikeTop is None:
                # happens when the newer patch folder is not loaded yet
                return

            Transform = QtGui.QTransform()
            ImageCache[f'SpikeTop00{style}'] = QtGui.QPixmap.fromImage(SpikeTop.mirrored(True, False))
            Transform.rotate(-90)
            ImageCache[f'SpikeTop10{style}'] = ImageCache[f'SpikeTop00{style}'].transformed(Transform)
            Transform.rotate(-90)
            ImageCache[f'SpikeTop20{style}'] = ImageCache[f'SpikeTop00{style}'].transformed(Transform)
            Transform.rotate(-90)
            ImageCache[f'SpikeTop30{style}'] = ImageCache[f'SpikeTop00{style}'].transformed(Transform)

            Transform = QtGui.QTransform()
            ImageCache[f'SpikeTop01{style}'] = QtGui.QPixmap.fromImage(SpikeTop)
            Transform.rotate(-90)
            ImageCache[f'SpikeTop11{style}'] = ImageCache[f'SpikeTop01{style}'].transformed(Transform)
            Transform.rotate(-90)
            ImageCache[f'SpikeTop21{style}'] = ImageCache[f'SpikeTop01{style}'].transformed(Transform)
            Transform.rotate(-90)
            ImageCache[f'SpikeTop31{style}'] = ImageCache[f'SpikeTop01{style}'].transformed(Transform)

    def dataChanged(self):
        orientation = (self.parent.spritedata[5] >> 4) % 4
        direction = self.parent.spritedata[5] & 1
        colour = self.parent.spritedata[2] & 7

        color = ("", "_red", "_orange", "_yellow", "_green", "_hothead", "_purple", "_black")[colour]
        # slow patch folder is slow, 2
        if 'SpikeTop01_red' not in ImageCache:
            return

        self.image = ImageCache[f'SpikeTop{orientation}{direction}{color}']

        if colour == 5:
            self.offset = (
                (0, -4),
                (-4, 0),
                (0, -4),
                (-4, 0),
            )[orientation]
        else:
            self.offset = (
                (0, -4),
                (-4, 0),
                (0, 0),
                (0, 0),
            )[orientation]

        super().dataChanged()


class ActorImage_NewerSpikeBall(actorlib.ActorImage_StaticMultiple):  # 63
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SpikeBall'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SpikeBall', 'spike_ball.png')
        actorlib.loadIfNotInImageCache('SnowBall', 'snow_ball.png')

    def dataChanged(self):
        snowy = self.parent.spritedata[2] & 1
        if snowy:
            self.image = ImageCache['SnowBall']
        else:
            self.image = ImageCache['SpikeBall']


class ActorImage_NewerBouncyCloud(actorlib.ActorImage_StaticMultiple):  # 78
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['CloudTrSmall'],
            (-2, -2),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('CloudTrBig', 'cloud_trampoline_big.png')
        actorlib.loadIfNotInImageCache('CloudTrSmall', 'cloud_trampoline_small.png')

        if 'CloudTrBig1' in ImageCache:
            return

        for size in ("Big", "Small"):
            for style in range(1, 7):
                name = f'CloudTr{size}{style}'
                ImageCache[name] = actorlib.GetPixmap(f"cloud_trampoline_{size.lower()}{style}.png")

    def dataChanged(self):
        style = (self.parent.spritedata[2] & 0xF) % 7
        raw_size = (self.parent.spritedata[4] >> 4) & 1
        size = "Small" if raw_size == 0 else "Big"

        if style == 0 or style > 6:
            self.image = ImageCache[f'CloudTr{size}']
            self.offset = (-2, -2)
        else:
            self.image = ImageCache[f'CloudTr{size}{style}']
            self.offset = (-2, -2)

        super().dataChanged()


class ActorImage_ActorSpawner(actorlib.ActorImage_Static):  # 88
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ActorSpawner'],
            (8, 0),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ActorSpawner', 'ActorSpawner.png')


class ActorImage_ActorMultiSpawner(actorlib.ActorImage_Static):  # 89
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ActorMultiSpawner'],
            (-8, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ActorMultiSpawner', 'ActorMultiSpawner.png')


class ActorImage_NewerHammerBroNormal(actorlib.ActorImage_StaticMultiple):  # 95
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (-4, -21)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('HammerBro', 'hammerbro.png')
        actorlib.loadIfNotInImageCache('HammerBroBlack', 'hammerbro_black.png')

    def dataChanged(self):
        black = self.parent.spritedata[2] & 1
        self.image = ImageCache['HammerBro'] if not black else ImageCache['HammerBroBlack']

        super().dataChanged()


class ActorImage_GiantSpikeBall(actorlib.ActorImage_StaticMultiple):  # 98
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GiantSpikeBall'],
            (-24, -24),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GiantSpikeBall', 'giant_spike_ball.png')
        actorlib.loadIfNotInImageCache('GiantSnowBall', 'giant_snow_ball.png')

    def dataChanged(self):
        snowy = self.parent.spritedata[2] & 1

        if snowy:
            self.image = ImageCache['GiantSnowBall']
        else:
            self.image = ImageCache['GiantSpikeBall']


class ActorImage_NewerBobomb(actorlib.ActorImage_StaticMultiple):  # 101
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Bobomb', 'bobomb.png')
        if 'Bobomb1' in ImageCache:
            return
        for i in range(8):
            ImageCache[f'Bobomb{i + 1}'] = actorlib.GetPixmap(f'bobomb_{i + 1}.png')

    def dataChanged(self):
        colour = (self.parent.spritedata[2] & 0xF) % 9
        if colour == 0:
            self.image = ImageCache['Bobomb']
            self.offset = (-8, -8)
        else:
            self.image = ImageCache[f'Bobomb{colour}']
            self.offset = (-10, -8)

        super().dataChanged()


class ActorImage_NewerPokey(actorlib.ActorImage_StaticMultiple):  # 105
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False
        self.parent.setZValue(24999)
        self.aux.append(actorlib.AuxiliaryImage(parent, 100, 252))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PokeyTop', 'pokey_top.png')
        actorlib.loadIfNotInImageCache('PokeyMiddle', 'pokey_middle.png')
        actorlib.loadIfNotInImageCache('PokeyBottom', 'pokey_bottom.png')

        for style in ("pumpkin", "jungle", "lava"):
            for i in range(8):
                ImageCache[f'Pokey{style}Top'] = actorlib.GetPixmap(f'pokey_{style}_top.png')
                ImageCache[f'Pokey{style}Middle'] = actorlib.GetPixmap(f'pokey_{style}_middle.png')
                ImageCache[f'Pokey{style}Bottom'] = actorlib.GetPixmap(f'pokey_{style}_bottom.png')
                ImageCache[f'PokeySnowman{i}'] = actorlib.GetPixmap(f'pokey_snowman{i}.png')

    def dataChanged(self):
        super().dataChanged()
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        height = self.parent.spritedata[5] % 8
        style = self.parent.spritedata[2] % 5
        color = ("", "pumpkin", "", "jungle", "lava")[style]

        pix = QtGui.QPixmap(100, 252)
        pix.fill(Qt.GlobalColor.transparent)
        paint = QtGui.QPainter(pix)

        if style == 2:
            snowman = ImageCache[f'PokeySnowman{height}']
            self.aux[0].image = snowman
            self.offset = (
                (-4, -31),  # (-6, -46)
                (-7, -46),  # (-10, -69)
                (-11, -62), # (-16, -93)
                (-13, -78), # (-20, -117)
                (-16, -94), # (-24, -141)
                (-19, -111),# (-29, -166)
                (-23, -126),# (-35, -189)
                (-25, -142) # (-38, -213)
            )[height]
            self.size = (snowman.width() / 1.5, snowman.height() / 1.5)

        else:
            self.width = 24
            self.height = (height * 16) + 16 + 25
            self.offset = (-4, -self.height + 16)

            paint.drawPixmap(0, 0, ImageCache[f'Pokey{color}Top'])
            paint.drawTiledPixmap(0, 37, 36, int(self.height * 1.5 - 61), ImageCache[f'Pokey{color}Middle'])
            paint.drawPixmap(0, int(self.height * 1.5 - 24), ImageCache[f'Pokey{color}Bottom'])
            self.aux[0].image = pix

        paint = None

class ActorImage_ModelLoaderResources(actorlib.ActorImage):  # 143, 321
    def __init__(self, parent):
        super().__init__(parent, 1.5)

class ActorImage_NewerFloatingBarrel(actorlib.ActorImage_StaticMultiple):  # 145
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            offset = (-16, -9)
        )
        image = ImageCache['FloatingBarrel']
        self.width = (image.width() / self.scale) + 1
        self.height = (image.height() / self.scale) + 2

        self.aux.append(actorlib.AuxiliaryImage(parent, image.width(), image.height()))
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 72, 2, 0, 36))

    @staticmethod
    def loadImages():
        if 'FloatingBarrel' in ImageCache:
            return
        ImageCache['FloatingBarrel'] = actorlib.GetPixmap('barrel_floating.png')
        for flag in (1, 2):
            ImageCache[f'FloatingBarrel{flag}'] = actorlib.GetPixmap(f'barrel_floating_{flag}.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        color = self.parent.spritedata[2] & 3
        if color == 0:
            img = ImageCache['FloatingBarrel']
        else:
            img = ImageCache[f'FloatingBarrel{color}']

        self.aux[0].image = img

        # Don't let actorlib.ActorImage_Static reset size
        actorlib.ActorImage.dataChanged(self)


class ActorImage_MessageBlock(actorlib.ActorImage_Static): # 152
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            actorlib.GetTile(0x98),
            (8, 0)
        )


class ActorImage_NewerQSwitchUnused(ActorImage_NewerSwitch): # 153
    def __init__(self, parent):
        super().__init__(parent)
        self.switchType = "Q"


class ActorImage_BigPumpkin(actorlib.ActorImage_StaticMultiple):  # 157
    def __init__(self, parent):
        super().__init__(parent)
        self.offset = (-8, -16)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BigPumpkin', 'giant_pumpkin.png')
        actorlib.loadIfNotInImageCache('ShipKey', 'ship_key.png')
        actorlib.loadIfNotInImageCache('5Coin', '5_coin.png')

        if 'YoshiFire' not in ImageCache:
            pix = QtGui.QPixmap(48, 24)
            pix.fill(Qt.GlobalColor.transparent)
            paint = QtGui.QPainter(pix)
            paint.drawPixmap(0, 0, ImageCache['BlockContents9'])
            paint.drawPixmap(24, 0, ImageCache['BlockContents3'])
            del paint
            ImageCache['YoshiFire'] = pix

        for power in range(0x10):
            if power in (0, 8, 12, 13):
                ImageCache[f'BigPumpkin{power}'] = ImageCache['BigPumpkin']
                continue

            x, y = 36, 48
            overlay = ImageCache[f'BlockContents{power}']
            if power == 9:
                overlay = ImageCache['YoshiFire']
                x = 24
            elif power == 10:
                overlay = ImageCache['5Coin']
            elif power == 14:
                overlay = ImageCache['ShipKey']
                x, y = 34, 42

            new = QtGui.QPixmap(ImageCache['BigPumpkin'])
            paint = QtGui.QPainter(new)
            paint.drawPixmap(x, y, overlay)
            del paint
            ImageCache[f'BigPumpkin{power}'] = new

    def dataChanged(self):

        power = self.parent.spritedata[5] & 0xF
        self.image = ImageCache[f'BigPumpkin{power}']
        super().dataChanged()


class ActorImage_ShyGuyGiant(actorlib.ActorImage_Static): # 167
    def __init__(self, parent):
        super().__init__(parent, 1.5)

    @staticmethod
    def loadImages():
        if "ShyGuy%s%s" in ImageCache:
            return
        for size in ("big", "mega", "colossal"):
            for colour in ("red", "blue", "green", "yellow", "magenta"):
                ImageCache[f'ShyGuy{size}{colour}'] = actorlib.GetPixmap(f'shyguy_{size}_{colour}.png')

    def dataChanged(self):
        size = (self.parent.spritedata[2] >> 4) & 3
        colour = (self.parent.spritedata[2] & 0xF) % 5
        scale = ("big", "mega", "colossal")[size]
        color = ("red", "blue", "green", "yellow", "magenta")[colour]

        self.image = ImageCache[f'ShyGuy{scale}{color}']

        if size == 0:
            self.offset = (-12.7, -118)
        elif size == 1:
            self.offset = (-32, -160)
        else:
            self.offset = (-52.7, -220)

        super().dataChanged()


class ActorImage_Thundercloud(actorlib.ActorImage_Static):  # 168
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Thundercloud'],
            (-24, -40),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Thundercloud', 'thundercloud.png')


class ActorImage_Meteor(actorlib.ActorImage_StaticMultiple):  # 183
    @staticmethod
    def loadImages():
        ImageCache['Meteor'] = actorlib.GetPixmap('meteor.png')
        ImageCache['MeteorElectric'] = actorlib.GetPixmap('meteor_electric.png')

    def dataChanged(self):
        multiplier = self.parent.spritedata[4] / 20
        if multiplier == 0:
            multiplier = 0.01
        isElectric = (self.parent.spritedata[5] >> 4) & 1

        # Get the size data, taking into account the size
        # differences between the non-electric and
        # electric varieties.
        sizes = (
            # Relative X offset (size 0x14),
            # relative Y offset (size 0x14),
            # absolute X offset,
            # absolute Y offset
            (-54, -53, 6, -1),
            (-61, -68, 6, 0),
        )
        size = sizes[1] if isElectric else sizes[0]
        relXoff = size[0]
        relYoff = size[1]
        absXoff = size[2]
        absYoff = size[3]

        base = ImageCache['MeteorElectric' if isElectric else 'Meteor']
        if base is None:
            return

        self.image = base.scaled(
            int(base.width() * multiplier) + 8,
            int(base.height() * multiplier) + 8,
        )
        self.offset = (
            (relXoff * multiplier) + absXoff,
            (relYoff * multiplier) + absYoff,
        )

        super().dataChanged()


class ActorImage_MidwayFlag(actorlib.ActorImage_StaticMultiple):  # 188
    def __init__(self, parent):
        super().__init__(parent)

    @staticmethod
    def loadImages():
        if 'MidwayFlag0' in ImageCache:
            return
        for i in range(19):
            ImageCache[f'MidwayFlag{i}'] = actorlib.GetPixmap(f'midway_flag_{i}.png')

    def dataChanged(self):
        style = self.parent.spritedata[2] % 19

        self.image = ImageCache[f'MidwayFlag{style}']
        if style == 18:
            self.offset = (-31 / 1.5, -47 / 1.5)
        else:
            self.offset = (1 / 1.5, -55 / 1.5)

        super().dataChanged()


class ActorImage_TileEventNewer(common.ActorImage_TileEvent):  # 191
    def __init__(self, parent):
        super().__init__(parent)
        self.notAllowedTypes = [2, 5, 7, 13, 15]

    def getTileFromType(self, type):
        if type == 0:
            return actorlib.GetTile(55)

        if type == 1:
            return actorlib.GetTile(48)

        if type == 3:
            return actorlib.GetTile(52)

        if type == 4:
            return actorlib.GetTile(51)

        if type == 6:
            return actorlib.GetTile(45)

        if type in [8, 9, 10, 11]:
            row = self.parent.spritedata[2] & 0xF
            col = self.parent.spritedata[3] >> 4

            tilenum = 256 * (type - 8)
            tilenum += row * 16 + col

            return actorlib.GetTile(tilenum)

        if type == 12:
            return actorlib.GetTile(256 * 3 + 67)

        if type == 14:
            return actorlib.GetTile(256)

        return None


class ActorImage_NewerHuckitCrab(actorlib.ActorImage_StaticMultiple):  # 195
    @staticmethod
    def loadImages():
        if 'HuckitCrabWhiteR' in ImageCache:
            return
        Huckitcrab = actorlib.GetImage('huckit_crab.png')
        Wintercrab = actorlib.GetImage('huckit_crab_white.png')
        if Wintercrab is None:
            return

        ImageCache['HuckitCrabL'] = QtGui.QPixmap.fromImage(Huckitcrab)
        ImageCache['HuckitCrabR'] = QtGui.QPixmap.fromImage(Huckitcrab.mirrored(True, False))
        ImageCache['HuckitCrabWhiteL'] = QtGui.QPixmap.fromImage(Wintercrab)
        ImageCache['HuckitCrabWhiteR'] = QtGui.QPixmap.fromImage(Wintercrab.mirrored(True, False))

    def dataChanged(self):
        info = self.parent.spritedata[5]
        colour = self.parent.spritedata[2] & 1

        colour = ("", "White")[colour]
        if 'HuckitCrabWhiteR' not in ImageCache:
            return
        if info == 1:
            self.image = ImageCache[f'HuckitCrab{colour}R']
            self.xOffset = 0
        else:
            if info == 13:
                self.image = ImageCache[f'HuckitCrab{colour}R']
                self.xOffset = 0
            else:
                self.image = ImageCache[f'HuckitCrab{colour}L']
                self.xOffset = -16

        super().dataChanged()


class ActorImage_NewerGiantGoomba(actorlib.ActorImage_StaticMultiple):  # 198
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GiantGoomba', 'giant_goomba.png')
        if 'GiantGoomba1' in ImageCache:
            return
        for i in range(6):
            ImageCache[f'GiantGoomba{i + 1}'] = actorlib.GetPixmap(f'giant_goomba_{i + 1}.png')

    def dataChanged(self):

        colour = (self.parent.spritedata[2] & 0xF) % 7

        if colour == 0:
            self.image = ImageCache['GiantGoomba']
            self.offset = (-6, -19)
        else:
            self.image = ImageCache[f'GiantGoomba{colour}']
            self.offset = (-7, -18)

        super().dataChanged()


class ActorImage_NewerMegaGoomba(actorlib.ActorImage_StaticMultiple):  # 199
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MegaGoomba', 'mega_goomba.png')
        if 'MegaGoomba1' in ImageCache:
            return
        for i in range(6):
            ImageCache[f'MegaGoomba{i + 1}'] = actorlib.GetPixmap(f'mega_goomba_{i + 1}.png')

    def dataChanged(self):
        colour = (self.parent.spritedata[2] & 0xF) % 7

        if colour == 0:
            self.image = ImageCache['MegaGoomba']
            self.offset = (-11, -37)
        else:
            self.image = ImageCache[f'MegaGoomba{colour}']
            self.offset = (-11, -37)

        super().dataChanged()


class ActorImage_Chest(actorlib.ActorImage_Static):  # 203
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Chest'],
            (-12, -10),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Chest', 'chest.png')


class ActorImage_Topman(actorlib.ActorImage_Static):  # 210
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Topman'],
            (-14, -34),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Topman', 'topman.png')


class ActorImage_CaptainBowser(actorlib.ActorImage_Static):  # 213
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['CaptainBowser'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('CaptainBowser', 'captain_bowser.png')


class ActorImage_NewerLineBlock(common.ActorImage_LineBlock):  # 219

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LineBlock0', 'lineblock.png')
        if 'LineBlock8' in ImageCache:
            return
        for i in range(8):
            ImageCache[f'LineBlock{i + 1}'] = actorlib.GetPixmap(f'lineblock{i + 1}.png')

    def dataChanged(self):
        # Make sure the relevant images have been loaded before processing the
        # sprite settings
        if ImageCache['LineBlock8'] is None:
            return

        color = (self.parent.spritedata[2] & 0xF) % 9

        self.setLineBlockImage(ImageCache[f'LineBlock{color}'])


class ActorImage_NewerSpringBlock(actorlib.ActorImage_StaticMultiple):  # 223
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SpringBlock', 'spring_block.png')
        actorlib.loadIfNotInImageCache('SpringBlockAlt', 'spring_block_alt.png')
        if 'SpringBlock1' in ImageCache:
            return
        for i in range(3):
            ImageCache[f'SpringBlock{i + 1}'] = actorlib.GetPixmap(f'spring_block_{i + 1}.png')
            ImageCache[f'SpringBlockAlt{i + 1}'] = actorlib.GetPixmap(f'spring_block_alt_{i + 1}.png')

    def dataChanged(self):
        colour = (self.parent.spritedata[2] & 0xF) % 4
        alt = self.parent.spritedata[5] & 1

        if colour == 0:
            self.image = ImageCache['SpringBlockAlt'] if alt else ImageCache['SpringBlock']
        else:
            self.image = ImageCache[f'SpringBlockAlt{colour}'] if alt else ImageCache[f'SpringBlock{colour}']

        super().dataChanged()


class ActorImage_NewerBramball(actorlib.ActorImage_StaticMultiple):  # 230
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (-50 / 1.5, -71 / 1.5)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Bramball', 'bramball.png')

        if 'Bramball1' in ImageCache:
            return

        for i in range(1, 5):
            ImageCache[f'Bramball{i}'] = actorlib.GetPixmap(f'bramball_{i}.png')

    def dataChanged(self):
        colour = (self.parent.spritedata[2] & 0xF) % 5

        if colour == 0:
            self.image = ImageCache['Bramball']
        else:
            self.image = ImageCache[f'Bramball{colour}']

        super().dataChanged()


class ActorImage_NewerWiggleShroom(actorlib.ActorImage):  # 231
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False
        self.parent.setZValue(24999)
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Vertical))

    @staticmethod
    def loadImages():
        if 'WiggleShroomL' in ImageCache:
            return
        ImageCache['WiggleShroomL'] = actorlib.GetPixmap('wiggle_shroom_left.png')
        ImageCache['WiggleShroomM'] = actorlib.GetPixmap('wiggle_shroom_middle.png')
        ImageCache['WiggleShroomR'] = actorlib.GetPixmap('wiggle_shroom_right.png')
        ImageCache['WiggleShroomS'] = actorlib.GetPixmap('wiggle_shroom_stem.png')

        if 'WiggleShroomredL' in ImageCache:
            return
        for style in ("red", "orange", "green", "blue"):
            ImageCache[f'WiggleShroom{style}L'] = actorlib.GetPixmap(f'wiggle_shroom_{style}_left.png')
            ImageCache[f'WiggleShroom{style}M'] = actorlib.GetPixmap(f'wiggle_shroom_{style}_middle.png')
            ImageCache[f'WiggleShroom{style}R'] = actorlib.GetPixmap(f'wiggle_shroom_{style}_right.png')
            ImageCache['WiggleShroomNewerS'] = actorlib.GetPixmap('wiggle_shroom_newer_stem.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        width = (self.parent.spritedata[4] & 0xF0) >> 4
        long = (self.parent.spritedata[3] >> 2) & 1
        extends = (self.parent.spritedata[3] >> 5) & 1
        distance = self.parent.spritedata[3] & 3 # this is also the stem length
        colour = (self.parent.spritedata[2] & 0xF) % 6
        shroom = ("", "red", "orange", "", "green", "blue")[colour]

        self.xOffset = -(width * 8) - 20
        self.width = (width * 16) + 56
        self.wiggleleft = ImageCache[f'WiggleShroom{shroom}L']
        self.wigglemiddle = ImageCache[f'WiggleShroom{shroom}M']
        self.wiggleright = ImageCache[f'WiggleShroom{shroom}R']
        if colour > 0:
            self.wigglestem = ImageCache['WiggleShroomNewerS']
        else:
            self.wigglestem = ImageCache['WiggleShroomS']

        if extends:
            self.aux[0].setPos((self.width * 0.75) - 12, (-distance * 24))
            self.aux[0].setSize(16, (distance * 32))
            if long:
                self.height = 96
            else:
                self.height = 64
        else:
            self.aux[0].setSize(0, 0)
            self.height = (distance * 16) + 64

    def paint(self, painter):
        xsize = self.width * 1.5
        painter.drawPixmap(0, 0, self.wiggleleft)
        painter.drawTiledPixmap(18, 0, int(xsize - 36), 24, self.wigglemiddle)
        painter.drawPixmap(int(xsize - 18), 0, self.wiggleright)
        painter.drawTiledPixmap(int((xsize / 2) - 12), 24, 24, int((self.height * 1.5) - 24), self.wigglestem)


class ActorImage_EventBlock(actorlib.ActorImage_Static): # 239
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            actorlib.GetTile(0x97),
            (-8, -16)
        )


class ActorImage_LineEvent(actorlib.ActorImage):  # 244
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 0, 0))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryRectOutline):
            return

        width = (self.parent.spritedata[5] >> 4) & 0xF
        height = self.parent.spritedata[4] & 0xF
        if width == 0:
            w = 1
        else:
            w = 0
        if height == 0:
            h = 1
        else:
            h = 0

        self.aux[0].setSize((width + w) * 24, (height + h) * 24)


class ActorImage_ElectricLine(actorlib.ActorImage_StaticMultiple):  # 250
    def __init__(self, parent):
        super().__init__(parent)
        lineOutline = actorlib.AuxiliaryRectOutline(parent, 48, 672)
        lineOutline.fillFlag = False
        self.aux.append(lineOutline)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ElectricLineLeft', 'electric_line_left.png')
        actorlib.loadIfNotInImageCache('ElectricLineRight', 'electric_line_right.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryRectOutline):
            return

        left = self.parent.spritedata[5] & 1

        if left:
            self.image = ImageCache['ElectricLineLeft']
            self.offset = (-16, -128)
            self.aux[0].setPos(24, -144)
        else:
            self.image = ImageCache['ElectricLineRight']
            self.offset = (-8, -128)
            self.aux[0].setPos(-12, -144)

        super().dataChanged()


class ActorImage_TopmanBoss(actorlib.ActorImage_Static):  # 251
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['TopmanBoss'],
            (-47.3, -66.6)
            #(-71, -100),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('TopmanBoss', 'topman_boss.png')


class ActorImage_NewerParabomb(actorlib.ActorImage_StaticMultiple):  # 269
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Parabomb', 'parabomb.png')
        if 'Parabomb1' in ImageCache:
            return
        for i in range(8):
            ImageCache[f'Parabomb{i + 1}'] = actorlib.GetPixmap(f'parabomb_{i + 1}.png')

    def dataChanged(self):
        colour = (self.parent.spritedata[2] & 0xF) % 9
        self.offset = (-2, -16)

        if colour == 0:
            self.image = ImageCache['Parabomb']

        else:
            self.image = ImageCache[f'Parabomb{colour}']

        super().dataChanged()


class ActorImage_RockyBoss(actorlib.ActorImage_Static):  # 279
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['RockyBoss'],
            (-25, -33),
        )

        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 71, 77, -166, -50))
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 71, 77, -334, -2))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RockyBoss', 'rocky_boss.png')


class ActorImage_AngrySun(actorlib.ActorImage_StaticMultiple):  # 282
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('AngrySun', 'angry_sun.png')
        actorlib.loadIfNotInImageCache('AngryMoon', 'angry_moon.png')

    def dataChanged(self):
        isMoon = self.parent.spritedata[5] & 1
        self.image = ImageCache['AngrySun' if not isMoon else 'AngryMoon']
        self.offset = (-18, -18) if not isMoon else (-13, -13)

        super().dataChanged()


class ActorImage_FuzzyBear(actorlib.ActorImage_StaticMultiple):  # 283
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FuzzyBear', 'fuzzy_bear.png')
        actorlib.loadIfNotInImageCache('FuzzyBearBig', 'fuzzy_bear_big.png')

    def dataChanged(self):
        big = (self.parent.spritedata[2] >> 4) & 1
        self.image = ImageCache['FuzzyBear' if not big else 'FuzzyBearBig']

        super().dataChanged()


class ActorImage_Boolossus(actorlib.ActorImage_Static):  # 290
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Boolossus'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Boolossus', 'boolossus.png')


class ActorImage_NewerParabeetle(actorlib.ActorImage_StaticMultiple):  # 291
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ParabeetleRight', 'parabeetle_right.png')
        actorlib.loadIfNotInImageCache('ParabeetleLeft', 'parabeetle_left.png')
        actorlib.loadIfNotInImageCache('ParabeetleMoreRight', 'parabeetle_moreright.png')
        actorlib.loadIfNotInImageCache('ParabeetleAtYou', 'parabeetle_atyou.png')

        if 'ParabeetleredRight' in ImageCache:
            return
        for colour in ("red", "orange", "yellow", "green", "skyblue", "blue", "purple", "black", "white", "pink"):
            ImageCache[f'Parabeetle{colour}Right'] = actorlib.GetPixmap(f'parabeetle_{colour}_right.png')
            ImageCache[f'Parabeetle{colour}Left'] = actorlib.GetPixmap(f'parabeetle_{colour}_left.png')
            ImageCache[f'Parabeetle{colour}MoreRight'] = actorlib.GetPixmap(f'parabeetle_{colour}_moreright.png')
            ImageCache[f'Parabeetle{colour}AtYou'] = actorlib.GetPixmap(f'parabeetle_{colour}_atyou.png')

    def dataChanged(self):
        self.yOffset = -8 / 1.5
        direction = self.parent.spritedata[5] & 0xf
        colour = self.parent.spritedata[2] & 15
        if colour > 10:
            colour = 0

        colour = ("", "red", "orange", "yellow", "green", "skyblue", "blue", "purple", "black", "white", "pink")[colour]
        if direction == 0:  # right
            self.xOffset = -19 / 1.5
            self.image = ImageCache[f'Parabeetle{colour}Right']
        elif direction in [1, 14]:  # left
            self.xOffset = -14 / 1.5
            self.image = ImageCache[f'Parabeetle{colour}Left']
        elif direction in [2, 4, 6, 8, 10]:  # more right
            self.xOffset = -14
            self.image = ImageCache[f'Parabeetle{colour}MoreRight']
        elif direction in [3, 5, 7, 9, 11, 12, 13, 15]:  # at you
            self.xOffset = -22
            self.image = ImageCache[f'Parabeetle{colour}AtYou']

        super().dataChanged()


class ActorImage_NewerHeavyParabeetle(actorlib.ActorImage_StaticMultiple):  # 292
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('HeavyParabeetleRight', 'heavy_parabeetle_right.png')
        actorlib.loadIfNotInImageCache('HeavyParabeetleLeft', 'heavy_parabeetle_left.png')
        actorlib.loadIfNotInImageCache('HeavyParabeetleMoreRight', 'heavy_parabeetle_moreright.png')
        actorlib.loadIfNotInImageCache('HeavyParabeetleAtYou', 'heavy_parabeetle_atyou.png')

        if 'HeavyParabeetleredRight' in ImageCache:
            return
        for colour in ("red", "orange", "yellow", "green", "skyblue", "blue", "purple", "black", "white", "pink"):
            ImageCache[f'HeavyParabeetle{colour}Right'] = actorlib.GetPixmap(f'heavy_parabeetle_{colour}_right.png')
            ImageCache[f'HeavyParabeetle{colour}Left'] = actorlib.GetPixmap(f'heavy_parabeetle_{colour}_left.png')
            ImageCache[f'HeavyParabeetle{colour}MoreRight'] = actorlib.GetPixmap(f'heavy_parabeetle_{colour}_moreright.png')
            ImageCache[f'HeavyParabeetle{colour}AtYou'] = actorlib.GetPixmap(f'heavy_parabeetle_{colour}_atyou.png')

    def dataChanged(self):
        self.yOffset = -85 / 1.5
        direction = self.parent.spritedata[5] & 0xf
        colour = self.parent.spritedata[2] & 15
        if colour > 10:
            colour = 0

        colour = ("", "red", "orange", "yellow", "green", "skyblue", "blue", "purple", "black", "white", "pink")[colour]
        if direction == 0:  # right
            self.xOffset = -58 / 1.5
            self.image = ImageCache[f'HeavyParabeetle{colour}Right']
        elif direction in [1, 14]:  # left
            self.xOffset = -58 / 1.5
            self.image = ImageCache[f'HeavyParabeetle{colour}Left']
        elif direction in [2, 4, 6, 8, 10]:  # more right
            self.xOffset = -58 / 1.5
            self.image = ImageCache[f'HeavyParabeetle{colour}MoreRight']
        elif direction in [3, 5, 7, 9, 11, 12, 13, 15]:  # at you
            self.xOffset = -58
            self.image = ImageCache[f'HeavyParabeetle{colour}AtYou']

        super().dataChanged()


class ActorImage_NewerMegaBuzzy(actorlib.ActorImage_StaticMultiple):  # 296
    @staticmethod
    def loadImages():
        if 'MegaBuzzyR' in ImageCache:
            return
        ImageCache['MegaBuzzyR'] = actorlib.GetPixmap('megabuzzy_right.png')
        ImageCache['MegaBuzzyL'] = actorlib.GetPixmap('megabuzzy_left.png')
        actorlib.loadIfNotInImageCache('MegaBuzzyF', 'megabuzzy_front.png')

        if 'MegaBuzzyredR' in ImageCache:
            return
        for style in ('red', 'orange', 'yellow', 'green', 'blue', 'purple', 'black', 'shyguy', 'monty'):
            ImageCache[f'MegaBuzzy{style}R'] = actorlib.GetPixmap(f'megabuzzy_{style}_right.png')
            ImageCache[f'MegaBuzzy{style}L'] = actorlib.GetPixmap(f'megabuzzy_{style}_left.png')
            ImageCache[f'MegaBuzzy{style}F'] = actorlib.GetPixmap(f'megabuzzy_{style}_front.png')

    def dataChanged(self):

        direction = self.parent.spritedata[5] & 3
        style = (self.parent.spritedata[2] & 0xF) % 10
        dir = ("R", "L", "F", "R")[direction]
        colour = ("", "red", "orange", "yellow", "green", "blue", "purple", "black", "shyguy", "monty")[style]

        if 'MegaBuzzymontyF' not in ImageCache:
            return
        self.image = ImageCache[f'MegaBuzzy{colour}{dir}']

        if style == 8: # Shy Guy's offset
            if direction == 2:
                self.offset = (-31, -71)
            else:
                self.offset = (-36, -71)
        elif style == 9: # Monty Mole's offset
            if direction == 2:
                self.offset = (-49, -73)
            else:
                self.offset = (-40, -73)
        else: # Buzzy Beetle's offset
            if direction == 2:
                self.offset = (-39, -74)
            else:
                self.offset = (-43, -74)


        super().dataChanged()


class ActorImage_RockyBossWrench(actorlib.ActorImage_StaticMultiple):  # 302
    @staticmethod
    def loadImages():
        if 'RockyBossWrench0' in ImageCache:
            return
        for big in (0, 1):
            for direction in range(3):
                ImageCache[f'RockyBossWrench{big}{direction}'] = actorlib.GetPixmap(f'rocky_boss_wrench_{big}{direction}.png')

    def dataChanged(self):
        big = (self.parent.spritedata[5] >> 4) & 1
        direction = self.parent.spritedata[5] & 3
        if direction == 3:
            direction = 2

        self.image = ImageCache[f'RockyBossWrench{big}{direction}']
        if big:
            self.offset = (
                    (2, -33),
                    (-5, -33),
                    (-11, 5)
                )[direction]
        else:
            self.offset = (
                    (6, -26),
                    (-1, -26),
                    (-5, 11)
                )[direction]

        super().dataChanged()


class ActorImage_NewerHammerBroPlatform(ActorImage_NewerHammerBroNormal):  # 308
    pass


class ActorImage_NewerMegaIcicle(actorlib.ActorImage_StaticMultiple):  # 311
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (-24, -3)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MegaIcicle', 'mega_icicle.png')
        actorlib.loadIfNotInImageCache('MegaCrystal', 'mega_crystal.png')

    def dataChanged(self):
        crystal = (self.parent.spritedata[3] >> 4) & 1
        self.image = ImageCache['MegaIcicle'] if not crystal else ImageCache['MegaCrystal']

        super().dataChanged()


class ActorImage_Flipblock(actorlib.ActorImage_Static):  # 319
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Flipblock'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Flipblock', 'flipblock.png')


class ActorImage_FallingChestnut(actorlib.ActorImage_StaticMultiple):  # 320
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Goomba', 'goomba.png')
        actorlib.loadIfNotInImageCache('Spiny', 'spiny.png')
        actorlib.loadIfNotInImageCache('StarCoin', 'starcoin.png')

        if 'ChestnutBrown' in ImageCache:
            return
        for color in ('Brown', 'Yellow'):
            ImageCache[f'Chestnut{color}'] = actorlib.GetPixmap(f'chestnut_{color}.png')

            items = (
                (4, 'Goomba',   ImageCache['Goomba']),
                (4, 'Spiny',    ImageCache['Spiny']),
                (4, 'Coin',     ImageCache['BlockContents1']),
                (4, 'Fire',     ImageCache['BlockContents3']),
                (3, 'StarCoin', ImageCache['StarCoin']),
            )
            for scaleF, itemName, overlayImage in items:
                newPix = QtGui.QPixmap(ImageCache[f'Chestnut{color}'])
                painter = QtGui.QPainter(newPix)

                w = overlayImage.width()
                h = overlayImage.height()

                painter.drawPixmap(113 - w, 119 - h, int(w * scaleF), int(h * scaleF), overlayImage)
                del painter
                ImageCache[f'Chestnut{color}{itemName}'] = newPix

    def dataChanged(self):
        yellow = self.parent.spritedata[5] & 1
        scale = (self.parent.spritedata[5] >> 4) & 0xF
        item = self.parent.spritedata[3] & 0xF

        color = ("Brown", "Yellow")[yellow]
        itemName = ('Goomba', 'Spiny', 'Coin', 'Fire', 'StarCoin')

        if item >= len(itemName):
            itemStr = ''
        else:
            itemStr = itemName[item]

        if ImageCache['ChestnutBrown'] is None:
            return
        self.image = ImageCache[f'Chestnut{color}{itemStr}'].scaled(*(
            (45, 40),
            (68, 59),
            (92, 80),
            (116, 99),
            (139, 119),
            (163, 140),
            (185, 159),
            (209, 180),
            (233, 199),
            (255, 219),
            (279, 238),
            (303, 258),
            (325, 278),
            (349, 298),
            (372, 318),
            (395, 338)
        )[scale])
        self.offset = (
                (-6, -11),#divide by 1.5
                (-14, -26),
                (-22, -41),
                (-30, -53),
                (-37, -67),
                (-46, -81),
                (-53, -96),
                (-61, -110),
                (-69, -124),
                (-77, -137),
                (-85, -151),
                (-93, -165),
                (-101, -178),
                (-109, -193),
                (-117, -207),
                (-125, -221)
            )[scale]

        super().dataChanged()


class ActorImage_MegaThwomp(actorlib.ActorImage):  # 322
    def __init__(self, parent):
        super().__init__(parent)
        megaThwompAuxImage = actorlib.AuxiliaryImage(parent, 121, 140)
        megaThwompAuxImage.image = ImageCache['MegaThwomp']
        megaThwompAuxImage.setPos(-60, -101)
        self.aux.append(megaThwompAuxImage)

        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Horizontal))
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Horizontal))
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Vertical))

    def dataChanged(self):
        if (
            not isinstance(self.aux[1], actorlib.AuxiliaryTrackObject)
            or not isinstance(self.aux[2], actorlib.AuxiliaryTrackObject)
            or not isinstance(self.aux[3], actorlib.AuxiliaryTrackObject)
        ):
            return

        left_buffer = self.parent.spritedata[2] + 2
        right_buffer = self.parent.spritedata[3] + 2
        top_buffer = self.parent.spritedata[4] + 2

        self.aux[1].setSize(left_buffer * 8, 16)
        self.aux[1].setPos((-left_buffer * 12) + 24, 0)

        self.aux[2].setSize(right_buffer * 8, 16)
        self.aux[2].setPos(0, 0)

        self.aux[3].setSize(16, top_buffer * 8)
        self.aux[3].setPos(0, (-top_buffer * 12) + 24)

        if left_buffer == 2:
            self.aux[1].setSize(0, 0)

        if right_buffer == 2:
            self.aux[2].setSize(0, 0)

        if top_buffer == 2:
            self.aux[3].setSize(0, 0)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MegaThwomp', 'giant_thwomp.png')


class ActorImage_Podouble(actorlib.ActorImage):  # 324
    def __init__(self, parent):
        super().__init__(parent)
        podoubleAuxImage = actorlib.AuxiliaryImage(parent, 110, 110)
        podoubleTrackObject = actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Vertical)
        podoubleAuxImage.setPos(-45, -67)
        podoubleTrackObject.setPos(0, -288)
        self.aux.append(podoubleAuxImage)
        self.aux.append(podoubleTrackObject)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PodoubleFire', 'podouble_fire.png')
        actorlib.loadIfNotInImageCache('PodoubleIce', 'podouble_ice.png')

    def dataChanged(self):
        if (
            not isinstance(self.aux[0], actorlib.AuxiliaryImage)
            or not isinstance(self.aux[1], actorlib.AuxiliaryTrackObject)
        ):
            return
        fire = (self.parent.spritedata[2] >> 4) & 1
        distance = self.parent.spritedata[5] & 0xFF

        self.aux[0].image = ImageCache['PodoubleFire' if fire else 'PodoubleIce']
        self.aux[1].setSize(16, 208 + (distance * 8))


class ActorImage_NewerBigShell(actorlib.ActorImage_StaticMultiple):  # 341
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (-149 / 1.5, -217 / 1.5)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BigShellGreen', 'bigshell_green.png')
        actorlib.loadIfNotInImageCache('BigShellGreenGrass', 'bigshell_green_grass.png')
        actorlib.loadIfNotInImageCache('BigShellRed', 'bigshell_red.png')
        actorlib.loadIfNotInImageCache('BigShellRedGrass', 'bigshell_red_grass.png')
        actorlib.loadIfNotInImageCache('BigShellInside', 'bigshell_inside.png')

    def dataChanged(self):
        style = self.parent.spritedata[5] & 1
        colour = self.parent.spritedata[2] & 1

        colour = ("Green", "Red")[colour]
        if style == 0:
            self.image = ImageCache[f'BigShell{colour}Grass']
        else:
            self.image = ImageCache[f'BigShell{colour}']

        super().dataChanged()

    def paint(self, painter):
        if globals_.Layer0Shown and self.image is not None:
            painter.drawPixmap(0, 0, self.image.width(), self.image.height(), self.image)
        else:
            painter.drawPixmap(0, 0, 322, 248, ImageCache['BigShellInside'])


class ActorImage_ShyGuy(actorlib.ActorImage_StaticMultiple):  # 351
    @staticmethod
    def loadImages():
        if 'ShyGuy0' in ImageCache:
            return
        for i in range(9):  # 0-8
            if i == 7:
                continue  # there's no ShyGuy7.png
            ImageCache[f'ShyGuy{i}'] = actorlib.GetPixmap(f'shyguy_{i}.png')

    def dataChanged(self):
        type = (self.parent.spritedata[2] >> 4) & 15

        #1 & 6 use the same image as 10 & 7 respectively, the rest use 0
        if type == 7:
            imgtype = 6
        elif type == 10:
            imgtype = 1
        elif type == 8 or type in range(1, 7):
            imgtype = type
        else:
            imgtype = 0

        self.image = ImageCache[f'ShyGuy{imgtype}']
        self.offset = (
            (6, -4),  # 0: red
            (6, -7),  # 1: blue
            (6, -6),  # 2: red (sleeper)
            (7, -6),  # 3: yellow (jumper)
            (6, -8),  # 4: purple (judo)
            (6, -6),  # 5: green (spike thrower)
            (2, -9),  # 6: red (ballooneer - horizontal)
            (2, -9),  # 7: red (ballooneer - vertical)
            (2, -14),  # 8: blue (ballooneer - circular)
        )[imgtype]

        super().dataChanged()


class ActorImage_NewerFruit(actorlib.ActorImage_StaticMultiple):  # 357
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Fruit', 'fruit.png')
        actorlib.loadIfNotInImageCache('FruitCherry', 'fruit_cherry.png')

    def dataChanged(self):

        style = self.parent.spritedata[5] & 1
        if style == 0:
            self.image = ImageCache['Fruit']
            self.offset = (0, 0)
        else:
            self.image = ImageCache['FruitCherry']
            self.offset = (-2, -11) #-3, -16

        super().dataChanged()


class ActorImage_NewerBush(actorlib.ActorImage_StaticMultiple):  # 387
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.parent.setZValue(24999)

    @staticmethod
    def loadImages():
        if 'bushgreensmall' in ImageCache:
            return
        for style in ('green', 'yellowish', 'yellow'):
            for size in ('small', 'med', 'large', 'xlarge'):
                ImageCache[f'bush{style}{size}'] = actorlib.GetPixmap(f'bush_{style}_{size}.png')

        if 'bushtreeleafsxlarge' in ImageCache:
            return
        for style in ('brown', 'darkred', 'yellow', 'darkbrown', 'red', 'treeleafs'):
            for size in ('small', 'med', 'large', 'xlarge'):
                ImageCache[f'bush{style}{size}'] = actorlib.GetPixmap(f'bush_{style}_{size}.png')

    def dataChanged(self):
        style = self.parent.spritedata[2] >> 4
        colors = style % 6
        size = self.parent.spritedata[5] & 3
        yellowish = (self.parent.spritedata[5] >> 4) & 1

        bush = ("green", "brown", "darkred", "yellow", "darkbrown", "red")[colors]
        scale = ("small", "med", "large", "xlarge")[size]
        if yellowish:
            self.image = ImageCache[f'bushyellowish{scale}']
        elif style == 15:
            self.image = ImageCache[f'bushtreeleafs{scale}']
        else:
            self.image = ImageCache[f'bush{bush}{scale}']

        if style == 15:
            self.offset = (
                (-59, 29), #89, -43
                (-63, -13), #95, 20
                (-71, -77), #106, 116
                (-86, -289), #129, 433
            )[size]
        else:
            self.offset = (
                (-22, -25),
                (-30, -44),
                (-40, -60),
                (-53, -78),
            )[size]

        super().dataChanged()


class ActorImage_NewerGlowBlock(actorlib.ActorImage):  # 391
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        glowBoxAuxImage = actorlib.AuxiliaryImage(parent, 48, 48)
        glowBoxAuxImage.setPos(-11, -11)
        self.aux.append(glowBoxAuxImage)

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        purple = self.parent.spritedata[2] & 1
        self.aux[0].image = ImageCache['GlowBlock' if not purple else 'GlowBlockPurple']

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GlowBlock', 'glow_block.png')
        actorlib.loadIfNotInImageCache('GlowBlockPurple', 'glow_block_1.png')


class ActorImage_GigaGoomba(actorlib.ActorImage_Static):  # 410
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GigaGoomba'],
            (-128 / 1.5, -188),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GigaGoomba', 'goomba_giga.png')


class ActorImage_NewerGabon(actorlib.ActorImage_StaticMultiple):  # 414
    @staticmethod
    def loadImages():
        if 'GabonLeft' in ImageCache:
            return
        gabon = actorlib.GetImage('gabon.png')
        ImageCache['GabonLeft'] = QtGui.QPixmap.fromImage(gabon)
        ImageCache['GabonRight'] = QtGui.QPixmap.fromImage(gabon.mirrored(True, False))
        actorlib.loadIfNotInImageCache('GabonSpike', 'gabon_spike.png')

        if 'GabonsnowRight' in ImageCache:
            return

        for style in ("red", "orange", "yellow", "snow"):
            gabon = actorlib.GetImage(f'gabon_{style}.png')

            if gabon is None:
                return

            ImageCache[f'Gabon{style}Left'] = QtGui.QPixmap.fromImage(gabon)
            ImageCache[f'Gabon{style}Right'] = QtGui.QPixmap.fromImage(gabon.mirrored(True, False))

        if 'GabonblackSpike' in ImageCache:
            return

        for color in ("red", "orange", "yellow", "green", "purple", "black"):
            ImageCache[f'Gabon{color}Spike'] = actorlib.GetPixmap(f'gabon_{color}_spike.png')

    def dataChanged(self):
        throwdir = self.parent.spritedata[5] & 1
        facing = self.parent.spritedata[4] & 1
        style = self.parent.spritedata[2] & 7

        if 'GabonsnowRight' not in ImageCache:
            return
        color = ("", "red", "orange", "yellow", "", "snow")[style % 6]
        colour = ("", "red", "orange", "yellow", "green", "", "purple", "black")[style & 7]
        if throwdir == 0:
            self.image = ImageCache[f'Gabon{colour}Spike']
            self.offset = (-7, -31) #-11, -47
        else:
            self.image = (
                ImageCache[f'Gabon{color}Left'],
                ImageCache[f'Gabon{color}Right'],
            )[facing]
            self.offset = (-8, -33) #-12, -50

        super().dataChanged()


class ActorImage_NewerFloatingQBlock(ActorImage_Block):  # 433
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49
        self.is_water_block = True

        self.contentsNybble = 5
        self.twelveIsMushroom = True


class ActorImage_NewerBowserSwitchSm(ActorImage_NewerSwitch):  # 478
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.switchType = 'E'


class ActorImage_NewerBowserSwitchLg(actorlib.ActorImage_StaticMultiple):  # 479
    @staticmethod
    def loadImages():
        if 'ELSwitch' in ImageCache:
            return
        elg = actorlib.GetImage('e_switch_lg.png')
        ImageCache['ELSwitch'] = QtGui.QPixmap.fromImage(elg)
        ImageCache['ELSwitchU'] = QtGui.QPixmap.fromImage(elg.mirrored(True, True))

        if 'ELSwitch1' not in ImageCache:
            for i in range(1, 6):
                elg2 = actorlib.GetImage(f'e_switch_lg{i}.png')

                if elg2 is None:
                    return

                ImageCache[f'ELSwitch{i}'] = QtGui.QPixmap.fromImage(elg2)
                ImageCache[f'ELSwitchU{i}'] = QtGui.QPixmap.fromImage(elg2.mirrored(True, True))

    def dataChanged(self):
        midway = (self.parent.spritedata[2] >> 6) & 1
        colour = (self.parent.spritedata[3] & 0xF) % 6
        upsideDown = self.parent.spritedata[5] & 1

        if midway:
            self.alpha = 0.5
        else:
            self.alpha = 1.0

        if 'ELSwitch5' not in ImageCache:
            return
        if colour == 0:
            if not upsideDown:
                self.image = ImageCache['ELSwitch']
                self.offset = (-15, -24)
            else:
                self.image = ImageCache['ELSwitchU']
                self.offset = (-15, 0)
        else:
            if not upsideDown:
                self.image = ImageCache[f'ELSwitch{colour}']
                self.offset = (-15, -40)
            else:
                self.image = ImageCache[f'ELSwitchU{colour}']
                self.offset = (-15, -16)

        super().dataChanged()


ImageClasses = {
    12: ActorImage_StarCollectable,
    13: ActorImage_ClownCar,
    17: ActorImage_MusicBlock,
    18: ActorImage_DragonCoasterPiece,
    19: ActorImage_SamuraiGuy,
    20: ActorImage_NewerGoomba,
    21: ActorImage_NewerParaGoomba,
    22: ActorImage_PumpkinGoomba,
    24: ActorImage_NewerBuzzyBeetle,
    25: ActorImage_NewerSpiny,
    26: ActorImage_NewerUpsideDownSpiny,
    40: ActorImage_NewerQSwitch,
    41: ActorImage_NewerPSwitch,
    42: ActorImage_NewerExcSwitch,
    43: ActorImage_NewerQSwitchBlock,
    45: ActorImage_NewerExcSwitchBlock,
    46: ActorImage_NewerPodoboo,
    47: ActorImage_Thwomp,
    48: ActorImage_GiantThwomp,
    49: ActorImage_FakeStarCoin,
    57: ActorImage_NewerKoopa,
    58: ActorImage_NewerParaKoopa,
    60: ActorImage_NewerSpikeTop,
    78: ActorImage_NewerBouncyCloud,
    63: ActorImage_NewerSpikeBall,
    88: ActorImage_ActorSpawner,
    89: ActorImage_ActorMultiSpawner,
    95: ActorImage_NewerHammerBroNormal,
    98: ActorImage_GiantSpikeBall,
    101: ActorImage_NewerBobomb,
    105: ActorImage_NewerPokey,
    107: actorlib.ActorImage,
    143: ActorImage_ModelLoaderResources,
    145: ActorImage_NewerFloatingBarrel,
    152: ActorImage_MessageBlock,
    153: ActorImage_NewerQSwitchUnused,
    157: ActorImage_BigPumpkin,
    167: ActorImage_ShyGuyGiant,
    168: ActorImage_Thundercloud,
    183: ActorImage_Meteor,
    188: ActorImage_MidwayFlag,
    191: ActorImage_TileEventNewer,
    195: ActorImage_NewerHuckitCrab,
    198: ActorImage_NewerGiantGoomba,
    199: ActorImage_NewerMegaGoomba,
    203: ActorImage_Chest,
    207: ActorImage_QBlock,
    208: ActorImage_QBlockUnused,
    209: ActorImage_BrickBlock,
    210: ActorImage_Topman,
    213: ActorImage_CaptainBowser,
    219: ActorImage_NewerLineBlock,
    223: ActorImage_NewerSpringBlock,
    230: ActorImage_NewerBramball,
    231: ActorImage_NewerWiggleShroom,
    239: ActorImage_EventBlock,
    244: ActorImage_LineEvent,
    250: ActorImage_ElectricLine,
    251: ActorImage_TopmanBoss,
    255: ActorImage_RotatingQBlock,
    256: ActorImage_RotatingBrickBlock,
    269: ActorImage_NewerParabomb,
    279: ActorImage_RockyBoss,
    282: ActorImage_AngrySun,
    283: ActorImage_FuzzyBear,
    286: ActorImage_NewerWoodCircle,
    290: ActorImage_Boolossus,
    291: ActorImage_NewerParabeetle,
    292: ActorImage_NewerHeavyParabeetle,
    296: ActorImage_NewerMegaBuzzy,
    302: ActorImage_RockyBossWrench,
    308: ActorImage_NewerHammerBroPlatform,
    311: ActorImage_NewerMegaIcicle,
    319: ActorImage_Flipblock,
    320: ActorImage_FallingChestnut,
    321: ActorImage_ModelLoaderResources,
    322: ActorImage_MegaThwomp,
    324: ActorImage_Podouble,
    341: ActorImage_NewerBigShell,
    351: ActorImage_ShyGuy,
    357: ActorImage_NewerFruit,
    387: ActorImage_NewerBush,
    391: ActorImage_NewerGlowBlock,
    402: ActorImage_LineQBlock,
    403: ActorImage_LineBrickBlock,
    410: ActorImage_GigaGoomba,
    414: ActorImage_NewerGabon,
    433: ActorImage_NewerFloatingQBlock,
    478: ActorImage_NewerBowserSwitchSm,
    479: ActorImage_NewerBowserSwitchLg,
}
