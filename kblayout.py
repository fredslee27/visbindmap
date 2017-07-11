#!/usr/bin/env python
# vi: set tabstop=4 expandtab shiftwidth=4 :
from __future__ import print_function

import sys
import gtk, gobject, glib
import math
import ast

import kbd_desc


class DndOpcodes:  # old-style class.
    class DndOpcodeEnum (object):  # new-style class.
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
    def __init__ (self, loglevel=None, sink=sys.stderr):
        self._sink = sink
        if loglevel is None: loglevel = Logger.info
        self.set_level(loglevel)

    def get_level (self): return self._level
    def set_level (self, val): self._level = val.__func__
    level = property(get_level, set_level)

    def __gate (self, lvlnum, lvlmarker, *msgparts):
        if self._level in self._levels[lvlnum:]:
            print(lvlmarker, *msgparts, file=self._sink)
    def fatal (self, *msgparts): self.__gate(0, "!!!", *msgparts)
    def error (self, *msgparts): self.__gate(1, "***", *msgparts)
    def warn (self, *msgparts):  self.__gate(2, "---", *msgparts)
    def info (self, *msgparts):  self.__gate(3, "===", *msgparts)
    def debug (self, *msgparts): self.__gate(4, "+++", *msgparts)
    _levels = [ fatal, error, warn, info, debug ]
logger = Logger(Logger.debug)
# set log level with: logger.level = logger.warn
# log with: logger.info("...", "...", ...)


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
        # TODO: these states should not be in data model.
        # active group
        self._group = 0
        # active layer
        self._layer = 0
        self.cluster_defaults()

    def clear (self):
        for grp in self.groups:
            grp.clear()
        self.set_group(0)
        self.set_layer(0)
        self.cluster_defaults()
        return

    def restore (self, other):
        if not other:
            return
        self._maxgroups = other.get_numgroups()
        self._maxlayers = other.get_numlayers()
        self._group = 0
        self._layer = 0
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

    def get_group (self):
        """Get active group number."""
        return self._group
    def set_group (self, val):
        self._group = val
        self.emit('group-changed', val)

    def get_layer (self):
        """Get active layer number."""
        return self._layer
    def set_layer (self, val):
        self._layer = val
        self.emit("layer-changed", val)

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

    def get_layermap (self, layernum, group=None):
        """Get layer (dict of keysym:binding) in specified group."""
        groupnum = group if group is not None else  self.get_group()
        if (0 <= layernum) and (layernum < self._maxlayers):
            return self.groups[groupnum].get_layermap(layernum)
        return None
    def set_layermap (self, layernum, value, group=None):
        groupnum = group if group is not None else self.get_group()
        if (0 <= layernum) and (layernum < self._maxlayers):
            if value is None:
                self.groups[groupnum].set_layermap(layernum, InpLayer(layernum, 0))
            else:
                self.groups[groupnum].set_layermap(layernum, value)

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

    def get_bind (self, inpsym,  group=None, layer=None):
        groupnum = group if group is not None else self.get_group()
        layernum = layer if layer is not None else self.get_layer()
        return self.get_grouplist(groupnum).get_layermap(layernum).get_bind(inpsym)
    def set_bind (self, inpsym, v,  group=None, layer=None):
        groupnum = group if group is not None else self.get_group()
        layernum = layer if layer is not None else self.get_layer()
        self.get_grouplist(groupnum).get_layermap(layernum).set_bind(inpsym, v)
        self.emit('bind-changed', groupnum, layernum, inpsym)


    def resolve_bind (self, inpsym,  group=None, layer=None):
        """Determine effective binding of a inpsym based on passthrough rules.
"""
        passthrough = False
        groupnum = group if group is not None else self.get_group()
        layernum = layer if layer is not None else self.get_layer()
        groupfollow = groupnum
        retval = None
        while (retval is None) and (groupfollow is not None):
            grp = self.get_grouplist(groupfollow)
            layerfollow = layernum
            while (retval is None) and (layerfollow is not None):
                layermap = grp.get_layermap(layerfollow)
                if layermap:
                    retval = layermap.get_bind(inpsym)
                if retval is None:
                    passthrough = True
                    if layerfollow != layermap._fallback:
                        layerfollow = layermap._fallback
                    else:
                        layerfollow = None
                    passthrough = True
                layerfollow = None  ## don't follow layer for now.
            if retval is None:
                passthrough = True
                if grp.fallback != groupfollow:
                    groupfollow = grp.fallback
                else:
                    groupfollow = None
        return passthrough, retval

    def resolve_bind_markup (self, inpsym, group=None, layer=None):
        passthrough, plaintext = self.resolve_bind(inpsym, group, layer)
        if plaintext:
            if passthrough:
                # Fell back to group 0; italicize.
                escbindlit = glib.markup_escape_text(plaintext)
                retval = "<i><small>{}</small></i>".format(escbindlit)
                return retval
            else:
                # Direct hit; return unadorned.
                escbindlit = glib.markup_escape_text(plaintext)
                return escbindlit
        return ""

    def swap_bind (self, firstsym, secondsym, group=None, layer=None):
        firstbind = self.get_bind(firstsym, group, layer)
        secondbind = self.get_bind(secondsym, group, layer)
        self.set_bind(firstsym, secondbind)
        self.set_bind(secondsym, firstbind)
        return

    def refresh (self):
        """Induce update of viewers of this model."""
        self.emit("layer-changed", self._layer)

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
gobject.signal_new("layer-changed", InpDescrModel, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,))
gobject.signal_new("group-changed", InpDescrModel, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,))



class KbTop (gtk.Button):
    """UI element of a key(board) top.  Presented as the inpsym on the first row, and a boxed text entry on the second row for the binding.
    Contents to display are packaged in a data model (InpDescrModel)
    """
    def __init__ (self, inpsym, inpdescr=None, vislayers=1):
        """Initialize with given data model, and the input symbol tied to this kbtop"""
        # UI elements
        gtk.Button.__init__(self)
        self.plane = gtk.VBox()
        self.inp_lbl = gtk.Label()
        self.spacer = gtk.HBox()
        self.vislayers = vislayers  # Visible layers.

        # data model
        self.set_model(inpdescr)
        self.inpdescr = inpdescr
        self.inpsym = inpsym
        self._baselayer = 0  # partial layers view; what the lowest layer number is.
        self._layer = 0  # Currently active layer shown.
        self._group = 0  # Currently active group shown.

        # Fill label (first row)
        self.label = self.inpdescr.get_label(self.inpsym)
        #self.set_keytop(self.label)

#        # Adjust bind display (second row)
#        self.inp_bind.set_width_chars(4)
#        self.inp_bind.set_justify(gtk.JUSTIFY_LEFT)

        self.setup_dnd()

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

        self.inp_binds = []
        self.lyr_lbls = []
        self.bg_binds = []
        self.inp_box = None

        self.uibuild_binddisplays()

        #self.inp_box.pack_start(temp)
        #self.align1.add(self.inp_box)
        self.box_bind.add(self.align1)

        self.plane.pack_start(self.box_bind, expand=False, fill=False)

        self.add(self.plane)

        self.update_display()

    def uibuild_binddisplays (self):
        if self.inp_box:
            self.align1.remove(self.inp_box)

        self.inp_box = gtk.VBox()

        m = max(1, self.inpdescr.get_numlayers())
        # Input binding displays.
        self.inp_binds = [ gtk.Label() for n in range(m) ]
        # Background for binding displays.
        self.bg_binds = [ gtk.EventBox() for n in range(m) ]
        # label for binding display layers.
        self.lyr_lbls = [ gtk.Label() for n in range(m) ]

        # set up droppable binding display (dressed up as a text entry).
        temp = gtk.Entry()  # copy style from Entry.
        self.refstyle = refstyle = temp.get_style().copy()
        # Prepare multi-layer view.
        for i in range(0, self.vislayers):
            ib = self.inp_binds[i]
            ib.set_alignment(0, 0.5)
            ib.set_width_chars(4)
            ib.set_justify(gtk.JUSTIFY_LEFT)
            bg = self.bg_binds[i]
            bg.modify_bg(gtk.STATE_NORMAL, refstyle.base[gtk.STATE_NORMAL])
            bg.modify_bg(gtk.STATE_ACTIVE, refstyle.base[gtk.STATE_ACTIVE])
            bg.modify_bg(gtk.STATE_PRELIGHT, refstyle.base[gtk.STATE_PRELIGHT])
            bg.modify_bg(gtk.STATE_SELECTED, refstyle.base[gtk.STATE_SELECTED])
            bg.add(ib)
            if i != 0:
                self.inp_box.pack_start(gtk.HSeparator(), expand=False, fill=False)

            #self.inp_box.pack_start(bg, expand=False, fill=False)
            bindline = gtk.HBox()
            bindline.pack_start(self.lyr_lbls[i], expand=False, fill=False)
            bindline.pack_start(bg, expand=True, fill=True)
            self.inp_box.pack_start(bindline, expand=False, fill=False)
        self.align1.add(self.inp_box)
        self.inp_box.show_all()

    def get_inpsym (self):
        return self.inpsym
    def set_inpsym (self, val):
        self.inpsym = val

    def get_vislayers (self):
        return self.vislayers
    def set_vislayers (self, v):
        self.vislayers = v
        self.uibuild_binddisplays()

    def get_model (self):
        return self.inpdescr
    def set_model (self, mdl):
        if mdl is None:
            mdl = InpDescrModel()
        self.inpdescr = mdl
        if self.inpdescr:
            self.inpdescr.connect("bind-changed", self.on_data_change)
            self.inpdescr.connect("label-changed", self.on_data_change)
            self.inpdescr.connect("layer-changed", self.on_layer_change)
            self.inpdescr.connect("group-changed", self.on_group_change)
        # self.emit("data-model-changed")

    def set_keytop (self, disp):
        if len(disp) > 2:
            self.inp_lbl.set_markup("<small>%s</small>" % disp)
        else:
            self.inp_lbl.set_text("%s" % disp)
        return

    def update_display (self):
        # Update keytop
        lbl = self.inpdescr.get_label(self.inpsym)
        self.set_keytop(lbl)
        # Update binding display
        groupnum = self.inpdescr.get_group()
        layernum = self.inpdescr.get_layer()
        layermap = self.inpdescr.get_layermap(layernum)

        self._baselayer = self.vislayers * (self._layer / self.vislayers)
        bindidx = self.vislayers - (self._layer - self._baselayer) - 1

        for i in range(self.vislayers):
            bg = self.bg_binds[i]
            layernum = self._baselayer + (self.vislayers - i) - 1
            if i == bindidx:
                # highlighted layer.
                refstyle = self.refstyle.base
                bg.modify_bg(gtk.STATE_NORMAL, refstyle[gtk.STATE_NORMAL])
                bg.modify_bg(gtk.STATE_ACTIVE, refstyle[gtk.STATE_ACTIVE])
                bg.modify_bg(gtk.STATE_PRELIGHT, refstyle[gtk.STATE_PRELIGHT])
                bg.modify_bg(gtk.STATE_SELECTED, refstyle[gtk.STATE_SELECTED])
            else:
                # unhighlighted layer.
                refstyle = self.refstyle.bg
                bg.modify_bg(gtk.STATE_NORMAL, refstyle[gtk.STATE_NORMAL])
                bg.modify_bg(gtk.STATE_ACTIVE, refstyle[gtk.STATE_ACTIVE])
                bg.modify_bg(gtk.STATE_PRELIGHT, refstyle[gtk.STATE_PRELIGHT])
                bg.modify_bg(gtk.STATE_SELECTED, refstyle[gtk.STATE_SELECTED])
            val = self.inpdescr.resolve_bind_markup(self.inpsym, layer=layernum)
            self.inp_binds[i].set_markup(val)
            # install layer prefix for multi-layer view.
            if self.vislayers > 1:
                self.lyr_lbls[i].set_markup("<small>%s:</small>" % layernum)
            else:
                self.lyr_lbls[i].set_text("")

    def on_data_change (self, *args):
        self.update_display()
    def on_layer_change (self, inpdescr, layernum, *args):
        self._layer = layernum
        self.update_display()
    def on_group_change (self, inpdescr, groupnum, *args):
        self._group = groupnum
        self.update_display()

    def setup_dnd (self):
        # Set up drag-and-drop for KbTop.
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
        logger.debug("kbtop.drag-data-get: %d" % info)
        if info == DndOpcodes.UNBIND:
            logger.debug("kbtop: try unbind  %s" % self.inpsym)
            seldata.set(seldata.target, 8, str(self.inpsym))
            self.pending_drag_unbinding = True
            return True
        if info == DndOpcodes.SWAP:
            logger.debug("kbtop.drag-data-get for swap")
            val = self.inpsym
            seldata.set(seldata.target, 8, str(self.inpsym))
            return True
        return False

    def on_drag_end (self, w, ctx, *args):
        if self.pending_drag_unbinding:
            logger.debug("kbtop unbind %s" % self.inpsym)
            self.inpdescr.set_bind(self.inpsym, "")
            self.pending_drag_unbinding = False
        return

    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        #print("%s drag-data-received %r" % (self.__class__.__name__, w))
        logger.debug("%s drag-data-received %r" % (self.__class__.__name__, w))
        if info == DndOpcodes.BIND:
            # Commands dropping.
            seltext = seldata.data
            logger.debug("kbtop Command install: %s <= %s" % (w.inpsym, seltext))
            self.inpdescr.set_bind(self.inpsym, seltext)
            ctx.finish(True, False, 0)
            return True
        elif info == DndOpcodes.SWAP:
            othersym = seldata.data
            logger.debug("kbtop Command swap: %s <=> %s" % (w.inpsym, othersym))
            self.inpdescr.swap_bind(w.inpsym, othersym)
            ctx.finish(True, False, 0)
            return True




class ArrangerEmpty (object):
    NAME = "empty"
    W = 12
    H = 12
    SIMPLE_PLACEMENTS = { }
    def __init__ (self, parent):
        self.parent = parent
        self.placements = dict()
        if self.SIMPLE_PLACEMENTS:
            for k,v in self.SIMPLE_PLACEMENTS.iteritems():
                row,col = v
                self.placements[k] = (row*self.H, col*self.H, self.W,self.H)
        self.build_widget_pool()

    def _populate_widget_pool (self, suffices):
        """Create KbTop instances as needed to add into widget_pool, a dict of inpsym to widget."""
        suffices = self.placements.keys()
        for suffix in suffices:
            inpsym = self.inpsymof(suffix)
            if not inpsym in self.parent.kbtops:
                kbtop = KbTop(inpsym, self.parent.inpdescr, self.parent.inivislayers)
                self.parent.kbtops[inpsym] = kbtop
                kbtop.connect("button-press-event", self.parent.on_button_press)

    def build_widget_pool (self):
        suffices = self.placements.keys()
        self._populate_widget_pool(suffices)

    def inpsymof (self, suffix):
        return "{}{}".format(self.parent.inpsymprefix, suffix)

    def full_rearrange (self, placements):
        """Common case of gridded arrangement, where
placements = dict of kbtop suffix to (row,col, width,height) tuple
"""
        self.parent.detach_all()
        for suffix,elt in placements.iteritems():
            row,col,xspan,yspan = elt
            inpsym = self.inpsymof(suffix)
            left = col
            right = col + xspan
            top = row
            bottom = row + yspan
            kbtop = self.parent.kbtops[inpsym]
            self.parent.grid.attach(kbtop, left, right, top, bottom)
            kbtop.show()
        #self.parent.show_all()

    def rearrange (self):
        self.parent.stacked.set_visible_child_name("0")
        self.full_rearrange(self.placements)

    def __repr__ (self):
        return "{!s}()".format(self.__class__.__name__)

class ArrangerOneButton (ArrangerEmpty):
    NAME = "SingleButton"
    # Click
    W = 12
    H = 12
    SIMPLE_PLACEMENTS = {
           # (row,col, colspan,rowspan)
        'c': (0,0),
    }

class ArrangerScrollwheel (ArrangerEmpty):
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
    NAME = "Mouse[Region]"
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
    NAME = "MouseRegion"
    W = 12
    H = 12
    SIMPLE_PLACEMENTS = {
        'c': (0,0),
    }

class ArrangerJoystick (ArrangerEmpty):
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
    NAME = "Touch Menu"
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
        '5': (3,0,3,3),                                      '6': (3,9,3,3),
                                '13': (3,3,6,6),
        '7': (6,0,3,3),                                      '8': (6,9,3,3),
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
        ArrangerEmpty.__init__(self, parent)
        self.set_capacity(cap)
        self.build_widget_pool()

    def build_widget_pool (self):
        """Create KbTop instances as needed to add into widget_pool, a dict of inpsym to widget."""
        # Generate '1'..'16' inclusive.
        suffices = [ str(ofs) for ofs in range(1, 17) ]
        self._populate_widget_pool(suffices)

    def set_capacity (self, cap):
        thresholds = self.ALL_PLACEMENTS.keys()
        thresholds.sort()
        while len(thresholds) > 1 and thresholds[0] < cap:
            del thresholds[0]
        lim = thresholds[0]
        self.cap = lim
        self.placements = self.ALL_PLACEMENTS[self.cap]

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
    NAME = "Radial Menu"
    def __init__ (self, parent, cap=2):
        ArrangerEmpty.__init__(self, parent)
        #self.placements = [ (0,6,1,1), (12,6,1,1) ]
        self.placements = {
            '1':  (0,6),
            '2': (12,6),
        }
        self.cap = 2
        self.set_capacity(cap)
        self.build_widget_pool()

    def build_widget_pool (self):
        """Create KbTop instances as needed to add into widget_pool, a dict of inpsym to widget."""
        # Generate '1'..'20' inclusive.
        suffices = [ str(ofs) for ofs in range(1, 21) ]
        self._populate_widget_pool(suffices)

    def set_capacity (self, cap=2):
        if (cap < 1):
            cap = 1
        if (cap > 20):
            cap = 20
        self.cap = cap
        # Radial places from top going clockwise.
        self.placements.clear()
        for idx in range(0, self.cap):
            angle = idx * (2 * math.pi) / cap
            theta = math.pi - angle
            w, h = 1, 1
            tx = math.cos(theta)
            ty = math.sin(theta)
            r = 6
            row = int((tx * r) + r + .5)
            col = int((ty * r) + r + .5)
            suffix = "{}".format(idx+1)
            self.placements[suffix] = (row, col, w,h)
        return

    def __repr__ (self):
        return "{!s}({:d})".format(self.__class__.__name__, self.cap)

class ArrangerListmenu_alternate (ArrangerEmpty):
    """Flat view of menu for brainstorming bind contents.
Applicable to: touch menu, radial menu, scrollwheel items.
Presents each menu item as an individual KbTop.
"""
    NAME = "menu list"
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

class ArrangerListmenu (ArrangerEmpty):
    """Flat view of menu for brainstorming bind contents.
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
        self.parent.menulist.pull_data()
        self.parent.stacked.set_visible_child_name("1")



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
            if self.active == page:
                page.show_all()
            else:
                page.hide_all()

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
        logger.debug("opening page %r" % self.active)
        self.readjust_visibility()


class KbMenuList (gtk.ScrolledWindow):
    """TreeView of list-based cluster types."""
    def __init__ (self, inpsymprefix=None, inpdescr=None):
        # Based on ScrollWindowed, containing a TreeView
        gtk.ScrolledWindow.__init__(self)
        self.inpdescr = inpdescr
        self.inpsymprefix = inpsymprefix or ""
        # The TreeView
        self.treeview = gtk.TreeView()
        self.rendertext = gtk.CellRendererText()
        self.col0 = gtk.TreeViewColumn("#", self.rendertext, text=0)
        self.col1 = gtk.TreeViewColumn("bind", self.rendertext, markup=1)
        self.treeview.append_column(self.col0)
        self.treeview.append_column(self.col1)
        self.add(self.treeview)  # and not with viewport.
        # private model updated from InpDescrModel, prefill with 20 inpsyms.
        self.scratch = gtk.ListStore(str,str)
        for i in range(0, 20):
            inpsym = "{}{}".format(self.inpsymprefix, i+1)
            self.scratch.append((inpsym, None))
        self.pull_data()  # Populate .scratch from InpDescrModel
        self.treeview.set_model(self.scratch)
        # Listen for changes to/in InpDescrModel (update .scratch)
        if self.inpdescr:
            self.conn_bind_changed = self.inpdescr.connect("bind-changed", self.on_inpdescr_bind_changed)
            self.conn_label_changed = self.inpdescr.connect("label-changed", self.on_inpdescr_label_changed)
            self.conn_layer_changed = self.inpdescr.connect("layer-changed", self.on_inpdescr_layer_changed)
            self.conn_group_changed = self.inpdescr.connect("group-changed", self.on_inpdescr_group_changed)
        # Set up drag-and-drop.
        self.setup_dnd()

        self.show_all()

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
        logger.debug("kbmenulist drag-end")
        if self.dropunbind:
            logger.debug("drop-unbind inpsym %s" % self.dropunbind)
            self.inpdescr.set_bind(self.dropunbind, "")
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
            logger.debug("kbmenulist drag-data-get reorder")
            data = repr(firstpath)
        elif info == DndOpcodes.UNBIND:
            logger.debug("kbmenulist drag-data-get unbind")
            data = inpsym
            self.dropunbind = inpsym
        elif info == DndOpcodes.SWAP:
            logger.debug("kbmenulist drag-data-get swap")
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
            logger.debug("kbmenulist reorder")
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
            logger.debug("kbmenulist bind-drop")
            dropinfo = w.get_dest_row_at_pos(x,y)
            seltext = seldata.data
            logger.debug("command-dropping: %r" % seltext)
            self.drop_in_bind(destpath, seltext)
            ctx.finish(True, False, time)
            return True
        elif info == DndOpcodes.SWAP:
            # swap with a kbtop, seldata.data is inpsym.
            logger.debug("kbmenulist swap")
            othersym = seldata.data
            destsym = self.scratch[destpath][0]
            logger.debug("command-swapping: %r,%r" % (destsym, othersym))
            self.inpdescr.swap_bind(destsym, othersym)
            ctx.finish(True, False, time)
            return True
        return False


    def drop_in_bind (self, treepath, newval):
        """Carry out action of (completing) a drop of a command on tree at path."""
        inpsym = self.scratch[treepath][0]
        self.inpdescr.set_bind(inpsym, newval)
        # Update inpdescr model, then rely on signals to auto-update scratch.
        return

    def drag_bind (self, bias, srcpath, dstpath):
        # mass pull.
        listbinds = [ b for s,b in self.scratch ]
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
        for h in [ self.conn_bind_changed, self.conn_label_changed, self.conn_layer_changed, self.conn_group_changed ]:
            self.inpdescr.handler_block(h)
        for i in range(0, len(listbinds)):
            bind = listbinds[i]
            n = i+1
            inpsym = "{}{}".format(self.inpsymprefix, n)
            self.inpdescr.set_bind(inpsym, bind)
            self.scratch.append((inpsym, bind))
        for h in [ self.conn_bind_changed, self.conn_label_changed, self.conn_layer_changed, self.conn_group_changed ]:
            self.inpdescr.handler_unblock(h)
        return

    def pull_data (self):
        """Synchronize .scratch based on InpDescrModel"""
        for row in self.scratch:
            inpsym = row[0]
            if self.inpdescr:
                bind_markedup = self.inpdescr.resolve_bind_markup(inpsym)
                row[1] = bind_markedup

    def on_inpdescr_bind_changed (self, mdl, grp, lyr, inpsym):
#        if (grp == self.inpdescr._group) and (lyr == self.inpdescr._layer):
#            if inpsym.startswith(self.inpsymprefix):
#                for row in self.scratch:
#                    if row[0] == inpsym:
#                        pass
        self.pull_data()
    def on_inpdescr_label_changed (self, *args):
        self.pull_data()
    def on_inpdescr_layer_changed (self, *args):
        self.pull_data()
    def on_inpdescr_group_changed (self, *args):
        self.pull_data()


class KbPlanar (gtk.EventBox):
    """Planar control cluster (stick, touchpad, etc.)
Contents to display are packaged in a data model (InpDescrModel)
Children are KbTop, but selectively shown and placed to reflect cluster type.

As arrangments can change during run-time, use strategies for rearranging:
* (d) Dpad : u,d,l,r,c
* (b) Diamond : n,e,w,s,c
* (m) Mouse : x,y,c
* (u) MouseRegion :
* (j) Joystick {Move,Camera,Mouse} : x-, x+, y-, y+, c
* (g) GyroTilt : x-, x+, y-, y+, w-, w+
* (t) Menu.Touch {2,4,7,9,12,13,16) : #1..#16
* (r) RadialMenu {1..20} : #1..#20
* (l) ListMenu {1..20} : #1..#20
* (o) OneButton : o
    """

    def __init__ (self, inpsymprefix, inpdescr=None, vislayers=1):
        """Initialize with given data model, and the input symbol prefix tied to this kbtop"""
        # UI elements
        gtk.EventBox.__init__(self)

        self.inpsymprefix = inpsymprefix
        self.inpdescr = inpdescr
        self.kbtops = dict()  # Mapping of inpsym to KbTop instance.

        self.frame = gtk.Frame(inpsymprefix)
        self.frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        self.frame_title = gtk.HBox()
        self.frame_lbl_sym = gtk.Label()
        #self.frame_lbl_sym.set_markup("<a href='#a'>{}</a>".format(self.inpsymprefix))
        self.frame_btn = gtk.Button(unichr(0x2026))
        self.frame_btn.set_tooltip_text("Change variant for this planar cluster")
        self.frame_title.pack_start(self.frame_btn, False, False, 0)
        self.frame_title.pack_start(self.frame_lbl_sym, False, False, 0)
        self.frame.set_label_widget(self.frame_title)

        # Table is (3x3), (4x4), or (6x6); LCD=(12,12), use multiple cells.
        self.grid = gtk.Table(12,12,True)

        self.stacked = PseudoStack()
        self.menulist = KbMenuList(self.inpsymprefix, self.inpdescr)
        self.stacked.add_named(self.grid, "0")
        self.stacked.add_named(self.menulist, "1")

        self.frame.add(self.stacked)
        self.add(self.frame)

        self.inivislayers = vislayers

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
        self.arrangerListmenu = ArrangerListmenu(self)

        self.arranger = self.arrangerEmpty

        self.ctxmenu = self.make_context_menu(self.inpsymprefix)
        self.connect_menuitems(self.ctxmenu)
        self.connect_ctxmenu()
        self.update_display()

    def arrangerTouchmenu (self, cap=2):
        self.detach_all()
        self.arrangerTouchmenu0.set_capacity(cap)
        return self.arrangerTouchmenu0
    def arrangerRadialmenu (self, cap=2):
        self.detach_all()
        self.arrangerRadialmenu0.set_capacity(cap)
        return self.arrangerRadialmenu0

    def find_arranger (self, name):
        match = [ a for a in self.__dict__.itervalues() if isinstance(a, ArrangerEmpty) and a.NAME == name ]
        if match:
            return match[0]
        return None
    def get_arranger (self):
        return self.arranger
    def set_arranger (self, arranger):
        if callable(arranger):
            self.arranger = arranger()
        elif arranger is None:
            self.arranger = self.arrangerEmpty
        else:
            self.arranger = arranger
        self.arranger.rearrange()
        #self.frame.set_label("{} <{!s}>".format(self.inpsymprefix, self.arranger.NAME))
        self.frame_lbl_sym.set_label(" {} <{!s}>".format(self.inpsymprefix, self.arranger.NAME))
        #self.frame_lbl_sym.set_markup("<a href='#a'>{} &lt;{!s}&gt;</a>".format(self.inpsymprefix, self.arranger.NAME))
        #self.show_all()
        self.grid.show_all()
        # save cluster type by name into InpDescrModel, using this input's prefix as the key, in group 0 layer 0.
        self.inpdescr.set_bind(self.inpsymprefix, self.arranger.NAME, 0, 0)

    def get_cluster_type (self):
        return self.arrange.NAME
    def set_cluster_type (self, cltype):
        arranger = self.find_arranger(cltype)
        self.set_arranger(arranger)
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
            ( "_List Menu", self.arrangerListmenu ),
            ]
        menu = self.make_menu(context_menu_desc)
        if menu_title:
            title = gtk.MenuItem(menu_title, False)
            title.set_sensitive(False)
            menu.prepend(title)
        menu.show_all()
        return menu

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
        self.detach_all()
        # Retrieve intended cluster type by name from InpDescrModel, using this input's prefix as the key, in group 0 layer 0.
        cluster_type = self.inpdescr.get_bind(self.inpsymprefix, 0, 0)
        self.set_cluster_type(cluster_type)
        if self.arranger:
            self.arranger.rearrange()
        return

    def detach_all (self):
        """Remove all widgets from table."""
#        for k,v in self.kbtops.iteritems():
#            v.hide()
#            if v.get_parent() != None:
#                self.grid.remove(v)
        for ch in self.grid.get_children():
            self.grid.remove(ch)

    def get_kbtops (self):
        return self.kbtops.values()


class KblayoutWidget (gtk.VBox):
    def __init__ (self, mdl=None):
        gtk.VBox.__init__(self)
        self.vislayers = 1
        self.mdl = mdl
        self.keytops = {}
        self.active = False
        self.grid = gtk.Table(homogeneous=True)
        #self.grid = gtk.Table(homogeneous=False)

        # Selector for specific layout.
        self.mdl_layout = gtk.ListStore(str)
        kbnames = sorted(self.kbdesc.keys())
        for k in kbnames:
            self.mdl_layout.append((k,))
        self.inp_layout = gtk.ComboBox(self.mdl_layout)
        self.cell_layout = gtk.CellRendererText()
        self.inp_layout.pack_start(self.cell_layout)
        self.inp_layout.add_attribute(self.cell_layout, 'text', 0)
        self.inp_layout.set_active(0)
        self.inp_layout.connect('changed', self.on_changed)

        # GUI Layout for KB Layout.
        self.lbl_layout = gtk.Label("Layout:")
        self.row_layout = gtk.HBox()
        self.row_layout.pack_start(self.lbl_layout, expand=False, fill=False)
        self.row_layout.pack_start(self.inp_layout, expand=False, fill=False)

        idx = self.inp_layout.get_active()
        val = self.mdl_layout[idx][0]
        self.fill_board(self.kbdesc[val])

        self.pack_start(self.row_layout, expand=False, fill=False)
        self.pack_start(self.grid, expand=False, fill=False)

    def get_model (self):
        return self.mdl
    def set_model (self, mdl):
        self.mdl = mdl
        for k in self.keytops.valueiter():
            k.set_model(mdl)

    def get_vislayers (self):
        return self.vislayers
    def set_vislayers (self, v):
        self.vislayers = v
        for kt in self.keytops.itervalues():
            kt.set_vislayers(v)
            kt.update_display()

    @property
    def kbdesc (self):
        return kbd_desc.KBD

    def fill_board (self, kbdesc):
        grid = self.grid
        keytops = {}
        rownum = 0
        colnum = 0
        for row in kbdesc:
            if row is not None:
                for keydata in row:
                    (label, height, width) = keydata
                    if label is not None:
                        inpsym, disp = label, label
                        if '\f' in label:
                            (disp, inpsym) = label.split('\f', 1)
                            if self.mdl:
                                self.mdl.set_label(inpsym, disp)
                        l, r = colnum, colnum+width
                        t, b = rownum, rownum+2*height
                        #print("attach %r %r %r %r %r" % (keytop, l, r, t, b))
                        if inpsym.endswith("#"):
                            planar = KbPlanar(inpsym, self.mdl, self.vislayers)
                            for inpsym,kbtop in planar.kbtops.iteritems():
                                kbtop.connect("clicked", self.on_keytop_clicked)
                                keytops[inpsym] = kbtop
                                self.active = kbtop
                            #print("planar attach (%d,%d, %d,%d)"%  (l,r, t,b))
                            #grid.attach(planar, l, r, t, b, xoptions=0, yoptions=0)
                            grid.attach(planar, l, r, t, b, xoptions=gtk.FILL, yoptions=gtk.FILL, xpadding=4, ypadding=4)
                            planar.show_all()
                            planar.update_display()
                            #grid.attach(planar, l, r, t, b)
                        else:
                            keytop = KbTop(inpsym, self.mdl, self.vislayers)
                            keytop.connect("clicked", self.on_keytop_clicked)
                            keytops[inpsym] = keytop
                            self.active = keytop
                            grid.attach(keytop, l, r, t, b)
                            keytop.show_all()
                        if keytops.has_key(inpsym):
                            logger.warn("potential duplicate: %s" % inpsym)
                    colnum += width
                rownum += 1  # totals 2 for non-empty row.
            rownum += 1
            colnum = 0
        self.keytops = keytops

    def clear_board (self):
        grid = self.grid
        for ch in grid.get_children():
            grid.remove(ch)
            ch.destroy()
        grid.resize(1,1)
        self.keytops = {}

    def on_changed (self, w, *args):
        idx = w.get_active()
        data = self.mdl_layout[idx]
        val = data[0]
        kbdata = self.kbdesc[val]
        self.clear_board()
        self.fill_board(kbdata)
        #self.show_all()
        self.show()
        self.emit("layout-changed", val)

    def on_keytop_clicked (self, w, *args):
        inpsym = w.inpsym
        logger.debug("target: %s" % inpsym)
        self.emit("key-selected", inpsym)

    def on_bind_changed (self, w, *args):
        #self.bindmap[w.inpsym] = w.bind
        self.emit("bind-changed", w)

    def on_bindid_changed (self, w, *args):
        #print("Kblayout: bindid-changed")
        #self.bindmap[w.inpsym] = w.bind
        self.emit("bindid-changed", w)

    def __getitem__ (self, inpsym):
        return self.keytops[inpsym]

    def __setitem__ (self, inpsym, val):
        self.keytops[inpsym].bind = val

    def __delitem__ (self, inpsym):
        del self.keytops[inpsym]

# Set up signals.
gobject.type_register(KblayoutWidget)
gobject.signal_new("key-selected", KblayoutWidget, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (str,))
gobject.signal_new("bind-changed", KblayoutWidget, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object,))
gobject.signal_new("bindid-changed", KblayoutWidget, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object,))
gobject.signal_new("layout-changed", KblayoutWidget, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object,))






# Testing standalone window.

class KblayoutWindow (gtk.Window):
    def __init__ (self):
        gtk.Window.__init__(self)
        self.set_size_request(640, 480)
        self.resize(720, 680)
        self.layout = gtk.VBox()
        self.add(self.layout)

        kbl = KblayoutWidget()
        self.layout.add(kbl)
        kbl.connect("key-selected", self.on_key_selected)
        kbl.connect("bind-changed", self.on_bind_changed)

        self.connect('delete-event', self.on_delete)

        #kbl['Space'] = 'Jump'

    def on_delete (self, w, *args):
        gtk.main_quit()

    def on_key_selected (self, w, inpsym, *args):
        logger.debug("Selected inpsym '%s'" % inpsym)

    def on_bind_changed (self, w, keytop, *args):
        logger.debug("Bind changed for %r" % keytop)

    def run (self):
        self.show_all()
        gtk.mainloop()


if __name__ == "__main__":
    x = KblayoutWindow()
    x.run()

