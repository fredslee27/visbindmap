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
            i = len(self)
            cb = lambda hiasym: self.observe_layerbind(i, hiasym)
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
        self.emit("ngroups-changed", n)
    ngroups = property(get_ngroups, set_ngroups)

    # This code section assumes all layers are the same size.
    # Later revisions may support different layers per group.
    def get_nlayers (self):
        return self.groups[0].nlayers
    def set_nlayers (self, n):
        for g in self.groups:
            g.set_nlayers(n)
        # TODO: should also emit when invoking BindLayer.set_nlayers()
        self.emit("nlayers-changed", 0, n)
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
        """Main entry point: set binding for given group, layer, hiasym:
 set_bind(groupid, layerid, hiasym, instance_BindValue)
 set_bind(groupid, layerid, hiasym, cmdtitle, cmdcode)
 set_bind(groupid, layerid, hiasym, cmdtitle)
"""
        cooked = None
        if hiacmd is not None:
            cooked = BindValue(hiaval, hiacmd)
        else:
            try:
                hiaval.cmdtitle, hiaval.cmdvalue  # quack-quack
                cooked = hiaval
            except AttributeError:
                cooked = BindValue(hiaval, hiaval)
        self.groups[groupid][layerid][hiasym] = cooked

    __gsignals__ = {
        # (hiasym, newtitle, newcode)
        str("bind-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (str, str, str) ),
        # (ngroups)
        str("ngroups-changed"): (GObject.SIGNAL_RUN_FIRST, None, (int,) ),
        # (groupid, nlayers)
        str("nlayers-changed"): (GObject.SIGNAL_RUN_FIRST, None, (int, int) ),
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
        self._device = None         # Active device id (layout)
        self._group = 0             # Active group
        self._layer = 0             # Active layer
        self._vislayers = [True]    # Visible layers (list of bool)

        n = bindstore.nlayers
        while len(self._vislayers) < n:
            self._vislayers.append(False)

        self._bindstore = bindstore
        if self._bindstore is None:
            self._bindstore = BindStore()
        self._bindstore.connect("nlayers-changed", self.on_bindstore_nlayers_changed)

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
        resize = 1
        try:
            iter(val_iterable)
            # is iterable.
            resize = len(val_iterable)
        except:
            # not iterable, expect int.
            resize = int(val_iterable)
        if len(self.vislayers) < resize:
            delta = resize - len(self.vislayers)
            self.vislayers.extend([False] * delta)
        if len(self.vislayers) > resize:
            del self.vislayers[resize:]
        try:
            # Try copy.
            self.vislayers[:] = val_iterable[:]
        except:
            # Nothing to copy, keep to simple resize.
            pass
        # use copy of list to suppress back-propagation of mutations.
        self.emit("vislayers-changed", self._vislayers[:])

    vislayers = property(get_vislayers, set_vislayers)

    def get_bindstore (self): return self._bindstore
    def set_bindstore (self, val):
        self._bindstore = val
        self.emit("bindstore-changed", val)
    bindstore = property(get_bindstore, set_bindstore)

    def on_bindstore_nlayers_changed (self, bindstore, groupid, nlayers):
        # Auto-resize vislayers to new number of layers.
        vislayers = self.vislayers[:]
        if len(vislayers) < nlayers:
            delta = nlayers - len(vislayers)
            vislayers.extend([False] * delta)
        if len(vislayers) > nlayers:
            vislayers = vislayers[:nlayers]
        self.set_vislayers(vislayers)
        return

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
    """POD for bind values to show in HiaBindable.
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
        #self._view = view
        #bindstore = view.bindstore if view else BindStore()
        self.set_view(view)
        #self.set_bindstore(bindstore)
        self.hiasym = str(hiasym)
        self.label = str(label if label is not None else self.hiasym)
        class ui: pass   # Plain data.
        self.ui = ui

    def get_view (self):
        return self._view
    def set_view (self, val):
        self._view = val
        bindstore = self._view.bindstore
        bindstore.connect("bind-changed", self.on_bind_changed)
        self._view.connect("bindstore-changed", self.on_bindstore_changed)
    view = property(get_view, set_view)

    def get_bindstore (self):
        return self.view.bindstore
    def set_bindstore (self, val):
#        if self._bindstore:
#            # TODO: Disconnect
#            pass
#        self._bindstore = val
#        self._bindstore.connect("bind-changed", self.on_bind_changed)
        pass
    bindstore = property(get_bindstore, set_bindstore)

    def on_bindstore_changed (self, view, bindstore):
        bindstore.connect("bind-changed", self.on_bind_changed)
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
        """Set up Gtk widgets in HiaTop"""
        self.set_no_show_all(True)

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
        self.ui.lbl.show()
        self.ui.spacer.show()
        self.ui.top.show()
        self.show()

    def setup_signals (self):
        """Set up widget signals within HiaTop."""
        self.view.connect("group-changed", self.on_group_changed)
        self.view.connect("layer-changed", self.on_layer_changed)
        self.view.connect("vislayers-changed", self.on_vislayers_changed)

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
                self.ui.layernums.append(lyr)
                br.pack_start(lyr, False, False, 0)
                br.pack_start(bv, True, True, 0)
                hrule = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                self.ui.hrules.append(hrule)
                self.ui.top.pack_start(hrule, False, False, 0)
                self.ui.top.pack_start(br, False, False, 0)
                if self.view.vislayers[bi]:
                    hrule.show()
                    br.show_all()
            else:
                # Update extant row.
                hr = self.ui.hrules[bi]
                br = self.ui.bindrows[bi]
                bv = self.ui.bindviews[bi]
                bb = self.ui.bindbufs[bi]
                lyr = self.ui.layernums[bi]
                bb.delete(bb.get_start_iter(), bb.get_end_iter())
                markup = bd.get_markup_str()
                bb.insert_markup(iter=bb.get_end_iter(), markup=markup, len=-1)
                if self.view.vislayers[bi]:
                    br.show()
                    bv.show()
                    lyr.show()
                    hr.show()
                else:
                    br.hide()
                    hr.hide()
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
        bindlist = self.get_bindlist()
        self.update_bindlist(bindlist)
    def on_vislayers_changed (self, hiavia, vislayers):
        bindlist = self.get_bindlist()
        self.update_bindlist(bindlist)

    def setup_dnd (self):
        """Set up Drag-and-Drop for HiaTop."""
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
        self.set_row_spacing(1)
        self.set_column_spacing(1)
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
        retval = HiaCluster(self.view, hiasym, hialabel)
        retval.show()
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
                filler = Gtk.HBox()
                filler.show()
                self.attach(filler, 0, y, 1, 1)
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
        """Set up Gtk widgets within HiaCluster."""
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
        """Set up widget signas in HiaCluster."""
        return

    def setup_dnd (self):
        """Set up Drag-and-Drop for HiaCluster."""
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
        Gtk.Frame.__init__(self)
        self.view = view
        self._title = title
        self._namelist = Gtk.ListStore(str)
        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()
        self.set_names(names_iterable)

    def setup_widgets (self):
        """Set up Gtk widgets within HiaSelect (base class)."""
        class ui: pass
        self.ui = ui
        #self.update_widgets()
        self.set_label(self._title)
        self.ui.top = Gtk.HBox()

        self.add(self.ui.top)
        self.show_all()
        return

    def setup_signals (self):
        # Base class method.
        return

    def setup_dnd (self):
        # Base class method.
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
    def __init__ (self, view, names_iterable=None):
        if names_iterable is None:
            names_iterable = []
        adjusted = [ "GLOBAL" ] + [ x for x in names_iterable ]
        HiaSelector.__init__(self, "Mode", view, adjusted)
    def on_button_clicked (self, w, ofs=None):
        if w.get_active():
            self.view.group = int(ofs)
        return


class HiaSelectorLayer (HiaSelector):
    EXPAND_MEMBERS = True
    def __init__ (self, view, names_iterable=None):
        if names_iterable is None:
            names_iterable = [ 'base' ]
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
        self._layouts = layouts
        self._model = Gtk.ListStore(str)
        layoutnames = sorted(self.layouts.keys())
        for i in range(len(layoutnames)):
            layoutname = layoutnames[i]
            self._model.append( (layoutname,) )
        self.setup_widgets()
        self.setup_signals()

    def setup_widgets (self):
        """Set up Gtk widgets within HiaSelectorCmd."""
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
        """Set up widget signals within HiaSelectorCmd."""
        self.ui.dropbox.connect("changed", self.on_selection_changed)

    def get_layouts (self):
        return self._layouts
    def set_layouts (self, val):
        self._layouts = val
        try:
            self.ui.dropbox.set_model(val)
        except AttributeError:
            pass
    layouts = property(get_layouts, set_layouts)

    def on_selection_changed (self, w):
        ofs = w.get_active()
        layoutname = self._model[ofs][0]
        #layoutinfo = self.layouts[layoutname]
        self.view.device = layoutname



########################
## Command Set Source ##
########################

class CommandPackStore (Gtk.TreeStore):
    def __init__ (self, packname=None, cmd_iterables=None):
        # ( cmd_id_number, cmd_name, display_text, tooltip_markup )
        Gtk.TreeStore.__init__(self, int, str, str, str)
        self._cursor = None
        self.uri = None             # Original source URI, if applicable.
        self.modelist = []          # List of names for modes/groups.
        self.packname = packname    # Name of pack, used in window title.
        # Default initial: unbind
        Gtk.TreeStore.append(self, None, (0, "", "(unbind)", ""))

    def begin_group (self, entry):
        """Serial creation -- create a nested grouping."""
        rowdata = entry
        # expect type(entyr) == tuple
        if not isinstance(entry, tuple):
            # Assume type(entry)==str; convert to expected tuple.
            rowdata = (-1, "", entry, "")
        cursor = Gtk.TreeStore.append(self, self._cursor, rowdata)
        self._cursor = cursor

    def end_group (self):
        """Serial creation -- end of a nested grouping; continue more adds with the parent."""
        if self._cursor:
            self._cursor = self.iter_parent(self._cursor)
        return

    def append (self, entry, *more):
        """Serial creation -- add entry at cursor."""
        if isinstance(entry, tuple):
            return Gtk.TreeStore.append(self, self._cursor, entry)
        else:
            # Assume tuple elements passed in as the arguments.
            #return Gtk.TreeStore.append(self, self._cursor, (entry,)+more)
            return Gtk.TreeStore.append(self, entry, *more)

    def _restore_tree (self, cmds_iterable):
        tupleiter = cmds_iterable.__iter__()
        treeiter = self.get_iter_root()
        stack = []  # recurse stack: element=(tuple_iterator, tree_iterator)
        while stack or tupleiter:
            try:
                entry = tupleiter.next()
            except StopIteration:
                # No more tuples, try to restore from stack.
                if stack:
                    tupleiter, treeiter = stack[-1]
                    del stack[-1]
                    continue
                else:
                    # Stack also empty; terminate loop.
                    break
            rowtuple, subtree = entry
            rowiter = self.append(treeiter, rowtuple)
            if subtree:
                stack.append( (tupleiter, treeiter) )
                treeiter = rowiter
                tupleiter = subtree.__iter__()

    def restore (self, primitives):
        if primitives['__class__'] != self.__class__.__name__:
            raise TypeError("Expected restore from class {}".format(self.__class__.__name__))
        self.packname = primitives['packname']
        cmds_iterable = primitives['cmds_iterable']
        self._restore_tree(cmds_iterable)

    def _snapshot_tree (self, treestore):
        retval = []
        stack = []
        treeiter = treestore.get_iter_first()
        while stack or treeiter:
            subtree = None
            if not treeiter:
                # end of (sub)list, resume from stack.
                subtree = retval
                treeiter, retval = stack[-1]
                del stack[-1]
            elif treestore.iter_has_child(treeiter):
                # save state, recurse.
                stack.append( (treeiter, retval) )
                retval = []
                treeiter = treestore.iter_children(treeiter)
                #continue

            rowtuple = tuple(self[self.get_path(treeiter)])
            entry = (rowtuple, subtree)
            retval.append(entry)
            treeiter = self.iter_next(treeiter)
        return retval

    def snapshot (self):
        retval = { "__class__": self.__class__.__name__ }
        retval['packname'] = self.packname
        retval['cmds_iterable'] = self._snapshot_tree(self)
        return retval

    def __repr__ (self):
        return "{}(packname={!r}, cmds_iterable={!r})".format(
            self.__class__.__name__,
            self.packname,
            self._snapshot_tree(self))


#
# Subclasses should implement functions:
#  @staticmethod is_acceptable(uri) 
#  build(self)
# 
# Use case:
#  CommandPackFeed.from_uri("file:///path/to/command/pack.csv")
#  => searches REGISRY for an instance where is_acceptable(uri) returns true
#  => instantiates that subclass with the specified URI
#  => invokes build() to populate instance.cmdpack, instance.modelist, instance.packname
#  
# Implementation case:
#  Subclass CommandPackFeed
#  Decorate with @CommandPackFeed.register to automagically register with base class/factory method.
#  Implement function @staticmethod is_acceptable(uri), returns bool.
#  Implement build(), guided with self._path, to populate self._cmdpack
class CommandPackFeed (object):
    """Base class for command pack source."""
    REGISTRY = {}   # class-scope, registry of specific command pack feeds.
    def __init__ (self, path):
        self._path = path       # Path/URI for command pack feed.
        self._cmdpack = None    # Instance of CommandPackStore made from URI.
        self._modelist = None   # GtkListStore: list of names for modes/groups.
        self._packname = None   # Name of the pack feed, used in window title.

    @staticmethod
    def is_acceptable (uri):
        raise NotImplementedError("Must implement method is_acceptable(uri)")
        return False

    def read (self):
        """Override in subclass.  Generate CommandPackStore from contents of URI.
Returns CommandPackStore instance.
"""
        return CommandPackStore("")

    @staticmethod
    def register (classobj):
        """Class scope, register specific command pack feed to be used from factory function.
Subclasses define @staticmethod is_acceptable(uri) if it understands URI.
Usable as a decorator to automagically register subclasses:

@CommandPackFeed.register
class CommandPackFeed_custom01 (CommandPackFeed):
  @staticmethod
  def is_acceptable (uri):
    ...
  def build (self):
    # uri is stored as self._path from constructor.
    ...
"""
        if not classobj in CommandPackFeed.REGISTRY:  # Do not overwite
            CommandPackFeed.REGISTRY[classobj] = classobj
        return classobj
    @staticmethod
    def open (uri):
        """Main factory function. Given a URI, automagically find subclass that can handle the URI, ready to create CommandPackStore (call read())."""
        for packtype in CommandPackFeed.REGISTRY:
            factory = packtype
            if factory.is_acceptable(uri):
                inst = factory(uri)
                return inst
        raise NameError("No factory for command pack source {!r}".format(uri))

# subclasses of CommandPackFeed can be decorated with CommandPackFeed.register to automagically register with the base class.
@CommandPackFeed.register
class CommandPackFeed_builtin (CommandPackFeed):
    """Builtin/hard-coded CommandPackFeed."""
    @staticmethod
    def is_acceptable (uri):
        # URI of None yields the hard-coded command pack feed.
        return (uri is None)

    def read (self):
        cmdpack = CommandPackStore("(builtin)")
        cmdpack._uri = self._path

        modelist = Gtk.ListStore(str,str)
        modelist.append( ("Global", None) )
        modelist.append( ("Menu", "Global") )
        modelist.append( ("Game", "Global") )
        cmdpack._modelist = modelist

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

        return cmdpack


class HiaSelectorCommand (Gtk.VBox):
    """View of the command pack.

static method 'make_model()' for generating a suitable TreeStore expected by this widget.
"""
    # Expected to rarely change, so model signals are ignored and instead set_model triggers refreshing view.
    def __init__ (self, mdl):
        Gtk.VBox.__init__(self)
        self._model = mdl
        if mdl is None:
            self._model = self.make_model()
        self._packname = None
        self.setup_widgets()
        self.setup_dnd()

    def get_model (self):
        return self._model
    def set_model (self, mdl=None):
        if mdl is not None:
            self._model = mdl
            self.ui.treeview.set_model(mdl)
            try:
                self._packname = self._model.packname
            except AttributeError:
                self._packname = None
            self.update_widgets()
    model = property(get_model, set_model)

    def setup_widgets (self):
        class ui: pass
        self.ui = ui

        self.ui.sclwin = Gtk.ScrolledWindow()

        self.ui.treeview = Gtk.TreeView(model=self._model)
        self.ui.treecols = []
        self.ui.treecelltxt = Gtk.CellRendererText()
        colname = "command"
        if self._model:
            colname = self._model.packname
        col0 = Gtk.TreeViewColumn(colname, self.ui.treecelltxt, text=2)
        self.ui.treecols.append(col0)
        for col in self.ui.treecols:
            self.ui.treeview.append_column(col0)

        self.ui.sclwin.add(self.ui.treeview)
        self.add(self.ui.sclwin)
        self.show_all()

        self.props.has_tooltip = True
        self.knowwhat = "cmdpackview"

    def update_widgets (self):
        self.ui.treeview.set_model(self._model)
        if self.packname:
            self.ui.treecols[0].set_title(self.packname)
        else:
            self.ui.treecols[0].set_title("command")
        return

    def setup_dnd (self):
        # DnD source: bind.
        drag_targets = [
            HiaDnd.BIND.target_same_app(),
            ]
        drag_actions = Gdk.DragAction.COPY
        self.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, drag_targets, drag_actions)
        # DnD destination: unbind.
        drop_targets = [
            HiaDnd.UNBIND.target_same_app(),
            ]
        drop_flags = Gtk.DestDefaults.DROP
        drop_actions = Gdk.DragAction.COPY
        #self.drag_dest_set(drop_flags, drop_targets, drop_actions)
    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        # is DnD source.
        treesel = w.get_selection()
        mdl, pathsels = treesel.get_selected_rows()
        firstsel = pathsels[0]
        selrow = mdl[firstsel]
        cmdname = selrow[1]
        if info == DndOpcodes.BIND:
            # dragged from command set.
            seldata.set(seldata.target, 8, str(cmdname))
            return True
        return False
    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        if info == DndOpcodes.UNBIND:
            hiasym = seldata.data
            return True
        return False

    @staticmethod
    def make_model ():
        # Data tuples = ( cmd_id_number, cmd_name, display_text, tooltip_text )
        store = CommandPackStore()
        store.append(None, (0, "", "(unbind)", None))
        return store




###################
# Aggregated View #
###################

# DEPRCATED
class HiaPicker (Gtk.VBox):
    def __init__ (self, view, layouts):
        Gtk.VBox.__init__(self)
        self.view = view
        self.layouts = layouts
        self.setup_widgets()
        self.setup_signals()

    def setup_widgets (self):
        class ui: pass
        self.ui = ui

        self.ui.sel_device = HiaSelectorDevice(self.view, self.layouts)
        self.ui.sel_group = HiaSelectorGroup(self.view, None)
        self.ui.sel_layer = HiaSelectorLayer(self.view, None)
        self.ui.sel_bind = HiaSurface(self.view)

        self.ui.sel_device.show_all()
        self.ui.sel_group.show_all()
        self.ui.sel_layer.show_all()
        self.ui.sel_bind.show()

        self.pack_start(self.ui.sel_device, False, False, 0)
        self.pack_start(self.ui.sel_group, False, False, 0)
        self.pack_start(self.ui.sel_layer, False, False, 0)
        self.pack_start(self.ui.sel_bind, False, False, 0)

        self.show()
        return

    def setup_signals (self):
        self.view.connect("device-changed", self.on_device_changed)
        return

    def on_device_changed (self, w, newdev):
        layoutinfo = self.layouts[newdev]
        layoutname, layoutdata = layoutinfo
        self.ui.sel_bind.set_layout(layoutdata)
        return


# Put together the command picker, the device selector, the group selector, the layer selector, the bind selector.
#
# +------------------------------
# | CmdPick | [DeviceSelector  v]
# |         |  ( ) Mode0   ( ) Mode1  ...
# |         |  ( ) Layer0  ( ) Layer1 ...
# |         | { HiaSelectorBind
# |         |  .
# |         |   .
# |         |    .
# |         |     }
# +---------+--------------------
class HiaPlanner (Gtk.HPaned):
    def __init__ (self, cmdpack, view, layouts):
        Gtk.HPaned.__init__(self)
        self.view = view
        self._layouts = layouts
        self._cmdpack = cmdpack
        self.setup_widgets()
        self.setup_signals()

    def get_layouts (self):
        return self._layouts
    def set_layouts (self, val):
        self._layouts = val
        try:
            self.ui.sel_device.set_model(val)
        except AttributeError:
            pass
    layouts = property(get_layouts, set_layouts)

    def get_cmdpack (self):
        return self._cmdpack
    def set_cmdpack (self, val):
        self._cmdpack = val
        try:
            self.ui.sel_cmd.set_model(val)
        except AttributeError:
            pass
    cmdpack = property(get_cmdpack, set_cmdpack)

    def setup_widgets (self):
        """Set up Gtk widgets within HiaPlanner."""
        class ui: pass
        self.ui = ui

        self.ui.sel_cmd = HiaSelectorCommand(self.cmdpack)
        self.ui.sel_device = HiaSelectorDevice(self.view, self.layouts)
        self.ui.sel_group = HiaSelectorGroup(self.view, None)
        self.ui.sel_layer = HiaSelectorLayer(self.view, None)
        self.ui.sel_bind = HiaSurface(self.view)

        self.ui.lhs = Gtk.VBox()
        self.ui.lhs.pack_start(self.ui.sel_cmd, True, True, 0)

        self.ui.rhs = Gtk.VBox()
        self.ui.rhs.pack_start(self.ui.sel_device, False, False, 0)
        self.ui.rhs.pack_start(self.ui.sel_group, False, False, 0)
        self.ui.rhs.pack_start(self.ui.sel_layer, False, False, 0)
        self.ui.rhs.pack_start(self.ui.sel_bind, False, False, 0)

        self.add1(self.ui.lhs)
        self.add2(self.ui.rhs)

        # TODO: calculate width and heights based on default typeface.
        ex, lineheight = 8, 12
        # command-picker width 24ex.
        self.set_position(24*ex)

        self.show_all()

    def setup_signals (self):
        self.view.connect("device-changed", self.on_device_changed)
        return

    def on_device_changed (self, w, newdev):
        layoutinfo = self.layouts[newdev]
        layoutname, layoutdata = layoutinfo
        self.ui.sel_bind.set_layout(layoutdata)
        return



