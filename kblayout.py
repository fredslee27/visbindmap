#!/usr/bin/env python
# vi: set tabstop=4 expandtab shiftwidth=4 :

import sys
import gtk, gobject

import kbd_desc



class InpDescrModel (gobject.GObject):
    """Input descriptor model.  UI elements refer to this object for visual properties to use."""

    class InpLayer (object):
        """To be accessed as if dict."""
        def __init__ (self, parent, layernum, fallback):
            self.layernum = layernum
            self._binds = dict()
            # if the binding resolution fails, borrow from the fallback layer.
            self._fallback = None

        def get_bind (self, k):
            if self._binds.has_key(k):
                return self._binds[k]
            elif self._fallback:
                return self._fallback[k]
            else:
                return None

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

    def __init__ (self, nlayers=1):
        gobject.GObject.__init__(self)
        # Mapping of inpsym to label to display in UI.
        self.labels = dict()
        # List of InpLayer representing the binding layers.
        self.layers = list()
        self.set_numlayers(nlayers)

    def get_label (self, inpsym):
        return self.labels.get(inpsym, inpsym)

    def set_label (self, inpsym, lbl):
        self.labels[inpsym] = lbl
        self.emit("label-changed", inpsym)

    def get_layer (self):
        return self._layer
    def set_layer (self, val):
        self._layer = val
        self.emit("layer-changed", val)

    def get_layer (self, n):
        if (0 <= n) and (n < len(self.layers)):
            return self.layers[n]

    def set_numlayers (self, n):
        self.maxlayers = n
        while (len(self.layers) < self.maxlayers):
            m = len(self.layers)
            if m > 0:
                fallback = m-1
            else:
                fallback = None
            temp = self.InpLayer(self, m, fallback)
            self.layers.append(temp)

    def get_bind (self, layernum, inpsym):
        self.get_layer(layernum).get_bind(inpsym)

    def set_bind (self, layernum, inpsym, v):
        self.get_layer(layernum).set_bind(inpsym, v)
        self.emit("bind-changed", layernum, inpsym)

    def resolve_bind (self, layernum, inpsym):
        follow = layernum
        retval = None
        while (retval is None) and (follow is not None):
            layer = self.get_layer(layernum)
            if layer:
                retval = layer.get_bind(inpsym)
            else:
                follow = layer._fallback

    # Signals:
    # * bind-changed(layer:int, inpsym:str) - a binding changed; update display
    # * label-changed() - labels for keytops has changed; update display
    # * layer-changed() - active layer changed

gobject.type_register(InpDescrModel)
gobject.signal_new("bind-changed", InpDescrModel, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_STRING))
gobject.signal_new("label-changed", InpDescrModel, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
gobject.signal_new("layer-changed", InpDescrModel, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,))



class KbTop (gtk.Button):
    """UI element of a key(board) top.  Presented as the inpsym on the first row, and a boxed text entry on the second row for the binding.
    Contents to display are packaged in a data model (InpDescrModel)
    """
    def __init__ (self, inpsym, inpdescr=None):
        """Initialize with given data model, and the input symbol tied to this kbtop"""
        # UI elements
        gtk.Button.__init__(self)
        self.plane = gtk.VBox()
        self.inp_lbl = gtk.Label()
        self.spacer = gtk.HBox()
        self.inp_bind = gtk.Label()

        # data model
        self.set_model(inpdescr)
        #self.inpdescr = inpdescr
        self.inpsym = inpsym

        # Fill label (first row)
        self.label = self.inpdescr.get_label(self.inpsym)
        #self.set_keytop(self.label)

        # Adjust bind display (second row)
        self.inp_bind.set_width_chars(4)
        self.inp_bind.set_justify(gtk.JUSTIFY_LEFT)

        # Set up drag-and-drop
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, [ ("bindid", gtk.TARGET_SAME_APP, 1) ], gtk.gdk.ACTION_LINK)
        self.connect("drag-drop", self.on_drop)
        self.connect("drag-data-received", self.on_drag_data_received)

        self.align0 = gtk.Alignment(0, 0, 0, 0)
        self.align0.add(self.inp_lbl)
        self.plane.pack_start(self.align0, expand=True, fill=True)
        self.plane.pack_start(self.spacer, expand=True, fill=True)

        self.box_bind = gtk.Frame()
        self.box_bind.set_shadow_type(gtk.SHADOW_IN)
        self.align1 = gtk.Alignment(0,0,1,1)
        self.bg_bind = gtk.EventBox()

        # TODO: pull color from Entry background (due to themes).
        bgcolor = gtk.gdk.color_parse('#ffffff')
        self.bg_bind.modify_bg(gtk.STATE_NORMAL, bgcolor)
        self.bg_bind.modify_bg(gtk.STATE_ACTIVE, bgcolor)
        self.bg_bind.modify_bg(gtk.STATE_PRELIGHT, bgcolor)
        self.bg_bind.modify_bg(gtk.STATE_SELECTED, bgcolor)
        #self.bg_bind.modify_bg(gtk.STATE_INSENSITIVE, bgcolor)

        self.inp_bind.set_alignment(0, 0.5)
        self.bg_bind.add(self.inp_bind)
        self.align1.add(self.bg_bind)
        self.box_bind.add(self.align1)

        self.plane.pack_start(self.box_bind, expand=False, fill=False)

        self.add(self.plane)

        self.update_display()

    def get_inpsym (self):
        return self.inpsym
    def set_inpsym (self, val):
        self.inpsym = val

    def get_model (self):
        return self.inpdescr
    def set_model (self, mdl):
        if mdl is None:
            mdl = InpDescrModel()
        self.inpdescr = mdl
        if self.inpdescr:
            self.inpdescr.connect("bind-changed", self.on_data_change)
            self.inpdescr.connect("label-changed", self.on_data_change)
            self.inpdescr.connect("layer-changed", self.on_data_change)
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
        layernum = 0
        val = self.inpdescr.get_layer(layernum).get_bind(self.inpsym)
        if val:
            self.inp_bind.set_text(val)
        else:
            self.inp_bind.set_text("")

    def on_data_change (self, *args):
        self.update_display()

    def on_drop (self, w, ctx, x, y, time, *args):
        dragdata = self.drag_get_data(ctx, "STRING", time)
        return True

    def on_drag_data_received (self, w, ctx, x, y, sel, info, time, *args):
        print("%s.on_drag_data_received" % self)
        bindid = int(sel.get_text())
        print(" drag_data => %s" % bindid)
        self.bindid = bindid
        ctx.finish(True, False, time)
        active_layer = 0
        #self.inpdescr.get_layer(active_layer).set_bind(self.inpsym, bindid)
        self.inpdescr.set_bind(active_layer, self.inpsym, str(bindid))
        print(" bind(inpsym=%s, val=%s)" % (self.inpsym, "test_ok"))

#gobject.type_register(KbTop)
#gobject.signal_new("bind-changed", KbTop, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
#gobject.signal_new("bindid-changed", KbTop, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())



class KblayoutWidget (gtk.VBox):
    def __init__ (self, mdl=None):
        gtk.VBox.__init__(self)
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
                        keytop = KbTop(inpsym, self.mdl)
                        l, r = colnum, colnum+width
                        t, b = rownum, rownum+2*height
                        #print("attach %r %r %r %r %r" % (keytop, l, r, t, b))
                        grid.attach(keytop, l, r, t, b)
                        if keytops.has_key(inpsym):
                            print("potential duplicate: %s" % inpsym)
                        keytops[inpsym] = keytop
                        keytop.connect("clicked", self.on_keytop_clicked)
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
        print("target: %s" % inpsym)
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
        print("Selected inpsym '%s'" % inpsym)

    def on_bind_changed (self, w, keytop, *args):
        print("Bind changed for %r" % keytop)

    def run (self):
        self.show_all()
        gtk.mainloop()


if __name__ == "__main__":
    x = KblayoutWindow()
    x.run()

