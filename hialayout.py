#!/usr/bin/env python3
# Python3 and Gtk3

# Python2-combatibility
from __future__ import print_function, with_statement, unicode_literals

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib




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
        for x in self.observers:
            x(hiasym)

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
        for x in self.observers:
            x(layernum, hiasym)


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

    def get_bind (self, groupid, layerid, hiasym):
        lyr = self.get_layer(groupid, layerid)
        if lyr is None: return None
        val = lyr.get(hiasym, None)
        return val

    def set_bind (self, groupid, layerid, hiasym, hiaval, hiacmd=None):
        cooked = None
        if hiacmd is not None:
            cooked = BindValue(hiaval, hiacmd)
        else:
            cooked = hiaval
        self.groups[groupid][layerid][hiasym] = cooked

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

    __gsignals__ = {
        str("bind-changed"): ( GObject.SIGNAL_RUN_FIRST, None, (str, str, str) ),
    }



