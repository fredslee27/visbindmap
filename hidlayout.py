#!/usr/bin/env python
# vim: expandtab shiftwidth=4 :

# TODO: adopt __gproperties__ pattern.
# TODO: bind resolution fallthrough

from __future__ import print_function

import sys
import gtk, gobject, glib
import math
import ast

import kbd_desc


class DndOpcodes:  # old-style class; enum symbols are class-scope members.
    """Drag-And-Drop opcodes enumeration;
this app overloads the drag-drop 'info' field to act as DnD opcode."""
    class DndOpcodeEnum (object):  # new-style class; enum values are instances.
        _GENSYM = 1
        def __init__ (self, name, val=None):
            self.name = name
            if val is None:
                val = self.__class__._GENSYM
                self.__class__._GENSYM += 1
            self.val = val
        def get_name (self): return self.name
        def get_val (self): return self.val
        s = property(get_name)
        i = property(get_val)
        d = property(get_val)
        def __int__ (self): return self.val
        def __str__ (self): return self.name
        def __eq__ (self, other):
            if type(other) == int:
                return other == self.val
            try:
                return other.name == self.name
            except:
                pass
            return (other is self)
        def __repr__ (self):
            return "DndOpcode({!r},{!r})".format(self.name, self.val)
    enum = DndOpcodeEnum

    BIND = enum("bind", 1)         # Copy bind into destination.
    UNBIND = enum("unbind", 2)     # Remove bind from destination.
    SWAP = enum("swap", 3)         # Trigger InpDescrModel.swap_bind.
    # BIND transfers binding value, SWAP transfers the symcode (key) .
    REORDER = enum("reorder", 11)  # Internal reordering of TreeView.


# Logging.
class Logger (object):
    """Logger class.
Instantiate with Logger(Logger.{THRESHOLD}), where TRESHOLD is one of:
 * fatal  -  user may expect the app to terminate immediately.
 * error  -  user may expect app state to no longer reflect persistent storage ("gone crazy").
 * warn   -  user may expect some data to be contrary to expectations ("weird").
 * info   -  user may expect app to be consistent.
 * debug  -  debug: development-relevant messages.

Change threshold during runtime by setting property "level":
 * loggerInstance.set_level(loggerInstance.info)
 * loggerInstance.level = loggerInstance.error


To change log-writing behavior:
1: assign file-like object to .sink; all log messages use print(..., file=sink)
 or
2: Override logmsg(self, lvlnum, *msgparts)
 * lvlnum = logging level of the message, for filtering purposes.
 * *msgparts = list of message parts, intended to be concatenated with ' '.
and is_loggable(lvlnum) as default filtering predicate:
    if is_loggable(lvlnum): do_log_print(*msgparts)

"""
    def __init__ (self, loglevel=None, sink=sys.stderr):
        self.sink = sink
        if loglevel is None: loglevel = Logger.info
        self.set_level(loglevel)

    def get_level (self): return self._level
    def set_level (self, val): self._level = val.__func__
    level = property(get_level, set_level)

    def is_loggable (self, lvlnum):
        return (self._level in self._levels[lvlnum:])
    def logmsg (self, lvlnum, *msgparts):
        if self.is_loggable(lvlnum):
            markers = [ "!!!", "***", "---", "===", "+++" ]
            lvlmarker = markers[lvlnum]
            print(lvlmarker, *msgparts, file=self.sink)
    def fatal (self, *msgparts): self.logmsg(0, *msgparts)
    def error (self, *msgparts): self.logmsg(1, *msgparts)
    def warn (self, *msgparts):  self.logmsg(2, *msgparts)
    def info (self, *msgparts):  self.logmsg(3, *msgparts)
    def debug (self, *msgparts): self.logmsg(4, *msgparts)
    _levels = [ fatal, error, warn, info, debug ]
#logger = Logger(Logger.info)
logger = Logger(Logger.debug)
# set log level with: logger.level = logger.warn
# log with: logger.info("...", "...", ...)






# hia = Human(-computer) Interface Atom
# Bind storage model:
# BindStore = dict of BindMode
#  + BindMode = list of BindLayer
#    + BindLayer = list of BindEntry
#      + BindEntry = dict of hiasym => str
#
# interface pattern:
# bindmap[mode][layer][hiasym]  =>  str: binding for hiasym in mode and layer
# bindmap[mode][layer]  =>  dict: all hiasyms for mode and layer
# bindmap[mode]  =>  list: all layers for mode


class BindLayer (dict):
    """dict, hiasym => str
 key = hiasym
 value = binding
"""
    def clear (self):
        for k in self.keys():
            del self[k]
    def __copy__ (self):
        retval = dict(self)
        return retval

class BindMode (object):
    """list of BindLayer, one per layer available.
 index = layer number
 value = BindLayer

"""
    def __init__ (self, nlayers=1, fallthrough=None, raw_data=None):
        """
 nlayers: int = number of layers to start with.
 fallthrough: BindMode = another BindMode to use if resolution fails.
"""
        self.layers = list()
        self.fallthrough = fallthrough
        self.resize_layers(nlayers)
        if raw_data is not None:
            self.decode(raw_data)
        
    def clear (self):
        for lyr in self.layers:
            lyr.clear()
    def resize_layers (self, nlayers=1):
        self.nlayers = nlayers
        # Try grow to/past count.
        while len(self.layers) < self.nlayers:
            self.layers.append(BindLayer())
        # Cull excess.
        while len(self.layers) > self.nlayers:
            del self.layers[-1]
        return

    def __copy__ (self):
        retval = BindMode(self.nlayers, self.fallthrough)
        for lyridx in range(self.nlayers):
            retval[lyridx] = self[lyridx].__copy__()
        return retval
    # Delegate sequence operators to .layers
    def __len__ (self):             return len(self.layers)
    def __getitem__ (self, key):
        if isinstance(key, slice):
            # slicing.
            sliced = self.layers.__getitem__(key)
            retval = BindMode(len(sliced), None)
            retval.layers = sliced
            return retval
        else:
            return self.layers.__getitem__(key)
    def __missing__ (self, key):    return self.layers.__missing__(key)
    def __iter__ (self):            return self.layers.__iter__()
    def __setitem__ (self, key, value): self.layers[key] = value
    def __setslice__ (self, i, j, seq): self.layers.__setslice__(i,j,seq)
    def __delslice__ (self, i, j):      self.layers.__delslice__(i,j)

    def decode (self, raw_data):
        self.layers = []
        for enclyr in raw_data:
            lyr = BindLayer(enclyr)
            self.layers.append(lyr)

    def encode (self):
        enc = dict()
        enc['.class'] = self.__class__.__name__
        enc['nlayers'] = self.nlayers
        enc['fallthrough'] = self.fallthrough
        enc['raw_data'] = self.layers
        return enc

    def __repr__ (self):
        return repr(self.encode)

class BindStore (object):
    """list of BindMode, one per mode available.
 index = mode number
 value = BindMode
"""
    def __init__ (self, nmodes=1, nlayers=1, raw_data=None):
        self.modes = []
        self.nmodes = nmodes
        self.nlayers = nlayers
        self.resize_layers(self.nlayers)
        self.resize_modes(self.nmodes)
        if raw_data is not None:
            self.decode(raw_data)
    def clear (self):
        # Erase all binds.
        for mode in self.modes:
            mode.clear()
    def resize_modes (self, nmodes):
        self.nmodes = nmodes
        while len(self.modes) < self.nmodes:
            self.modes.append(BindMode(self.nlayers))
        while len(self.modes) > self.nmodes:
            del self.modes[-1]
        return
    def resize_layers (self, nlayers):
        self.nlayers = nlayers
        for bindmode in self.modes:
            bindmode.resize_layers(self.nlayers)
        return
    def resolve_binds_markup (self, hiasym, modenum):
        binds = []
        mode = self.modes[modenum]
        redirect_limit = len(mode.layers)+1  # number of layers.
        for layernum in range(len(mode.layers)):
            lyr = mode.layers[layernum]
            m = mode
            redirects = 0
            bindval = ""
            entry = ""
            while m and not entry and redirects < redirect_limit:
                rawval = m[layernum].get(hiasym, "")
                if rawval is None:
                    rawval = ""
                bindval = glib.markup_escape_text(rawval)
                if bindval:
                    break
                if m.fallthrough is not None:
                    m = self.modes[m.fallthrough]
                    redirects += 1
                else:
                    m = None
            if redirects:
                # Keep trailing space for vertical spacing.
                entry = "<i><small>{}</small></i> ".format(bindval)
            else:
                entry = "{}".format(bindval)
            binds.append(entry)
        return binds
    def __copy__ (self):
        retval = BindStore(self.nmodes, self.nlayers)
        copymap = dict()    # map fallthrough links.
        for modeidx in range(len(self.modes)):
            # TODO: handle mismatched layers.
            retval.modes[modeidx] = self.modes[modeidx].__copy__()
            copymap[self.modes[modeidx]] = retval[modeidx]
        # Redirect remapped fallthroughs.
        for mode in retval.modes:
            if mode.fallthrough:
                mode.fallthrough = copymap[mode.fallthrough]
        return retval
    # Delegate sequence operators to .modes
    def __len__ (self):             return len(self.modes)
    def __getitem__ (self, key):    return self.modes.__getitem__(key)
    def __missing__ (self, key):    return self.modes.__missing__(key)
    def __iter__ (self):            return self.modes.__iter__()
    def __setitem__ (self, key, value): self.modes.__setitem__(key, value)
    def __setslice__ (self, i, j, seq): self.modes.__setslice__(i,j,seq)
    def __delslice__ (self, i, j):      self.modes.__delslice__(i,j)

    def __str__ (self):
        parts = [self.__class__.__name__]
        parts.append(" [")
        parts.append("\n")
        for gn in range(self.nmodes):
            parts.append("  [ # Mode %d\n" % gn)
            for ln in range(self.nlayers):
                parts.append("   { # Layer %d\n" % ln)
                for k,v in self.modes[gn][ln].iteritems():
                    parts.append("   %r: %r\n" % (k, v))
                parts.append("   } # L%d\n" % ln)
            parts.append("  ] # G%d\n" % gn)
        parts.append(" ]")
        return "".join(parts)

    def decode (self, raw_data):
        self.modes = []
        for encmode in raw_data:
            if encmode['.class'] != BindMode.__name__:
                raise TypeError("Did not find expected BindMode")
            temp = dict(encmode)
            del temp['.class']
            mode = BindMode(**temp)
            self.modes.append(mode)

    def encode (self):
        enc = dict()
        enc['.class'] = self.__class__.__name__
        enc['nmodes'] = self.nmodes
        enc['nlayers'] = self.nlayers
        ser = []
        for mode in self.modes:
            encmode = mode.encode()
            ser.append(encmode)
        enc['raw_data'] = ser
        return enc

    def __repr__ (self):
        return repr(self.encode())




class HidLayoutStore (gtk.TreeStore):
    """Description of HID element layout.
Items are (inpsym, lbl, prototype, x, y, w, h)

inpsym is an identifier expected to conform to C identifier constraints, used as the key in a mapping type for bindings.
lbl is an arbitrary string to show the user for the input element.

prototype: key, cluster


rowrun format is list rowdesc
 rowdesc is list of tuples
  tuple = ( width, height, inpsym, lbl, prototype ) |
          ( width, height, inpsym, lbl ) |
          ( width, height, inpsym ) |
          ( width, height )

width, height - in terms of cells (gtk.Table, GtkGrid)
"""

    def __init__ (self, layout_name):
        gtk.TreeStore.__init__(self, str, str, str, int, int, int, int)
        self.name = layout_name
        self.nrows = 0
        self.ncols = 0
        self.lookup = dict()

    # TODO: overload mutators and check for size maximums there.
    def append (self, parentiter, rowdata):
        x, y, w, h = rowdata[3:7]
        xlim = x + w
        ylim = y + h
        if xlim > self.ncols:
            self.ncols = xlim
        if ylim > self.nrows:
            self.nrows = ylim
        treeiter = gtk.TreeStore.append(self, parentiter, rowdata)
        inpsym = rowdata[0]
        self.lookup[inpsym] = self.get_path(treeiter)

    def get_label (self, inpsym):
        treeiter = self.lookup.get(inpsym, None)
        lbl = ""
        if treeiter:
            lbl = self[treeiter][1]
        return lbl

    def build_from_rowrun (self, desc):
        rownum = 0
        colnum = 0
        maxrow = 0
        maxcol = 0
        for rowdesc in desc:
            if rowdesc:
                for eltdesc in rowdesc:
                    inpsym, lbl, prototyp = None, None, None
                    rowspan, colspan = eltdesc[0], eltdesc[1]
                    if len(eltdesc) > 2:
                        inpsym = eltdesc[2]
                    if len(eltdesc) > 3:
                        lbl = eltdesc[3]
                    if len(eltdesc) > 4:
                        prototyp = eltdesc[4]
                    y, x = rownum, colnum
                    h, w = rowspan, colspan
                    if prototyp is None:
                        if inpsym is None:
                            prototyp = 'blank'
                        else:
                            prototyp = 'key'
                    if lbl is None:
                        lbl = inpsym
                    if inpsym is not None:
                        data = (inpsym, lbl, prototyp, x, y, w, h)
                        self.append(None, data)
                    colnum += colspan
            rownum += 1
            colnum = 0
        return

class HidLayouts (gtk.ListStore):
    """AList of HidLayoutStore.
Rows are tuples of (layout_name, layout_map).
"""
    def __init__ (self):
        gtk.ListStore.__init__(self, gobject.TYPE_STRING, gobject.TYPE_OBJECT)

    def build_from_all_rowrun (self, all_rowrun):
        for hidname in all_rowrun.keys():
            hiditem = all_rowrun[hidname]
            onelayout = HidLayoutStore(hidname)
            onelayout.build_from_rowrun(hiditem)
            row = self.append((hidname, onelayout))

    def build_from_legacy_store (self):
        alldata = kbd_desc.KBD
        self.build_from_all_rowrun(alldata)

    def __getitem__ (self, key):
        match = []
        for row in gtk.ListStore.__iter__(self):
            if row[0] == key:
                match.append(row[1])
        if match:
            return match[0]
        return gtk.ListStore.__getitem__(self, key)
        #raise KeyError("Key not found: {}".format(key))
    def __setitem__ (self, key, val):
        try:
            gtk.ListStore.__setitem__(self, key, val)
        except IndexError:
            pass
        # could not use ListStore __getitem__, act like alist.
        match = [ n for n in range(len(self)) if self[n][0] == key ]
        if match:
            # replace.
            ofs = match[0]
            k, v = self[ofs][0], val
            self[ofs] = (k, v)
        else:
            # create.
            cooked = ( key, val )
            self.append(cooked)
    def keys (self):
        return [ k for k,v in self ]




class DumbData (object):
    def __getattr__ (self, attr):
        return self.__dict__[attr]
    def __setattr__ (self, attr, val):
        self.__dict__[attr] = val
    def __delattr__ (self, attr):
        del self.__dict__[attr]


class Bindable (object):
    """Base class for widgets showing binds.
"""
    def __init__ (self, hiasym, label=None, vis=None, init_binds=None):
        self._hiasym = hiasym
        self._label = label
        self._layer = 0     # Currently active layer.
        if vis is None:
            vis = [ True ]
        # TODO: change to tuple?
        self._vis = vis  # List of bool, visibility of each layer; len is total number of layers.
        if init_binds is None:
            init_binds = (None,)*len(self._vis)
        self._binds = init_binds     # Tuple of str, one per layer.  Tuple-ness as the grouping is an intrinsic property (immutability of the sequence).

    @property
    def nlayers (self): return len(self.vis)

    def get_hiasym (self):
        return self._hiasym
    def set_hiasym (self, val):
        self._hiasym = val
        self.update_hiasym()
    hiasym = property(get_hiasym, set_hiasym)

    def get_toplabel (self):
        return self._label
    def set_toplabel (self, val):
        self._label = val
        self.update_toplabel()
    def del_toplabel (self, val):
        self.set_toplabel(None)
    toplabel = property(get_toplabel, set_toplabel, del_toplabel)

    def get_layer (self):
        return self._layer
    def set_layer (self, val):
        self._layer = val
        self.update_layer()
    layer = property(get_layer, set_layer)

    def get_vis (self):
        return self._vis
    def set_vis (self, val):
        self._vis = val
        self.update_vis()
    vis = property(get_vis, set_vis)

    def get_binds (self):
        return self._binds
    def set_binds (self, bindlist):
        if len(bindlist) < self.nlayers:
            shortage = self.nlayers - len(bindlist)
            self._binds = tuple(bindlist) + (None,)*shortage
        elif len(bindlist) > self.nlayers:
            self._binds = tuple(bindlist)[:self.nlayers]
        else:
            self._binds = tuple(bindlist)
        self.update_binds()
    binds = property(get_binds, set_binds)

    def update_hiasym (self): """Called after set_hiasym; override."""
    def update_toplabel (self): """Called after set_toplabel; override."""
    def update_layer (self): """Called after set_layer; override."""
    def update_vis (self): """Called after set_vis; override."""
    def update_binds (self): """Called after set_binds; override."""

    def make_hiatop (self, descr, init_binds=None, parent_cluster=None):
        hiasym, hialbl, hiatype, x, y, w, h = descr
        hiatop = None
        if hiatype == "cluster":
            hiatop = BindableCluster(hiasym, hialbl, self.vis, init_binds)
            if parent_cluster:
                parent_cluster.hiatops[hiasym] = hiatop
                parent_cluster.hiaclusters[hiasym] = hiatop
        elif hiatype == "key":
            hiatop = BindableTop(hiasym, hialbl, self.vis, init_binds)
            if parent_cluster:
                parent_cluster.hiatops[hiasym] = hiatop
        else:
            pass
        if hiatop:
            hiatop.connect("bind-assigned", self.on_bind_assigned)
            hiatop.connect("bind-swapped", self.on_bind_swapped)
            hiatop.connect("bind-erased", self.on_bind_erased)
        return hiatop

    __gsignals__ = {
        "bind-assigned": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        "bind-swapped": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        "bind-erased": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
    }


class BindableTop (gtk.Button, Bindable):
    """The bindable atom, metaphor for keyboard key top.

Supports drag-and-drop.  Semantics:
 * from command set to btop - assign binding : bind-assigned(hiasym, bindval)
 * from btop to btop - swap binding : bind-swaped(src-hiasym, dst-hiasym)
 * from btop to command set - erase binding : bind-erased(src-hiasym)
"""
    def __init__ (self, hiasym, label=None, vis=None, init_binds=None):
        Bindable.__init__(self, hiasym, label, vis, init_binds)
        gtk.Button.__init__(self)
        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()

    def setup_widgets (self):
        """One-time setup; visual widgets."""
        # UI components:
        #  row1 = Label
        #  row2 = bind,layer[0]
        #  row3 = bind,layer[1]
        self.ui = DumbData()
        self.ui.top = gtk.VBox()

        # First row: element label; gravitate top-left.
        self.ui.lbl = gtk.Label()
        self.ui.align0 = gtk.Alignment(0, 0, 0, 0)
        self.ui.align0.add(self.ui.lbl)
        self.ui.top.pack_start(self.ui.align0, expand=False, fill=True)

        # Second row: depressed relief for binds.
        self.ui.frame = gtk.Frame()
        self.ui.frame.set_shadow_type(gtk.SHADOW_IN)
        self.ui.dispbox = gtk.VBox()
        self.ui.align1 = gtk.Alignment(0,0,1,1)  # gravitate top+left.
        self.ui.align1.add(self.ui.dispbox)
        self.ui.frame.add(self.ui.align1)
        self.ui.top.pack_start(self.ui.frame, expand=False, fill=True)

        # Third row: expanding spacer.
        self.ui.spacer = gtk.HBox()
        self.ui.top.pack_start(self.ui.spacer, expand=True, fill=True)

        # Reference widget for styling display labels.
        temp = gtk.Entry()
        #self.refstyle = temp.get_style().copy()
        refstyle = temp.get_style().copy()
        self.refstyle = DumbData()
        self.refstyle.bg = refstyle.bg
        self.refstyle.base = refstyle.base
        del temp

        # Multiple/variable number of layers to display; all in .dispbox.
        self.ui.disp = []       # Display binding.
        self.ui.lyr = []        # Layers labeling prefix to binding.
        self.ui.bg = []         # Backgrounds for bind displays.
        self.ui.hrules = []     # List of HSeparator between layer rows.
        self.ui.rows = []       # Box for each line of hrule+lyr+disp

        # Attach button face.
        self.add(self.ui.top)
        self.show_all()

        # (re)adjust binds display.
        self.update_toplabel()
        self.adjust_widgets()

        self.set_no_show_all(True)

    def update_hiasym (self):
        """HIA symbol changed; may update label."""
        if self.toplabel is None:
            self.toplabel = self.hiasym  # chain reaction into update_toplabel.

    def update_toplabel (self):
        """Update GUI element for hiasym with stored value."""
        toplabel = self.toplabel
        if toplabel is None:
            toplabel = self.hiasym
        if toplabel is None:
            toplabel = "(???)"
        toplabel = glib.markup_escape_text(toplabel)
        self.ui.lbl.set_markup(str(toplabel))

    def update_layer (self):
        """Layer updated; repaint highlights."""
        self.adjust_widgets()
        for ofs in range(len(self.ui.bg)):
            bg = self.ui.bg[ofs]
            self.paint_bg(bg, ofs == self.layer)

    def update_vis (self):
        """Visibility updated; ensure consistency with layers widgets."""
        self.adjust_widgets()

    def update_binds (self):
        """Binds updated; (re)populated binds displays."""
        for ofs in range(len(self.binds)):
            bindval = self.binds[ofs]
            binddisp = self.ui.disp[ofs]
            if bindval is None:
                bindval = ""
            binddisp.set_markup(bindval)

    def paint_bg (self, bg, activestyle):
        """Set background highlighting for a bind display;
Copy style of an active Entry for current layer;
Use style of out-of-focus Entry for all other layers."""
        usestyle = self.refstyle.bg
        if activestyle:
            usestyle = self.refstyle.base
        if bg.usestyle != usestyle:
            # Update if differs.
            bg.modify_bg(gtk.STATE_NORMAL, usestyle[gtk.STATE_NORMAL])
            bg.modify_bg(gtk.STATE_ACTIVE, usestyle[gtk.STATE_ACTIVE])
            bg.modify_bg(gtk.STATE_PRELIGHT, usestyle[gtk.STATE_PRELIGHT])
            bg.modify_bg(gtk.STATE_SELECTED, usestyle[gtk.STATE_SELECTED])
            bg.usestyle = usestyle

    def goal_binddisp (self, ofs):
        """Ensure a complete set of binddisp for layer 'ofs'."""
        if not self.ui.hrules[ofs]:
            self.ui.hrules[ofs] = gtk.HSeparator() if ofs != 0 else gtk.HBox()
            self.ui.dispbox.pack_start(self.ui.hrules[ofs], False, True, 0)

        if not self.ui.lyr[ofs]:
            self.ui.lyr[ofs] = gtk.Label("{}:".format(ofs))
        if not self.ui.disp[ofs]:
            self.ui.disp[ofs] = gtk.Label()
            self.ui.disp[ofs].set_alignment(0, 0.5)
            self.ui.disp[ofs].set_width_chars(4)
            self.ui.disp[ofs].set_justify(gtk.JUSTIFY_LEFT)
        if not self.ui.bg[ofs]:
            self.ui.bg[ofs] = gtk.EventBox()
            self.ui.bg[ofs].add(self.ui.disp[ofs])

            self.ui.bg[ofs].usestyle = None
            self.paint_bg(self.ui.bg[ofs], ofs == self.layer)

        if not self.ui.rows[ofs]:
            self.ui.rows[ofs] = gtk.HBox()
            hbox = self.ui.rows[ofs]
            hbox.pack_start(self.ui.lyr[ofs], False, False, 0)
            #hbox.pack_start(self.ui.disp[ofs], True, True, 0)
            hbox.pack_start(self.ui.bg[ofs], True, True, 0)
            self.ui.dispbox.pack_start(hbox, False, True, 0)

    def adjust_widgets (self):
        """Dynamically adjust contained widgets."""
        # For each binding, generate: a hrule, a lyr Label, a disp Entry, encompassing HBox (row).
        nlayers = len(self.vis)
        for lim_checkable in [ self.ui.disp, self.ui.lyr, self.ui.bg, self.ui.hrules, self.ui.rows ]:
            if len(lim_checkable) < nlayers:
                lim_checkable.extend([ None, ] * (nlayers - len(lim_checkable)))
        nvis = 0
        for lyrnum in range(nlayers):
            self.goal_binddisp(lyrnum)
            # Juggle visibility.
            if self.vis[lyrnum]:
                nvis += 1
                if not self.ui.lyr[lyrnum].get_visible():
                    self.ui.rows[lyrnum].show_all()
                    if nvis == 1:
                        # keep hidden if first hrule to be made visible.
                        self.ui.hrules[lyrnum].hide()
                    else:
                        self.ui.hrules[lyrnum].show()
            else:
                if self.ui.lyr[lyrnum].get_visible():
                    self.ui.lyr[lyrnum].hide()
                self.ui.hrules[lyrnum].hide()
                self.ui.rows[lyrnum].hide_all()
        if nvis == 1:
            # only one, hide lyr label and all hrules.
            for lyr in self.ui.lyr:
                if lyr.get_visible():
                    lyr.hide_all()
            for hrule in self.ui.hrules:
                if hrule.get_visible():
                    hrule.hide()
        return


    def setup_signals (self):
        """One-time setup, GTK signals."""
        pass


    def setup_dnd (self):
        """One-time setup, GTK Drag-and-Drop."""
        # self as DnD source: erase, swap.
        dnd_targets = [
          (str(DndOpcodes.UNBIND), gtk.TARGET_SAME_APP, DndOpcodes.UNBIND),
          (str(DndOpcodes.SWAP), gtk.TARGET_SAME_APP, DndOpcodes.SWAP),
        ]
        dnd_actions = gtk.gdk.ACTION_COPY
        self.drag_source_set(gtk.gdk.BUTTON1_MASK, dnd_targets, dnd_actions)
        self.connect("drag-data-get", self.on_drag_data_get)
        self.connect("drag-end", self.on_drag_end)

        # self as DnD destination: bind, swap.
        dnd_targets = [
          (str(DndOpcodes.BIND), gtk.TARGET_SAME_APP, DndOpcodes.BIND),
          (str(DndOpcodes.SWAP), gtk.TARGET_SAME_APP, DndOpcodes.SWAP),
        ]
        dnd_actions = gtk.gdk.ACTION_COPY
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, dnd_targets, dnd_actions)
        self.connect("drag-data-received", self.on_drag_data_received)

        self.pending_drag_unbinding = False

    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        # is DnD source.
        logger.debug("hiatop.drag-data-get: %d" % info)
        if info == DndOpcodes.UNBIND:
            # dragged to command set.
            logger.debug("hiatop: try unbind  %s" % self.hiasym)
            seldata.set(seldata.target, 8, str(self.hiasym))
            self.pending_drag_unbinding = True
            return True
        if info == DndOpcodes.SWAP:
            # dragged to another BindableTop.
            logger.debug("hiatop.drag-data-get for swap")
            val = self.hiasym
            seldata.set(seldata.target, 8, str(self.hiasym))
            return True
        return False

    def on_drag_end (self, w, ctx, *args):
        """As DnD source, drag has finished."""
        logger.debug("hiatop.drag-end")
        if self.pending_drag_unbinding:  # Check if drag-to-unbind.
            logger.debug("hiatop unbind %s" % self.hiasym)
            self.emit("bind-erased", self.hiasym)
            self.pending_drag_unbinding = False
        return
#
    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        """As DnD destination, data/details received from DnD Source."""
        logger.debug("%s drag-data-received %r" % (self.__class__.__name__, w))
        if info == DndOpcodes.BIND:
            # Commands dropping.
            seltext = seldata.data
            logger.debug("hiatop Command install: %s <= %s" % (w.hiasym, seltext))
            self.emit("bind-assigned", self.hiasym, seltext)
            ctx.finish(True, False, 0)
            return True
        elif info == DndOpcodes.SWAP:
            othersym = seldata.data
            logger.debug("hiatop Command swap: %s <=> %s" % (w.hiasym, othersym))
            #self.swap_bind(w.hiasym, othersym)
            self.emit("bind-swapped", w.hiasym, othersym)
            ctx.finish(True, False, 0)
            return True

    __gsignals__ = Bindable.__gsignals__



class BindableListStore (gtk.ListStore):
    def __init__ (self, nlayers):
        # hiasym, hialbl, columns with binds.
        columns = (str,str) + (str,)*nlayers


class BindableListView (gtk.ScrolledWindow):
    """TreeView of list-based cluster types.

Parent BindableCluster manipulates bound model (BindableListStore).
"""
    def __init__ (self, mdl, vis=None):
        gtk.ScrolledWindow.__init__(self)
        self._mdl = mdl
        self._vis = vis
        self._layer = 0

        self.setup_states()
        self.setup_widget()
        self.setup_signals()
        self.setup_dnd()

        self.show_all()

    def get_nlayers (self):
        return len(self._mdl[0])-2
    nlayers = property(get_nlayers)

    def get_vis (self):
        return self._vis
    def set_vis (self, val):
        self._vis = tuple(val)
        self.update_vis()
    vis = property(get_vis, set_vis)
    def update_vis (self):
        for colnum in range(len(self._vis)):
            self.ui.bindcols[colnum].set_visible(self._vis[colnum])

    def get_layer (self):
        return self._layer
    def set_layer (self, val):
        self._layer = val
        self.update_layer()
    layer = property(get_layer, set_layer)
    def update_layer (self):
        for i in range(self.nlayers):
            renderer = self.ui.renderers[i]
            usestyle = self.refstyle.bg
            if i == self.layer:
                usestyle = self.refstyle.base
            styleval = usestyle[gtk.STATE_NORMAL]
            renderer.props.background = usestyle[gtk.STATE_NORMAL]
        self.queue_draw()
        return

    def get_model (self):
        return self._mdl
    def set_model (self, val):
        self._mdl = val
        self.update_model()
    model = property(get_model, set_model)
    def update_model (self):
        pass

    def setup_states (self):
        temp = gtk.Button().get_style().copy()
        self.refstyle = DumbData()
        self.refstyle.bg = temp.bg
        self.refstyle.base = temp.base
        del temp

    def setup_widget (self):
        # The TreeView
        self.ui = DumbData()
        self.ui.treeview = gtk.TreeView(self._mdl)
        self.ui.rendertext = gtk.CellRendererText()
        nlayers = self.nlayers
        self.ui.col0 = gtk.TreeViewColumn("#", self.ui.rendertext, text=1)
        self.ui.treeview.append_column(self.ui.col0)
        self.ui.bindcols = []
        self.ui.renderers = []
        for i in range(nlayers):
            title = "bind%d" % i
            renderer = gtk.CellRendererText()
            datacol = i+2
            bind_col = gtk.TreeViewColumn(title, renderer, markup=datacol)
            bind_col.set_expand(True)
            self.ui.bindcols.append(bind_col)
            self.ui.renderers.append(renderer)
            self.ui.treeview.append_column(bind_col)
        self.update_vis()
        self.update_layer()

        self.add(self.ui.treeview)  # and not with viewport -- scroll with anchored column header.
        self.show_all()

    def setup_signals (self):
        pass

    def setup_dnd (self):
        """Set up drag-and-drop."""
        # DnD Source
        dnd_targets = [
          (str(DndOpcodes.REORDER), gtk.TARGET_SAME_WIDGET, DndOpcodes.REORDER),
          (str(DndOpcodes.UNBIND), gtk.TARGET_SAME_WIDGET, DndOpcodes.UNBIND),
          (str(DndOpcodes.SWAP), gtk.TARGET_SAME_APP, DndOpcodes.SWAP),
        ]
        dnd_actions = gtk.gdk.ACTION_COPY
        self.ui.treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, dnd_targets, dnd_actions)
        self.ui.treeview.connect("drag-data-get", self.on_drag_data_get)
        self.ui.treeview.connect("drag-end", self.on_drag_end)

        # DnD Destination
        dnd_targets = [
          (str(DndOpcodes.REORDER), gtk.TARGET_SAME_WIDGET, DndOpcodes.REORDER),
          (str(DndOpcodes.BIND), gtk.TARGET_SAME_APP, DndOpcodes.BIND),
          (str(DndOpcodes.SWAP), gtk.TARGET_SAME_APP, DndOpcodes.SWAP),
        ]
        dnd_actions = gtk.gdk.ACTION_COPY
        self.ui.treeview.enable_model_drag_dest(dnd_targets, dnd_actions)
        self.ui.treeview.connect("drag-data-received", self.on_drag_data_received)

#        self.droppath = None
        self.dropunbind = None

    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        # As DnD source, determine what was dragged away.
        treesel = w.get_selection()
        mdl, pathsels = treesel.get_selected_rows()
        firstpath = pathsels[0]
        selrow = mdl[firstpath]
        hiasym = selrow[0]
        data = None
        if info == DndOpcodes.REORDER:
            # Reordering.  Encoding source path into string.
            #logger.debug("hialistview drag-data-get reorder")
            data = repr(firstpath)
        elif info == DndOpcodes.UNBIND:
            logger.debug("hidmenulist drag-data-get unbind")
            data = hiasym
            self.dropunbind = hiasym
        elif info == DndOpcodes.SWAP:
            logger.debug("hidmenulist drag-data-get swap")
            data = hiasym
        if data is not None:
            seldata.set(seldata.target, 8, data)

    def on_drag_end (self, w, ctx, *args):
        logger.debug("hidmenulist drag-end")
        if self.dropunbind:
            logger.debug("list-bind-erasing %s" % self.dropunbind)
            #self.set_bind(self.dropunbind, "")
            self.emit("bind-erased", self.dropunbind)
            self.dropunbind = None
        return True

    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        # As DnD destination, determine what was dragged in.
        srcw = ctx.get_source_widget()
#        droppath = self.droppath
        dropinfo = w.get_dest_row_at_pos(x,y)
        destpath, destpos = None, None
        if dropinfo:
            destpath, destpos = dropinfo
        else:
            # all cases rely on dropinfo being valid.
            return False

        if info == DndOpcodes.REORDER:
            #logger.debug("hidmenulist reorder")
            # Reordering internally, seldata.data is tree path.
            encoded = seldata.data
            srcpath = ast.literal_eval(encoded)
            func, bias = {
                gtk.TREE_VIEW_DROP_INTO_OR_BEFORE: (self.reorder_bindlist, 0),
                gtk.TREE_VIEW_DROP_INTO_OR_AFTER: (self.reorder_bindlist, 0),
                gtk.TREE_VIEW_DROP_BEFORE: (self.reorder_bindlist, -1),
                gtk.TREE_VIEW_DROP_AFTER: (self.reorder_bindlist, +1),
            }.get(destpos, (None,None))
            logger.debug("reordering internally: %r vs %r" % (srcpath, destpath))
            if callable(func):
                func(*(bias, srcpath, destpath))
            if ctx.action == gtk.gdk.ACTION_MOVE:
                ctx.finish(True, True, time)
            return True
        elif info == DndOpcodes.BIND:
            # bind-drop from commands set, seldata.data is bind (str).
            #logger.debug("hialistview bind-drop")
            dropinfo = w.get_dest_row_at_pos(x,y)
            bindval = seldata.data
            hiasym = self.model[destpath][0]
            logger.debug("list-bind-assigning: %r <- %r" % (hiasym, bindval))
            self.emit("bind-assigned", hiasym, bindval)
            ctx.finish(True, False, time)
            return True
        elif info == DndOpcodes.SWAP:
            # swap with a hidtop, seldata.data is hiasym.
            #logger.debug("hidmenulist swap")
            othersym = seldata.data
            destsym = self.model[destpath][0]
            logger.debug("list-bind-swapping: %r,%r" % (destsym, othersym))
            self.emit("bind-swapped", destsym, othersym)
            ctx.finish(True, False, time)
            return True
        return False


    def reorder_bindlist (self, bias, srcpath, dstpath):
        # Pull binds for the current layer.
        listbinds = [ r[2+self.layer] for r in self.model ]
        srcrow = srcpath[0]
        dstrow = dstpath[0]
        srcbind = listbinds[srcrow]
        # Re-order binds list.
        if bias == 0:
            # swap.
            listbinds[srcrow] = listbinds[dstrow]
            listbinds[dstrow] = srcbind
        else:
            # insert before a row, or append at end if no "before".
            listbinds[srcrow] = trashed = object()  # nonce value for removals.
            if bias < 0:
                listbinds.insert(dstrow, srcbind)
            elif dstrow < len(listbinds):
                listbinds.insert(dstrow+1, srcbind)
            else:
                listbinds.append(srcbind)
#            if srcrow > dstrow:
#                srcrow += 1
#            del listbinds[srcrow]
            listbinds = [ x for x in listbinds if x is not trashed ]

        # Identify binds to be changed.
        for i in range(0, len(listbinds)):
            reordered_bind = listbinds[i]    # new bind for this row.
            hiasym = self.model[i][0]        # hiasym for this row.
            oldbind = self.model[i][2+self.layer]  # old bind for this row.
            if oldbind != reordered_bind:
                # Change detected, notify listeners.
                logger.debug("change for %r" % hiasym)
                self.emit("bind-assigned", hiasym, reordered_bind)
        return

    __gsignals__ = {
        "bind-assigned": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        "bind-swapped": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        "bind-erased": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
    }

gobject.type_register(BindableListView)



class ClusteredLayouts (HidLayouts):
    """Nested layouts for clusters."""
    def __init__ (self, symprefix):
        HidLayouts.__init__(self)
        self.symprefix = symprefix
        self.build_layouts()

    # onebutton, scroll, dpad, bquad, mouse, trackpad, js, gyro, touchmenu, radialmenu

    def build_layouts (self):
        self._build_layout_empty()
        self._build_layout_one()
        self._build_layout_scrl()
        self._build_layout_dpad()
        self._build_layout_bquad()
        self._build_layout_track()
        self._build_layout_mouse()
        self._build_layout_js()
        self._build_layout_gyro()
        self._build_layout_touchmenu()
        self._build_layout_radialmenu()
        return

    def make_layoutstore (self, suffix):
        #layoutname = "{}_{}".format(self.symprefix, suffix)
        layoutname = "{}".format(suffix)
        layout = HidLayoutStore(layoutname)
        return layout

    def make_gridded_layoutstore (self, suffix, w, h, simple_placements):
        layout = self.make_layoutstore(suffix)
        for datum in simple_placements:
            suffix, x, y = datum
            row = y * h
            col = x * w
            hiasym = "{}{}".format(self.symprefix, suffix)
            cooked = (hiasym, hiasym, "key", col, row, w, h)
            layout.append(None, cooked)
        return layout

    def _build_layout_empty (self):
        layout = self.make_layoutstore("Empty")
        self.append( (layout.name, layout) )

    def _build_layout_one (self):
        layout = self.make_gridded_layoutstore("OneButton",
          12, 12,
          [ ("c", 0, 0) ]
        )
        self.append( (layout.name, layout) )

    def _build_layout_scrl (self):
        layout = self.make_gridded_layoutstore("ScrollWheel",
          4, 4,
          [
            ("u", 1, 0),
            ("c", 1, 1),
            ("d", 1, 2),
            ]
        )
        self.append( (layout.name, layout) )

    def _build_layout_dpad (self):
        layout = self.make_gridded_layoutstore("DirectionPad",
          4, 4,
          [
            ("u", 1, 0),
            ("l", 0, 1),
            ("c", 1, 1),
            ("r", 2, 1),
            ("d", 1, 2),
            ]
        )
        self.append( (layout.name, layout) )

    def _build_layout_bquad (self):
        layout = self.make_gridded_layoutstore("ButtonQuad",
          4, 4,
          [
            ("n", 1, 0),
            ("w", 0, 1),
            ("e", 2, 1),
            ("s", 1, 2),
            ]
        )
        self.append( (layout.name, layout) )

    def _build_layout_track (self):
        layout = self.make_gridded_layoutstore("MousePad",
          4, 4,
          [
            ("c", 1, 1),
            ("x+", 2, 1),
            ("y+", 1, 2),
            ]
        )
        self.append( (layout.name, layout) )

    def _build_layout_mouse (self):
        layout = self.make_gridded_layoutstore("MouseRegion",
          4, 4,
          [
            ("y-", 1, 0),
            ("x-", 0, 1),
            ("c",  1, 1),
            ("x+", 2, 1),
            ("y+", 1, 2),
            ]
        )
        self.append( (layout.name, layout) )

    def _build_layout_js (self):
        layout = self.make_gridded_layoutstore("Joystick",
          4, 4,
          [
            ("y-", 1, 0),
            ("x-", 0, 1),
            ("c",  1, 1),
            ("x+", 2, 1),
            ("y+", 1, 2),
            ]
        )
        self.append( (layout.name, layout) )

    def _build_layout_gyro (self):
        layout = self.make_gridded_layoutstore("GyroTilt",
          4, 4,
          [
            ("z-", 0, 0),
            ("y-", 1, 0),
            ("z+", 2, 0),
            ("x-", 0, 1),
            ("c",  1, 1),
            ("x+", 2, 1),
            ("y+", 1, 2),
            ]
        )
        self.append( (layout.name, layout) )

    def _build_layout_touchmenu (self):
        # Variants: 2, 4, 7, 9, 12, 13, 16
        # the homogeneous grids: 2, 4, 9, 12, 16
        layout2 = self.make_gridded_layoutstore("TouchMenu02",
          6, 12,
          [
            ("1", 0, 0), ("2", 1, 0),
            ]
        )
        layout4 = self.make_gridded_layoutstore("TouchMenu04",
          6, 6,
          [
            ("1", 0, 0), ("2", 1, 0),
            ("3", 0, 1), ("4", 1, 1),
            ]
        )
        layout9 = self.make_gridded_layoutstore("TouchMenu09",
          4, 4,
          [
            ("1", 0, 0), ("2", 1, 0),
            ("3", 0, 1), ("4", 1, 1),
            ]
        )
        layout12 = self.make_gridded_layoutstore("TouchMenu12",
          3, 4,
          [
            ("1", 0, 0),  ("2", 1, 0),  ("3", 2, 0),  ("4", 3, 0),
            ("5", 0, 1),  ("6", 1, 1),  ("7", 2, 1),  ("8", 3, 1),
            ("9", 0, 2), ("10", 1, 2), ("11", 2, 2), ("12", 3, 2),
            ]
        )
        layout16 = self.make_gridded_layoutstore("TouchMenu16",
          3, 3,
          [
             ("1", 0, 0),  ("2", 1, 0),  ("3", 2, 0),  ("4", 3, 0),
             ("5", 0, 1),  ("6", 1, 1),  ("7", 2, 1),  ("8", 3, 1),
             ("9", 0, 2), ("10", 1, 2), ("11", 2, 2), ("12", 3, 2),
            ("13", 0, 3), ("14", 1, 3), ("15", 2, 3), ("16", 3, 3),
            ]
        )
        # The irregular layouts: 7, 13
        """
        |  1 2
        | 3 4 5
        |  6 7
        """

        def SYM (suffix):
            return "{}{}".format(self.symprefix, suffix)
        layout7 = self.make_layoutstore("TouchMenu07")
        layout7.append(None, (SYM(1), SYM(1), "key", 2,0,4,4))
        layout7.append(None, (SYM(2), SYM(2), "key", 6,0,4,4))
        layout7.append(None, (SYM(3), SYM(3), "key", 0,4,4,4))
        layout7.append(None, (SYM(4), SYM(4), "key", 4,4,4,4))
        layout7.append(None, (SYM(5), SYM(5), "key", 8,4,4,4))
        layout7.append(None, (SYM(6), SYM(6), "key", 2,8,4,4))
        layout7.append(None, (SYM(7), SYM(7), "key", 6,8,4,4))

        """
        | 01 02 03 04
        | 05       06
        |     13
        | 07       08
        | 09 10 11 12
        """
        layout13 = self.make_layoutstore("TouchMenu13")
        layout13.append(None, (SYM(1), SYM(1), "key", 0,0,3,3))
        layout13.append(None, (SYM(2), SYM(2), "key", 3,0,3,3))
        layout13.append(None, (SYM(3), SYM(3), "key", 6,0,3,3))
        layout13.append(None, (SYM(4), SYM(4), "key", 9,0,3,3))

        layout13.append(None, (SYM(5), SYM(5), "key", 0,3,3,3))
        layout13.append(None, (SYM(6), SYM(6), "key", 9,3,3,3))

        layout13.append(None, (SYM(7), SYM(7), "key", 0,6,3,3))
        layout13.append(None, (SYM(8), SYM(8), "key", 9,6,3,3))

        layout13.append(None, (SYM(9), SYM(9),  "key", 0,9,3,3))
        layout13.append(None, (SYM(10), SYM(10), "key", 3,9,3,3))
        layout13.append(None, (SYM(11), SYM(11), "key", 6,9,3,3))
        layout13.append(None, (SYM(12), SYM(12), "key", 9,9,3,3))

        layout13.append(None, (SYM(13), SYM(13), "key", 3,3,6,6))

        for layout in [ layout2, layout4, layout7, layout9, layout12, layout13, layout16 ]:
            self.append( (layout.name, layout) )
        return

    def _build_layout_radialmenu (self):
        # 19 variants, for counts 1..20.
        def SYM (suffix):
            return "{}{}".format(self.symprefix, suffix)
        def radialize (n, r=6):
            for step in range(n):
                angle = step * 2*math.pi / float(n)
                theta = - math.pi / 2. + angle
                x = r + (float(r) * math.cos(theta)) - .5
                y = r + (float(r) * math.sin(theta)) + .5
                yield (SYM(n), SYM(n), "key", x, y, 1, 1)
        for variant in range(1,21):
            layout = self.make_layoutstore("{}{:02d}".format("RadialMenu", variant))
            for entry in radialize(variant, r=6):
                layout.append(None, entry)
            self.append( (layout.name, layout) )
        return




class BindableArrangerContextMenu (gtk.Menu):
    """Context menu to change arrangements of hia cluster."""
    MENU_DESC = [
        # Tuples of (item_label, layout_name)
        ( "_None", "Empty"),
        ( "_SingleButton", "OneButton"),
        ( "Scroll_Wheel", "ScrollWheel"),
        ( "_DPad", "DirectionPad"),
        ( "_ButtonQuad", "ButtonQuad"),
        ( "_MousePad", "MousePad"),
        ( "_Joystick", "Joystick"),
        ( "_GyroTilt", "GyroTilt"),
        ( "_Touch Menu", [
            ( "_2 items", "TouchMenu02"),
            ( "_4 items", "TouchMenu04"),
            ( "_7 items", "TouchMenu07"),
            ( "_9 items", "TouchMenu09"),
            ( "_12 items", "TouchMenu12"),
            ( "_13 items", "TouchMenu13"),
            ( "_16 items", "TouchMenu16"),
            ]),
        ( "_Radial Menu", [
            ( "_01..09 items", [
                ("_1 item", "RadialMenu01"),
                ("_2 items", "RadialMenu02"),
                ("_3 items", "RadialMenu03"),
                ("_4 items", "RadialMenu04"),
                ("_5 items", "RadialMenu05"),
                ("_6 items", "RadialMenu06"),
                ("_7 items", "RadialMenu07"),
                ("_8 items", "RadialMenu08"),
                ("_9 items", "RadialMenu09"),
                ]),
            ( "_10..19 items", [
                ("1_0 items", "RadialMenu10"),
                ("1_1 items", "RadialMenu11"),
                ("1_2 items", "RadialMenu12"),
                ("1_3 items", "RadialMenu13"),
                ("1_4 items", "RadialMenu14"),
                ("1_5 items", "RadialMenu15"),
                ("1_6 items", "RadialMenu16"),
                ("1_7 items", "RadialMenu17"),
                ("1_8 items", "RadialMenu18"),
                ("1_9 items", "RadialMenu19"),
                ]),
            ( "_20.._29 items", [
                ("2_0 items", "RadialMenu20"),
                ]),
            ]),
        ( "_List Menu", "ListMenu" ),
        ]

    def __init__ (self, menu_title=None):
        gtk.Menu.__init__(self)
        self.build_menu(self, self.MENU_DESC)
        if menu_title is not None:
            title = gtk.MenuItem(str(menu_title), False)
            title.set_sensitive(False)
            self.prepend(title)
        self.connect_menuitems()
        self.show_all()

    @staticmethod
    def build_menu (menuobj, menudesc):
        if menuobj is None:
            menuobj = gtk.Menu()
        for itemdesc in menudesc:
            menuitem = gtk.MenuItem(itemdesc[0], True)
            if type(itemdesc[1]) == list:
                # submenu
                submenu = BindableArrangerContextMenu.build_menu(None, itemdesc[1])
                menuitem.set_submenu(submenu)
            else:
                # leaf
                menuitem.userdata = itemdesc[1]
            menuobj.append(menuitem)
        menuobj.show_all()
        return menuobj

    def connect_menuitems (self, submenu=None):
        if not submenu:
            submenu = self
        for menuitem in submenu.get_children()[:]:
            userdata = None
            try:
                userdata = menuitem.userdata
            except AttributeError:
                pass
            if userdata:
                menuitem.connect("activate", self.on_context_menuitem, userdata)
            submenu = menuitem.get_submenu()
            if submenu:
                self.connect_menuitems(submenu)

    def on_button_press (self, w, ev):
        if ev.button == 3:
            self.ctxmenu.popup(None,None,None,ev.button,ev.time)
            return True
        elif ev.button == 1:
            try:
                self.clicked()
            except AttributeError:
                pass
        return False

    def on_context_menuitem (self, w, userdata):
        arranger = userdata
        self.emit("arrangement-activated", userdata)
        return True

    __gsignals__ = {
        "arrangement-activated": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
    }

gobject.type_register(BindableArrangerContextMenu)




# TODO: factor out base class to avoid that long "if" in the UI builder.

class BindableCluster (gtk.EventBox, Bindable):
    """Groups together multiple BindableTops into a unit.
Intended for use in the context of Steam Controller touchpads.
Also re-used for the top-level layout view.

Composed of two parts visible at any one time:
* Grid layout
* List layout
"""
    def __init__ (self, hiasym, label=None, vis=None, init_binds=None):
        Bindable.__init__(self, hiasym, label, vis, init_binds)
        # TODO: In the context of Cluster, init_binds indicates what arrangement to use per layer.
        gtk.EventBox.__init__(self)
        #self._layoutmap = None
        self.clustered_layouts = ClusteredLayouts(self.hiasym)
        self._layoutmap = self.clustered_layouts[0][1]

        self.setup_states()
        self.setup_widget()
        self.setup_signals()

    def setup_states (self):
        self.hiatops = dict()
        self.hiaclusters = dict()

    def get_layoutmap (self):
        return self._layoutmap
    def set_layoutmap (self, val):
        self._layoutmap = val
        self.update_layoutmap()
    layoutmap = property(get_layoutmap, set_layoutmap)

    def setup_widget (self):
        class ui:
            pass
        self.ui = ui
        self.ui.ctxmenu = None
        if self.hiasym:
            self.ui.frame = gtk.Frame()
            self.ui.frame.set_shadow_type(gtk.SHADOW_IN)
            self.ui.lbl_title = gtk.Label(" {} <{}>".format(self.hiasym, self._layoutmap.name))
            self.ui.btn_popup = gtk.Button("...")
            self.ui.ctxmenu = BindableArrangerContextMenu()
            self.ui.row_lbl = gtk.HBox()
            self.ui.row_lbl.pack_start(self.ui.btn_popup, False, False, 0)
            self.ui.row_lbl.pack_start(self.ui.lbl_title, False, False, 0)
            self.ui.row_lbl.show_all()
            self.ui.frame.set_label_widget(self.ui.row_lbl)
        self.ui.top = gtk.VBox()
        #self.ui.grid = gtk.Table(12,12,True)
        self.ui.grid = gtk.Table(1,1,True)
        # Map of hiasym to hiatop, hiatops grouped in this cluster, not
        # necessarily visible or attached to grid.
        # Expect "#c", "#1", "#2", ... "#20".
        listdescr = (str,str) + (str,)*self.nlayers
        self.mdl_listmenu = gtk.ListStore(*listdescr)
        # TODO: should handle changing number of layers.
        for n in range(1,21):
            hiasym = "{}{}".format(self.hiasym, n)
            self.mdl_listmenu.append( (hiasym,hiasym,)+("",)*self.nlayers )
        self.ui.listview = BindableListView(self.mdl_listmenu, self._vis)
        # KLUDGE: pull up all clusterd_layouts hiatops.
        for layoutrow in self.clustered_layouts:
            layoutname, layoutmap = layoutrow
            self.refill_hiatops(layoutmap)

        self.ui.page_grid = gtk.VBox()
        self.ui.page_grid.pack_start(self.ui.grid, True, True, 0)
        self.ui.page_list = gtk.VBox()
        self.ui.top.pack_start(self.ui.page_grid, True, True, 0)
        self.ui.top.pack_start(self.ui.page_list, True, True, 0)

        if self.hiasym:
            self.ui.frame.add(self.ui.top)
            self.add(self.ui.frame)
            self.ui.frame.show()
        else:
            self.add(self.ui.top)

        self.ui.grid.show()
        self.ui.top.show()
        self.show()

        self.on_arrangement_activated(self, self.binds[self._layer] or "Empty")

    def setup_signals (self):
        if self.ui.ctxmenu:
            self.ui.btn_popup.connect('clicked', self.on_btn_popup_clicked)
            self.ui.ctxmenu.connect("arrangement-activated", self.on_arrangement_activated)
        self.ui.listview.connect("bind-assigned", self.on_bind_assigned)
        self.ui.listview.connect("bind-swapped", self.on_bind_swapped)
        self.ui.listview.connect("bind-erased", self.on_bind_erased)
        return

    def update_vis (self):
        for hiasym in self.hiatops:
            hiatop = self.hiatops[hiasym]
            if hiatop.get_visible():
                hiatop.set_vis(self.vis)
        self.ui.listview.set_vis(self.vis)
        return

    def update_layer (self):
        for hiasym in self.hiatops:
            hiatop = self.hiatops[hiasym]
            if hiatop.get_visible():
                hiatop.set_layer(self.layer)
        self.ui.listview.set_layer(self.layer)
        return

    def refill_hiatops (self, layoutmap):
        for hiadata in layoutmap:
            hiasym, lbl, prototyp, x, y, w, h = hiadata
            #hiasym = "{}{}".format(self.hiasym, hiasuffix)
            if not hiasym in self.hiatops:
                #hiatop = BindableTop(hiasym, lbl, self.vis, init_binds=None)
                #self.hiatops[hiasym] = hiatop
                hiatop = self.make_hiatop(hiadata, self.binds, self)
                try:
                    hiatop.connect("cluster-type-changed", self.on_cluster_type_changed)
                except TypeError:
                    pass
            else:
                hiatop = self.hiatops[hiasym]
                # TODO: update bind?
            hiatop.set_vis(self.vis)
            hiatop.show()
        return

    def update_layoutmap (self):
        """Based on .layoutmap, ensure widgets exist and are attached to grid."""
        # Detach all existent hia.
        for ch in self.ui.grid.children():
            self.ui.grid.remove(ch)

        # Resize to initial grid size.
        if self.hiasym:
            # nested cluster.
            self.ui.grid.resize(12,12)
        else:
            # top-level cluster.
            self.ui.grid.resize(1,1)

        # Update frame title.
        if self.hiasym:
            self.ui.lbl_title.set_label(" {} <{}>".format(self.hiasym, self._layoutmap.name))

        # Attach all specified hia.
        self.refill_hiatops(self.layoutmap)
        for hiadata in self.layoutmap:
            hiasym, lbl, prototyp, x, y, w, h = hiadata
            hiatop = self.hiatops[hiasym]
            if isinstance(hiatop, BindableCluster):
                self.ui.grid.attach(hiatop, x, x+w, y, y+h, xpadding=4, ypadding=4)
            else:
                self.ui.grid.attach(hiatop, x, x+w, y, y+h)
        self.ui.grid.show()
        self.ui.top.show()
        self.emit("cluster-type-changed", self.hiasym, self._binds[self._layer])
        self.show()

    def update_binds (self):
        activelayout = None
        bindval = self._binds[self._layer]
        for row in self.clustered_layouts:
            name = row[0]
            if name == bindval:
                activelayout = row[1]
        if activelayout:
            self.set_layoutmap(activelayout)

    def proxy_set_binds (self, hiasym, bindsval):
        hiatop = self.hiatops.get(hiasym, None)
        if not hiatop:
            return
        hiatop.set_binds(bindsval)
        for row in self.mdl_listmenu:
            if row[0] == hiasym:
                for colnum in range(len(bindsval)):
                    row[2+colnum] = bindsval[colnum]

    def on_btn_popup_clicked (self, w, *args):
        if self.ui.ctxmenu:
            self.ui.ctxmenu.popup(None,None,None,1,0)

    def on_arrangement_activated (self, w, arranger, *args):
        if arranger == "ListMenu":
            self.ui.page_grid.hide()
            if not self.ui.listview.get_parent():
                self.ui.page_list.pack_start(self.ui.listview, True, True, 0)
                self.ui.listview.show_all()
            self.ui.page_list.show()
        else:
            if not self.ui.page_grid.get_visible():
                self.ui.page_grid.show()
            if self.ui.page_list.get_visible():
                self.ui.page_list.hide()
        self.emit("bind-assigned", self.hiasym, arranger)

    def on_cluster_type_changed (self, w, hiasym, cluster_type):
        """Nested cluster type changed -- pull in its nested hiatops."""
        hiacluster = self.hiaclusters[hiasym]
        for subsym in hiacluster.hiatops:
            subtop = hiacluster.hiatops[subsym]
            self.hiatops[subsym] = subtop
        self.emit("cluster-type-changed", hiasym, cluster_type)

    def on_bind_assigned (self, w, hiasym, hiabind):
        self.emit("bind-assigned", hiasym, hiabind)
    def on_bind_swapped (self, w, src_hiasym, dst_hiasym):
        self.emit("bind-swapped", src_hiasym, dst_hiasym)
    def on_bind_erased (self, w, hiasym):
        self.emit("bind-erased", hiasym)

#    __gsignals__ = Bindable.__gsignals__
    __gsignals__ = dict(
        [ (k,v) for k,v in Bindable.__gsignals__.iteritems() ]
        +
        [ (k,v) for k,v in {
            "cluster-type-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
          }.iteritems() ]
        )

gobject.type_register(BindableCluster)




class BindableLayoutView (BindableCluster):
    """Special case of BindableCluster at top-level view.
    
Controller interface:
 * set_layoutmap(HidLayoutStore) : set of hiatops and their spatial locations.
 * set_layer(int) : set active layer
 * set_mode(int) : set active mode
 * set_vis(list(bool)) : set visibilities of all layers
"""
    def __init__ (self, vis, layoutmap, bind_store):
        BindableCluster.__init__(self, "", "", vis, layoutmap)
        self.bindstore = bind_store
        self._mode = 0
        self._nvislayers = None
        self.update_binds()

    # inherits property 'vis' from BindableCluster
    # inherits property 'layer' from BindableCluster
    # inherits property 'layoutmap' from BindableCluster

    def get_mode (self):
        return self._mode
    def set_mode (self, val):
        self._mode = val
        self.update_mode()
    mode = property(get_mode, set_mode)

    def get_bindstore (self):
        return self.bindstore
    def set_bindstore (self, val):
        self.bindstore = val
        self.update_bindstore()

    def update_bindstore (self):
        self.update_binds()

    def update_vis (self):
        # Explicitly setting visibility, disable nvislayers auto-calculation.
        self._nvislayers = None
        BindableCluster.update_vis(self)

    def update_mode (self):
        self.update_binds()
        return

    def update_binds (self):
        for hiasym in self.hiatops.keys():
            hiatop = self.hiatops[hiasym]
            #hiabinds = [ lyr.get(hiasym,"") for lyr in self.bindstore[self._mode] ]
            hiabinds = self.bindstore.resolve_binds_markup(hiasym, self._mode)
            if hiatop.get_visible():
                hiatop.set_binds(hiabinds)
        for hiasym in self.hiaclusters:
            hiacluster = self.hiaclusters[hiasym]
            hiabinds = [ lyr.get(hiasym,"") for lyr in self.bindstore[self._mode] ]
            if hiacluster.get_visible():
                hiacluster.set_binds(hiabinds)
                # KLUDGE: Could turn into O(n^2).
                # TODO: subclass all tops as Cluster, where keytop are singleton special case?  Then all set_binds would take (hiasym, bindval) parameters.
                for subsym in hiacluster.hiatops:
                    # TODO: fix, would only allow one level of nesting.
                    #subval = [ lyr.get(subsym,"") for lyr in self.bindstore[self._mode] ]
                    subval = self.bindstore.resolve_binds_markup(subsym, self._mode)
                    hiacluster.proxy_set_binds(subsym, subval)
        return

    def update_layoutmap (self):
        BindableCluster.update_layoutmap(self)
        self.update_binds()

    def on_bind_assigned (self, w, hiasym, hiabind):
        logger.debug("doing on_bind_assigned(layer=%d, sym=%r, val=%r)" % (self.layer, hiasym, hiabind))
        self.bindstore[self.mode][self.layer][hiasym] = hiabind
        self.update_binds()
        return
    def on_bind_swapped (self, w, src_hiasym, dst_hiasym):
        logger.debug("doing on_bind_swapped(layer=%d, asym=%r, bsym=%r" % (self.layer, src_hiasym, dst_hiasym))
        srcbind = self.bindstore[self.mode][self.layer].get(src_hiasym,None)
        dstbind = self.bindstore[self.mode][self.layer].get(dst_hiasym,None)
        self.bindstore[self.mode][self.layer][src_hiasym] = dstbind
        self.bindstore[self.mode][self.layer][dst_hiasym] = srcbind
        self.update_binds()
        return
    def on_bind_erased (self, w, hiasym):
        logger.debug("doing on_bind_erased(layer=%d, sym=%r" % (self.layer, hiasym))
        del self.bindstore[self.mode][self.layer][hiasym]
        self.update_binds()
        return






implicit_layouts = HidLayouts()
implicit_layouts.build_from_legacy_store()




class BindableLayoutSelectors (gtk.VBox):
    """Selectors (controls) for BindableLayoutView in a single widget.
Default selector, is separate so a custom control may be used instead.

Signals:
 * layout-changed(str) : when layout has been chosen, name of layout.
 * mode-changed(int) : when mode has been chosen, index of mode.
 * layer-changed(int) : when layer has been chosen, index of layer.

External controls, to trigger selection controls with a single primitive:
 * frob_layout(str)
 * frob_mode(int)
 * frob_layer(int)

N.B. without the frob_*(), changing selectors would involve something like
instance.sel_layer.buttons[2].activate()
"""
    def __init__ (self, model_layouts, model_modes, model_layers):
        gtk.VBox.__init__(self)
        self.mdl_layouts = model_layouts
        #self.mdl_modes = model_modes
        self.mdl_modes = gtk.ListStore(str,str)
        self.mdl_layers  = model_layers
        self.setup_widget()
        self.setup_signals()

    def get_layouts_model (self):
        return self.mdl_layouts
    def set_layouts_model (self, val):
        self.mdl_layouts = val
    layouts_model = property(get_layouts_model, set_layouts_model)

    def get_modes_model (self):
        return self.mdl_mode
    def set_modes_model (self, val):
        #self.mdl_modes = val
        self.mdl_modes.clear()
        for row in val:
            self.mdl_modes.append(tuple(row))
    modes_model = property(get_modes_model, set_modes_model)

    def get_layers_model (self):
        return self.mdl_layers
    def set_layers_model (self, val):
        self.mdl_layers = val
    layers_model = property(get_layers_model, set_layers_model)

    def frob_layout (self, val):
        """Adjust layout with a single primitive type."""
        n = None
        for i in range(len(self.mdl_layouts)):
            if (self.mdl_layouts[i][0] == val) or (i == val):
                n = i
        if n is not None:
            self.ui.sel_layout.set_active(n)
    def frob_mode (self, val):
        """Adjust mode with a single primitive type."""
        # TODO: if val isa str
        n = None
        for i in range(len(self.mdl_modes)):
            if (i == val):
                n = i
        if n is not None:
            self.ui.sel_mode.buttons[n].activate()
    def frob_layer (self, val):
        """Adjust layer with a single primitive type."""
        n = int(val)
        self.ui.sel_layer.buttons[n].activate()

    def setup_widget (self):
        self.ui = DumbData()

        # Row with layout selector.
        self.ui.sel_layout = self.LayoutSelectorWidget(self.mdl_layouts)
        self.ui.lbl_layout = gtk.Label("Layout:")
        self.ui.row_layout = gtk.HBox()
        self.ui.row_layout.pack_start(self.ui.lbl_layout, False, False, 0)
        self.ui.row_layout.pack_start(self.ui.sel_layout, False, False, 0)

        # Row with mode selector.
        #self.ui.sel_mode = self.ModeSelectorWidget(self.mdl_modes)
        self.ui.sel_mode = self.ModeSelectorWidget(self, self.mdl_modes)

        # Row with layer selector.
        self.ui.sel_layer = self.LayerSelectorWidget()

        self.pack_start(self.ui.row_layout, False, False, 0)
        self.pack_start(self.ui.sel_mode, False, False, 0)
        self.pack_start(self.ui.sel_layer, False, False, 0)

        self.ui.row_layout.show_all()
        self.ui.sel_mode.show_all()
        self.ui.sel_layer.show_all()

        # Initial layout.
        self.ui.sel_layout.set_active(0)
        #idx = self.ui.sel_layout.get_active()
        #val = self.mdl_layouts[idx][0]

    def setup_signals (self):
        pass

    def LayoutSelectorWidget (self, mdl_layouts):
        # Combo (drop) list.
        selector = gtk.ComboBox(mdl_layouts)
        selector.cell_layout = gtk.CellRendererText()
        selector.pack_start(selector.cell_layout)
        selector.add_attribute(selector.cell_layout, 'text', 0)
        selector.set_active(0)
        selector.connect("changed", self.on_layout_changed)
        return selector

    def on_layout_changed (self, w, *args):
        idx = w.get_active()
        data = self.mdl_layouts[idx]
        val = data[0]
        #self.activename = val   # trigger update_activehid()
        #self.activehid = self.all_layouts[val]
        #self.hidview.set_layoutmap(self.activehid)
        # TODO: propagate binds to newly revealed clusters.
        #self.show()
        self.emit("layout-changed", val)

    class ModeSelectorWidget (gtk.Frame):
        def __init__ (self, parent, mdl_modes):
            gtk.Frame.__init__(self, "Mode")
            self._parent = parent
            self.mdl = mdl_modes
            self.row = gtk.HBox()
            self.btnbox = gtk.HButtonBox()
            self.buttons = None

            self.mdl.connect("row-changed", self.on_data_changed)
            self.mdl.connect("row-deleted", self.on_data_changed)
            self.mdl.connect("row-inserted", self.on_data_changed)

            self.rebuild_buttons()
            self.row.pack_start(self.btnbox, expand=False)
            self.add(self.row)

        def rebuild_buttons (self):
            w = self
            if w.buttons:
                for btn in w.buttons:
                    w.btnbox.remove(btn)
            w.buttons = list()
            for modeid in range(len(w.mdl)):
                # Radio group is first button; make leader if no buttons.
                mode = w.buttons[0] if w.buttons else None
                lbl = w.mdl[modeid][0]  # first column => displayed name.
                btn = gtk.RadioButton(mode, lbl)
                btn.modenum = modeid
                btn.connect('toggled', self.on_mode_toggled)
                w.buttons.append(btn)
                w.btnbox.add(btn)
            w.row.show_all()
            return

        def on_data_changed (self, w, mdl, *args):
            self.rebuild_buttons()

        def on_mode_toggled (self, w, *args):
            if w.get_active():
                modenum = w.modenum
                #self.emit("mode-changed", modenum)
                self._parent.emit("mode-changed", modenum)

    def LayerSelectorWidget (self):
        selector = gtk.Frame("Layer")
        selector.mdl = self.mdl_layers
        selector.row = gtk.HBox()
        selector.btnbox = gtk.HButtonBox()
        selector.buttons = list()

        for layerinfo in selector.mdl:
            # Group leader is first button; use None to become group leader.
            lyrnum, lbl = layerinfo[0], layerinfo[1]
            grp = selector.buttons[0] if selector.buttons else None
            btn = gtk.RadioButton(grp, lbl)
            btn.layernum = lyrnum
            btn.connect("toggled", self.on_layer_toggled)
            selector.buttons.append(btn)
            selector.btnbox.add(btn)

        selector.row.pack_start(selector.btnbox, expand=True)
        selector.add(selector.row)
        return selector

    def on_layer_toggled (self, w, *args):
        # Effective visibility <- current layer and number of visible layers.
        if w.get_active():
            layernum = w.layernum
            self.emit("layer-changed", layernum)

    __gsignals__ = {
        "layout-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        "layer-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        "mode-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        }

gobject.type_register(BindableLayoutSelectors)




class BindableLayoutWidget (gtk.VBox):
    """Controller wrapper to BindableLayoutView.

 * set_nvislayers(int) : convenience function to automatically determine layer visibilties based on active layers and nearest power-of-two layer.
"""
    def __init__ (self, all_layouts, init_layout=None, mdl_modes=None, mdl_layers=None, bindstore=None):
        gtk.VBox.__init__(self)
        self._bindstore = bindstore
        self._layer = 0
        self._vis = [ False ] * len(bindstore[0])
        self._vis[0] = True
        self._nvislayers = None
        self.mdl_modes = mdl_modes
        self.mdl_layers = mdl_layers
        if all_layouts is None:
            all_layouts = implicit_layouts
        self.all_layouts = all_layouts

        self.setup_state()
        self.setup_widget()
        self.setup_signals()

        if init_layout is not None:
            self.ui.selectors.frob_layout(init_layout)
            self.ui.selectors.emit("layout-changed", init_layout)

        self.update_modelist()

    def setup_state (self):
        self._activename = None
        self._activehid = None
        self._modelist = gtk.ListStore(str,str)
        self._modelist.append( ("Global", None) )

    def setup_widget (self):
        class ui:
            pass
        self.ui = ui

        # Primary bindables view.
        #self.ui.hidview = BindableCluster("")
        #self.ui.hidview = BindableLayoutView(self.vis, implicit_layouts['en_US (pc104)'], self._bindstore)
        #emptylayout = HidLayoutStore("empty")
        #emptylayout.append( None, ("empty", "empty", "key", 0, 0, 1, 1) )
        self.ui.hidview = BindableLayoutView(self.vis, None, self._bindstore)

        self.ui.selectors = BindableLayoutSelectors(self.all_layouts, self.mdl_modes, self.mdl_layers)
        self.ui.selectors.show_all()

        self.ui.hidview.show()

        self.pack_start(self.ui.selectors, False, False, 0)
        self.pack_start(self.ui.hidview, False, False, 0)

    def on_layout_changed (self, w, layoutname):
        self.set_active(layoutname)
    def on_mode_changed (self, w, modenum):
        self.set_mode(modenum)
    def on_layer_changed (self, w, layernum):
        self.set_layer(layernum)

    def setup_signals (self):
        self.ui.selectors.connect("layout-changed", self.on_layout_changed)
        self.ui.selectors.connect("mode-changed", self.on_mode_changed)
        self.ui.selectors.connect("layer-changed", self.on_layer_changed)
        return

    def get_mode (self):
        return self_mode
    def set_mode (self, val):
        self._mode = val
        self.update_mode()
    mode = property(get_mode, set_mode)

    def update_mode (self):
        self.ui.hidview.set_mode(self._mode)

    def get_layer (self):
        return self._layer
    def set_layer (self, val):
        self._layer = val
        self.update_layer()
    layer = property(get_layer, set_layer)

    def update_layer (self):
        self.ui.hidview.set_layer(self._layer)
        self.update_nvislayers()

    def get_nvislayers (self):
        return self._nvislayers
    def set_nvislayers (self, val):
        self._nvislayers = val
        self.update_nvislayers()
    nvislayers = property(get_nvislayers, set_nvislayers)

    def update_nvislayers (self):
        if not self._nvislayers:
            effvis = [ (x==self._layer) for x in range(len(self.vis)) ]
            self.set_vis(effvis)
            return
        nlayers = len(self.bindstore[0]) if self.bindstore else 1
        alayer = self.ui.hidview.layer   # Currectly active layer.
        vlayers = self._nvislayers       # Visible layers.
        # the layer corresponding to the alignment point.
        baselayer = int(alayer / vlayers) * vlayers
        temp = list(self.vis)
        for ofs in range(len(temp)):
            # Make visible within the range baselayer:baselayer+n
            temp[ofs] = (ofs >= baselayer and ofs < baselayer+vlayers)
        #BindableCluster.set_vis(self, temp)
        self.ui.hidview.set_vis(temp)

    def get_bindstore (self):
        return self._bindstore
    def set_bindstore (self, val):
        self._bindstore = val
        self.update_bindstore()
    bindstore = property(get_bindstore, set_bindstore)

    def update_bindstore (self):
        self.ui.hidview.set_bindstore(self._bindstore)
        self.ui.hidview.update_binds()

    def get_modelist (self):
        return self.mdl_modes
    def set_modelist (self, val):
        self.mdl_modes = val
        self.update_modelist()
    modelist = property(get_modelist, set_modelist)
    def update_modelist (self):
        # Set up fallback web.
        lu_modes = dict([(self.mdl_modes[rownum][0],rownum) for rownum in range(len(self.mdl_modes)) ])
        for k,fall in self.mdl_modes:
            self.bindstore[lu_modes[k]].fallthrough = lu_modes.get(fall, None)
        self.ui.selectors.set_modes_model(self.mdl_modes)  # this call actually resolves to a ListStore copy.
        return

    def get_activename (self):
        return self._activename
    def set_activename (self, val):
        self._activename = val
        self._activehid = self.all_layouts[self._activename]
        self.update_activehid()
    activename = property(get_activename, set_activename)

    def get_activehid (self):
        return self._activehid
    def set_activehid (self, val):
        self._activename = None
        self._activehid = val
        self.update_activehid()
    activehid = property(get_activehid, set_activehid)

    def update_activehid (self):
        self.ui.hidview.set_layoutmap(self._activehid)

    def get_layouts (self):
        return self.all_layouts
    def set_layouts (self, val):
        self.all_layouts = val
    layouts = property(get_layouts, set_layouts)

    # Backwards-compat
    # TODO: elide later.
    def get_active (self):
        return self.activename
    def set_active (self, val):
        self.activename = val
        self.activehid = self.all_layouts[val]
        # TODO: update display
        #self.rebuild_display()
        self.update_activehid()
    active = property(get_active, set_active)

    def get_vis (self):
        return self._vis
    def set_vis (self, val):
        self._vis = val
        self._nvislayers = None
        self.update_vis()
    vis = property(get_vis, set_vis)

    def update_vis (self):
        self.ui.hidview.set_vis(self.vis)
        return




########################
## Command set source ##
########################

class CommandPackStore (gtk.TreeStore):
    def __init__ (self, packname=None, raw_data=None):
        # Data tuples = ( cmd_id_number, cmd_name, display_text, tooltip_text )
        gtk.TreeStore.__init__(self, int, str, str, str)
        self._cursor = None
        self.packname = packname
        if raw_data is None:
            # Default initial entry for unbind.
            gtk.TreeStore.append(self, None, (0, "", "(unbind)", ""))
        else:
            self.decode(raw_data)

    def begin_group (self, entry):
        rowdata = entry
        if not isinstance(entry, tuple):
            rowdata = (-1, "", entry, "")
        cursor = gtk.TreeStore.append(self, self._cursor, rowdata)
        self._cursor = cursor

    def end_group (self):
        if self._cursor:
            self._cursor = self.iter_parent(self._cursor)
        return

    def append (self, entry, *more):
        if isinstance(entry, tuple):
            return gtk.TreeStore.append(self, self._cursor, entry)
        else:
            return gtk.TreeStore.append(self, entry, *more)

    def decode (self, raw_data):
        tupleiter = raw_data.__iter__()
        treeiter = self.get_iter_root()
        stack = []
        while stack or tupleiter:
            try:
                entry = tupleiter.next()
            except StopIteration:
                if stack:
                    tupleiter, treeiter = stack[-1]
                    del stack[-1]
                    continue
                else:
                    break
            rowtuple, subtree = entry
            rowiter = self.append(treeiter, rowtuple)
            if subtree:
                stack.append( (tupleiter, treeiter) )
                treeiter = rowiter
                tupleiter = subtree.__iter__()

    def encode (self):
        enc = dict()
        enc['.class'] = self.__class__.__name__
        enc['packname'] = self.packname

        ser = []
        stack = []
        treeiter = self.get_iter_root()
        while stack or treeiter:
            #ser.append( tuple(self[self.get_path(treeiter)]) )
            subtree = None
            if not treeiter:
                # resume from stack.
                subtree = ser
                treeiter, ser = stack[-1]
                del stack[-1]
            elif self.iter_has_child(treeiter):
                # save state, recurse.
                stack.append( (treeiter, ser) )
                ser = []
                treeiter = self.iter_children(treeiter)
                continue

            rowtuple = tuple(self[self.get_path(treeiter)])
            entry = (rowtuple, subtree)
            ser.append(entry)
            treeiter = self.iter_next(treeiter)
        enc['raw_data'] = ser
        return enc

    def __repr__ (self):
        return repr(self.encode())


class CommandInfo (object):
    """Base class for command pack source."""
    REGISTRY = {}
    def __init__ (self, path, raw_data=None):
        self._path = path
        self._cmdpack = None
        self._modelist = None
        self._packname = None
        if raw_data is None:
            self.build()
        else:
            self.decode(raw_data)
    def build (self):
        pass
    def get_cmdpack (self):
        return self._cmdpack
    def set_cmdpack (self, val):
        self._cmdpack = val
    cmdpack = property(get_cmdpack, set_cmdpack)
    def get_modelist (self):
        return self._modelist
    def set_modelist (self, val):
        self._modelist = val
    modelist = property(get_modelist, set_modelist)
    def get_packname (self):
        return self._packname
    def set_packname (self, val):
        self._packname = val
    packname = property(get_packname, set_packname)
    @staticmethod
    def register (classobj):
        if not classobj in CommandInfo.REGISTRY:
            CommandInfo.REGISTRY[classobj] = classobj
        return classobj
    @staticmethod
    def from_uri (uri):
        """Main factory function."""
        for packtype in CommandInfo.REGISTRY:
            factory = packtype
            if factory.is_acceptable(uri):
                inst = factory(uri)
                return inst
        raise NameError("No factory for command pack source {!r}".format(uri))

    def decode (self, raw_data):
        temp = raw_data['cmdpack']
        del temp['.class']
        self._cmdpack = CommandPackStore(**temp)
        self._modelist = gtk.ListStore(str,str)
        for (a,b) in raw_data['modelist']:
            self._modelist.append( (a,b) )
        self._packname = raw_data['packname']

    def encode (self):
        enc = dict()
        enc['.class'] = self.__class__.__name__
        enc['path'] = self._path
        enc['raw_data'] = raw_data = dict()
        raw_data['cmdpack'] = self._cmdpack
        raw_data['modelist'] = [ tuple(x) for x in self._modelist ] if self._modelist else None
        raw_data['packname'] = self.packname
        return enc

    def __repr__ (self):
        return repr(self.encode())

@CommandInfo.register
class CommandInfo_builtin (CommandInfo):
    @staticmethod
    def is_acceptable (uri):
        return (uri is None)

    def build (self):
        modelist = gtk.ListStore(str,str)
        modelist.append( ("Global", None) )
        modelist.append( ("Menu", "Global") )
        modelist.append( ("Game", "Global") )
        self._modelist = modelist

        cmdpack = CommandPackStore("(builtin)")
        cmdid, grpid = 1, 1

        grp = cmdpack.append(None, (grpid, "", "Shifter", "") ); grpid += 1
        cmdpack.append(grp, (cmdid, "^1", "^1", "")); cmdid += 1
        cmdpack.append(grp, (cmdid, "^2", "^2", "")); cmdid += 1
        cmdpack.append(grp, (cmdid, "^3", "^3", "")); cmdid += 1
        cmdpack.append(grp, (cmdid, "^4", "^4", "")); cmdid += 1
        cmdpack.append(grp, (cmdid, "^5", "^5", "")); cmdid += 1

        grp = cmdpack.append(None, (grpid, "", "Menu", "") ); grpid += 1
        cmdpack.append(grp, (cmdid, "Pause", "Pause", "")); cmdid += 1
        cmdpack.append(grp, (cmdid, "Minimize", "Minimize", "")); cmdid += 1

        grp = cmdpack.append(None, (grpid, "", "Game", "") ); grpid += 1
        cmdpack.append(grp, (cmdid, "Up", "Up", "")); cmdid += 1
        cmdpack.append(grp, (cmdid, "Down", "Down", "")); cmdid += 1
        cmdpack.append(grp, (cmdid, "Left", "Left", "")); cmdid += 1
        cmdpack.append(grp, (cmdid, "Right", "Right", "")); cmdid += 1
        cmdpack.append(grp, (cmdid, "Jump", "Jump", "")); cmdid += 1
        cmdpack.append(grp, (cmdid, "Action", "Action", "")); cmdid += 1

        self._cmdpack = cmdpack


class CommandPackView (gtk.VBox):
    """View of the command pack.

static method 'make_model()' for generating a suitable TreeStore expected by this widget.
"""
    # Expected to rarely change, so model signals are ignored and instead set_model triggers refreshing view.
    def __init__ (self, mdl):
        gtk.VBox.__init__(self)
        self._mdl = mdl
        self._packname = None
        self.setup_state()
        self.setup_widget()
        self.setup_dnd()

    def get_model (self):
        return self._mdl
    def set_model (self, mdl=None):
        if mdl is not None:
            self._mdl = mdl
            self.ui.treeview.set_model(mdl)
            try:
                self._packname = self._mdl.packname
            except AttributeError:
                self._packname = None
            self.update_view()
    model = property(get_model, set_model)

    def update_view (self):
        if self._packname:
            self.ui.treecols[0].set_title(self._packname)
        else:
            self.ui.treecols[0].set_title("command")
        return

    def setup_state (self):
        return

    def setup_widget (self):
        self.ui = DumbData()
        self.ui.sclwin = gtk.ScrolledWindow()

        self.ui.treeview = gtk.TreeView(self._mdl)
        self.ui.treecols = []
        self.ui.treecelltxt = gtk.CellRendererText()
        col0 = gtk.TreeViewColumn("command", self.ui.treecelltxt, text=2)
        self.ui.treecols.append(col0)
        for col in self.ui.treecols:
            self.ui.treeview.append_column(col0)

        self.ui.sclwin.add(self.ui.treeview)
        self.add(self.ui.sclwin)
        self.show_all()

    def setup_dnd (self):
        """One-time setup, GTK Drag-and-Drop."""
        # self as DnD source: bind.
        drag_targets = [
          (str(DndOpcodes.BIND), gtk.TARGET_SAME_APP, DndOpcodes.BIND),
        ]
        drag_actions = gtk.gdk.ACTION_COPY
        self.ui.treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, drag_targets, drag_actions)
        self.ui.treeview.connect("drag-data-get", self.on_drag_data_get)

        # self as DnD destination: erase.
        drop_targets = [
          (str(DndOpcodes.UNBIND), gtk.TARGET_SAME_APP, DndOpcodes.UNBIND),
        ]
        drop_actions = gtk.gdk.ACTION_COPY
        self.ui.treeview.enable_model_drag_dest(drop_targets, drop_actions)
        self.ui.treeview.connect("drag-data-received", self.on_drag_data_received)
    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        # is DnD source.
        treesel = w.get_selection()
        mdl, pathsels = treesel.get_selected_rows()
        firstsel = pathsels[0]
        selrow = mdl[firstsel]
        cmdname = selrow[1]
        if info == DndOpcodes.BIND:
            # dragged from command set.
            logger.debug("cmdpack: bind with %s" % (cmdname,))
            seldata.set(seldata.target, 8, str(cmdname))
            return True
        return False
    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        logger.debug("cmdpack on_drag_data_received")
        if info == DndOpcodes.UNBIND:
            hiasym = seldata.data
            logger.debug("cmdpack: unbind %s" % (hiasym,))
            return True
        return False

    @staticmethod
    def make_model ():
        # Data tuples = ( cmd_id_number, cmd_name, display_text, tooltip_text )
        store = CommandPackStore()
        store.append(None, (0, "", "(unbind)", None))
        return store




# Testing standalone window.

class HidLayoutWindow (gtk.Window):
    def __init__ (self):
        gtk.Window.__init__(self)
        self.set_size_request(640, 480)
        self.resize(720, 680)
        self.layout = gtk.VBox()
        self.add(self.layout)

        #inpdescr = InpDescrModel(8)
        #dispstate = InpDisplayState(inpdescr)
        #hidw = HidLayoutWidget(dispstate, implicit_layouts)
        #self.layout.add(hidw)
        #hidw.connect("key-selected", self.on_key_selected)
        #hidw.connect("bind-changed", self.on_bind_changed)

        self.bindstore = BindStore(3,2)
        hidw = BindableLayoutWidget(implicit_layouts, None, self.bindstore)
        self.layout.add(hidw)

        self.connect('delete-event', self.on_delete)

    def on_delete (self, w, *args):
        gtk.main_quit()

    def on_key_selected (self, w, inpsym, *args):
        logger.debug("Selected inpsym '%s'" % inpsym)

    def on_bind_changed (self, w, keytop, *args):
        logger.debug("Bind changed for %r" % keytop)

    def run (self):
        self.show_all()
        #self.show()
        gtk.mainloop()


if __name__ == "__main__":
    x = HidLayoutWindow()
    x.run()

