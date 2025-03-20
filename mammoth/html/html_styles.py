"""
    Style definitions simulating specific styles defined in Microsoft Word following the OpenOfficeXML documentation.
    Not all style definitions are correct or proper. I paid more attention to the ones I cared most.
    If you find a style is not sufficient, update this file to reflect a better simulation of the MS styles.
    I attempt to organize the styles by dictionaries with the key being the token string found in the XML and the
    value being the CSS result that should be injected in the HTML output.
"""

"""
    All possible WordML shapes below. For now, I only define a select few.
    See `DrawingML <http://officeopenxml.com/drwSp-prstGeom.php>`_

    accentBorderCallout1
    accentBorderCallout2
    accentBorderCallout3
    accentCallout1
    accentCallout2
    accentCallout3
    actionButtonBackPrevious
    actionButtonBeginning
    actionButtonBlank
    actionButtonDocument
    actionButtonEnd
    actionButtonForwardNext
    actionButtonHelp
    actionButtonHome
    actionButtonInformation
    actionButtonMovie
    actionButtonReturn
    actionButtonSound
    arc
    bentArrow
    bentConnector2
    bentConnector3
    bentConnector4
    bentConnector5
    bentUpArrow
    bevel
    blockArc
    borderCallout1
    borderCallout2
    borderCallout3
    bracePair
    bracketPair
    callout1
    callout2
    callout3
    can
    chartPlus
    chartStar
    chartX
    chevron
    chord
    circularArrow
    cloud
    cloudCallout
    corner
    cornerTabs
    cube
    curvedConnector2
    curvedConnector3
    curvedConnector4
    curvedConnector5
    curvedDownArrow
    curvedLeftArrow
    curvedRightArrow
    curvedUpArrow
    decagon
    diagStripe
    diamond
    dodecagon
    donut
    doubleWave
    downArrow
    downArrowCallout
    ellipse
    ellipseRibbon
    ellipseRibbon2
    flowChartAlternateProcess
    flowChartCollate
    flowChartConnector
    flowChartDecision
    flowChartDelay
    flowChartDisplay
    flowChartDocument
    flowChartExtract
    flowChartInputOutput
    flowChartInternalStorage
    flowChartMagneticDisk
    flowChartMagneticDrum
    flowChartMagneticTape
    flowChartManualInput
    flowChartManualOperation
    flowChartMerge
    flowChartMultidocument
    flowChartOfflineStorage
    flowChartOffpageConnector
    flowChartOnlineStorage
    flowChartOr
    flowChartPredefinedProcess
    flowChartPreparation
    flowChartProcess
    flowChartPunchedCard
    flowChartPunchedTape
    flowChartSort
    flowChartSummingJunction
    flowChartTerminator
    folderCorner
    frame
    funnel
    gear6
    gear9
    halfFrame
    heart
    heptagon
    hexagon
    homePlate
    horizontalScroll
    irregularSeal1
    irregularSeal2
    leftArrow
    leftArrowCallout
    leftBrace
    leftBracket
    leftCircularArrow
    leftRightArrow
    leftRightArrowCallout
    leftRightCircularArrow
    leftRightRibbon
    irregularSeal1
    leftRightUpArrow
    leftUpArrow
    lightningBolt
    line
    lineInv
    mathDivide
    mathEqual
    mathMinus
    mathMultiply
    mathNotEqual
    mathPlus
    moon
    nonIsoscelesTrapezoid
    noSmoking
    notchedRightArrow
    octagon
    parallelogram
    pentagon
    pie
    pieWedge
    plaque
    plaqueTabs
    plus
    quadArrow
    quadArrowCallout
    rect
    ribbon
    ribbon2
    rightArrow
    rightArrowCallout
    rightBrace
    rightBracket
    round1Rect
    round2DiagRect
    round2SameRect
    roundRect
    rtTriangle
    smileyFace
    snip1Rect
    snip2DiagRect
    snip2SameRect
    snipRoundRect
    squareTabs
    star10
    star12
    star16
    star24
    star32
    star4
    star5
    star6
    star7
    star8
    straightConnector1
    stripedRightArrow
    sun
    swooshArrow
    teardrop
    trapezoid
    triangle
    upArrow
    upArrowCallout
    upDownArrow
    upDownArrowCallout
    uturnArrow
    verticalScroll
    wave
    wedgeEllipseCallout
    wedgeRectCallout
    wedgeRoundRectCallout
"""
MS_SHAPES = {
    "rect": "clip-path: polygon(100% 100%,0% 100%,0% 0%,100% 0%);",
    "triangle": "clip-path: polygon(100% 100%,0% 100%,50% 0%);",
    "hexagon": "clip-path: polygon(93.30% 75%,50% 100%,6.70% 75%,6.70% 25%,50% 0%,93.30% 25%);",
    "diamond": "clip-path: polygon(100% 50%,50% 100%,0% 50%,50% 0.00%);",
    "roundRect": "clip-path: inset(0% 0% 0% 0% round 5%);",
    "circle": "clip-path: inset(0% 0% 0% 0% round 100%);",
    "rtTriangle": "clip-path: polygon(100% 100%,0% 100%,0% 0%,100% 100%);"
}


"""
    single - a single line
    dashDotStroked - a line with a series of alternating thin and thick strokes
    dashed - a dashed line
    dashSmallGap - a dashed line with small gaps
    dotDash - a line with alternating dots and dashes
    dotDotDash - a line with a repeating dot - dot - dash sequence
    dotted - a dotted line
    double - a double line
    doubleWave - a double wavy line
    inset - an inset set of lines
    nil - no border
    none - no border
    outset - an outset set of lines
    thick - a single line
    thickThinLargeGap - a thick line contained within a thin line with a large-sized intermediate gap
    thickThinMediumGap - a thick line contained within a thin line with a medium-sized intermediate gap
    thickThinSmallGap - a thick line contained within a thin line with a small intermediate gap
    thinThickLargeGap - a thin line contained within a thick line with a large-sized intermediate gap
    thinThickMediumGap - a thick line contained within a thin line with a medium-sized intermediate gap
    thinThickSmallGap - a thick line contained within a thin line with a small intermediate gap
    thinThickThinLargeGap - a thin-thick-thin line with a large gap
    thinThickThinMediumGap - a thin-thick-thin line with a medium gap
    thinThickThinSmallGap - a thin-thick-thin line with a small gap
    threeDEmboss - a three-staged gradient line, getting darker towards the paragraph
    threeDEngrave - a three-staged gradient like, getting darker away from the paragraph
    triple - a triple line
    wave - a wavy line
"""
MS_BORDER_STYLES = {
    'single': 'border-style: solid;',
    'dashDotStroked': 'border-style: dashed dotted solid;',
    'dashed': 'border-style: dashed;',
    'dashSmallGap': 'border-style: dashed;',
    'dotDash': 'border-style: dotted dashed;',
    'dotDotDash': 'border-style: dotted dotted dashed;',
    'dotted': 'border-style: dotted;',
    'double': 'border-style: double;',
    'doubleWave': 'border-style: double;',
    'inset': 'border-style: inset;',
    'nil': 'border-style: hidden;',
    'none': 'border-style: none;',
    'outset': 'border-style: outset;',
    'thick': 'border-style: solid;',
    'thickThinLargeGap': 'border-style: solid;',
    'thickThinMediumGap': 'border-style: solid;',
    'thickThinSmallGap': 'border-style: solid;',
    'thinThickLargeGap': 'border-style: solid;',
    'thinThickMediumGap': 'border-style: solid;',
    'thinThickSmallGap': 'border-style: solid;',
    'thinThickThinLargeGap': 'border-style: solid;',
    'thinThickThinMediumGap': 'border-style: solid;',
    'thinThickThinSmallGap': 'border-style: solid;',
    'threeDEmboss': 'border-style: outset;',
    'threeDEngrave': 'border-style: inset;',
    'triple': 'border-style: solid;',
    'wave': 'border-style: solid;',
}
