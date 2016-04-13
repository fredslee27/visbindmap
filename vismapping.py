#!/usr/bin/env python
# vim: set expandtab tabstop=4 :

import gtk
import sqlite3

import pprint
import pickle

import kblayout


BASENAME="factorio"
DEFAULT_DBNAME="cmds"


def crumb (x):
    pass


def BuildMenuBar (menubardesc):
    def BuildMenuItem (itemdesc):
        if itemdesc is None: return gtk.SeparatorMenuItem()  # separator
        retval = gtk.MenuItem(itemdesc[0])
        if callable(itemdesc[1]):  # leaf
            retval.connect("activate", itemdesc[1])
        elif hasattr(itemdesc[1], "__getslice__"):  # submenu
            retval.set_submenu(BuildMenu(itemdesc[1]))
        return retval
    def BuildMenu (menudesc, menu=None):
        menu = menu or gtk.Menu()
        map(menu.append, map(BuildMenuItem, menudesc))
        return menu
    return BuildMenu(menubardesc, gtk.MenuBar())


# SDL binding string:
# {type}/{number}/{value}
# type:
#  A = axis
#  B = button
#  H = hat
#  T = trackball
# number:
#  {0..}
# value:
#  0 = off/center
#  1 = pressed (implied if not found)
#  - = <0
#  + = >0
#e.g. "A/0/+", "B/3/1"


# Lookup table of control name to printable glyph representing the control.
class Glyphs:
    L2 = unichr(0x25e2)  # BLACK LOWER RIGHT TRIANGLE
    L1 = unichr(0x25ff)  # LOWER RIGHT TRIANGLE
    R2 = unichr(0x25e3)  # BLACK LOWER LEFT TRIANGLE
    R1 = unichr(0x25fa)  # LOWER LEFT TRIANGLE

    l = unichr(0x2190)  # LEFTWARDS ARROW
    d = unichr(0x2193)  # DOWNWARDS ARROW
    u = unichr(0x2191)  # UPWARDS ARROW
    r = unichr(0x2192)  # RIGHTWARDS ARROW

#    O = unichr(0x2460)  # CIRCLED DIGIT ONE
#    X = unichr(0x2461)  # CIRCLED DIGIT TWO
#    T = unichr(0x2462)  # CIRCLED DIGIT THREE
#    S = unichr(0x2463)  # CIRCLED DIGIT FOUR)

    _1 = unichr(0x2460)  # CIRCLED DIGIT ONE
    _2 = unichr(0x2461)  # CIRCLED DIGIT TWO
    _3 = unichr(0x2462)  # CIRCLED DIGIT THREE
    _4 = unichr(0x2463)  # CIRCLED DIGIT FOUR
    _5 = unichr(0x2464)  # CIRCLED DIGIT FIVE
    _6 = unichr(0x2465)  # CIRCLED DIGIT SIX
    _7 = unichr(0x2466)  # CIRCLED DIGIT SEVEN
    _8 = unichr(0x2467)  # CIRCLED DIGIT EIGHT
    _9 = unichr(0x2468)  # CIRCLED DIGIT NINE
    _0 = unichr(0x24EA)  # CIRCLED DIGIT ZERO

    L3 = unichr(0x24c1)  # CIRCLED LATIN CAPITAL LETTER L
#    Lx = unichr(0x21a6)  # RIGHTWARDS ARROW FROM BAR
#    Ly = unichr(0x21a7)  # DOWNWARDS ARROW FROM BAR
#    xL = unichr(0x21a4)  # LEFTWARDS ARROW FROM BAR
#    yL = unichr(0x21a5)  # UPWARDS ARROW FROM BAR
    Lx = unichr(0x27a1)  # BLACK RIGHTWARDS ARROW
    Ly = unichr(0x2b07)  # DOWNWARDS BLACK ARROW
    xL = unichr(0x2b05)  # LEFTWARDS BLACK ARROW
    yL = unichr(0x2b06)  # UPWARDS BLACK ARROW

    R3 = unichr(0x24c7)  # CIRCLED LATIN CAPITAL LETTER R
#    Rx = unichr(0x21a6)  # RIGHTWARDS ARROW FROM BAR
#    Ry = unichr(0x21a7)  # DOWNWARDS ARROW FROM BAR
#    xR = unichr(0x21a4)  # LEFTWARDS ARROW FROM BAR
#    yR = unichr(0x21a5)  # UPWARDS ARROW FROM BAR
    Rx = unichr(0x21e8)  # RIGHTWARDS WHITE ARROW
    Ry = unichr(0x21e9)  # DOWNWARDS WHITE ARROW
    xR = unichr(0x21e6)  # LEFTWARDS WHITE ARROW
    yR = unichr(0x21e7)  # UPWARDS WHITE ARROW

    SELECT = unichr(0x25ad)  # WHITE RECTANGLE
    START = unichr(0x25b7)  # WHITE RIGHT-POINTING TRIANGLE
#    HOME = '?'
#    HOME = unichr(0x25cf)  # BLACK CIRCLE
#    HOME = unichr(0x2693)  # ANCHOR
#    HOME = unichr(0x2699)  # GEAR
#    HOME = unichr(0x262e)  # PEACE SYMBOL
    HOME = unichr(0x2318)  # PLACE OF INTEREST SIGN
#    HOME = unichr(0x2302)  # HOUSE

#    yawL = unichr(0x21ba)  # ANTICLOCKWISE OPEN CIRCLE ARROW
#    yawR = unichr(0x21bb)  # CLOCKWISE OPEN CIRCLE ARROW
    yawL = unichr(0x21b6)  # ANTICLOCKWISE TOP SEMICIRCLE ARROW
    yawR = unichr(0x21b7)  # CLOCKWISE TOP SEMICIRCLE ARROW

#    fL = unichr(0x2b10)  # LEFTWARDS ARROW WITH TIP DOWNWARDS
#    fR = unichr(0x2b0e)  # RIGHTWARDS ARROW WITH TIP DOWNWARDS
    fL = unichr(0x21a4)  # LEFTWARDS ARROW FROM BAR
    fR = unichr(0x21a6)  # RIGHTWARDS ARROW FROM BAR

    #fU = unichr(0x21e1)  # UPWARDS DASHED ARROW
    #fD = unichr(0x21e3)  # DOWNWARDS DASHED ARROW
    fU = unichr(0x2299)  # CIRCLED DOT OPERATOR
    fD = unichr(0x00d7)  # MULTIPLICATION SIGN

#    fF = unichr(0x21de)  # UPWARDS ARROW WITH DOUBLE STROKE
#    fB = unichr(0x21df)  # DOWNWARDS ARROW WITH DOUBLE STROKE
    fF = unichr(0x21a5)  # UPWARDS ARROW FROM BAR
    fB = unichr(0x21a7)  # DOWNWARDS ARROW FROM BAR

    ## xb360, aliases
    TL = L1
    LT = L2
    TR = R1
    RT = R2
    LS = L3
    RS = R3
    A = unichr(0x24B6)  # CIRCLED LATIN CAPITAL LETTER A
    B = unichr(0x24B7)  # CIRCLED LATIN CAPITAL LETTER B
    X = unichr(0x24CD)  # CIRCLED LATIN CAPITAL LETTER X
    Y = unichr(0x24CE)  # CIRCLED LATIN CAPITAL LETTER Y
    BACK = unichr(0x25C1)  # WHITE LEFT-POINTING TRIANGLE

    ## Ouya
    O = unichr(0x24C4)  # CIRCLED LATIN CAPITAL LETTER O
    U = unichr(0x24CA)  # CIRCLED LATIN CAPITAL LETTER O

    ## N64
    tu = unichr(0x25b4) # BLACK UP-POINTING SMALL TRIANGLE
    td = unichr(0x25be) # BLACK DOWN-POINTING SMALL TRIANGLE
    tl = unichr(0x25c2) # BLACK LEFT-POINTING SMALL TRIANGLE
    tr = unichr(0x25b8) # BLACK RIGHT-POINTING SMALL TRIANGLE
    Z = unichr(0x24cf) # CIRCLED LATIN CAPITAL LETTER Z

    ## Steam
    LClick = L3
    RClick = R3
    #LG = 'b'
    #RG = 'd'
    LG = unichr(0x25d7)  # RIGHT HALF BLACK CIRCLE
    RG = unichr(0x25d6)  # LEFT HALF BLACK CIRCLE
    meta1 = BACK
    meta2 = HOME
    meta3 = START




# Persistant storage.
class Store (object):
    DEFAULT_FILENAME = BASENAME + ".cfg"

    def reset (self):
        self.binddata = []
#        for n in range(self._numlayers):
#            self.binddata.append({})
        for n in range(self._numlevels):
            self.binddata.append([])
            for m in range(self._numlayers):
                self.binddata[n].append({})

#    def __init__ (self, backingFileName=None):
    def __init__ (self, numlayers=8, backingFileName=None):
        # list of bindings, one binding per layer (typically 8 layers).
        # bindings are mapping SDL_binding => command
        self._numlayers = numlayers
        self._numlevels = numlayers
#        self.binddata = []
#        for n in range(numlayers):
#            self.binddata.append({})
        self.reset()
        self.fname = backingFileName
        if not backingFileName:
            self.fname = self.DEFAULT_FILENAME

    def load (self, fileobj=None):
        if fileobj is None:
            fileobj = open(self.fname, "rb")
        #fileobj = open(fname, "rb")
        self.binddata = pickle.load(fileobj)
        #fileobj.close()

    def save (self, fileobj=None):
        if fileobj is None:
            fileobj = open(self.fname, "wb")
        #fileobj = open(fname, "wb")
        pickle.dump(self.binddata, fileobj)
        #fileobj.close()




class PadLayouts:
    class ClassicPC:
        INP = {
          'Lx-': (Glyphs.xL, 'A/0/-'),
          'Lx+': (Glyphs.Lx, 'A/0/+'),
          'Ly-': (Glyphs.yL, 'A/1/-'),
          'Ly+': (Glyphs.Ly, 'A/1/+'),
          '_1': (Glyphs._1, "B/0"),
          '_2': (Glyphs._2, "B/1"),
          None: (' ', None),
          }
        MINI = [
          (0, 3) + INP['Ly-'],
          (1, 1) + INP['Lx-'],
          (1, 4) + INP['Lx+'],
          (2, 3) + INP['Ly+'],

          (0, 5) + INP[None],

          (1, 6) + INP['_1'],
          (1, 7) + INP['_2'],
          ]
        FULL = [
          (0, 3) + INP['Ly-'],
          (1, 1) + INP['Lx-'],
          (1, 4) + INP['Lx+'],
          (2, 3) + INP['Ly+'],

          (0, 5) + INP[None],

          (1, 6) + INP['_1'],
          (1, 7) + INP['_2'],
          ]


    class PS2:
        INP = {
          'Lx-': (Glyphs.xL, 'A/0/-'),
          'Lx+': (Glyphs.Lx, 'A/0/+'),
          'Ly-': (Glyphs.yL, 'A/1/-'),
          'Ly+': (Glyphs.Ly, 'A/1/+'),
          'Rx-': (Glyphs.xR, 'A/2/-'),
          'Rx+': (Glyphs.Rx, 'A/2/+'),
          'Ry-': (Glyphs.yR, 'A/3/-'),
          'Ry+': (Glyphs.Ry, 'A/3/+'),
          'u': (Glyphs.u, 'B/4'),
          'l': (Glyphs.l, 'B/7'),
          'r': (Glyphs.r, 'B/5'),
          'd': (Glyphs.d, 'B/6'),
          'SELECT': (Glyphs.SELECT, 'B/0'),
          'START': (Glyphs.START, 'B/3'),
          'O': (Glyphs._1, 'B/13'),
          'X': (Glyphs._2, 'B/14'),
          'T': (Glyphs._3, 'B/12'),
          'S': (Glyphs._4, 'B/15'),
          'L1': (Glyphs.L1, 'B/8'),
          'L2': (Glyphs.L2, 'B/10'),
          'L3': (Glyphs.L3, 'B/1'),
          'R1': (Glyphs.R1, 'B/9'),
          'R2': (Glyphs.R2, 'B/11'),
          'R3': (Glyphs.R3, 'B/2'),
          None: ('    ', None),
          }
        MINI = [
          (1, 3) + INP['L2'],
          (1, 9) + INP['R2'],
          (2, 2) + INP['L1'],
          (2, 10) + INP['R1'],

          (4, 2) + INP['u'],
          (5, 1) + INP['l'],
          (5, 3) + INP['r'],
          (6, 2) + INP['d'],

          (5, 5) + INP['SELECT'],
          (5, 7) + INP['START'],
          (6, 6) + INP[None],

          (4, 10) + INP['T'],
          (5, 9) + INP['S'],
          (5, 11) + INP['O'],
          (6, 10) + INP['X'],

          (8, 4) + INP['L3'],
          (8, 5) + INP['Lx+'],
          (9, 4) + INP['Ly+'],
          (8, 3) + INP['Lx-'],
          (7, 4) + INP['Ly-'],

          (8, 8) + INP['R3'],
          (8, 9) + INP['Rx+'],
          (9, 8) + INP['Ry+'],
          (8, 7) + INP['Rx-'],
          (7, 8) + INP['Ry-'],
          ]
        FULL = [
          (1, 2) + INP['L2'],
          (1, 4) + INP['R2'],
          (2, 1) + INP['L1'],
          (2, 5) + INP['R1'],

          (4, 1) + INP['u'],
          (5, 0) + INP['l'],
          (5, 2) + INP['r'],
          (6, 1) + INP['d'],

          (4, 5) + INP['T'],
          (5, 4) + INP['S'],
          (5, 6) + INP['O'],
          (6, 5) + INP['X'],

          (8, 2) + INP['SELECT'],
#          (8, 3, Glyphs.HOME, 'HOME'),
          (8, 3) + INP[None],
          (8, 4) + INP['START'],

          (11, 1) + INP['L3'],
          (11, 2) + INP['Lx+'],
          (12, 1) + INP['Ly+'],
          (11, 0) + INP['Lx-'],
          (10, 1) + INP['Ly-'],

          (11, 5) + INP['R3'],
          (11, 6) + INP['Rx+'],
          (12, 5) + INP['Ry+'],
          (11, 4) + INP['Rx-'],
          (10, 5) + INP['Ry-'],
          ]

    class PS3:
        INP = {
          'Lx-': (Glyphs.xL, 'A/0/-'),
          'Lx+': (Glyphs.Lx, 'A/0/+'),
          'Ly-': (Glyphs.yL, 'A/1/-'),
          'Ly+': (Glyphs.Ly, 'A/1/+'),
          'Rx-': (Glyphs.xR, 'A/2/-'),
          'Rx+': (Glyphs.Rx, 'A/2/+'),
          'Ry-': (Glyphs.yR, 'A/3/-'),
          'Ry+': (Glyphs.Ry, 'A/3/+'),
          'u': (Glyphs.u, 'B/4'),
          'l': (Glyphs.l, 'B/7'),
          'r': (Glyphs.r, 'B/5'),
          'd': (Glyphs.d, 'B/6'),
          'SELECT': (Glyphs.SELECT, 'B/0'),
          'HOME': (Glyphs.HOME, 'B/16'),
          'START': (Glyphs.START, 'B/3'),
          'O': (Glyphs._1, 'B/13'),
          'X': (Glyphs._2, 'B/14'),
          'T': (Glyphs._3, 'B/12'),
          'S': (Glyphs._4, 'B/15'),
          'L1': (Glyphs.L1, 'B/8'),
          'L2': (Glyphs.L2, 'B/10'),
          'L3': (Glyphs.L3, 'B/1'),
          'R1': (Glyphs.R1, 'B/9'),
          'R2': (Glyphs.R2, 'B/11'),
          'R3': (Glyphs.R3, 'B/2'),
          None: ('    ', None),
          }
        MINI = [
          (1, 3) + INP['L2'],
          (1, 9) + INP['R2'],
          (2, 2) + INP['L1'],
          (2, 10) + INP['R1'],

          (4, 2) + INP['u'],
          (5, 1) + INP['l'],
          (5, 3) + INP['r'],
          (6, 2) + INP['d'],

          (5, 5) + INP['SELECT'],
          (5, 7) + INP['START'],
          (6, 6) + INP['HOME'],

          (4, 10) + INP['T'],
          (5, 9) + INP['S'],
          (5, 11) + INP['O'],
          (6, 10) + INP['X'],

          (8, 4) + INP['L3'],
          (8, 5) + INP['Lx+'],
          (9, 4) + INP['Ly+'],
          (8, 3) + INP['Lx-'],
          (7, 4) + INP['Ly-'],

          (8, 8) + INP['R3'],
          (8, 9) + INP['Rx+'],
          (9, 8) + INP['Ry+'],
          (8, 7) + INP['Lx-'],
          (7, 8) + INP['Ly-'],
          ]
        FULL = [
          (1, 2) + INP['L2'],
          (1, 4) + INP['R2'],
          (2, 1) + INP['L1'],
          (2, 5) + INP['R1'],

          (4, 1) + INP['u'],
          (5, 0) + INP['l'],
          (5, 2) + INP['r'],
          (6, 1) + INP['d'],

          (4, 5) + INP['T'],
          (5, 4) + INP['S'],
          (5, 6) + INP['O'],
          (6, 5) + INP['X'],

          (8, 2) + INP['SELECT'],
          (8, 3) + INP['HOME'],
          (8, 4) + INP['START'],

          (11, 1) + INP['L3'],
          (11, 2) + INP['Lx+'],
          (12, 1) + INP['Ly+'],
          (11, 0) + INP['Lx-'],
          (10, 1) + INP['Ly-'],

          (11, 5) + INP['R3'],
          (11, 6) + INP['Rx+'],
          (12, 5) + INP['Ry+'],
          (11, 4) + INP['Rx-'],
          (10, 5) + INP['Ry-'],
          ]

    class PS3ff:
        MINI = [
          (1, 3, Glyphs.L2, 'L2'),
          (1, 9, Glyphs.R2, 'R2'),
          (2, 2, Glyphs.L1, 'L1'),
          (2, 10, Glyphs.R1, 'R1'),

          (4, 2, Glyphs.u, 'u'),
          (5, 1, Glyphs.l, 'l'),
          (5, 3, Glyphs.r, 'r'),
          (6, 2, Glyphs.d, 'd'),

          (5, 5, Glyphs.SELECT, 'SEL'),
          (5, 7, Glyphs.START, 'STA'),
          (6, 6, Glyphs.HOME, 'HOME'),

          (4, 10, Glyphs._3, 'T'),
          (5, 9, Glyphs._4, 'S'),
          (5, 11, Glyphs._1, 'O'),
          (6, 10, Glyphs._2, 'X'),

          (8, 4, Glyphs.L3, 'L3'),
          (8, 5, Glyphs.Lx, 'Lx+'),
          (9, 4, Glyphs.Ly, 'Ly+'),
          (8, 3, Glyphs.xL, 'Lx-'),
          (7, 4, Glyphs.yL, 'Ly-'),

          (8, 8, Glyphs.R3, "R3"),
          (8, 9, Glyphs.Rx, "Rx+"),
          (9, 8, Glyphs.Ry, "Ry+"),
          (8, 7, Glyphs.xR, "Rx-"),
          (7, 8, Glyphs.yR, "Ry-"),

          (1, 1, Glyphs.yawL, 'rL'),
          (1, 6, Glyphs.fF, 'fF'),
          (1, 11, Glyphs.yawR, 'rR'),
          (3, 5, Glyphs.fU, 'fU'),
          (3, 7, Glyphs.fD, 'fD'),
          (9, 6, Glyphs.fB, 'fB'),
          (3, 1, Glyphs.fL, 'fL'),
          (3, 11, Glyphs.fR, 'fR'),
          ]
        FULL = [
          (1, 2, Glyphs.L2, 'L2'),
          (1, 4, Glyphs.R2, 'R2'),
          (2, 1, Glyphs.L1, 'L1'),
          (2, 5, Glyphs.R1, 'R1'),

          (4, 1, Glyphs.u, 'u'),
          (5, 0, Glyphs.l, 'l'),
          (5, 2, Glyphs.r, 'r'),
          (6, 1, Glyphs.d, 'd'),

          (4, 5, Glyphs._3, 'T'),
          (5, 4, Glyphs._4, 'S'),
          (5, 6, Glyphs._1, 'O'),
          (6, 5, Glyphs._2, 'X'),

          (8, 2, Glyphs.SELECT, 'SEL'),
          (8, 3, Glyphs.HOME, 'HOME'),
          (8, 4, Glyphs.START, 'STA'),

          (11, 1, Glyphs.L3, 'L3'),
          (11, 2, Glyphs.Lx, 'Lx+'),
          (12, 1, Glyphs.Ly, 'Ly+'),
          (11, 0, Glyphs.xL, 'Lx-'),
          (10, 1, Glyphs.yL, 'Ly-'),

          (11, 5, Glyphs.R3, "R3"),
          (11, 6, Glyphs.Rx, "Rx+"),
          (12, 5, Glyphs.Ry, "Ry+"),
          (11, 4, Glyphs.xR, "Rx-"),
          (10, 5, Glyphs.yR, "Ry-"),

          (1, 0, Glyphs.yawL, 'rL'),
          (1, 6, Glyphs.yawR, 'rR'),
          (1, 3, Glyphs.fF, 'fF'),
          (8, 0, Glyphs.fL, 'fL'),
          (8, 6, Glyphs.fR, 'fR'),
          (7, 3, Glyphs.fU, 'fU'),
          (9, 3, Glyphs.fD, 'fD'),
          (12, 3, Glyphs.fB, 'fB'),
          ]


    class XB360:
        INP = {
          'LT': (Glyphs.LT, 'A/2/+'),
          'RT': (Glyphs.RT, 'A/5/+'),
          'TL': (Glyphs.TL, 'B/4'),
          'TR': (Glyphs.TR, 'B/5'),

          'LS': (Glyphs.LS, 'B/9'),
          'Lx-': (Glyphs.xL, 'A/0/-'),
          'Lx+': (Glyphs.Lx, 'A/0/+'),
          'Ly-': (Glyphs.yL, 'A/1/-'),
          'Ly+': (Glyphs.Ly, 'A/1/+'),

          'A': (Glyphs.A, 'B/0'),
          'B': (Glyphs.B, 'B/1'),
          'X': (Glyphs.X, 'B/2'),
          'Y': (Glyphs.Y, 'B/3'),

          'BACK': (Glyphs.BACK, 'B/6'),
          'HOME': (Glyphs.HOME, 'B/15'),
          'START': (Glyphs.START, 'B/7'),

          'l': (Glyphs.l, 'A/5/-'),
          'r': (Glyphs.r, 'A/5/+'),
          'u': (Glyphs.u, 'A/6/-'),
          'd': (Glyphs.d, 'A/6/+'),

          'RS': (Glyphs.R3, 'B/10'),
          'Rx-': (Glyphs.xR, 'A/3/-'),
          'Rx+': (Glyphs.Rx, 'A/3/+'),
          'Ry-': (Glyphs.yR, 'A/4/-'),
          'Ry+': (Glyphs.Ry, 'A/4/+'),
          }
        MINI = [
          (1, 3) + INP['LT'],
          (1, 7) + INP['RT'],
          (2, 2) + INP['TL'],
          (2, 8) + INP['TR'],

          (3, 2) + INP['Ly-'],
          (4, 1) + INP['Lx-'],
          (4, 2) + INP['LS'],
          (4, 3) + INP['Lx+'],
          (5, 2) + INP['Ly+'],

          (3, 8) + INP['Y'],
          (4, 7) + INP['X'],
          (4, 9) + INP['B'],
          (5, 8) + INP['A'],

          (5, 4) + INP['BACK'],
          (5, 5) + INP['HOME'],
          (5, 6) + INP['START'],

          (7, 3) + INP['u'],
          (8, 2) + INP['l'],
          (8, 4) + INP['r'],
          (9, 3) + INP['d'],

          (7, 7) + INP['Ly-'],
          (8, 6) + INP['Rx-'],
          (8, 7) + INP['RS'],
          (8, 8) + INP['Rx+'],
          (9, 7) + INP['Ry+'],
          ]
        FULL = [
          (0, 3) + INP['LT'],
          (0, 5) + INP['RT'],
          (1, 2) + INP['TL'],
          (1, 6) + INP['TR'],

          (2, 2) + INP['Ly-'],
          (3, 1) + INP['Lx-'],
          (3, 2) + INP['LS'],
          (3, 3) + INP['Lx+'],
          (4, 2) + INP['Ly+'],

          (2, 6) + INP['Y'],
          (3, 5) + INP['X'],
          (3, 7) + INP['B'],
          (4, 6) + INP['A'],

          (8, 3) + INP['BACK'],
          (8, 4) + INP['HOME'],
          (8, 5) + INP['START'],

          (10, 2) + INP['u'],
          (11, 1) + INP['l'],
          (11, 3) + INP['r'],
          (12, 2) + INP['d'],

          (10, 6) + INP['Ry-'],
          (11, 5) + INP['Rx-'],
          (11, 6) + INP['RS'],
          (11, 7) + INP['Rx+'],
          (12, 6) + INP['Ry+'],
          ]

    class N64:
        INP = {
          'L': (Glyphs.L1, 'B/9'),
          'R': (Glyphs.R1, 'B/10'),

          'u': (Glyphs.u, 'B/4'),
          'r': (Glyphs.r, 'B/5'),
          'd': (Glyphs.d, 'B/6'),
          'l': (Glyphs.l, 'B/7'),

          'x+': (Glyphs.Lx, 'A/0/+'),
          'x-': (Glyphs.xL, 'A/0/-'),
          'y+': (Glyphs.Ly, 'A/1/+'),
          'y-': (Glyphs.yL, 'A/1/-'),

          'Cu': (Glyphs.tu, 'B/12'),
          'Cr': (Glyphs.tr, 'B/13'),
          'Cd': (Glyphs.td, 'B/14'),
          'Cl': (Glyphs.tl, 'B/15'),

          'A': (Glyphs.A, 'B/1'),
          'B': (Glyphs.B, 'B/2'),
          'Z': (Glyphs.Z, 'B/3'),
          'START': (Glyphs.START, 'B/0'),

          None: ('    ', None),
          }
        MINI = [
          (1, 1) + INP['L'],
          (1, 8) + INP['R'],

          (2, 1) + INP['u'],
          (3, 0) + INP['l'],
          (3, 2) + INP['r'],
          (4, 1) + INP['d'],

          (1, 3) + INP[None],
          (4, 4) + INP['START'],
          (1, 5) + INP[None],

          (2, 8) + INP['Cu'],
          (3, 7) + INP['Cl'],
          (3, 9) + INP['Cr'],
          (4, 8) + INP['Cd'],

          (4, 6) + INP['B'],
          (5, 7) + INP['A'],

          (5, 4) + INP['y-'],
          (6, 3) + INP['x-'],
          (6, 4) + INP['Z'],
          (6, 5) + INP['x+'],
          (7, 4) + INP['y+'],
          ]
        FULL = [
          (1, 1) + INP['L'],
          (1, 5) + INP['R'],

          (2, 1) + INP['u'],
          (3, 0) + INP['l'],
          (3, 2) + INP['r'],
          (4, 1) + INP['d'],

          (4, 3) + INP['START'],

          (2, 5) + INP['Cu'],
          (3, 4) + INP['Cl'],
          (3, 6) + INP['Cr'],
          (4, 5) + INP['Cd'],

          (5, 4) + INP['B'],
          (6, 5) + INP['A'],

          (10, 3) + INP['y-'],
          (11, 2) + INP['x-'],
          (6, 3) + INP['Z'],
          (11, 4) + INP['x+'],
          (12, 3) + INP['y+'],
          ]

    class Steam00:
        INP = {
          'L1': (Glyphs.L1, 'B/0'),
          'L2': (Glyphs.L2, 'B/0'),
          'L3': (Glyphs.LG, 'B/0'),

          'R1': (Glyphs.R1, 'B/0'),
          'R2': (Glyphs.R2, 'B/0'),
          'R3': (Glyphs.RG, 'B/0'),

          'Lx-': (Glyphs.xL, 'B/0'),
          'Lx+': (Glyphs.Lx, 'B/0'),
          'Ly-': (Glyphs.yL, 'B/0'),
          'Ly+': (Glyphs.Ly, 'B/0'),
          'LP': (Glyphs.LClick, 'B/0'),

          'Rx-': (Glyphs.xR, 'B/0'),
          'Rx+': (Glyphs.Rx, 'B/0'),
          'Ry-': (Glyphs.yR, 'B/0'),
          'Ry+': (Glyphs.Ry, 'B/0'),
          'RP': (Glyphs.RClick, 'B/0'),

          'A': (Glyphs.A, 'B/0'),
          'B': (Glyphs.B, 'B/0'),
          'X': (Glyphs.X, 'B/0'),
          'Y': (Glyphs.Y, 'B/0'),

          'meta1': (Glyphs.meta1, 'B/0'),
          'meta2': (Glyphs.meta2, 'B/0'),
          'meta3': (Glyphs.meta3, 'B/0'),

          'Q1': (Glyphs._1, 'B/0'),
          'Q2': (Glyphs._2, 'B/0'),
          'Q3': (Glyphs._3, 'B/0'),
          'Q4': (Glyphs._4, 'B/0'),
          }
        MINI = [
          (0, 2) + INP['L2'],
          (1, 1) + INP['L1'],

          (2, 1) + INP['Ly-'],
          (3, 0) + INP['Lx-'],
          (3, 1) + INP['LP'],
          (3, 2) + INP['Lx+'],
          (4, 1) + INP['Ly+'],

          (2, 2) + INP['Y'],
          (4, 2) + INP['X'],

          (5, 0) + INP['L3'],


          (8, 2) + INP['meta1'],
          (8, 3) + INP['meta2'],
          (8, 4) + INP['meta3'],


          (5, 6) + INP['R3'],

          (2, 4) + INP['B'],
          (4, 4) + INP['A'],

          (2, 5) + INP['Ry-'],
          (3, 4) + INP['Rx-'],
          (3, 5) + INP['RP'],
          (3, 6) + INP['Rx+'],
          (4, 5) + INP['Ry+'],

          (0, 4) + INP['R2'],
          (1, 5) + INP['R1'],

          (2, 3) + INP['Q1'],
          (3, 3) + INP['Q2'],
          (4, 3) + INP['Q3'],
          (5, 3) + INP['Q4'],
          ]
        FULL = MINI

    class SteamCES2014:
        INP = {
          'L1': (Glyphs.L1, 'B/0'),
          'L2': (Glyphs.L2, 'B/0'),
          'L3': (Glyphs.LG, 'B/0'),

          'R1': (Glyphs.R1, 'B/0'),
          'R2': (Glyphs.R2, 'B/0'),
          'R3': (Glyphs.RG, 'B/0'),

          'Lx-': (Glyphs.xL, 'B/0'),
          'Lx+': (Glyphs.Lx, 'B/0'),
          'Ly-': (Glyphs.yL, 'B/0'),
          'Ly+': (Glyphs.Ly, 'B/0'),
          'LP': (Glyphs.LClick, 'B/0'),

          'Rx-': (Glyphs.xR, 'B/0'),
          'Rx+': (Glyphs.Rx, 'B/0'),
          'Ry-': (Glyphs.yR, 'B/0'),
          'Ry+': (Glyphs.Ry, 'B/0'),
          'RP': (Glyphs.RClick, 'B/0'),

          'A': (Glyphs.A, 'B/0'),
          'B': (Glyphs.B, 'B/0'),
          'X': (Glyphs.X, 'B/0'),
          'Y': (Glyphs.Y, 'B/0'),

          'meta1': (Glyphs.meta1, 'B/0'),
          'meta2': (Glyphs.meta2, 'B/0'),
          'meta3': (Glyphs.meta3, 'B/0'),

          'u': (Glyphs.u, 'B/0'),
          'd': (Glyphs.d, 'B/0'),
          'l': (Glyphs.l, 'B/0'),
          'r': (Glyphs.r, 'B/0'),
          }
        MINI = [
              (0, 2) + INP['L2'], (0, 6) + INP['R2'],
          (1, 1) + INP['L1'],         (1, 7) + INP['R1'],

                                (2, 1) + INP['Ly-'],
          (3, 0) + INP['Lx-'],  (3, 1) + INP['LP'], (3, 2) + INP['Lx+'],
                                (4, 1) + INP['Ly+'],

          (6, 0) + INP['L3'],

                                (4, 2) + INP['u'],
          (5, 1) + INP['l'],                        (5, 3) + INP['r'],
                                (6, 2) + INP['d'],

          (3, 3) + INP['meta1'], (3, 4) + INP['meta2'], (3, 5) + INP['meta3'],

                                (4, 6) + INP['Y'],
          (5, 5) + INP['X'],                        (5, 7) + INP['B'],
                                (6, 6) + INP['A'],

                                                        (6, 8) + INP['R3'],

                                (2, 7) + INP['Ry-'],
          (3, 6) + INP['Rx-'],  (3, 7) + INP['RP'], (3, 8) + INP['Rx+'],
                                (4, 7) + INP['Ry+'],
          ]
        FULL = [
              (0, 2) + INP['L2'], (0, 4) + INP['R2'],
          (1, 1) + INP['L1'],         (1, 5) + INP['R1'],

                                (2, 1) + INP['Ly-'],
          (3, 0) + INP['Lx-'],  (3, 1) + INP['LP'], (3, 2) + INP['Lx+'],
                                (4, 1) + INP['Ly+'],

          (5, 0) + INP['L3'],

                                (10, 1) + INP['u'],
          (11, 0) + INP['l'],                       (11, 2) + INP['r'],
                                (12, 1) + INP['d'],

          (8, 2) + INP['meta1'], (8, 3) + INP['meta2'], (8, 4) + INP['meta3'],

                                (10, 5) + INP['Y'],
          (11, 4) + INP['X'],                       (11, 6) + INP['B'],
                                (12, 5) + INP['A'],

                                                        (5, 6) + INP['R3'],

                                (2, 5) + INP['Ry-'],
          (3, 4) + INP['Rx-'],  (3, 5) + INP['RP'], (3, 6) + INP['Rx+'],
                                (4, 5) + INP['Ry+'],
          ]




# Graphical representation of the game controller pad.

class PadGlyph (gtk.HBox):
    # (row, column, text, name)

    def __init__ (self, data=None):
        gtk.HBox.__init__(self, 10, 12)
        self.clicking = 0
        self.frame = gtk.Frame("Vispad")
        table = gtk.Table()
        if data is not None:
            self.LAYOUT = data.MINI
        for elt in self.LAYOUT:
            (row, col, txt, name) = elt
            lbl = gtk.Label("%s" % txt)
            #lbl = gtk.Button(txt)
            #lbl.set_relief(gtk.RELIEF_NONE)
            #lbl.connect("clicked", self.on_click)
            #lbl.set_border_width(0)
            #padglyph = lbl

            evbox = gtk.EventBox()
            evbox.clicking = 0
            evbox.set_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.LEAVE_NOTIFY_MASK)
            self.evbox = evbox
            evbox.add(lbl)
            #evbox.connect("realize", self.on_realize)
            #evbox.realize()
            evbox.connect("button_press_event", self.on_button,  1, name)
            evbox.connect("button_release_event", self.on_button,  2, name)
            evbox.connect("leave_notify_event", self.on_leave)
            #padglyph.connect("clicked", self.on_click)
            padglyph = evbox

            table.attach(padglyph, col, col+1, row, row+1, xoptions=0, yoptions=0)


        self.table = table
        self.frame.add(self.table)
        self.add(self.frame)

#    def on_realize (self, w, *args):
#        print("realized %r" % w)

    def on_click (self, w, *args):
        print("clicked.")

    def on_button (self, w, evt, *args):
        self.clicking |= args[0]
        if self.clicking == 0x3:
            self.on_click(w, *args)
            self.clicking = 0

    def on_leave (self, w, evt, *args):
        #print("pointer leave")
        self.clicking = 0


class PadGlyph_PS3 (PadGlyph):
    LAYOUT=PadLayouts.PS3.MINI

class PadGlyph_PS2 (PadGlyph):
    LAYOUT=PadLayouts.PS2.MINI

class PadGlyph_ClassicPC (PadGlyph):
    LAYOUT=PadLayouts.ClassicPC.MINI

class PadGlyph_XB360 (PadGlyph):
    LAYOUT=PadLayouts.XB360.MINI




class Commands (object):
    """Database of game commands."""
    def __init__ (self, dbname):
        self.dbname = dbname
#        self.db = [(0, "", "", "(none)", None)]
        # Open DB.
        self.conn = sqlite3.connect(dbname)
        # Pull relevant rows.
        cursor = self.conn.cursor()
        cursor.execute('''SELECT id,layer,grp,cmd,label,hint FROM cmd;''')
#        for row in cursor.fetchall():
#            (cmdid, grp, cmd, label, hint) = row
#            self.db.append((cmdid, grp, cmd, label, hint))
#        print("conn = %r" % self.conn)

    def get_modes (self):
        cursor = self.conn.cursor()
        rows = cursor.execute('''SELECT name FROM modes ORDER BY id;''')
        modenames = []
        for row in rows:
            modename = row[0];
            modenames.append(modename)
        return modenames

    def get_groups (self):
        cursor = self.conn.cursor()
        rows = cursor.execute('''SELECT grp FROM cmd GROUP BY grp ORDER BY id;''');
        grpnames = []
        for row in rows:
            grpname = row[0]
            grpnames.append(grpname)
        return grpnames

    groups = property(get_groups)

    def get_by_id (self, val):
        # TODO: look through tree model instead?
        if val is None:
            print("[None]=>None...")
            return [ None, 0x1f, "", "", "", "" ]

        cursor = self.conn.cursor()
        #cursor.execute('''SELECT cmd FROM cmd WHERE id=? LIMIT 1;''', str(val))
        cursor.execute('''SELECT id,layer,grp,cmd,label,hint FROM cmd WHERE id=? LIMIT 1;''', (str(val),))
        result = cursor.fetchone()
        if result:
            if not result[4]:
                result = result[:4] + (result[3],) + result[5:]
            return result
        else:
            return None

    def get_count (self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT COUNT(*) FROM cmd;''')
        return cursor.fetchone()[0]

    def find (self, cmdname):
        if cmdname is None:
            print("find(None) => None")
            return None

        cursor = self.conn.cursor()
        cursor.execute("""SELECT id FROM cmd WHERE cmd=? LIMIT 1;""", (str(cmdname),))
        retval = cursor.fetchone()
        if retval:
            return retval[0]
        else:
            return -1

    def get (self, cmdname, altval):
        idx = self.find(cmdname)
        if (idx < 0):
            return altval
        return self.get_by_id(idx)

    def __getitem__ (self, idx):
        return self.get_by_id(idx)

    def __len__ (self):
        return self.get_count()

    def __iter__ (self):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT id,layer,grp,cmd,label,hint FROM cmd;""")
        row = cursor.fetchone()
        while row:
            yield row
            row = cursor.fetchone()
        raise StopIteration()

    def build_treestore (self, store):
        # The unbind item.
        store.append(None, (0, "", "(unbind)", "", self))
#            treeiter = store.append(grpiter, (cmdid, cmd, desc, hint, self))
        # Build all groups.
        groupheads = {}

        def make_group (grpname):
            if '/' in grpname:
                splitpt = grpname.rindex('/')
                prefix = grpname[:splitpt]
                suffix = grpname[splitpt+1:]
                make_group(prefix)
                parentiter = groupheads[prefix]
                #treeiter = store.append(parentiter, (0, "", grp, ""))
                treeiter = store.append(parentiter, (0, "", suffix, "", self))
                groupheads[grpname] = treeiter
            else:
                if not groupheads.has_key(grpname):
                    treeiter = store.append(None, (0, "", grp, "", self))
                    groupheads[grpname] = treeiter

        for grp in self.groups:
#            treeiter = store.append(None, (0, "", grp, ""))
#            groupheads[grp] = treeiter
            make_group(grp)

        for cmdinfo in self.__iter__():
            (cmdid, layer, grp, cmd, desc, hint) = cmdinfo
            grpiter = groupheads[grp]
            if not desc:
                desc = cmd
            treeiter = store.append(grpiter, (cmdid, cmd, desc, hint, self))




class VisCmds (gtk.VBox):
    """Visual presentation of commands: a tree of group and the commands."""
    DEFAULT_DATASOURCE = DEFAULT_DBNAME + ".sqlite3"

    def __init__ (self, datasrc=None):
        gtk.VBox.__init__(self)
        # id, cmd, display, hint

        self.cmdlist = gtk.TreeStore(int, str, str, str, object)

        if datasrc is None:
            datasrc = self.DEFAULT_DATASOURCE
        self.cmds = Commands(datasrc)
        self.cmds.build_treestore(self.cmdlist)

        self.entry = gtk.TreeView(self.cmdlist)
        self.entry.drag_source_set(gtk.gdk.BUTTON1_MASK, [ ("bind", gtk.TARGET_SAME_APP, 1), ], gtk.gdk.ACTION_LINK)
        self.entry.drag_source_set(gtk.gdk.BUTTON1_MASK, [ ("bindid", gtk.TARGET_SAME_APP, 1), ], gtk.gdk.ACTION_LINK)
        self.entry.connect("drag-data-get", self.on_drag_data_get)
        self.cell0 = gtk.CellRendererText()
        self.col0 = gtk.TreeViewColumn("command", self.cell0, text=2)
        self.entry.append_column(self.col0)
#        self.add(gtk.Label("VisCmds"))

        #self.add(self.entry)
        self.entrywin = gtk.ScrolledWindow()
        self.entrywin.add_with_viewport(self.entry)
        self.add(self.entrywin)
        self.set_size_request(160, 100)

    def on_drag_data_get (self, w, ctx, sel, info, time, *args):
#        print("on-drag-data-get:", w, ctx, sel, info, time)
#        print("sel.selection == %r" % sel.selection)
#        print("sel.target == %r" % sel.target)
#        print("sel.type == %r" % sel.type)
#        print("sel.data == %r" % sel.data)
        if sel.target == "bind":
#            print("+++ target is bind")
            srcw = ctx.get_source_widget()
            treesel = srcw.get_selection()
            (treemdl, treeiter) = treesel.get_selected()

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                #sel.data = None
                sel.set_text("", 0)
#                ctx.drop_finish(False, 0)
                return
            # Get the command to bind.
            val = treemdl.get_value(treeiter, 1)

#            print("using val=%r" % val)
            #sel.set_text(val, len(val))
            sel.set("STRING", 8, val)  # 8 bits per unit.
        elif sel.target == "bindid":
#            print("+++ target is bind")
            srcw = ctx.get_source_widget()
            treesel = srcw.get_selection()
            (treemdl, treeiter) = treesel.get_selected()

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                #sel.data = None
                sel.set_text("", 0)
#                ctx.drop_finish(False, 0)
                return
            # Get the command to bind.
            val = treemdl.get_value(treeiter, 0)

#            print("using val=%r" % val)
            #sel.set_text(val, len(val))
            sel.set("STRING", 8, str(val))  # 8 bits per unit.



# Graphically lay out bindings meanings.
class VisBind (gtk.VBox):
    """Graphical layout of bindings; "central pane" of main window."""
    #LAYOUT = PadLayouts.PS3.FULL
    LAYOUT = PadLayouts.ClassicPC.FULL
    #LAYOUT = PadLayouts.XB360.FULL

    @property
    def bindlevels (self):
        return self.store.binddata

    @property
    def bindlayers (self):
        return self.store.binddata[self.levelnum]

    @property
    def bindentry (self):
        return self.kbl.keytops

    def reset (self):
        #self.store.reset()
        self.levelnum = 0

        self.bindmap = self.bindlayers[0]  # active bindmap.

        self.layernum = 0  # current layer number.
        self.load_bindmap(self.layernum)


    def __init__ (self, store, paddata=None, cmds=None):
        gtk.VBox.__init__(self)

        self.store = store
        self.cmds = cmds

        self.shiftrow = self.InpSelectLevel()
        self.pack_start(self.shiftrow)

        self.moderow = self.InpSelectMode()
        self.pack_start(self.moderow)

        # grid/tablular layout of inpbind+bindcmd
        self.kbl = kblayout.KblayoutWidget()
        self.kbl.connect("key-selected", self.on_key_selected)
        self.kbl.connect("bind-changed", self.on_bind_changed)
        self.kbl.connect("bindid-changed", self.on_bindid_changed)
        self.kbl.connect("layout-changed", self.on_layout_changed)
#        self.bindentry = self.kbl.keytops

        #self.add(self.kbl)
        self.pack_start(self.kbl, expand=False, fill=False)

        self.reset()

    def on_key_selected (self, w, ksym, *args):
        print("key-selected: %s" % ksym)

    def on_layout_changed (self, w, layoutname, *args):
        self.relabel_keys(self.levelnum)
        self.load_bindmap(self.layernum)

    def on_bind_changed (self, w, keytop, *args):
        #print("VisBind.bind-changed: %r" % keytop)
        #self.bindmap[keytop.ksym] = keytop.bind
        pass

    def on_bindid_changed (self, w, keytop, *args):
        #print("VisBind.bindid-changed: %r" % keytop)
        cmdinfo = self.cmds[keytop.bindid]
        if cmdinfo:
            self.bind_cmd(keytop.ksym, cmdinfo)
        else:
            cmdtext = None
            self.unbind_cmd(keytop.ksym)
        pass

    def InpSelectMode (self):
        moderow = gtk.HBox()
        modebtns = gtk.HButtonBox()

        moderow.lbl = gtk.Label("MODE:")
        # "Select Layer" radio buttons.
        #modes = [ "(GLOBAL)", "Game", "Inventory", "Crafting", "Editor" ]
        modes = [ "*GLOBAL" ] + self.cmds.get_modes()
            
        moderow.btns = []  # private data.
        #moderow.pack_start(moderow.lbl, expand=False)
        for modeid in range(0, len(modes)):
            grp = moderow.btns and moderow.btns[0] or None    # is group leader or member.
            lbl = modes[modeid]
            btn = gtk.RadioButton(grp, lbl)  # create element.
            btn.layernum = modeid  # private data
            btn.connect('clicked', self.on_mode_toggle)  # react
            modebtns.add(btn)  # GUI
            moderow.btns.append(btn)  # internal storage.
        moderow.pack_start(modebtns, expand=False)

        #return moderow
        modebox = gtk.Frame("MODE")
        modebox.add(moderow)
        return modebox

    def InpSelectLevel (self):
        shiftbox = gtk.Frame("LEVEL")
        shiftrow = gtk.HBox()
        shiftbtns = gtk.HButtonBox()
        MAX_SHIFTER = 3
        btns = []
        #shiftrow.lbl = gtk.Label("LEVEL")
        #shiftrow.pack_start(shiftrow.lbl, expand=False)
        for lvlnum in xrange(0, 8):
            sh = []
            for b in xrange(0, 8):
                if (lvlnum & (1 << b)):
                    sh.append("^%s" % (b+1))
            if sh:
                lbl = "%d " % lvlnum + ("(" + " + ".join(sh) + ")")
            else:
                lbl = "base"
            grp = btns and btns[0] or None
            btn = gtk.RadioButton(grp, lbl)
            btn.levelnum = lvlnum
            btn.connect('clicked', self.on_shifter_toggle)  # react
            btns.append(btn)
            shiftbtns.add(btn)
        shiftrow.btns = btns
        shiftrow.pack_start(shiftbtns, expand=True)
        #return shiftrow
        shiftbox.add(shiftrow)
        return shiftbox

    def save_bindmap (self, bindmask):
        crumb("\f")
        crumb("save_bindmap -- nop")
        pass

    def load_bindmap (self, layernum):
        """Load binding map: update visual keys with bindings from given layer."""
        srcmap = self.bindlayers[layernum]
        self.layernum = layernum
        self.bindmap = srcmap
        for k in self.bindentry.keys():
            w = self.bindentry[k]
            val = self.bindmap.get(k, None)
            if val:
                w.bind = val
            elif self.bindlayers[0].get(k, None):
                w.bind = "<i>%s</i>" % self.bindlayers[0][k]
            else:
                del w.bind
        crumb("Loaded current = %r" % self.bindmap)
        crumb("of full %r" % self.bindlayers)
        return

    def relabel_keys (self, levelnum):
        for k in self.bindentry.keys():
            w = self.bindentry[k]
            if levelnum:
                lbl = "%s^%d" % (w.label, levelnum)
            else:
                lbl = w.label
            #w.inp_lbl.set_text(lbl)
            w.set_keytop(lbl)

    def on_mode_toggle (self, w, *args):
        self.layernum = w.layernum
        self.load_bindmap(w.layernum)
        return

    def on_shifter_toggle (self, w, *args):
        self.levelnum = w.levelnum
        self.load_bindmap(self.layernum)
        self.relabel_keys(self.levelnum)
        return

    def bind_cmd (self, ksym, cmdinfo):
        cmd = cmdinfo[4]
#        crumb("bind_cmd / ksym=%r / cmd=%r" % (ksym, cmd))
        crumb("cmdinfo = %r" % (cmdinfo,))
        if cmdinfo:
            layernum = cmdinfo[1]
            self.bindlayers[layernum][ksym] = cmd
            if self.layernum != layernum:
                self.bindentry[ksym].bind = "<i>%s</i>" % cmd
            else:
                self.bindentry[ksym].bind = cmd
        return

    def unbind_cmd (self, ksym):
        self.bindlayers[self.layernum][ksym] = None
        del self.bindentry[ksym].bind




class VisMapperWindow (gtk.Window):
    """Main window, majority of state information."""
    def reset (self):
        self.bindpad.reset()

    def __init__ (self, parent=None):
        self.app = parent
        gtk.Window.__init__(self)
        self.set_title("Vismapper")

        self.saveuri = None

        self.store = self.app.store

        self.panes = gtk.VBox()
        self.add(self.panes)

        self.spans = gtk.HBox()

        self.padpane = gtk.VBox()

        #self.padlayout = PadLayouts.ClassicPC
        #self.padlayout = PadLayouts.PS2
        #self.padlayout = PadLayouts.XB360
        #self.padlayout = PadLayouts.N64
        #self.padlayout = PadLayouts.SteamCES2014
        self.padlayout = PadLayouts.PS3

        self.padrow = gtk.HBox()
        #self.vispad = PadGlyph_PS3()
        #self.vispad = PadGlyph_ClassicPC()
        self.vispad = PadGlyph(self.padlayout)
        self.padrow.pack_start(gtk.Label(), expand=True)
        self.padrow.pack_start(self.vispad, expand=False)
        self.padrow.pack_start(gtk.Label(), expand=True)
        self.padpane.pack_start(self.padrow, expand=False)

        self.connect("delete-event", self.on_quit)

        self.cmdcol = VisCmds()

        self.bindrow = gtk.VBox()
        self.bindpad = VisBind(self.store, self.padlayout, self.cmdcol.cmds)
        self.bindrow.pack_start(self.bindpad)
        self.padpane.pack_start(self.bindrow)

        self.spans = gtk.HPaned()
        self.spans.add(self.padpane)
        self.spans.add(self.cmdcol)

        self.menubar = self.MakeMenubar()
        self.statusbar = gtk.Statusbar()
        self.panes.pack_start(self.menubar, expand=False, fill=True)
        self.panes.pack_start(self.spans, expand=False)

        if 1:
            self.debugrow = gtk.HBox()
            self.debugbuf = gtk.TextBuffer()
            self.debugwin = gtk.TextView(self.debugbuf)
            self.debugrow.pack_start(self.debugwin, expand=True, fill=True)
            debugpane = gtk.ScrolledWindow()
            debugpane.add_with_viewport(self.debugrow)
            #self.panes.pack_start(self.debugrow, expand=True, fill=True)
            self.panes.pack_start(debugpane, expand=True, fill=True)
            self.debugbuf.insert_at_cursor("Debug")
            self.debugbuf.insert_at_cursor(" ready:")
            self.debugbuf.insert_at_cursor("\n")
            def debugcrumb (x):
                if x == "\f":
                    self.debugbuf.delete(self.debugbuf.get_start_iter(), self.debugbuf.get_end_iter())
                else:
                    self.debugbuf.insert_at_cursor(x + "\n")
            globals()['crumb'] = debugcrumb

        self.panes.pack_start(self.statusbar, expand=False)

    def MakeMenubar (self):
        menu_desc = [
          ('_File', [
            ('_New', self.on_new),
            ('_Open', self.on_open),
            ('_Save', self.on_save),
            ('Save _As', self.on_saveas),
            None,
            ('_Quit', self.on_quit),
            ]),
          ('_Edit', [
            ('_Copy', self.on_copy),
            ('C_ut', self.on_cut),
            ('_Paste', self.on_paste),
            None,
            ('_Options', self.on_options),
            ]),
          ('_Help', [
            ('_Help', self.on_help),
            None,
            ('_About', self.on_about),
            ]),
          ]

        return BuildMenuBar(menu_desc)

    def ask_open (self):
        loadname = None
        dlg = gtk.FileChooserDialog("Open", None, action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=("Open",1, "Cancel", 0))
        response = dlg.run()
        if response == 1:
            loadname = dlg.get_filename()
            if loadname[-4:] != ".cfg":
                loadname = loadname + ".cfg"
        dlg.destroy()
        return loadname

    def ask_save (self):
        savename = None
        dlg = gtk.FileChooserDialog("Save As", None, action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=("Save",1, "Cancel",0))
        response = dlg.run()
        if response == 1:
            savename = dlg.get_filename()
            if savename[-4:] != ".cfg":
                savename = savename + ".cfg"
        dlg.destroy()
        return savename

    def on_new (self, w, *args):
        self.app.reset()

    def on_open (self, w, *args):
        loadname = self.ask_open()
        if loadname:
            loadfile = open(loadname, "rb")
            self.store.load(loadfile)
            loadfile.close()
        #crumb("loaded binddata = %r" % (self.bindpad.bindlayers,))
        self.bindpad.moderow.btn_global.clicked()
        return

    def on_save (self, w, *args):
        if self.saveuri is None:
            # Dialog for filename.
            return self.on_saveas(w, *args)
        else:
            savefile = open(self.saveuri, "wb")
            self.app.save(savefile)
            savefile.close()
        return

    def on_saveas (self, w, *args):
        savename = self.ask_save()
        if savename:
            self.saveuri = savename
            savefile = open(savename, "wb")
            self.app.save(savefile)
            savefile.close()
        return

    def on_copy (self, w, *args):
        pass

    def on_cut (self, w, *args):
        pass

    def on_paste (self, w, *args):
        pass

    def on_options (self, w, *args):
        pass

    def on_help (self, w, *args):
        pass

    def on_about (self, w, *args):
        pass

    def on_quit (self, w, *args):
        self.app.quit()




class VisMapperApp (object):
    """Overall application object, minimalist wrapper."""
    def __init__ (self):
        self.store = Store(8)
        self.ui = VisMapperWindow(self)

    def go (self):
        self.ui.show_all()
        gtk.mainloop()

    def load (self, srcfile):
        self.store.load(destfile)
        return 0

    def save (self, destfile):
        self.store.save(destfile)
        return 0

    def reset (self):
        self.store.reset()
        self.ui.reset()

    def quit (self):
        gtk.main_quit()



if __name__ == "__main__":
    #s = Store()
    #s.save()
    app = VisMapperApp()
    app.go()


