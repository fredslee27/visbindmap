import unittest
import time

import kblayout
import gobject
import gtk


class TestKblayout(unittest.TestCase):
    def setUp (self):
        gtk.threads_init()
        pass


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


#    @unittest.skip("skip models")
    def test_models (self):
        bindchanged = []
        def on_bindchange (w, *args):
            bindchanged.append(True)

        x = kblayout.InpDescrModel(1)
        x.connect("bind-changed", on_bindchange)

        playback=[ lambda: x.set_bind(0, "K_ESCAPE", 0, 0),
                   ]

        self.runloop(playback)
        self.assertTrue(True in bindchanged)

#    @unittest.skip("skip kbtop")
    def test_kbtop (self):
        def on_bindchange(w, *args):
            pass
        mdl = kblayout.InpDescrModel(1)
        mdl.connect("bind-changed", on_bindchange)
        ds = kblayout.InpDisplayState(mdl)

        w = gtk.Window()
        w.set_title("Test KbTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = kblayout.KbTop("K_TEST", ds)
        layout.pack_start(b, expand=False, fill=False, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        w.show_all()

        playback = [ lambda: None,
                     1,
                     lambda: mdl.set_label("K_TEST", "TEST"),
                     1,
                     lambda: mdl.set_bind("K_TEST", "test_changer", 0, 0),
                     2
                     ]

        self.runloop(playback)
        self.assertEqual(b.inp_lbl.get_text(), "TEST")
        self.assertEqual(b.inp_binds[0].get_text(), "test_changer")
        #time.sleep(4)
        w.hide()

    def test_kbplanar (self):
        def on_bindchange(w, *args):
            pass
        mdl = kblayout.InpDescrModel(1)
        mdl.connect("bind-changed", on_bindchange)
        ds = kblayout.InpDisplayState(mdl)

        w = gtk.Window()
        w.set_title("Test KbTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = kblayout.KbPlanar("L", ds)
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

    def test_kbplanar_radial_calc (self):
        def on_bindchange(w, *args):
            pass
        mdl = kblayout.InpDescrModel(1)
        mdl.connect("bind-changed", on_bindchange)
        ds = kblayout.InpDisplayState(mdl)

        w = gtk.Window()
        w.set_title("Test KbTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = kblayout.KbPlanar("L", ds)
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

    def test_kbplanar_ctxmenu (self):
        def on_bindchange(w, *args):
            pass
        mdl = kblayout.InpDescrModel(1)
        mdl.connect("bind-changed", on_bindchange)
        ds = kblayout.InpDisplayState(mdl)

        w = gtk.Window()
        w.set_title("Test KbTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = kblayout.KbPlanar("L", ds)
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

    def test_kbplanar_persist (self):
        def on_bindchange(w, *args):
            pass
        mdl = kblayout.InpDescrModel(1)
        mdl.connect("bind-changed", on_bindchange)
        ds = kblayout.InpDisplayState(mdl)

        w = gtk.Window()
        w.set_title("Test KbTop")
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
            data.b = kblayout.KbPlanar("L", ds)
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

    def test_kblayout (self):
        mdl = kblayout.InpDescrModel(1)
        ds = kblayout.InpDisplayState(mdl)
        class KblayoutWindow (gtk.Window):
            def __init__ (self):
                gtk.Window.__init__(self)
                self.set_size_request(640, 480)
                self.resize(720, 680)
                self.layout = gtk.VBox()
                self.add(self.layout)

                kbl = kblayout.KblayoutWidget(ds)
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
        mdl = kblayout.InpDescrModel(1,8)
        ds = kblayout.InpDisplayState(mdl)

        w = gtk.Window()
        w.set_title("Test KbTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = kblayout.KbTop("K_TEST", ds)
        layout.pack_start(b, expand=False, fill=False, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        w.show_all()

        playback = [ lambda: None,
                     1,
                     lambda: mdl.set_label("K_TEST", "TEST"),
                     1,
                     lambda: mdl.set_bind("K_TEST", "test_changer", 0, 0),
                     2,
                     lambda: ds.set_vislayers(2),
                     2
                     ]

        self.runloop(playback)
        self.assertEqual(b.inp_lbl.get_text(), "TEST")
        self.assertEqual(b.inp_binds[1].get_text(), "test_changer")
        self.assertEqual(ds.get_vislayers(), 2)
        self.assertEqual(b.vislayers, 2)
        #time.sleep(4)
        w.hide()



if __name__ == '__main__':
    unittest.main()



