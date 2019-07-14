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

# Newer-specific base classes
class SpriteImage_NewerSwitch(common.SpriteImage_Switch):

    @staticmethod
    def loadImages():
        common.SpriteImage_Switch.loadImages()

        if 'QSwitch2' not in ImageCache:
            for i in range(2, 5):
                p = SLib.GetImg('q_switch%d.png' % i, True)

                if p is None:
                    # happens when the newer patch folder is not loaded yet
                    return

                ImageCache['QSwitch%d' % i] = QtGui.QPixmap.fromImage(p)
                ImageCache['QSwitchU%d' % i] = QtGui.QPixmap.fromImage(p.mirrored(True, True))

        if 'ExSwitch2' not in ImageCache:
            for i in range(2, 5):
                p = SLib.GetImg('e_switch%d.png' % i, True)
                ImageCache['ESwitch%d' % i] = QtGui.QPixmap.fromImage(p)
                ImageCache['ESwitchU%d' % i] = QtGui.QPixmap.fromImage(p.mirrored(True, True))

    def dataChanged(self):
        self.styleType = self.parent.spritedata[3] & 0xF
        upsideDown = self.parent.spritedata[5] & 1

        if self.styleType > 0:
            self.yOffset = -16 + 32 * upsideDown
        else:
            self.yOffset = 0

        if self.styleType == 1 or self.styleType > 4:
            self.styleType = 0

        # hack needed if data is changed before patch folder is loaded
        if 'QSwitch2' not in ImageCache:
            return

        super().dataChanged()

################################################################################
################################################################################
################################################################################

class SpriteImage_StarCollectable(SLib.SpriteImage_Static):  # 12
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['StarCollectable'],
            (3, 3),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('StarCollectable', 'star_collectable.png')


class SpriteImage_ClownCar(SLib.SpriteImage_Static):  # 13
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ClownCar'],
            (16, -28),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('ClownCar', 'clown_car.png')


# TODO: Fix massive artifacts when moving the sprite image, caused by an incorrect
# bounding rectangle.
class SpriteImage_DragonCoasterPiece(SLib.SpriteImage_StaticMultiple): # 18
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5
        )

        self.yOffset = -4

    @staticmethod
    def loadImages():
        if 'DragonHead' in ImageCache: return
        ImageCache['DragonHead'] = SLib.GetImg('dragon_coaster_head.png')
        ImageCache['DragonBody'] = SLib.GetImg('dragon_coaster_body.png')
        ImageCache['DragonTail'] = SLib.GetImg('dragon_coaster_tail.png')

    def dataChanged(self):
        piece = self.parent.spritedata[5] & 3
        direction = (self.parent.spritedata[3] >> 4) & 1
        rotates = self.parent.spritedata[2] & 0x10

        sPiece = ("Head", "Body", "Tail")[piece]

        self.image = ImageCache["Dragon%s" % sPiece]

        transform = None

        if direction == 1:
            transform = QtGui.QTransform()
            transform.translate(12, 0)
            transform.scale(-1, 1)
            transform.translate(-12, 0)
        else:
            self.xOffset = -16

        if rotates:
            if transform is None:
                transform = QtGui.QTransform()

            angle = self.parent.spritedata[2] & 0xF

            if angle < 8:
                angle -= 8
            else:
                angle -= 7

            angle *= (180.0 / 16)

            transform.translate(24, 15)
            transform.rotate(angle)
            transform.translate(-24, -15)

        if transform is not None:
            self.parent.setTransform(transform)

        super().dataChanged()


class SpriteImage_SamuraiGuy(SLib.SpriteImage_Static):  # 19
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SamuraiGuy'],
            (-1, 20),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('SamuraiGuy', 'samurai_guy.png')


class SpriteImage_NewerGoomba(SLib.SpriteImage_StaticMultiple):  # 20
    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Goomba', 'goomba.png')
        if 'Goomba1' in ImageCache: return
        for i in range(8):
            ImageCache['Goomba%d' % (i + 1)] = SLib.GetImg('goomba_%d.png' % (i + 1))

    def dataChanged(self):

        color = (self.parent.spritedata[2] & 0xF) % 9

        if color == 0:
            self.image = ImageCache['Goomba']
            self.offset = (-1, -4)
        else:
            self.image = ImageCache['Goomba%d' % color]
            self.offset = (0, -4) if color not in (7, 8) else (0, -5)

        super().dataChanged()


class SpriteImage_PumpkinGoomba(SLib.SpriteImage_StaticMultiple):  # 22
    def __init__(self, parent):
        super().__init__(parent)
        self.offset = (-4, -48)

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('PumpkinGoomba', 'pumpkin_goomba.png')
        SLib.loadIfNotInImageCache('PumpkinParagoomba', 'pumpkin_paragoomba.png')

    def dataChanged(self):
        para = self.parent.spritedata[5] & 1
        self.image = ImageCache['PumpkinGoomba' if not para else 'PumpkinParagoomba']

        super().dataChanged()


class SpriteImage_NewerBuzzyBeetle(SLib.SpriteImage_StaticMultiple):  # 24
    @staticmethod
    def loadImages():
        if "BuzzyBeetle" not in ImageCache:
            ImageCache["BuzzyBeetle"] = SLib.GetImg('buzzy_beetle.png')
            ImageCache["BuzzyBeetleU"] = SLib.GetImg('buzzy_beetle_u.png')
            ImageCache["BuzzyBeetleShell"] = SLib.GetImg('buzzy_beetle_shell.png')
            ImageCache["BuzzyBeetleShellU"] = SLib.GetImg('buzzy_beetle_shell_u.png')

        if "BuzzyBeetleBlack" not in ImageCache:
            for colour in ("Black", "Blue", "Green", "Orange", "Purple", "Red", "Yellow"):
                ImageCache["BuzzyBeetle%s" % colour] = SLib.GetImg('buzzy_beetle_%s.png' % colour.lower())
                ImageCache["BuzzyBeetle%sU" % colour] = SLib.GetImg('buzzy_beetle_%s_u.png' % colour.lower())
                ImageCache["BuzzyBeetle%sShell" % colour] = SLib.GetImg('buzzy_beetle_%s_shell.png' % colour.lower())
                ImageCache["BuzzyBeetle%sShellU" % colour] = SLib.GetImg('buzzy_beetle_%s_shell_u.png' % colour.lower())

    def dataChanged(self):

        orient = self.parent.spritedata[5] & 15
        colour = self.parent.spritedata[2] & 15
        if colour > 7:
            colour = 0

        colour = ("", "Red", "Orange", "Yellow", "Green", "Blue", "Purple", "Black")[colour]
        if orient == 1:
            self.image = ImageCache['BuzzyBeetle%sU' % colour]
            self.yOffset = 0
        elif orient == 2:
            self.image = ImageCache['BuzzyBeetle%sShell' % colour]
            self.yOffset = 2
        elif orient == 3:
            self.image = ImageCache['BuzzyBeetle%sShellU' % colour]
            self.yOffset = 2
        else:
            self.image = ImageCache['BuzzyBeetle%s' % colour]
            self.yOffset = 0

        super().dataChanged()


class SpriteImage_NewerQSwitch(SpriteImage_NewerSwitch): # 40
    def __init__(self, parent):
        super().__init__(parent)
        self.switchType = "Q"


class SpriteImage_ExcSwitch(SpriteImage_NewerSwitch):  # 42
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.switchType = 'E'


class SpriteImage_Thwomp(SLib.SpriteImage_StaticMultiple):  # 47
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Thwomp'],
            (-6, -6),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Thwomp', 'thwomp.png')
        SLib.loadIfNotInImageCache('ThwompIce', 'thwomp_ice.png')

    def dataChanged(self):
        icy = self.parent.spritedata[2] & 1

        if icy:
            self.image = ImageCache['ThwompIce']
        else:
            self.image = ImageCache['Thwomp']


class SpriteImage_GiantThwomp(SLib.SpriteImage_StaticMultiple):  # 48
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GiantThwomp'],
            (-8, -8),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('GiantThwomp', 'giant_thwomp.png')
        SLib.loadIfNotInImageCache('GiantThwompIce', 'giant_thwomp_ice.png')

    def dataChanged(self):
        icy = self.parent.spritedata[2] & 1

        if icy:
            self.image = ImageCache['GiantThwompIce']
        else:
            self.image = ImageCache['GiantThwomp']


class SpriteImage_FakeStarCoin(SLib.SpriteImage_Static):  # 49
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['FakeStarCoin'],
            (-8, -16),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('FakeStarCoin', 'starcoin_fake.png')


class SpriteImage_NewerKoopa(SLib.SpriteImage_StaticMultiple):  # 57
    @staticmethod
    def loadImages():
        if 'KoopaG' in ImageCache: return
        ImageCache['KoopaG'] = SLib.GetImg('koopa_green.png')
        ImageCache['KoopaR'] = SLib.GetImg('koopa_red.png')
        ImageCache['KoopaShellG'] = SLib.GetImg('koopa_green_shell.png')
        ImageCache['KoopaShellR'] = SLib.GetImg('koopa_red_shell.png')
        for flag in (0, 1):
            for style in range(4):
                ImageCache['Koopa%d%d' % (flag, style + 1)] = \
                    SLib.GetImg('koopa_%d%d.png' % (flag, style + 1))
                if style < 3:
                    ImageCache['KoopaShell%d%d' % (flag, style + 1)] = \
                        SLib.GetImg('koopa_shell_%d%d.png' % (flag, style + 1))

    def dataChanged(self):
        # get properties
        props = self.parent.spritedata[5]
        shell = (props >> 4) & 1
        red = props & 1
        texhack = (self.parent.spritedata[2] & 0xF) % 5

        if not shell:

            if texhack == 0:
                self.offset = (-7, -15)
                self.image = ImageCache['KoopaG'] if not red else ImageCache['KoopaR']
            else:
                self.offset = (-5, -13)
                self.image = ImageCache['Koopa%d%d' % (red, texhack)]
        else:
            del self.offset

            if texhack in (0, 4):
                self.image = ImageCache['KoopaShellG'] if not red else ImageCache['KoopaShellR']
            else:
                self.image = ImageCache['KoopaShell%d%d' % (red, texhack)]

        super().dataChanged()


class SpriteImage_NewerSpikeBall(SLib.SpriteImage_StaticMultiple):  # 63
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SpikeBall'],
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('SpikeBall', 'spike_ball.png')
        SLib.loadIfNotInImageCache('SnowBall', 'snow_ball.png')

    def dataChanged(self):
        snowy = self.parent.spritedata[2] & 1
        if snowy:
            self.image = ImageCache['SnowBall']
        else:
            self.image = ImageCache['SpikeBall']


class SpriteImage_NewerBouncyCloud(SLib.SpriteImage_StaticMultiple):  # 78
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['CloudTrSmall'],
            (-2, -2),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('CloudTrBig', 'cloud_trampoline_big.png')
        SLib.loadIfNotInImageCache('CloudTrSmall', 'cloud_trampoline_small.png')

        if 'CloudTrBig1' in ImageCache:
            return

        for size in ("Big", "Small"):
            for style in range(1, 7):
                name = "CloudTr%s%d" % (size, style)
                ImageCache[name] = SLib.GetImg("cloud_trampoline_%s%d.png" % (size.lower(), style))

    def dataChanged(self):
        style = self.parent.spritedata[2] & 0xF
        raw_size = (self.parent.spritedata[4] >> 4) & 1
        size = "Small" if raw_size == 0 else "Big"

        if style == 0 or style > 7:
            self.image = ImageCache['CloudTr%s' % size]
            self.offset = (-2, -2)
        else:
            self.image = ImageCache['CloudTr%s%d' % (size, style)]
            self.offset = (-2, -2)

        super().dataChanged()


class SpriteImage_GiantSpikeBall(SLib.SpriteImage_StaticMultiple):  # 98
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GiantSpikeBall'],
            (-24, -24),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('GiantSpikeBall', 'giant_spike_ball.png')
        SLib.loadIfNotInImageCache('GiantSnowBall', 'giant_snow_ball.png')

    def dataChanged(self):
        snowy = self.parent.spritedata[2] & 1

        if snowy:
            self.image = ImageCache['GiantSnowBall']
        else:
            self.image = ImageCache['GiantSpikeBall']


class SpriteImage_MessageBlock(SLib.SpriteImage_Static): # 152
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            SLib.Tiles[0x98].main,
            (8, 0)
        )


class SpriteImage_BigPumpkin(SLib.SpriteImage_StaticMultiple):  # 157
    def __init__(self, parent):
        super().__init__(parent)
        self.offset = (-8, -16)

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BigPumpkin', 'giant_pumpkin.png')
        SLib.loadIfNotInImageCache('ShipKey', 'ship_key.png')
        SLib.loadIfNotInImageCache('5Coin', '5_coin.png')

        if 'YoshiFire' not in ImageCache:
            pix = QtGui.QPixmap(48, 24)
            pix.fill(Qt.transparent)
            paint = QtGui.QPainter(pix)
            paint.drawPixmap(0, 0, ImageCache['Blocks'][9])
            paint.drawPixmap(24, 0, ImageCache['Blocks'][3])
            del paint
            ImageCache['YoshiFire'] = pix

        for power in range(0x10):
            if power in (0, 8, 12, 13):
                ImageCache['BigPumpkin%d' % power] = ImageCache['BigPumpkin']
                continue

            x, y = 36, 48
            overlay = ImageCache['Blocks'][power]
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
            ImageCache['BigPumpkin%d' % power] = new

    def dataChanged(self):

        power = self.parent.spritedata[5] & 0xF
        self.image = ImageCache['BigPumpkin%d' % power]
        super().dataChanged()


class SpriteImage_ShyGuyGiant(SLib.SpriteImage_Static): # 167
    def __init__(self, parent):
        super().__init__(parent, 1.5)
    
    @staticmethod
    def loadImages():
        if "ShyGuy%s%s" in ImageCache: return
        for size in ("Big", "Mega", "Colossal"):
            for colour in ("Red", "Blue", "Green", "Yellow", "Magenta"):
                ImageCache['ShyGuy%s%s' % (size, colour)] = SLib.GetImg('shyguy_%s_%s.png' % (size, colour))
    
    def dataChanged(self):
        size = (self.parent.spritedata[2] >> 4) & 3
        colour = (self.parent.spritedata[2] & 0xF) % 5
        scale = ("Big", "Mega", "Colossal")[size]
        color = ("Red", "Blue", "Green", "Yellow", "Magenta")[colour]
        
        self.image = ImageCache['ShyGuy%s%s' % (scale, color)]
        
        if size == 0:
            self.offset = (-12.7, -128)
        elif size == 1:
            self.offset = (-32, -165.3)
        else:
            self.offset = (-52.7, -229.3)

        super().dataChanged()


class SpriteImage_Thundercloud(SLib.SpriteImage_Static):  # 168
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Thundercloud'],
            (-24, -40),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Thundercloud', 'thundercloud.png')


class SpriteImage_Meteor(SLib.SpriteImage_StaticMultiple):  # 183
    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Meteor', 'meteor.png')
        SLib.loadIfNotInImageCache('MeteorElectric', 'meteor_electric.png')

    def dataChanged(self):
        multiplier = self.parent.spritedata[4] / 20.0
        if multiplier == 0: multiplier = 0.01
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

        self.image = base.scaled(
            (base.width() * multiplier) + 8,
            (base.height() * multiplier) + 8,
        )
        self.offset = (
            (relXoff * multiplier) + absXoff,
            (relYoff * multiplier) + absYoff,
        )

        super().dataChanged()


class SpriteImage_MidwayFlag(SLib.SpriteImage_StaticMultiple):  # 188
    def __init__(self, parent):
        super().__init__(parent)
        self.yOffset = -37

    @staticmethod
    def loadImages():
        if 'MidwayFlag0' in ImageCache: return
        for i in range(18):
            ImageCache['MidwayFlag%d' % i] = SLib.GetImg('midway_flag_%d.png' % i)

    def dataChanged(self):

        style = self.parent.spritedata[2]
        if style > 17: style = 0

        self.image = ImageCache['MidwayFlag%d' % style]

        super().dataChanged()


class SpriteImage_TileEventNewer(common.SpriteImage_TileEvent):  # 191
    def __init__(self, parent):
        super().__init__(parent)
        self.notAllowedTypes = (2, 5, 7, 13, 15)

    def getTileFromType(self, type_):
        if type_ == 0:
            return SLib.Tiles[55]

        if type_ == 1:
            return SLib.Tiles[48]

        if type_ == 3:
            return SLib.Tiles[52]

        if type_ == 4:
            return SLib.Tiles[51]

        if type_ == 6:
            return SLib.Tiles[45]

        if type_ in [8, 9, 10, 11]:
            row = self.parent.spritedata[2] & 0xF
            col = self.parent.spritedata[3] >> 4

            tilenum = 256 * (type_ - 8)
            tilenum += row * 16 + col

            return SLib.Tiles[tilenum]

        if type_ == 12:
            return SLib.Tiles[256 * 3 + 67]

        if type_ == 14:
            return SLib.Tiles[256]

        return None
        

class SpriteImage_NewerHuckitCrab(SLib.SpriteImage_StaticMultiple):  # 195
    @staticmethod
    def loadImages():
        if 'HuckitCrabWhiteR' in ImageCache: return
        Huckitcrab = SLib.GetImg('huckit_crab.png', True)
        Wintercrab = SLib.GetImg('huckit_crab_white.png', True)
        ImageCache['HuckitCrabL'] = QtGui.QPixmap.fromImage(Huckitcrab)
        ImageCache['HuckitCrabR'] = QtGui.QPixmap.fromImage(Huckitcrab.mirrored(True, False))
        ImageCache['HuckitCrabWhiteL'] = QtGui.QPixmap.fromImage(Wintercrab)
        ImageCache['HuckitCrabWhiteR'] = QtGui.QPixmap.fromImage(Wintercrab.mirrored(True, False))

    def dataChanged(self):
        info = self.parent.spritedata[5]
        colour = self.parent.spritedata[2] & 1

        colour = ("", "White")[colour]
        if info == 1:
            self.image = ImageCache['HuckitCrab%sR' % colour]
            self.xOffset = 0
        else:
            if info == 13:
                self.image = ImageCache['HuckitCrab%sR' % colour]
                self.xOffset = 0
            else:
                self.image = ImageCache['HuckitCrab%sL' % colour]
                self.xOffset = -16

        super().dataChanged()


class SpriteImage_Topman(SLib.SpriteImage_Static):  # 210
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Topman'],
            (-22, -32),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Topman', 'topman.png')


class SpriteImage_CaptainBowser(SLib.SpriteImage_Static):  # 213
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['CaptainBowser'],
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('CaptainBowser', 'captain_bowser.png')


class SpriteImage_EventBlock(SLib.SpriteImage_Static): # 239
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            SLib.Tiles[0x97].main,
            (-8, -16)
        )


class SpriteImage_TopmanBoss(SLib.SpriteImage_Static):  # 251
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
        SLib.loadIfNotInImageCache('TopmanBoss', 'topman_boss.png')


class SpriteImage_RockyBoss(SLib.SpriteImage_Static):  # 279
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['RockyBoss'],
            (-25, -33),
        )

        self.aux.append(SLib.AuxiliaryRectOutline(parent, 71, 77, -166, -50))
        self.aux.append(SLib.AuxiliaryRectOutline(parent, 71, 77, -334, -2))

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('RockyBoss', 'rocky_boss.png')


class SpriteImage_AngrySun(SLib.SpriteImage_StaticMultiple):  # 282
    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('AngrySun', 'angry_sun.png')
        SLib.loadIfNotInImageCache('AngryMoon', 'angry_moon.png')

    def dataChanged(self):
        isMoon = self.parent.spritedata[5] & 1
        self.image = ImageCache['AngrySun' if not isMoon else 'AngryMoon']
        self.offset = (-18, -18) if not isMoon else (-13, -13)

        super().dataChanged()


class SpriteImage_FuzzyBear(SLib.SpriteImage_StaticMultiple):  # 283
    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('FuzzyBear', 'fuzzy_bear.png')
        SLib.loadIfNotInImageCache('FuzzyBearBig', 'fuzzy_bear_big.png')

    def dataChanged(self):
        big = (self.parent.spritedata[2] >> 4) & 1
        self.image = ImageCache['FuzzyBear' if not big else 'FuzzyBearBig']

        super().dataChanged()


class SpriteImage_Boolossus(SLib.SpriteImage_Static):  # 290
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Boolossus'],
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Boolossus', 'boolossus.png')


class SpriteImage_Flipblock(SLib.SpriteImage_Static):  # 319
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Flipblock'],
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Flipblock', 'flipblock.png')


class SpriteImage_MegaThwomp(SLib.SpriteImage):  # 322
    def __init__(self, parent):
        super().__init__(parent)
        self.aux.append(SLib.AuxiliaryImage(parent, 121, 140))
        self.aux[0].image = ImageCache['MegaThwomp']
        self.aux[0].setPos(-60, -101)

        self.aux.append(SLib.AuxiliaryTrackObject(parent, 16, 16, SLib.AuxiliaryTrackObject.Horizontal))
        self.aux.append(SLib.AuxiliaryTrackObject(parent, 16, 16, SLib.AuxiliaryTrackObject.Horizontal))
        self.aux.append(SLib.AuxiliaryTrackObject(parent, 16, 16, SLib.AuxiliaryTrackObject.Vertical))

    def dataChanged(self):
        super().dataChanged()

        left_buffer = self.parent.spritedata[2] + 2
        right_buffer = self.parent.spritedata[3] + 2
        top_buffer = self.parent.spritedata[4] + 2

        self.aux[1].setSize(left_buffer * 8, 16)
        self.aux[1].setPos((-left_buffer * 12) + 24, 0)

        self.aux[2].setSize(right_buffer * 8, 16)
        self.aux[2].setPos(0, 0)

        self.aux[3].setSize(16, top_buffer * 8)
        self.aux[3].setPos(0, (-top_buffer * 12) + 24)

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('MegaThwomp', 'giant_thwomp.png')


class SpriteImage_Podoboule(SLib.SpriteImage_StaticMultiple):  # 324
    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('PodobouleFire', 'podoboule_fire.png')
        SLib.loadIfNotInImageCache('PodobouleIce', 'podoboule_ice.png')

    def dataChanged(self):
        fire = (self.parent.spritedata[2] >> 4) & 1
        self.image = ImageCache['PodobouleFire' if fire else 'PodobouleIce']

        super().dataChanged()


class SpriteImage_ShyGuy(SLib.SpriteImage_StaticMultiple):  # 351
    @staticmethod
    def loadImages():
        if 'ShyGuy0' in ImageCache: return
        for i in range(9):  # 0-8
            if i == 7: continue  # there's no ShyGuy7.png
            ImageCache['ShyGuy%d' % i] = SLib.GetImg('shyguy_%d.png' % i)

    def dataChanged(self):
        type = (self.parent.spritedata[2] >> 4) % 9

        imgtype = type if type != 7 else 6  # both linear ballooneers have image 6
        self.image = ImageCache['ShyGuy%d' % imgtype]

        self.offset = (
            (6, -7),  # 0: red
            (6, -7),  # 1: blue
            (6, -4),  # 2: red (sleeper)
            (7, -6),  # 3: yellow (jumper)
            (6, -8),  # 4: purple (judo)
            (6, -8),  # 5: green (spike thrower)
            (2, -9),  # 6: red (ballooneer - vertical)
            (2, -9),  # 7: red (ballooneer - horizontal)
            (2, -9),  # 8: blue (ballooneer - circular)
        )[type]

        super().dataChanged()


class SpriteImage_GigaGoomba(SLib.SpriteImage_Static):  # 410
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GigaGoomba'],
            (-108, -160),
        )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('GigaGoomba', 'goomba_giga.png')


ImageClasses = {
    12: SpriteImage_StarCollectable,
    13: SpriteImage_ClownCar,
    18: SpriteImage_DragonCoasterPiece,
    19: SpriteImage_SamuraiGuy,
    20: SpriteImage_NewerGoomba,
    22: SpriteImage_PumpkinGoomba,
    24: SpriteImage_NewerBuzzyBeetle,
    40: SpriteImage_NewerQSwitch,
    42: SpriteImage_ExcSwitch,
    47: SpriteImage_Thwomp,
    48: SpriteImage_GiantThwomp,
    49: SpriteImage_FakeStarCoin,
    57: SpriteImage_NewerKoopa,
    78: SpriteImage_NewerBouncyCloud,
    63: SpriteImage_NewerSpikeBall,
    98: SpriteImage_GiantSpikeBall,
    107: SLib.SpriteImage,
    152: SpriteImage_MessageBlock,
    157: SpriteImage_BigPumpkin,
    167: SpriteImage_ShyGuyGiant,
    168: SpriteImage_Thundercloud,
    183: SpriteImage_Meteor,
    188: SpriteImage_MidwayFlag,
    191: SpriteImage_TileEventNewer,
    195: SpriteImage_NewerHuckitCrab,
    210: SpriteImage_Topman,
    213: SpriteImage_CaptainBowser,
    239: SpriteImage_EventBlock,
    251: SpriteImage_TopmanBoss,
    279: SpriteImage_RockyBoss,
    282: SpriteImage_AngrySun,
    283: SpriteImage_FuzzyBear,
    290: SpriteImage_Boolossus,
    319: SpriteImage_Flipblock,
    322: SpriteImage_MegaThwomp,
    324: SpriteImage_Podoboule,
    351: SpriteImage_ShyGuy,
    410: SpriteImage_GigaGoomba,
}
