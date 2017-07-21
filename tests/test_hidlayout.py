import unittest
import time

import hidlayout
import kbd_desc
import gobject
import gtk


class TestHidlayout(unittest.TestCase):
    def setUp (self):
        gtk.threads_init()
        self.inpdescr = hidlayout.InpDescrModel(8,8)
        self.ds = hidlayout.InpDisplayState(self.inpdescr)


    def runloop (self, playback=[lambda: None]):
        for n in range(0, len(playback)):
            t = time.time()
            timegate = t
            invoke = playback[n]
            if callable(invoke):
                invoke()
            elif type(invoke) in ( int, float ):
                timegate = t + invoke
            else:
                pass
            while t <= timegate:
                while gtk.events_pending():
                    gtk.main_iteration_do(block=False)
                t = time.time()


    def test_models (self):
        bindchanged = []
        def on_bindchange (w, *args):
            bindchanged.append(True)

        self.inpdescr.connect("bind-changed", on_bindchange)

        playback=[ lambda: self.inpdescr.set_bind(0, "K_ESCAPE", 0, 0),
                   ]

        self.runloop(playback)
        self.assertTrue(True in bindchanged)

    def test_hidtop (self):
        def on_bindchange(w, *args):
            pass
        self.inpdescr.connect("bind-changed", on_bindchange)

        w = gtk.Window()
        w.set_title("Test HidTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = hidlayout.HidTop("K_TEST", self.ds)
        b.set_hidtop(self.inpdescr.get_label("K_TEST"))
        layout.pack_start(b, expand=False, fill=False, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        w.show_all()

        playback = [ lambda: None,
                     1,
                     lambda: self.inpdescr.set_label("K_TEST", "TEST"),
                     lambda: b.set_hidtop(self.inpdescr.get_label("K_TEST")),
                     lambda: self.assertEqual(b.inp_lbl.get_text(), "TEST"),
                     1,
                     lambda: self.inpdescr.set_bind("K_TEST", "test_changer", 0, 0),
                     lambda: b.set_dispbinds(self.ds.resolve_bind_group_markup("K_TEST")),
                     2
                     ]

        self.runloop(playback)
        self.assertEqual(b.inp_lbl.get_text(), "TEST")
        self.assertEqual(b.inp_binds[0].get_text(), "test_changer")
        #time.sleep(4)
        w.hide()

    def test_hidplanar (self):
        def on_bindchange(w, *args):
            pass
        self.inpdescr.connect("bind-changed", on_bindchange)

        w = gtk.Window()
        w.set_title("Test HidTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = hidlayout.HidPlanar("L#", self.ds)
#        b.set_arranger(b.arrangerDpad())
        #layout.pack_start(b, expand=False, fill=False, padding=0)
        layout.pack_start(b, expand=True, fill=True, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        #layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        def use_arranger (arranger):
            b.set_arranger(arranger)
            lbl.set_label("Testing: %s " % b.get_arranger())
        use_arranger(b.arrangerOneButton)

        w.show_all()

        playback = [ lambda: None,
                     2,
                     lambda: use_arranger(b.arrangerScrollwheel),
                     2,
                     lambda: use_arranger(b.arrangerListmenu),
                     4,
                     lambda: use_arranger(b.arrangerDpad),
                     2,
                     lambda: use_arranger(b.arrangerMouse),
                     2,
                     lambda: use_arranger(b.arrangerDiamond),
                     2,
                     lambda: use_arranger(b.arrangerJoystick),
                     2,
                     lambda: use_arranger(b.arrangerTouchmenu),
                     2,
                     lambda: use_arranger(b.arrangerTouchmenu(4)),
                     2,
                     lambda: use_arranger(b.arrangerTouchmenu(6)),
                     2,
                     lambda: use_arranger(b.arrangerTouchmenu(10)),
                     2,
                     lambda: use_arranger(b.arrangerTouchmenu(20)),
                     2,
                     lambda: use_arranger(b.arrangerRadialmenu(2)),
                     2,
                     lambda: use_arranger(b.arrangerRadialmenu(3)),
                     2,
                     lambda: use_arranger(b.arrangerRadialmenu(4)),
                     2,
                     lambda: use_arranger(b.arrangerRadialmenu(7)),
                     2,
                     lambda: use_arranger(b.arrangerRadialmenu(8)),
                     2,
                     lambda: use_arranger(b.arrangerRadialmenu(12)),
                     2,
                     lambda: use_arranger(b.arrangerRadialmenu(15)),
                     2,
                     lambda: use_arranger(b.arrangerRadialmenu(20)),
                     2,
                     ]

        self.runloop(playback)
        #time.sleep(4)
        w.hide()

    def test_hidplanar_radial_calc (self):
        def on_bindchange(w, *args):
            pass
        self.inpdescr.connect("bind-changed", on_bindchange)

        w = gtk.Window()
        w.set_title("Test HidTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = hidlayout.HidPlanar("L#", self.ds)
        b.set_arranger(b.arrangerRadialmenu(3))
        layout.pack_start(b, expand=False, fill=False, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        w.show_all()

        playback = [ lambda: None,
                     1,
                     lambda: b.set_arranger(b.arrangerRadialmenu(4)),
                     1,
                     lambda: b.set_arranger(b.arrangerRadialmenu(7)),
                     1,
                     lambda: b.set_arranger(b.arrangerRadialmenu(10)),
                     1,
                     lambda: b.set_arranger(b.arrangerRadialmenu(14)),
                     1,
                     lambda: b.set_arranger(b.arrangerRadialmenu(16)),
                     1,
                     lambda: b.set_arranger(b.arrangerRadialmenu(20)),
                     3,
                     lambda: b.set_arranger(b.arrangerRadialmenu(16)),
                     1,
                     lambda: b.set_arranger(b.arrangerRadialmenu(12)),
                     1,
                     lambda: b.set_arranger(b.arrangerRadialmenu(8)),
                     1,
                     lambda: b.set_arranger(b.arrangerRadialmenu(2)),
                     1,
                     ]

        self.runloop(playback)
        #time.sleep(4)
        w.hide()

    def test_hidplanar_ctxmenu (self):
        def on_bindchange(w, *args):
            pass
        self.inpdescr.connect("bind-changed", on_bindchange)

        w = gtk.Window()
        w.set_title("Test HidTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = hidlayout.HidPlanar("L#", self.ds)
        layout.pack_start(b, expand=True, fill=True, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)

        def popup_ctx_menu ():
            b.ctxmenu.popup(None,None,None,gtk.gdk.RIGHTBUTTON,0)
        b.set_arranger(b.arrangerDpad)

        w.show_all()

        playback = [ lambda: None,
                     2,
                     lambda: popup_ctx_menu(),
                     1,
                     lambda: b.ctxmenu.select_item(b.ctxmenu.get_children()[2]),
                     1,
                     lambda: b.ctxmenu.activate_item(b.ctxmenu.get_children()[2], False),
                     8,
                     ]

        self.runloop(playback)
        #time.sleep(4)
        w.hide()

    def test_hidplanar_persist (self):
        def on_bindchange(w, *args):
            pass
        self.inpdescr.connect("bind-changed", on_bindchange)

        w = gtk.Window()
        w.set_title("Test HidTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        class data:
            b = None

        def popup_ctx_menu ():
            data.b.ctxmenu.popup(None,None,None,gtk.gdk.RIGHTBUTTON,0)
        def rebuild ():
            if data.b:
                layout.remove(data.b)
            data.b = hidlayout.HidPlanar("L#", self.ds)
            layout.pack_start(data.b, expand=True, fill=True, padding=0)
            lbl = gtk.Label("Testing...")
            layout.pack_start(lbl, expand=False, fill=True, padding=0)
        rebuild()
        data.b.set_arranger(data.b.arrangerDpad)

        w.show_all()

        playback = [ lambda: None,
                     2,
                     lambda: popup_ctx_menu(),
                     lambda: data.b.ctxmenu.select_item(data.b.ctxmenu.get_children()[2]),
                     lambda: data.b.ctxmenu.activate_item(data.b.ctxmenu.get_children()[2], False),
                     2,
                     lambda: rebuild(),
                     2,
                     lambda: data.b.update_display(),
                     2,
                     ]

        self.runloop(playback)
        #time.sleep(4)
        w.hide()

    def test_hidlayout (self):
        parent = self
        class KblayoutWindow (gtk.Window):
            def __init__ (self):
                gtk.Window.__init__(self)
                self.set_size_request(640, 480)
                self.resize(720, 680)
                self.layout = gtk.VBox()
                self.add(self.layout)

                kbl = hidlayout.KblayoutWidget(parent.ds)
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

        w = KblayoutWindow()
        w.show_all()
        playback = [ 3,
                     ]
        self.runloop(playback)
        w.hide()

    def test_change_vislayers (self):
        w = gtk.Window()
        w.set_title("Test HidTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = hidlayout.HidTop("K_TEST", self.ds)
        b.set_hidtop(self.inpdescr.get_label("K_TEST"))
        layout.pack_start(b, expand=False, fill=False, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        w.show_all()

        playback = [ lambda: None,
                     1,
                     lambda: self.inpdescr.set_label("K_TEST", "TEST"),
                     lambda: b.set_hidtop(self.inpdescr.get_label("K_TEST")),
                     lambda: self.assertEqual(b.inp_lbl.get_text(), "TEST"),
                     lambda: self.inpdescr.set_bind("K_TEST", "test_changer", 0, 0),
                     lambda: b.set_dispbinds(self.ds.resolve_bind_group_markup("K_TEST")),
                     2,
                     lambda: self.ds.set_vislayers(2),
                     lambda: b.update_display(),
                     2,
                     lambda: self.ds.set_vislayers(4),
                     lambda: b.update_display(),
                     2,
                     lambda: self.ds.set_vislayers(8),
                     lambda: b.update_display(),
                     2,
                     ]

        self.runloop(playback)
        self.assertEqual(b.inp_lbl.get_text(), "TEST")
        self.assertEqual(b.inp_binds[0].get_text(), "test_changer")
        self.assertEqual(self.ds.get_vislayers(), 8)
        self.assertEqual(b.vislayers, 8)
        self.assertTrue(b.lyr_lbls[1].get_visible())
        #time.sleep(4)
        w.hide()

    def test_change_layer (self):
        w = gtk.Window()
        w.set_title("Test HidTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = hidlayout.HidTop("K_TEST", self.ds)
        b.set_hidtop(self.inpdescr.get_label("K_TEST"))
        layout.pack_start(b, expand=False, fill=False, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        w.show_all()

        playback = [ lambda: None,
                     lambda: self.inpdescr.set_label("K_TEST", "TEST"),
                     lambda: b.set_hidtop(self.inpdescr.get_label("K_TEST")),
                     lambda: self.assertEqual(b.inp_lbl.get_text(), "TEST"),
                     lambda: self.inpdescr.set_bind("K_TEST", "test_changer", 0, 0),
                     lambda: b.set_dispbinds(self.ds.resolve_bind_group_markup("K_TEST")),
                     1,
                     lambda: self.ds.set_vislayers(2),
                     lambda: b.update_display(),
                     1,
                     lambda: self.ds.set_vislayers(4),
                     lambda: b.update_display(),
                     1,
                     lambda: self.ds.set_layer(3),
                     lambda: b.update_display(),
                     2,
                     ]

        self.runloop(playback)
        #time.sleep(4)
        w.hide()

    def test_hidlayout0 (self):
        kbkey= "en_US (pc104)"
        hiddesc = kbd_desc.KBD[kbkey]
        layout = hidlayout.HidLayoutStore(kbkey)
        layout.build_from_rowrun(hiddesc)
        flat = []
        for row in layout:
            flat.append( layout.get(row.iter, 0, 1, 2, 3, 4, 5, 6) )
        #print("flat = %r" % (flat,))
        self.assertTrue(('ESC', 'Esc', 'key', 0, 0, 6, 1) in flat)
        self.assertTrue(('UP', 'Up', 'key', 6, 12, 6, 1) in flat)
        self.assertEqual(layout.nrows, 14)
        self.assertEqual(layout.ncols, 87)

    def test_hidtop_signals (self):
        def on_nop (self, *args):
            pass
        w = gtk.Window()
        w.set_title("Test HidTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = hidlayout.HidTop("K_TEST", self.ds)
        b.set_hidtop(self.inpdescr.get_label("K_TEST"))
        layout.pack_start(b, expand=False, fill=False, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        #bb = hidlayout.HidBindable(None, None)
        #bb.connect("bind-assigned", on_nop)

        b.connect("bind-assigned", on_nop)

        w.show_all()

    def test_hidplanar_signals (self):
        def on_nop (self, *args):
            pass
        w = gtk.Window()
        w.set_title("Test HidTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = hidlayout.HidPlanar("L#", self.ds)
        #b.set_hidtop(self.inpdescr.get_label("K_TEST"))
        layout.pack_start(b, expand=False, fill=False, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        #bb = hidlayout.HidBindable(None, None)
        #bb.connect("bind-assigned", on_nop)

        b.connect("bind-assigned", on_nop)
        b.connect("cluster-type-changed", on_nop)

        w.show_all()


if __name__ == '__main__':
    unittest.main()

