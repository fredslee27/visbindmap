#!/usr/bin/env python
# vi: set tabstop=4 expandtab shiftwidth=4 :
from __future__ import print_function

import sys
import gtk, gobject

import kbd_desc


# Logging.
class Log (object):
    def __init__ (self, loglevel=None, sink=sys.stderr):
        self._sink = sink
        if loglevel is None: loglevel = Log.info
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
log = Log(Log.debug)
# set log level with: log.level = log.warn
# log with: log.info("...", "...", ...)


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
        return "%s.%s(groupnum=%r, numlayers=%r, layers=%r" % (self.__class__.__module__, self.__class__.__name__, self.groupnum, len(self.layers), self.layers)
    def __json__ (self):
        return {
            '__module__': self.__class__.__module__,
            '__class__': self.__class__.__class__,
            'groupnum': self.groupnum,
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
        # active group
        self._group = 0
        # active layer
        self._layer = 0

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
            if m is None:
                self.groups[n] = InpGroup(n, 0, layercount, None)
            else:
                self.groups[n] = m

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

        # Set up drag-and-drop
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, [ ("bind", gtk.TARGET_SAME_APP, 1) ], gtk.gdk.ACTION_LINK)
        #self.drag_dest_set(gtk.DEST_DEFAULT_ALL, [ ("bindid", gtk.TARGET_SAME_APP, 1) ], gtk.gdk.ACTION_LINK)
        #self.drag_dest_set(gtk.DEST_DEFAULT_ALL, [ ("binduri", gtk.TARGET_SAME_APP, 1) ], gtk.gdk.ACTION_LINK)
        self.connect("drag-drop", self.on_drop)
        self.connect("drag-data-received", self.on_drag_data_received)

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

        # TODO: pull color from Entry background (due to themes).
#        bgcolor = gtk.gdk.color_parse('#333333')
#        self.bg_bind.modify_bg(gtk.STATE_NORMAL, bgcolor)
#        self.bg_bind.modify_bg(gtk.STATE_ACTIVE, bgcolor)
#        self.bg_bind.modify_bg(gtk.STATE_PRELIGHT, bgcolor)
#        self.bg_bind.modify_bg(gtk.STATE_SELECTED, bgcolor)
        #self.bg_bind.modify_bg(gtk.STATE_INSENSITIVE, bgcolor)

        self.inp_binds = []
        self.bg_binds = []
        self.inp_box = None

#        m = max(1, inpdescr.get_numlayers())
#        # Input binding displays.
#        self.inp_binds = [ gtk.Label() for n in range(m) ]
#        self.inp_bind = self.inp_binds[0]
#        # Background for binding displays.
#        self.bg_binds = [ gtk.EventBox() for n in range(m) ]
#
#        # set up droppable binding display (dressed up as a text entry).
#        self.inp_bind.set_alignment(0, 0.5)
#        self.inp_box = gtk.VBox()
#        temp = gtk.Entry()
#        self.refstyle = refstyle = temp.get_style()
#        for i in range(0, self.vislayers):
#            ib = self.inp_binds[i]
#            ib.set_alignment(0, 0.5)
#            ib.set_width_chars(4)
#            ib.set_justify(gtk.JUSTIFY_LEFT)
#            bg = self.bg_binds[i]
#            bg.modify_bg(gtk.STATE_NORMAL, refstyle.base[gtk.STATE_NORMAL])
#            bg.modify_bg(gtk.STATE_ACTIVE, refstyle.base[gtk.STATE_ACTIVE])
#            bg.modify_bg(gtk.STATE_PRELIGHT, refstyle.base[gtk.STATE_PRELIGHT])
#            bg.modify_bg(gtk.STATE_SELECTED, refstyle.base[gtk.STATE_SELECTED])
#            bg.add(ib)
#            if i != 0:
#                self.inp_box.pack_start(gtk.HSeparator(), expand=False, fill=False)
#            self.inp_box.pack_start(bg, expand=False, fill=False)
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
        #self.inp_bind = self.inp_binds[0]
        # Background for binding displays.
        self.bg_binds = [ gtk.EventBox() for n in range(m) ]

        # set up droppable binding display (dressed up as a text entry).
        #self.inp_bind.set_alignment(0, 0.5)
        temp = gtk.Entry()
        self.refstyle = refstyle = temp.get_style()
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
            self.inp_box.pack_start(bg, expand=False, fill=False)
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
#        if layermap is not None:
#            val = layermap.get_bind(self.inpsym)  # could be null.
#        else:
#            val = None

#        shadow, val = self.inpdescr.resolve_bind(self.inpsym)
        self._baselayer = self.vislayers * (self._layer / self.vislayers)
        bindidx = self.vislayers - (self._layer - self._baselayer) - 1
#
#        if val is None:
#            val = ""
#            #self.inp_bind.set_text(val)
#            self.inp_binds[bindidx].set_text(val)
#        elif shadow:
#            val = "<i><small>%s</small></i>" % val
#            #self.inp_bind.set_markup(val)
#            self.inp_binds[bindidx].set_markup(val)
#        else:
#            #self.inp_bind.set_text(val)
#            self.inp_binds[bindidx].set_text(val)

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
            shadow, val = self.inpdescr.resolve_bind(self.inpsym, layer=layernum)
            inp_bind = self.inp_binds[i]
            layermap = self.inpdescr.get_layermap(layernum)
            should = self.inpdescr.get_bind(self.inpsym, group=self._group, layer=layernum)
            should2 = layermap.get_bind(self.inpsym)
            if val is None:
                self.inp_binds[i].set_text("")
            elif shadow:
                val = "<i><small>%s</small></i>" % val
                self.inp_binds[i].set_markup(val)
            else:
                self.inp_binds[i].set_text(val)

    def on_data_change (self, *args):
        self.update_display()
    def on_layer_change (self, inpdescr, layernum, *args):
        self._layer = layernum
        self.update_display()
    def on_group_change (self, inpdescr, groupnum, *args):
        self._group = groupnum
        self.update_display()

    def on_drop (self, w, ctx, x, y, time, *args):
        dragdata = self.drag_get_data(ctx, "STRING", time)
        return True

    def on_drag_data_received (self, w, ctx, x, y, sel, info, time, *args):
        #print("%s drag-data-received %r" % (self.__class__.__name__, w))
        log.debug("%s drag-data-received %r" % (self.__class__.__name__, w))
        srcw = ctx.get_source_widget()
        #print(" srcw = %r" % srcw)
        log.debug(" srcw = %r" % srcw)
        seltext = sel.get_text()
        #self.bindid = int(sel.get_text())
        #self.binduri = sel.get_text()
        log.debug("  sel = %r" % seltext)
        #bindid = int(seltext)
        ctx.finish(True, False, time)
        self.emit("dnd-link", srcw, seltext)

gobject.type_register(KbTop)
gobject.signal_new("dnd-link", KbTop, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object, str))   # src, dnd-data
#gobject.signal_new("bind-changed", KbTop, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
#gobject.signal_new("bindid-changed", KbTop, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())



class KblayoutWidget (gtk.VBox):
    def __init__ (self, mdl=None):
        gtk.VBox.__init__(self)
        self.vislayers = 1
        self.mdl = mdl
        self.keytops = {}
        self.active = False
        self.grid = gtk.Table(homogeneous=True)

        # Selector for specific layout.
        self.mdl_layout = gtk.ListStore(str)
        kbnames = sorted(self.kbdesc.keys())
        for k in kbnames:
            self.mdl_layout.append((k,))
        self.inp_layout = gtk.ComboBox(self.mdl_layout)
        self.cell_layout = gtk.CellRendererText()
        self.inp_layout.pack_start(self.cell_layout)
        self.inp_layout.add_attribute(self.cell_layout, 'text', 0)
        #idx = kbnames.index("en_US (pc104)")
        idx = kbnames.index("PS3")
        self.inp_layout.set_active(idx)
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
                        keytop = KbTop(inpsym, self.mdl, self.vislayers)
                        l, r = colnum, colnum+width
                        t, b = rownum, rownum+2*height
                        #print("attach %r %r %r %r %r" % (keytop, l, r, t, b))
                        grid.attach(keytop, l, r, t, b)
                        if keytops.has_key(inpsym):
                            log.warn("potential duplicate: %s" % inpsym)
                        keytops[inpsym] = keytop
                        keytop.connect("clicked", self.on_keytop_clicked)
                        keytop.connect("dnd-link", self.on_keytop_bound)
                        self.active = keytop
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
        self.show_all()
        self.emit("layout-changed", val)

    def on_keytop_clicked (self, w, *args):
        inpsym = w.inpsym
        log.debug("target: %s" % inpsym)
        self.emit("key-selected", inpsym)

    def on_keytop_bound (self, dstw, srcw, dnddata, *args):
        log.debug("keytop_bound dstw=%r srcw=%r data=%r" % (dstw, srcw, dnddata))
        self.emit("dnd-link", dstw, srcw, dnddata)

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
gobject.signal_new("dnd-link", KblayoutWidget, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object, object, str))





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
        log.debug("Selected inpsym '%s'" % inpsym)

    def on_bind_changed (self, w, keytop, *args):
        log.debug("Bind changed for %r" % keytop)

    def run (self):
        self.show_all()
        gtk.mainloop()


if __name__ == "__main__":
    x = KblayoutWindow()
    x.run()

