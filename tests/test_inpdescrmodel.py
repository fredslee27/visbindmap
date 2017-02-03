import unittest
import time

import kblayout
import gobject
import gtk


class TestInpDescrModel(unittest.TestCase):
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
    def test_bind_change (self):
        bindchanged = []
        def on_bindchange (w, *args):
            bindchanged.append(True)

        x = kblayout.InpDescrModel(8,8)
        x.connect("bind-changed", on_bindchange)

        playback=[ lambda: x.set_bind("K_ESCAPE", None),
                   ]

        self.runloop(playback)
        self.assertTrue(True in bindchanged)

    def test_layer_change (self):
        layerchanged = []
        def on_layerchange (w, *args):
            layerchanged.append(True)
        x = kblayout.InpDescrModel(8,8)
        x.connect("layer-changed", on_layerchange)
        playback = [ lambda: x.set_layer(2),
                     ]
        self.runloop(playback)
        self.assertTrue(True in layerchanged)
        self.assertEqual(x.get_layer(), 2)


    def test_group_change (self):
        groupchanged = []
        def on_groupchange (w, *args):
            groupchanged.append(True)
        x = kblayout.InpDescrModel(8,8)
        x.connect("group-changed", on_groupchange)
        playback = [ lambda: x.set_group(1),
                     ]
        self.runloop(playback)
        self.assertTrue(True in groupchanged)
        self.assertEqual(x.get_group(), 1)


    def test_get_bind_via_implicit (self):
        bindchanged = []
        layerchanged = []
        groupchanged = []
        def on_bindchange (w, *args): bindchanged.append(True)
        def on_layerchange (w, *args): layerchanged.append(True)
        def on_groupchange (w, *args): groupchanged.append(True)
        x = kblayout.InpDescrModel(8,8)
        x.connect("bind-changed", on_bindchange)
        x.connect("layer-changed", on_layerchange)
        x.connect("group-changed", on_groupchange)
        playback = [ lambda: x.set_group(1),
                     lambda: x.set_layer(3),
                     lambda: x.set_bind('K_ESCAPE', 'Quit'),
                     lambda: x.set_group(2),
                     lambda: x.set_bind('K_ESCAPE', 'NotQuit'),
                     ]
        self.runloop(playback)
        self.assertTrue(True in bindchanged)
        self.assertTrue(True in layerchanged)
        self.assertTrue(True in groupchanged)
        self.assertEqual(x.get_group(), 2)
        self.assertEqual(x.get_layer(), 3)
        self.assertEqual(x.get_bind("K_ESCAPE"), 'NotQuit')
        self.assertEqual(x.get_bind("K_ESCAPE", group=1, layer=3), 'Quit')

    def test_get_binds1 (self):
        x = kblayout.InpDescrModel(8,8)
        playback = [ lambda: x.set_bind('K_ESCAPE', 'Quit'),
                     lambda: x.set_bind('K_ESCAPE', 'NotQuit', layer=1),
                     ]
        self.runloop(playback)
        self.assertEqual(x.get_bind("K_ESCAPE", layer=0), 'Quit')
        self.assertEqual(x.get_bind("K_ESCAPE", layer=1), 'NotQuit')
        self.assertEqual(x.resolve_bind("K_ESCAPE", layer=0), (False, "Quit"))
        self.assertEqual(x.resolve_bind("K_ESCAPE", layer=1), (False, "NotQuit"))

# TODO: test model failing:
# * change group to OOB
# * change layer to OOB




if __name__ == '__main__':
    unittest.main()

