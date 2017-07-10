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

        playback=[ lambda: x.set_bind(0, "K_ESCAPE", None),
                   ]

        self.runloop(playback)
        self.assertTrue(True in bindchanged)

#    @unittest.skip("skip kbtop")
    def test_kbtop (self):
        def on_bindchange(w, *args):
            pass
        mdl = kblayout.InpDescrModel(1)
        mdl.connect("bind-changed", on_bindchange)

        w = gtk.Window()
        w.set_title("Test KbTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = kblayout.KbTop("K_TEST", mdl)
        layout.pack_start(b, expand=False, fill=False, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        w.show_all()

        playback = [ lambda: None,
                     1,
                     lambda: mdl.set_label("K_TEST", "TEST"),
                     1,
                     lambda: mdl.set_bind(0, "K_TEST", "test_changer"),
                     2
                     ]

        self.runloop(playback)
        self.assertEqual(b.inp_lbl.get_text(), "TEST")
        #time.sleep(4)
        w.hide()

    def test_kbplanar (self):
        def on_bindchange(w, *args):
            pass
        mdl = kblayout.InpDescrModel(1)
        mdl.connect("bind-changed", on_bindchange)

        w = gtk.Window()
        w.set_title("Test KbTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = kblayout.KbPlanar("L", mdl)
        layout.pack_start(b, expand=False, fill=False, padding=0)
        lbl = gtk.Label("Testing...")
        layout.pack_start(lbl, expand=False, fill=True, padding=0)
        layout.pack_start(gtk.HBox(), expand=True, fill=True, padding=0)

        w.show_all()

        playback = [ lambda: None,
                     1,
                     lambda: mdl.set_label("Lu", "Lu"),
                     1,
                     lambda: mdl.set_bind(0, "Lu", "test_changer"),
                     2
                     ]

        self.runloop(playback)
        self.assertEqual(b.inp_lbl.get_text(), "TEST")
        #time.sleep(4)
        w.hide()

    def test_kbplanar_radial_calc (self):
        def on_bindchange(w, *args):
            pass
        mdl = kblayout.InpDescrModel(1)
        mdl.connect("bind-changed", on_bindchange)

        w = gtk.Window()
        w.set_title("Test KbTop")
        w.resize(640, 480)

        layout = gtk.VBox()
        w.add(layout)

        b = kblayout.KbPlanar("L", mdl)
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
                     1,
                     2
                     ]

        self.runloop(playback)
        self.assertEqual(b.inp_lbl.get_text(), "TEST")
        #time.sleep(4)
        w.hide()

    def test_kblayout (self):
        mdl = kblayout.InpDescrModel(1)
        class KblayoutWindow (gtk.Window):
            def __init__ (self):
                gtk.Window.__init__(self)
                self.set_size_request(640, 480)
                self.resize(720, 680)
                self.layout = gtk.VBox()
                self.add(self.layout)

                kbl = kblayout.KblayoutWidget(mdl)
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



if __name__ == '__main__':
    unittest.main()



