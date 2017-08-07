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
        """Returns two values: iter:TreeIter, parent_iter:TreeIter;
Second value is useful for the appender, knowing which entry is the parent of the new entry.
"""
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

    def getvalue (self, path, defval=None):
        """Returns the "value" portion of an entry, which is the second column and onwards."""
        treeiter = self.get_iter(path)
        if treeiter:
            #row = self.__getitem__(treeiter)
            row = tuple(Gtk.TreeStore.__getitem__(self, treeiter))
            return row[1:]
        else:
            return defval

    def getfirst (self, path, defval=None):
        """Returns first column of "value" portion, for the use case of this object as a dict."""
        row = self.getvalue(path, defval)
        if row and row is not defval:
            return row[0]
        else:
            return defval



# BindDisplayStore: provided to all widgets that can display bindings.
# list of hiasym and the associated bind to display.

class BindDisplayStore (TreeAssocStore):
    """
Every widget expected to show a bind-value of some sort views this model.

Columns = (hiasym:str, symattr:int, bind[0]:str, attr[0]:int, bind[1]:str, attr[
1]:int, ...)

With row 0 (hiasym == ".vis") holding visibility list.

Clusters have an entry, with column values indicating the cluster type (per laye
r?), with children corresponding to their nested binds.
(cluster: iter_has_child() == True)
"""
    def __init__ (self, nlayers):
        # Columns = (hiasym, hialabel, bind[0], attr[0], bind[1], attr[1], ...)
        col_def = (str,str) + (str,int)*nlayers
        TreeAssocStore.__init__(self, *col_def)



def gproperty (name, defval=None):
    """selfish gobject properties -- generically 'object' to be Pythonic dynamically typed."""
    def prop_getter (self):
        try:
            return self._gproperties.get(name, defval)
        except AttributeError:
            self._gproperties = dict({name:defval})
            return defval
    return prop_getter

class SimpleGPropertiesMixin (object):
    def do_get_property (self, propname):
        try:
            return self._gpropertis.get(propname)
        except AttributeError:
            self._gproperties = { propname: None }
            return None
    def do_set_property (self, propname, val):
        try:
            self._gproperties[propname] = val
        except AttributeError:
            self._gproperties = { propname, val }


class BindAware (Gtk.Widget):
    """Base class for objects that are aware of BindDisplayModel."""

    display_model = GObject.Property(type=object)

    def __init__ (self, mdl_binddisplay):
        Gtk.Widget.__init__(self)
        #self.set_property("display_model" , "Nope")

GObject.type_register(BindAware)




class BindTop (Gtk.ToolButton, BindAware):
    """One human-computer interface device element, based on an approximation of a keyboard key."""

    toplabel = GObject.Property(type=str, default="")
    # Explicit inheritance?
    display_model = BindAware.display_model

    def __init__ (self, bindsym, mdl_binddisplay=None):
        BindAware.__init__(self, mdl_binddisplay)
        #Gtk.VBox.__init__(self)
        #Gtk.Button.__init__(self)
        Gtk.ToolButton.__init__(self, None, None)
        self.setup_states()

        #self.set_property("display_model", bindsym)
        self.set_property("toplabel", "BUTTON")

        self.setup_widget()
        self.setup_signals()
        self.setup_dnd()

    def setup_states (self):
        pass

    def setup_states (self):
        return

    def setup_widget (self):
        """"BindTop Button, label composed of multiple rows:
1. a row, (typically) left-justified, for the bindtop label.
2. an event box with "SHADOW_IN" depressed-box effect for bind layers and DnD:
 2A. sequence of re-styleable GtkLabels, showing binding for one layer.
 2A. sequence of Separator(horizontal) between the GtkLabels.
"""
        self.ui = type("ui", (), {})
        self.ui.widget = Gtk.VBox()
        self.ui.lbl_top = Gtk.Label(self.props.toplabel)
        self.ui.lbl_top.set_xalign(0.0)

        self.ui.frame_bind = Gtk.Frame()
        self.ui.frame_bind.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

        refstylectx = Gtk.Entry().get_style_context()
        bg_rgb = refstylectx.get_background_color(Gtk.StateFlags.NORMAL)
        #self.ui.box_layers = Gtk.EventBox()
        #self.ui.box_layers.set_visible_window(False)

        nlayers = 8
        self.ui.bindrows = []   # Bind rows (HBox).
        self.ui.lyrs = []       # layer prefix (Label)
        self.ui.disps = []      # Bind display (Label)
        self.ui.hseps = []      # Separators between rows (HSeparator)

        box = Gtk.VBox()
        for i in range(nlayers):
            bindrow = Gtk.HBox()
            lyr = Gtk.Label()
            disp = Gtk.Label()
            hsep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            bindrow.pack_start(lyr, False, False, 0)
            bindrow.pack_start(disp, True, True, 0)
            self.ui.bindrows.append(bindrow)
            self.ui.lyrs.append(lyr)
            self.ui.disps.append(disp)
            self.ui.hseps.append(hsep)
            box.pack_start(hsep, False, False, 0)
            box.pack_start(bindrow, False, False, 0)

            if i == 0:
                stylectx = disp.get_style_context()
                #print("path: %r" % (refstylectx.get_path()))
                #stylectx.set_path(refstylectx.get_path())

        #self.ui.box_layers.add(box)
        self.ui.frame_bind.add(box)

        self.ui.widget.pack_start(self.ui.lbl_top, False, False, 0)
        #self.ui.widget.pack_start(self.ui.box_layers, True, True, 0)
        self.ui.widget.pack_start(self.ui.frame_bind, True, True, 0)
        self.ui.widget.pack_start(Gtk.Label("Another"), False, False, 0)
        self.ui.widget.pack_start(Gtk.Label("Another2"), False, False, 0)
        self.ui.widget.show_all()

        #self.set_image(self.ui.widget)
        self.set_label_widget(self.ui.widget)
        self.show_all()
        return

    def setup_signals (self):
        return

    def setup_dnd (self):
        return

GObject.type_register(BindTop)


class BindClusterable (object):
    """Handles multiple BindTop simulataneously."""
    def __init__ (self):
        pass


class BindListView (object):
    """View BindDisplayModel, or portions thereof, as a TreeView."""
    def __init__ (self):
        pass

class BindPlanar (BindClusterable):
    """
Originally modeled after Steam Controller touchpad and Steam client's handling of it.
"""
    def __init__ (self):
        pass

class BindLayout (BindClusterable):
    """
Top level grouping of BindTops nad BindPlanar.
"""
    def __init__ (self):
        pass




class CommandPackStore (Gtk.TreeStore):
    def __init__ (self):
        pass

class CommandPackView (Gtk.TreeView):
    def __init__ (self):
        pass




class BindSelectors (object):
    def __init__ (self):
        pass




class BindMapView (object):
    def __init__ (self):
        pass




class BindMapWidget (object):
    def __init__ (self):
        pass



if __name__ == "__main__":
    pass
