#!/usr/bin/env python
# vi: set tabstop=4 expandtab shiftwidth=4 :

import sys
import gtk, gobject

import kbd_desc



class KbTop (gtk.Button):
    def __init__ (self, label):
        gtk.Button.__init__(self)
        self.plane = gtk.VBox()
        self.inp_lbl = gtk.Label()
        self.spacer = gtk.HBox()
        #self.inp_bind = gtk.Entry()
        #self.inp_bind = gtk.TextView()
        self.inp_bind = gtk.Label()
        self.ksym = None
        self._bind = None
        self._bindid = None
#        self.layers = {}  # Mapping layer id to bind for that layer.

        encoded = label.split("\f")
        self.label = encoded[0]
        if len(encoded) > 1:
            self.ksym = encoded[1]
        else:
            self.ksym = self.label

#        if len(self.label) > 2:
#            self.inp_lbl.set_markup("<small>%s</small>" % self.label)
#        else:
#            self.inp_lbl.set_text("%s" % self.label)
        self.set_keytop(self.label)

#        if 1:
#            style = self.inp_bind.get_style().copy()
#            #self.inp_bind.set_style('draw-border', True)
#            print("style: %r" % style)
#            #self.inp_bind.set_border_width(2)
#            #border = gtk.Border(2,2,2,2)
#            #style.draw_border = border
#            bg = style.bg
#            print("bg: %r // %r" % (bg, list(bg)))
#            bg[0] = gtk.gdk.Color('#ffffff')
#            bg[1] = gtk.gdk.Color('#ffffff')
#            bg[2] = gtk.gdk.Color('#ffffff')
#            bg[3] = gtk.gdk.Color('#ffffff')
#            bg[4] = gtk.gdk.Color('#ffffff')
#            print("new-bg: %r // %r" % (bg, list(bg)))
#            #self.inp_bind.set_style(style)
#            self.inp_bind.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color('#ffffff'))
#            self.inp_bind.set_markup("<span bgcolor='white'>BLAH</span>")
#            #self.inp_bind.set_markup("<span bgcolor='white'>%-32s</span>" % "")
#            pass

        #self.inp_bind.set_sensitive(False)
        #self.inp_bind.set_width_chars(32)
        #self.inp_bind.set_max_width_chars(8)
        self.inp_bind.set_width_chars(4)
        self.inp_bind.set_justify(gtk.JUSTIFY_LEFT)
        #print("inp_bind events = %r" % self.inp_bind.get_events())

        #self.evbox = gtk.EventBox()
#        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, [ ("bind", gtk.TARGET_SAME_APP, 1) ], gtk.gdk.ACTION_LINK)
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
        #self.bg_bind.add(self.inp_bind)
        #self.box_bind.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#ffffff'))

        # TODO: pull color from Entry background (due to themes).
        bgcolor = gtk.gdk.color_parse('#ffffff')
        self.bg_bind.modify_bg(gtk.STATE_NORMAL, bgcolor)
        self.bg_bind.modify_bg(gtk.STATE_ACTIVE, bgcolor)
        self.bg_bind.modify_bg(gtk.STATE_PRELIGHT, bgcolor)
        self.bg_bind.modify_bg(gtk.STATE_SELECTED, bgcolor)
        #self.bg_bind.modify_bg(gtk.STATE_INSENSITIVE, bgcolor)

        #self.box_bind.add(self.bg_bind)
#        self.row_bind = gtk.HBox()
#        self.row_bind.pack_start(gtk.Label("["), False, False)
#        self.row_bind.pack_start(self.inp_bind, False, False)
#        self.row_bind.pack_start(gtk.Label("]"), True, True)
        self.inp_bind.set_alignment(0, 0.5)
        self.bg_bind.add(self.inp_bind)
        self.align1.add(self.bg_bind)
        self.box_bind.add(self.align1)

#        self.bg_bind.add(self.inp_bind)
#        self.bg_bind.set_above_child(True)
#        self.align1.add(self.bg_bind)
#        self.box_bind.add(self.align1)

        self.plane.pack_start(self.box_bind, expand=False, fill=False)

        #self.evbox.add(self.plane)

        del self.bind

        self.add(self.plane)
        #self.add(self.evbox)

    def set_keytop (self, disp):
        if len(disp) > 2:
            self.inp_lbl.set_markup("<small>%s</small>" % disp)
        else:
            self.inp_lbl.set_text("%s" % disp)
        return

    def get_bind (self):
        return self._bind
    def set_bind (self, value):
        self._bind = value
        if value is None:
#            dispval = "<span bgcolor='white'>%-8s</span>" % ""
#            self.inp_bind.set_markup(dispval)
            self.inp_bind.set_text("")
        else:
            #self.inp_bind.set_text("%-8s" % value)
            dispval = value
#            dispval = "<span bgcolor='yellow'>%-8s</span>" % value
            if len(value) > 6:
                dispval = "<small>%s</small> " % dispval
            self.inp_bind.set_markup(dispval)
#            self.inp_bind.set_text(value)
        self.emit("bind-changed")
    def del_bind (self):
        self._bind = None
#        self.inp_bind.set_text("")
#        dispval = "<span bgcolor='white'>%-8s</span>" % ""
#        self.inp_bind.set_markup(dispval)
        self.inp_bind.set_text("")
        self.emit("bind-changed")

    bind = property(get_bind, set_bind, del_bind)

    def get_bindid (self):
        return self._bindid
    def set_bindid (self, val):
        self._bindid = val
        self.emit("bindid-changed")
    def del_bindid (self):
        self._bindid = None
        self.emit("bindid-changed")

    bindid = property(get_bindid, set_bindid, del_bindid)

    def on_drop (self, w, ctx, x, y, time, *args):
#        other = ctx.get_source_widget()
#        sel = other.get_selection()
#        (treemdl, treeiter) = sel.get_selected()
#        val = treemdl.get_command(treeiter)
#        self.bind = val
#
#        if treemdl.iter_has_child(treeiter):
#            # non-terminal item; fail.
#            ctx.drop_finish(False, 0)
#            return
#        # Get the command to bind.
#        #val = treemdl.get_value(treeiter, 0)
#        val = treemdl.get_value(treeiter, 1)
#        w.set_text(val)
#        print("calling drag_get_data")
        self.drag_get_data(ctx, "STRING", time)

        return True

#    def on_drag_data_received (self, w, ctx, x, y, sel, info, time, *args):
##        print("DATA RECEIVED: %r" % sel.get_text())
#        self.bind = sel.get_text()
#        ctx.finish(True, False, time)
    def on_drag_data_received (self, w, ctx, x, y, sel, info, time, *args):
#        print("DATA RECEIVED: %r" % sel.get_text())
        #self._bindid = int(sel.get_text())
        self.bindid = int(sel.get_text())
        #self.bind = sel.get_text()
        ctx.finish(True, False, time)

gobject.type_register(KbTop)
gobject.signal_new("bind-changed", KbTop, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
gobject.signal_new("bindid-changed", KbTop, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())



class KblayoutWidget (gtk.VBox):
    def __init__ (self):
        gtk.VBox.__init__(self)
        self.keytops = {}
        self.active = False
        #self.grid = gtk.Table(homogeneous=True)
        self.grid = gtk.Table(homogeneous=True)

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

        self.lbl_layout = gtk.Label("Layout:")
        self.row_layout = gtk.HBox()
        self.row_layout.pack_start(self.lbl_layout, expand=False, fill=False)
        self.row_layout.pack_start(self.inp_layout, expand=False, fill=False)

        #self.fill_board(kbd_desc.KBD['en_US'])
        #self.fill_board(self.kbdesc['en_US'])
        #self.fill_board(self.kbdesc['en_US (HHK)'])
        idx = self.inp_layout.get_active()
        val = self.mdl_layout[idx][0]
        self.fill_board(self.kbdesc[val])

#        self.gridport = gtk.ScrolledWindow()
#        self.gridport.add_with_viewport(self.grid)
#        self.hscroll = gtk.Adjustment(0, 1, 0, 1, 1, 1)
#        self.vscroll = gtk.Adjustment(0, 0, 100, 1, 10, 10)
##        self.gridport = gtk.Viewport(self.hscroll, self.vscroll)
##        self.gridport.add(self.grid)
#        self.gridport.set_hadjustment(self.hscroll)
#        self.gridport.set_vadjustment(self.vscroll)
#        self.gridport.size_allocate(gtk.gdk.Rectangle(0, 0, 640, 1024))

        self.pack_start(self.row_layout, expand=False, fill=False)
#        self.pack_start(self.gridport, expand=True, fill=True)
        self.pack_start(self.grid, expand=False, fill=False)

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
                        keytop = KbTop(label)
                        l, r = colnum, colnum+width
                        t, b = rownum, rownum+2*height
                        #print("attach %r %r %r %r %r" % (keytop, l, r, t, b))
                        grid.attach(keytop, l, r, t, b)
                        if keytops.has_key(keytop.ksym):
                            print("potential duplicate: %s" % keytop.label)
                        keytops[keytop.ksym] = keytop
                        keytop.connect("clicked", self.on_keytop_clicked)
                        keytop.connect("bind-changed", self.on_bind_changed)
                        keytop.connect("bindid-changed", self.on_bindid_changed)
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
        ksym = w.ksym
        print("target: %s" % ksym)
        self.emit("key-selected", ksym)

    def on_bind_changed (self, w, *args):
        #self.bindmap[w.ksym] = w.bind
        self.emit("bind-changed", w)

    def on_bindid_changed (self, w, *args):
        #print("Kblayout: bindid-changed")
        #self.bindmap[w.ksym] = w.bind
        self.emit("bindid-changed", w)

    def __getitem__ (self, ksym):
        return self.keytops[ksym]

    def __setitem__ (self, ksym, val):
        self.keytops[ksym].bind = val

    def __delitem__ (self, ksym):
        del self.keytops[ksym]

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

    def on_key_selected (self, w, ksym, *args):
        print("Selected ksym '%s'" % ksym)

    def on_bind_changed (self, w, keytop, *args):
        print("Bind changed for %r" % keytop)

    def run (self):
        self.show_all()
        gtk.mainloop()


if __name__ == "__main__":
    x = KblayoutWindow()
    x.run()

