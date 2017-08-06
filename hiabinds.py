#!/usr/bin/env python2
# vim: set ai et ts=4 sw=4 :

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GObject

def isstringlike (x):
    try:
        x.isalpha
        return True
    except:
        return False

def issequencelike_nostring (x):
    if isstringlike(x):
        return False
    try:
        x.__len__
        return True
    except:
        return False

class TreeAssocStore (Gtk.TreeStore):
    """Extension to Gtk.TreeStore that treats the first column as a key value usable in search-by-key."""
    def __init__ (self, *args):
        self._col_def = args
        Gtk.TreeStore.__init__(self, *args)
    # Correctness first, optimize later.
    def get_iter_info (self, path, recurse=None):
        if isstringlike(path) and recurse is None:
            drill = self.get_iter_first()
            return self.get_iter_info((path,), drill)
        else:
            if not isstringlike(path[0]):
                #return Gtk.TreeStore.get_iter(self, path), Gtk.TreeStore.iter_parent(self, Gtk.TreePath(path))
                return Gtk.TreeStore.get_iter(self, path), None
            # More drill-down.
            finditer = self.get_iter_first()
            result = None
            for k in path:
                chiter = None
                while finditer:
                    if (Gtk.TreeStore.__getitem__(self, finditer)[0] == k):
                        result = finditer
                        finditer = Gtk.TreeStore.iter_children(self, finditer)
                        break
                    finditer = self.iter_next(finditer)
                else:
                    result = None
            return result, finditer
    def get_iter (self, path):
        treeiter, parentiter = self.get_iter_info(path)
        return treeiter
    def __getitem__ (self, k):
        treeiter = self.get_iter(k)
        if treeiter is None:
            raise KeyError("path not found: {!r}".format(k))
        return Gtk.TreeStore.__getitem__(self, treeiter)

    def __setitem__ (self, k, val):
        treeiter, parentiter = self.get_iter_info(k)
        # Transform val as needed.
        if issequencelike_nostring(val):
            ncols = len(self._col_def)
            if len(val) == ncols:
                pass  # matched; leave alone.
            elif len(val) == ncols-1:
                val = (k,)+val
            else:
                raise ValueError("mismatched number of columns: {!r}".format(val))
        else:
            # singular value; prepend k and extend with None to columns.
            val = (k,) + (val,) + (None,)*(len(self._col_def)-2)
        if treeiter is None:
            # append.
            treeiter = self.append(parentiter, val)
        else:
            # assign in place.
            return Gtk.TreeStore.__setitem__(self, treeiter, val)

