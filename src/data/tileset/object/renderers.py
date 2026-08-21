import globals_


def RenderObject(tileset, objnum, width, height, fullslope=False):
    """
    Render a tileset object into an array
    """
    # allocate an array
    dest = [[0] * width for _ in range(height)]

    # ignore non-existent objects
    try:
        tileset_defs = globals_.ObjectDefinitions[tileset]
    except IndexError:
        tileset_defs = None

    if tileset_defs is None:
        return dest

    try:
        obj = tileset_defs[objnum]
    except IndexError:
        obj = None

    if obj is None or not obj.rows:
        return dest

    # Diagonal objects are rendered differently
    if (obj.rows[0][0][0] & 0x80) != 0:
        RenderDiagonalObject(dest, obj, width, height, fullslope)
        return dest

    # Standard object
    repeatFound = False
    beforeRepeat = []
    inRepeat = []
    afterRepeat = []

    for row in obj.rows:
        if not row: continue

        if (row[0][0] & 2) != 0:
            repeatFound = True
            inRepeat.append(row)
        else:
            if repeatFound:
                afterRepeat.append(row)
            else:
                beforeRepeat.append(row)

    bc = len(beforeRepeat)
    ic = len(inRepeat)
    ac = len(afterRepeat)
    if ic == 0:
        for y in range(height):
            RenderStandardRow(dest[y], beforeRepeat[y % bc], y, width)
    else:
        afterthreshold = height - ac - 1
        for y in range(height):
            if y < bc:
                RenderStandardRow(dest[y], beforeRepeat[y], y, width)
            elif y > afterthreshold:
                RenderStandardRow(dest[y], afterRepeat[y - height + ac], y, width)
            else:
                RenderStandardRow(dest[y], inRepeat[(y - bc) % ic], y, width)

    return dest


def RenderStandardRow(dest, row, y, width):
    """
    Render a row from an object
    """
    repeatFound = False
    beforeRepeat = []
    inRepeat = []
    afterRepeat = []

    for tile in row:
        tiling = (tile[0] & 1) != 0

        if tiling:
            repeatFound = True
            inRepeat.append(tile)
        else:
            if repeatFound:
                afterRepeat.append(tile)
            else:
                beforeRepeat.append(tile)

    bc = len(beforeRepeat)
    ic = len(inRepeat)
    ac = len(afterRepeat)
    if ic == 0:
        for x in range(width):
            dest[x] = beforeRepeat[x % bc][1]
    else:
        afterthreshold = width - ac - 1
        for x in range(width):
            if x < bc:
                dest[x] = beforeRepeat[x][1]
            elif x > afterthreshold:
                dest[x] = afterRepeat[x - width + ac][1]
            else:
                dest[x] = inRepeat[(x - bc) % ic][1]


def RenderDiagonalObject(dest, obj, width, height, fullslope):
    """
    Render a diagonal object
    """
    # Set all to empty tiles
    for row in dest:
        for x in range(width):
            row[x] = -1

    # Get sections
    mainBlock, subBlock = GetSlopeSections(obj)
    cbyte = obj.rows[0][0][0]

    # Get direction
    goLeft = ((cbyte & 1) != 0)
    goDown = ((cbyte & 2) != 0)

    # Base the amount to draw by seeing how much we can fit in each direction
    if fullslope:
        drawAmount = max(height // len(mainBlock), width // len(mainBlock[0]))
    else:
        drawAmount = min(height // len(mainBlock), width // len(mainBlock[0]))

    if not goLeft and not goDown:
        # slope going from SW => NE
        # start off at the bottom left
        x = 0
        y = height - len(mainBlock) - (0 if subBlock is None else len(subBlock))
        xi = len(mainBlock[0])
        yi = -len(mainBlock)

    elif goLeft and not goDown:
        # slope going from SE => NW
        # start off at the top left
        x = 0
        y = 0
        xi = len(mainBlock[0])
        yi = len(mainBlock)

    elif not goLeft and goDown:
        # slope going from NW => SE
        # start off at the top left
        x = 0
        y = (0 if subBlock is None else len(subBlock))
        xi = len(mainBlock[0])
        yi = len(mainBlock)

    else:
        # slope going from SW => NE
        # start off at the bottom left
        x = 0
        y = height - len(mainBlock)
        xi = len(mainBlock[0])
        yi = -len(mainBlock)

    # Finally draw it
    for i in range(drawAmount):
        PutObjectArray(dest, x, y, mainBlock, width, height)
        if subBlock is not None:
            xb = x
            if goLeft: xb = x + len(mainBlock[0]) - len(subBlock[0])
            if goDown:
                PutObjectArray(dest, xb, y - len(subBlock), subBlock, width, height)
            else:
                PutObjectArray(dest, xb, y + len(mainBlock), subBlock, width, height)
        x += xi
        y += yi


def PutObjectArray(dest, xo, yo, block, width, height):
    """
    Places a tile array into an object
    """
    for y in range(yo, yo + len(block)):
        if y < 0: continue
        if y >= height: continue
        drow = dest[y]
        srow = block[y - yo]

        for x in range(xo, xo + len(srow)):
            if x < 0: continue
            if x >= width: continue
            drow[x] = srow[x - xo][1]

def GetSlopeSections(obj):
    """
    Sorts the slope data into sections
    """
    sections = []
    currentSection = []

    for row in obj.rows:
        # Begin new section
        if row and (row[0][0] & 0x80) != 0:
            if currentSection:
                sections.append(CreateSection(currentSection))
            currentSection = []
        currentSection.append(row)

    # End last section
    if currentSection:
        sections.append(CreateSection(currentSection))

    if len(sections) == 1:
        return (sections[0], None)
    else:
        return (sections[0], sections[1])

def CreateSection(rows):
    """
    Create a slope section
    """
    # Calculate width
    width = 0
    for row in rows:
        thiswidth = CountTiles(row)
        width = max(width, thiswidth)

    # Create the section
    section = []
    for row in rows:
        drow = [0] * width
        x = 0
        for tile in row:
            if (tile[0] & 0x80) == 0:
                drow[x] = tile
                x += 1
        section.append(drow)

    return section

def CountTiles(row):
    """
    Counts the amount of real tiles in an object row
    """
    res = 0
    for tile in row:
        if (tile[0] & 0x80) == 0:
            res += 1
    return res


def IncrementTilesetFrame():
    """
    Moves each tileset to the next frame
    """
    if not globals_.TilesetsAnimating: return
    for tile in globals_.Tiles:
        if tile is not None: tile.nextFrame()

    # TODO: Test if this is more efficient over updating the entire scene
    # (seems obvious on paper, but tests are wildly inconsistent and give no answer)
    # for layer in globals_.Area.layers:
    #     for obj in layer:
    #         obj.update()

    main_window = globals_.mainWindow
    if main_window is not None:
        main_window.scene.update()
        main_window.objPicker.update()
