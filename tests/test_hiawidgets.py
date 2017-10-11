# vim: set ai et ts=4 sw=4 :
import unittest
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib
import time

import skel
import hialayout


class TestHiaWidgets (skel.TestSkel):
    def setUp (self):
        #GObject.threads_init()  # earlier python may need this.
        self.all_layouts = hialayout.HiaLayouts()
        self.all_layouts.build_from_legacy_store()
        self.bindstore = hialayout.BindStore()
        self.layouts0 = hialayout.HiaLayouts()
        self.layouts0.append(("(None)", None))
        self.layouts0.append(("keypad", self._build_sample_layout1()))
        #self.hiaview = hialayout.HiaView(self.bindstore, self.all_layouts)
        self.hiaview = hialayout.HiaView(self.bindstore, self.layouts0)
        #self.controller = hialayout.HiaControl(self.hiaview)
        self.controller = hialayout.AppControl(self.hiaview)
        self.w = Gtk.Window(title="TestHiaWidget")
        self.controller.insert_actions_into_widget(self.w)
        return

    @staticmethod
    def main ():
        if __name__ == "__main__":
            unittest.main()

    def _build_sample_binds0 (self, bindstore):
        bindstore.clear_bindstore()
        #bindstore.nlayers = 4
        bindstore.add_layer()
        bindstore.add_layer()
        bindstore.add_layer()
        bindstore.set_bind(0, 0, 'K_ESC', 'quit')
        return bindstore

    def test_hiaview (self):
        class box:
            vislayers_delta = 0
        def on_vislayers_changed (w, vislayers):
            box.vislayers_delta += 1
        def on_device_changed (w, devid):
            pass
        def on_group_changed (w, groupid):
            pass
        def on_layer_changed (w, groupid, layerid):
            pass
        def on_bind_changed (w, hiasym, newtitle, newcode):
            pass

        self.hiaview.connect("vislayers-changed", on_vislayers_changed)

        def script ():
            self.hiaview.vislayers = [ True, True, True, True ]
            yield 0.1
            self.assertEqual(len(self.hiaview.vislayers), 4)
            self.assertEqual(self.hiaview.vislayers, [True,True,True,True])

        self.runloop(script)

    def test_hiatop (self):
        self.hiaview.vislayers = [ True, True, True, True ]
        self._build_sample_binds0(self.hiaview.bindstore)
        hiatop = hialayout.HiaTop(self.controller, "K_ESC")
        self.w.add(hiatop)
        #self.bindstore.nlayers = 4

        def script ():
            self.w.show_all()
            yield 1

            self.bindstore.set_bind(0,0,'K_ESC','crash-0')
            v = hiatop.binddisp[0].cmdtitle
            v = self.bindstore.get_bind(0,0,'K_ESC').cmdtitle
            self.assertEqual(v, "crash-0")
            yield 1

            self.bindstore.set_bind(0,0,'K_ESC','crash--0')
            v = hiatop.binddisp[0].cmdtitle
            self.assertEqual(v, "crash--0")
            yield 0.5

        self.runloop(script)
        self.w.destroy()

    def _build_sample_layout1 (self):
        retval = hialayout.HiaLayoutStore("sample1")
        retval.append(None, ("NUMLK", "N.L.", "key",  0, 0, 1, 1))
        retval.append(None, ("KP_DIVIDE", "/", "key",  1, 0, 1, 1))
        retval.append(None, ("KP_MULTIPLY", "*", "key",  2, 0, 1, 1))
        retval.append(None, ("KP_MINUS", "-", "key",  3, 0, 1, 1))
        retval.append(None, ("KP_7", "7", "key",  0, 1, 1, 1))
        retval.append(None, ("KP_8", "8", "key",  1, 1, 1, 1))
        retval.append(None, ("KP_9", "9", "key",  2, 1, 1, 1))
        retval.append(None, ("KP_ADD", "+", "key",  3, 1, 1, 2))
        retval.append(None, ("KP_4", "4", "key",  0, 2, 1, 1))
        retval.append(None, ("KP_5", "5", "key",  1, 2, 1, 1))
        retval.append(None, ("KP_6", "6", "key",  2, 2, 1, 1))
        retval.append(None, ("KP_1", "1", "key",  0, 3, 1, 1))
        retval.append(None, ("KP_2", "2", "key",  1, 3, 1, 1))
        retval.append(None, ("KP_3", "3", "key",  2, 3, 1, 1))
        retval.append(None, ("KP_ENTER", "ENTER", "key",  3, 3, 1, 2))
        retval.append(None, ("KP_0", "0", "key",  0, 4, 2, 1))
        retval.append(None, ("KP_DECIMAL", ".", "key",  2, 4, 1, 1))
        return retval

    def _build_sample_binds1 (self, bindstore):
        bindstore.clear()
        #bindstore.nlayers = 2
        bindstore.add_layer("1")
        bindstore.set_bind(0, 0, 'KP_8', 'Up')
        bindstore.set_bind(0, 0, 'KP_4', 'Left')
        bindstore.set_bind(0, 0, 'KP_6', 'Right')
        bindstore.set_bind(0, 0, 'KP_2', 'Down')

        bindstore.set_bind(0, 1, 'KP_8', '8')
        bindstore.set_bind(0, 1, 'KP_4', '4')
        bindstore.set_bind(0, 1, 'KP_6', '6')
        bindstore.set_bind(0, 1, 'KP_2', '2')

        bindstore.set_bind(0, 0, 'CL#u', 'Up')
        bindstore.set_bind(0, 0, 'CL#d', 'Down')
        bindstore.set_bind(0, 0, 'CL#l', 'Left')
        bindstore.set_bind(0, 0, 'CL#r', 'Right')
        bindstore.set_bind(0, 0, 'CL#c', 'Return')

        bindstore.set_bind(0, 0, 'CL#1', 'Return')
        bindstore.set_bind(0, 0, 'CL#2', 'Return')
        bindstore.set_bind(0, 0, 'CL#3', 'Return')
        bindstore.set_bind(0, 0, 'CL#4', 'Return')
        bindstore.set_bind(0, 0, 'CL#5', 'Return')
        bindstore.set_bind(0, 0, 'CL#6', 'Return')
        bindstore.set_bind(0, 0, 'CL#7', 'Return')
        bindstore.set_bind(0, 0, 'CL#8', 'Return')
        bindstore.set_bind(0, 0, 'CL#9', 'Return')
        bindstore.set_bind(0, 0, 'CL#10', 'Return')
        bindstore.set_bind(0, 0, 'CL#11', 'Return')
        bindstore.set_bind(0, 0, 'CL#12', 'Return')
        bindstore.set_bind(0, 0, 'CL#13', 'Return')
        bindstore.set_bind(0, 0, 'CL#14', 'Return')
        bindstore.set_bind(0, 0, 'CL#15', 'Return')
        bindstore.set_bind(0, 0, 'CL#16', 'Return')
        bindstore.set_bind(0, 0, 'CL#17', 'Return')
        bindstore.set_bind(0, 0, 'CL#18', 'Return')
        bindstore.set_bind(0, 0, 'CL#19', 'Return')
        bindstore.set_bind(0, 0, 'CL#20', 'Return')

        return bindstore

    def test_hiasurface (self):
        layouts = hialayout.HiaLayouts()
        layouts.build_from_legacy_store()
        self._build_sample_binds1(self.hiaview.bindstore)
        hiasurface = hialayout.HiaSelectorSym(self.controller)
        #hiasurface.layout = layouts['en_US (pc104)'][1]
        hiasurface.layout = self._build_sample_layout1()

        self.w.add(hiasurface)

        def script ():
            self.w.show_all()
            yield 1

            ch = hiasurface.hiachildren['KP_8']
            bt = ch
            v = bt.binddisp[0].cmdtitle
            self.assertEqual(v, "Up")
            yield 2

        self.runloop(script)
        self.w.destroy()

    def test_hiacluster (self):
        layouts = hialayout.HiaLayouts()
        layouts.build_from_legacy_store()
        self._build_sample_binds1(self.hiaview.bindstore)
        #self.hiaview.vislayers = [ True, False ]

        hiacluster = hialayout.HiaCluster(self.controller, "CL#")
        #hiacluster.set_layout(layouts['en_US (pc104)'][1])
        self.bindstore.set_bind(0,0,'CL#','OneButton')

        self.w.add(hiacluster)

        def script ():
            self.w.show_all()
            yield 1
            hiacluster.ui.frame_arranger.set_use_popover(False)
            hiacluster.ui.frame_arranger.clicked()
            yield 0.2
            menu = hiacluster.ui.frame_arranger.get_property("popup")
            menu.set_active(4)  # ButtonQuad
            menuitem = menu.get_active()
            menuitem.activate()
            yield 0.2
            menu.popdown()
            hiacluster.ui.frame_arranger.clicked()
            occupied_scan = [ (0,0), (0,1), (0,2),
                              (1,0), (1,1), (1,2),
                              (2,0), (2,1), (2,2), ]
            occupied_report = [ bool(hiacluster.ui.sel_sym.ui.grid.get_child_at(x,y)) for (x,y) in occupied_scan ]
            self.assertTrue(occupied_report, [ False,True,False,  True,False,True,  False,True,False ])
            yield 2

        self.runloop(script)
        self.w.destroy()

    def test_hialist (self):
        layouts = hialayout.HiaLayouts()
        layouts.build_from_legacy_store()
        self._build_sample_binds1(self.hiaview.bindstore)
        #self.hiaview.vislayers = [ True, False ]

        hiacluster = hialayout.HiaCluster(self.controller, "CL#")
        #self.bindstore.set_bind(0,0,'CL#','RadialMenu10')
        self.bindstore.set_bind(0,0,'CL#','Joystick')

        self.w.add(hiacluster)

        def script ():
            self.w.set_size_request(200,200)
            self.w.show_all()
            yield 2
            hiacluster.ui.sel_sym.set_visible_child_name("tabular")
            self.bindstore.set_bind(0,0,'CL#','RadialMenu10')
            yield 5

        self.runloop(script)
        self.w.destroy()

    def test_hiaselectors (self):
        self.hiaview.layouts = self.all_layouts

        self.bindstore.add_group("Menu")
        self.bindstore.add_group("Game")
        self.bindstore.add_layer("1")
        self.bindstore.add_layer("2")
        self.bindstore.add_layer("3")

        gensel = hialayout.HiaSelectorRadio('Generic', self.controller)
        gensel.get_axislist = lambda: [ (0,'','one','',None), (0,'','two','',None), (0,'','three','',None) ]
        gensel.update_widgets()

        grpsel = hialayout.HiaSelectorGroup(self.controller)
        lyrsel = hialayout.HiaSelectorLayer(self.controller)
        devsel = hialayout.HiaSelectorDevice(self.controller)
        box = Gtk.VBox()
        box.pack_start(gensel, False, False, 0)
        box.pack_start(grpsel, False, False, 0)
        box.pack_start(lyrsel, False, False, 0)
        box.pack_start(devsel, False, False, 0)
        self.w.add(box)

        class box:
            ddev = 0
            dgrp = 0
            dlyr = 0

        def on_device_changed (self, newdev):
            box.ddev += 1

        def on_group_changed (self, newgrp):
            box.dgrp += 1

        def on_layer_changed (self, newlyr):
            box.dlyr += 1

        self.hiaview.connect("device-changed", on_device_changed)
        self.hiaview.connect("group-changed", on_group_changed)
        self.hiaview.connect("layer-changed", on_layer_changed)

        def script ():
            self.w.show_all()
            self.assertEqual(len(grpsel.buttons), 3)
            yield 0.1
            #print("to use group 1")
            grpsel.buttons[1].clicked()
            self.assertEqual(self.hiaview.group, 1)
            self.assertEqual(box.dgrp, 1)
            yield 0.1
            #print("to use group 0")
            grpsel.buttons[0].clicked()
            self.assertEqual(self.hiaview.group, 0)
            self.assertEqual(box.dgrp, 2)
            yield 0.1
            #print("to use layer 2")
            lyrsel.buttons[2].clicked()
            self.assertEqual(self.hiaview.layer, 2)
            self.assertEqual(box.dlyr, 1)
            yield 0.5
            devsel.ui.inp_dev.popup()
            yield 0.5
            devsel.ui.inp_dev.set_active(4)
            yield 0.5
            devsel.ui.inp_dev.popdown()
            self.assertEqual(self.hiaview.device_name, "SteamController")
            self.assertEqual(box.ddev, 1)
            dd = self.hiaview.device_details
            self.assertTrue(len(dd) > 1)
            yield 0.5
            # Ensure widget updates based on setting plan model.
            self.hiaview.layer = 1
            self.assertTrue(lyrsel.buttons[1].get_active())
            yield 0.5
            # Expand layers.
            #self.hiaview.bindstore.nlayers = 8
            #while self.hiaview.bindstore.nlayers < 8:
            #    self.hiaview.bindstore.add_layer()
            #self.hiaview.bindstore.add_layershifter()
            self.controller.add_layershifter()
            yield 0.1
            self.assertEqual(len(lyrsel.buttons), 8)
            self.assertEqual(lyrsel.labels[7].get_label(), "7 (^1 + ^2 + ^3)")
            yield 0.1
            self.assertEqual(self.hiaview.layer, 1)
            self.assertTrue(lyrsel.buttons[1].get_active())
            yield 1

        self.runloop(script)
        self.w.destroy()

    def test_hiaplanner (self):
        self.hiaview.layouts = self.layouts0
        #self.hiaview.bindstore.nlayers = 2
        self.hiaview.bindstore.add_layer("1",None)
        self.hiaview.vislayers = [ True, False ]
        self._build_sample_binds1(self.hiaview.bindstore)
        picker = hialayout.HiaPlanner(cmdpack=None, controller=self.controller)
        self.w.add(picker)
        self.w.set_size_request(640, 480)

        def script ():
            self.w.show()
            yield 1
            picker.ui.sel_device.ui.inp_dev.set_active(1)
            self.assertEqual(self.hiaview.device_name, "keypad")
            probe = picker.ui.sel_sym.ui.grid.get_child_at(0,2)
            self.assertIsNotNone(probe)
            self.assertEqual(probe.hiasym, "KP_4")
            yield 1
            self.hiaview.bindstore.nlayers = 4
            self.hiaview.vislayers = [ True, True, True, True ]
            yield 1
            self.hiaview.bindstore.nlayers = 2
            self.hiaview.vislayers = [ True, True ]
            yield 2

        self.runloop(script)
        self.w.destroy()

    def test_hiaactions (self):
        self.hiaview.layouts = self.layouts0
        self.hiaview.vislayers = [ True, False ]
        self._build_sample_binds1(self.hiaview.bindstore)
        picker = hialayout.HiaPlanner(cmdpack=None, controller=self.controller)
        self.w.add(picker)
        self.w.set_size_request(640, 480)
        controller = picker.controller

        def script ():
            self.w.show()
            yield 0.2
            controller.assign_bind_explicit(0,0,'K_ESC','quit','quit')
            yield 1

        self.runloop(script)
        self.w.destroy()

    def test_hiaplanner2 (self):
        self.hiaview.layouts = self.all_layouts
        self.hiaview.bindstore.add_layer("1",None)
        self.hiaview.vislayers = [ True, False ]
        self._build_sample_binds1(self.hiaview.bindstore)
        picker = hialayout.HiaPlanner(cmdpack=None, controller=self.controller)
        self.w.add(picker)
        self.w.set_size_request(640, 480)

        def script ():
            self.w.show()
            yield 0.2
            self.controller.pick_device('PS4/Steam')
            self.controller.view.bindstore.set_bind(0,0,'DP#','Joystick')
            self.controller.load_commandpack("cmdset/KerbalSpaceProgram.sqlite3")
            action = self.controller.actions.lookup_action("view_bindlist__DP#")
            action.activate()
            yield 5

        self.runloop(script)
        self.w.destroy()



if __name__ == '__main__':
    unittest.main()

