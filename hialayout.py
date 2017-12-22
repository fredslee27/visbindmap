#!/usr/bin/env python3
# Python3 and Gtk3

# Python2-combatibility
from __future__ import print_function, with_statement, unicode_literals

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib, Gio

import ast
import os, sys, math
import fcntl
import threading
import shlex
import json

import kbd_desc



PACKAGE="BindPlanner"
VERSION="0.1"
ABOUT = {
    'program-name': "HID Bind Planner",
    'copyright': 'Copyright 2017',
    'version': VERSION,
    'license-type': Gtk.License.GPL_2_0,
}



def _crash ():
    print("*** CRASHING")
    sys.exit(99)




###########
# Logging #
###########

class Logger (object):
    FATAL=0     # Continued operation impossible.
    ERROR=1     # Continued operation yields very wrong result.
    WARN=2      # Operation may continue with unexpected results.
    INFO=3      # Operational within nominal parameters.
    DEBUG=4     # spam.

    _threshold = INFO
    _domain = "none"
    _observers = None

    def get_threshold (self):
        return self._threshold
    def set_threshold (self, val):
        mapped = {
            self.fatal: Logger.FATAL,
            self.error: Logger.ERROR,
            self.warn: Logger.WARN,
            self.info: Logger.INFO,
            self.debug: Logger.DEBUG,
            Logger.fatal: Logger.FATAL,
            Logger.error: Logger.ERROR,
            Logger.warn: Logger.WARN,
            Logger.info: Logger.INFO,
            Logger.debug: Logger.DEBUG,
        }
        if val in mapped:
            self._threshold = mapped[val]
        else:
            self._threshold = val
    threshold = property(get_threshold, set_threshold)

    def __init__ (self, domain, threshold=None):
        self._domain = domain
        if threshold is not None:
            self.threshold = threshold
        self._observers = []

    def add_observer (self, obj):
        self._observers.append(obj)
    def remove_observer (self, obj):
        self._observers.remove(obj)

    def msg (self, severity, *args):
        cooked = " ".join(args)
        if severity <= self.threshold:
            print(cooked)
        for ob in self._observers:
            try:
                ob.logger
            except AttributeError:
                continue
            ob.logger(severity, cooked)
    def fatal (self, *args):
        return self.msg(self.FATAL, *args)
    def error (self, *args):
        return self.msg(self.ERROR, *args)
    def warn (self, *args):
        return self.msg(self.WARN, *args)
    def info (self, *args):
        return self.msg(self.INFO, *args)
    def debug (self, *args):
        return self.msg(self.DEBUG, *args)

logger = Logger("all", Logger.INFO)



####################
# Helper functions #
####################


def pytypes_to_GVariantTypeEncoder (pyval):
    """Convert python type objects into GVariantType description."""
    recurse = pytypes_to_GVariantTypeEncoder
    # literal type object.
    converter = {
        list: (lambda v: "a?"),
        dict: (lambda v: "a{?*}"),
        float: (lambda v: "f"),
        int: (lambda v: "i"),
        bool: (lambda v: "b"),
        bytes: (lambda v: "ay"),
        str: (lambda v: "s"),
        any: (lambda v: "?"),  # technically a builtin function.
        all: (lambda v: "*"),  # technically a builtin function.
    }
    # is an instance of ...
    predicated = [
        (str, lambda v: "s"),
        (tuple, lambda v: "({})".format("".join([ recurse(x) for x in v ]))),
        # list-of-types (first as prototype), or list-of-anything if empty.
        (list, lambda v: "a?" if 0==len(v) else "a{}".format(recurse(v[0]))),
        (dict, lambda v: "a{?*}"),
        # multi-bytes => "ay", else 0-or-1 bytes => "y"
        (bytes, lambda v: "ay" if len(v) > 1 else "y"),
    ]

    if hasattr(pyval,"isalpha"):   # string-like.
        return "s"
    for (typ,pred) in predicated:
        if isinstance(pyval,typ): return pred(pyval)
    if pyval in converter:
        return converter[pyval](pyval)
    pytype = type(pyval)
    if pytype in converter:
        return converter[pytype](pytype)
    # fallback.
    return "s"

def to_GVariant (pyval):
    gformat = pytypes_to_GVariantTypeEncoder(pyval)
    #gparam = GLib.VariantType(gformat)
    if pyval is None:
        retval = GLib.Variant.new_maybe(GLib.VariantType('s'),None)
    elif type(pyval) is tuple and None in pyval:
        # Build it hard-core.
        vlist = [ to_GVariant(x) for x in pyval ]
        retval = GLib.Variant.new_tuple(*vlist)
    else:
        # Build it easy mode.
        retval = GLib.Variant(gformat, pyval)
    #print("built GVariant %r <- %r" % (retval, pyval))
    return retval



def HiaMenu (menu_desc, detail_transformer=None):
    """For use where Gio.Menu is needed (e.g. GtkMenu), loading menu description from various resources:
 * python nestable list+tuples: [  (item1, detailed_action1), None, (item2, detailed_action2), (item2, [ (subitem1, subaction1), (subitem2, subaction2), ... ], ... ]
"""
#    def __init__ (self, menu_desc):
#        Gio.Menu.__init__(self)
#        if type(menu_desc) is list:
#            self.build_menu_from_pylist(self, menu_desc)

    def build_menu_from_pylist (menu, menudesc, xfm=None):
        """Generate Gio.Menu from list+tuple simplified description.
    Format is a list of tuples.
    Each tuple is one of three forms:
     None  -  separator/section
     (str, list) - sub-menu, with recursive list-of-tuples for submenu.
     (str, str)  -  menu item: (label, detailed)
       of detailed:
         str - assign directly to GAction as detailed_action
         (str,GLib.GVariant) - assign as (action_name,target_value)

"""
        if menu is None:
            menu = Gio.Menu()
        menusect = Gio.Menu()
        sectsize = 0
        for itemdesc in menudesc:
            # extend itemdesc to be (over-)padded with None.
            extended = (itemdesc if itemdesc else ()) + (None,)*3
            lbl = extended[0]
            detail = extended[1]
            stock_id = extended[2]
            if lbl is None:
                # separator/section.
                # wrap up old section into a 'section' menuitem.
                menuitem = Gio.MenuItem.new_section(None, section=menusect)
                menu.append_item(menuitem)
                # prepare new section.
                menusect = Gio.Menu()
                sectsize = 0
            elif type(detail) == list:
                # submenu
                submenu = build_menu_from_pylist(None, detail, xfm)
                menuitem = Gio.MenuItem.new_submenu(label=lbl, submenu=submenu)
                menusect.append_item(menuitem)
                sectsize += 1
            else:
                # normal item.
                menuitem = Gio.MenuItem()
                menuitem.set_label(lbl)
                cooked = xfm(detail) if xfm else detail
                if type(cooked) is tuple:
                    (action,target) = cooked
                    menuitem.set_action_and_target_value(action,target)
                else:
                    detailed_action = cooked
                    menuitem.set_detailed_action(detailed_action)
                menusect.append_item(menuitem)
                sectsize += 1
        if sectsize > 0:
            # trailing section, attach at end.
            menuitem = Gio.MenuItem.new_section(None, section=menusect)
            menu.append_item(menuitem)
        return menu

    if type(menu_desc) is list:
        return build_menu_from_pylist(None, menu_desc, detail_transformer)


def AbbrevSignals (sigdescr, **full_desc):
    """Generate __gsignals__ accepted value from abbreviated description of signals that (try to) run first and return None:
[
  (signal_name:str, *signal_param:tuple),
  ...
]

e.g.
[
  ("custom-signal", int, int, int)
]
transforms into
{
    "custom-signal": (GObject.SIGNAL_RUN_FIRST, None, (int, int, int))
}


Also takes an optional dict acceptable for __gsignals__, added onto the return value after converting abbreviated descriptions (i.e. can overwrite abbreviated signals).
"""
    retval = dict()
    for v in sigdescr:
        signal_name = v[0]
        signal_param = tuple(v[1:])
        retval[str(signal_name)] = (GObject.SIGNAL_RUN_FIRST, None, signal_param)
    for k in full_desc:
        retval[k] = full_desc[k]
    return retval




########################
# BindStore data model #
########################

# Associative List - look up by path or key (first column).
# TODO: caching dict
class AListStore (Gtk.ListStore):
    def __init__ (self, *columns):
        Gtk.ListStore.__init__(self, *columns)

    def find (self, k):
        # Exhaustive search.
        finditer = self.get_iter_first()
        while finditer:
            data = Gtk.ListStore.__getitem__(self, finditer)[0]
            if data == k:
                return finditer
            finditer = self.iter_next(finditer)
        return None

    def get (self, k, *args):
        treeiter = self.find(k)
        if treeiter:
            return Gtk.ListStore.__getitem__(self, treeiter)
        try:
            return Gtk.ListStore.get(self, k, *args)
        except TypeError:
            return args

    def __getitem__ (self, k):
        treeiter = self.find(k)
        if treeiter:
            return Gtk.ListStore.__getitem__(self, treeiter)
        # Delegate to super().__getitem__
        return Gtk.ListStore.__getitem__(self, k)

    def __setitem__ (self, k, v):
        listiter = None
        entry = (k,)+v if type(v) is tuple else (k,)+(v,)
        treeiter = self.find(k)
        if treeiter:
            for colnum in range(self.get_n_columns()):
                Gtk.ListStore.set(self, treeiter, colnum, entry[colnum])
        # Delegate to super().__setitem__
        try:
            int(k)
            Gtk.ListStore.__setitem__(self, k, v)
        except (ValueError, TypeError):
            # Not a path; presume key.
            self.append(entry)


# named tuple?
class BindTreeValue (object):
    def __init__ (self, cmdtitle, cmdcode=None):
        if type(cmdtitle) is dict:
            self.restore(cmdtitle)
        else:
            self._cmdtitle = cmdtitle
            self._cmdcode = cmdcode if cmdcode is not None else cmdtitle

    @property
    def cmdtitle (self): return self._cmdtitle
    @cmdtitle.setter
    def set_cmdtitle (self, val): self._cmdtitle = val

    @property
    def cmdcode (self): return self._cmdcode
    @cmdcode.setter
    def set_cmdcode (self, val): self._cmdcode = val

    def restore (self, primitives):
        """Deserialize binds TreeStore."""
        if primitives['__class__'] != self.__class__.__name__:
            raise TypeError("Expected restore from class {}".format(self.__class__.__name__))
        self._cmdtitle = primitives['cmdtitle']
        self._cmdcode = primitives['cmdcode']

    def snapshot (self):
        retval = {
            "__class__": self.__class__.__name__,
            "cmdtitle": self.cmdtitle,
            "cmdcode": self.cmdcode,
        }
        return retval

    def __repr__ (self):
        return "{}(cmdtitle={!r},cmdcode={!r})".format(self.__class__.__name__, self.cmdtitle, self.cmdcode)

BindValue = BindTreeValue



# TODO: layer.bindmap:dict for speeding up hiabind access.
#       or keep layer.children sorted by [1] (hiasym).
class BindTreeStore (Gtk.TreeStore):
    def __init__ (self):
        # generic: (seq_id:int, key:str, label:str, code:str, ephemeral:object)
        # depth=1: (mode_id:int, _:str, mode_label:str, None:str, None:object)
        # depth=2: (layer_id:int, _:str, layer_label:str, layer_bindable:str, bind_dict:object)
        # depth=3: (_:int, hiasym:str, cmdtitle:str, cmdcode:str, None)
# (depth 0 is tree root)
# at depth 1, correspond to Mode selector model
# at depth 2, correspond to Layer selector model
# at depth 3, association list of (hiasym, cmdtitle, cmdcode), mapping of a unique keysym to an arbitrary display string and an output-specific coding value.
        Gtk.TreeStore.__init__(self, int,str,str,str,object)
        self._slicetree_modes = None
        self._slicetree_layers = None
        self.setup_sanity()

    def setup_sanity (self):
        if 0 == len(self):
            self.add_mode("GLOBAL")
        if 0 == self.iter_n_children(self.get_iter_first()):
            self.add_layer("base")

    # nominal maximums; shorts are created on demand, excesses hidden.
    nmodes = GObject.Property(type=int, default=1)
    nlayers = GObject.Property(type=int, default=1)

    @staticmethod
    def iter_depth (treemdl, treeiter):
        retval = 0
        while treeiter:
            treeiter = treemdl.iter_parent(treeiter)
            retval += 1
        return retval

    @staticmethod
    def is_mode_depth (treemdl, treeiter, *args):
        return BindTreeStore.iter_depth(treemdl, treeiter) == 1

    @staticmethod
    def is_layer_depth (treemdl, treeiter, *args):
        return BindTreeStore.iter_depth(treemdl, treeiter) == 2

    @staticmethod
    def is_bind_depth (treemdl, treeiter, *args):
        return BindTreeStore.iter_depth(treemdl, treeiter) == 3

    @GObject.Property(type=object)
    def modes (self):
        """Get TreeModel representing available modes for selection."""
        if not self._slicetree_modes:
            self._slicetree_modes = Gtk.TreeStore.filter_new(self, None)
            self._slicetree_modes.set_visible_func(self.is_mode_depth)
        return self._slicetree_modes
    @GObject.Property(type=object)
    def layers (self):
        """Get TreeModel representing available layers for selection."""
        path_mode = Gtk.TreePath.new_first()
        def filter_layer (treemdl, treeiter, *args):
            parentpath = treemdl.get_path(treemdl.iter_parent(treeiter))
            return parentpath == path_mode
        if not self._slicetree_layers:
            self._slicetree_layers = Gtk.TreeStore.filter_new(self, path_mode)
            self._slicetree_layers.set_visible_func(self.is_layer_depth)
        return self._slicetree_layers

    def get_mode (self, mode_id):
        return self[mode_id]

    def get_layer (self, mode_id, layer_id):
        return self[(mode_id,layer_id)]

    def add_mode (self, mode_name, mode_code=None):
        """Add another mode available for selection."""
        mode_id = len(self)
        rowdata = (mode_id,"", mode_name, mode_code, None)
        iter_mode = self.append( None, rowdata )
        self.nmodes = mode_id+1
        self._slicetree_modes = None  # Invalidate sliced tree.
        self.emit("mode-names-changed", self.modes)
        return mode_id

    def add_layer (self, layer_name=None, layer_code=None):
        """Add another layer available for selection."""
        path_global = Gtk.TreePath.new_first()
        iter_global = self.get_iter(path_global)
        lyr_id = self.iter_n_children(iter_global)
        if layer_name is None:
            layer_name = str(lyr_id)
        bindmap = dict()
        rowdata = (lyr_id,"", layer_name, layer_code, bindmap)
        iter_layer = self.append( iter_global, rowdata )
        self.nlayers = lyr_id+1
        self._slicetree_layers = None  # Invalidate sliced tree.
        # TODO: handle 'row-added' to propagate to all other modes.

        modeiter = self.get_iter_first()
        modeiter = self.iter_next(modeiter)
        while modeiter:
            lyriter = self.append( modeiter, rowdata )
            modeiter = self.iter_next(modeiter)

        #self.emit("nlayers-changed", 0, self.nlayers)
        self.emit("layer-names-changed", self.layers, 0)
        return lyr_id

    def rename_mode (self, mode_id, mode_name, mode_code=None):
        path_target = Gtk.TreePath([mode_id])
        self[path_target][2] = mode_name
        self[path_target][3] = mode_code
        self._slicetree_modes = None  # Invalidate sliced tree.

    def rename_layer (self, layer_id, layer_name, layer_code=None):
        path_global = Gtk.TreePath([0])
        path_target = Gtk.TreePath([0, layer_id])
        self[path_target][2] = layer_name
        self[path_target][3] = layer_code
        self._slicetree_layers = None  # Invalidate sliced tree.

    def del_mode (self, mode_id):
        """Delete mode by id; cannot delete 0."""
        if mode_id == 0:
            raise ValueError("Cannot delete global mode (consider clear_mode()?)")
        path_target = Gtk.TreePath([mode_id])
        iter_target = self.get_iter(path_target)
        self.remove(iter_target)
        self.nmodes -= 1
        self._slicetree_modes = None  # Invalidate sliced tree.

    def del_layer (self, layer_id):
        """Delete layer by id; cannot delete last remaining layer."""
        mode_id = 0
        layers = self.iter_n_children(Gkt.TreePath([mode_id]))
        if len(layers) == 1:
            raise ValueError("Cannot delete final remaining layer (consider clear_layer()?)")
        path_target = Gtk.TreePath([mode_id,layer_id])
        iter_target = self.get_iter(path_target)
        self.remove(iter_target)
        # TODO: handle 'row-deleted' to propagate to all other modes.
        self.nlayers -= 1
        self._slicetree_layers = None  # Invalidate sliced tree.

    def clear_layer (self, mode_id, layer_id):
        """Remove all binds in layer."""
        path_layer = Gtk.TreePath([mode_id,layer_id])
        iter_layer = self.get_iter(path_layer)
        row_layer = self[path_layer]
        # Delete all binds.
        child = self.iter_children(iter_layer)
        if child:
            while self.remove(child):
                pass
        # Invalidate dict.
        row_layer[4].clear()

    def clear_mode (self, mode_id):
        """Erase all binds, remove all non-first layers."""
        path_mode = Gtk.TreePath([mode_id])
        iter_mode = self.get_iter(path_mode)
        row_mode = self[path_mode]
        # Remove non-first layers.
        iter_layer = self.iter_children(iter_mode)
        iter_target = self.iter_next(iter_layer)
        if iter_target:
            while self.remove(iter_target):
                pass
        # Clear first layer.
        self.clear_layer(mode_id, 0)
        self._slicetree_layers = None  # Invalidate sliced tree.
        self.nlayers = 1

    def clear_bindstore (self):
        """Erase everything, reset modes and layers."""
        iter_first = self.get_iter_first()
        if not iter_first:
            self.setup_sanity()
            return
        # Remove non-first modes.
        iter_target = self.iter_next(iter_first)
        if iter_target:
            while self.remove(iter_target):
                pass
        # Clear first mode.
        self.clear_mode(0)
        self._slicetree_modes = None  # Invalidate sliced tree.
        self._slicetree_layers = None  # Invalidate sliced tree.
        self.nmodes = 1
        # Rename first mode and first layer.
        try:
            self[0] = (0,"", "GLOBAL", "GLOBAL", None)
            self[(0,0)] = (0,"", "base", None, None)
        except KeyError:
            pass
        self.emit("mode-names-changed", self.modes)
        self.emit("layer-names-changed", self.layers, 0)
        self.emit("bind-changed", 0, 0, "", "", "")

    def find_mode (self, mode_name):
        """Convert mode name to mode id; returns -1 if no match."""
        modeid = 0
        modes = self.modes
        for modeid in len(modes):
            if modes[moded][2] == mode_name:
                return modeid
        return -1

    def get_bind (self, modeid, layerid, hiasym, default=None):
        """Get bind specified by mode, layer, and keysym,
returns BindValue."""
        try:
            row_mode = self[modeid]
        except IndexError as e:
            if modeid < self.nmodes:
                return default
            else:
                raise e
        try:
            row_layer = self[(modeid,layerid)]
        except IndexError as e:
            if modeid < self.nlayers:
                return default
            else:
                raise e
        row_bind = None
        for probe in row_layer.iterchildren():
            if probe[1] == hiasym:
                row_bind = probe
                break
        if not row_bind:
            #raise KeyError(hiasym)
            return default
        return BindTreeValue(row_bind[2], row_bind[3])

    def put_bind (self, modeid, layerid, hiasym, cmdtitle_or_bindvalue, cmdcode=None):
        """Assign binding to hiasym in specified modeid and layerid."""
        bindvalue = None
        cmdtitle = None
        if isinstance(cmdtitle_or_bindvalue, BindTreeValue):
            bindvalue = cmdtitle_or_bindvalue
            cmdtitle = bindvalue.cmdtitle
            cmdcode = bindvalue.cmdcode
        else:
            cmdtitle = cmdtitle_or_bindvalue
            bindvalue = BindTreeValue(cmdtitle_or_bindvalue, cmdcode)
        row_mode = self[modeid]
        row_layer = self[(modeid,layerid)]
        row_bind = None
        for probe in row_layer.iterchildren():
            if probe[1] == hiasym:
                row_bind = probe
                break
        if cmdtitle is None:
            cmdtitle = ""
        if cmdcode is None:
            cmdcode = ""
        if not row_bind:
            rowdata = (0,hiasym, cmdtitle, cmdcode, None)
            iter_layer = row_layer.iter
            row_bind = self.append( iter_layer, rowdata )
        else:
            row_bind[2] = cmdtitle
            row_bind[3] = cmdcode
        self.emit("bind-changed", modeid, layerid, hiasym, cmdtitle, cmdcode)
        return

    set_bind = put_bind

    def iter_binds (self):
        """Iterate through all binds in store, yielding tuples (mode_id:int, layer_id:int, hiasym:str, cmdtitle:str, cmdcode:str)"""
        modeid = 0
        lyrid = 0
        symid = 0
        for row_mode in self:
            iter_mode = row_mode.iter
            layers = self.iter_children(iter_mode)
            lyrid = 0
            for row_layer in layers:
                iter_layer = row_layer.iter
                binds = self.iter_children(iter_layer)
                symid = 0
                for row_bind in binds:
                    hiasym = row_bind[1]
                    cmdtitle = row_bind[2]
                    cmdcode = row_bind[3]
                    yield (modeid, lyrid, hiasym, cmdtitle, cmdcode)
                    symid += 1
                lyrid += 1
            modeid += 1
        return

    def clear (self):
        Gtk.TreeStore.clear(self)
        self.setup_sanity()

    def serialize_tree (self, treemodel, localrootiter=None):
        retval = []
        rowiter = treemodel.iter_children(localrootiter)
        while rowiter:
            row = treemodel[rowiter]
            subtree = None
            children = row.iterchildren()
            if children:
                subtree = self.serialize_tree(treemodel, rowiter)
            ser_row = tuple(row) + (subtree,)
            retval.append(ser_row)
            rowiter = treemodel.iter_next(rowiter)
        return retval

    def deserialize_tree (self, primitive, treemodel, anchoriter=None):
        for row in primitive:
            rowdata = row[:-1]
            subprime = row[-1]
            iter_add = treemodel.append(anchoriter, rowdata)
            if subprime:
                self.deserialize_tree(subprime, treemodel, iter_add)
        self._slicetree_modes = None
        self._slicetree_layers = None
        return

    def restore (self, primitives):
        """Deserialize binds TreeStore."""
        if primitives['__class__'] != self.__class__.__name__:
            raise TypeError("Expected restore from class {}".format(self.__class__.__name__))
        bindstore = primitives['data']
        Gtk.TreeStore.clear(self)
        self.deserialize_tree(bindstore, self, None)
        self.emit("mode-names-changed", self.modes)
        self.emit("layer-names-changed", self.layers, 0)
        self.emit("bind-changed", 0, 0, "", "", "")
        return

    def snapshot (self):
        """Serialize binds TreeStore."""
        retval = {}
        retval['__class__'] = self.__class__.__name__
        retval['data'] = self.serialize_tree(self, None)
        return retval

    __gsignals__ = AbbrevSignals([
        ("layer-names-changed", object, int),
        ("mode-names-changed", object),
        ("bind-changed", int, int, str, str, str),

        # DEPRECATED
        ("ngroups-changed", int),
        ("nlayers-changed", int, int),
    ])


# alias.
BindStore = BindTreeStore



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
    mode = GObject.Property(type=int, default=0)
    layer = GObject.Property(type=int, default=0)
    nvislayers = GObject.Property(type=int, default=1)  # iter wrapper to _nvislayers bitvector.
    _vislayers = BitVector(1)
    bindstore = GObject.Property(type=object)   # instance of BindStore.
    hialabels = GObject.Property(type=object)   # AListStore(name:str, display_label:str)
    layouts = GObject.Property(type=object)     # ListStore(name:str,LayoutStore:object)
    active_sym = GObject.Property(type=str)     # currently selected HiaTop

    #vislayers = GObject.Property(type=int)      # bit vector.
#    @GObject.Property(type=object)
    @property
    def vislayers (self):
        retval = list(self._vislayers)
        return list(self._vislayers)
    @vislayers.setter
    def vislayers (self, list_bool):
        vbl = len(list_bool)
        for i in range(vbl):
            if list_bool[i]:
                self._vislayers.set_bit(i)
            else:
                self._vislayers.clear_bit(i)
        self._vislayers.count = vbl
        self.emit("vislayers-changed", list(self._vislayers))

    @GObject.Property(type=object)
    def nlayers (self):
        return self.bindstore.nlayers

    @GObject.Property(type=object)
    def nmodes (self):
        return self.bindstore.nmodes



    def __init__ (self, bindstore=None, layouts=None):
        GObject.Object.__init__(self)
        self.setup_properties()
        self.hialabels = AListStore(str,str)
        self.bindstore = bindstore
        self.layouts = layouts
        self.setup_signals()

    def setup_properties (self):
        self.connect('notify::device-name', self.on_notify_device_name)
        self.connect('notify::device-details', self.on_notify_device_details)
        self.connect('notify::mode', self.on_notify_mode)
        self.connect('notify::layer', self.on_notify_layer)
        #self.connect('notify::vislayers', self.on_notify_vislayers)
        self.connect('notify::bindstore', self.on_notify_bindstore)
        self.connect('notify::layouts', self.on_notify_layouts)
        self.connect('notify::nvislayers', self.on_notify_nvislayers)

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
    def on_notify_mode (self, inst, param):
        self.emit("mode-changed", self.mode)
    def on_notify_layer (self, inst, param):
        self.emit("layer-changed", self.layer)
    def on_notify_bindstore (self, inst, param):
        bindstore = self.bindstore
        bindstore.connect("bind-changed", self.on_bindstore_bind_changed)
        bindstore.connect('mode-names-changed', self.on_bindstore_mode_names_changed)
        bindstore.connect('layer-names-changed', self.on_bindstore_layer_names_changed)
        self.emit("bindstore-changed", self.bindstore)
    def on_notify_layouts (self, inst, param):
        if not self.layouts:
            return
        def asciisort (mdl, iterA, iterB, *args):
            # No cmp() in python3; workaround.  Still valid in python2.
            valA, valB = mdl[iterA][0], mdl[iterB][0]
            return (valA > valB) - (valA < valB)
        self.layouts.set_sort_func(0, asciisort)
        self.layouts.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.emit("layouts-changed", self.layouts)
    def on_notify_nvislayers (self, inst, param):
        self.emit("layer-changed", self.layer)

    def on_bindstore_mode_names_changed (self, bindstore, mdl):
        self.emit("mode-names-changed", mdl)
    def on_bindstore_layer_names_changed (self, bindstore, mdl, modeid):
        # Auto-resize vislayers to new number of layers.
        vislayers = self.vislayers[:]
        nlayers = self.nlayers
        if len(vislayers) < nlayers:
            delta = nlayers - len(vislayers)
            vislayers.extend([False] * delta)
        if len(vislayers) > nlayers:
            vislayers = vislayers[:nlayers]
        self.vislayers = vislayers
        self.emit("layer-names-changed", mdl, modeid)
    def on_bindstore_bind_changed (self, bindstore, modeid, layerid, hiasym, newtitle, newcode):
        self.emit("bind-changed", modeid, layerid, hiasym, newtitle, newcode)
#    def on_bindstore_nmodes_changed (self, bindstore, nmodes):
#        self.emit("nmodes-changed", nmodes)

    __gsignals__ = {
        # change in selected device (layout) name
        str("device-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (str,)),
        # change in selected mode.
        str("mode-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (int,)),
        # change in selected layer.
        str("layer-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (int,)),
        # content of vislayers changed.
        str("vislayers-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (object,)),
        # new instance of BindStore assigned
        str("bindstore-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (object,)),
        # new instance of HiaLayouts assigned
        str("layouts-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (object,)),
        # Relay bindstore.
        # bind-changed(mode,layer,hiasym,newtitle,newcode)
        str("bind-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (int, int, str, str, str)),
#        str("nmodes-changed"): (GObject.SIGNAL_RUN_FIRST, None, (int,) ),
#        str("nlayers-changed"): (GObject.SIGNAL_RUN_FIRST, None, (int, int) ),

        str("mode-names-changed"): (GObject.SIGNAL_RUN_FIRST, None, (object,) ),
        str("layer-names-changed"): (GObject.SIGNAL_RUN_FIRST, None, (object, int) ),
    }



# decorator for marking methods automagically tied to Gio.SimpleAction.
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
            if "\n" in funcobj.__doc__:
                label, tooltip = funcobj.__doc__.split("\n", 1)
            else:
                label, tooltip = funcobj.__doc__, ""
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
            tooltip=tooltip,
            stock_id=stock_id)
        return funcobj
    # curry.
    return wrapper


def HiaSimpleActionInstall (inst_or_class):
    """1. decorator on class: automatically create pythonic wrapper methods to GAction activations, for methods decorated with HiaSimpleAction.  Where the GAction handler method is named 'act_FROB_FOOBAR', generates wrapper pythonic method 'FROB_FOOBAR'.  Pythonic in this sense meaning taking arguments in a typical function call manner, instead of wrapped in a one-argument tuple for Gio.Variant conversion.

2. called within bound method (inside setup()) to install into self.actions the Gio.SimpleAction entries derived from bound methods of an object which are GAction handlers, wherein such methods were tagged by the 'HiaSimpleAction' decorator.  So handlers named 'act_FROB_FOOBAR' guide the creation of a GAction named 'FROB_FOOBAR' -- intended to be paired with class-decorator use such that instance.FROB_FOOBAR(..) is a convenience wrapper for invoking action FROB_FOOBAR.activate((...)).
"""
    def Xmake_proxy (action_name, param_type):
        param_type = param_type.replace("m","") if param_type else param_type
        if not param_type:
            # No parameter.
            def f (self):
                action = self.actions.lookup(action_name)
                action.activate()
            return f
        elif param_type.startswith("("):
            # turn arguments into tuple
            def f (self, *args):
                action = self.actions.lookup(action_name)
                v = GLib.Variant(param_type, args)
                action.activate(v)
            return f
        elif param_type:
            # singular argument?
            encparm = param_type.replace('m',"")
            def f (self, arg):
                action = self.actions.lookup(action_name)
                v = GLib.Variant(param_type, arg)
                action.activate(v)
            return f
    def make_proxy (action_name, param_type):
        def f (self, *args):
            action = self.actions.lookup_action(action_name)
            t = action.get_parameter_type()
            if len(args) == 0:
                if t:
                    # Want arguments, given none.
                    # TODO: tuples of None with param_type
                    v = to_GVariant(None)
                    action.activate(v)
                else:
                    action.activate()
            elif len(args) == 1:
                v = to_GVariant(args[0])
                if not v.is_of_type(t):
                    return False
                action.activate(v)
            else:
                v = to_GVariant(tuple(args))
                if not v.is_of_type(t):
                    return False
                action.activate(v)
            return True
        return f

    def decorate_class (classobj):
        for a in dir(classobj):
            if not a.startswith("act_"):
                continue
            o = getattr(classobj, a)
            if not callable(o):
                continue
            if not hasattr(o, "__gaction__"):
                continue
            actdesc = o.__gaction__
            name = actdesc['name']
            gparam = actdesc['gparam']
            param_type = gparam.dup_string() if gparam else None
            proxyname = a[4:]
            proxy = make_proxy(name, param_type)
            setattr(classobj, proxyname, proxy)
        return classobj

    def install_actions (inst):
        for a in dir(inst):
            o = getattr(inst, a)
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
            inst.actions.add_action(action)
        return inst

    if callable(inst_or_class):
        # classes are callable to create instances.
        return decorate_class(inst_or_class)
    else:
        # instances are not callable.
        return install_actions(inst_or_class)
    

@HiaSimpleActionInstall
class HiaControl (GObject.Object):
    """Controller wrapper to HiaView."""

    view = GObject.Property(type=object)    # Instance of HiaView.
    _registry = None    # map str => Gio.Action (typ. Gio.SimpleAction)
    actions = None      # Instance Gio.SimpleActionGroup
    groupwin = None     # Instance GtkWidget

    def __init__ (self, hiaview):
        GObject.Object.__init__(self)
        self.connect("notify::view", self.on_notify_view)
        self.view = hiaview
        self.actions = Gio.SimpleActionGroup()
        self.setup_signals()

    def on_notify_view (self, inst, param):
        pass

    def insert_actions_into_widget (self, parent_widget):
        parent_widget.insert_action_group("hia", self.actions)
        self.groupwin = parent_widget

    def setup_signals (self):
        HiaSimpleActionInstall(self)


    @HiaSimpleAction(param_type="s", init_state=None, stock_id=None)
    def act_pick_device (self, action, param):
        """Pick HiaDevice
Specify HiaDevice to make focus"""
        self.view.device_name = param.get_string()
        # TODO: try interpret as int?
        logger.info("Using device %r" % self.view.device_name)
        return

    @HiaSimpleAction(param_type="i", init_state=None, stock_id=None)
    def act_pick_mode (self, action, param):
        """Pick HiaMode
Specify HiaMode to make focus"""
        self.view.mode = param.get_int32()
        logger.info("Focusing mode %r" % self.view.mode)
        return

    @HiaSimpleAction(param_type="i", init_state=None, stock_id=None)
    def act_pick_layer (self, action, param):
        """Pick HiaLayer
Specify HiaLayer to make focus."""
        self.view.layer = param.get_int32()
        logger.info("Focusing layer %r" % self.view.layer)
        return

    @HiaSimpleAction(param_type="i", init_state=None, stock_id=None)
    def act_pick_command (self, action, param):
        """Pick HiaCommand by id.
"""
        cmdid = param.get_int32()
        return

    @HiaSimpleAction(param_type="s", init_state=None, stock_id=None)
    def act_pick_sym (self, action, param):
        """Pick HiaSym by name.
"""
        hiasym = param.get_string()
        hialabel = self.view.hialabel.get(hiasym, hiasym)[0]
        self.view.active_sym = hiasym
        logger.info("Focusing hiasym {} ({})".format(hialabel, hiasym))
        return

#    @HiaSimpleAction(param_type="i", init_state=None, stock_id=None)
#    def act_push_bind (self, action, param):
#        """Assign bind by command id.
#Assign bind to selected hiasym by command id (from command pack).
#"""
#        return

    @HiaSimpleAction(param_type="(iisss)", init_state=None, stock_id=None)
    def act_assign_bind_explicit (self, action, param):
        (modeid, layerid, hiasym, cmdtitle, cmdcode) = param
        hialabel = self.view.hialabels.get(hiasym, hiasym)[1]
        self.view.bindstore.set_bind(modeid, layerid, hiasym, cmdtitle, cmdcode)
        logger.info("Assigned bind {} ({}) = '{}'".format(hialabel, hiasym, cmdtitle))
        return

    @HiaSimpleAction(param_type="(sss)", init_state=None, stock_id=None)
    def act_assign_bind (self, action, param):
        (hiasym, cmdtitle, cmdcode) = param
        (modeid, layerid) = (self.view.mode, self.view.layer)
        self.assign_bind_explicit(modeid, layerid, hiasym, cmdtitle, cmdcode)
        return

    @HiaSimpleAction("(iis)")
    def act_erase_bind_explicit (self, action, param):
        (modeid, layerid, hiasym) = param
        self.view.bindstore.set_bind(modeid, layerid, hiasym, None, None)
        return

    @HiaSimpleAction("s")
    def act_erase_bind (self, action, param):
        hiasym = param.get_string()
        (modeid, layerid) = (self.view.mode, self.view.layer)
        self.erase_bind_explicit(modeid, layerid, hiasym)
        logger.info("Erased bind %r" % hiasym)
        return

    @HiaSimpleAction("(iisiis)")
    def act_exchange_binds_explicit (self, action, param):
        """Exchange binds between syms, compleat path specifications.
"""
        (modeA, layerA, symA, modeB, layerB, symB) = param
        bvA = self.view.bindstore.get_bind(modeA, layerA, symA)
        bvB = self.view.bindstore.get_bind(modeB, layerB, symB)
        cmdtitleA, cmdtitleB, cmdcodeA, cmdcodeB = "", "", "", ""
        if bvA:
            cmdtitleA, cmdcodeA = bvA.cmdtitle, bvA.cmdcode
        if bvB:
            cmdtitleB, cmdcodeB = bvB.cmdtitle, bvB.cmdcode
        self.view.bindstore.set_bind(modeA, layerA, symA, cmdtitleB, cmdcodeB)
        self.view.bindstore.set_bind(modeB, layerB, symB, cmdtitleA, cmdcodeA)
        logger.info("Swapped binds %r and %r" % (symA, symB))
        return

    @HiaSimpleAction("(ss)")
    def act_exchange_binds (self, action, param):
        """Exchange binds between syms.
"""
        symA, symB = param
        modeA = modeB = self.view.mode
        layerA = layerB = self.view.layer
        self.exchange_binds_explicit(modeA,layerA,symA, modeB,layerB,symB)
        return

    @HiaSimpleAction("(iisiis)")
    def act_exchange_clusters_explicit (self, action, param):
        (modeA, layerA, symA, modeB, layerB, symB) = param
#        bvA = self.view.bindstore.get_bind(modeA, layerA, symA)
#        bvB = self.view.bindstore.get_bind(modeB, layerB, symB)
        #hiaA = (self.groupwin).planner.ui.sel_sym.hiachildren(symA)
        win = self.groupwin
        planner = win.planner
        sel_sym = planner.ui.sel_sym
        bindstore = planner.view.bindstore
        hiaA = sel_sym.hiachildren[symA]
        hiaB = sel_sym.hiachildren[symB]

        def resolve_bind (mode, lyr, sym):
            bv = bindstore.get_bind(mode, lyr, sym)
            if bv: return bv
            bv = bindstore.get_bind(mode, 0, sym)
            if bv: return bv
            bv = bindstore.get_bind(0, lyr, sym)
            if bv: return bv
            bv = bindstore.get_bind(0, 0, sym)
            if bv: return bv

        # temp is snapshot of A
        temp = []
        bvA = resolve_bind(modeA, layerA, symA)
        temp.append( (symA, bvA) )
        for subsymA in hiaA.hiachildren:
            subhiaA = hiaA.hiachildren[subsymA]
            temp.append( (subsymA, bindstore.get_bind(modeA, layerA, subsymA)) )

        # Transfer B into A
        #bvB = bindstore.get_bind(modeB, layerB, symB)
        bvB = resolve_bind(modeB, layerB, symB)
        if bvB:
            cmdtitle, cmdcode = bvB.cmdtitle, bvB.cmdcode
        else:
            cmdtitle, cmdcode = "", ""
        bindstore.set_bind(modeA, layerA, symA, cmdtitle, cmdcode)
        for subsymB in hiaB.hiachildren:
            suffix = subsymB[len(symB):]
            subhiaB = hiaB.hiachildren[subsymB]
            subsymA = "{}{}".format(symA, suffix)
            bvB = bindstore.get_bind(modeB, layerB, subsymB)
            if bvB:
                cmdtitle, cmdcode = bvB.cmdtitle, bvB.cmdcode
            else:
                cmdtitle, cmdcode = "", ""
            bindstore.set_bind(modeA, layerA, subsymA, cmdtitle, cmdcode)

        # Transfer temp into B
        for sym,val in temp:
            suffix = sym[len(symA):]
            subsymB = "{}{}".format(symB, suffix)
            bindstore.set_bind(modeB, layerB, subsymB, val)

        logger.info("Swapped clusters %r and %r" % (symA, symB))
        return

    @HiaSimpleAction()
    def act_clear_bindstore (self, action, param):
        """Clear BindStore.
Erases all bindings.
"""
        self.view.bindstore.clear_bindstore()
        logger.info("Cleared BindStore")
        return

    @HiaSimpleAction("(s*)")  # (sms)
    def act_add_mode (self, action, param):
        (mode_name, mode_code) = param
        self.view.bindstore.add_mode(mode_name, mode_code)

    @HiaSimpleAction("(is*)")  # (tsms)
    def act_rename_mode (self, action, param):
        (modeid, mode_name, mode_code) = param
        self.view.bindstore.rename_mode(modeid, mode_name, mode_code)

    @HiaSimpleAction("i")
    def act_del_mode (self, action, param):
        modeid = param
        self.view.bindstore.del_mode(modeid)

    @HiaSimpleAction("(s*)")  # (sms)
    def act_add_layer (self, action, param):
        (layer_name, layer_code) = param
        self.view.bindstore.add_layer(layer_name, layer_code)

    @HiaSimpleAction("(is*)")  # (tsms)
    def act_rename_layer (self, action, param):
        (layerid, layer_name, layer_code) = param
        self.view.bindstore.rename_layer(layerid, layer_name, layer_code)

    @HiaSimpleAction()
    def act_add_layershifter (self, action, param):
        def _decompose_shifters (layernum):
            shifters = []
            val = layernum
            n = 0
            while val > 0:
                if (val & 1):
                    shifters.append(n)
                val >>= 1
                n += 1
            return shifters
        count = self.view.nlayers
        layernum = count
        for one_more in range(count):
            shifters = _decompose_shifters(layernum)
            shiftertag = " + ".join([ "^{}".format(x+1) for x in shifters ])
            label = "{} ({})".format(layernum, shiftertag)
            code = shiftertag if not "+" in shiftertag else None
            self.add_layer(label, code)
            layernum += 1
        return

    @HiaSimpleAction("i")
    def act_del_layer (self, action, param):
        self.view.bindstore.del_layer(param)

    @HiaSimpleAction("i")
    def act_view_nlayers (self, action, param):
        n_vis = param.get_int32()
        self.view.nvislayers = n_vis

    @HiaSimpleAction()
    def act_readjust_vislayers (self, action, param):
        """Readjust vislayers.
"""
        n_vis = self.view.nvislayers
        a = self.view.layer
        basis = int(a / n_vis) * n_vis
        vislayers = [ False ] * self.view.nlayers
        for i in range(n_vis):
            try:
                vislayers[basis+i] = True
            except IndexError:
                pass
        self.view.vislayers = vislayers



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
    CLUSTER_SWAP = enum("cluster_swap", 4)
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
        # self.cmdcode ...
        if self.cmdcode is not None:
            lbl = GLib.markup_escape_text(str(self.cmdtitle))
            if self.redirects == 0:
                # on point
                dispval = lbl
            elif self.redirects == 1:
                # defer to first layer
                dispval = "<i>{}</i>".format(lbl)
            elif self.redirects == 2:
                # deferred to first mode, current layer.
                dispval = "<b>{}</b>".format(lbl)
            elif self.redirects == 3:
                # deferred to first mode, first layer.
                dispval = "<b><i>{}</i></b>".format(lbl)
            else:
                dispval = "<small><b>{}</b></small>".format(lbl)
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
        self.hiasym = hiasym

        class sig_handlers:
            view = {}
        self._sh = sig_handlers

        self.connect("notify::binddisp", self.on_notify_binddisp)
        self.connect("notify::view", self.on_notify_view)
        self.connect("notify::label", self.on_notify_label)
        self.connect("notify::controller", self.on_notify_controller)

        #self.view = view
        self.controller = controller
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
        val.connect("mode-changed", self.on_mode_changed)
        val.connect("layer-changed", self.on_layer_changed)
        val.connect("vislayers-changed", self.on_vislayers_changed)

    def get_binddisp (self): return self.binddisp
    def set_bindstore (self, val): self.binddisp = val
    def on_notify_binddisp (self, inst, param):
        self.emit("binddisp-changed", self.binddisp)

    def get_label (self): return self.label
    def set_label (self, val): self.label = val
    def on_notify_label (self, inst, param):
        return

    def get_bindstore (self): return self.view.bindstore
    def set_bindstore (self, val): pass
    bindstore = property(get_bindstore, set_bindstore)

    def on_bindstore_changed (self, view, bindstore):
        #bindstore.connect("bind-changed", self.on_bind_changed)
        return
    def on_bind_changed (self, bindstore, hiasym, newtitle, newcode):
        pass
    def on_mode_changed (self, hiaview, newmode):
        pass
    def on_layer_changed (self, hiaview, newlyr):
        pass
    def on_vislayers_changed (self, hiavia, vislayers):
        pass

    def get_bindlist (self):
        """Return list of HiaBind (one per layer)."""
        retval = []
        for lid in range(self.bindstore.nlayers):
            modeid = self.view.mode
            redirections = [
                (modeid, lid),
                (modeid, 0),
                (0, lid),
                (0, 0) ]
            hiabind = None
            redirects = -1
            cmdtitle = ""
            cmdcode = ""
            for ridx in range(len(redirections)):
                (g, l) = redirections[ridx]
                bv = self.bindstore.get_bind(g, l, self.hiasym)
                if bv is not None and bv.cmdtitle:
                    redirects = ridx
                    cmdtitle = bv.cmdtitle
                    cmdcode = bv.cmdcode
                    break
            if hiabind is None:
                hiabind = HiaBind(redirects, cmdtitle, cmdcode)
            retval.append(hiabind)
        return retval

    _gsignals = {
        # (hiasym, instance_BindValue)
        str("bind-assigned"): (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
        # (hiasym, hiasym_other)
        str("bind-swapped"): (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
        # (hiasym,)
        str("bind-erased"): (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        # (hiasym,)
        str("sym-selected"): (GObject.SignalFlags.RUN_FIRST, None, (str,)),
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
  * to Mode Selector = swap bind across mode
* as destination:
  * from CmdPackView = set/copy bind
  * from other HiaTop = swap bind
"""
    # Inherited GProperties: binddisp, view, controller, hiasym, label

    # CSS for styling the binddisp widgets.
    _css1 = Gtk.CssProvider()
    _css1.load_from_data((r"""
.binddisp {
    padding: 0px 0px;
    border: none;
}
.binddisp:insensitive {
    background-color: rgba(0,0,0, 0.05);
}
""").encode())

    def __init__ (self, controller, hiasym, label=None):
        HiaBindable.__init__(self, controller, hiasym, label)

        if self.bindstore:
            self.binddisp = self.get_bindlist()
        else:
            self.binddisp = [ HiaBind(-1, ""), ]
        self.hiasym = str(hiasym)
        lbl = controller.view.hialabels.get(self.hiasym, self.hiasym)[1]
        self.label = str(lbl)

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
        self.ui.button.connect("clicked", self.on_button_clicked)
        self.view.connect("mode-changed", self.on_mode_changed)
        self.view.connect("layer-changed", self.on_layer_changed)
        self.view.connect("vislayers-changed", self.on_vislayers_changed)
        return

    def on_realize (self, w):
        self.binddisp = self.view.bindstore.get_bindlist()
        self.update_widgets()

    def make_binddispline_textview (self):
        bb, bv = Gtk.TextBuffer(), Gtk.TextView()
        bb.insert_markup(iter=bb.get_end_iter(), markup=markup, len=-1)
        bv.set_buffer(bb)
        bv.set_editable(False)
        return bb, bv

    def make_binddispline_label (self):
        bb, bv = None, Gtk.Label()
        bv.set_halign(Gtk.Align.FILL)   # to fill the rest of box with bg.
        bv.set_xalign(0.0)              # to force glyphs start at far left.

        stylectx = bv.get_style_context()
        stylectx.add_class("entry")
        stylectx.add_class("binddisp")
        stylectx.add_provider(self._css1, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        return bb, bv

    def update_binddispline_textview (self, bb, bv, markup):
        bb.delete(bb.get_start_iter(), bb.get_end_iter())
        bb.insert_markup(iter=bb.get_end_iter(), markup=markup, len=-1)

    def update_binddispline_label (self, bb, bv, markup):
        bv.set_markup(markup)

    def update_widgets (self, binddisp=None):
        if binddisp is None:
            binddisp = self.binddisp
        for bi in range(len(binddisp)):
            bd = binddisp[bi]
            if len(self.ui.bindrows) <= bi:
                # Add another row.

                markup = bd.get_markup_str()
                #bb, bv = self.make_binddispline_textview()
                bb, bv = self.make_binddispline_label()
                bv.set_markup(markup)

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
                    hrule.hide()
                    br.hide()
            else:
                # Update extant row.
                hr = self.ui.hrules[bi]
                br = self.ui.bindrows[bi]
                bv = self.ui.bindviews[bi]
                bb = self.ui.bindbufs[bi]
                lyr = self.ui.layernums[bi]
                # Replace text content.
                markup = bd.get_markup_str()
                # self.update_binddispline_textview(bb, bv, markup)
                self.update_binddispline_label(bb, bv, markup)

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
            bv = self.ui.bindviews[bi]
            if bi == self.view.layer:
                bv.get_style_context().set_state(Gtk.StateFlags.NORMAL)
                bv.get_style_context().add_class("entry")
            else:
                bv.get_style_context().set_state(Gtk.StateFlags.INSENSITIVE)
                bv.get_style_context().remove_class("entry")
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

    def on_bind_changed (self, bindstore, modeid, layerid, hiasym, newtitle, newcode):
        bindlist = self.get_bindlist()
        self.binddisp = bindlist
    def on_mode_changed (self, hiaview, newmode):
        bindlist = self.get_bindlist()
        self.binddisp = bindlist
    def on_layer_changed (self, hiaview, newlyr):
        bindlist = self.get_bindlist()
        self.binddisp = bindlist
    def on_vislayers_changed (self, hiavia, vislayers):
        bindlist = self.get_bindlist()
        self.binddisp = bindlist
    def on_button_clicked (self, w, *args):
        self.emit("sym-selected", self.hiasym)

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
        # Drag from HiaTop
        if info == HiaDnd.UNBIND:
            # dragged to command set.
            seldata.set(seldata.get_target(), 8, self.hiasym.encode())
            #self.emit("bind-erased", self.hiasym)
            self.controller.erase_bind(self.hiasym)
        elif info == HiaDnd.SWAP:
            # dragged to HiaTop.
            val = self.hiasym
            seldata.set(seldata.get_target(), 8, self.hiasym.encode())
        return False

    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        # Drop on HiaTop
        if info == HiaDnd.BIND:
            seltext = seldata.get_data().decode()
            if seltext:
                bv = BindValue(ast.literal_eval(seltext))
                self.controller.assign_bind(self.hiasym, bv.cmdtitle, bv.cmdcode)
            else:
                self.controller.erase_bind(self.hiasym)
            ctx.finish(True, False, 0)
        elif info == HiaDnd.SWAP:
            othersym = seldata.get_data().decode()
            #self.emit("bind-swapped", self.hiasym, othersym)
            self.controller.exchange_binds(self.hiasym, othersym)
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

    def make_menu (self):
        # Return a Gio.Menu describing a menu choosing an available layout.
        def detail_transformer(layoutname):
            if not "." in layoutname:
                actname = "app.assign_bind"
                hiasym = self.symprefix
                cmdtitle = layoutname
                cmdcode = layoutname
                gvalue = GLib.Variant("(sss)", (hiasym, cmdtitle, cmdcode))
            else:
                (res, actname, gvalue) = Gio.Action.parse_detailed_name(layoutname)
            return (actname, gvalue)
        MENU_DESC = [
            # (displayed_label, bind_value)  =>  menuitem set layout
            # || (displayed_label, [ nested_MENUDESC ] )  =>  submenu
            ("_None", "app.erase_bind('%s')" % self.symprefix),
            ("_Empty", "Empty"),
            ("_Single Button", "OneButton"),
            ("Scroll _Wheel", "ScrollWheel"),
            ("_D-Pad", "DirectionPad"),
            ("Button _Quad", "ButtonQuad"),
            ("Tr_ackpad", "MousePad"),
            ("_Mouse Region", "MouseRegion"),
            ("_Joystick", "Joystick"),
            ("_Gyro", "GyroTilt"),
            ("_Touch Menu", [
                ("_2 items", "TouchMenu02"),
                ("_4 items", "TouchMenu04"),
                ("_7 items", "TouchMenu07"),
                ("_9 items", "TouchMenu09"),
                ("1_2 items", "TouchMenu12"),
                ("1_3 items", "TouchMenu13"),
                ("1_6 items", "TouchMenu16"),
                ]),
            ("_Radial Menu", [
                ("_01..09 items", [
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
                ("_10.._19 items", [
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
                ("_20 items", "RadialMenu20"),
                ]),
            ]
        menu = HiaMenu(MENU_DESC, detail_transformer)
        return menu

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
            ("01", 0, 0), ("02", 1, 0),
            ]
        )
        layout4 = self.make_gridded_layoutstore("TouchMenu04",
          6, 6,
          [
            ("01", 0, 0), ("02", 1, 0),
            ("03", 0, 1), ("04", 1, 1),
            ]
        )
        layout9 = self.make_gridded_layoutstore("TouchMenu09",
          4, 4,
          [
            ("01", 0, 0), ("02", 1, 0), ("03", 2, 0),
            ("04", 0, 1), ("05", 1, 1), ("06", 2, 1),
            ("07", 0, 2), ("08", 1, 2), ("09", 2, 2),
            ]
        )
        layout12 = self.make_gridded_layoutstore("TouchMenu12",
          3, 4,
          [
            ("01", 0, 0), ("02", 1, 0), ("03", 2, 0), ("04", 3, 0),
            ("05", 0, 1), ("06", 1, 1), ("07", 2, 1), ("08", 3, 1),
            ("09", 0, 2), ("10", 1, 2), ("11", 2, 2), ("12", 3, 2),
            ]
        )
        layout16 = self.make_gridded_layoutstore("TouchMenu16",
          3, 3,
          [
            ("01", 0, 0), ("02", 1, 0), ("03", 2, 0), ("04", 3, 0),
            ("05", 0, 1), ("06", 1, 1), ("07", 2, 1), ("08", 3, 1),
            ("09", 0, 2), ("10", 1, 2), ("11", 2, 2), ("12", 3, 2),
            ("13", 0, 3), ("14", 1, 3), ("15", 2, 3), ("16", 3, 3),
            ]
        )

        def SYM (suffix):
            """Helper function for manually-defined layouts - generate extended hiasym."""
            return "{}{:02d}".format(self.symprefix, suffix)

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
            return "{}{:02d}".format(self.symprefix, suffix)
        def radialize (n, r=6):
            for step in range(n):
                angle = step * 2*math.pi / float(n)
                theta = - math.pi / 2. + angle
                x = r + (float(r) * math.cos(theta)) - .5
                y = r + (float(r) * math.sin(theta)) + .5
                hiasym = SYM(step+1)
                yield (hiasym, hiasym, "key", x, y, 1, 1)
        # Generate RadialMenu01 through RadialMenu20
        for variant in range(1,21):
            layout = self.make_layoutstore("{}{:02d}".format("RadialMenu", variant))
            for entry in radialize(variant, r=6):
                layout.append(None, entry)
            self.append( (layout.name, layout) )
        return


class HiaSelectorSym (Gtk.Stack):
    """Display of a HiaLayout."""

    layout = GObject.Property(type=object)      # instance of LayoutStore
    hiachildren = GObject.Property(type=object) # dict, hiasym => hiatop
    view = GObject.Property(type=object)        # instance of HiaView
    controller = GObject.Property(type=object)  # instance of HiaControl
    _view = None        # Previously known instance.
    listmodel = GObject.Property(type=object)   # TreeStore (internal use)

    def __init__ (self, controller):
        Gtk.Stack.__init__(self)
        class ui: pass
        self.ui = ui

        self.connect("notify::layout", self.on_notify_layout)
        self.connect("notify::hiachildren", self.on_notify_hiachildren)
        self.connect("notify::view", self.on_notify_view)
        self.connect("notify::controller", self.on_notify_controller)

        self.controller = controller
        self._view = None
        self.hiachildren = {}
        self.listmodel = Gtk.TreeStore(str,)    # placeholder model.

        self.setup_widgets()

    def setup_widgets (self):
        self.ui.grid = Gtk.Grid()
        self.ui.grid.set_row_homogeneous(True)
        self.ui.grid.set_column_homogeneous(True)
        self.ui.grid.set_row_spacing(1)
        self.ui.grid.set_column_spacing(1)

        self.ui.treecells = []
        self.ui.treecols = []
        self.ui.listview = Gtk.TreeView()

        self.ui.grid_top = Gtk.VBox()
        #self.ui.add_named(self.ui.grid_top, "planar")
        #self.ui.add_named(self.ui.listview, "tabular")

        #self.ui.portal_grid = Gtk.ScrolledWindow()
        #self.ui.portal_grid.add(self.ui.grid)
        self.ui.portal_grid = Gtk.VBox()
        self.ui.portal_grid.pack_start(self.ui.grid, False, False, 0)
        self.add_named(self.ui.portal_grid, "planar")

        self.ui.portal_list = Gtk.ScrolledWindow()
        self.ui.portal_list.add(self.ui.listview)
        self.add_named(self.ui.portal_list, "tabular")

        self.rebuild_listview()

        self.show_all()

    def on_notify_layout (self, inst, param):
        self.rebuild_surface()
        self.rebuild_listmodel()
        self.rebuild_listview()

    def on_notify_hiachildren (self, inst, param):
        return

    def on_notify_controller (self, inst, param):
        self.view = self.controller.view
        return

    def on_notify_view (self, inst, param):
        self.view.connect("vislayers-changed", self.on_view_vislayers_changed)
        self.view.connect("layer-changed", self.on_view_layer_changed)
        self.view.connect("mode-changed", self.on_view_mode_changed)
        self.set_vislayers(self.view.vislayers)
        self.set_layer(self.view.layer)
        return

    def on_notify_view_device_details (self, inst, param):
        self.layout = self.view.device_details

    def disown_children (self):
        grid = self.ui.grid
        chlist = grid.get_children()
        # TODO: disconnect signals.
        for ch in chlist:
            grid.remove(ch)
        self.hiachildren = {}

    def make_hiawidget_cluster (self, hiasym, hialabel):
        self.controller.view.hialabels[hiasym] = hialabel
        retval = HiaCluster(self.controller, hiasym, hialabel)
        retval.connect("bind-assigned", self.on_bind_assigned)
        retval.connect("bind-swapped", self.on_bind_swapped)
        retval.connect("bind-erased", self.on_bind_erased)
        retval.connect("sym-selected", self.on_sym_selected)
        retval.show()
        return retval
    def make_hiawidget_key (self, hiasym, hialabel):
        self.controller.view.hialabels[hiasym] = hialabel
        retval = HiaTop(self.controller, hiasym, hialabel)
        retval.connect("bind-assigned", self.on_bind_assigned)
        retval.connect("bind-swapped", self.on_bind_swapped)
        retval.connect("bind-erased", self.on_bind_erased)
        retval.connect("sym-selected", self.on_sym_selected)
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
        grid = self.ui.grid
        for rowentry in self.layout:
            intent = (str,str,str, int,int,int,int)
            #(hiasym, lbl, prototype, x, y, w, h) = rowentry
            (hiasym, lbl, prototype, x, y, w, h) = [ intended(rawval) for (intended,rawval) in zip(intent,rowentry) ]
            hw = self.make_hiawidget(hiasym, lbl, prototype)
            self.hiachildren[hiasym] = hw
            if hw:
                grid.attach(hw, x, y, w, h)
            if y > max_row:
                max_row = y
            bv = self.view.bindstore.get_bind(self.view.mode, self.view.layer, hiasym)
            if bv:
                hw.cluster_type = bv
        for y in range(max_row):
            if not grid.get_child_at(0, y):
                filler = Gtk.HBox()
                filler.show()
                grid.attach(filler, 0, y, 1, 1)
        grid.show()

        return

    def rebuild_listmodel (self):
        # Re-make listmodel on nlayer change.
        #print("rebuild listmodel, hiachildren %r" % (self.hiachildren.keys(),))
        nlayers = self.controller.view.nlayers
        coldesc = (str,) + (str,)*nlayers
        listmodel = Gtk.TreeStore(*coldesc)
        chsyms = sorted(self.hiachildren.keys())
        for hiasym in chsyms:
            hia = self.hiachildren[hiasym]
            bindlist = [ b.get_markup_str() for b in hia.get_bindlist() ]
            rowdata = (hiasym,) + tuple(bindlist)
            listmodel.append(None, rowdata)
            #print("adding row %r" % (rowdata,))
        self.listmodel = listmodel
        self.rebuild_listview()
        return

    def rebuild_listview (self):
        treeview = self.ui.listview
        for treecol in self.ui.treecols:
            treeview.remove_column(treecol)

        cell0 = Gtk.CellRendererText()
        col0 = Gtk.TreeViewColumn("sym", cell0, markup=0)
        treeview.append_column(col0)

        treecells = [cell0]
        treecols = [col0]

        nlayers = self.controller.view.nlayers
        for i in range(nlayers):
            cellI = Gtk.CellRendererText()
            if i:
                #titleI = "bind{}".format(i)
                titleI = "[{}]".format(i)
            else:
                titleI = "[base]"
#            colI = Gtk.TreeViewColumn(titleI, cellI, markup=i+1)
            colI = Gtk.TreeViewColumn()
            colI.set_expand(True)
            headerI = Gtk.Label(label=titleI)
            headerI.show()
            colI.set_widget(headerI)
            colI.pack_start(cellI, True)
            colI.add_attribute(cellI, "markup", i+1)
            treeview.append_column(colI)
            treecells.append(cellI)
            treecols.append(colI)

        self.ui.treecells = treecells
        self.ui.treecols = treecols
        treeview.set_model(self.listmodel)

        # set up drag-and-drop for list view.
        drag_targets = [
            HiaDnd.SWAP.target_same_app(),
            HiaDnd.UNBIND.target_same_app(),
            ]
        drag_actions = Gdk.DragAction.COPY
        drag_buttons = Gdk.ModifierType.BUTTON1_MASK
        treeview.enable_model_drag_source(drag_buttons, drag_targets, drag_actions)
        treeview.connect("drag-data-get", self.on_row_drag_data_get)
        # DnD destination: bind, swap.
        drop_targets = [
            HiaDnd.SWAP.target_same_app(),
            HiaDnd.BIND.target_same_app(),
            ]
        drop_dests = Gtk.DestDefaults.ALL
        drop_actions = Gdk.DragAction.COPY
        treeview.enable_model_drag_dest(drop_targets, drop_actions)
        treeview.connect("drag-data-received", self.on_row_drag_data_received)

        treeview.get_style_context().add_provider(HiaTop._css1, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        treeview.get_style_context().add_class("binddisp")

        self.set_layer(self.view.layer)
        self.set_vislayers(self.view.vislayers)

        self.ui.listview = treeview
        return

    def on_bind_assigned (self, w, hiasym, bindvalue):
        self.emit("bind-assigned", hiasym, bindvalue)

    def on_bind_swapped (self, w, hiasym, othersym):
        self.emit("bind-swapped", hiasym, othersym)

    def on_bind_erased (self, w, hiasym):
        self.emit("bind-erased", hiasym)

    def on_sym_selected (self, w, hiasym):
        self.emit("sym-selected", hiasym)

    def on_bind_changed (self, bindstore, mode, lyr, hiasym, newtitle, newcode):
        bindpath = None
        for bindrow in self.listmodel:
            if bindrow[0] == hiasym:
                #bindrow[lyr+1] = newtitle
                hia = self.hiachildren[hiasym]
                bindlist = [ b.get_markup_str() for b in hia.get_bindlist() ]
                for i in range(len(bindlist)):
                    bindrow[i+1] = bindlist[i]
        self.ui.listview.queue_draw()

    def set_mode (self, layer_id):
        self.rebuild_listmodel()
        self.rebuild_listview()
        return
    def set_layer (self, layer_id):
        try:
            self.ui.treecells
        except AttributeError:
            return
        listview = self.ui.listview
        for colid in range(1, len(self.ui.treecols)):
            lid = colid-1
            # TODO: dim unselected layers' headers.
            if lid == layer_id:
                self.ui.treecells[colid].props.cell_background_rgba = Gdk.RGBA(0,0,0,0)
            else:
                self.ui.treecells[colid].props.cell_background_rgba = Gdk.RGBA(0,0,0,0.10)
        self.ui.listview.queue_draw()
        return
    def set_vislayers (self, vislayers):
        # TODO: this gets called multiple times per invocation from parent, but only one reacts visually... figure out where multiplicity comes from.
        if not self.listmodel:
            return
        try:
            self.ui.treecols
        except AttributeError:
            return
        m = self.listmodel.get_n_columns()
        v = (tuple(vislayers) if vislayers else ()) + (False,)*m
        for lid in range(len(vislayers)):
            try:
                self.ui.treecols[1+lid].set_visible(v[lid])
            except IndexError:
                pass
        return

    def on_view_mode_changed (self, view, mode_id):
        self.set_mode(mode_id)
    def on_view_layer_changed (self, view, layer_id):
        self.set_layer(layer_id)
    def on_view_vislayers_changed (self, view, vislayers):
        self.set_vislayers(vislayers)

    def on_row_drag_data_get (self, w, ctx, seldata, info, time, *args):
        # Drag from HiaListRow (equiv to HiaTop).
        selinfo = self.ui.listview.get_selection()
        treemdl, selrows = selinfo.get_selected_rows()
        if info == HiaDnd.UNBIND:
            # dragged to command set.
            if len(selrows) != 1:
                return
            selpath = selrows[0]
            selrow = treemdl[selpath]
            hiasym = selrow[0]
            seldata.set(seldata.get_target(), 8, hiasym.encode())
            self.controller.erase_bind(hiasym)
        elif info == HiaDnd.SWAP:
            # dragged to HiaTop or HiaListRow.
            if len(selrows) != 1: return
            val = hiasym = treemdl[selrows[0]][0]
            seldata.set(seldata.get_target(), 8, hiasym.encode())
        return False

    def on_row_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        # Drop on HiaListRow
        listview = self.ui.listview
        if info == HiaDnd.BIND:
            # from command set, or that which provides a drop-bind.
            seltext = seldata.get_data().decode()
            bv = BindValue(ast.literal_eval(seltext))
            listinfo = listview.get_dest_row_at_pos(x,y)
            if not listinfo:
                return
            (selpath, selpos) = listinfo
            hiasym = self.listmodel[selpath][0]
            self.controller.assign_bind(hiasym, bv.cmdtitle, bv.cmdcode)
            ctx.finish(True, False, 0)
        elif info == HiaDnd.SWAP:
            # from HiaTop or HiaListRow.
            othersym = seldata.get_data().decode()
            (selpath, selpos) = listview.get_dest_row_at_pos(x,y)
            hiasym = self.listmodel[selpath][0]
            self.controller.exchange_binds(hiasym, othersym)
            ctx.finish(True, False, 0)
        return False

    __gsignals__ = {
        str("sym-selected"): (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        str("bind-assigned"): (GObject.SIGNAL_RUN_FIRST, None, (str,str)),
        str("bind-swapped"): (GObject.SIGNAL_RUN_FIRST, None, (str,str)),
        str("bind-erased"): (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }


class HiaCluster (HiaBindable):
    """
Represent the jointed cluster types, e.g. joystick, mousepad, button_quad, etc.
"""

    cluster_type = GObject.Property(type=object)    # BindValue

    def __init__ (self, controller, hiasym, label=None):
        HiaBindable.__init__(self, controller, hiasym, label)

        self.connect("notify::cluster-type", self.on_notify_cluster_type)

        # Instantiated per HiaCluster instance due to self.hiasym prefix.
        self._clustered_layouts = ClusteredLayouts(self.hiasym)

        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()

        self.update_cluster_type()

    @GObject.Property(type=object)
    def hiachildren (self):
        try:
            return self.ui.sel_sym.hiachildren
        except AttributeError:
            return None

    def get_extended_label_markup (self):
        cluster_type = self.cluster_type
        cmdtitle = cluster_type.cmdtitle if cluster_type else None
        if cmdtitle:
            markup = self.cluster_type.get_markup_str()
        else:
            markup = GLib.markup_escape_text("?")
        lbl = self.controller.view.hialabels.get(self.hiasym, self.hiasym)[1]
        hialabel = str(lbl)
        return " {} &lt;{}&gt;".format(hialabel, markup)

    def setup_widgets (self):
        """Set up Gtk widgets within clustered control."""
        self.ui.mnu_layout = self._clustered_layouts.make_menu()

        name_act_listview = "view_bindlist__%s" % self.hiasym
        self.ui.act_listview = Gio.SimpleAction.new_stateful(name=name_act_listview, parameter_type=None, state=to_GVariant(False))
        self.controller.actions.add_action(self.ui.act_listview)
        self.ui.mnu_layout.append("_List View", "app.{}".format(name_act_listview))
        self.ui.act_listview.connect("change-state", self.on_act_listview)

        self.ui.frame = Gtk.Frame()
        self.ui.frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.ui.frame_title = Gtk.HBox()
        self.ui.frame_arranger = Gtk.MenuButton()
        self.ui.frame_arranger.set_use_popover(False)  # TODO: GSettings.
        self.ui.frame_arranger.set_menu_model(self.ui.mnu_layout)
        label = self.get_extended_label_markup()
        self.ui.frame_label = Gtk.Label()
        self.ui.frame_label.set_markup(label)
        self.ui.frame_title.pack_start(self.ui.frame_arranger, False, False, 0)
        self.ui.frame_title.pack_start(self.ui.frame_label, False, False, 0)
        self.ui.frame.set_label_widget(self.ui.frame_title)

        self.ui.sel_sym = HiaSelectorSym(self.controller)

        self.add(self.ui.frame)
        self.ui.frame.add(self.ui.sel_sym)

        self.show_all()

    def setup_signals (self):
        """Set up widget signas in clustered control."""
        return

    def setup_dnd (self):
        """Set up Drag-and-Drop for clustered control."""
        # DnD source: cluster_swap
        drag_targets = [
            HiaDnd.CLUSTER_SWAP.target_same_app(),
            ]
        drag_actions = Gdk.DragAction.COPY
        drag_buttons = Gdk.ModifierType.BUTTON1_MASK
        w = self.ui.frame_arranger
        w.drag_source_set(drag_buttons, drag_targets, drag_actions)
        w.connect("drag-data-get", self.on_drag_data_get)
        # DnD destination: cluster_swap
        drop_targets = [
            HiaDnd.CLUSTER_SWAP.target_same_app(),
            ]
        drop_dests = Gtk.DestDefaults.ALL
        drop_actions = Gdk.DragAction.COPY
        w.drag_dest_set(drop_dests, drop_targets, drop_actions)
        w.connect("drag-data-received", self.on_drag_data_received)

    def update_cluster_type (self):
        self.cluster_type = self.get_bindlist()[self.view.layer]
        #  cascades notify_cluster_type()
        sel_sym = None
        layout_name = self.cluster_type.cmdtitle
        try:
            layout = self._clustered_layouts[layout_name][1]
        except TypeError:
            layout = None
        try:
            self.ui.sel_sym
            self.ui.sel_sym.layout = layout
        except AttributeError:
            pass

    def on_notify_cluster_type (self, inst, param):
        try:
            self.ui.frame_label
        except AttributeError:
            return
        markup = self.get_extended_label_markup()
        self.ui.frame_label.set_markup(markup)

    def on_bind_changed (self, bindstore, modeid, layerid, hiasym, newtitle, newcode):
        # TODO: check current mode and layer.
        if hiasym == self.hiasym:
            self.update_cluster_type()
        if hiasym in self.hiachildren:
            self.ui.sel_sym.on_bind_changed(bindstore, modeid, layerid, hiasym, newtitle, newcode)
        return
    def on_mode_changed (self, hiaview, newmode):
        self.update_cluster_type()
        return
    def on_layer_changed (self, hiaview, newlyr):
        self.update_cluster_type()
        return
    def on_vislayers_changed (self, hiaview, vislayers):
        return

    def on_frame_switch (self, w, *args):
        cur = self.ui.sel_sym.get_visible_child_name()
        if cur == "planar":
            target = "tabular"
        else:
            target = "planar"
        self.ui.sel_sym.set_visible_child_name(target)

    def on_act_listview (self, inst, param):
        v = param.get_boolean()
        inst.set_state(param)
        target = "tabular" if v else "planar"
        self.ui.sel_sym.set_visible_child_name(target)

    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        if info == HiaDnd.CLUSTER_SWAP:
            """Swap cluster layout and bindings."""
            hiasym = self.hiasym
            seldata.set(seldata.get_target(), 8, hiasym)
        return

    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        if info == HiaDnd.CLUSTER_SWAP:
            # Swap across layers.
            othersym = str(seldata.get_data().decode())
            bindstore = self.view.bindstore
            mode = self.view.mode
            layer = self.view.layer
            self.controller.exchange_clusters_explicit(mode,layer,self.hiasym, mode,layer,othersym)
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

    def __init__ (self, title, controller):
        Gtk.Frame.__init__(self)

        self.connect("notify::view", self.on_notify_view)
        self.connect("notify::controller", self.on_notify_controller)
        self.connect("notify::title", self.on_notify_title)

        self.controller = controller
        #self.view = controller.view
        self.title = title

        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()

    def get_names (self):
        return [ x[0] for x in self.get_axislist ]
    names = property(get_names)

    def on_notify_view (self, inst, param):
        pass
    def on_notify_controller (self, inst, param):
        self.view = self.controller.view
        pass
    def on_notify_title (self, inst, param):
        self.set_label(self.title)

    def get_axislist (self):
        # overrride in subclass.
        # returns list of tuple(str,str); typ. TreeStore(str,str)
        return []
    def get_axes (self):
        return self.controller.view.axes
    axes = property(get_axes)

    def setup_widgets (self):
        """Set up Gtk widgets within radio-button selector base class."""
        class ui: pass
        self.ui = ui
        #self.set_label(self._title)
        self.set_label(self.title)
        self.ui.top = Gtk.HBox()

        self.update_widgets()

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
        oldval = self.get_active_radio()
        for ch in self.ui.top.get_children():
            # TODO: disconnect signals.
            self.ui.top.remove(ch)
        self.buttons = []
        self.labels = []
        mode = None
        namelist = self.get_axislist()
        btn_id = 0

        # Set up DnD for radio buttons.
        # buttons with 'cmdcode' field are draggable.
        drag_targets = [
            HiaDnd.BIND.target_same_app(),
            ]
        drag_actions = Gdk.DragAction.COPY
        drag_buttons = Gdk.ModifierType.BUTTON1_MASK

        # all button are destinations.
        drop_targets = [
            HiaDnd.SWAP.target_same_app(),
            HiaDnd.CLUSTER_SWAP.target_same_app(),
            ]
        drop_dests = Gtk.DestDefaults.ALL
        drop_actions = Gdk.DragAction.COPY

        for listrow in namelist:
            #name = listrow[0]
            name = listrow[2]
            code = listrow[3]
            b = Gtk.RadioButton(group=mode)
            b.cmdcode = code
            d = Gtk.Label()
            d.set_markup(name)
            b.add(d)
            if not self.buttons:
                mode = b
            if btn_id == oldval:
                # Restore old value.
                b.set_active(True)

            # DnD
            if b.cmdcode:
                # Buttons with cmdcode are drag sources.
                b.drag_source_set(drag_buttons, drag_targets, drag_actions)
                b.connect("drag-data-get", self.on_drag_data_get, b.cmdcode)
            # all buttons are drag destinations.
            b.drag_dest_set(drop_dests, drop_targets, drop_actions)
            b.connect("drag-data-received", self.on_drag_data_received)

            b.connect("clicked", self.on_button_clicked, btn_id)
            b.show_all()
            self.buttons.append(b)
            self.labels.append(d)
            self.ui.top.pack_start(b, self.EXPAND_MEMBERS, True, self.PADDING)
            btn_id += 1
        return

    def on_button_clicked (self, w, ofs=None):
        return
    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        return
    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        return

    def get_active_radio (self): # override
        return 0


class HiaSelectorMode (HiaSelectorRadio):
    EXPAND_MEMBERS = False
    PADDING = 16
    def __init__ (self, controller):
        HiaSelectorRadio.__init__(self, "Mode", controller)
    def get_active_radio (self): return self.view.mode
    def get_axislist (self):
        submodel = self.view.bindstore.modes
        return submodel
    def on_notify_view (self, inst, param):
        self.view.connect("mode-changed", self.on_mode_changed)
        self.view.connect("mode-names-changed", self.on_mode_names_changed)
        try:
            self.update_widget()
        except AttributeError:
            pass
    def on_mode_changed (self, view, modeid):
        w = self.buttons[modeid]
        w.set_active(True)
    def on_mode_names_changed (self, view, mdl):
        self.update_widgets()
    def on_button_clicked (self, w, ofs=None):
        if w.get_active():
            self.controller.pick_mode(int(ofs))
        return

    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        # dropped on mode.
        btn = w
        nth = self.buttons.index(btn)
        if nth < 0:
            # Invalid destination.
            return
        dstmode = nth
        if info == HiaDnd.SWAP:
            # Swap across modes.
            hiasym = str(seldata.get_data().decode())
            srcmode = self.controller.view.mode
            dstmode = nth
            layer = self.controller.view.layer
            self.controller.exchange_binds_explicit(srcmode, layer, hiasym,  dstmode, layer, hiasym)
            return
        elif info == HiaDnd.CLUSTER_SWAP:
            hiasym = str(seldata.get_data().decode())
            srcmode = self.controller.view.mode
            dstmode = nth
            layer = self.controller.view.layer
            self.controller.exchange_clusters_explicit(srcmode, layer, hiasym,  dstmode, layer, hiasym)
            return


class HiaSelectorLayer (HiaSelectorRadio):
    EXPAND_MEMBERS = True
    def __init__ (self, controller):
        HiaSelectorRadio.__init__(self, "Layer", controller)
    def get_active_radio (self): return self.view.layer
    def get_axislist (self):
        submodel = self.view.bindstore.layers
        return submodel
    def setup_signals (self):
        #self.view.bindstore.connect("nlayers-changed", self.on_bindstore_nlayers_changed)
        pass
    def on_notify_view (self, inst, param):
        self.view.connect("layer-changed", self.on_layer_changed)
        self.view.connect("layer-names-changed", self.on_layer_names_changed)
        try:
            self.update_widget()
        except AttributeError:
            pass
    def on_layer_changed (self, view, layerid):
        w = self.buttons[layerid]
        w.set_active(True)
    def on_button_clicked (self, w, ofs=None):
        if w.get_active():
            #self.view.layer = int(ofs)
            self.controller.pick_layer(int(ofs))
        return
    def on_layer_names_changed (self, view, mdl, modeid):
        # TODO: check modeid?
        self.update_widgets()

    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
        # drag from layer to sym.
        btn = w
        bindval = str(args[0])
        if info == HiaDnd.BIND:
            bv = BindValue(bindval, bindval)
            bindvalue = repr(bv.snapshot()).encode()
            seldata.set(seldata.get_target(), 8, bindvalue)
        return

    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        # dropped on layer.
        btn = w
        nth = self.buttons.index(btn)
        if nth < 0:
            # Invalid destination.
            return
        if info == HiaDnd.SWAP:
            # Swap across layers.
            hiasym = str(seldata.get_data().decode())
            srclayer = self.controller.view.layer
            dstlayer = nth
            mode = self.controller.view.mode
            self.controller.exchange_binds_explicit(mode, srclayer, hiasym,  mode, dstlayer, hiasym)
            return
        elif info == HiaDnd.CLUSTER_SWAP:
            hiasym = str(seldata.get_data().decode())
            srclayer = self.controller.view.layer
            dstlayer = nth
            mode = self.controller.view.mode
            self.controller.exchange_clusters_explicit(mode, srclayer, hiasym,  mode, dstlayer, hiasym)


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
        #self.controller.pick_device('(none)')
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
        self.modelist = []          # List of names for modes.
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
#  CommandPackFeed.open("file:///path/to/command/pack.csv")
#  => searches REGISRY for an instance where is_acceptable(uri) returns true
#  => instantiates that subclass with the specified URI
#  => invoke read() to return an instance of CommandPackStore.
#  
# Implementation case:
#  Subclass CommandPackFeed
#  Decorate with @CommandPackFeed.register to automagically register with base class/factory method.
#  Implement function @staticmethod is_acceptable(uri), returns bool.
#    May examine contents to determine validity (but should close handle before returning).
#  Implement read(), guided with self._path, to create and return instance of CommandPackStore.
#
# Classes that return True for is_acceptable() will have their open() invoked.
# If open() fails, factory function moves on to next factory class.
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
        #return (uri is None)
        return (uri == "")

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


import sqlite3

@CommandPackFeed.register
class CommandPackFeed_sqlite3 (CommandPackFeed):
    @staticmethod
    def is_acceptable (uri):
        # URI of None yields the hard-coded command pack feed.
        if not uri:
            return False
        try:
            conn = sqlite3.connect(uri)
            curs = conn.cursor()
            rows = curs.execute("SELECT COUNT(*) FROM cmd;")
        except sqlite3.DatabaseError:
            return False
        if not conn:
            return False
        conn.close()
        return True

    def read (self):
        dbname = self._path
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()

        # Pack name: derived from dbname, then override with table content.
        packname = os.path.basename(dbname)
        try:
            rows = cursor.execute('''SELECT packname FROM packname LIMIT 1;''')
            row = rows.fetchone()
            packname = row[0]
        except sqlite3.OperationalError:
            pass

        cmdpack = CommandPackStore(packname)
        cmdpack.uri = self._path

        # Get modes.
        try:
            rows = cursor.execute('''SELECT name FROM modes ORDER BY id;''')
            modelist = [ row[0] for row in rows ]
        except sqlite3.OperationalError:
            rows = []
            modelist = []
        cmdpack.modelist = modelist

        # Get groupings.
        rows = cursor.execute('''SELECT grp FROM cmd GROUP BY grp ORDER BY id;''')
        grpnames = [ row[0] for row in rows ]

        grploc = {}
        grptree = {}
        for grpname in grpnames:
            grpiter = None
            grpnode = grptree
            parts = grpname.split('/')
            prefix = []
            for k in parts:
                prefix.append(k)
                ancestorkey = '/'.join(prefix)
                if not k in grpnode:
                    # Create ancestor.
                    grpiter = cmdpack.append(grpiter, (-1, "", k, ""))
                    grploc[ancestorkey] = grpiter
                    grpnode[k] = dict()
                else:
                    # Lookup ancestor.
                    grpiter = grploc[ancestorkey]
                # Keep drilling.
                grpnode = grpnode[k]

        # Iterate all rows.
        stmt = '''SELECT id,layer,grp,cmd,label,hint FROM cmd;'''
        try:
            rows = cursor.execute(stmt)
        except sqlite3.OperationalError:
            rows = []
        for row in rows:
            cmdid, lyr, grp, cmd, lbl, hint = row
            if lbl is None:
                lbl = cmd
            datum = (cmdid, cmd, lbl, hint)
            # Find group, attach to group.
            grpiter = grploc.get(grp, None)
            cmdpack.append(grpiter, datum)

        conn.close()

        return cmdpack




class HiaSelectorCommand (Gtk.VBox):
    """View of the command pack.

static method 'make_model()' for generating a suitable TreeStore expected by this widget.
"""
    model = GObject.Property(type=object)       # CommandPackStore

    # Expected to rarely change, so model signals are ignored and instead set_model triggers refreshing view.
    def __init__ (self, mdl):
        Gtk.VBox.__init__(self)
        self.connect("notify::model", self.on_notify_model)

        if mdl:
            self.model = mdl

        self.setup_widgets()
        self.setup_signals()
        self.setup_dnd()

    def on_notify_model (self, inst, param):
        if self.model:
            #self.ui.treeview.set_model(self.model)
            self.update_widgets()
        self.emit("model-changed", self.model)
        return

    def setup_widgets (self):
        """Set up Gtk widgets within command selector."""
        class ui: pass
        self.ui = ui

        self.ui.sclwin = Gtk.ScrolledWindow()

        # TreeView
        self.ui.treeview = Gtk.TreeView(model=self.model)
        self.ui.treeview.set_search_column(2)
        # TreeViewColumns
        self.ui.treecols = []
        self.ui.treecelltxt = Gtk.CellRendererText()
        colname = "command"
        if self.model:
            colname = self.model.packname
        col0 = Gtk.TreeViewColumn(colname, self.ui.treecelltxt, text=2)
        self.ui.treecols.append(col0)
        for col in self.ui.treecols:
            self.ui.treeview.append_column(col0)

        self.ui.custombox = Gtk.VBox()
        self.ui.customtitle_line = Gtk.HBox()
        self.ui.customtitle_label = Gtk.Label(label="Title: ")
        self.ui.customtitle_inp = Gtk.Entry()
        self.ui.customtitle_inp.set_width_chars(10)
        self.ui.customtitle_line.pack_start(self.ui.customtitle_label, False, False, 0)
        self.ui.customtitle_line.pack_start(self.ui.customtitle_inp, True, True, 0)
        self.ui.customcode_line = Gtk.HBox()
        self.ui.customcode_label = Gtk.Label(label="Code: ")
        self.ui.customcode_inp = Gtk.Entry()
        self.ui.customcode_inp.set_width_chars(8)
        self.ui.customcode_line.pack_start(self.ui.customcode_label, False, False, 0)
        self.ui.customcode_line.pack_start(self.ui.customcode_inp, True, True, 0)
        self.ui.customadd_line = Gtk.HBox()
        self.ui.customadd_btn = Gtk.Button(label="Add Custom")
        self.ui.customadd_line.pack_start(self.ui.customadd_btn, False, False, 0)
        self.ui.custombox.pack_start(self.ui.customtitle_line, False, False, 0)
        self.ui.custombox.pack_start(self.ui.customcode_line, False, False, 0)
        self.ui.custombox.pack_start(self.ui.customadd_line, False, False, 0)

        self.ui.sclwin.add(self.ui.treeview)
        #self.add(self.ui.sclwin)
        self.pack_start(self.ui.sclwin, True, True, 0)
        self.pack_start(Gtk.HSeparator(), False, False, 0)
        self.pack_start(self.ui.custombox, False, False, 0)
        self.show_all()

        self.props.has_tooltip = True
        self.knowwhat = "cmdpackview"

    def update_widgets (self):
        try:
            self.ui
        except AttributeError:
            return
        self.ui.treeview.set_model(self.model)
        packname = self.model.packname if self.model else None
        if packname:
            self.ui.treecols[0].set_title(packname)
        else:
            self.ui.treecols[0].set_title("command")
        return

    def setup_signals (self):
        self.connect("realize", self.on_realize)
        return

    def on_realize (self, w, *args):
        toplevel = self.get_toplevel()
        actions = toplevel.get_action_group("app")
        if actions:
            act0 = actions.lookup_action("load_commandpack")
            act0.connect("activate", self.on_act_load_commandpack)
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
        # TreeView is DnD source.
        treesel = w.get_selection()
        mdl, pathsels = treesel.get_selected_rows()
        firstsel = pathsels[0]
        selrow = mdl[firstsel]
        #cmdname = selrow[1]
        if selrow[0] == 0:
            bindvalue = ""
        else:
            bv = BindValue(selrow[2], selrow[1])
            bindvalue = repr(bv.snapshot())
        if info == HiaDnd.BIND:
            # dragged from command set.
            seldata.set(seldata.get_target(), 8, bindvalue.encode())
        return False
    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
        # TreeView is DnD destination.
        if info == HiaDnd.UNBIND:
            hiasym = seldata.get_data()
        return False

    def on_act_load_commandpack (self, action, paramval):
        if not paramval.is_of_type(GLib.VariantType('s')):
            return
        uri = paramval.get_string()
        try:
            feed = CommandPackFeed.open(uri)
        except NameError:
            logger.warn("Could not load command pack %r" % uri)
            return
        pack = feed.read()
        if uri:
            logger.info("Loaded command pack %r" % uri)
        self.model = pack
        return

    @staticmethod
    def make_model ():
        # Data tuples = ( cmd_id_number, cmd_name, display_text, tooltip_text )
        store = CommandPackStore()
        store.append(None, (0, "", "(unbind)", None))
        return store

    __gsignals__ = AbbrevSignals([
        ('model-changed', object),
        ])




###################
# Aggregated View #
###################

# Put together the command picker, the device selector, the group selector, the layer selector, the bind selector.
#
# +------------------------------
# | CmdPick | [DeviceSelector  v]
# |         |  ( ) Mode0   ( ) Mode1  ...
# |         |  ( ) Layer0  ( ) Layer1 ...
# |         | { HiaSelectorSym
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
            #feed = CommandPackFeed.open(None)
            #cmdpack = feed.read()
            cmdpack = CommandPackStore()
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
        self.controller.view.connect("device-changed", self.on_device_changed)
        self.controller.view.connect("layer-changed", self.on_layer_changed)
        try:
            self.ui.sel_device
        except AttributeError:
            return
        for children in [
                # self.ui.sel_cmd,
                self.ui.sel_device,
                self.ui.sel_mode,
                self.ui.sel_layer,
                self.ui.sel_sym,
                ]:
            children.controller = self.controller

    def on_notify_view (self, inst, param):
        #self.view.connect("notify::device-details", self.on_notify_view_device_details)
        pass

    def on_notify_view_device_details (self, inst, param):
        # top-level HiaSelectorSym.
        details = self.view.device_details
        try:
            self.ui.sel_sym.layout = details
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
        self.ui.sel_mode = HiaSelectorMode(self.controller)
        self.ui.sel_layer = HiaSelectorLayer(self.controller)
        self.ui.sel_sym = HiaSelectorSym(self.controller)

        self.ui.lhs = Gtk.VBox()
        self.ui.lhs.pack_start(self.ui.sel_cmd, True, True, 0)

        self.ui.rhs = Gtk.VBox()
        self.ui.rhs.pack_start(self.ui.sel_device, False, False, 0)
        self.ui.rhs.pack_start(self.ui.sel_mode, False, False, 0)
        self.ui.rhs.pack_start(self.ui.sel_layer, False, False, 0)
        self.ui.rhs.pack_start(self.ui.sel_sym, False, True, 0)

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
        self.ui.sel_sym.connect("bind-assigned", self.on_bind_assigned)
        self.ui.sel_sym.connect("bind-swapped", self.on_bind_swapped)
        self.ui.sel_sym.connect("bind-erased", self.on_bind_erased)
        self.ui.sel_sym.connect("sym-selected", self.on_sym_selected)
        return

    def on_device_changed (self, view, devname):
        # Top-level HiaSelectorSym.
        try:
            self.ui.sel_sym
        except AttributeError:
            return
        details = self.controller.view.device_details
        self.ui.sel_sym.layout = details

    def on_layer_changed (self, view, layerid):
        # Top-level layer change -- update vislayers.
        #vislayers = [False] * view.bindstore.nlayers
        #vislayers[layerid] = True
        #self.controller.view.vislayers = vislayers
        self.controller.readjust_vislayers()

    def on_bind_assigned (self, w, hiasym, bindvalue):
        self.emit("bind-assigned", hiasym, bindvalue)
    def on_bind_swapped (self, w, hiasym, othersym):
        self.emit("bind-swapped", hiasym, othersym)
    def on_bind_erased (self, w, hiasym):
        self.emit("bind-erased", hiasym)
    def on_sym_selected (self, w, hiasym):
        self.controller.pick_sym(hiasym)
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
        planner.controller.insert_actions_into_widget(self)
        #planner.controller.view.bindstore.nlayers = 4
        #planner.controller.view.bindstore.ngroups = 3
#        planner.controller.use_group_names([('Menu',''),('Game','')])
#        planner.controller.use_layer_names([('base',''), ('1',''), ('2',''), ('3','')])
        self.add(planner)
        self.show_all()
        planner.controller.view_nlayers(2)



##################
# GtkApplication #
##################


@HiaSimpleActionInstall
class AppControl (HiaControl):

    # Inherited properties: actions, hiaview

    def __init__ (self, hiaview):
        HiaControl.__init__(self, hiaview)

    def insert_actions_into_widget (self, parent_widget):
        parent_widget.insert_action_group("app", self.actions)
        self.groupwin = parent_widget

    @HiaSimpleAction()
    def act_ragequit (self, inst, param):
        # Hooked into GtkApplication elsewhere.
        pass

    @HiaSimpleAction("b")
    def act_quit (self, inst, param):
        # TODO: check dirtiness to present confirmation dialog.
        pass


    @HiaSimpleAction()
    def act_new_file (self, inst, param):
        self.view.bindstore.clear_bindstore()
        self.pick_device(self.view.layouts[0][0])
        self.pick_mode(0)
        self.pick_layer(0)
        self.add_layershifter()
        self.add_layershifter()
        self.add_layershifter()
        logger.info("New file")
        return

    @HiaSimpleAction("s")
    def act_open_file (self, inst, param):
        pathname = param.get_string()
        f = open(pathname, "rt")
        whole = json.load(f)
        f.close()
        if whole['version'] == 3:
            bs = whole.get('bindstore', None)
            if not bs:
                raise ValueError("invalid file format")
            bs['__class__'] = BindTreeStore.__name__
            self.view.bindstore.restore(bs)
            selectors = whole.get('selectors', None)
            no_dev = (self.view.device_details is None) or (len(self.view.device_details) == 0)
            if selectors and no_dev:
                dn = selectors.get("device", None)
                gn = selectors.get("mode", None)
                ln = selectors.get("layer", None)
                if dn is not None: self.pick_device(dn)
                if gn is not None: self.pick_mode(gn)
                if ln is not None: self.pick_layer(ln)
        logger.info("Opened file %r" % (pathname,))
        return

    @HiaSimpleAction("s")
    def act_save_file (self, inst, param):
        pathname = param.get_string()
        whole = {}

        whole['version'] = 3
        # mode names
        whole['modes'] = [ row[2] for row in self.view.bindstore.modes ]
        # layer names
        whole['layers'] = [ row[2] for row in self.view.bindstore.layers ]

        whole['selectors'] = {
            'device': self.view.device_name,
            'mode': self.view.mode,
            'layer': self.view.layer,
        }

        whole['bindstore'] = self.view.bindstore.snapshot()
        del whole['bindstore']['__class__']

        f = open(pathname, "wt")
        json.dump(whole, f, indent=4)
        f.close()
        logger.info("Saved file %r" % (pathname,))
        return

    @HiaSimpleAction()
    def act_ask_file_new (self, inst, param):
        # Check for dirtiness, then present confirmation dialog or continue straight to clear_file.

        dirty = True

        if dirty:
            dlg = Gtk.MessageDialog(transient_for=self.groupwin, title="Erase working board", flags=Gtk.DialogFlags.MODAL, type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.YES_NO, text="Detected unsaved changes.\nForce erasing the working data you see?")
            response = dlg.run()
            dlg.hide()
            if response == Gtk.ResponseType.YES:
                self.new_file()
            dlg.destroy()
        return

    @HiaSimpleAction()
    def act_ask_file_open (self, inst, param):
        dlg = None
        try:
            dlg = self.groupwin.dlg_open
        finally:
            if dlg is None:
                return
        response = dlg.run()
        dlg.hide()
        if response == Gtk.ResponseType.ACCEPT:
            pathname = dlg.get_filename()
            self.open_file(pathname)

    @HiaSimpleAction()
    def act_ask_file_save (self, inst, param):
        # determine dirtiness, then invoke ask_file_saveas or continue straight to save_file.
        return

    @HiaSimpleAction()
    def act_ask_file_saveas (self, inst, param):
        """Save file by name chooser.
"""
        dlg = None
        try:
            dlg = self.groupwin.dlg_save
        finally:
            if dlg is None:
                return
        response = dlg.run()
        dlg.hide()
        if response == Gtk.ResponseType.ACCEPT:
            pathname = dlg.get_filename()
            self.save_file(pathname)

    @HiaSimpleAction()
    def act_ask_commandpack (self, inst, param):
        try:
            dlg = self.groupwin.dlg_cmdpack
        except AttributeError:
            return
        if not dlg:
            return
        response = dlg.run()
        dlg.hide()
        if response == Gtk.ResponseType.ACCEPT:
            pathname = dlg.get_filename()
            uri = "file://{}".format(pathname)
            self.load_commandpack(pathname)

    @HiaSimpleAction("s")
    def act_load_commandpack (self, inst, param):
        # also run in parallel: HiaSelectorCommand.on_act_load_commandpack
        pass

    @HiaSimpleAction()
    def act_edit_copy (self, inst, param):
        pass

    @HiaSimpleAction()
    def act_edit_cut (self, inst, param):
        pass

    @HiaSimpleAction()
    def act_edit_paste (self, inst, param):
        pass

    @HiaSimpleAction()
    def act_preferences (self, inst, param):
        pass

    @HiaSimpleAction("i")
    def act_view_layers (self, inst, param):
        m = param.get_int32()
        self.view.nvislayers = m
        logger.info("Viewing %d layers at a time" % m)

    @HiaSimpleAction()
    def act_reset_panes (self, inst, param):
        # TODO: calculate width and heights based on default typeface.
        ex, lineheight = 8, 12
        # command-picker width 24ex.
        self.groupwin.planner.set_position(24*ex)
        logger.info("Reset pane sizes")
        return

    @HiaSimpleAction()
    def act_help_help (self, inst, param):
        pass

    @HiaSimpleAction()
    def act_about (self, inst, param):
        dlg = Gtk.AboutDialog(transient_for=self.groupwin, **ABOUT)
        dlg.run()
        dlg.hide()
        return




class HiaAppWindow (Gtk.ApplicationWindow):
    """Main application window.
Holds app-wide GAction.
"""

    controller = GObject.Property(type=object)      # AppControl
    dlg_cmdpack = GObject.Property(type=object)     # GtkFileChooserDialog
    dlg_open = GObject.Property(type=object)        # GtkFileChooserDialog
    dlg_save = GObject.Property(type=object)        # GtkFileChooserDialog

    def __init__ (self, app, controller=None):
        Gtk.ApplicationWindow.__init__(self, application=app)

        self.controller = controller

        self.setup_widgets()
        self.setup_signals()

    def setup_widgets (self):
        self.set_size_request(1280,720)
        self.set_title("HID Bind Planner")
        self.vbox = Gtk.VBox()
        self.controller.insert_actions_into_widget(self)
        planner = HiaPlanner(controller=self.controller)
        self.planner = planner

        self.statusbar = Gtk.Statusbar()
        self.statusbar.push(self.statusbar.get_context_id("status"), "Ready.")
        self.statusctx = self.statusbar.get_context_id("main")
        logger.add_observer(self)

        self.setup_menubar()

        self.vbox.pack_start(self.menubar, False, False, 0)
        self.vbox.pack_start(self.planner, True, True, 0)
        self.vbox.pack_start(self.statusbar, False, False, 0)
        self.add(self.vbox)
        self.show_all()

        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files (*)")
        filter_all.add_pattern("*")

        filter_cfg = Gtk.FileFilter()
        filter_cfg.set_name("Plan File (*.cfg)")
        filter_cfg.add_pattern("*.cfg")

        filter_sqlite3 = Gtk.FileFilter()
        filter_sqlite3.set_name("SQLite3 (*.sqlite3)")
        filter_sqlite3.add_pattern("*.sqlite3")

        filter_sql = Gtk.FileFilter()
        filter_sql.set_name("Raw SQL (*.sql)")
        filter_sql.add_pattern("*.sql")

        title = "Load Command Pack"
        action = Gtk.FileChooserAction.OPEN
        buttons = [
            Gtk.STOCK_APPLY, Gtk.ResponseType.ACCEPT,
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            ]
        self.dlg_cmdpack = Gtk.FileChooserDialog(title=title, transient_for=self, action=action)
        self.dlg_cmdpack.add_buttons(*buttons)
        self.dlg_cmdpack.add_filter(filter_sqlite3)
        self.dlg_cmdpack.add_filter(filter_sql)
        self.dlg_cmdpack.add_filter(filter_all)

        title = "Save File"
        action = Gtk.FileChooserAction.SAVE
        buttons = [
            Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT,
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            ]
        filters = Gtk.FileFilter()
        self.dlg_save = Gtk.FileChooserDialog(title=title, transient_for=self, action=action)
        self.dlg_save.add_buttons(*buttons)
        self.dlg_save.add_filter(filter_cfg)
        self.dlg_save.add_filter(filter_all)

        title = "Open File"
        action = Gtk.FileChooserAction.OPEN
        buttons = [
            Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT,
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            ]
        filters = Gtk.FileFilter()
        self.dlg_open = Gtk.FileChooserDialog(title=title, transient_for=self, action=action, )
        self.dlg_open.add_buttons(*buttons)
        self.dlg_open.add_filter(filter_cfg)
        self.dlg_open.add_filter(filter_all)

        return

    def setup_menubar (self):
        def detail_transformer (raw):
            actprefix = "app."
            cooked = raw
            if type(raw) is tuple:
                (actname, paramtype, pyval) = raw
                v = GLib.Variant(paramtype, pyval)
                cooked = ("{}{}".format(actprefix, actname), v)
            else:
                cooked = "{}{}".format(actprefix, raw)
            return cooked
        MENU_DESC = [
            ('_File', [
                ('_New', "ask_file_new"),
                ('_Open', "ask_file_open"),
                ('_Save', "ask_file_save"),
                ('Save _As', "ask_file_saveas"),
                None,
                ('_CommandPack', "ask_commandpack"),
                None,
                ('_Quit', ("quit", "b", False)),
                ('RageQuit', "ragequit"),
                ]),
            ('_Edit', [
                ('_Copy', "edit_copy"),
                ('C_ut', "edit_cut"),
                ('_Paste', "edit_paste"),
                None,
                ('Pr_eferences', "preferences"),
                ]),
            ('_View', [
                ('_1 Layer', ("view_layers", "i", 1)),
                ('_2 Layers', ("view_layers", "i", 2)),
                ('_4 Layers', ("view_layers", "i", 4)),
                ('_8 Layers', ("view_layers", "i", 8)),
                None,
                ('_Reset Panes', "reset_panes"),
                ]),
            ('_Help', [
                ('_Contents', "help_help"),
                None,
                ('_About', "about"),
                ]),
            ]
        self.menu_main = HiaMenu(MENU_DESC, detail_transformer)
        menubar = Gtk.MenuBar.new_from_model(self.menu_main)
        self.menubar = menubar
        return menubar

    def setup_signals (self):
        """signals for (main) application window."""
        self.planner.ui.sel_cmd.connect("model-changed", self.on_cmdpack_changed)
        return

    def on_cmdpack_changed (self, w, cmdpackstore):
        # get modelist for BindStore adjustment.
        modelist = cmdpackstore.modelist
        for srcidx in range(len(modelist)):
            modenum = srcidx+1
            modename = modelist[srcidx]
            if modenum < len(self.controller.view.bindstore.modes):
                # rename
                self.controller.rename_mode(modenum, modename, modename)
            else:
                # add.
                self.controller.add_mode(modename, modename)
        self.planner.ui.sel_mode.update_widgets()
        return

    def logger (self, severity, msg):
        self.statusbar.push(self.statusctx, msg)



class HiaApplication (Gtk.Application):
    APP_ID = "localhost.vismapper"

    controller = GObject.Property(type=object)  # Instance AppControl
    stdin = GObject.Property(type=object)       # Instance GInputStream
    cmdline = GObject.Property(type=object)     # GApplicatCommandLine
    cmdbuf = GObject.Property(type=object)      # bytes
    repl = GObject.Property(type=object)        # GThread

    def __init__ (self, *args, **kwargs):
        flags = 0
        flags |= Gio.ApplicationFlags.NON_UNIQUE
        flags |= Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        #flags |= Gio.ApplicationFlags.HANDLES_OPEN
        Gtk.Application.__init__(self, *args, application_id=self.APP_ID, flags=flags, **kwargs)
        self.connect("activate", self.on_activate)
        self.connect("command-line", self.on_command_line)
        self.connect("handle-local-options", self.on_handle_local_options)
        self.connect("open", self.on_open)
        self.connect("shutdown", self.on_shutdown)
        self.connect("startup", self.on_startup)
        self.connect("notify::stdin", self.on_notify_stdin)
        self.mainw = None

    def on_startup (self, app):
        # app:Gio.Application
        # just after registration (app name with GNOME?)
        print("STARTUP")
        logger.threshold = logger.warn
        bindstore = BindStore()
        layouts = HiaLayouts()
        layouts.build_from_legacy_store()
        hiaview = HiaView(bindstore, layouts)
        controller = AppControl(hiaview)  # HiaControl(hiaview)
        self.controller = controller

        self.controller.actions.lookup_action('ragequit').connect("activate", lambda *a: self.quit())

        return True
    def on_shutdown (self, app):
        print("SHUTDOWN")
        return True
    def on_open (self, app, files, hint):
        # file:Gio.File
        # file:str
        return False
    def on_handle_local_options (self, app, options):
        # options:GLib.VariantDict
        PLEASE_RESUME = -1
        PLEASE_EXIT_SUCCESS = 0
        PLEASE_EXIT_ERROR = 1  # any positive integer.
        return PLEASE_RESUME
    def on_command_line (self, app, command_line):
        print("COMMAND_LINE: %r" % command_line)
        PLEASE_RESUME = 0
        # command_line:Gio.ApplicationCommandLine
        self.cmdline = command_line
        self.activate()
        self.stdin = command_line.get_stdin()
        return PLEASE_RESUME
    def on_activate (self, app):
        print("ACTIVATE")
        if not self.mainw:
            self.mainw = HiaAppWindow(self, controller=self.controller)
        self.mainw.present()
        self.controller.new_file()
        self.controller.load_commandpack("")
        return

    def cmd_actions (self, *args):
        actnames = self.controller.actions.list_actions()
        actlist = []
        for actname in actnames:
            action = self.controller.actions.lookup_action(actname)
            param_type = action.get_parameter_type()
            if param_type:
                p = param_type.dup_string()
                if not p.startswith("("):
                    p = "({})".format(p)
                entry = " ".join( (actname, p) )
            else:
                entry = actname
            actlist.append(entry)
        return "\n".join(actlist)

    def on_interactive_command (self, words):
        g_print = print
        dispatch = {
            'crash': (lambda *a: _crash()),
            'echo': (lambda *a: " ".join(a)),
            'version': (lambda *a: "version 0"),
            '#t': (lambda *a: True),
            '#f': (lambda *a: False),
            '#n': (lambda *a: None),
            'help': (lambda *a: r"""Commands are matched against action names, arguments are converted and grouped for action activation.  Command arguments are interpreted as int, bool (#t or #f), None (#n), str.
Use command 'actions' for list of known actions.
"""),
            'actions': self.cmd_actions,
        }
        if not words:
            return  # Can happen if input is all whitespaces.
        cmd = words[0]
        f = dispatch.get(cmd, None)
        if f:
            return f(*words[1:])
        action = self.controller.actions.lookup_action(cmd)
        if action:
            entry = getattr(self.controller, cmd)
            # convert rest of arguments to integer or string.
            args = []
            for word in words[1:]:
                v = None
                if len(word) == 0:
                    v = str("")
                elif word[0].isdigit():
                    try:
                        v = int(word)
                    except ValueError:
                        v = str(word)
                elif word[0] == '#':
                    ch1 = word[1] if len(word) > 1 else '\0'
                    if ch1 in ("t", "T"):
                        v = True
                    elif ch1 in ("f", "F"):
                        v = False
                    elif ch1 in ("n", "N"):
                        v = None
                    else:
                        v = str(word)
                else:
                    v = str(word)
                args.append(v)
            pyval = entry(*args)
            return pyval
        return "BAD_COMMAND({!r})".format(cmd)

    def thread_repl (self, ginputstream):
        pass

    def pump_stdin (self, extra=None):
        count = 4096
        ioprio = GLib.PRIORITY_DEFAULT
        cancellable = None
        callback = self.on_stdin_async_ready
        self.stdin.read_bytes_async(count, ioprio, cancellable, callback, extra)
        return False

    def on_stdin_async_ready (self, srcobj, res, extra):
        # read
        buf = srcobj.read_bytes_finish(res).get_data()
        if buf:
            self.cmdbuf += buf
        else:
            # Delay 0.05s and re-run pump_stdin().
            GLib.timeout_add(GLib.PRIORITY_DEFAULT, 50, self.pump_stdin, extra)
            return
        pending = str(self.cmdbuf.decode())
        g_print = print
        while "\n" in pending:
            oneline, pending = pending.split("\n", 1)
            # eval
            words = shlex.split(oneline)
            printable = self.on_interactive_command(words)
            # print
            if printable is True: g_print("#t")
            elif printable is False: g_print("#f")
            elif printable is None: pass  # g_print("#n")
            else: g_print(printable)
        self.cmdbuf = bytes(pending.encode())
        # loop.
        self.pump_stdin()

    def on_notify_stdin (self, inst, param):
        # set non-block
        #fcntl.fcntl(self.stdin.get_fd(), fcntl.F_SETFL, os.O_NONBLOCK)
        # Spin up stdin-reading and parsing thread.
        self.pump_stdin()
        self.cmdbuf = bytes()



if __name__ == "__main__":
    #w = HiaWindow()
    #Gtk.main()
    a = HiaApplication()
    a.run(sys.argv)

