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

    def skel (self):
        layout = gtk.VBox()
        self.w.add(layout)

        layout.pack_start(WIDGET, True, True, 0)

        #w.show_all()
        self.w.show()
        layout.show()
        b.show()

        def script ():
            yield 1

        self.runloop(script)
        #time.sleep(4)
        self.w.hide()

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

        bindstore = hidlayout.BindStore(8,8)
        bv = hidlayout.BindableLayoutWidget(None, bindstore=bindstore)

        layout.add(bv)
        layout.show()
        bv.show()
        self.w.show()

        def script ():
            bv.ui.selectors.frob_layout(9)
            bv.ui.selectors.frob_layer(0)
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

    def test_bindcluster2 (self):
        # Test clustered layouts.
        cl = hidlayout.ClusteredLayout("TEST")
        self.assertIn("OneButton", [ x[0] for x in cl ])
        self.assertIsNotNone(cl[0])
        self.assertIsNotNone(cl["OneButton"])

    def test_nvislayers (self):
        # Test layer-visibility auto-calculation.
        layout = gtk.VBox()
        self.w.add(layout)

        bindstore = hidlayout.BindStore(8,8)
        bv = hidlayout.BindableLayoutWidget(None, bindstore=bindstore)

        layout.add(bv)
        layout.show()
        bv.show()
        self.w.show()

        def script ():
            bv.ui.selectors.frob_layout("PS3")
            yield 1

            bv.set_vis([True,True,True,True, False,False,False,False])
            hiatop = bv.ui.hidview.hiatops['B/8']
            bg0 = hiatop.ui.bg[0]
            yield 1
            self.assertEqual(bg0.usestyle, hiatop.refstyle.base)
            self.assertTrue(hiatop.ui.lyr[0].get_visible())
            self.assertTrue(hiatop.ui.lyr[0].get_visible())
            self.assertTrue(hiatop.ui.lyr[2].get_visible())
            self.assertTrue(hiatop.ui.lyr[3].get_visible())
            self.assertFalse(hiatop.ui.lyr[4].get_visible())
            self.assertFalse(hiatop.ui.lyr[5].get_visible())
            self.assertFalse(hiatop.ui.lyr[6].get_visible())
            self.assertFalse(hiatop.ui.lyr[7].get_visible())

            bv.set_layer(2)
            yield 1
            self.assertEqual(bg0.usestyle, hiatop.refstyle.bg)
            bg2 = hiatop.ui.bg[2]
            self.assertEqual(bg2.usestyle, hiatop.refstyle.base)

            bv.set_nvislayers(2)
            yield 1
            self.assertEqual(bg2.usestyle, hiatop.refstyle.base)
            self.assertFalse(hiatop.ui.lyr[0].get_visible())
            self.assertFalse(hiatop.ui.lyr[1].get_visible())
            self.assertTrue(hiatop.ui.lyr[2].get_visible())
            self.assertTrue(hiatop.ui.lyr[3].get_visible())
            self.assertFalse(hiatop.ui.lyr[4].get_visible())
            self.assertFalse(hiatop.ui.lyr[5].get_visible())
            self.assertFalse(hiatop.ui.lyr[6].get_visible())
            self.assertFalse(hiatop.ui.lyr[7].get_visible())

            bv.set_layer(7)
            yield 1
            bg7 = hiatop.ui.bg[7]
            self.assertEqual(bg7.usestyle, hiatop.refstyle.base)
            self.assertFalse(hiatop.ui.lyr[0].get_visible())
            self.assertFalse(hiatop.ui.lyr[1].get_visible())
            self.assertFalse(hiatop.ui.lyr[2].get_visible())
            self.assertFalse(hiatop.ui.lyr[3].get_visible())
            self.assertFalse(hiatop.ui.lyr[4].get_visible())
            self.assertFalse(hiatop.ui.lyr[5].get_visible())
            self.assertTrue(hiatop.ui.lyr[6].get_visible())
            self.assertTrue(hiatop.ui.lyr[7].get_visible())

            yield 5

        self.runloop(script, 1)
        self.w.hide()

    def test_bindrestore (self):
        layout = gtk.VBox()
        self.w.add(layout)

        bindstore = hidlayout.BindStore(8,8)
        bv = hidlayout.BindableLayoutWidget(None, bindstore=bindstore)

        bindstore2 = hidlayout.BindStore(8,8)
        bindstore2[0][0]['B/4'] = "Test1"

        layout.add(bv)
        layout.show()
        bv.show()
        self.w.show()

        def script ():
            bv.ui.selectors.frob_layout("PS3")
            yield 1

            bv.set_bindstore(bindstore2)

            yield 2

        print("bindstore=%r" % bindstore2)
        self.runloop(script, 1)
        self.w.hide()

    def test_bindarranger (self):
        layout = gtk.VBox()
        self.w.add(layout)

        bindstore = hidlayout.BindStore(8,8)
        bv = hidlayout.BindableLayoutWidget(None, bindstore=bindstore)

        layout.add(bv)
        layout.show()
        bv.show()
        self.w.show()

        def script ():
            bv.ui.selectors.frob_layout(9)
            bv.ui.selectors.frob_layer(0)
            yield 1

            bindstore[0][0]['LP#'] = "OneButton"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "ScrollWheel"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "DirectionPad"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "ButtonQuad"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "TrackPad"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "TouchMenu02"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "TouchMenu04"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "TouchMenu07"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "TouchMenu12"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "TouchMenu13"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "TouchMenu16"
            bv.ui.hidview.update_binds()
            yield 1

            yield 5

        self.runloop(script, 1)
        self.w.hide()

    def test_radialmenu (self):
        layout = gtk.VBox()
        self.w.add(layout)

        bindstore = hidlayout.BindStore(8,8)
        bv = hidlayout.BindableLayoutWidget(None, bindstore=bindstore)

        layout.add(bv)
        layout.show()
        bv.show()
        self.w.show()

        def script ():
            bv.ui.selectors.frob_layout(9)
            bv.ui.selectors.frob_layer(0)
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu01"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu02"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu03"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu04"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu05"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu06"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu07"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu08"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu09"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu10"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu11"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu12"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu13"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu14"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu15"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu16"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu17"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu18"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu19"
            bv.ui.hidview.update_binds()
            yield 1

            bindstore[0][0]['LP#'] = "RadialMenu20"
            bv.ui.hidview.update_binds()
            yield 1

            yield 5

        self.runloop(script, 1)
        self.w.hide()

    def test_bindlist0 (self):
        layout = gtk.HBox()
        self.w.add(layout)

        mdl_listmenu = gtk.ListStore(str,str,  str,str,str,str)
        mdl_listmenu.append(("K_TEST1", "K_TEST1", "test1", "testA", "t1", "tA"))
        mdl_listmenu.append(("K_TEST2", "K_TEST2", "test2", "testB", "t2", "tB"))
        mdl_listmenu.append(("K_TEST3", "K_TEST3", "test3", "testC", "t3", "tC"))
        mdl_listmenu.append(("K_TEST4", "K_TEST4", "test4", "testD", "t4", "tD"))
        bl = hidlayout.BindableListView(mdl_listmenu)
        layout.pack_start(bl, True, True, 0)

        #w.show_all()
        self.w.show()
        layout.show()
        bl.show()

        def script ():
            yield 1
            bl.set_layer(1)
            yield 5

        self.runloop(script, 1)
        #time.sleep(4)
        self.w.hide()

    def test_bindlistdnd0 (self):
        layout = gtk.HBox()
        self.w.add(layout)

        mdl_cmds = hidlayout.CommandPackStore()
        mdl_cmds.append(None, (1, "Action", "Action", ""))
        mdl_cmds.append(None, (2, "Jump", "Jump", ""))

        cmdview = hidlayout.CommandPackView(mdl_cmds)
        cmdview.show_all()

        b = hidlayout.BindableTop("K_TEST1", "K_TEST1", [True], ["test1"])
        b.show()

        mdl_listmenu = gtk.ListStore(str,str,  str,str,str,str)
        lu_listmenu = dict()
        lu_listmenu["K_TEST1"] = mdl_listmenu.append(("K_TEST1", "K_TEST1", "test1", "testA", "t1", "tA"))
        lu_listmenu["K_TEST2"] = mdl_listmenu.append(("K_TEST2", "K_TEST2", "test2", "testB", "t2", "tB"))
        lu_listmenu["K_TEST3"] = mdl_listmenu.append(("K_TEST3", "K_TEST3", "test3", "testC", "t3", "tC"))
        lu_listmenu["K_TEST4"] = mdl_listmenu.append(("K_TEST4", "K_TEST4", "test4", "testD", "t4", "tD"))
        bl = hidlayout.BindableListView(mdl_listmenu)

        vb = gtk.VBox()
        vb.add(cmdview)
        vb.add(b)
        vb.show()

        pane = gtk.HPaned()
        pane.add(vb)
        pane.add(bl)
        pane.show()
#        layout.pack_start(cmdview, False, False, 0)
        vb.set_size_request(150, -1)
#        layout.pack_start(bl, True, True, 0)
        layout.pack_start(pane, True, True, 0)

        #w.show_all()
        self.w.show()
        layout.show()
        bl.show()

        def on_bind_assigned (w, hiasym, bindval, *args):
            mdl_listmenu[lu_listmenu[hiasym]][2+w._layer] = bindval
            b.set_binds(tuple(mdl_listmenu[lu_listmenu[b.hiasym]])[2:])
        def on_bind_swapped (w, srcsym, dstsym, *args):
            colnum = 2+w._layer
            srcbind = mdl_listmenu[lu_listmenu[srcsym]][colnum]
            dstbind = mdl_listmenu[lu_listmenu[dstsym]][colnum]
            mdl_listmenu[lu_listmenu[srcsym]][colnum] = dstbind
            mdl_listmenu[lu_listmenu[dstsym]][colnum] = srcbind
            b.set_binds(tuple(mdl_listmenu[lu_listmenu[b.hiasym]])[2:])
        def on_bind_erased (w, hiasym, *args):
            mdl_listmenu[lu_listmenu[hiasym]][2+w._layer] = ""
            b.set_binds(tuple(mdl_listmenu[lu_listmenu[b.hiasym]])[2:])
        bl.connect("bind-assigned", on_bind_assigned)
        bl.connect("bind-swapped", on_bind_swapped)
        bl.connect("bind-erased", on_bind_erased)
        b.connect("bind-assigned", on_bind_assigned)
        b.connect("bind-swapped", on_bind_swapped)
        b.connect("bind-erased", on_bind_erased)

        def script ():
            yield 1
            #bl.set_layer(1)
            yield 8

        self.runloop(script, 1)
        #time.sleep(4)
        self.w.hide()



if __name__ == '__main__':
    unittest.main()

