#!/usr/bin/env python
# vim: expandtab shiftwidth=4 :

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
# BindStore = dict of BindGroup
#  + BindGroup = list of BindLayer
#    + BindLayer = list of BindEntry
#      + BindEntry = dict of hiasym => str
#
# interface pattern:
# bindmap[group][layer][hiasym]  =>  str: binding for hiasym in group and layer
# bindmap[group][layer]  =>  dict: all hiasyms for group and layer
# bindmap[group]  =>  list: all layers for group


class BindLayer (dict):
    """dict, hiasym => str
 key = hiasym
 value = binding
"""
    pass
    def __copy__ (self):
        retval = dict(self)
        return retval

class BindGroup (object):
    """list of BindLayer, one per layer available.
 index = layer number
 value = BindLayer

"""
    def __init__ (self, nlayers=1, fallthrough=None):
        """
 nlayers: int = number of layers to start with.
 fallthrough: BindGroup = another BindGroup to use if resolution fails.
"""
        self.layers = list()
        self.fallthrough = fallthrough
        self.resize_layers(nlayers)
        
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
        retval = BindGroup(self.nlayers, self.fallthrough)
        for lyridx in range(self.nlayers):
            retval[lyridx] = self[lyridx].__copy__()
        return retval
    # Delegate sequence operators to .layers
    def __len__ (self):             return len(self.layers)
    def __getitem__ (self, key):
        if isinstance(key, slice):
            # slicing.
            sliced = self.layers.__getitem__(key)
            retval = BindGroup(len(sliced), None)
            retval.layers = sliced
            return retval
        else:
            return self.layers.__getitem__(key)
    def __missing__ (self, key):    return self.layers.__missing__(key)
    def __iter__ (self):            return self.layers.__iter__()
    def __setitem__ (self, key, value): self.layers[key] = value
    def __setslice__ (self, i, j, seq): self.layers.__setslice__(i,j,seq)
    def __delslice__ (self, i, j):      self.layers.__delslice__(i,j)

class BindStore (object):
    """list of BindGroup, one per group available.
 index = group number
 value = BindGroup
"""
    def __init__ (self, ngroups=1, nlayers=1):
        self.groups = []
        self.ngroups = ngroups
        self.nlayers = nlayers
        self.resize_layers(self.nlayers)
        self.resize_groups(self.ngroups)
    def resize_groups (self, ngroups):
        self.ngroups = ngroups
        while len(self.groups) < self.ngroups:
            self.groups.append(BindGroup(self.nlayers))
        while len(self.groups) > self.ngroups:
            del self.groups[-1]
        return
    def resize_layers (self, nlayers):
        self.nlayers = nlayers
        for bindgrp in self.groups:
            bindgrp.resize_layers(self.nlayers)
        return
    def __copy__ (self):
        retval = BindStore(self.ngroups, self.nlayers)
        copymap = dict()    # map fallthrough links.
        for grpidx in range(len(self.groups)):
            retval.groups[grpidx] = self.groups[grpidx].__copy__()
            copymap[self.groups[grpidx]] = retval[grpidx]
        # Redirect remapped fallthroughs.
        for grp in retval.groups:
            if grp.fallthrough:
                grp.fallthrough = copymap[grp.fallthrough]
        return retval
    # Delegate sequence operators to .groups
    def __len__ (self):             return len(self.groups)
    def __getitem__ (self, key):    return self.groups.__getitem__(key)
    def __missing__ (self, key):    return self.groups.__missing__(key)
    def __iter__ (self):            return self.groups.__iter__()
    def __setitem__ (self, key, value): self.groups.__setitem__(key, value)
    def __setslice__ (self, i, j, seq): self.groups.__setslice__(i,j,seq)
    def __delslice__ (self, i, j):      self.groups.__delslice__(i,j)




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
    def __init__ (self, hiasym, label=None, vis=None, initbinds=None):
        self._hiasym = hiasym
        self._label = label
        self._layer = 0     # Currently active layer.
        if vis is None:
            vis = [ True ]
        # TODO: change to tuple?
        self._vis = vis  # List of bool, visibility of each layer; len is total number of layers.
        if initbinds is None:
            initbinds = (None,)*len(self._vis)
        self._binds = initbinds     # Tuple of str, one per layer.  Tuple-ness as the grouping is an intrinsic property (immutability of the sequence).

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

    def make_hiatop (self, descr, initbinds=None, parent_cluster=None):
        hiasym, hialbl, hiatype, x, y, w, h = descr
        hiatop = None
        if hiatype == "cluster":
            hiatop = BindableCluster(hiasym, hialbl, self.vis, initbinds)
            if parent_cluster:
                parent_cluster.hiatops[hiasym] = hiatop
                parent_cluster.hiaclusters[hiasym] = hiatop
        elif hiatype == "key":
            hiatop = BindableTop(hiasym, hialbl, self.vis, initbinds)
            if parent_cluster:
                parent_cluster.hiatops[hiasym] = hiatop
        else:
            pass
        return hiatop


class BindableTop (gtk.Button, Bindable):
    """The bindable atom, metaphor for keyboard key top.

Supports drag-and-drop.  Semantics:
 * from command set to btop - assign binding : bind-assigned(hiasym, bindval)
 * from btop to btop - swap binding : bind-swaped(src-hiasym, dst-hiasym)
 * from btop to command set - erase binding : bind-erased(src-hiasym)
"""
    def __init__ (self, hiasym, label=None, vis=None, initbinds=None):
        Bindable.__init__(self, hiasym, label, vis, initbinds)
        gtk.Button.__init__(self)
        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()
#        self.connect("map", self.on_map)
#        self.setup_dnd()
#        self.update_display()

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
        self.refstyle = temp.get_style().copy()
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

#        self.connect("map", self.on_map)
#        self.setup_dnd()
#        self.update_display()

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
        self.ui.lbl.set_markup(str(toplabel))

    def update_layer (self):
        """Layer updated; repaint highlights."""
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
        #self.connect("drag-end", self.on_drag_end)

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
            logger.debug("hiatop: try unbind  %s" % self.inpsym)
            seldata.set(seldata.target, 8, str(self.inpsym))
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



class BindableListStore (gtk.ListStore):
    def __init__ (self, nlayers):
        pass


class BindableListView (gtk.ScrolledWindow):
    """TreeView of list-based cluster types.
    
Heavily reliant on clusters acting as proxy (hiatop to hiacluster to hiaview, and backwards) to maintain consistency.

Given a list of BindableTops to keep track of (watch).

"""
#    def __init__ (self, hiasym, label=None, nlayers=None, initbinds=None):
    def __init__ (self, tracktops):
        # Based on ScrollWindowed, containing a TreeView
        gtk.ScrolledWindow.__init__(self)

        #Bindable.__init__(self, "-", "", 1, {})

        self._tracktops = tracktops
        self.mdl = None

        self.refstyle = gtk.Button().get_style().copy()

        self.setup_states()
        self.setup_widgets()
        self.setup_dnd()

#        self.conn_display_adjusted = self.dispstate.connect("display-adjusted", self.on_display_adjusted)
#        self.conn_bind_changed = self.dispstate.inpdescr.connect("bind-changed", self.on_inpdescr_bind_changed)
#        self.conn_label_changed = self.dispstate.inpdescr.connect("label-changed", self.on_inpdescr_label_changed)

        self.show_all()
#        self.update_display()

    def setup_states (self):
        pass

    def get_nlayers (self):
        try:
            return self._tracktops[0].nlayers
        except IndexError:
            return 1
    nlayers = property(get_nlayers)

    def get_layer (self):
        return self._tracktops[0].layer
    layer = property(get_layer)

    def get_vis (self):
        return self._tracktops[0].vis
    vis = property(get_vis)

    def get_tracktops (self):
        return self._tracktops
    def set_tracktops (self, val):
        self._tracktops = val
    tracktops = property(get_tracktops, set_tracktops)

    def update_layer (self):
        for lyridx in range(self.nlayers):
            renderer = self.renderers[lyridx]
            bgrgb = self.refstyle.bg[gtk.STATE_NORMAL]
            if lyridx == self.layer:
                bgrgb = self.refstyle.base[gtk.STATE_NORMAL]
            renderer.props.background = bgrgb
            self.bindcols[lyridx].set_expand(True)
        self.queue_draw()
        return

    def update_vis (self):
        for lyridx in range(self.nlayers):
            self.bindcols[lyridx].set_visible(bool(self.vis[lyridx]))
        return

    def setup_widgets (self):
        # Data model.
        nlayers = 1
        try:
            nlayers = self.tracktops[0].nlayers
        except IndexError:
            pass
        cols = (str,str,)  +  (str,) * nlayers
        self.mdl = gtk.ListStore(*cols)
        for hiatop in self.tracktops:
            hiasym = hiatop.hiasym
            hialbl = hiatop.toplabel
            hiabinds = hiatop.binds
            if hialbl is None:
                hialbl = hiasym
            rowdata = (hiasym, hialbl,) + hiabinds
            self.mdl.append(rowdata)

        # The TreeView
        self.treeview = gtk.TreeView(self.mdl)
        self.rendertext = gtk.CellRendererText()
        nlayers = self.nlayers
        self.col0 = gtk.TreeViewColumn("#", self.rendertext, text=1)
        self.treeview.append_column(self.col0)
        self.bindcols = []
        self.renderers = []
        for i in range(nlayers):
            title = "bind%d" % i
            renderer = gtk.CellRendererText()
            renderer.props.background = "gray"
            datacol = i+2
            bind_col = gtk.TreeViewColumn(title, renderer, markup=datacol)
            self.bindcols.append(bind_col)
            self.renderers.append(renderer)
            self.treeview.append_column(bind_col)

        self.add(self.treeview)  # and not with viewport.

    def setup_dnd (self):
        """Set up drag-and-drop."""
        # DnD Source
        dnd_targets = [
          (str(DndOpcodes.REORDER), gtk.TARGET_SAME_WIDGET, DndOpcodes.REORDER),
          (str(DndOpcodes.UNBIND), gtk.TARGET_SAME_WIDGET, DndOpcodes.UNBIND),
          (str(DndOpcodes.SWAP), gtk.TARGET_SAME_APP, DndOpcodes.SWAP),
        ]
        dnd_actions = gtk.gdk.ACTION_COPY
        self.treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, dnd_targets, dnd_actions)
        self.treeview.connect("drag-data-get", self.on_drag_data_get)
        self.treeview.connect("drag-end", self.on_drag_end)

        # DnD Destination
        dnd_targets = [
          (str(DndOpcodes.REORDER), gtk.TARGET_SAME_WIDGET, DndOpcodes.REORDER),
          (str(DndOpcodes.BIND), gtk.TARGET_SAME_APP, DndOpcodes.BIND),
          (str(DndOpcodes.SWAP), gtk.TARGET_SAME_APP, DndOpcodes.SWAP),
        ]
        dnd_actions = gtk.gdk.ACTION_COPY
        self.treeview.enable_model_drag_dest(dnd_targets, dnd_actions)
        self.treeview.connect("drag-data-received", self.on_drag_data_received)

        self.droppath = None
        self.dropunbind = None

    def on_drag_end (self, w, ctx, *args):
        logger.debug("hidmenulist drag-end")
        if self.dropunbind:
            logger.debug("drop-unbind inpsym %s" % self.dropunbind)
            self.set_bind(self.dropunbind, "")
            self.dropunbind = None
        return True

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
            #data = repr(firstpath)
            pass
        elif info == DndOpcodes.UNBIND:
            logger.debug("hidmenulist drag-data-get unbind")
            data = hiasym
            self.dropunbind = hiasym
        elif info == DndOpcodes.SWAP:
            logger.debug("hidmenulist drag-data-get swap")
            data = hiasym
        if data is not None:
            seldata.set(seldata.target, 8, data)

    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        # As DnD destination, determine what was dragged in.
        srcw = ctx.get_source_widget()
        droppath = self.droppath
        dropinfo = w.get_dest_row_at_pos(x,y)
        destpath, destpos = None, None
        if dropinfo:
            destpath, destpos = dropinfo
        else:
            # all cases rely on dropinfo being valid.
            return False

        if info == DndOpcodes.REORDER:
#            logger.debug("hidmenulist reorder")
#            # Reordering internally, seldata.data is tree path.
#            encoded = seldata.data
#            srcpath = ast.literal_eval(encoded)
#            func, bias = {
#                gtk.TREE_VIEW_DROP_INTO_OR_BEFORE: (self.drag_bind, 0),
#                gtk.TREE_VIEW_DROP_INTO_OR_AFTER: (self.drag_bind, 0),
#                gtk.TREE_VIEW_DROP_BEFORE: (self.drag_bind, -1),
#                gtk.TREE_VIEW_DROP_AFTER: (self.drag_bind, +1),
#            }.get(destpos, (None,None))
#            logger.debug("reordering internally: %r vs %r" % (srcpath, destpath))
#            if callable(func):
#                func(*(bias, srcpath, destpath))
#            if ctx.action == gtk.gdk.ACTION_MOVE:
#                ctx.finish(True, True, time)
#            return True
            pass
        elif info == DndOpcodes.BIND:
            # bind-drop from commands set, seldata.data is bind (str).
            logger.debug("hialistview bind-drop")
            dropinfo = w.get_dest_row_at_pos(x,y)
            bindval = seldata.data
            logger.debug("command-dropping: %r" % seltext)
            hiasym = self.mdl[destpath][0]
            self.emit("bind-assigned", hiasym, bindval)
            ctx.finish(True, False, time)
            return True
        elif info == DndOpcodes.SWAP:
            # swap with a hidtop, seldata.data is inpsym.
            logger.debug("hidmenulist swap")
            othersym = seldata.data
            destsym = self.scratch[destpath][0]
            logger.debug("command-swapping: %r,%r" % (destsym, othersym))
            self.emit("bind-swapped", destsym, othersym)
            ctx.finish(True, False, time)
            return True
        return False


    def drag_bind (self, bias, srcpath, dstpath):
        # mass pull.
        #listbinds = [ b for s,b in self.scratch ]
        listbinds = [ r[1+self.layer] for r in self.scratch ]
        srcrow = srcpath[0]
        dstrow = dstpath[0]
        srcbind = listbinds[srcrow]
        if bias == 0:
            listbinds[srcrow] = listbinds[dstrow]
            listbinds[dstrow] = srcbind
        else:
            listbinds[srcrow] = None  # Flag for removal.
            if bias < 0:
                listbinds.insert(dstrow, srcbind)
            elif dstrow < len(listbinds):
                listbinds.insert(dstrow+1, srcbind)
            else:
                listbinds.append(srcbind)
#            if srcrow > dstrow:
#                srcrow += 1
#            del listbinds[srcrow]
            listbinds = [ x for x in listbinds if x is not None ]
        # Rebuild scratch from listbinds.
        self.scratch.clear()
#        for h in [ self.conn_bind_changed, self.conn_label_changed, self.conn_layer_changed, self.conn_group_changed ]:
#            self.inpdescr.handler_block(h)
        for i in range(0, len(listbinds)):
            bind = listbinds[i]
            n = i+1
            inpsym = "{}{}".format(self.inpsymprefix, n)
            self.set_bind(inpsym, bind)
            nlayers = self.dispstate.inpdescr.get_numlayers()
            self.scratch.append((inpsym,) + ("",)*nlayers)
#        for h in [ self.conn_bind_changed, self.conn_label_changed, self.conn_layer_changed, self.conn_group_changed ]:
#            self.inpdescr.handler_unblock(h)
        return

#    def pull_data (self):
#        """Synchronize .scratch based on InpDescrModel"""
#        nlayers = self.dispstate.inpdescr.get_numlayers()
#        for row in self.scratch:
#            inpsym = row[0]
#            def visit_bindcol (i, v):
#                bind_markup = self.resolve_bind_markup(inpsym, layer=i)
#                row[1+i] = bind_markup
#            self.foreach_layervis(visit_bindcol)

    def update_display (self):
        logger.info("menulist update_display")

        def visit_bindcol (i, v):
            if v:
                self.bindcols[i].set_visible(True)
                self.bindcols[i].set_expand(True)
                if i == self.layer:
                    # highlighted layer.
                    usestyle = self.refstyle.base
                else:
                    # unhighlighted layer.
                    usestyle = self.refstyle.bg
                styleval = usestyle[gtk.STATE_NORMAL]
                self.renderers[i].props.background = styleval
            else:
                self.bindcols[i].set_visible(False)
        self.foreach_layervis(visit_bindcol)
        self.queue_draw()
        return




class BindableCluster (gtk.EventBox, Bindable):
    """Groups together multiple BindableTops into a unit.
Intended for use in the context of Steam Controller touchpads.
Also re-used for the top-level layout view.

Composed of two parts visible at any one time:
* Grid layout
* List layout
"""
#    def __init__ (self, hiasym, label=None, nlayers=None, initbinds=None):
    def __init__ (self, hiasym, label=None, vis=None, initbinds=None):
        Bindable.__init__(self, hiasym, label, vis, initbinds)
        # TODO: In the context of Cluster, initbinds indicates what arrangement to use per layer.
        gtk.EventBox.__init__(self)
        self._layoutmap = None

        self.setup_states()
        self.setup_widget()

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
        if self.hiasym:
            self.ui.frame = gtk.Frame()
            self.ui.frame.set_shadow_type(gtk.SHADOW_IN)
            self.ui.lbl = gtk.Label(self.hiasym)
            self.ui.row_lbl = gtk.HBox()
            self.ui.row_lbl.pack_start(self.ui.lbl, False, False, 0)
            self.ui.row_lbl.show_all()
            self.ui.frame.set_label_widget(self.ui.row_lbl)
        self.ui.top = gtk.VBox()
        self.ui.grid = gtk.Table(12,12,True)
        # Map of hiasym to hiatop, hiatops grouped in this cluster, not
        # necessarily visible or attached to grid.
        # Expect "#c", "#1", "#2", ... "#20".
        self.ui.listview = BindableListView([])

        self.ui.top.pack_start(self.ui.grid, True, True, 0)
        if self.hiasym:
            self.ui.frame.add(self.ui.top)
            self.add(self.ui.frame)
            self.ui.frame.show()
        else:
            self.add(self.ui.top)

        self.ui.grid.show()
        self.ui.top.show()
        self.show()

    def update_layoutmap (self):
        """Based on .layoutmap, ensure widgets exist and are attached to grid."""
        # Detach all existent hia.
        for ch in self.ui.grid.children():
            self.ui.grid.remove(ch)

        # Attach all specified hia.
        for hiadata in self.layoutmap:
            hiasuffix, lbl, prototyp, x, y, w, h = hiadata
            hiasym = "{}{}".format(self.hiasym, hiasuffix)
            if not hiasym in self.hiatops:
                #hiatop = BindableTop(hiasym, lbl, self.vis, initbinds=None)
                #self.hiatops[hiasym] = hiatop
                hiatop = self.make_hiatop(hiadata, self.binds, self)
            else:
                hiatop = self.hiatops[hiasym]
                hiatop.set_vis(self.vis)
                # TODO: update bind?
            self.ui.grid.attach(hiatop, x, x+w, y, y+h)
            hiatop.show()
        self.ui.grid.show()
        self.ui.top.show()
        self.show()




class BindableLayoutView (BindableCluster):
    def __init__ (self, vis, bind_store):
        BindableCluster.__init__(self, "", "", vis, bind_store)




class InpLayer (object):
    """To be accessed as if dict.
One layer of bindings.
Keys are keysym.

Multiple layers attach to a group.
"""
    def __init__ (self, layernum, fallback, binds=None):
        self.layernum = layernum
        if binds is None:
            self._binds = dict()
        else:
            self._binds = binds
        # if the binding resolution fails, borrow from the fallback layer.
        self._fallback = None

    def clear (self):
        self._binds = dict()
        return

    def get_bind (self, k):
        retval = None
        if self._binds.has_key(k):
            retval = self._binds[k]
        elif self._fallback:
            retval = self._fallback[k]
        else:
            retval = None
        return retval

    def set_bind (self, k, v):
        self._binds[k] = v

    def has_bind (self, k):
        if self._binds.has_key(k):
            return True
        elif self._fallback:
            return self._fallback.has_key(k)
        else:
            return False
        
    def __getitem__ (self, k):
        return self.get_bind(k)

    def __setitem__ (self, k, v):
        self.set_bind(k,v)

    def has_key (self, k):
        return self.has_bind(k)

    def __repr__ (self):
        return "%s.%s(layernum=%r, fallback=%r, binds=%r)" % (self.__class__.__module__, self.__class__.__name__, self.layernum, self._fallback, self._binds)
        #return str(self.__json__())

    def __json__ (self):
        """JSON-friendly representation of this object."""
        return {
            '__module__': self.__class__.__module__,
            '__class__': self.__class__.__name__,
            'layernum': self.layernum,
            'fallback': self._fallback,
            'binds': self._binds,
            }


class InpGroup (gobject.GObject):
    """To be accessed as if list.
One group of binding layer.
Indices are group number.

Multiple layers attach to a group.
(i.e. contains multiple layers)
"""
    def __init__ (self, groupnum, fallback, numlayers, layers=None):
        self.groupnum = groupnum
        self.fallback = fallback
        if layers:
            self.layers = layers
        else:
            self.layers = []
            for i in range(groupnum):
                fallback = max(i-1, 0)
                self.layers.append(InpLayer(i, fallback, None))

    def clear (self):
        for lyr in self.layers:
            lyr.clear()
        return

    def get_layermap (self, n):
        return self.layers[n]

    def set_layermap (self, n, m):
        if (0 <= n) and (n < len(self.layers)):
            if m is None:
                self.layers[n] = InpLayer(n, max(n-1,0), None)
            else:
                self.layers[n] = m

    def get_numlayers (self):
        return self._maxlayers or 0
    def set_numlayers (self, n):
        self._maxlayers = n
        while (len(self.layers) < self._maxlayers):
            m = len(self.layers)
            temp = InpLayer(m, max(m-1, 0))
            self.layers.append(temp)

    def __getitem__ (self, k):
        self.get_layermap(k)
    def __setitem__ (self, k, v):
        self.set_layermap(k, v)
    def __len__ (self):
        return len(self.layers)
    def __repr__ (self):
        return "%s.%s(groupnum=%r, fallback=%r, numlayers=%r, layers=%r)" % (self.__class__.__module__, self.__class__.__name__, self.groupnum, self.fallback, len(self.layers), self.layers)
    def __json__ (self):
        return {
            '__module__': self.__class__.__module__,
            '__class__': self.__class__.__class__,
            'groupnum': self.groupnum,
            'fallback': self.fallback,
            'numlayers': len(self.layers),
            'layers': self.layers,
            }


class InpDescrModel (gobject.GObject):
    """Input descriptor model.  UI elements refer to this object for visual properties to use."""

    def __init__ (self, ngroups=1, nlayers=1, labels=None, groups=None):
        gobject.GObject.__init__(self)
        # Mapping of inpsym to label to display in UI.
        if labels is None:
            self.labels = dict()
        else:
            self.labels = labels
#        # List of InpLayer representing the binding layers.
#        self.layers = list()
        # List of InpGroup representing the binding groups.
        if groups is None:
            self.groups = list()
        else:
            self.groups = groups
        self._maxlayers = 1
        self._maxgroups = 1
        self.set_numgroups(ngroups)
        self.set_numlayers(nlayers)
#        # TODO: these states should not be in data model.
#        # active group
#        self._group = 0
#        # active layer
#        self._layer = 0
        self.cluster_defaults()

    def clear (self):
        for grp in self.groups:
            grp.clear()
#        self.set_group(0)
#        self.set_layer(0)
#        self.cluster_defaults()
        return

    def restore (self, other):
        if not other:
            return
        self._maxgroups = other.get_numgroups()
        self._maxlayers = other.get_numlayers()
#        self._group = 0
#        self._layer = 0
        for i in range(other.get_numgroups()):
            self.set_grouplist(i, other.get_grouplist(i))

    def cluster_defaults (self):
        # Handful of default binds.
        self.set_bind("LP#", ArrangerDpad.NAME, 0, 0)
        self.set_bind("RP#", ArrangerMouse.NAME, 0, 0)
        self.set_bind("L#", ArrangerJoystick.NAME, 0, 0)
        self.set_bind("R#", ArrangerJoystick.NAME, 0, 0)
        self.set_bind("B#", ArrangerDiamond.NAME, 0, 0)
        self.set_bind("DP#", ArrangerDpad.NAME, 0, 0)
        return

    def get_label (self, inpsym):
        """If no model data, return inpsym as the label."""
        return self.labels.get(inpsym, inpsym)

    def set_label (self, inpsym, lbl):
        self.labels[inpsym] = lbl
        self.emit("label-changed", inpsym)

#    def get_group (self):
#        """Get active group number."""
#        return self._group
#    def set_group (self, val):
#        self._group = val
#        self.emit('group-changed', self, val)
#
#    def get_layer (self):
#        """Get active layer number."""
#        return self._layer
#    def set_layer (self, val):
#        self._layer = val
#        self.emit("layer-changed", self, val)

    def get_grouplist (self, n):
        """Get group (list of InpLayer)"""
        if (0 <= n) and (n < self._maxgroups):
            return self.groups[n]
        return None
    def set_grouplist (self, n, l):
        try:
            layercount = self._maxlayers
        except AttributeError:
            layercount = 1
        if (0 <= n) and (n < self._maxgroups):
            if l is None:
                self.groups[n] = InpGroup(n, 0, layercount, None)
            else:
                self.groups[n] = l

#    def get_layermap (self, layernum, group=None):
#        """Get layer (dict of keysym:binding) in specified group."""
#        groupnum = group if group is not None else  self.get_group()
#        if (0 <= layernum) and (layernum < self._maxlayers):
#            return self.groups[groupnum].get_layermap(layernum)
#        return None
#    def set_layermap (self, layernum, value, group=None):
#        groupnum = group if group is not None else self.get_group()
#        if (0 <= layernum) and (layernum < self._maxlayers):
#            if value is None:
#                self.groups[groupnum].set_layermap(layernum, InpLayer(layernum, 0))
#            else:
#                self.groups[groupnum].set_layermap(layernum, value)

    def get_numgroups (self):
        return self._maxgroups or 0
    def set_numgroups (self, n):
        self._maxgroups = n
        try:
            maxlayers = self._maxlayers
        except AttributeError:
            # Max layers not known yet.
            maxlayers = 1
        while (len(self.groups) < self._maxgroups):
            m = len(self.groups)
            if m > 0:
                fallback = m-1
            else:
                fallback = None
            temp = InpGroup(m, 0, self._maxlayers, None)
            self.groups.append(temp)

    def get_numlayers (self):
        return self._maxlayers or 0
    def set_numlayers (self, n):
        self._maxlayers = n
        for grp in self.groups:
            grp.set_numlayers(n)

    def get_bind (self, inpsym,  group, layer):
        groupnum = group
        layernum = layer
        return self.get_grouplist(groupnum).get_layermap(layernum).get_bind(inpsym)
    def set_bind (self, inpsym, v,  group, layer):
        groupnum = group
        layernum = layer
        self.get_grouplist(groupnum).get_layermap(layernum).set_bind(inpsym, v)
        self.emit('bind-changed', groupnum, layernum, inpsym)


#    def resolve_bind (self, inpsym,  group=None, layer=None):
#        """Determine effective binding of a inpsym based on passthrough rules.
#"""
#        passthrough = False
#        groupnum = group if group is not None else self.get_group()
#        layernum = layer if layer is not None else self.get_layer()
#        groupfollow = groupnum
#        retval = None
#        while (retval is None) and (groupfollow is not None):
#            grp = self.get_grouplist(groupfollow)
#            layerfollow = layernum
#            while (retval is None) and (layerfollow is not None):
#                layermap = grp.get_layermap(layerfollow)
#                if layermap:
#                    retval = layermap.get_bind(inpsym)
#                if retval is None:
#                    passthrough = True
#                    if layerfollow != layermap._fallback:
#                        layerfollow = layermap._fallback
#                    else:
#                        layerfollow = None
#                    passthrough = True
#                layerfollow = None  ## don't follow layer for now.
#            if retval is None:
#                passthrough = True
#                if grp.fallback != groupfollow:
#                    groupfollow = grp.fallback
#                else:
#                    groupfollow = None
#        return passthrough, retval
#
#    def resolve_bind_markup (self, inpsym, group=None, layer=None):
#        passthrough, plaintext = self.resolve_bind(inpsym, group, layer)
#        if plaintext:
#            if passthrough:
#                # Fell back to group 0; italicize.
#                escbindlit = glib.markup_escape_text(plaintext)
#                retval = "<i><small>{}</small></i>".format(escbindlit)
#                return retval
#            else:
#                # Direct hit; return unadorned.
#                escbindlit = glib.markup_escape_text(plaintext)
#                return escbindlit
#        return ""
#
#    def swap_bind (self, firstsym, secondsym, group=None, layer=None):
#        firstbind = self.get_bind(firstsym, group, layer)
#        secondbind = self.get_bind(secondsym, group, layer)
#        self.set_bind(firstsym, secondbind)
#        self.set_bind(secondsym, firstbind)
#        return

#    def refresh (self):
#        """Induce update of viewers of this model."""
#        self.emit("layer-changed", self._layer)

    def __repr__ (self):
        return "%s.%s(ngroups=%d, nlayers=%d, labels=%r, groups=%r)" % (
          self.__class__.__module__,
          self.__class__.__name__,
          self._maxgroups,
          self._maxlayers,
          self.labels,
          self.groups
          )
#        return str(self.__json__())

    def __json__ (self):
        """JSON-friendly representation of this object."""
        return {
            '__module__': self.__class__.__module__,
            '__class__': self.__class__.__name__,
            'maxgroups': self._maxgroups,
            'maxlayers': self._maxlayers,
            'labels': self.labels,
            'groups': self.groups,
            }

    # Signals:
    # * bind-changed(layer:int, inpsym:str) - a binding changed; update display
    # * label-changed() - labels for keytops has changed; update display
    # * layer-changed() - active layer changed

gobject.type_register(InpDescrModel)
gobject.signal_new("bind-changed", InpDescrModel, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_STRING))
gobject.signal_new("label-changed", InpDescrModel, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
#gobject.signal_new("layer-changed", InpDescrModel, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,))
#gobject.signal_new("group-changed", InpDescrModel, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,))



class InpDisplayState (gobject.GObject):
    """Run-time state affecting display of input-bindables.

Display states tracked:
 * layer = current layer selected
 * group = current group (mode) selected
 * vislayers = number of layers to be visible at a time.
 ** visbase = lowest layer id visibile in vislayers (as aligned at powers of 2).
 * layout = current HID layout
"""
    def __init__ (self, inpdescr, all_layouts=None):
        gobject.GObject.__init__(self)
        self.inpdescr = inpdescr
        self._layer = 0
        self._group = 0
        self._vislayers = 1
        self._layout = None  # key of active inpdescr layout.
        self.activehid = None  # reference to active inpdescr layout.
#        self.inpdescr.connect("layer-changed", self.on_inpdescr_layer_changed)
#        self.inpdescr.connect("group-changed", self.on_inpdescr_group_changed)
        self.inpdescr.connect("bind-changed", self.on_inpdescr_bind_changed)
        self.inpdescr.connect("label-changed", self.on_inpdescr_label_changed)
        self.cluster_defaults()

    def get_inpdescr (self):
        return self.inpdescr
    def set_inpdescr (self, v):
        self.inpdescr = v

    def get_layer (self):
        return self._layer
    def set_layer (self, val):
        self._layer = val
        self.emit("layer-changed", val)
        #self.emit("display-adjusted")
    layer = property(get_layer, set_layer)

    def get_group (self):
        return self._group
    def set_group (self, val):
        self._group = val
        self.emit("group-changed", val)
        #self.emit("display-adjusted")
    group = property(get_group, set_group)

    def get_vislayers (self):
        return self._vislayers
    def set_vislayers (self, val):
        self._vislayers = val
        #self.emit("layer-changed", val)
        #self.emit("display-adjusted")
        self.emit("vislayers-changed", val)
    vislayers = property(get_vislayers, set_vislayers)

    def get_layoutname (self):
        return self._layout
    def set_layoutname (self, v):
        self._layout = v
        # TODO: update layout
        self.activehid = self._all_layouts[self._layout]
        self.emit("layout-changed")
    layoutname = property(get_layoutname, set_layoutname)

    def get_layout (self):
        return self.activehid
    layout = property(get_layout)

    def get_layouts (self):
        return self._all_layouts
    def set_layouts (self, v):
        self._all_layouts = v
        # TODO: update layout - refresh on layout name?
        self.activehid = self._all_layouts[self._layout]
        self.emit("layout-changed")
    layouts = property(get_layouts, set_layouts)

    def refresh (self):
        """Induce update of viewers of this model."""
        self.emit("display-adjusted", self)

    def on_inpdescr_bind_changed (self, inpdescr, group, layer, inpsym):
        pass

    def on_inpdescr_label_changed (self, inpdescr, inplbl):
        pass

    def clear (self):
        """Reset to initial state."""
        self.inpdescr.clear()
        self.set_group(0)
        self.set_layer(0)
        self.set_layoutname(None)

    def restore (self, other):
        """Restore state from another."""
        if not other:
            return
        self.inpdescr.restore(other.inpdescr)
        self.set_group(other.get_group())
        self.set_layer(other.get_layer())
        self.set_layoutname(other.get_layoutname)

    def cluster_defaults (self):
        """Handful of default binds."""
# TODO: somewhere else.
        self.set_bind("LP#", ArrangerDpad.NAME, 0, 0)
        self.set_bind("RP#", ArrangerMouse.NAME, 0, 0)
        self.set_bind("L#", ArrangerJoystick.NAME, 0, 0)
        self.set_bind("R#", ArrangerJoystick.NAME, 0, 0)
        self.set_bind("B#", ArrangerDiamond.NAME, 0, 0)
        self.set_bind("DP#", ArrangerDpad.NAME, 0, 0)
        return

#    def get_layermap (self, layernum, group=None):
#        """Get layer (dict of keysym:binding) in specified group."""
#        groupnum = group if group is not None else  self.get_group()
#        if (0 <= layernum) and (layernum < self.inpdescr._maxlayers):
#            return self.inpdescr.groups[groupnum].get_layermap(layernum)
#        return None
#    def set_layermap (self, layernum, value, group=None):
#        groupnum = group if group is not None else self.get_group()
#        if (0 <= layernum) and (layernum < self.inpdescr._maxlayers):
#            if value is None:
#                self.inpdescr.groups[groupnum].set_layermap(layernum, InpLayer(layernum, 0))
#            else:
#                self.inpdescr.groups[groupnum].set_layermap(layernum, value)

    def get_bind (self, inpsym,  group=None, layer=None):
        groupnum = group if group is not None else self.get_group()
        layernum = layer if layer is not None else self.get_layer()
        return self.inpdescr.get_bind(inpsym, groupnum, layernum)
    def set_bind (self, inpsym, v,  group=None, layer=None):
        groupnum = group if group is not None else self.get_group()
        layernum = layer if layer is not None else self.get_layer()
        #self.inpdescr.get_grouplist(groupnum).get_layermap(layernum).set_bind(inpsym, v)
        self.inpdescr.set_bind(inpsym, v, groupnum, layernum)
        #self.emit('display-adjusted')

    def resolve_bind_group (self, inpsym, group=None):
        """Determine effective binding in a group of a inpsym,
using passthrough rules.

Each element is a tuple of (bool, str):
  bool = retrieved by passthrough
  str = effective binding
"""

        passthrough = False
        groupnum = group if group is not None else self.get_group()
#        layernum = layer if layer is not None else self.get_layer()
        groupfollow = groupnum
        retval = []

        fellthrough = False
        while groupfollow is not None:
            grp = self.inpdescr.get_grouplist(groupfollow)
            while len(retval) < len(grp.layers):
                retval.append((False,""))
            for layernum in range(len(grp.layers)):
                layermap = grp.get_layermap(layernum)
                probe = layermap.get_bind(inpsym)
                if not retval[layernum][1]:
                    retval[layernum] = (fellthrough, probe)
            groupfollow = grp.fallback if grp.fallback != groupfollow else None
            fellthrough = True
        return retval

    def resolve_bind_group_markup (self, inpsym, group=None):
        grpbind = self.resolve_bind_group(inpsym, group)
        retval = []
        for fellthrough,plaintext in grpbind:
            escbindlit = glib.markup_escape_text(plaintext) if plaintext is not None else ""
            if fellthrough:  # italicize
                item = "<i><small>{}</small></i>".format(escbindlit)
            else:  # unadorned.
                item = escbindlit
            retval.append(item)
        return retval

#    def resolve_bind (self, inpsym,  group=None, layer=None):
#        """Determine effective binding of a inpsym based on passthrough rules.
#"""
#        passthrough = False
#        groupnum = group if group is not None else self.get_group()
#        layernum = layer if layer is not None else self.get_layer()
#        groupfollow = groupnum
#        retval = None
#        while (retval is None) and (groupfollow is not None):
#            grp = self.inpdescr.get_grouplist(groupfollow)
#            layerfollow = layernum
#            while (retval is None) and (layerfollow is not None):
#                layermap = grp.get_layermap(layerfollow)
#                if layermap:
#                    retval = layermap.get_bind(inpsym)
#                if retval is None:
#                    passthrough = True
#                    if layerfollow != layermap._fallback:
#                        layerfollow = layermap._fallback
#                    else:
#                        layerfollow = None
#                    passthrough = True
#                layerfollow = None  ## don't follow layer for now.
#            if retval is None:
#                passthrough = True
#                if grp.fallback != groupfollow:
#                    groupfollow = grp.fallback
#                else:
#                    groupfollow = None
#        return passthrough, retval

    def resolve_bind (self, inpsym,  group=None, layer=None):
        groupnum = group if group is not None else self.get_group()
        layernum = layer if layer is not None else self.get_layer()
        grpbind = self.resolve_bind_group(inpsym, group=groupnum)
        retval = grpbind[layernum]
        # Returns tuple (bool,str)
        return retval

    def resolve_bind_markup (self, inpsym, group=None, layer=None):
        passthrough, plaintext = self.resolve_bind(inpsym, group, layer)
        if plaintext:
            escbindlit = glib.markup_escape_text(plaintext)
            if passthrough:
                # Fell back to group 0; italicize.
                retval = "<i><small>{}</small></i>".format(escbindlit)
                return retval
            else:
                # Direct hit; return unadorned.
                return escbindlit
        return ""

    __gsignals__ = {
        "display-adjusted": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        "layer-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        "group-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        "vislayers-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        "layout-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
    }

gobject.type_register(InpDisplayState)
#gobject.signal_new("display-adjusted", InpDisplayState, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
#gobject.signal_new("layer-changed", InpDisplayState, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (InpDisplayState, gobject.TYPE_INT,))
#gobject.signal_new("group-changed", InpDisplayState, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (InpDisplayState, gobject.TYPE_INT,))


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
    """List of HidLayoutStore."""
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
        match = [ v for k,v in self if k == key]
        if match:
            return match[0]
        raise KeyError("Key not found: {}".format(key))
    def keys (self):
        return [ k for k,v in self ]




# HID = Human(-Computer) Interface Device; including: keyboard, mouse, joystick, gamepad

class HidBindable (object):
    """Base class for elements that can take binds (from command set)."""

    def __init__ (self, inpsym, dispstate):
#    def build (self, inpsym, dispstate):
        #gobject.GObject.__init__(self)
        #self.__gobject_init__()
        self.inpsym = inpsym
        self.dispstate = dispstate
        #self.conn_display_adjusted = self.dispstate.connect("display-adjusted", self.on_display_adjusted)
        #self.conn_bind_changed = self.dispstate.inpdescr.connect("bind-changed", self.on_inpdescr_bind_changed)
        #self.conn_label_changed = self.dispstate.inpdescr.connect("label-changed", self.on_inpdescr_label_changed)
        self.dispbinds = []   # Array of binds to display, elements are tuple (binding, attr) per layer.  With markup.

        temp = gtk.Entry()
        self.refstyle = temp.get_style().copy()

        # Currently active layer.
        self._layer = 0
        # Number of layers to show at once.
        self._vislayers = 1
        # array of visibility, bool per layer.
        self._layervis = [True]

#    @property
#    def layer (self): return self.dispstate.get_layer()
#    @layer.setter
#    def set_layer (self, val): self.dispstate.set_layer(val)
#    @property
#    def group (self): return self.dispstate.get_group()
#    @group.setter
#    def set_group (self, val): self.dispstate.set_group(val)
#    @property
#    def vislayers (self): return self.dispstate.get_vislayers()
#    @vislayers.setter
#    def set_vislayers (self, val):
#        logger.debug("changing vislayers")
#        self.dispstate.set_vislayers(val)

    def get_layer (self): return self._layer
    def set_layer (self, v):
        self._layer = v
        self.update_display()
    layer = property(get_layer, set_layer)

    def get_vislayers (self):
        return self._vislayers
    def set_vislayers (self, v):
        self._vislayers = v
        self.update_display()
    vislayers = property(get_vislayers, set_vislayers)

#    def get_bind (self, inpsym, group=None, layer=None):
#        raise NotImplementedError("HidBindinable.get_bind() should not be implemented")
#        #return self.dispstate.get_bind(inpsym, group, layer)
#    def set_bind (self, inpsym, v, group=None, layer=None):
#        raise NotImplementedError("HidBindinable.set_bind() should not be implemented")
#        self.dispstate.set_bind(inpsym, v, group, layer)
#    def resolve_bind (self, inpsym, group=None, layer=None):
#        raise NotImplementedError("HidBindinable.resolve_bind() should not be implemented")
#        return self.dispstate.resolve_bind(inpsym, group, layer)
#    def resolve_bind_markup (self, inpsym, group=None, layer=None):
#        raise NotImplementedError("HidBindinable.resolve_bind_markup() should not be implemented")
#        return self.dispstate.resolve_bind_markup(inpsym, group, layer)
#    def swap_bind (self, firstsym, secondsym, group=None, layer=None):
#        raise NotImplementedError("HidBindinable.swap_bind() should not be implemented")
#        return self.dispstate.swap_bind(firstsym, secondsym, group, layer)

    def get_label (self):
        raise NotImplementedError("get_label() is abstract")
    def set_label (self, val):
        raise NotImplementedError("set_label() is abstract")

    def get_layervis (self):
        # array of bool
        return self._layervis
    def set_layervis (self, v):
        self._layervis = v
        self.update_layervis()
    layervis = property(get_layervis, set_layervis)

    def update_layervis (self):
        # override.
        pass

    def set_dispbinds (self, grpbind):
        """Set displayed binds for all layers at once.
grpbind = list of bindings (with pango markup), one per layer in sequence."""
        self.dispbinds = grpbind[:]  # copy
        self.update_dispbinds()

    def update_dispbinds (self):
        # override.
        pass

    def contains_inpsym (self, inpsym):
        return self.inpsym == inpsym

    def foreach_layervis (self, cb):
        """To avoid lots of for-loop with nested predicates, this walker function calls cb with two arguments: (layer_number, is_visible)."""
        baselayer = self.vislayers * (self.layer / self.vislayers)
        visspan = self.vislayers
        #nlayers = self.dispstate.inpdescr.get_numlayers()
        nlayers = len(self._layervis)
        for i in range(nlayers):
            cb(i, (i >= baselayer) and (i < baselayer+visspan))
        return

    def on_display_adjusted (self, dispstate, *args):
        self.update_display()

    def on_inpdescr_bind_changed (self, inpdescr, group, layer, inpsym):
        if self.inpsym == inpsym:
            self.update_display()

    def on_inpdescr_label_changed (self, inpdescr, inpsym):
        if self.inpsym == inpsym:
            self.update_display()

    def block_signals (self):
        for (obj, sigh) in [ (self.dispstate, self.conn_display_adjusted), (self.dispstate.inpdescr, self.conn_bind_changed), (self.dispstate.inpdescr, self.conn_label_changed) ]:
            obj.handler_block(sigh)

    def unblock_signals (self):
        for (obj, sigh) in [ (self.dispstate, self.conn_display_adjusted), (self.dispstate.inpdescr, self.conn_bind_changed), (self.dispstate.inpdescr, self.conn_label_changed) ]:
            obj.handler_unblock(sigh)

    def update_display (self):
        raise NotImplementedError("update_display() is abstract")

    __gsignals__ = {
        'bind-assigned': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        'bind-swapped': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
        'bind-erased': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
    }

#gobject.type_register(HidBindable)
#gobject.signal_new("bind-assigned", HidBindable, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING))
#gobject.signal_new("bind-swapped", HidBindable, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING))
#gobject.signal_new("bind-erased", HidBindable, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))


class HidTop (gtk.Button, HidBindable):
    """UI element of a key(board) top.  Presented as the inpsym on the first row, and a boxed text entry on the second row for the binding.
Contents to display are packaged in a data model (InpDescrModel)

Properties:
 @property grpbind : tuple(bool, str) = binds for all layers in current group; elt
 @property label : str = keytop label
 @property layervis : list[] = list of bool per layer

Parent callback:
 * after-hidtop-dropped
 * after-hidtop-swapped
 * after-hidtop-erased
    """
    def __init__ (self, inpsym, dispstate):
        """Initialize with given data model, and the input symbol tied to this hidtop"""
        # UI elements
        gtk.Button.__init__(self)
        HidBindable.__init__(self, inpsym, dispstate)
        #HidBindable.build(self, inpsym, dispstate)
        self.plane = gtk.VBox()
        self.inp_lbl = gtk.Label()
        self.spacer = gtk.HBox()

        # Fill label (first row)
        #self.label = self.dispstate.inpdescr.get_label(self.inpsym)
        lbl = self.label = inpsym
        self.set_label(lbl)

        # Alignment widget.
        self.align0 = gtk.Alignment(0, 0, 0, 0)
        self.align0.add(self.inp_lbl)
        self.plane.pack_start(self.align0, expand=True, fill=True)
        self.plane.pack_start(self.spacer, expand=True, fill=True)

        # Outline of key.
        self.box_bind = gtk.Frame()
        self.box_bind.set_shadow_type(gtk.SHADOW_IN)
        self.align1 = gtk.Alignment(0,0,1,1)
        self.bg_bind = gtk.EventBox()

        self.inp_binds = []     # Show binding.
        self.lyr_lbls = []      # Layers labeling prefix to binding.
        self.bg_binds = []      # Background for binding display.
        self.hrules = []        # HSeparator.
        self.bindrows = []      # Box for each line of hrule+lyr+bind
        self.inp_box = None

        #nlayers = self.dispstate.inpdescr.get_numlayers()
        nlayers = 8
        self.maxlayers = nlayers
        self.uibuild_binddisplays(nlayers)

        self.box_bind.add(self.align1)

        self.plane.pack_start(self.box_bind, expand=False, fill=False)

        self.add(self.plane)

        self.connect("map", self.on_map)
        self.setup_dnd()
#        self.update_display()

    def uibuild_binddisplays (self, nlayers=None):
        if self.inp_box:
            if self.inp_box.get_parent():
                self.align1.remove(self.inp_box)
            else:
                logger.debug("no parent %r %r" % (self.inp_box, self.inpsym))

        if nlayers is None:
            nlayers = self.maxlayers

        self.inp_box = gtk.VBox()

        # Input binding displays.
        self.inp_binds = [ gtk.Label() for n in range(nlayers) ]
        # Background for binding displays.
        self.bg_binds = [ gtk.EventBox() for n in range(nlayers) ]
        # label for binding display layers.
        self.lyr_lbls = [ gtk.Label() for n in range(nlayers) ]
        self.hrules = [ gtk.HSeparator() for n in range(nlayers) ]

        # set up droppable binding display (dressed up as a text entry).
        # Prepare multi-layer view for HidTop.
        for i in range(0, nlayers):
            ib = self.inp_binds[i]
            ib.set_alignment(0, 0.5)
            ib.set_width_chars(4)
            ib.set_justify(gtk.JUSTIFY_LEFT)
            bg = self.bg_binds[i]
            bg.add(ib)

            #self.inp_box.pack_start(bg, expand=False, fill=False)
            bindline = gtk.HBox()
            bindline.pack_start(self.lyr_lbls[i], expand=False, fill=False)
            self.lyr_lbls[i].set_markup("<small>%s:</small>" % i)
            bindline.pack_start(bg, expand=True, fill=True)

            if i != 0:
                self.inp_box.pack_start(self.hrules[i], False, False, 0)
            self.inp_box.pack_start(bindline, expand=False, fill=False)
            if i > self.vislayers:
                bindline.hide()
                self.hrules[i].hide()
            else:
                bindline.show()
                self.hrules[i].show()
            self.bindrows.append(bindline)
        self.align1.add(self.inp_box)

    def on_map (self, w):
        logger.debug("hidtop map %r=%r" % (self.inpsym, self.label))
        self.update_display()
        return True

    def show (self):
        logger.debug("hidtop show %r=%r" % (self.inpsym, self.label))
        self.update_display()

    def get_inpsym (self):
        return self.inpsym
    def set_inpsym (self, val):
        self.inpsym = val

    def get_label (self):
        #return self.label.get_text()
        return self.label
    def set_label (self, v):
        self.label = v
        logger.debug("set_label %r <- %r" % (self.inpsym, v))
        if not v:
            raise Exception("Break")
        self.set_hidtop(v)

    def update_layervis (self):
        nlayers = len(self.layervis)
        self.uibuild_binddisplays()
        self.update_display()
        return

    def update_dispbinds (self):
        # Populate bind displays from self.dispbinds[]
        # TODO: expand self.inp_box when maxlayers grow.
        for lyr in range(len(self.dispbinds)):
            self.inp_binds[lyr].set_markup(self.dispbinds[lyr])

    def set_hidtop (self, disp):
        if len(disp) > 2:
            self.inp_lbl.set_markup("<small>%s</small>" % disp)
        else:
            self.inp_lbl.set_text("%s" % disp)
        return

    def update_display (self):
        # Update keytop
        logger.debug("hidtop update_display %r=%r" % (self.inpsym,self.get_label()))
        #lbl = self.dispstate.inpdescr.get_label(self.inpsym)
        #self.set_hidtop(lbl)

        # Update binding display
        self.mid_vis = False
        self.show_all()
        def visit_bindrow (i, v):
            logger.debug("visit_bindrow, %r, %r" % (i, v))
            if v:
                self.bindrows[i].show()
                if self.mid_vis:
                    self.hrules[i].show()
                else:
                    self.hrules[i].hide()
                    self.mid_vis = True
                bg = self.bg_binds[i]
                if i == self.layer:
                    usestyle = self.refstyle.base
                else:
                    usestyle = self.refstyle.bg
                bg.modify_bg(gtk.STATE_NORMAL, usestyle[gtk.STATE_NORMAL])
                bg.modify_bg(gtk.STATE_ACTIVE, usestyle[gtk.STATE_ACTIVE])
                bg.modify_bg(gtk.STATE_PRELIGHT, usestyle[gtk.STATE_PRELIGHT])
                bg.modify_bg(gtk.STATE_SELECTED, usestyle[gtk.STATE_SELECTED])

                #val = self.resolve_bind_markup(self.inpsym, layer=i)
                #self.inp_binds[i].set_markup(val)
                self.lyr_lbls[i].set_visible(self.vislayers > 1)
            else:
                logger.debug(" hiding %r" % (i,))
                self.bindrows[i].hide()
                self.hrules[i].hide()
        self.foreach_layervis(visit_bindrow)

    def setup_dnd (self):
        # Set up drag-and-drop for HidTop.
        # DnD source.
        dnd_targets = [
          (str(DndOpcodes.UNBIND), gtk.TARGET_SAME_APP, DndOpcodes.UNBIND),
          (str(DndOpcodes.SWAP), gtk.TARGET_SAME_APP, DndOpcodes.SWAP),
        ]
        dnd_actions = gtk.gdk.ACTION_COPY
        self.drag_source_set(gtk.gdk.BUTTON1_MASK, dnd_targets, dnd_actions)
        self.connect("drag-data-get", self.on_drag_data_get)
        self.connect("drag-end", self.on_drag_end)

        # DnD destination.
        dnd_targets = [
          (str(DndOpcodes.BIND), gtk.TARGET_SAME_APP, DndOpcodes.BIND),
          (str(DndOpcodes.SWAP), gtk.TARGET_SAME_APP, DndOpcodes.SWAP),
        ]
        dnd_actions = gtk.gdk.ACTION_COPY
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, dnd_targets, dnd_actions)
        self.connect("drag-data-received", self.on_drag_data_received)

        self.pending_drag_unbinding = False

    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        """Being dragged to elsewhere."""
        logger.debug("hidtop.drag-data-get: %d" % info)
        if info == DndOpcodes.UNBIND:
            logger.debug("hidtop: try unbind  %s" % self.inpsym)
            seldata.set(seldata.target, 8, str(self.inpsym))
            self.pending_drag_unbinding = True
            return True
        if info == DndOpcodes.SWAP:
            logger.debug("hidtop.drag-data-get for swap")
            val = self.inpsym
            seldata.set(seldata.target, 8, str(self.inpsym))
            return True
        return False

    def on_drag_end (self, w, ctx, *args):
        if self.pending_drag_unbinding:
            logger.debug("hidtop unbind %s" % self.inpsym)
            #self.set_bind(self.inpsym, "")
            #self.emit("layer-bind-changed", self.inpsym, "")
            self.emit("bind-erased", self.inpsym)
            self.pending_drag_unbinding = False
        return

    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        logger.debug("%s drag-data-received %r" % (self.__class__.__name__, w))
        if info == DndOpcodes.BIND:
            # Commands dropping.
            seltext = seldata.data
            logger.debug("hidtop Command install: %s <= %s" % (w.inpsym, seltext))
            #self.set_bind(self.inpsym, seltext)
            #self.emit("layer-bind-changed", self.inpsym, seltext)
            self.emit("bind-assigned", self.inpsym, seltext)
            ctx.finish(True, False, 0)
            return True
        elif info == DndOpcodes.SWAP:
            othersym = seldata.data
            logger.debug("hidtop Command swap: %s <=> %s" % (w.inpsym, othersym))
            #self.swap_bind(w.inpsym, othersym)
            self.emit("bind-swapped", w.inpsym, othersym)
            ctx.finish(True, False, 0)
            return True

    __gsignals__ = HidBindable.__gsignals__

gobject.type_register(HidTop)
#gobject.signal_new("layer-bind-change", HidTop, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.STRING, gobject.STRING))
#gobject.signal_new("layer-bind-swap", HidTop, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.STRING, gobject.STRING))



class Arranger (object):
    """Base case for arranger: no sub-elements.
Also base class for arrangers.
"""
    NAME = "base"
    W = 12
    H = 12
    # Simplified placements: based on cell groupings of WxH, locations of sub-sym hidtops keyed by inpsym.  Programmatically convert to HidLayoutStore.
    SIMPLE_PLACEMENTS = { }
    def __init__ (self, parent, layoutmap=None):
        self.parent = parent
        self.placements = dict()
        if layoutmap is None:
            layoutmap = HidLayoutStore("{}.{}".format(parent.inpsym, self.NAME))
        self.layoutmap = layoutmap

        if self.SIMPLE_PLACEMENTS:
            self._derive_layoutmap_from_simple_placements(self.layoutmap, self.SIMPLE_PLACEMENTS)
        self.build_widget_pool()

    def _derive_layoutmap_from_simple_placements (self, layoutmap, simple_placements):
        for k,v in simple_placements.iteritems():
            row,col = v
            lbl = "{}{}".format(self.parent.inpsym, k)
            inpsym = "{}{}".format(self.parent.inpsym, k)
            x, y = col*self.H, row*self.H
            w, h = self.W, self.H
            rowdata = (inpsym, lbl, "key", x, y, w, h)
            layoutmap.append(None, rowdata)
        return layoutmap

    def _populate_widget_pool (self, layoutmap=None):
        """Create instances of HidTop as needed according to visible inpsyms.
"""
        if layoutmap is None:
            layoutmap = self.layoutmap

        for eltdata in layoutmap:
            self.parent.make_hidelt(eltdata)
        return

    def get_layoutmap (self):
        return self.layoutmap
    def set_layoutmap (self, val):
        self.layoutmap = val
        self._populate_widget_pool(self.layoutmap)

    def build_widget_pool (self, suffices=()):
#        suffices = self.placements.keys()
#        self._populate_widget_pool(suffices)
        self._populate_widget_pool(self.layoutmap)

    def inpsymof (self, suffix):
        return "{}{}".format(self.parent.inpsymprefix, suffix)

    def full_rearrange (self, layoutmap):
        """Common case of gridded arrangement, where
layoutmap = HidStoreLayout instance, rows are (inpsym, lbl, prototype, row, col, width|colspan, height|rowspan)
"""
        self.parent.detach_all()
        self.parent.grid.resize(12,12)
        for elt in layoutmap:
            logger.debug("elt = %r" % (elt,))
            inpsym,lbl,prototyp,col,row,xspan,yspan = elt
            if col < 0 or row < 0:
                # Treat negative positions as "ignore".
                continue
            #inpsym = self.inpsymof(suffix)
            left = col
            right = col + xspan
            top = row
            bottom = row + yspan
            hidtop = self.parent.hidtops[inpsym]
            self.parent.grid.attach(hidtop, left, right, top, bottom)
            #hidtop.hide_all()
            #hidtop.show_all()
            hidtop.show()
        #self.parent.show_all()
        return

    def rearrange (self):
        self.parent.stacked.set_visible_child_name("0")
        self.full_rearrange(self.layoutmap)

    def __repr__ (self):
        return "{!s}()".format(self.__class__.__name__)

class ArrangerEmpty (Arranger):
    """no-element arranger."""
    NAME = "empty"
    def __init__ (self, parent):
        Arranger.__init__(self, parent)

class ArrangerStored (Arranger):
    """Arranged based on HidLayoutStore."""
    NAME = "stored"
    def __init__ (self, parent, layoutmap):
        Arranger.__init__(self, parent, layoutmap)

class ArrangerOneButton (ArrangerEmpty):
    """Large single button."""
    NAME = "SingleButton"
    # Click
    W = 12
    H = 12
    SIMPLE_PLACEMENTS = {
           # (row,col, colspan,rowspan)
        'c': (0,0),
    }

class ArrangerScrollwheel (ArrangerEmpty):
    """Scroll wheel of the up/down/center variety.
For scroll-items, use MenuList."""
    NAME = "ScrollWheel"
    # Up Click Down
    W = 4
    H = 4
    SIMPLE_PLACEMENTS = {
        'u': (0,1),
        'c': (1,1),
        'd': (2,1),
    }

class ArrangerDpad (ArrangerEmpty):
    """Direction pad"""
    NAME = "Dpad"
    # Up Down Left Right Center/Click OuterRing
    W = 4
    H = 4
    SIMPLE_PLACEMENTS = {
        'u': (0,1),
        'l': (1,0),
        'c': (1,1),
        'r': (1,2),
        'd': (2,1),
        'o': (2,2),
    }

class ArrangerDiamond (ArrangerEmpty):
    """Button cluster: N, W, E, S; aka Y, X, B, A"""
    NAME = "ButtonQuad"
    # North East West South Click/Center
    W = 4
    H = 4
    SIMPLE_PLACEMENTS = {
        'n': (0,1),
        'w': (1,0),
#        'c': (1,1),
        'e': (1,2),
        's': (2,1),
    }

class ArrangerMouse (ArrangerEmpty):
    """Mouse/trackball."""
    NAME = "Mouse"
    # touch click double-tap x y
    W = 4
    H = 4
    SIMPLE_PLACEMENTS = {
        't': (0,0),
        'tt': (0,2),
        'c': (1,1),
        'x': (1,2),
        'y': (2,1),
    }

class ArrangerMouseRegion (ArrangerEmpty):
    """Mouse region."""
    NAME = "MouseRegion"
    W = 12
    H = 12
    SIMPLE_PLACEMENTS = {
        'c': (0,0),
    }

class ArrangerJoystick (ArrangerEmpty):
    """Joystick: left/right, up/down."""
    NAME = "Joystick"
    # x-, x+, y-, y+, Click, OuterRing
    W = 4
    H = 4
    SIMPLE_PLACEMENTS = {
        'y-': (0,1),
        'x-': (1,0),
        'c':  (1,1),
        'x+': (1,2),
        'y+': (2,1),
        'o': (2,2),
    }

class ArrangerGyrotilt (ArrangerEmpty):
    """Gyroscope tiltable: yaw left/right, up/down, roll left/right"""
    NAME = "GyroTilt"
    # x-, x+, y-, y+, w-, w+, Click, OuterRing
    W = 4
    H = 4
    SIMPLE_PLACEMENTS = {
        'w-': (0,0),
        'y-': (0,1),
        'w+': (0,2),
        'x-': (1,0),
        'c':  (1,1),
        'x+': (1,2),
        'y+': (2,1),
    }

class ArrangerTouchmenu (ArrangerEmpty):
    """(on-screen display) touch menu."""
    NAME = "TouchMenu"
    ALL_PLACEMENTS = {
    2: {
        '1': (0,0,6,12),  '2': (0,6,6,12),
    },
    4: {
        '1': (0,0,6,6),  '2': (0,6,6,6),
        '3': (6,0,6,6),  '4': (6,6,6,6),
    },
    7: {
        '1': (0,2,4,4),  '2': (0,6,4,4),
        '3': (4,0,4,4),  '4': (4,4,4,4), '5': (4,8,4,4),
        '6': (8,2,4,4),  '7': (8,6,4,4),
    },
    9: {
        '1': (0,0,4,4),  '2': (0,4,4,4), '3': (0,8,4,4),
        '4': (4,0,4,4),  '5': (4,4,4,4), '6': (4,8,4,4),
        '7': (8,0,4,4),  '8': (8,4,4,4), '9': (8,8,4,4),
    },
    12: {
        '1': (0,0,3,4),  '2': (0,3,3,4),  '3': (0,6,3,4),  '4': (0,9,3,4),
        '5': (4,0,3,4),  '6': (4,3,3,4),  '7': (4,6,3,4),  '8': (4,9,3,4),
        '9': (8,0,3,4), '10': (8,3,3,4), '11': (8,6,3,4), '12': (8,9,3,4),
    },
    13: {
        '1': (0,0,3,3),  '2': (0,3,3,3),  '3': (0,6,3,3),  '4': (0,9,3,3),
        '5': (3,0,3,3),                                    '6': (3,9,3,3),
                                '13': (3,3,6,6),
        '7': (6,0,3,3),                                    '8': (6,9,3,3),
        '9': (9,0,3,3), '10': (9,3,3,3), '11': (9,6,3,3), '12': (9,9,3,3),
    },
    16: {
        '1': (0,0,3,3),  '2': (0,3,3,3),  '3': (0,6,3,3),  '4': (0,9,3,3),
        '5': (3,0,3,3),  '6': (3,3,3,3),  '7': (3,6,3,3),  '8': (3,9,3,3),
        '9': (6,0,3,3), '10': (6,3,3,3), '11': (6,6,3,3), '12': (6,9,3,3),
       '13': (9,0,3,3), '14': (9,3,3,3), '15': (9,6,3,3), '16': (9,9,3,3),
    },
    }

    def __init__ (self, parent, cap=2):
        self.parent = parent
        self.all_layouts = dict()
        self._build_all_layouts()
        self.set_capacity(cap)
        ArrangerEmpty.__init__(self, parent)
        #self.build_widget_pool()

    def _build_all_layouts (self):
        """Convert dict of SIMPLE_PLACEMENTS to dict of HidLayoutStore."""
        for k,v in self.ALL_PLACEMENTS.iteritems():
            storename = k
            layoutmap = HidLayoutStore(storename)
            for suffix,dims in v.iteritems():
                y,x,w,h = dims
                inpsym = "{}{}".format(self.parent.inpsymprefix, suffix)
                lbl = inpsym
                prototyp = 'key'
                rowdata = (inpsym, lbl, prototyp, x, y, w, h)
                layoutmap.append(None, rowdata)
            self.all_layouts[k] = layoutmap
        return

    def build_widget_pool (self):
        """Create HidTop instances as needed to add into widget_pool, a dict of inpsym to widget."""
        # Generate '1'..'16' inclusive.
        #suffices = [ str(ofs) for ofs in range(1, 17) ]
        # Populate widget pool based on largest layout.
        self._populate_widget_pool(self.all_layouts[16])

    def set_capacity (self, cap):
        thresholds = self.ALL_PLACEMENTS.keys()
        thresholds.sort()
        while len(thresholds) > 1 and thresholds[0] < cap:
            del thresholds[0]
        lim = thresholds[0]
        self.cap = lim
        self.placements = self.ALL_PLACEMENTS[self.cap]
        self.layoutmap = self.all_layouts[self.cap]

    def __repr__ (self):
        return "{!s}({})".format(self.__class__.__name__, self.cap)

# Explicitly-numbered aliases.
class ArrangerTouchmenu2 (ArrangerTouchmenu):
    def __init__ (self, parent): ArrangerTouchmenu.__init__(self, parent, 2)

class ArrangerTouchmenu4 (ArrangerTouchmenu):
    def __init__ (self, parent): ArrangerTouchmenu.__init__(self, parent, 4)

class ArrangerTouchmenu7 (ArrangerTouchmenu):
    def __init__ (self, parent): ArrangerTouchmenu.__init__(self, parent, 7)

class ArrangerTouchmenu9 (ArrangerTouchmenu):
    def __init__ (self, parent): ArrangerTouchmenu.__init__(self, parent, 9)

class ArrangerTouchmenu12 (ArrangerTouchmenu):
    def __init__ (self, parent): ArrangerTouchmenu.__init__(self, parent, 12)

class ArrangerTouchmenu13 (ArrangerTouchmenu):
    def __init__ (self, parent): ArrangerTouchmenu.__init__(self, parent, 13)

class ArrangerTouchmenu16 (ArrangerTouchmenu):
    def __init__ (self, parent): ArrangerTouchmenu.__init__(self, parent, 16)


class ArrangerRadialmenu (ArrangerEmpty):
    """(on-screen display) radial menu, aka pie menu"""
    NAME = "RadialMenu"
    MAX_ITEMS = 20
    def __init__ (self, parent, cap=2):
        ArrangerEmpty.__init__(self, parent)
        #self.placements = [ (0,6,1,1), (12,6,1,1) ]
        self.placements = {
            '1':  (0,6),
            '2': (12,6),
        }
        self.layoutmap = HidLayoutStore(parent.inpsymprefix)
        for n in range(1,self.MAX_ITEMS+1):
            inpsym = "{}{}".format(self.parent.inpsymprefix, n)
            lbl = inpsym
            prototyp = 'key'
            rowdata = (inpsym, lbl, prototyp, -1, -1, -1, -1)
            self.layoutmap.append(None, rowdata)
        #self.cap = 2
        self.set_capacity(cap)
        self.build_widget_pool()

    def build_widget_pool (self):
        """Create HidTop instances as needed to add into widget_pool, a dict of inpsym to widget."""
        # Generate '1'..'20' inclusive.
        #suffices = [ str(ofs) for ofs in range(1, 21) ]
        #self._populate_widget_pool(suffices)
        self._populate_widget_pool(self.layoutmap)

    def set_capacity (self, cap=2):
        cap = max(1, cap)
        cap = min(cap, self.MAX_ITEMS)
        self.cap = cap
        # Radial places from top going clockwise.
        self.placements.clear()
        for idx in range(0, self.cap):
            angle = idx * (2 * math.pi) / cap
            #theta = math.pi - angle
            theta = - (math.pi / 2) + angle
            w, h = 1, 1
            tx = math.cos(theta)
            ty = math.sin(theta)
            r = 6
            row = int((ty * r) + r + .5)
            col = int((tx * r) + r + .5)
            suffix = "{}".format(idx+1)
            self.placements[suffix] = (row, col, w,h)
            self.layoutmap[idx][3] = col
            self.layoutmap[idx][4] = row
            self.layoutmap[idx][5] = w
            self.layoutmap[idx][6] = h
        for idx in range(cap, self.MAX_ITEMS):
            self.layoutmap[idx][3] = -1
        return

    def __repr__ (self):
        return "{!s}({:d})".format(self.__class__.__name__, self.cap)

class ArrangerMenulist_alternate (ArrangerEmpty):
    """Flat view of menu for brainstorming bind contents.
Buttons crammed into a grid.
Applicable to: touch menu, radial menu, scrollwheel items.
Presents each menu item as an individual HidTop.
"""
    NAME = "menu_list"
    def __init__ (self, parent):
        ArrangerEmpty.__init__(self, parent)
        for idx in range(0,24):
            if idx == 20:
                continue  # ignore/empty
            elif idx in [21,22,23]:
                suffix = [ "u", "c", "d" ][idx-21]
            else:
                suffix = "{}".format(idx+1)
            col = int(idx / 6)
            row = idx % 6
            w, h = 3, 2
            self.placements[suffix] = (row*h, col*w, w-1,h)
        self.build_widget_pool()

    def rearrange (self):
        #self.parent.vadj.set_lower(0)
        #self.parent.vadj.set_upper(12)
        if self.parent.menulist:
            self.parent.menulist.show_all()
        else:
            self.parent.menulist = gtk.TreeView()
            self.parent.stacked.pack_start(self.parent.menulist, True, True, 0)
        self.full_rearrange(self.placements)

class ArrangerMenulist (ArrangerEmpty):
    """Flat view of menu for brainstorming bind contents.
TreeView, where each row corresponds to a hidtop.
Applicable to: touch menu, radial menu, scrollwheel items.
Presents all menuitems in a TreeView.
"""
    NAME = "MenuList"
    def __init__ (self, parent):
        ArrangerEmpty.__init__(self, parent)
        for idx in range(0,24):
            if idx == 20:
                continue  # ignore/empty
            elif idx in [21,22,23]:
                suffix = [ "u", "c", "d" ][idx-21]
            else:
                suffix = "{}".format(idx+1)
            col = int(idx / 6)
            row = idx % 6
            w, h = 3, 2
            self.placements[suffix] = (row*h, col*w, w-1,h)
        self.build_widget_pool()

    def rearrange (self):
        self.parent.stacked.set_visible_child_name("1")
        # TODO: sync data somehow?
        #self.parent.menulist.pull_data()
        self.parent.menulist.update_display()
        #self.parent.menulist.set_vislayers(self.parent.vislayers)



class PseudoStack (gtk.VBox):
    """Mimick GTK3 style Stack widget behavior by using a VBox of VBoxes, juggling visibility attributes and events."""
    def __init__ (self):
        gtk.VBox.__init__(self)
        self.pages = dict()
        self.active = None
        self.connect("map", self.on_map)

    def add_named (self, child, name):
        page = gtk.VBox()
        page.pack_start(child, True, True, 0)
        self.pages[name] = page
        self.pack_start(page, True, True, 0)
        if not self.active:
            self.active = page

    def readjust_visibility (self):
        for page in self.pages.itervalues():
#            (page.show_all if self.active == page else page.hide_all)()
            if page == self.active:
                #page.show_all()
                page.show()
            else:
                page.hide_all()

    def get_visible_child (self):
        return self.active.get_children()[0]
    def get_visible_child_name (self):
        match = [ k for k,v in self.pages if v.get_children()[0] == self.active ]
        return match[0]

    def set_visible_child (self, child):
        for page in self.pages.itervalues():
            if child in page.get_children():
                self.active = page
                break
        self.readjust_visibility()

    def set_visible_child_name (self, name):
        self.active = self.pages[name]
        self.readjust_visibility()

    def on_map (self, w, *args):
        logger.debug("opening page %r" % self.active.get_children()[0])
        self.readjust_visibility()


class HidMenuList (gtk.ScrolledWindow, HidBindable):
    """TreeView of list-based cluster types."""
    def __init__ (self, inpsymprefix, dispstate):
        # Based on ScrollWindowed, containing a TreeView
        gtk.ScrolledWindow.__init__(self)
        if inpsymprefix is None:
            inpsymprefix = ""
        HidBindable.__init__(self, inpsymprefix, dispstate)
        self.inpsymprefix = inpsymprefix
        self.dispstate = dispstate
        # The TreeView
        self.treeview = gtk.TreeView()
        self.rendertext = gtk.CellRendererText()
        nlayers = self.dispstate.inpdescr.get_numlayers()
        self.col0 = gtk.TreeViewColumn("#", self.rendertext, text=0)
        self.treeview.append_column(self.col0)
        self.bindcols = []
        self.renderers = []
        for i in range(nlayers):
            title = "bind%d" % i
            renderer = gtk.CellRendererText()
            renderer.props.background = "gray"
            datacol = i+1
            bind_col = gtk.TreeViewColumn(title, renderer, markup=datacol)
            self.bindcols.append(bind_col)
            self.renderers.append(renderer)
            self.treeview.append_column(bind_col)

        self.add(self.treeview)  # and not with viewport.
        # private model updated from InpDescrModel, prefill with 20 inpsyms.
        # first column = inpsym, following columns follow layers.
        #self.scratch = gtk.ListStore(str,str)
        coldesc = (str,) + (str,)*nlayers
        self.scratch = gtk.ListStore( *coldesc )
        for i in range(0, 20):
            inpsym = "{}{}".format(self.inpsymprefix, i+1)
            self.scratch.append((inpsym,) + (None,)*nlayers)
#        self.pull_data()  # Populate .scratch from InpDescrModel
        self.treeview.set_model(self.scratch)
        # Set up drag-and-drop.
        self.setup_dnd()

#        self.conn_display_adjusted = self.dispstate.connect("display-adjusted", self.on_display_adjusted)
#        self.conn_bind_changed = self.dispstate.inpdescr.connect("bind-changed", self.on_inpdescr_bind_changed)
#        self.conn_label_changed = self.dispstate.inpdescr.connect("label-changed", self.on_inpdescr_label_changed)

        self.show_all()
        self.update_display()

    def get_label (self):
        return self.inpsymprefix
    def set_label (self, v):
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
        self.treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, dnd_targets, dnd_actions)
        self.treeview.connect("drag-data-get", self.on_drag_data_get)
        self.treeview.connect("drag-end", self.on_drag_end)

        # DnD Destination
        dnd_targets = [
          (str(DndOpcodes.REORDER), gtk.TARGET_SAME_WIDGET, DndOpcodes.REORDER),
          (str(DndOpcodes.BIND), gtk.TARGET_SAME_APP, DndOpcodes.BIND),
          (str(DndOpcodes.SWAP), gtk.TARGET_SAME_APP, DndOpcodes.SWAP),
        ]
        dnd_actions = gtk.gdk.ACTION_COPY
        self.treeview.enable_model_drag_dest(dnd_targets, dnd_actions)
        self.treeview.connect("drag-data-received", self.on_drag_data_received)

        self.droppath = None
        self.dropunbind = None

    def on_drag_end (self, w, ctx, *args):
        logger.debug("hidmenulist drag-end")
        if self.dropunbind:
            logger.debug("drop-unbind inpsym %s" % self.dropunbind)
            self.set_bind(self.dropunbind, "")
            self.dropunbind = None
        return True

    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        treesel = w.get_selection()
        mdl, pathsels = treesel.get_selected_rows()
        firstpath = pathsels[0]
        selrow = mdl[firstpath]
        inpsym = selrow[0]
        bind = selrow[1] if selrow[1] is not None else ""
        data = None
        if info == DndOpcodes.REORDER:
            # Reordering.  Encoding source path into string.
            logger.debug("hidmenulist drag-data-get reorder")
            data = repr(firstpath)
        elif info == DndOpcodes.UNBIND:
            logger.debug("hidmenulist drag-data-get unbind")
            data = inpsym
            self.dropunbind = inpsym
        elif info == DndOpcodes.SWAP:
            logger.debug("hidmenulist drag-data-get swap")
            data = inpsym
        if data is not None:
            seldata.set(seldata.target, 8, data)
        return True

    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        """Data that was asked for is now received."""
        srcw = ctx.get_source_widget()
        droppath = self.droppath
        dropinfo = w.get_dest_row_at_pos(x,y)
        destpath, destpos = None, None
        if dropinfo:
            destpath, destpos = dropinfo
        else:
            # all cases rely on dropinfo being valid.
            return False

        if info == DndOpcodes.REORDER:
            logger.debug("hidmenulist reorder")
            # Reordering internally, seldata.data is tree path.
            encoded = seldata.data
            srcpath = ast.literal_eval(encoded)
            func, bias = {
                gtk.TREE_VIEW_DROP_INTO_OR_BEFORE: (self.drag_bind, 0),
                gtk.TREE_VIEW_DROP_INTO_OR_AFTER: (self.drag_bind, 0),
                gtk.TREE_VIEW_DROP_BEFORE: (self.drag_bind, -1),
                gtk.TREE_VIEW_DROP_AFTER: (self.drag_bind, +1),
            }.get(destpos, (None,None))
            logger.debug("reordering internally: %r vs %r" % (srcpath, destpath))
            if callable(func):
                func(*(bias, srcpath, destpath))
            if ctx.action == gtk.gdk.ACTION_MOVE:
                ctx.finish(True, True, time)
            return True
        elif info == DndOpcodes.BIND:
            # bind-drop from commands set, seldata.data is bind (str).
            logger.debug("hidmenulist bind-drop")
            dropinfo = w.get_dest_row_at_pos(x,y)
            seltext = seldata.data
            logger.debug("command-dropping: %r" % seltext)
            self.drop_in_bind(destpath, seltext)
            ctx.finish(True, False, time)
            return True
        elif info == DndOpcodes.SWAP:
            # swap with a hidtop, seldata.data is inpsym.
            logger.debug("hidmenulist swap")
            othersym = seldata.data
            destsym = self.scratch[destpath][0]
            logger.debug("command-swapping: %r,%r" % (destsym, othersym))
            self.swap_bind(destsym, othersym)
            ctx.finish(True, False, time)
            return True
        return False


    def drop_in_bind (self, treepath, newval):
        """Carry out action of (completing) a drop of a command on tree at path."""
        inpsym = self.scratch[treepath][0]
        # TODO: propagate to inpdescr
        return

    def drag_bind (self, bias, srcpath, dstpath):
        # mass pull.
        #listbinds = [ b for s,b in self.scratch ]
        listbinds = [ r[1+self.layer] for r in self.scratch ]
        srcrow = srcpath[0]
        dstrow = dstpath[0]
        srcbind = listbinds[srcrow]
        if bias == 0:
            listbinds[srcrow] = listbinds[dstrow]
            listbinds[dstrow] = srcbind
        else:
            listbinds[srcrow] = None  # Flag for removal.
            if bias < 0:
                listbinds.insert(dstrow, srcbind)
            elif dstrow < len(listbinds):
                listbinds.insert(dstrow+1, srcbind)
            else:
                listbinds.append(srcbind)
#            if srcrow > dstrow:
#                srcrow += 1
#            del listbinds[srcrow]
            listbinds = [ x for x in listbinds if x is not None ]
        # Rebuild scratch from listbinds.
        self.scratch.clear()
#        for h in [ self.conn_bind_changed, self.conn_label_changed, self.conn_layer_changed, self.conn_group_changed ]:
#            self.inpdescr.handler_block(h)
        for i in range(0, len(listbinds)):
            bind = listbinds[i]
            n = i+1
            inpsym = "{}{}".format(self.inpsymprefix, n)
            self.set_bind(inpsym, bind)
            nlayers = self.dispstate.inpdescr.get_numlayers()
            self.scratch.append((inpsym,) + ("",)*nlayers)
#        for h in [ self.conn_bind_changed, self.conn_label_changed, self.conn_layer_changed, self.conn_group_changed ]:
#            self.inpdescr.handler_unblock(h)
        return

#    def pull_data (self):
#        """Synchronize .scratch based on InpDescrModel"""
#        nlayers = self.dispstate.inpdescr.get_numlayers()
#        for row in self.scratch:
#            inpsym = row[0]
#            def visit_bindcol (i, v):
#                bind_markup = self.resolve_bind_markup(inpsym, layer=i)
#                row[1+i] = bind_markup
#            self.foreach_layervis(visit_bindcol)
    def update_dispbinds (self):
        for row in self.scratch:
            # row == (inpsym, bind[0], bind[1], bind[2], ...)
            inpsym = row[0]
            def visit_bindcol (i, v):
                row[1+i] = self.dispbinds[i]
            self.foreach_layervis(visit_bindcol)

    def update_display (self):
        logger.info("menulist update_display")

        def visit_bindcol (i, v):
            if v:
                self.bindcols[i].set_visible(True)
                self.bindcols[i].set_expand(True)
                if i == self.layer:
                    # highlighted layer.
                    usestyle = self.refstyle.base
                else:
                    # unhighlighted layer.
                    usestyle = self.refstyle.bg
                styleval = usestyle[gtk.STATE_NORMAL]
                self.renderers[i].props.background = styleval
            else:
                self.bindcols[i].set_visible(False)
        self.foreach_layervis(visit_bindcol)
        self.queue_draw()
        return

#    def on_inpdescr_bind_changed (self, mdl, grp, lyr, inpsym):
#        self.pull_data()
#    def on_inpdescr_label_changed (self, *args):
#        self.pull_data()
#    def on_inpdescr_layer_changed (self, inpdescr, layernum, *args):
#        self._layer = layernum
#        self.pull_data()
#        self.update_display()
#    def on_inpdescr_group_changed (self, inpdescr, groupnum, *args):
#        self._group = groupnum
#        self.pull_data()
#        self.update_display()



# Does not subclass HidBindable since top-level HidView is not.
class HidCluster (object):
    """Clusters hold a collection of HidTop in particular arrangement.
Nestable.
Tracks HidTop instances belonging to cluster.
Cluster tracks drag-drop activity on nested HidTop.
internal activity:
 - drag from cmdset to hidtop = assign bind: ("bind-assigned", inpsym, bindval)
 - drag from hidtop to hidtop = swap bind: ("bind-swapped", target-inpsym, source-inpsym)
 - drag from hidtop to cmdset/trash = erase bind ("bind-erased", target-inpsym)
external activity:
 - set inpsym for cluster: @property label
 - a bind changed, propagate (as proxy) to internal hidtop: @property Proxy.bind
 - a label changed, propagate (as proxy) to the internal hidtop: @property Proxy.label
 - vislayers changed, update internal hidtops: @property layervis

 + remove all nested elements: clear_board()
 + place nested elements into position: populate_board()
 + show/refresh relevant nested elements: update_display()

Base class for:
* HidPlanar - Steam Controller touchpad personality
* HidBoard - toplevel view.

set_bind proxy:
 * INPSYM.bind()
    => Cluster.Proxy(INPSYM).bind()
    => Cluster.subtop.bind(), Cluster.bookkeeping()
~~ set_label proxy



Properties, direct:
@property label : str = label for hid cluster, if applicable (e.g. HidPlanar)
@property layoutmap : HidLayoutStore
@property hidtops : dict[] = dict of nested HidBindable, keyed by inpsym

"""
    def __init__ (self, hidparent, inpsymprefix, dispstate):
        self.__init__gtk__(inpsymprefix)
        self.hidparent = hidparent
        self.layoutmap = None
        self._hidlabel = None
        self.hidtops = dict()
        self.dispstate = dispstate

    def __init__gtk__ (self, inpsymprefix):
        pass

    def build_cluster (self):
        """Build cluster internals, delegated by __init__.
Override in subclasses.
"""
        pass

    def make_hidtop (self, inpsym):
        """Factory function to generate an immediately nested HidTop."""
        inst = None
        #inst = HidTopProxy(inpsym, None)
        #inst = HidTopProxy(self, inpsym)
        return inst

    def make_hidplanar (self, inpsym):
        """Factory function to generate nested HidPlanar."""
        pass

    def get_label (self):
        return self._hidlabel
    def set_label (self, v):
        self._hidlabel = v
        self.update_hidlabel()
    hidlabel = property(get_label, set_label)

    def get_layoutmap (self):
        return self.layoutmap
    def set_layoutmap (self, layoutval):
        self.layoutmap = layoutval

    def get_hidtops (self):
        return self.hidtops
    def set_hidtops (self, val):
        self.hidtops = val

    def get_subelt (self, inpsym):
        hidelt = self.hidtops.get(inpsym, None)
        return hidelt


    def clear_board (self):
        pass

    def populate_board (self):
        pass

    def setup_signals (self):
        pass


    def update_layervis (self, v):
        """Updates the layer visibility list(of bool)"""
        return

    def update_hidlabel (self):
        """Override in subclasses.
Update any relevant HID element label."""
        return



    def get_dispstate (self):
        return self.dispstate
    def set_dispstate (self, val):
        self.dispstate = val
        for elt in self.hidtops.valueiter():
            elt.set_dispstate(val)

    def update_display (self):
        pass

    def refresh_hie (self, inpsym):
        pass

    def on_display_adjusted (self, ds, *args):
        return

    def on_inpdescr_bind_changed (self, mdl, group, layer, inpsym):
        return

    def on_inpdescr_label_changed (self, mdl, inpsym):
        return



class HidPlanar (gtk.EventBox, HidBindable):
    """Planar control cluster (stick, touchpad, etc.)
Contents to display are packaged in a data model (InpDescrModel)
Children are HidTop, but selectively shown and placed to reflect cluster type.

As arrangments can change during run-time, use strategies for rearranging:
* (d) Dpad : u,d,l,r,c
* (b) Diamond : n,e,w,s,c
* (m) Mouse : x,y,c
* (u) MouseRegion :
* (j) Joystick {Move,Camera,Mouse} : x-, x+, y-, y+, c
* (g) GyroTilt : x-, x+, y-, y+, w-, w+
* (t) Menu.Touch {2,4,7,9,12,13,16) : #1..#16
* (r) RadialMenu {1..20} : #1..#20
* (l) MenuList {1..20} : #1..#20
* (o) OneButton : o
* (s) LayoutStore : ...
"""

    def __init__ (self, inpsymprefix, dispstate):
        """Initialize with given data model, and the input symbol prefix tied to this hidtop"""
        # UI elements
        gtk.EventBox.__init__(self)
        HidBindable.__init__(self, inpsymprefix, dispstate)

        self.inpsymprefix = inpsymprefix
        self.hid_label = self.inpsymprefix  # initialize with copy.
        self.dispstate = dispstate
        self.hidtops = dict()  # Mapping of inpsym to HidTop instance.
        self.clusters = dict()

        self.frame = gtk.Frame(inpsymprefix)
        # Frame title: [ HBox: [Button>Menu] [Label] ]
        self.frame_title = gtk.HBox()
        self.frame_lbl_sym = gtk.Label()
        self.frame_btn = gtk.Button(unichr(0x2026))
        self.frame_btn.set_tooltip_text("Change variant for this planar cluster")
        if inpsymprefix:
            # Add decoration to non-root Planar (i.e. inpsyprefix is True-ish)
            self.frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
            self.frame_title.pack_start(self.frame_btn, False, False, 0)
            self.frame_title.pack_start(self.frame_lbl_sym, False, False, 0)
            self.frame.set_label_widget(self.frame_title)
        else:
            # top-level (root) Planar has inpsymprefix value that is False-ish.
            self.frame.set_shadow_type(gtk.SHADOW_NONE)

        # Table is (3x3), (4x4), or (6x6); LCD=(12,12), use multiple cells per widget.
        self.grid = gtk.Table(12,12,True)

        # Stacked view: first layer = the grid; second layer = menulist view
        self.stacked = PseudoStack()
        self.menulist = HidMenuList(self.inpsymprefix, self.dispstate)
        self.stacked.add_named(self.grid, "0")
        self.stacked.add_named(self.menulist, "1")

        self.frame.add(self.stacked)
        self.add(self.frame)

        self.setup_arrangers()
        self.setup_ctxmenu()

        #self.show_all()
        #self.update_display()
        self.connect("map", self.on_map)

    def on_map (self, *args):
        #self.update_display()
        return True

    def get_label (self):
        return self.hid_label
    def set_label (self, v):
        self.hid_label = v
        self.update_label()

    def get_layoutmap (self):
        return self.arrangerStored.get_layoutmap()
    def set_layoutmap (self, val):
        self.arrangerStored.set_layoutmap(val)

#    def update_layervis (self):
#        for ch in self.grid.get_children():
#            try:
#                ch.set_layervis(self.layervis)
#            except AttributeError:
#                pass
#            except:
#                raise
#        self.menulist.set_layervis(self.layervis)

    def arrangerTouchmenu (self, cap=2):
        self.detach_all()
        self.arrangerTouchmenu0.set_capacity(cap)
        return self.arrangerTouchmenu0
    def arrangerRadialmenu (self, cap=2):
        self.detach_all()
        self.arrangerRadialmenu0.set_capacity(cap)
        return self.arrangerRadialmenu0
    def setup_arrangers (self):
        self.arrangerEmpty = ArrangerEmpty(self)
        self.arrangerOneButton = ArrangerOneButton(self)
        self.arrangerScrollwheel = ArrangerScrollwheel(self)
        self.arrangerDpad = ArrangerDpad(self)
        self.arrangerDiamond = ArrangerDiamond(self)
        self.arrangerButtons = ArrangerDiamond(self)
        self.arrangerMouse = ArrangerMouse(self)
        self.arrangerMouseRegion = ArrangerMouseRegion(self)
        self.arrangerJoystick = ArrangerJoystick(self)
        self.arrangerGyrotilt = ArrangerGyrotilt(self)
        self.arrangerTouchmenu0 = ArrangerTouchmenu(self, 2)
        self.arrangerRadialmenu0 = ArrangerRadialmenu(self, 2)
        self.arrangerMenulist = ArrangerMenulist(self)
        self.arrangerStored = ArrangerStored(self, None)

        self.arranger = self.arrangerEmpty

    def update_label (self):
        #self.frame.set_label("{} <{!s}>".format(self.inpsymprefix, self.arranger.NAME))
        #self.frame_lbl_sym.set_label(" {} <{!s}>".format(self.inpsymprefix, self.arranger.NAME))
        #self.frame_lbl_sym.set_markup("<a href='#a'>{} &lt;{!s}&gt;</a>".format(self.inpsymprefix, self.arranger.NAME))
        self.frame_lbl_sym.set_label(" {} <{!s}>".format(self.hid_label, self.arranger.NAME))

    def find_arranger (self, name):
        match = [ a for a in self.__dict__.itervalues() if isinstance(a, ArrangerEmpty) and a.NAME == name ]
        if match:
            return match[0]
        return None
    def get_arranger (self):
        return self.arranger
    def set_arranger (self, arranger):
        oldval = self.arranger
        if callable(arranger):
            self.arranger = arranger()
        elif arranger is None:
            self.arranger = self.arrangerEmpty
        else:
            self.arranger = arranger
        self.update_label()
        self.arranger.rearrange()
        #self.show_all()
        #self.grid.show_all()
        self.grid.show()
        # save cluster type by name into InpDescrModel, using this input's prefix as the key, in group 0 layer 0.
        #self.set_bind(self.inpsymprefix, self.arranger.NAME, 0, 0)
        self.emit("cluster-type-changed", oldval.NAME, self.arranger.NAME)

    def on_inpdescr_bind_changed (self, inpdescr, group, layer, inpsym):
        # Ignore bind changes for the inpsym prefix (saving cluster type).
        pass

    def get_cluster_type (self):
        return self.arrange.NAME
    def set_cluster_type (self, cltype):
        arranger = self.find_arranger(cltype)
        self.set_arranger(arranger)
        return

    def contains_inpsym (self, inpsym):
        return (inpsym in self.hidtops)
    def refresh_hie (self, inpsym):
        # Update label and/or bind.
        logger.debug("hidplanar refresh_hie")
        self.rearranger.rearrange()
        pass


    def make_hidelt (self, layout_store_row):
        eltdata = layout_store_row
        inpsym, lbl, prototyp = eltdata[0], eltdata[1], eltdata[2]
        if not inpsym in self.hidtops:
            hidtop = None
            if prototyp == 'cluster':
                planar = HidPlanar(inpsym, self.dispstate)
                for subsym,subelt in planar.hidtops.iteritems():
                    self.hidtops[subsym] = subelt
                    lbltext = planar.arranger.layoutmap.get_label(subsym)
                    if lbltext:
                        subelt.set_label(lbltext)
                    self.active = subelt
                attach_tweaks = {
                    'xoptions': gtk.FILL,
                    'yoptions': gtk.FILL,
                    'xpadding': 4,
                    'ypadding': 4,
                }
                self.clusters[inpsym] = planar
                self.hidtops[inpsym] = planar
                #planar.show_all()
                planar.show()
                planar.update_display()
                planar.connect('cluster-type-changed', self.on_subplanar_cluster_type_changed)
                hidtop = planar
            elif prototyp == 'key':
                lbltext = lbl
                hidtop = HidTop(inpsym, self.dispstate)
                hidtop.set_label(lbltext)
                self.hidtops[inpsym] = hidtop
                self.active = hidtop
                #hidtop.show_all()
                hidtop.show()

            else:
                pass
            hidtop.set_layer(self.get_layer())
            hidtop.set_layervis(self.get_layervis())
            hidtop.connect('bind-assigned', self.on_subelt_bind_assigned)
            hidtop.connect('bind-swapped', self.on_subelt_bind_swapped)
            hidtop.connect('bind-erased', self.on_subelt_bind_erased)
        return


    def make_menu (self, menudesc):
        menu = gtk.Menu()
        for itemdesc in menudesc:
            menuitem = gtk.MenuItem(itemdesc[0], True)
            if type(itemdesc[1]) == list:
                # submenu
                submenu = self.make_menu(itemdesc[1])
                menuitem.set_submenu(submenu)
            else:
                # leaf
                menuitem.userdata = itemdesc[1]
            menu.append(menuitem)
        menu.show_all()
        return menu

    def make_context_menu (self, menu_title=None):
        """Create context menu of changing cluster types by GUI."""
        context_menu_desc = [
            # Tuples of (item_lable, arranger_factory)
            ( "_None", self.arrangerEmpty ),
            ( "_Fixed", self.arrangerStored ),
            ( "_SingleButton", self.arrangerOneButton ),
            ( "Scroll_Wheel", self.arrangerScrollwheel ),
            ( "_DPad", self.arrangerDpad ),
            ( "_ButtonQuad", self.arrangerButtons ),
            ( "_Mouse", self.arrangerMouse ),
            ( "_Joystick", self.arrangerJoystick ),
            ( "_GyroTilt", self.arrangerGyrotilt ),
            ( "_Touch Menu", [
                ( "_2 items", lambda: self.arrangerTouchmenu(2) ),
                ( "_4 items", lambda: self.arrangerTouchmenu(4) ),
                ( "_7 items", lambda: self.arrangerTouchmenu(7) ),
                ( "_9 items", lambda: self.arrangerTouchmenu(9) ),
                ( "_12 items", lambda: self.arrangerTouchmenu(12) ),
                ( "_13 items", lambda: self.arrangerTouchmenu(13) ),
                ( "_16 items", lambda: self.arrangerTouchmenu(16) ),
                ]),
            ( "_Radial Menu", [
                ( "_01..09 items", [
                    ("_1 item", lambda: self.arrangerRadialmenu(1) ),
                    ("_2 items", lambda: self.arrangerRadialmenu(2) ),
                    ("_3 items", lambda: self.arrangerRadialmenu(3) ),
                    ("_4 items", lambda: self.arrangerRadialmenu(4) ),
                    ("_5 items", lambda: self.arrangerRadialmenu(5) ),
                    ("_6 items", lambda: self.arrangerRadialmenu(6) ),
                    ("_7 items", lambda: self.arrangerRadialmenu(7) ),
                    ("_8 items", lambda: self.arrangerRadialmenu(8) ),
                    ("_9 items", lambda: self.arrangerRadialmenu(9) ),
                    ]),
                ( "_10..19 items", [
                    ("1_0 items", lambda: self.arrangerRadialmenu(10)),
                    ("1_1 items", lambda: self.arrangerRadialmenu(11)),
                    ("1_2 items", lambda: self.arrangerRadialmenu(12)),
                    ("1_3 items", lambda: self.arrangerRadialmenu(13)),
                    ("1_4 items", lambda: self.arrangerRadialmenu(14)),
                    ("1_5 items", lambda: self.arrangerRadialmenu(15)),
                    ("1_6 items", lambda: self.arrangerRadialmenu(16)),
                    ("1_7 items", lambda: self.arrangerRadialmenu(17)),
                    ("1_8 items", lambda: self.arrangerRadialmenu(18)),
                    ("1_9 items", lambda: self.arrangerRadialmenu(19)),
                    ]),
                ( "_20.._29 items", [
                    ("2_0 items", lambda: self.arrangerRadialmenu(20)),
                    ]),
                ]),
            ( "_List Menu", self.arrangerMenulist ),
            ]
        menu = self.make_menu(context_menu_desc)
        if menu_title:
            title = gtk.MenuItem(menu_title, False)
            title.set_sensitive(False)
            menu.prepend(title)
        menu.show_all()
        return menu

    def setup_ctxmenu (self):
        self.ctxmenu = self.make_context_menu(self.inpsymprefix)
        self.connect_menuitems(self.ctxmenu)
        self.connect_ctxmenu()

    def connect_menuitems (self, submenu=None):
        if not submenu:
            return
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

    def connect_ctxmenu (self):
        if 0:  # TODO: conditional guard, based on Preferences?
            self.connect("button-press-event", self.on_button_press)
        self.frame_btn.connect("clicked", self.on_cluster_menu)

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

    def on_cluster_menu (self, w, *args):
        self.ctxmenu.popup(None,None,None,1,0)
        return True

    def on_context_menuitem (self, w, userdata):
        arranger = userdata
        if arranger:
            self.set_arranger(arranger)
        return True

    def update_display (self):
        logger.info("hidplanar update_display")
        self.detach_all()
        # Retrieve intended cluster type by name from InpDescrModel, using this input's prefix as the key, in group 0 layer 0.
        # TODO: update cluster type from outside
#        cluster_type = self.get_bind(self.inpsymprefix, 0, 0)
#        self.set_cluster_type(cluster_type)
        if self.arranger:
            self.arranger.rearrange()
        logger.info(" > menulist update_display")
        self.menulist.update_display()
        gtk.Frame.show_all(self)
        #self.show_all()
        #self.frame_title.show_all()
        return

    def detach_all (self):
        """Remove all widgets from table."""
#        for k,v in self.hidtops.iteritems():
#            v.hide()
#            if v.get_parent() != None:
#                self.grid.remove(v)
        for ch in self.grid.get_children():
            ch.hide()
            self.grid.remove(ch)

    def get_hidtops (self):
        return self.hidtops.values()

    def on_subplanar_cluster_type_changed (self, w, old, updated):
        pass
    def on_subelt_bind_assigned (self, hidelt, inpsym, bindval):
        logger.debug("on_subelt_bind_assigned %r, %r, %r" % (hidelt, inpsym, bindval))
        self.emit("bind-assigned", inpsym, bindval)
        return True
    def on_subelt_bind_swapped (self, hidelt, target_inpsym, source_inpsym):
        self.emit("bind-swapped", target_inpsym, source_inpsym)
        return True
    def on_subelt_bind_erased (self, hidelt, inpsym):
        self.emit("bind-erased", inpsym)
        return True


    def get_group (self):
        return self._group
    def set_group (self, v):
        self._group = v
    def update_group (self):
        # TODO: update bind displays.
        pass

    def get_layer (self):
        return self._layer
    def set_layer (self, v):
        """Set current layer, propagagte to children."""
        logger.debug("%s set_layer %r" % (self.__class__.__name__, v))
        self._layer = v
        self.update_layer()
    def update_layer (self):
        ## what the first visibile layer is.
        #baselayer = self._vislayers * (self._layer / self._vislayers)
        ## how many layers to show at once.
        #visspan = self._vislayers
        ## update children to:
        for ch in self.hidtops.itervalues():
            ch.set_layer(self._layer)
        for cl in self.clusters.itervalues():
            cl.set_layer(self._layer)

    def get_layervis (self):
        return self._layervis
    def set_layervis (self, v):
        self._layervis = v
        self.update_layervis()
    def update_layervis (self):
        for ch in self.hidtops.itervalues():
            ch.set_layervis(self._layervis)
        for cl in self.clusters.itervalues():
            cl.set_layervis(self._layervis)
        self.menulist.set_layervis(self.layervis)
        

#    __gsignals__ = HidBindable.__gsignals__.copy().update({
#      "cluster-type-chnaged": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
#      })
    __gsignals__ = dict(
      [ (k,v) for k,v in HidBindable.__gsignals__.iteritems() ]
      +
      [ (k,v) for k,v in {
        "cluster-type-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
      }.iteritems() ]
    )

#gobject.type_register(HidPlanar)
#gobject.signal_new("cluster-type-changed", HidPlanar, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING))


implicit_layouts = HidLayouts()
implicit_layouts.build_from_legacy_store()




class BindableLayoutWidget (gtk.VBox):
    """Controller wrapper to BindablwLayoutView.
"""
    def __init__ (self, all_layouts, init_layout=None):
        # TODO: use init_layout for initial layoutname.
        gtk.VBox.__init__(self)
        self.all_layouts = None
        if self.all_layouts is None:
            self.all_layouts = implicit_layouts

        self.setup_widget()

        # dumb struct, track signal handler ids.
        class signal_handlers:
            clicked = dict()
            cluster_type_changed = dict()
            bind_assigned = dict()
            bind_swapped = dict()
            bind_erased = dict()
        self.signal_handlers = signal_handlers

#        self.rebuild_display()

        self.setup_signals()

    def setup_state (self):
        self._activename = None
        self._activehid = None

    def setup_widget (self):
        class ui:
            pass
        self.ui = ui

        # Primary bindables view.
        #self.ui.hidview = BindableCluster("")
        self.ui.hidview = BindableLayoutView([True], implicit_layouts['en_US (pc104)'])

        # Data model for layout selector.
        self.mdl_layout = gtk.ListStore(str)
        hidnames = sorted(self.all_layouts.keys())
        for k in hidnames:
            self.mdl_layout.append((k,))

        # Row with layout selector.
        self.ui.sel_layout = self.LayoutSelectorWidget(self.mdl_layout)
        self.ui.lbl_layout = gtk.Label("Layout:")
        self.ui.row_layout = gtk.HBox()
        self.ui.row_layout.pack_start(self.ui.lbl_layout, False, False, 0)
        self.ui.row_layout.pack_start(self.ui.sel_layout, False, False, 0)

        # Data model for group selector.
        self.mdl_groups = gtk.ListStore(int, str)
        for datum in [ (0,"Global"), (1,"Menu"), (2,"Game") ]:
            self.mdl_groups.append(datum)

        # Row with group selector.
        self.ui.sel_group = self.GroupSelectorWidget(self.mdl_groups)

        # Row with layer selector.
        self.ui.sel_layer = self.LayerSelectorWidget()

        self.pack_start(self.ui.row_layout, False, False, 0)
        self.pack_start(self.ui.sel_group, False, False, 0)
        self.pack_start(self.ui.sel_layer, False, False, 0)
        self.pack_start(self.ui.hidview, False, False, 0)
        #self.hidview.show()
        #self.show_all()
        self.ui.row_layout.show_all()
        self.ui.sel_group.show_all()
        self.ui.sel_layer.show_all()
        self.ui.hidview.show()

        # Initial layout.
        idx = self.ui.sel_layout.get_active()
        val = self.mdl_layout[idx][0]
        self.activename = val  # trigger update_activehid()

    def setup_signals (self):
        self.ui.sel_layout.connect('changed', self.on_layout_changed)
        return

    def LayoutSelectorWidget (self, mdl_layouts):
        # Combo (drop) list.
        selector = gtk.ComboBox(mdl_layouts)
        selector.cell_layout = gtk.CellRendererText()
        selector.pack_start(selector.cell_layout)
        selector.add_attribute(selector.cell_layout, 'text', 0)
        selector.set_active(0)
        return selector

    def on_layout_changed (self, w, *args):
        idx = w.get_active()
        data = self.mdl_layout[idx]
        val = data[0]
        self.activename = val   # trigger update_activehid()
        #self.activehid = self.all_layouts[val]
        #self.hidview.set_layoutmap(self.activehid)
        # TODO: propagate binds to newly revealed clusters.
        self.show()

    def GroupSelectorWidget (self, mdl_groups):
        selector = gtk.Frame("Group")
        selector.mdl = mdl_groups
        selector.row = gtk.HBox()
        selector.btnbox = gtk.HButtonBox()
        selector.buttons = None

        def rebuild_buttons (w):
            if w.buttons:
                for btn in w.buttons:
                    w.buttonbox.remove(btn)
            w.buttons = list()
            for grpid in range(len(w.mdl)):
                # Radio group is first button; make leader if no buttons.
                grp = w.buttons[0] if w.buttons else None
                lbl = w.mdl[grpid][1]  # second column => displayed name.
                btn = gtk.RadioButton(grp, lbl)
                btn.groupnum = grpid
                btn.connect('toggled', self.on_group_toggled)
                w.buttons.append(btn)
                w.btnbox.add(btn)
            w.row.show_all()
            return
        selector.rebuild_buttons = lambda: rebuild_buttons(selector)
        def on_data_changed (w, mdl, *args):
            rebuild_buttons(selector)
        selector.on_data_changed = lambda *args: on_data_changed(selector, *args)

        selector.mdl.connect("row-changed", selector.on_data_changed)
        selector.mdl.connect("row-deleted", selector.on_data_changed)
        selector.mdl.connect("row-inserted", selector.on_data_changed)

        selector.rebuild_buttons()
        selector.row.pack_start(selector.btnbox, expand=False)
        selector.add(selector.row)
        return selector

    def on_group_toggled (self, w, *args):
        if w.get_active():
            self.ui.hidview.set_group(w.groupnum)
            pass

    def LayerSelectorWidget (self):
        selector = gtk.Frame("Layer")
        selector.row = gtk.HBox()
        selector.btnbox = gtk.HButtonBox()
        selector.buttons = list()

        maxshifters = 3
        maxlayers = (1 << maxshifters)

        for lyrnum in range(0, maxlayers):
            sh = []
            # List the shifters that are involved in activating this layer.
            for b in range(0, maxshifters):
                if (lyrnum & (1 << b)):
                    sh.append("^%s" % (b+1))
            if sh:
                lbl = "{} ({})".format(lyrnum, " + ".join(sh))
            else:
                lbl = "base"
            # Group leader is first button; use None to become group leader.
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
        if w.get_active():
            # Turn on.
            self.ui.hidview.set_layer(w.layernum)


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
        self.update_vis()
    vis = property(get_vis, set_vis)

    def update_vis (self):
        for ch in self.grid.children():
            ch.set_vis(self.vis)
        return

#    def rebuild_display (self):
#        # Update visuals to reflect active layout.
#        self.hidview.set_layoutmap(self.activehid)
#
#    def on_active_layout_changed (self, w, *args):
#        idx = w.get_active()
#        data = self.mdl_layout[idx]
#        val = data[0]
#        self.activename = val
#        self.activehid = self.all_layouts[val]
#        #self.clear_board()
#        #self.fill_board(self.activehid)
#        #self.show_all()
#        self.rebuild_display()
#        self.show()
##        self.emit("layout-changed", val)




class HidLayoutWidget (gtk.VBox):
    """Controller wrapper to HidLayoutView.
"""
    def __init__ (self, dispstate=None, all_layouts=None):
        gtk.VBox.__init__(self)
        self.dispstate = dispstate
        self.active = False
        self.all_layouts = None
        if self.all_layouts is None:
            self.all_layouts = implicit_layouts

        # Selector for specific layout.
        self.build_layout_selector()   # .mdl_layout, .row_layout

        # GUI for HID Layout.
        #self.hidview = HidView2(self, "", self.dispstate)
        self.hidview = HidPlanar("", self.dispstate)

        self.layersel = self.LayerSelectorWidget()

        # TODO: from outside.
        mdl_groups = gtk.ListStore(int, str)
        mdl_groups.append((0, "Global"))
        mdl_groups.append((1, "Menu"))
        mdl_groups.append((2, "Game"))
        self.groupsel = self.GroupSelectorWidget(mdl_groups)

        # Initial layout.
        idx = self.inp_layout.get_active()
        val = self.mdl_layout[idx][0]
        #self.activehid = HidLayoutStore(val)
        #self.activehid.build_from_rowrun(self.hiddesc[val])
        self.activename = val
        self.activehid = self.all_layouts[val]
        #self.fill_board(self.activehid)

        # Compose GUI.
        self.pack_start(self.row_layout, expand=False, fill=False)
        self.pack_start(self.groupsel, expand=False, fill=False)
        self.pack_start(self.layersel, expand=False, fill=False)
        self.pack_start(self.hidview, expand=False, fill=False)

        # dumb struct, track signal handler ids.
        class signal_handlers:
            clicked = dict()
            cluster_type_changed = dict()
            bind_assigned = dict()
            bind_swapped = dict()
            bind_erased = dict()
        self.signal_handlers = signal_handlers

        self.dispstate.connect("layer-changed", self.on_dispstate_layer_changed)
        self.dispstate.connect("group-changed", self.on_dispstate_group_changed)
        self.dispstate.connect("display-adjusted", self.on_dispstate_display_adjusted)

        self.rebuild_display()

    def build_layout_selector (self):
        # Data model for selector.
        self.mdl_layout = gtk.ListStore(str)
        hidnames = sorted(self.all_layouts.keys())
        for k in hidnames:
            self.mdl_layout.append((k,))

        # Combo (drop) list.
        self.inp_layout = gtk.ComboBox(self.mdl_layout)
        self.cell_layout = gtk.CellRendererText()
        self.inp_layout.pack_start(self.cell_layout)
        self.inp_layout.add_attribute(self.cell_layout, 'text', 0)
        self.inp_layout.set_active(0)
        self.inp_layout.connect('changed', self.on_active_layout_changed)

        # Label for selector.
        self.lbl_layout = gtk.Label("Layout:")

        # Compose GUI.
        self.row_layout = gtk.HBox()
        self.row_layout.pack_start(self.lbl_layout, expand=False, fill=False)
        self.row_layout.pack_start(self.inp_layout, expand=False, fill=False)


    def GroupSelectorWidget (self, mdl_groups):
        selector = gtk.Frame("Group")
        selector.mdl = mdl_groups
        selector.row = gtk.HBox()
        selector.btnbox = gtk.HButtonBox()
        selector.buttons = None

        def rebuild_buttons (w):
            if w.buttons:
                for btn in w.buttons:
                    w.buttonbox.remove(btn)
            w.buttons = list()
            for grpid in range(len(w.mdl)):
                # Radio group is first button; make leader if no buttons.
                grp = w.buttons[0] if w.buttons else None
                lbl = w.mdl[grpid][1]  # second column => displayed name.
                btn = gtk.RadioButton(grp, lbl)
                btn.groupnum = grpid
                btn.connect('toggled', self.on_group_toggled)
                w.buttons.append(btn)
                w.btnbox.add(btn)
            w.row.show_all()
            return
        selector.rebuild_buttons = lambda: rebuild_buttons(selector)
        def on_data_changed (w, mdl, *args):
            rebuild_buttons(selector)
        selector.on_data_changed = lambda *args: on_data_changed(selector, *args)

        selector.mdl.connect("row-changed", selector.on_data_changed)
        selector.mdl.connect("row-deleted", selector.on_data_changed)
        selector.mdl.connect("row-inserted", selector.on_data_changed)

        selector.rebuild_buttons()
        selector.row.pack_start(selector.btnbox, expand=False)
        selector.add(selector.row)
        return selector

    def on_group_toggled (self, w, *args):
        if w.get_active():
            self.hidview.set_group(w.groupnum)
            pass

    def LayerSelectorWidget (self):
        selector = gtk.Frame("Layer")
        selector.row = gtk.HBox()
        selector.btnbox = gtk.HButtonBox()
        selector.buttons = list()

        maxshifters = 3
        maxlayers = (1 << maxshifters)

        for lyrnum in range(0, maxlayers):
            sh = []
            # List the shifters that are involved in activating this layer.
            for b in range(0, maxshifters):
                if (lyrnum & (1 << b)):
                    sh.append("^%s" % (b+1))
            if sh:
                lbl = "{} ({})".format(lyrnum, " + ".join(sh))
            else:
                lbl = "base"
            # Group leader is first button; use None to become group leader.
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
        if w.get_active():
            # Turn on.
            self.hidview.set_layer(w.layernum)


    def get_dispstate (self):
        return self.dispstate
    def set_dispstate (self, dispstate):
        self.dispstate = dispstate
        self.hidview.set_dispstate(dispstate)

    def get_layouts (self):
        return self.all_layouts
    def set_layouts (self, val):
        self.all_layouts = val

    def get_active (self):
        return self.activename
    def set_active (self, val):
        self.activename = val
        self.activehid = self.all_layouts[val]
        # TODO: update display
        self.rebuild_display()

    def get_vislayers (self):
        return self.dispstate.vislayers
    def set_vislayers (self, v):
        self.dispstate.set_vislayers(v)

    def rebuild_display (self):
        # Update visuals to reflect active layout.
        self.hidview.set_layoutmap(self.activehid)
        self.hidview.set_arranger(self.hidview.arrangerStored)
#        self.hidview.build_cluster()
#        for hidtop in self.hidview.hidtops.itervalues():
#            hidtop.connect('clicked', self.on_hidtop_clicked)
        def stash_signal_handler (w, handler_store, signal_name, signal_handler):
            logger.debug('stashing signal %r.%r' % (w.inpsym, signal_name))
            if not w.inpsym in handler_store:
                sh = None
                try:
                    sh = w.connect(signal_name, signal_handler)
                except TypeError:
                    pass
                if sh:
                    handler_store[w.inpsym] = sh
                    logger.debug("connect handler(%r,%r) = %r" % (w.inpsym, signal_name, signal_handler))
            return

        for inpsym in self.hidview.hidtops:
            hidelt = self.hidview.hidtops.get(inpsym, None)
            if not hidelt:
                continue
            if not inpsym in self.signal_handlers.clicked:
                sh = None
                try:
                    # Connect 'clicked' signal for those that support it.

                    sh = hidelt.connect('clicked', self.on_hidtop_clicked)
                except TypeError:
                    pass
                if sh:
                    self.signal_handlers.clicked[inpsym] = sh
                bindgrp = self.dispstate.resolve_bind_group_markup(inpsym)
                hidelt.set_dispbinds(bindgrp)

            stash_signal_handler(hidelt, self.signal_handlers.bind_assigned, "bind-assigned", self.on_bind_assigned)
            stash_signal_handler(hidelt, self.signal_handlers.bind_swapped, "bind-swapped", self.on_bind_swapped)
            stash_signal_handler(hidelt, self.signal_handlers.bind_erased, "bind-erased", self.on_bind_erased)

        for symprefix in self.hidview.clusters:
            hidcluster = self.hidview.clusters.get(symprefix, None)
            if not hidcluster:
                continue
            if not symprefix in self.signal_handlers.cluster_type_changed:
                sh = None
                try:
                    sh = hidcluster.connect('cluster-type-changed', self.on_cluster_type_changed)
                except TypeError:
                    pass
                if sh:
                    self.signal_handlers.cluster_type_changed[symprefix] = sh

            stash_signal_handler(hidcluster, self.signal_handlers.bind_assigned, "bind-assigned", self.on_bind_assigned)
            stash_signal_handler(hidcluster, self.signal_handlers.bind_swapped, "bind-swapped", self.on_bind_swapped)
            stash_signal_handler(hidcluster, self.signal_handlers.bind_erased, "bind-erased", self.on_bind_erased)
        return

    def on_active_layout_changed (self, w, *args):
        idx = w.get_active()
        data = self.mdl_layout[idx]
        val = data[0]
        self.activename = val
        self.activehid = self.all_layouts[val]
        #self.clear_board()
        #self.fill_board(self.activehid)
        #self.show_all()
        self.rebuild_display()
        self.show()
#        self.emit("layout-changed", val)


    def __getitem__ (self, inpsym):
        return self.hidtops[inpsym]

    def __setitem__ (self, inpsym, val):
        self.hidtops[inpsym].bind = val

    def __delitem__ (self, inpsym):
        del self.hidtops[inpsym]


    def on_hidtop_clicked (self, w, *args):
        inpsym = w.inpsym
        logger.debug("target: %s" % inpsym)
        self.emit("key-selected", inpsym)

    def on_cluster_type_changed (self, w, *args):
        pass

    def on_bind_assigned (self, w, inpsym, bindval):
        logger.debug("bind-assign %r <- %r" % (inpsym, bindval))
        self.dispstate.set_bind(inpsym, bindval)
        grpbind = self.dispstate.resolve_bind_group_markup(inpsym)
        logger.debug("grpbind(%s) = %r" % (inpsym, grpbind))
        hidtop = self.hidview.hidtops.get(inpsym, None)
        if hidtop:
            hidtop.set_dispbinds(grpbind)
    def on_bind_swapped (self, w, srcsym, dstsym):
        logger.debug("bind-swap %r <-> %r" % (srcsym, dstsym))
        bindmdl = self.dispstate
        srcbind = bindmdl.get_bind(srcsym)
        dstbind = bindmdl.get_bind(dstsym)
        bindmdl.set_bind(srcsym, dstbind)
        bindmdl.set_bind(dstsym, srcbind)
        grpbind = self.dispstate.resolve_bind_group_markup(srcsym)
        hidtop = self.hidview.hidtops.get(srcsym, None)
        if hidtop:
            hidtop.set_dispbinds(grpbind)
        grpbind = self.dispstate.resolve_bind_group_markup(dstsym)
        hidtop = self.hidview.hidtops.get(dstsym, None)
        if hidtop:
            hidtop.set_dispbinds(grpbind)
    def on_bind_erased (self, w, inpsym):
        self.dispstate.set_bind(inpsym, "")
        grpbind = self.dispstate.resolve_bind_group_markup(inpsym)
        hidtop = self.hidview.hidtops.get(inpsym, None)
        if hidtop:
            hidtop.set_dispbinds(grpbind)

    def on_dispstate_layer_changed (self, mdl, newlayer):
        # TODO: Update all children for new layer.
        pass
    def on_dispstate_group_changed (self, mdl, newgroup):
        # TODO: update all children for new group...
        pass
    def on_dispstate_display_adjusted (self, mdl):
        # TODO: redraw?...
        pass

#    def on_bind_changed (self, w, *args):
#        #self.bindmap[w.inpsym] = w.bind
#        self.emit("bind-changed", w)
#
#    def on_bindid_changed (self, w, *args):
#        #print("HidLayoutWidget: bindid-changed")
#        #self.bindmap[w.inpsym] = w.bind
#        self.emit("bindid-changed", w)


# Set up signals.
gobject.type_register(HidLayoutWidget)
gobject.signal_new("key-selected", HidLayoutWidget, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (str,))
gobject.signal_new("bind-changed", HidLayoutWidget, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object,))
gobject.signal_new("bindid-changed", HidLayoutWidget, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object,))
gobject.signal_new("layout-changed", HidLayoutWidget, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object,))







# Testing standalone window.

class HidLayoutWindow (gtk.Window):
    def __init__ (self):
        gtk.Window.__init__(self)
        self.set_size_request(640, 480)
        self.resize(720, 680)
        self.layout = gtk.VBox()
        self.add(self.layout)

        inpdescr = InpDescrModel(8)
        dispstate = InpDisplayState(inpdescr)
        hidw = HidLayoutWidget(dispstate, implicit_layouts)
        self.layout.add(hidw)
        hidw.connect("key-selected", self.on_key_selected)
        hidw.connect("bind-changed", self.on_bind_changed)

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

