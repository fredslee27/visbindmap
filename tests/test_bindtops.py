import unittest
import time

import hidlayout
import kbd_desc
import gobject
import gtk


class TestBindtops(unittest.TestCase):
    def setUp (self):
        gtk.threads_init()
        self.bindstore = hidlayout.BindStore(8,8)
        self.w = gtk.Window()
        self.w.set_title(self.__class__.__name__)
        self.w.resize(640, 480)


    def runloop (self, script=lambda: 0, pause_scale=0.1):
        """Run test script, coded as a coroutine.
Coroutine yield()s number of seconds to pause; gtk event handler runs during the script pause.
Loop ends when coroutine ends (uses return instead of yield)
"""
        phase = 0
        for pauselen in script():
            self.w.set_title("{} #{}".format(self.__class__.__name__, phase))
            t = time.time()
            timegate = t + (pauselen * pause_scale)
            while t <= timegate:
                while gtk.events_pending():
                    gtk.main_iteration_do(block=False)
                t = time.time()
            phase += 1


    def test_bindtop (self):
        layout = gtk.VBox()
        self.w.add(layout)

        vis = [True] + [ False ] * 3
        b = hidlayout.BindableTop("K_TEST", "K_TEST", vis)
        b.set_layer(0)
        layout.pack_start(b, True, True, 0)
        #b.set_vis([True, True, True, True])

        #w.show_all()
        self.w.show()
        layout.show()
        b.show()

        def script ():
            self.assertEqual(b.ui.lbl.get_text(), "K_TEST")
            self.assertFalse(b.ui.lyr[0].get_visible())
            self.assertFalse(b.ui.lyr[1].get_visible())
            self.assertFalse(b.ui.lyr[2].get_visible())
            self.assertFalse(b.ui.lyr[3].get_visible())
            self.assertTrue(b.ui.rows[0].get_visible())
            self.assertFalse(b.ui.rows[1].get_visible())
            self.assertFalse(b.ui.rows[2].get_visible())
            self.assertFalse(b.ui.rows[3].get_visible())
            self.assertFalse(b.ui.hrules[1].get_visible())
            self.assertFalse(b.ui.hrules[2].get_visible())
            self.assertFalse(b.ui.hrules[3].get_visible())
            yield 2
            b.set_vis([True, True, True, True])
            self.assertEqual(len(b.ui.lyr), 4)
            self.assertEqual(b.nlayers, 4)
            self.assertTrue(b.ui.lyr[0].get_visible())
            self.assertTrue(b.ui.lyr[1].get_visible())
            self.assertTrue(b.ui.lyr[2].get_visible())
            self.assertTrue(b.ui.lyr[3].get_visible())
            self.assertTrue(b.ui.rows[0].get_visible())
            self.assertTrue(b.ui.rows[1].get_visible())
            self.assertTrue(b.ui.rows[2].get_visible())
            self.assertTrue(b.ui.rows[3].get_visible())
            self.assertTrue(b.ui.hrules[1].get_visible())
            self.assertTrue(b.ui.hrules[2].get_visible())
            self.assertTrue(b.ui.hrules[3].get_visible())
            yield 1
            b.set_layer(1)
            yield 1
            b.set_layer(2)
            yield 2
            b.set_vis([True, False, False, False])
            b.set_layer(0)
            self.assertTrue(b.ui.rows[0].get_visible())
            self.assertFalse(b.ui.lyr[0].get_visible())
            self.assertFalse(b.ui.lyr[1].get_visible())
            self.assertFalse(b.ui.lyr[2].get_visible())
            self.assertFalse(b.ui.lyr[3].get_visible())
            self.assertTrue(b.ui.rows[0].get_visible())
            self.assertFalse(b.ui.rows[1].get_visible())
            self.assertFalse(b.ui.rows[2].get_visible())
            self.assertFalse(b.ui.rows[3].get_visible())
            self.assertFalse(b.ui.hrules[1].get_visible())
            self.assertFalse(b.ui.hrules[2].get_visible())
            self.assertFalse(b.ui.hrules[3].get_visible())
            yield 2
            b.set_toplabel("K_TEST_2")
            yield 2
            self.assertEqual(b.ui.lbl.get_text(), "K_TEST_2")
            yield 2
            b.set_binds(['do_1', 'do_2', 'do_3', 'do_4'])
            self.assertEqual([r.get_visible() for r in b.ui.rows], [ True, False, False, False ])
            yield 2
            b.set_vis([True, True, True, True])
            yield 2
            b.set_layer(6)
            yield 4
            return

        self.runloop(script)
        #time.sleep(4)
        self.w.hide()


    def test_bindlist (self):
        layout = gtk.VBox()
        self.w.add(layout)

        vis = [ True, False, False, False ]
        bb = [
          hidlayout.BindableTop("K_TEST1", None, vis),
          hidlayout.BindableTop("K_TEST2", None, vis),
          hidlayout.BindableTop("K_TEST3", None, vis),
          hidlayout.BindableTop("K_TEST4", None, vis),
          ]
        self.assertEqual(bb[0].vis, [ True, False, False, False ])
        v = hidlayout.BindableListView(bb)
        bb[0].set_layer(0)
        for x in bb:
            x.set_vis([True, True, True, True])
        layout.pack_start(v, True, True, 0)
        self.assertEqual(v.layer, 0)

        self.w.show()
        layout.show()
        v.show()

        def script ():
            v.update_layer()
            yield 1
            bb[0].set_layer(1)
            v.update_layer()
            yield 1
            bb[0].set_vis([True, False, False, False])
            v.update_vis()
            yield 1
            bb[0].set_vis([False, False, True, False])
            v.update_vis()
            yield 2
            return

        self.runloop(script, 1)
        self.w.hide()

    def test_bindcluster0 (self):
        # Test as top-level hiacluster.
        layout = gtk.VBox()
        self.w.add(layout)
        vis = (True,) + (False,)*7
        bc = hidlayout.BindableCluster("NEOGEO#", "NEOGEO#", vis, [])
        mdl = hidlayout.HidLayoutStore("test")
        mdl.append(None, ("A", "A", "key", 0, 3, 3, 3))
        mdl.append(None, ("B", "B", "key", 3, 0, 3, 3))
        mdl.append(None, ("C", "C", "key", 6, 0, 3, 3))
        mdl.append(None, ("D", "D", "key", 9, 0, 3, 3))
        bc.set_layoutmap(mdl)

        layout.add(bc)
        layout.show()
        self.w.show()

        def script ():
            yield 1
            bc.set_vis([True,True,True,True,False,False,False,False])
            #bc.set_layer(1)
            yield 1
            bc.set_layer(3)
            bc.set_vis([False,False,False,True,False,False,False,False])
            yield 2

        self.runloop(script, 1)
        self.w.hide()

    def test_bindcluster1 (self):
        # Test as top-level hiacluster.
        layout = gtk.VBox()
        self.w.add(layout)
        vis = (True,) + (False,)*7
        bc = hidlayout.BindableCluster("", "", vis, [])
#        mdl = hidlayout.HidLayoutStore("test")
#        mdl.build_from_rowrun(kbd_desc.KBD['en_US (pc104)'])
        mdl = hidlayout.implicit_layouts['en_US (pc104)']
        bc.set_layoutmap(mdl)

        layout.add(bc)
        layout.show()
        self.w.show()

        def script ():
            yield 5

        self.runloop(script, 1)
        self.w.hide()

    def test_bindwidget (self):
        layout = gtk.VBox()
        self.w.add(layout)

        bv = hidlayout.BindableLayoutWidget(None)

        layout.add(bv)
        layout.show()
        bv.show()
        self.w.show()

        def script ():
            yield 1
            bv.ui.sel_layout.set_active(2)
            bv.ui.sel_layer.buttons[1].activate()
            yield 5

        self.runloop(script, 1)
        self.w.hide()

    def test_changegroup (self):
        layout = gtk.VBox()
        self.w.add(layout)

        self.bindstore = hidlayout.BindStore(2,4)
        for hiasym in [ "B/%d"%x for x in range(0,12) ]:
            for gn in range(0, 2):
                for lyr in range(0,4):
                    hiabind = "%s_g%dl%d" % (hiasym, gn, lyr)
                    self.bindstore[gn][lyr][hiasym] = hiabind
        #print("bindstore = %s" % (self.bindstore,))

        bv = hidlayout.BindableLayoutWidget(None, None, self.bindstore)

        layout.add(bv)
        layout.show()
        bv.show()
        self.w.show()

        def script ():
            yield 1
            bv.ui.sel_layout.set_active(2)  # layout2
            yield 1
            bv.ui.sel_layer.buttons[1].activate()  #Layer1
            yield 1
            bv.ui.sel_group.buttons[1].activate()  #Group1
            yield 1
            bv.ui.sel_layer.buttons[2].activate()  #Layer2
            yield 9

        self.runloop(script, 1)
        self.w.hide()




if __name__ == '__main__':
    unittest.main()

