#!/usr/bin/env python3
# Python3 and Gtk3

# Python2-combatibility
from __future__ import print_function, with_statement, unicode_literals

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib

import math

import kbd_desc



########################
# BindStore data model #
########################

class BindValue (object):
    """
 cmdtitle:str = what is shown in bind value widget (and cmdpack view).
 cmdval:str = hint/indicator/value to exporter.
"""
    def __init__ (self, observer, cmdtitle=None, cmdcode=None):
        self._cmdtitle = cmdtitle
        self._cmdcode = cmdcode if (not cmdcode is None) else cmdtitle
        self.observers = [ observer ]

    def get_cmdtitle (self): return self._cmdtitle
    def set_cmdtitle (self, val):
        self._cmdtitle = val
        for x in self.observers:
            x()
    cmdtitle = property(get_cmdtitle, set_cmdtitle)

    def get_cmdcode (self): return self._cmdcode
    def set_cmdcode (self, val):
        self._cmdcode = val
        for x in self.observers:
            x()
    cmdcode = property(get_cmdcode, set_cmdcode)

    def __getitem__ (self, idx):
        defer = [ self.get_cmdtitle,
                    self.get_cmdcode ]
        return defer[idx]()

    def __setitem__ (self, idx, val):
        defer = [ self.set_cmdtitle,
                    self.set_cmdcode ]
        defer[idx](val)

    def snapshot (self):
        retval = { "__class__": self.__class__.__name__ }
        retval['cmdtitle'] = self.cmdtitle
        retval['cmdcode'] = self.cmdcode
        return retval

    def restore (self, primitives):
        if primitives['__class__'] != self.__class__.__name__:
            raise TypeError("Expected restore from class {}".format(self.__class__.__name__))
        self._cmdtitle = primitives['cmdtitle']
        self._cmdcode = primitives['cmdcode']
        self.notify_observers()
        return self

    def notify_observers (self):
        for o in self.observers:
            o()

    def __repr__ (self):
        return "{}(cmdtitle={!r}, cmdcode={!r})".format(
            self.__class__.__name__,
            self.cmdtitle,
            self.cmdcode)

# One layer consists of a dict mapping hiasym to bindvalues.
class BindLayer (dict):
    """
 keys are strings hiasym, to BindValue instance
"""
    def __init__ (self, observer, values=None):
        self.observers = [ observer ]
        if values is None:
            dict.__init__(self)
        else:
            dict.__init__(self, values)
        self.observers = [ observer ]

    def __getitem__ (self, key):
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)
        return None
    def __setitem__ (self, key, val):
        cmdtitle, cmdcode = None, None
        cooked = None
        cb = lambda: self.observe_bindvalue(key)
        if isinstance(val, tuple):
            # tuple, of (cmdtitle, cmdcode)
            cooked = BindValue(cb,  val[0], val[1])
        else:
            try:
                # assuming BindValue instance.
                cooked = BindValue(cb, val.cmdtitle, val.cmdcode)
            except AttributeError:
                # assuming str or str-ish, as both title and cmdval.
                valstr = str(val)
                cooked = BindValue(cb, valstr, valstr)
        dict.__setitem__(self, key, cooked)
        self.observe_bindvalue(key)

    def observe_bindvalue (self, hiasym):
        self.notify_observers(hiasym)

    def notify_observers (self, hiasym):
        for o in self.observers:
            o(hiasym)

    def snapshot (self):
        retval = { "__class__": self.__class__.__name__ }
        retval['dict'] = dict()
        for hiasym in self:
            retval['dict'][hiasym] = self[hiasym].snapshot()
        return retval

    def restore (self, primitives):
        if primitives['__class__'] != self.__class__.__name__:
            raise TypeError("Expected restore from class {}".format(self.__class__.__name__))
        dict.clear(self)
        for k in primitives['dict']:
            cb = lambda: self.observe_bindvalue(k)
            pd = primitives['dict'][k]
            v = BindValue(cb, None, None)
            self[k] = v
            self[k].restore(pd)
        return self

    def __repr__ (self):
        return "{}(values={})".format(
            self.__class__.__name__,
            dict.__repr__(self))


class BindGroup (list):
    """
 list of BindLayer instances.
"""
    def __init__ (self, observer, layers=None):
        try:
            len(layers)
            # Initialize from list.
#            cb = lambda hiasym: self.observe_layerbind(0, hiasym)
#            for x in layers:
#                self.append(x)
            for n in len(layers):
                cb = lambda hiasym: self.observe_layerbind(0, hiasym)
                self.append(BindLayer(cb), layers[n])
        except TypeError:
            if layers:
                # assume integer.
                self.set_nlayers(layers)
            else:
                # assume empty argument.
                cb = lambda hiasym: self.observe_layerbind(0, hiasym)
                self.append( BindLayer(cb) )
        self.observers = [ observer ]

    def get_nlayers (self):
        return len(self)
    def set_nlayers (self, n):
        while len(self) < n:
            cb = lambda hiasym: self.observe_layerbind(len(self), hiasym)
            self.append(BindLayer(cb))
    nlayers = property(get_nlayers, set_nlayers)

    def __getitem__ (self, idx):
        return list.__getitem__(self, idx)
    def __setitem__ (self, idx, val):
        # Assign layer -> copy from another BindLayer.
        cb = lambda hiasym: self.observe_layerbind(idx, hiasym)
        local = BindLayer(cb)
        other = val
        list.__setitem__(self, idx, local)
        for hiasym in other:
            v = other[hiasym]
            local[hiasym] = v

    def observe_layerbind (self, layernum, hiasym):
        self.notify_observers(layernum, hiasym)

    def notify_observers (self, layernum, hiasym):
        for o in self.observers:
            o(layernum, hiasym)

    def snapshot (self):
        retval = { "__class__": self.__class__.__name__ }
        retval['list'] = [None]*len(self)
        for i in range(len(self)):
            retval['list'][i] = self[i].snapshot()
        return retval

    def restore (self, primitives):
        if primitives['__class__'] != self.__class__.__name__:
            raise TypeError("Expected restore from class {}".format(self.__class__.__name__))
        while len(self):
            del self[0]
        for i in range(len(primitives['list'])):
            pl = primitives['list'][i]
            cb = lambda hiasym: self.observe_layerbind(i, hiasym)
            l = BindLayer(cb)
            list.append(self, l)
            l.restore(pl)
        return self


class BindStore (GObject.GObject):
    """
 groups = list of BindGroup instances
 resolve_bindview : list of tuple(redirects, BindValue)
"""
    def __init__ (self):
        GObject.GObject.__init__(self)
        self.groups = [BindGroup(self.make_cb(0))]

    def clear (self):
        self.groups = [ BindGroup(self.make_cb(0)) ]

    def make_cb (self, grp):
        return lambda lyr, sym: self.observe_groupbind(grp,lyr,sym)

    def observe_groupbind (self, groupid, layerid, hiasym):
        bindval = self.groups[groupid][layerid][hiasym]
        (cmdtitle, cmdcode) = (bindval.cmdtitle, bindval.cmdcode)
        self.emit("bind-changed", hiasym, cmdtitle, cmdcode)

    def get_group (self, groupid):
        try:
            grp = self.groups[groupid]
            return grp
        except IndexError:
            return None

    def get_layer (self, groupid, layerid):
        grp = self.get_group(groupid)
        if grp is None: return None
        try:
            lyr = grp[layerid]
            return lyr
        except (AttributeError, IndexError):
            return None

    def get_ngroups (self):
        return len(self.groups)
    def set_ngroups (self, n):
        nlyr = self.get_nlayers()
        while len(self.groups) < n:
            cb = self.make_cb(len(self.groups))
            g = BindGroup(cb)
            g.set_nlayers(nlyr)
            self.groups.append(g)
    ngroups = property(get_ngroups, set_ngroups)

    # This code section assumes all layers are the same size.
    # Later revisions may support different layers per group.
    def get_nlayers (self):
        return self.groups[0].nlayers
    def set_nlayers (self, n):
        for g in self.groups:
            g.set_nlayers(n)
    nlayers = property(get_nlayers, set_nlayers)

    def resolve_bindview (self, hiasym, groupid=0):
        return

    def snapshot (self):
        """Serialize to Python primitives (toplevel dict)."""
        retval = { "__class__": self.__class__.__name__ }
        retval['groups'] = [None]*len(self.groups)
        for i in range(len(self.groups)):
            retval['groups'][i] = self.groups[i].snapshot()

    def restore (self, primitives):
        """Restore BindStore from Python primitives (serialized)."""
        if primitives['__class__'] != self.__class__.__name__:
            raise TypeError("Expected restore from class {}".format(self.__class__.__name__))
        self.groups = []
        for i in range(len(primitives['groups'])):
            pg = primitives['groups'][i]
            g = BindGroup(self.make_cb(i))
            self.groups.append(g)
            g.restore(pg)
        return self

    def __repr__ (self):
        return "{}(groups={!r})".format(
            self.__class__.__name__,
            self.groups,
            )

    def get_bind (self, groupid, layerid, hiasym):
        """Main entry point: get binding for given group, layer, hiasym."""
        lyr = self.get_layer(groupid, layerid)
        if lyr is None: return None
        val = lyr.get(hiasym, None)
        return val

    def set_bind (self, groupid, layerid, hiasym, hiaval, hiacmd=None):
        """Main entry point: set binding for given grou, layer, hiasym:
 set_bind(groupid, layerid, hiasym, instance_BindValue)
 set_bind(groupid, layerid, hiasym, cmdtitle, cmdcode)
"""
        cooked = None
        if hiacmd is not None:
            cooked = BindValue(hiaval, hiacmd)
        else:
            cooked = hiaval
        self.groups[groupid][layerid][hiasym] = cooked

    __gsignals__ = {
        str("bind-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (str, str, str) ),
    }





################################
# Human-Interface Atom widgets #
################################
# originally "keytops", but some devices don't have keys.
# They are, nonetheless, elements Human-Computer Interface.

class HiaView (GObject.GObject):  # HiaViewModel
    """state information for binds views."""
    def __init__ (self, bindstore=None):
        GObject.GObject.__init__(self)
        self._device = None     # Active device (layout)
        self._group = 0         # Active group
        self._layer = 0         # Active layer
        self._vislayers = []    # Visible layers (list of bool)
        self._bindstore = bindstore
        if self._bindstore is None:
            self._bindstore = BindStore()

    def get_device (self): return self._device
    def set_device (self, val):
        self._device = val
        self.emit("device-changed", val)
    device = property(get_device, set_device)

    def get_group (self): return self._group
    def set_group (self, val):
        self._group = val
        self.emit("group-changed", val)
    group = property(get_group, set_group)

    def get_layer (self): return self._layer
    def set_layer (self, val):
        self._layer = val
        self.emit("layer-changed", val)
    layer = property(get_layer, set_layer)

    def get_vislayers (self): return self._vislayers
    def set_vislayers (self, val_iterable):
        if len(val_iterable) < len(self._vislayers):
            self._vislayers = self._vislayers[:len(val_iterable)]
        elif len(val_iterable) > len(self._vislayers):
            delta = len(val_iterable) - len(self._vislayers)
            self._vislayers.extend([False]*delta)
        for i in range(len(val_iterable)):
            self._vislayers[i] = val_iterable[i]
        self.emit("vislayers-changed", self._vislayers[:])
    vislayers = property(get_vislayers, set_vislayers)

    def get_bindstore (self): return self._bindstore
    def set_bindstore (self, val):
        self._bindstore = val
        self.emit("bindstore-changed", val)
    bindstore = property(get_bindstore, set_bindstore)

    __gsignals__ = {
        str("device-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (str,)),
        str("group-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (int,)),
        str("layer-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (int,)),
        str("vislayers-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (object,)),
        str("bindstore-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (object,)),
    }


class HiaDnd (object):
    """Drag-and-Drop opcodes enumeration;
overload the drag-drop 'info' field to as DnD opcodes."""
    class DndOpcodeEnum (object):
        _GENSYM = 1
        def __init__ (self, name, val=None):
            self.name = name
            if val is None:
                self.val = self.__class__._GENSYM
                self.__class__._GENSYM += 1
            else:
                self.val = val
        def get_name (self): return self.name
        def get_val (self): return self.val
        s = property(get_name)  # As string
        i = property(get_val)   # As integer
        d = property(get_val)   # As decimal
        def __int__ (self): return self.val
        def __str__ (self): return self.name
        def __eq__ (self, other):
            if type(other) == int: return other == self.val
            try:
                return other == self.val
            except:
                return (other is self)
        def _dnd_target (self, target_bitflags): return Gtk.TargetEntry.new(str(self), target_bitflags, int(self))
        def target_same_app (self): return self._dnd_target(Gtk.TargetFlags.SAME_APP)
        def target_same_widget (self): return self._dnd_target(Gtk.TargetFlags.SAME_WIDGET)
        def target_other_app (self): return self._dnd_target(Gtk.TargetFlags.OTHER_APP)
        def target_other_widget (self): return self._dnd_target(Gtk.TargetFlags.OTHER_WIDGET)
        def __repr__ (self): return "{}({!r},{!r})".format(self.__class__.__name__, self.name, self.val)

    enum = DndOpcodeEnum
    BIND = enum("bind", 1)
    UNBIND = enum("unbind", 2)
    SWAP = enum("swap", 3)
    REORDER = enum("reorder", 11)


class HiaBind (object):
    """POD for bind values to show in HiaTops.
"""
    # cmdcode used as lookup within cmdpack.
    def __init__ (self, redirects=0, cmdtitle=None, cmdcode=None):
        self.redirects = redirects
        self.cmdtitle = cmdtitle
        self.cmdcode = cmdcode

    def get_markup_str (self):
        """Return string intended for display to user."""
        dispval = self.cmdtitle
        if self.cmdcode is not None:
            dispval = self.cmdcode
        return dispval

    def __repr__ (self):
        return "{}(redirects={!r}, cmdtitle={!r}, cmdcode={!r})".format(
            self.__class__.__name__,
            self.redirects,
            self.cmdtitle,
            self.cmdcode)


class HiaBindable (GObject.GObject):
    """Bindables store and respond to changes in BindStore.
For HiaTops, affects bind value to display,
For HiaCluster, affects what layout to use.
"""
    def __init__ (self, view, hiasym, label=None):
        GObject.GObject.__init__(self)
        self.view = view
        self._bindstore = None
        bindstore = view.bindstore if view else BindStore()
        self.set_bindstore(bindstore)
        self.hiasym = str(hiasym)
        self.label = str(label if label is not None else self.hiasym)
        class ui: pass   # Plain data.
        self.ui = ui

    def get_bindstore (self):
        return self._bindstore
    def set_bindstore (self, val):
        if self._bindstore:
            # TODO: Disconnect
            pass
        self._bindstore = val
        self._bindstore.connect("bind-changed", self.on_bind_changed)
    bindstore = property(get_bindstore, set_bindstore)

    def on_bind_changed (self, bindstore, hiasym, newtitle, newcode):
        pass
    def on_group_changed (self, hiaview, newgrp):
        pass
    def on_layer_changed (self, hiaview, newlyr):
        pass
    def on_vislayers_changed (self, hiavia, vislayers):
        pass

    def get_bindlist (self):
        """Return list of HiaBind (one per layer)."""
        retval = []
        for lid in range(self.bindstore.nlayers):
            grpid = self.view.group
            bv = self.bindstore.get_bind(grpid, lid, self.hiasym)
            cmdtitle = bv.cmdtitle if bv else ""
            cmdcode = bv.cmdcode if bv else ""
            hb = HiaBind(-1, cmdtitle, cmdcode)
            retval.append(hb)
        return retval


class PlainData (object):
    def __getattr__ (self, attr):
        return self.__dict__[attr]
    def __setattr__ (self, attr, val):
        self.__dict__[attr] = val
    def __delattr__ (self, attr):
        del self.__dict__[attr]


class HiaTop (Gtk.Button, HiaBindable):
    """Generalization (i.e. not specific to keyboard) of keytop.
    
Visual:
+-----------
| display_label
|  ## spacer as needed ##
| [ layer0 ]
| [ layer1 ]
| ...
+-----------
    

Drag-and-Drop
* as source:
  * to CmdPackView = erase bind
  * to other HiaTop = swap bind
  * to Layer Selector = swap bind across layer
  * to Group Selector = swap bind across group
* as destination:
  * from CmdPackView = set/copy bind
  * from other HiaTop = swap bind
"""
    def __init__ (self, view, hiasym, label=None):
        HiaBindable.__init__(self, view, hiasym, label)
        Gtk.Button.__init__(self)

        self.binddisp = [ HiaBind(-1, ""), ]
        if self.bindstore:
            self.binddisp = self.get_bindlist()

        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()

    def setup_widgets (self):
        self.ui.top = Gtk.VBox()
        self.ui.lbl = Gtk.Label(label=self.label)
        self.ui.lbl.set_halign(Gtk.Align.START)
        self.ui.spacer = Gtk.VBox()
        self.ui.hrules = []
        self.ui.bindrows = []
        self.ui.layernums = []
        self.ui.bindviews = []
        self.ui.bindbufs = []

        self.ui.top.pack_start(self.ui.lbl, False, False, 0)
        self.ui.top.pack_start(self.ui.spacer, True, True, 0)

        self.add(self.ui.top)

        self.update_bindview()
        self.ui.top.show_all()

    def setup_signals (self):
        pass

    def update_bindview (self, binddisp=None):
        if binddisp is None:
            binddisp = self.binddisp
        for bi in range(len(binddisp)):
            bd = binddisp[bi]
            if len(self.ui.bindrows) <= bi:
                # Add another row.
                bb, bv = Gtk.TextBuffer(), Gtk.TextView()
                markup = bd.get_markup_str()
                bb.insert_markup(iter=bb.get_end_iter(), markup=markup, len=-1)
                bv.set_buffer(bb)
                br = Gtk.HBox()
                lyr = Gtk.Label(label="{}:".format(bi))
                self.ui.bindrows.append(br)
                self.ui.bindbufs.append(bb)
                self.ui.bindviews.append(bv)
                br.pack_start(lyr, False, False, 0)
                br.pack_start(bv, True, True, 0)
                hrule = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                self.ui.hrules.append(hrule)
                self.ui.top.pack_start(hrule, False, False, 0)
                self.ui.top.pack_start(br, False, False, 0)
                hrule.show()
                br.show_all()
            else:
                # Update extant row.
                bb = self.ui.bindbufs[bi]
                bb.delete(bb.get_start_iter(), bb.get_end_iter())
                markup = bd.get_markup_str()
                bb.insert_markup(iter=bb.get_end_iter(), markup=markup, len=-1)
            # Sensitize to active layer.
            #self.ui.bindviews[bi].set_sensitive(bi == self.view.layer)
#            bv = self.ui.bindviews[bi]
#            if bi == self.view.layer:
#                bv.set_state_flags(Gtk.StateFlags.ACTIVE, False)
#            else:
#                bv.set_state_flags(Gtk.StateFlags.NORMAL, False)
        for bi in range(len(binddisp), len(self.ui.bindrows)):
            self.ui.hrules[bi].hide()
            self.ui.bindrows[bi].hide()
        return

    def update_bindlist (self, bindlist):
        binddisp = []
        for lid in range(len(self.view.vislayers)):
            if self.view.vislayers[lid]:
                hiabind = bindlist[lid]
                binddisp.append(hiabind)
        self.binddisp = binddisp
        self.update_bindview(binddisp)

    def on_bind_changed (self, bindstore, hiasym, newtitle, newcode):
        bindlist = self.get_bindlist()
        self.update_bindlist(bindlist)
    def on_group_changed (self, hiaview, newgrp):
        bindlist = self.get_bindlist()
        self.update_bindlist(bindlist)
    def on_layer_changed (self, hiaview, newlyr):
        self.update_bindview()
    def on_vislayers_changed (self, hiavia, vislayers):
        self.update_bindlist()

    def setup_dnd (self):
        # DnD source: erase, swap.
        drag_targets = [
            HiaDnd.UNBIND.target_same_app(),
            HiaDnd.SWAP.target_same_app(),
            ]
        drag_actions = Gdk.DragAction.COPY
        self.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, drag_targets, drag_actions)
        # DnD destination: bind, swap.
        drop_targets = [
            HiaDnd.BIND.target_same_app(),
            HiaDnd.SWAP.target_same_app(),
            ]
        drop_flags = Gtk.DestDefaults.DROP
        drop_actions = Gdk.DragAction.COPY
        self.drag_dest_set(drop_flags, drop_targets, drop_actions)





class HiaLayoutStore (Gtk.TreeStore):
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

width, height - in terms of cells (Gtk.Table, GtkGrid)
"""

    def __init__ (self, layout_name):
        # (hiasym, label, prototype,  x, y, width_columns, height_rows)
        Gtk.TreeStore.__init__(self, str, str, str, int, int, int, int)
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
        treeiter = Gtk.TreeStore.append(self, parentiter, rowdata)
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

class HiaLayouts (Gtk.ListStore):
    """AssociationList of HiaLayoutStore.
Rows are tuples of (layout_name, layout_map).
"""
    def __init__ (self):
        #Gtk.ListStore.__init__(self, gobject.TYPE_STRING, gobject.TYPE_OBJECT)
        Gtk.ListStore.__init__(self, str, object)

    def build_from_all_rowrun (self, all_rowrun):
        for hidname in all_rowrun.keys():
            hiditem = all_rowrun[hidname]
            onelayout = HiaLayoutStore(hidname)
            onelayout.build_from_rowrun(hiditem)
            row = self.append((hidname, onelayout))

    def build_from_legacy_store (self):
        alldata = kbd_desc.KBD
        self.build_from_all_rowrun(alldata)

    def __findkey (self, key):
        match = []
        for row in Gtk.ListStore.__iter__(self):
            if row[0] == key:
                match.append(row)
        return match

    def __contains__ (self, key):
        return bool(self.__findkey(key))

    def __getitem__ (self, key):
        match = self.__findkey(key)
        if match:
            return match[0]
        return Gtk.ListStore.__getitem__(self, key)
        #raise KeyError("Key not found: {}".format(key))
    def __setitem__ (self, key, val):
        try:
            Gtk.ListStore.__setitem__(self, key, val)
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

class ClusteredLayouts (HiaLayouts):
    """Nested layouts for clusters."""
    def __init__ (self, symprefix):
        HiaLayouts.__init__(self)
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
        layout = HiaLayoutStore(layoutname)
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
            ("t", 0, 0),
            ("dt", 2, 0),
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
            ("1", 0, 0), ("2", 1, 0), ("3", 2, 0),
            ("4", 0, 1), ("5", 1, 1), ("6", 2, 1),
            ("7", 0, 2), ("8", 1, 2), ("9", 2, 2),
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

        def SYM (suffix):
            """Helper function for manually-defined layouts - generate extended hiasym."""
            return "{}{}".format(self.symprefix, suffix)

        # The irregular layouts: 7, 13
        """
        |  1 2
        | 3 4 5
        |  6 7
        """
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
        # Generate RadialMenu01 through RadialMenu20
        for variant in range(1,21):
            layout = self.make_layoutstore("{}{:02d}".format("RadialMenu", variant))
            for entry in radialize(variant, r=6):
                layout.append(None, entry)
            self.append( (layout.name, layout) )
        return


class HiaSurface (Gtk.Grid):
    """Display of a HiaLayout."""
    def __init__ (self, view):
        Gtk.Grid.__init__(self)
        self.set_row_homogeneous(True)
        self.set_column_homogeneous(True)
        self.view = view
        self._layout = None
        self.children = {}   # map hiasym to hiatop

    def get_layout (self):
        return self._layout
    def set_layout (self, layout):
        self._layout = layout
        self.rebuild_surface()
    layout = property(get_layout, set_layout)

    def disown_children (self):
        chlist = self.get_children()
        # TODO: disconnect signals.
        for ch in chlist:
            self.remove(ch)
        self.children = {}

    def make_hiawidget_cluster (self, hiasym, hialabel):
        retval = None
        return retval
    def make_hiawidget_key (self, hiasym, hialabel):
        retval = HiaTop(self.view, hiasym, hialabel)
        retval.show()
        return retval

    def make_hiawidget (self, hiasym, hialabel, hiaprototype):
        dispatch = {
            str("cluster"): self.make_hiawidget_cluster,
            str("key"): self.make_hiawidget_key,
        }
        maker = dispatch.get(hiaprototype, self.make_hiawidget_key)
        retval = maker(hiasym, hialabel)
        return retval

    def rebuild_surface (self):
        self.disown_children()
        if not self.layout:
            return
        max_row = 0
        for rowentry in self.layout:
            intent = (str,str,str, int,int,int,int)
            #(hiasym, lbl, prototype, x, y, w, h) = rowentry
            (hiasym, lbl, prototype, x, y, w, h) = [ intended(rawval) for (intended,rawval) in zip(intent,rowentry) ]
            hw = self.make_hiawidget(hiasym, lbl, prototype)
            #self.children.append(hw)
            self.children[hiasym] = hw
            if hw:
                self.attach(hw, x, y, w, h)
            if y > max_row:
                max_row = y
        for y in range(max_row):
            if not self.get_child_at(0, y):
                self.attach(Gtk.Label(), 0, y, 1, 1)
        self.show()
        return


class HiaCluster (Gtk.Frame, HiaBindable):
    """
Represent the jointed cluster types, e.g. joystick, mousepad, button_quad, etc.
"""
    def __init__ (self, view, hiasym, label=None):
        HiaBindable.__init__(self, view, hiasym, label)
        Gtk.Frame.__init__(self)
        self.hiachildren = []   # List of nested HiaBindable
        self._clustered_layouts = ClusteredLayouts(self.hiasym)
        bindlist = self.get_bindlist()
        layoutname = bindlist[self.view.layer].cmdtitle
        try:
            self._layout = self._clustered_layouts[layoutname][1]
        except TypeError:
            self._layout = None
        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()

    def setup_widgets (self):
        self.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.ui.frame_title = Gtk.HBox()
        self.ui.frame_menu = Gtk.Button(label="=")
        self.ui.frame_label = Gtk.Label(label=self.label)
        self.ui.frame_title.pack_start(self.ui.frame_menu, False, False, 0)
        self.ui.frame_title.pack_start(self.ui.frame_label, False, False, 0)
        self.set_label_widget(self.ui.frame_title)
        #self.ui.frame_title.show_all()

        self.ui.planar = HiaSurface(self.view)
        self.ui.planar.layout = self._layout
        self.ui.tabular = None

        self.ui.top = Gtk.Stack()
        self.ui.top.add_named(self.ui.planar, "planar")

        self.add(self.ui.top)

        self.show_all()

    def setup_signals (self):
        return

    def setup_dnd (self):
        return

    def get_layout (self):
        return self._layout
    def set_layout (self, val):
        self._layout = val
        self.ui.planar.layout = val
    layout = property(get_layout, set_layout)

    def on_bind_changed (self, bindstore, hiasym, newtitle, newcode):
        layoutname = newtitle
        try:
            layoutinfo = self._clustered_layouts[layoutname][1]
        except TypeError:
            layoutinfo = None
        self.layout = layoutinfo
        return
    def on_group_changed (self, hiaview, newgrp):
        return
    def on_layer_changed (self, hiaview, newlyr):
        return
    def on_vislayers_changed (self, hiavia, vislayers):
        return



#############
# Selectors #
#############

class HiaSelector (Gtk.Frame):
    """
Row of RadioButton (one-of-many pressed)
"""
    EXPAND_MEMBERS = False
    PADDING = 0
    def __init__ (self, title, view, names_iterable):
        Gtk.HBox.__init__(self)
        self.view = view
        self._title = title
        self._namelist = Gtk.ListStore(str)
        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()
        self.set_names(names_iterable)

    def setup_widgets (self):
        class ui: pass
        self.ui = ui
        #self.update_widgets()
        self.set_label(self._title)
        self.ui.top = Gtk.HBox()

        self.add(self.ui.top)
        self.show_all()
        return

    def setup_signals (self):
        return

    def setup_dnd (self):
        return

    def update_widgets (self):
        for ch in self.ui.top.get_children():
            # TODO: disconnect signals.
            self.ui.top.remove(ch)
        self.buttons = []
        group = None
        for listrow in self._namelist:
            name = listrow[0]
            b = Gtk.RadioButton(group=group, label=name)
            if not self.buttons:
                group = b
            #b.connect("clicked", self.on_button_clicked)
            b.connect("clicked", self.on_button_clicked, len(self.buttons))
            #b.connect("toggled", self.on_button_clicked, len(self.buttons))
            b.show()
            self.buttons.append(b)
            self.ui.top.pack_start(b, self.EXPAND_MEMBERS, False, self.PADDING)
        return

    def get_names (self):
        return [ x[0] for x in self._namelist ]
    def set_names (self, names_iterable):
        self._namelist.clear()
        for name in names_iterable:
            self._namelist.append( (name,) )
        self.update_widgets()
    names = property(get_names, set_names)

    def get_title (self): return self._title
    def set_title (self, val):
        self._title = None
        self.set_label(self._title)
    title = property(get_title, set_title)

    def on_button_clicked (self, w, ofs=None):
        print("generic clicked")
        return


class HiaSelectorGroup (HiaSelector):
    EXPAND_MEMBERS = False
    PADDING = 16
    def __init__ (self, view, names_iterable):
        HiaSelector.__init__(self, "Mode", view, names_iterable)
    def on_button_clicked (self, w, ofs=None):
        if w.get_active():
            self.view.group = int(ofs)
        return


class HiaSelectorLayer (HiaSelector):
    EXPAND_MEMBERS = True
    def __init__ (self, view, names_iterable):
        HiaSelector.__init__(self, "Layer", view, names_iterable)
    def on_button_clicked (self, w, ofs=None):
        if w.get_active():
            self.view.layer = int(ofs)
        return


# Intended to be named HiaSelectorLayout, but spelling too similar to *Layer
class HiaSelectorDevice (Gtk.HBox):
    def __init__ (self, view, layouts):
        Gtk.HBox.__init__(self)
        self.view = view
        self.layouts = layouts
        self._model = Gtk.ListStore(str)
        layoutnames = sorted(self.layouts.keys())
        for i in range(len(layoutnames)):
            layoutname = layoutnames[i]
            self._model.append( (layoutname,) )
        self.setup_widgets()
        self.setup_signals()

    def setup_widgets (self):
        class ui: pass
        self.ui = ui

        self.ui.lbl = Gtk.Label(label="Device:")

        self.ui.render0 = Gtk.CellRendererText()

        #self.ui.sel = Gtk.ComboBox(model=self._model)
        dropbox = Gtk.ComboBox(model=self._model)
        dropbox.pack_start(self.ui.render0, 0)
        dropbox.add_attribute(self.ui.render0, 'text', 0)
        dropbox.set_active(0)
        self.view.device = ('(none)', None)
        self.ui.dropbox = dropbox

        self.pack_start(self.ui.lbl, False, False, 0)
        self.pack_start(self.ui.dropbox, False, False, 0)

        self.show_all()

    def setup_signals (self):
        self.ui.dropbox.connect("changed", self.on_selection_changed)

    def on_selection_changed (self, w):
        ofs = w.get_active()
        layoutname = self._model[ofs][0]
        #layoutinfo = self.layouts[layoutname]
        self.view.device = layoutname



