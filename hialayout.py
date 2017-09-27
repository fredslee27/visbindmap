#!/usr/bin/env python3
# Python3 and Gtk3

# Python2-combatibility
from __future__ import print_function, with_statement, unicode_literals

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib




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
        self.group = 0          # Active group
        self.layer = 0          # Active layer
        self.vislayers = []     # Visible layers (list of bool)
        self.bindstore = bindstore
        if self.bindstore is None:
            self.bindstore = BindStore()

    __gsignals__ = {
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


class HiaBindable (GObject.GObject):
    """Bindables store and respond to changes in BindStore.
For HiaTops, affects bind value to display,
For HiaCluster, affects what layout to use.
"""
    def __init__ (self, view, bindstore, hiasym, label=None):
        GObject.GObject.__init__(self)
        self.view = view
        if bindstore is None:
            self._bindstore = BindStore()
        else:
            self._bindstore = bindstore
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

    def on_bind_changed (self, bindstore, hiasym, newtitle, newcode):
        pass
    def on_group_changed (self, hiaview, newgrp):
        pass
    def on_layer_changed (self, hiaview, newlyr):
        pass
    def on_vislayers_changed (self, hiavia, vislayers):
        pass

    def get_bindview (self):
        """Return list of HiaBind (one per layer)."""
        retval = []
        for lid in range(self.bindstore.nlayers):
            grpid = view.group
            lyrid = view.layer
            bv = self.bindstore.get_bind(grpid, lyrid, self.hiasym)
            hb = HiaBind(-1, bv.cmdtitle, bv.cmdcode)
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
    def __init__ (self, view, bindstore, hiasym, label=None):
        HiaBindable.__init__(self, view, bindstore, hiasym, label)
        Gtk.Button.__init__(self)

        self.binddisp = [
            HiaBind(-1, "bind_0"),
            HiaBind(-1, "bind_1"),
            HiaBind(-1, "bind_2"),
            HiaBind(-1, "crash_to_desktop"),
        ]

        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()

    def setup_widgets (self):
        self.ui.top = Gtk.VBox()
        self.ui.lbl = Gtk.Label(label=self.label)
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

    def update_bindview (self):
        for bi in range(len(self.binddisp)):
            bd = self.binddisp[bi]
            if len(self.ui.bindrows) <= bi:
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
                bb = self.ui.bindbufs[bi]
                bb.delete(bb.get_start_iter(), bb.get_end_iter())
                markup = bd.get_markup_str()
                bb.insert_markup(iter=bb.get_end_iter(), markup=markup, len=-1)
        for bi in range(len(self.binddisp), len(self.ui.bindrows)):
            self.ui.hrules[bi].hide()
            self.ui.bindrows[bi].hid_all()
        return


    def on_bind_changed (self, bindstore, hiasym, newtitle, newcode):
        pass
    def on_group_changed (self, hiaview, newgrp):
        pass
    def on_layer_changed (self, hiaview, newlyr):
        pass
    def on_vislayers_changed (self, hiavia, vislayers):
        pass

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



class HiaCluster (Gtk.Frame, HiaBindable):
    def __init__ (self, view, bindstore, hiasym, label=None):
        HiaBindable.__init__(self, view, bindstore, hiasym, label)
        Gtk.Button.__init__(self)
        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()

    def setup_widgets (self):
        self.ui.labeling = Gtk.HBox()
        self.ui.frame_menu = Gtk.Button("=")
        self.ui.frame_label = Gtk.Label(label=self.label)
        self.ui.labeling.pack_start(self.ui.frame_menu, False, False, 0)
        self.ui.labeling.pack_start(self.ui.frame_label, False, False, 0)
        self.set_label_widget(self.ui.labeling)
        self.ui.top = Gtk.VBox()




