#!/usr/bin/env python3
# Python3 and Gtk3

# Python2-combatibility
from __future__ import print_function, with_statement, unicode_literals

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib, Gio

import ast
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
        self.emit("bind-changed", groupid, layerid, hiasym, cmdtitle, cmdcode)

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
            cooked = BindValue(lambda: False, hiaval, hiacmd)
        else:
            try:
                hiaval.cmdtitle, hiaval.cmdcode  # quack-quack
                cooked = hiaval
            except AttributeError as e:
                cooked = BindValue(lambda: False, hiaval, hiaval)
        self.groups[groupid][layerid][hiasym] = cooked

    __gsignals__ = {
        # (groupid, layerid, hiasym, newtitle, newcode)
        str("bind-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (int, int, str, str, str) ),
        # (ngroups)
        str("ngroups-changed"): (GObject.SIGNAL_RUN_FIRST, None, (int,) ),
        # (groupid, nlayers)
        str("nlayers-changed"): (GObject.SIGNAL_RUN_FIRST, None, (int, int) ),
    }



class BitVector (object):
    def __init__ (self, initval):
        self.count = 8
        self.encoded = 0
        try:
            self.encoded = int(initval)
        except TypeError:
            iter(initval)
            boolvec = [ bool(x) for x in initval ]
            self.count = len(initval)
            for i in range(self.count):
                self.encoded |= (1 << i) if boolvec[i] else 0

    def __iter__ (self):
        for i in range(self.count):
            yield ((self.encoded & (1 << i)) != 0)
    def __getitem__ (self, idx):
        if idx >= self.count:
            raise IndexError("vector index out of range")
        return ( (self.encoded & (1 << idx)) != 0 )
    def __setitem__ (self, idx, val):
        if val:
            self.encoded |= (1 << idx)
        else:
            self.encoded &= ~(1 << idx)
        if idx >= self.count:
            self.count = idx+1
    def __len__ (self):
        return self.count
    def __int__ (self):
        return self.encoded
    def set_bit (self, bitidx):
        self.encoded |= (1 << bitidx)
    def clear_bit (self, bitidx):
        self.encoded &= ~(1 << bitidx)
    def mask_bits (self, bitmask):
        self.encoed &= bitmask
    def __add__ (self, bitidx):
        """set bit"""
        self.set_bit(bitidx)
        return self
    def __sub__ (self, bitidx):
        """clear bit"""
        self.clear_bit(bitidx)
        return self
    def __mul__ (self, bitmask):
        """binary and (mask bits, clear multiple bits)"""
        self.mask_bits(bitmask)
        return self
    def __repr__ (self):
        return "{}(initval=%r)".format(self.__class__.__name__, self.encoded)




################################
# Human-Interface Atom widgets #
################################
# originally "keytops", but some devices don't have keys.
# They are, nonetheless, elements of Human-Computer Interface (atoms).


class HiaView (GObject.Object):
    """Hia-planning data; M in MVC."""
    device_name = GObject.Property(type=str, default="")
    device_details = GObject.Property(type=object)  # instance of LayoutStore, references self.layouts[].
    group = GObject.Property(type=int, default=0)
    layer = GObject.Property(type=int, default=0)
    _vislayers = BitVector(1)
    bindstore = GObject.Property(type=object)   # instance of BindStore.
    layouts = GObject.Property(type=object)     # ListStore(name:str,LayoutStore:object)

    #vislayers = GObject.Property(type=int)      # bit vector.
    @GObject.Property(type=object)
    def vislayers (self):
        return list(self._vislayers)
    @vislayers.setter
    def set_vislayers (self, list_bool):
        vbl = len(list_bool)
        for i in range(vbl):
            self._vislayers.set_bit(i)
        self._vislayers.count = vbl
        self.emit("vislayers-changed", list(self._vislayers))


    def __init__ (self, bindstore=None, layouts=None):
        GObject.Object.__init__(self)
        self.setup_properties()
        self.bindstore = bindstore
        self.layouts = layouts
        self.setup_signals()

    def setup_properties (self):
        self.connect('notify::device-name', self.on_notify_device_name)
        self.connect('notify::device-details', self.on_notify_device_details)
        self.connect('notify::group', self.on_notify_group)
        self.connect('notify::layer', self.on_notify_layer)
        #self.connect('notify::vislayers', self.on_notify_vislayers)
        self.connect('notify::bindstore', self.on_notify_bindstore)
        self.connect('notify::layouts', self.on_notify_layouts)

    def setup_signals (self):
        pass

    def on_notify_device_name (self, inst, param):
        details = None
        if self.device_name is None:
            # Don't bother searching on None.
            self.device_details = details
        else:
            # Search by name.
            for row in self.layouts:
                if row[0] == self.device_name:
                    details = row[1]
                    break
            # Reference by integer offset.
            if details is None:
                # Interpret as integer offset.
                try:
                    details = row[int(self.device_name)]
                except ValueError:
                    pass
            # Settle.
            if details is None:
                self.device_name = None     # Recurse and settle None,None
            else:
                self.device_details = details
    def on_notify_device_details (self, inst, param):
        self.emit("device-changed", self.device_name)
        return
    def on_notify_group (self, inst, param):
        self.emit("group-changed", self.group)
    def on_notify_layer (self, inst, param):
        self.emit("layer-changed", self.layer)
    def on_notify_bindstore (self, inst, param):
        bindstore = self.bindstore
        bindstore.connect("bind-changed", self.on_bindstore_bind_changed)
        bindstore.connect("ngroups-changed", self.on_bindstore_ngroups_changed)
        bindstore.connect("nlayers-changed", self.on_bindstore_nlayers_changed)
        self.emit("bindstore-changed", self.bindstore)
    def on_notify_layouts (self, inst, param):
        def asciisort (mdl, iterA, iterB, *args):
            # No cmp() in python3; workaround.  Still valid in python2.
            valA, valB = mdl[iterA][0], mdl[iterB][0]
            return (valA > valB) - (valA < valB)
        self.layouts.set_sort_func(0, asciisort)
        self.layouts.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.emit("layouts-changed", self.layouts)

    def on_bindstore_bind_changed (self, bindstore, groupid, layerid, hiasym, newtitle, newcode):
        self.emit("bind-changed", groupid, layerid, hiasym, newtitle, newcode)
    def on_bindstore_ngroups_changed (self, bindstore, ngroups):
        self.emit("ngroups-changed", ngroups)
    def on_bindstore_nlayers_changed (self, bindstore, groupid, nlayers):
        # Auto-resize vislayers to new number of layers.
        vislayers = self.vislayers[:]
        if len(vislayers) < nlayers:
            delta = nlayers - len(vislayers)
            vislayers.extend([False] * delta)
        if len(vislayers) > nlayers:
            vislayers = vislayers[:nlayers]
        #self.set_vislayers(vislayers)
        self.vislayers = vislayers
        self.emit("nlayers-changed", groupid, nlayers)

    __gsignals__ = {
        # change in selected device (layout) name
        str("device-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (str,)),
        # change in selected group.
        str("group-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (int,)),
        # change in selected layer.
        str("layer-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (int,)),
        # content of vislayers changed.
        str("vislayers-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (object,)),
        # new instance of BindStore assigned
        str("bindstore-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (object,)),
        # new instance of HiaLayouts assigned
        str("layouts-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (object,)),
        # Relay bindstore.
        # bind-changed(group,layer,hiasym,newtitle,newcode)
        str("bind-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (int, int, str, str, str)),
        str("ngroups-changed"): (GObject.SIGNAL_RUN_FIRST, None, (int,) ),
        str("nlayers-changed"): (GObject.SIGNAL_RUN_FIRST, None, (int, int) ),
    }


class HiaControl (GObject.Object):
    """Controller wrapper to HiaView."""

    view = GObject.Property(type=object)    # Instance of HiaView.
    _registry = None    # map str => Gio.Action (typ. Gio.SimpleAction)
    actions = None      # Instance Gio.SimpleActionGroup

    def __init__ (self, hiaview):
        GObject.Object.__init__(self)
        self.connect("notify::view", self.on_notify_view)
        self.view = hiaview
        self.actions = Gio.SimpleActionGroup()
        self.setup_signals()

    def on_notify_view (self, inst, param):
        pass

    def setup_signals (self):
        def make_closure (action, param_type):
            # Create an action activation closure.
            def f (arg):
                action.activate(GLib.Variant(param_type, arg))
            return f
        for a in dir(self):
            o = getattr(self, a)
            if not callable(o):
                continue
            if not hasattr(o, "__gaction__"):
                continue
            actdesc = o.__gaction__
            name = actdesc['name']
            gparam = actdesc['gparam']
            gstate = actdesc['gstate']
            label = actdesc['label']
            tooltip = actdesc['tooltip']
            action = Gio.SimpleAction(name=name, parameter_type=gparam, state=gstate)
            action.connect('activate', o)
            self.actions.add_action(action)

            # Create an aliased method, with the leading 'act_' removed.
            if gparam:
                param_type = gparam.dup_string()
                closure = make_closure(action, param_type)
                self.__dict__[name] = closure
            else:
                closure = lambda: action.activate()
                self.__dict__[name] = closure
        return

    def HiaSimpleAction (param_type=None, init_state=None, stock_id=None):
        """Class-specific decorator.
Label and tooltip are extracted from function's docstring, which is a plain string as the first (interpreted) line of a function.
The first line, delimited to a newline, is the tooltip's label.
Subsequent lines constitute the action's tooltip text (with Pango markup).
"""
        def wrapper (funcobj):
            # Given a class method, add introspection fields for GAction.
            name = funcobj.__name__
            if name.startswith("act_"):
                name = name[4:]
            else:
                return  # Force error.
            gparam, gstate = None, None
            label, tooltip = None, None
            if funcobj.__doc__:
                # label <- __doc__ until first newline
                # tooltip <- __doc__ after first newline
                label, tooltip = funcobj.__doc__.split("\n", 1)
                # Strip whitespaces from start and end.
                tooltip = tooltip.strip()
            if param_type is not None:
                gparam = GLib.VariantType(str(param_type))
            if init_state is not None:
                fmt, val = init_state
                gstate = GLib.Variant(str(fmt), val)
            funcobj.__gaction__ = dict(
                name=name,
                gparam=gparam,
                gstate=gstate,
                label=label,
                tooltip=tooltip)
            return funcobj
        return wrapper

    @HiaSimpleAction(param_type="s", init_state=None, stock_id=None)
    def act_pick_device (self, action, param):
        """Pick HiaGroup
Specify HiaGroup to make focus"""
        self.view.device_name = param.get_string()
        # TODO: try interpret as int?
        return

    @HiaSimpleAction(param_type="x", init_state=None, stock_id=None)
    def act_pick_group (self, action, param):
        """Pick HiaGroup
Specify HiaGroup to make focus"""
        self.view.group = param.get_int64()
        return

    @HiaSimpleAction(param_type="x", init_state=None, stock_id=None)
    def act_pick_layer (self, action, param):
        """Pick HiaLayer
Specify HiaLayer to make focus."""
        self.view.layer = param.get_int64()
        return

    @HiaSimpleAction(param_type="x", init_state=None, stock_id=None)
    def act_pick_command (self, action, param):
        """Pick HiaCommand by id.
"""
        cmdid = param.get_int64()
        return

    @HiaSimpleAction(param_type="s", init_state=None, stock_id=None)
    def act_pick_sym (self, action, param):
        """Pick HiaSym by name.
"""
        hiasym = param.get_string()
        return

#    @HiaSimpleAction(param_type="x", init_state=None, stock_id=None)
#    def act_push_bind (self, action, param):
#        """Assign bind by command id.
#Assign bind to selected hiasym by command id (from command pack).
#"""
#        return

    @HiaSimpleAction(param_type="(xxsss)", init_state=None, stock_id=None)
    def act_assign_bind_explicit (self, action, param):
        (groupid, layerid, hiasym, cmdtitle, cmdcode) = param
        self.view.bindstore.set_bind(groupid, layerid, hiasym, cmdtitle, cmdcode)
        return

    @HiaSimpleAction(param_type="(sss)", init_state=None, stock_id=None)
    def act_assign_bind (self, action, param):
        (hiasym, cmdtitle, cmdcode) = param
        (groupid, layerid) = (self.view.group, self.view.layer)
        self.assign_bind_explicit((groupid, layerid, hiasym, cmdtitle, cmdcode))
        return

    @HiaSimpleAction("(xxs)")
    def act_erase_bind_explicit (self, action, param):
        (groupid, layerid, hiasym) = param
        self.view.bindstore.set_bind(groupid, layerid, hiasym, "", "")
        return

    @HiaSimpleAction("s")
    def act_erase_bind (self, action, param):
        hiasym = param.get_string()
        (groupid, layerid) = (self.view.group, self.view.layer)
        self.erase_bind_explicit((groupid, layerid, hiasym))
        return

    @HiaSimpleAction("(xxsxxs)")
    def act_exchange_binds_explicit (self, action, param):
        (groupA, layerA, symA, groupB, layerB, symB) = param
        bvA = self.view.bindstore.get_bind(groupA, layerA, symA)
        bvB = self.view.bindstore.get_bind(groupB, layerB, symB)
        cmdtitleA, cmdtitleB, cmdcodeA, cmdcodeB = "", "", "", ""
        if bvA:
            cmdtitleA, cmdcodeA = bvA.cmdtitle, bvA.cmdcode
        if bvB:
            cmdtitleB, cmdcodeB = bvB.cmdtitle, bvB.cmdcode
        self.view.bindstore.set_bind(groupA, layerA, symA, cmdtitleB, cmdcodeB)
        self.view.bindstore.set_bind(groupB, layerB, symB, cmdtitleA, cmdcodeA)
        return

    @HiaSimpleAction("(ss)")
    def act_exchange_binds (self, action, param):
        symA, symB = param
        groupA = groupB = self.view.group
        layerA = layerB = self.view.layer
        self.exchange_binds_explicit((groupA,layerA,symA, groupB,layerB,symB))
        return

    @HiaSimpleAction()
    def act_clear_bindstore (self, action, param):
        return




class HiaDnd (object):
    """Drag-and-Drop opcodes enumeration;
overload the drag-drop 'info' field to as DnD opcodes."""
    class OpcodeEnum (object):
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

    enum = OpcodeEnum
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


class HiaBindable (Gtk.HBox):
    """Bindables store and respond to changes in BindStore.
For HiaTops, affects bind value to display,
For HiaCluster, affects what layout to use.
"""

    def __init__ (self, controller, hiasym, label=None):
        Gtk.HBox.__init__(self)

        self.connect("notify::binddisp", self.on_notify_binddisp)
        self.connect("notify::view", self.on_notify_view)
        self.connect("notify::controller", self.on_notify_controller)

        #self.view = view
        self.controller = controller
        self.hiasym = hiasym
        self.label = str(label if label is not None else self.hiasym)
        class ui: pass   # Plain data.
        self.ui = ui

    binddisp = GObject.Property(type=object)
    hiasym = GObject.Property(type=str, default=None)
    label = GObject.Property(type=str, default="")
    view = GObject.Property(type=object)
    controller = GObject.Property(type=object)

    def get_controller (self): return self.controller
    def set_controller (self, val): self.controller = val
    def on_notify_controller (self, inst, param):
        self.view = self.controller.view

    def get_view (self): return self.view
    def set_view (self, val): self.view = val
    def on_notify_view (self, inst, param):
        val = self.view
        val.connect("bind-changed", self.on_bind_changed)
        val.connect("bindstore-changed", self.on_bindstore_changed)
        val.connect("group-changed", self.on_group_changed)
        val.connect("layer-changed", self.on_layer_changed)
        val.connect("vislayers-changed", self.on_vislayers_changed)

    def get_binddisp (self): return self.binddisp
    def set_bindstore (self, val): self.binddisp = val
    def on_notify_binddisp (self, inst, param):
        self.emit("binddisp-changed", self.binddisp)

    def get_bindstore (self): return self.view.bindstore
    def set_bindstore (self, val): pass
    bindstore = property(get_bindstore, set_bindstore)

    def on_bindstore_changed (self, view, bindstore):
        #bindstore.connect("bind-changed", self.on_bind_changed)
        return
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

    _gsignals = {
        # (hiasym, instance_BindValue)
        str("bind-assigned"): (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
        # (hiasym, hiasym_other)
        str("bind-swapped"): (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
        # (hiasym,)
        str("bind-erased"): (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    __gsignals__ = _gsignals




class HiaTop (HiaBindable):
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
    # Inherited GProperties: binddisp, view, controller, hiasym, label

    def __init__ (self, controller, hiasym, label=None):
        HiaBindable.__init__(self, controller, hiasym, label)

        if self.bindstore:
            self.binddisp = self.get_bindlist()
        else:
            self.binddisp = [ HiaBind(-1, ""), ]
        self.hiasym = str(hiasym)
        self.label = str(label if label is not None else hiasym)

        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()

    def setup_widgets (self):
        """Set up Gtk widgets for keytop."""
        self.set_no_show_all(True)

        self.ui.button = Gtk.Button()
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

        self.ui.button.add(self.ui.top)
        self.add(self.ui.button)

        self.update_widgets()
        self.ui.button.show()
        self.ui.lbl.show()
        self.ui.spacer.show()
        self.ui.top.show()
        self.show()

    def setup_signals (self):
        """Set up widget signals within key top."""
#        self.connect("realize", self.on_realize)
        self.view.connect("group-changed", self.on_group_changed)
        self.view.connect("layer-changed", self.on_layer_changed)
        self.view.connect("vislayers-changed", self.on_vislayers_changed)
        return

    def on_realize (self, w):
        self.binddisp = self.view.bindstore.get_bindlist()
        self.update_widgets()

    def update_widgets (self, binddisp=None):
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
                # track the composited widgets.
                self.ui.bindrows.append(br)
                self.ui.bindbufs.append(bb)
                self.ui.bindviews.append(bv)
                self.ui.layernums.append(lyr)
                # row is [[lyr:Label][bv:TextView]], with a horizontal rule in between eachrow.
                br.pack_start(lyr, False, False, 0)
                br.pack_start(bv, True, True, 0)
                hrule = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                self.ui.hrules.append(hrule)
                self.ui.top.pack_start(hrule, False, False, 0)
                self.ui.top.pack_start(br, False, False, 0)
                # Determine visibility.
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
                # Replace text content.
                bb.delete(bb.get_start_iter(), bb.get_end_iter())
                markup = bd.get_markup_str()
                bb.insert_markup(iter=bb.get_end_iter(), markup=markup, len=-1)
                # vislayers may have shrunk; treat the extras as invisible.
                if (bi < len(self.view.vislayers)) and (self.view.vislayers[bi]):
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

    def on_notify_binddisp (self, inst, param):
        try:
            self.ui.bindrows
        except AttributeError:
            return
        self.update_widgets()
        return

    def on_bind_changed (self, bindstore, groupid, layerid, hiasym, newtitle, newcode):
        bindlist = self.get_bindlist()
        self.binddisp = bindlist
    def on_group_changed (self, hiaview, newgrp):
        bindlist = self.get_bindlist()
        self.binddisp = bindlist
    def on_layer_changed (self, hiaview, newlyr):
        bindlist = self.get_bindlist()
        self.binddisp = bindlist
    def on_vislayers_changed (self, hiavia, vislayers):
        bindlist = self.get_bindlist()
        self.binddisp = bindlist

    def setup_dnd (self):
        """Set up Drag-and-Drop for key top."""
        # DnD source: erase, swap.
        drag_targets = [
            HiaDnd.SWAP.target_same_app(),
            HiaDnd.UNBIND.target_same_app(),
            ]
        drag_actions = Gdk.DragAction.COPY
        drag_buttons = Gdk.ModifierType.BUTTON1_MASK
        self.ui.button.drag_source_set(drag_buttons, drag_targets, drag_actions)
        self.ui.button.connect("drag-data-get", self.on_drag_data_get)
        # DnD destination: bind, swap.
        drop_targets = [
            HiaDnd.SWAP.target_same_app(),
            HiaDnd.BIND.target_same_app(),
            ]
        drop_dests = Gtk.DestDefaults.ALL
        drop_actions = Gdk.DragAction.COPY
        self.ui.button.drag_dest_set(drop_dests, drop_targets, drop_actions)
        self.ui.button.connect("drag-data-received", self.on_drag_data_received)

    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        if info == HiaDnd.UNBIND:
            # dragged to command set.
            seldata.set(seldata.get_target(), 8, str(self.hiasym))
            #self.emit("bind-erased", self.hiasym)
            self.controller.erase_bind(self.hiasym)
        elif info == HiaDnd.SWAP:
            # dragged to HiaTop.
            val = self.hiasym
            seldata.set(seldata.get_target(), 8, str(self.hiasym))
        return False

    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        if info == HiaDnd.BIND:
            seltext = seldata.get_data()
            #self.emit("bind-assigned", self.hiasym, seltext)
            bv = BindValue(lambda: False)
            bv.restore(ast.literal_eval(seltext))
            self.controller.assign_bind((self.hiasym, bv.cmdtitle, bv.cmdcode))
            ctx.finish(True, False, 0)
        elif info == HiaDnd.SWAP:
            othersym = seldata.get_data()
            #self.emit("bind-swapped", self.hiasym, othersym)
            self.controller.exchange_binds((self.hiasym, othersym))
            ctx.finish(True, False, 0)
        return False

#    __gsignals__ = dict(HiaBindable._gsignals)




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


class HiaSelectorSym (Gtk.Grid):
    """Display of a HiaLayout."""

    layout = GObject.Property(type=object)      # instance of LayoutStore
    children = GObject.Property(type=object)    # dict, hiasym => hiatop
    view = GObject.Property(type=object)        # instance of HiaView
    controller = GObject.Property(type=object)  # instance of HiaControl
    _view = None        # Previously known instance.

    def __init__ (self, controller):
        Gtk.Grid.__init__(self)
        self.set_row_homogeneous(True)
        self.set_column_homogeneous(True)
        self.set_row_spacing(1)
        self.set_column_spacing(1)

        self.connect("notify::layout", self.on_notify_layout)
        self.connect("notify::children", self.on_notify_children)
        self.connect("notify::view", self.on_notify_view)
        self.connect("notify::controller", self.on_notify_controller)

        self.controller = controller
        self._view = None
        #self.view = view
        #self.layout = layout
        self.children = {}

    def on_notify_layout (self, inst, param):
        self.rebuild_surface()

    def on_notify_children (self, inst, param):
        return

    def on_notify_controller (self, inst, param):
        self.view = self.controller.view
        return

    def on_notify_view (self, inst, param):
        return

    def on_notify_view_device_details (self, inst, param):
        self.layout = self.view.device_details

    def disown_children (self):
        chlist = self.get_children()
        # TODO: disconnect signals.
        for ch in chlist:
            self.remove(ch)
        self.children = {}

    def make_hiawidget_cluster (self, hiasym, hialabel):
        retval = HiaCluster(self.controller, hiasym, hialabel)
        retval.connect("bind-assigned", self.on_bind_assigned)
        retval.connect("bind-swapped", self.on_bind_swapped)
        retval.connect("bind-erased", self.on_bind_erased)
        retval.show()
        return retval
    def make_hiawidget_key (self, hiasym, hialabel):
        retval = HiaTop(self.controller, hiasym, hialabel)
        retval.connect("bind-assigned", self.on_bind_assigned)
        retval.connect("bind-swapped", self.on_bind_swapped)
        retval.connect("bind-erased", self.on_bind_erased)
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

    def on_bind_assigned (self, w, hiasym, bindvalue):
        self.emit("bind-assigned", hiasym, bindvalue)

    def on_bind_swapped (self, w, hiasym, othersym):
        self.emit("bind-swapped", hiasym, othersym)

    def on_bind_erased (self, w, hiasym):
        self.emit("bind-erased", hiasym)

    __gsignals__ = {
        str("bind-assigned"): (GObject.SIGNAL_RUN_FIRST, None, (str,str)),
        str("bind-swapped"): (GObject.SIGNAL_RUN_FIRST, None, (str,str)),
        str("bind-erased"): (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }


class HiaCluster (HiaBindable):
    """
Represent the jointed cluster types, e.g. joystick, mousepad, button_quad, etc.
"""

    hiachildren = GObject.Property(type=object) # list of nested HiaBindable
    layout_name = GObject.Property(type=str)    # active clustered_layout name

    def __init__ (self, controller, hiasym, label=None):
        HiaBindable.__init__(self, controller, hiasym, label)

        self.connect("notify::hiachildren", self.on_notify_hiachildren)
        self.connect("notify::layout-name", self.on_notify_layout_name)

        self.hiachildren = []
        # Instantiated per HiaCluster instance due to self.hiasym prefix.
        self._clustered_layouts = ClusteredLayouts(self.hiasym)
        # Initial layout.
        bindlist = self.get_bindlist()
        layoutname = bindlist[self.view.layer].cmdtitle
        self.layout_name = layoutname
#        self._layout = self._clustered_layouts[layoutname][1]

        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()

    def setup_widgets (self):
        """Set up Gtk widgets within clustered control."""
        self.ui.frame = Gtk.Frame()
        self.ui.frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.ui.frame_title = Gtk.HBox()
        self.ui.frame_menu = Gtk.Button(label="=")
        self.ui.frame_label = Gtk.Label(label=self.label)
        self.ui.frame_title.pack_start(self.ui.frame_menu, False, False, 0)
        self.ui.frame_title.pack_start(self.ui.frame_label, False, False, 0)
        self.ui.frame.set_label_widget(self.ui.frame_title)

        self.ui.planar = HiaSelectorSym(self.controller)
        try:
            self.ui.planar.layout = self._clustered_layouts[self.layout_name][1]
        except TypeError:
            pass
        self.ui.tabular = None

        self.ui.top = Gtk.Stack()
        self.ui.top.add_named(self.ui.planar, "planar")

        self.ui.frame.add(self.ui.top)
        self.add(self.ui.frame)

        self.show_all()

    def setup_signals (self):
        """Set up widget signas in clustered control."""
        return

    def setup_dnd (self):
        """Set up Drag-and-Drop for clustered control."""
        return

    def on_notify_hiachildren (self, inst, param):
        pass

    def on_notify_layout_name (self, inst, param):
        layoutname = self.layout_name
        try:
            layout = self._clustered_layouts[layoutname][1]
        except TypeError:
            layout = None
        try:
            self.ui.planar
            self.ui.planar.layout = layout
        except AttributeError:
            pass

    def on_bind_changed (self, bindstore, groupid, layerid, hiasym, newtitle, newcode):
        # TODO: check current group and layer.
        if hiasym == self.hiasym:
            self.layout_name = newtitle
        return
    def on_group_changed (self, hiaview, newgrp):
        return
    def on_layer_changed (self, hiaview, newlyr):
        return
    def on_vislayers_changed (self, hiavia, vislayers):
        return

#    __gsignals__ = dict(HiaBindable._gsignals)



#############
# Selectors #
#############

class HiaSelectorRadio (Gtk.Frame):
    """
Row of RadioButton (one-of-many pressed)

Main store is Gtk.ListStore 'namelist'.
Convenience property 'names' to access/mutate with python list-of-str.
"""
    EXPAND_MEMBERS = False
    PADDING = 0

    view = GObject.Property(type=object)        # Instance of HiaView.
    controller = GObject.Property(type=object)  # Instance of HiaControl.
    title = GObject.Property(type=str)
    namelist = GObject.Property(type=object)    # Instance of ListStore.

    def __init__ (self, title, controller, names_iterable):
        Gtk.Frame.__init__(self)

        self.connect("notify::view", self.on_notify_view)
        self.connect("notify::controller", self.on_notify_controller)
        self.connect("notify::title", self.on_notify_title)
        self.connect("notify::namelist", self.on_notify_namelist)

        self.controller = controller
        #self.view = controller.view
        self.title = title
        self.namelist = Gtk.ListStore(str)

        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()
        self.set_names(names_iterable)

    def get_names (self):
        return [ x[0] for x in self.namelist ]
    def set_names (self, names_iterable):
        self.namelist.clear()
        for name in names_iterable:
            self.namelist.append( (name,) )
        self.update_widgets()
    names = property(get_names, set_names)

    def on_notify_view (self, inst, param):
        pass
    def on_notify_controller (self, inst, param):
        self.view = self.controller.view
        pass
    def on_notify_title (self, inst, param):
        self.set_label(self.title)
    def on_notify_namelist (self, inst, param):
        self.namelist.connect("row-changed", self.on_namelist_row_changed)
        pass

    def setup_widgets (self):
        """Set up Gtk widgets within radio-button selector base class."""
        class ui: pass
        self.ui = ui
        #self.update_widgets()
        #self.set_label(self._title)
        self.set_label(self.title)
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
        # Remove current children and add new ones.
        for ch in self.ui.top.get_children():
            # TODO: disconnect signals.
            self.ui.top.remove(ch)
        self.buttons = []
        group = None
        for listrow in self.namelist:
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

    def on_namelist_row_changed (self):
        # rebuild all child widgets on any model changes.
        # TODO: kind of expensive.  Optimize later?
        self.update_widget()

    def on_button_clicked (self, w, ofs=None):
        return


class HiaSelectorGroup (HiaSelectorRadio):
    EXPAND_MEMBERS = False
    PADDING = 16
    def __init__ (self, controller, names_iterable=None):
        if names_iterable is None:
            names_iterable = []
        adjusted = [ "GLOBAL" ] + [ x for x in names_iterable ]
        HiaSelectorRadio.__init__(self, "Mode", controller, adjusted)
    def on_notify_view (self, inst, param):
        self.view.connect("group-changed", self.on_group_changed)
    def on_group_changed (self, view, groupid):
        w = self.buttons[groupid]
        w.set_active(True)
    def on_button_clicked (self, w, ofs=None):
        if w.get_active():
            #self.view.group = int(ofs)
            self.controller.pick_group(int(ofs))
        return


class HiaSelectorLayer (HiaSelectorRadio):
    EXPAND_MEMBERS = True
    def __init__ (self, controller, names_iterable=None):
        if names_iterable is None:
            names_iterable = [ 'base' ]
        HiaSelectorRadio.__init__(self, "Layer", controller, names_iterable)
    def on_notify_view (self, inst, param):
        self.view.connect("layer-changed", self.on_layer_changed)
    def on_layer_changed (self, view, layerid):
        w = self.buttons[layerid]
        w.set_active(True)
    def on_button_clicked (self, w, ofs=None):
        if w.get_active():
            #self.view.layer = int(ofs)
            self.controller.pick_layer(int(ofs))
        return


# Intended to be named HiaSelectorLayout, but spelling too similar to *Layer
class HiaSelectorDevice (Gtk.HBox):
    view = GObject.Property(type=object)        # instance of HiaView.
    controller = GObject.Property(type=object)  # instance of HiaControl.

    def __init__ (self, controller):
        Gtk.HBox.__init__(self)

        self.connect("notify::view", self.on_notify_view)
        self.connect("notify::controller", self.on_notify_controller)

        self.controller = controller
        #self.view = view

        self.setup_widgets()
        self.setup_signals()

    @property
    def model (self):
        return self.view.layouts if self.view else None

    def on_notify_view (self, inst, param):
        # Watch for changes in .device
        #self.view.connect("notify::device-name", self.on_notify_view_device_name)
        self.view.connect("notify::layouts", self.on_notify_view_layouts)
        #self.view.connect("device-changed", self.on_device_changed)
        try:
            self.ui.inp_sel
        except AttributeError:
            return
        self.ui.inp_sel.set_model(self.view.layouts)

    def on_notify_controller (self, inst, param):
        self.view = self.controller.view

    def on_notify_view_layouts (self):
        self.ui.inp_sel.set_model(self.view.layouts)

    def setup_widgets (self):
        """Set up Gtk widgets within device selector."""
        class ui: pass
        self.ui = ui

        self.ui.lbl = Gtk.Label(label="Device:")

        self.ui.render0 = Gtk.CellRendererText()

        inp_dev = Gtk.ComboBox(model=self.model)
        inp_dev.pack_start(self.ui.render0, 0)
        inp_dev.add_attribute(self.ui.render0, 'text', 0)
        inp_dev.set_active(0)
        #self.view.device = ('(none)', None)
        #self.view.device = '(none)'
        #self.view.device_name = '(none)'
        self.controller.pick_device('(none)')
        self.ui.inp_dev = inp_dev

        self.pack_start(self.ui.lbl, False, False, 0)
        self.pack_start(self.ui.inp_dev, False, False, 0)

        self.show_all()

    def setup_signals (self):
        """Set up widget signals within device selector."""
        self.ui.inp_dev.connect("changed", self.on_selection_changed)
        self.view.connect("device-changed", self.on_view_device_changed)

    def on_view_device_changed (self, view, devname):
        try:
            self.ui.inp_dev
        except AttributeError:
            return
        devname = self.view.device_name
        selid = self.ui.inp_dev.get_active()
        if selid < 0:
            return
        selname = self.model[selid][0]
        if devname == selname:
            return
        devofs = -1
        for i in range(len(self.view.layouts)):
            probe = self.view.layouts[i][0]
            if devname == probe:
                devofs = i
        self.ui.inp_dev.set_active(devofs)

    def on_selection_changed (self, w):
        ofs = w.get_active()
        if ofs < 0:
            return
        layoutname = self.model[ofs][0]
        #self.view.device_name = layoutname
        self.controller.pick_device(layoutname)



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
        """Set up Gtk widgets within command selector."""
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
        """Set up Drag-and-Drop for command selector."""
        treeview = self.ui.treeview
        # DnD source: bind.
        drag_targets = [
            HiaDnd.BIND.target_same_app(),
            ]
        drag_actions = Gdk.DragAction.COPY
        drag_buttons = Gdk.ModifierType.BUTTON1_MASK
        treeview.enable_model_drag_source(drag_buttons, drag_targets, drag_actions)
        treeview.connect("drag-data-get", self.on_drag_data_get)
        # DnD destination: unbind.
        drop_targets = [
            HiaDnd.UNBIND.target_same_app(),
            ]
        drop_flags = Gtk.DestDefaults.DROP
        drop_actions = Gdk.DragAction.COPY
        treeview.enable_model_drag_dest(drop_targets, drop_actions)
        treeview.connect("drag-data-received", self.on_drag_data_received)
    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        # is DnD source.
        treesel = w.get_selection()
        mdl, pathsels = treesel.get_selected_rows()
        firstsel = pathsels[0]
        selrow = mdl[firstsel]
        #cmdname = selrow[1]
        bv = BindValue(lambda:False, selrow[2], selrow[1])
        bindvalue = repr(bv.snapshot())
        if info == HiaDnd.BIND:
            # dragged from command set.
            # TODO: encode BindValue
            seldata.set(seldata.get_target(), 8, bindvalue)
        return False
    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        if info == HiaDnd.UNBIND:
            hiasym = seldata.get_data()
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
    cmdpack = GObject.Property(type=object)
    view = GObject.Property(type=object)
    controller = GObject.Property(type=object)

    def __init__ (self, cmdpack=None, controller=None):
        Gtk.HPaned.__init__(self)

        self.setup_properties()

        if cmdpack is None:
            # Fall back to builtin command pack.
            feed = CommandPackFeed.open(None)
            cmdpack = feed.read()
        if controller is None:
            # Build default view.
            bindstore = BindStore()
            layouts = HiaLayouts()
            layouts.build_from_legacy_store()
            view = HiaView(bindstore, layouts)
            controller = HiaControl(view)
        #self.view = view
        self.cmdpack = cmdpack
        self.controller = controller
        self.setup_widgets()
        self.setup_signals()

    def setup_properties (self):
        self.connect("notify::cmdpack", self.on_notify_cmdpack)
        self.connect("notify::view", self.on_notify_view)
        self.connect("notify::controller", self.on_notify_controller)

    def on_notify_cmdpack (self, inst, param):
        # TODO: re-populate HiaSelectorCommand.
        pass

    def on_notify_controller (self, inst, param):
        self.view = self.controller.view

    def on_notify_view (self, inst, param):
        self.view.connect("notify::device-details", self.on_notify_view_device_details)
        try:
            self.ui.sel_device
        except AttributeError:
            return
        for children in [
                # self.ui.sel_cmd,
                self.ui.sel_device,
                self.ui.sel_group,
                self.ui.sel_layer,
                self.ui.sel_bind,
                ]:
            children.view = self.view

    def on_notify_view_device_details (self, inst, param):
        # top-level HiaSelectorSym.
        details = self.view.device_details
        try:
            self.ui.sel_bind.layout = details
        except AttributeError:
            pass

    def get_bindstore (self):
        return self.view.bindstore
    bindstore = property(get_bindstore)

    def setup_widgets (self):
        """Set up Gtk widgets within binds planner."""
        class ui: pass
        self.ui = ui

        self.ui.sel_cmd = HiaSelectorCommand(self.cmdpack)
        self.ui.sel_device = HiaSelectorDevice(self.controller)
        self.ui.sel_group = HiaSelectorGroup(self.controller, None)
        self.ui.sel_layer = HiaSelectorLayer(self.controller, None)
        self.ui.sel_bind = HiaSelectorSym(self.controller)

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
        """Set up signals within binds planner."""
#        self.view.connect("device-changed", self.on_device_changed)
        self.ui.sel_bind.connect("bind-assigned", self.on_bind_assigned)
        self.ui.sel_bind.connect("bind-swapped", self.on_bind_swapped)
        self.ui.sel_bind.connect("bind-erased", self.on_bind_erased)
        #self.ui.sel_cmd.connect("bind-erased", self.on_bind_erased)
        return

    def on_bind_assigned (self, w, hiasym, bindvalue):
        self.emit("bind-assigned", hiasym, bindvalue)
    def on_bind_swapped (self, w, hiasym, othersym):
        self.emit("bind-swapped", hiasym, othersym)
    def on_bind_erased (self, w, hiasym):
        self.emit("bind-erased", hiasym)

    __gsignals__ = {
        # Named device changed.
        str("bind-assigned"): (GObject.SIGNAL_RUN_FIRST, None, (str,str)),
        str("bind-swapped"): (GObject.SIGNAL_RUN_FIRST, None, (str,str)),
        str("bind-erased"): (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }



class HiaWindow (Gtk.Window):
    def __init__ (self):
        Gtk.Window.__init__(self)
        self.set_size_request(640, 480)
        #bindstore = BindStore()
        #layouts = HiaLayouts()
        #layouts.build_from_legacy_store()
        #view = HiaView(bindstore, layouts)
        #feed = CommandPackFeed.open(None)
        #cmdpack = feed.read()
        #planner = HiaPlanner(cmdpack, view, layouts)
        planner = HiaPlanner()
        self.add(planner)
        self.show_all()


if __name__ == "__main__":
    w = HiaWindow()
    Gtk.main()

