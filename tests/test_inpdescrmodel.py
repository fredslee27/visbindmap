import unittest
import time

import hidlayout
import gobject
import gtk


class TestInpDescrModel(unittest.TestCase):
    def setUp (self):
        gtk.threads_init()
        self.inpdescr = hidlayout.InpDescrModel(8,8)
        self.ds = hidlayout.InpDisplayState(self.inpdescr)
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
    def test_bind_change (self):
        bindchanged = []
        def on_bindchange (w, *args):
            bindchanged.append(True)

        self.inpdescr.connect("bind-changed", on_bindchange)

        playback=[ lambda: self.ds.set_bind("K_ESCAPE", None),
                   ]

        self.runloop(playback)
        self.assertTrue(True in bindchanged)

    def test_layer_change (self):
        layerchanged = []
        def on_layerchange (w, *args):
            layerchanged.append(True)
        self.ds.connect("display-adjusted", on_layerchange)
        playback = [ lambda: self.ds.set_layer(2),
                     ]
        self.runloop(playback)
        self.assertTrue(True in layerchanged)
        self.assertEqual(self.ds.get_layer(), 2)


    def test_group_change (self):
        groupchanged = []
        def on_groupchange (w, *args):
            groupchanged.append(True)
        self.ds.connect("display-adjusted", on_groupchange)
        playback = [ lambda: self.ds.set_group(1),
                     ]
        self.runloop(playback)
        self.assertTrue(True in groupchanged)
        self.assertEqual(self.ds.get_group(), 1)


    def test_get_bind_via_implicit (self):
        bindchanged = []
        layerchanged = []
        groupchanged = []
        def on_bindchange (w, *args): bindchanged.append(True)
        def on_layerchange (w, *args): layerchanged.append(True)
        def on_groupchange (w, *args): groupchanged.append(True)
        self.inpdescr.connect("bind-changed", on_bindchange)
        self.ds.connect("display-adjusted", on_layerchange)
        self.ds.connect("display-adjusted", on_groupchange)
        playback = [ lambda: self.ds.set_group(1),
                     lambda: self.ds.set_layer(3),
                     lambda: self.ds.set_bind('K_ESCAPE', 'Quit'),
                     lambda: self.ds.set_group(2),
                     lambda: self.ds.set_bind('K_ESCAPE', 'NotQuit'),
                     ]
        self.runloop(playback)
        self.assertTrue(True in bindchanged)
        self.assertTrue(True in layerchanged)
        self.assertTrue(True in groupchanged)
        self.assertEqual(self.ds.get_group(), 2)
        self.assertEqual(self.ds.get_layer(), 3)
        self.assertEqual(self.ds.get_bind("K_ESCAPE"), 'NotQuit')
        self.assertEqual(self.ds.get_bind("K_ESCAPE", group=1, layer=3), 'Quit')

    def test_get_binds1 (self):
        playback = [ lambda: self.ds.set_bind('K_ESCAPE', 'Quit'),
                     lambda: self.ds.set_bind('K_ESCAPE', 'NotQuit', layer=1),
                     ]
        self.runloop(playback)
        self.assertEqual(self.ds.get_bind("K_ESCAPE", layer=0), 'Quit')
        self.assertEqual(self.ds.get_bind("K_ESCAPE", layer=1), 'NotQuit')
        self.assertEqual(self.ds.resolve_bind("K_ESCAPE", layer=0), (False, "Quit"))
        self.assertEqual(self.ds.resolve_bind("K_ESCAPE", layer=1), (False, "NotQuit"))

    def test_get_groupbind (self):
        self.inpdescr.set_bind("K_TEST", "_0", 0, 0)
        self.inpdescr.set_bind("K_TEST", "__1", 1, 1)
        self.inpdescr.set_bind("K_TEST", "__2", 1, 2)
        self.inpdescr.set_bind("K_TEST", "__3", 1, 3)
        self.inpdescr.set_bind("K_TEST", "__4", 1, 4)
        self.inpdescr.set_bind("K_TEST", "__5", 1, 5)
        self.inpdescr.set_bind("K_TEST", "__6", 1, 6)
        self.inpdescr.set_bind("K_TEST", "_7", 0, 7)
        self.inpdescr.set_bind("K_TEST", "___7", 2, 7)
        self.inpdescr.set_bind("K_TEST", "<<_6", 2, 6)
        a,b = self.ds.resolve_bind("K_TEST", 0, 0)

        self.assertEqual(a, False)
        self.assertEqual(b, "_0")

        g = self.ds.resolve_bind_group("K_TEST", 1)
        self.assertEqual(len(g), 8)
        self.assertEqual(g[0], (True, "_0"))
        self.assertEqual(g[1], (False, "__1"))
        self.assertEqual(g[2], (False, "__2"))
        self.assertEqual(g[3], (False, "__3"))
        self.assertEqual(g[7], (True, "_7"))

        g = self.ds.resolve_bind_group("K_TEST", 2)
        self.assertEqual(len(g), 8)
        self.assertEqual(g[0], (True, "_0"))
        self.assertEqual(g[7], (False, "___7"))

        gm = self.ds.resolve_bind_group_markup("K_TEST", 2)
        self.assertEqual(len(gm), 8)
        self.assertEqual(gm[0], "<i><small>_0</small></i>")
        self.assertEqual(gm[6], "&lt;&lt;_6")
        self.assertEqual(gm[7], "___7")

# TODO: test model failing:
# * change group to OOB
# * change layer to OOB




if __name__ == '__main__':
    unittest.main()

