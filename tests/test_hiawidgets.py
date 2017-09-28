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
        self.bindstore = hialayout.BindStore()
        self.hiaview = hialayout.HiaView(self.bindstore)
        self.all_layouts = hialayout.HiaLayouts()
        self.all_layouts.build_from_legacy_store()
        self.layouts0 = hialayout.HiaLayouts()
        self.layouts0.append(("(None)", None))
        self.layouts0.append(("keypad", self._build_sample_layout1()))
        self.w = Gtk.Window(title="TestHiaWidget")
        return

    @staticmethod
    def main ():
        if __name__ == "__main__":
            unittest.main()

    def _build_sample_binds0 (self, bindstore):
        bindstore.clear()
        bindstore.nlayers = 4
        bindstore.set_bind(0, 0, 'K_ESC', 'quit')
        return bindstore

    def test_hiatop (self):
        self.hiaview.vislayers = [ True, True, True, True ]
        self._build_sample_binds0(self.hiaview.bindstore)
        hiatop = hialayout.HiaTop(self.hiaview, "K_ESC")
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
        bindstore.nlayers = 2
        bindstore.set_bind(0, 0, 'KP_8', 'Up')
        bindstore.set_bind(0, 0, 'KP_4', 'Left')
        bindstore.set_bind(0, 0, 'KP_6', 'Right')
        bindstore.set_bind(0, 0, 'KP_2', 'Down')

        bindstore.set_bind(0, 1, 'KP_8', '8')
        bindstore.set_bind(0, 1, 'KP_4', '4')
        bindstore.set_bind(0, 1, 'KP_6', '6')
        bindstore.set_bind(0, 1, 'KP_2', '2')
        return bindstore

    def test_hiasurface (self):
        layouts = hialayout.HiaLayouts()
        layouts.build_from_legacy_store()
        self._build_sample_binds1(self.hiaview.bindstore)
        hiasurface = hialayout.HiaSurface(self.hiaview)
        #hiasurface.layout = layouts['en_US (pc104)'][1]
        hiasurface.layout = self._build_sample_layout1()

        self.w.add(hiasurface)

        def script ():
            self.w.show_all()
            yield 1

            ch = hiasurface.children['KP_8']
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

        hiacluster = hialayout.HiaCluster(self.hiaview, "CL#")
        #hiacluster.set_layout(layouts['en_US (pc104)'][1])
        self.bindstore.set_bind(0,0,'CL','OneButton')

        self.w.add(hiacluster)

        def script ():
            self.w.show_all()
            yield 5

        self.runloop(script)
        self.w.destroy()

    def test_hiaselectors (self):
        sel = hialayout.HiaSelector('Generic', self.hiaview, ['one', 'two', 'three'])
        grpsel = hialayout.HiaSelectorGroup(self.hiaview, ['Menu', 'Game'])
        lyrsel = hialayout.HiaSelectorLayer(self.hiaview, ['0', '1', '2', '3'])
        devsel = hialayout.HiaSelectorDevice(self.hiaview, self.all_layouts)
        box = Gtk.VBox()
        box.pack_start(sel, False, False, 0)
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
            devsel.ui.dropbox.popup()
            yield 0.5
            devsel.ui.dropbox.set_active(4)
            yield 0.5
            devsel.ui.dropbox.popdown()
            self.assertEqual(self.hiaview.device, "SteamController")
            self.assertEqual(box.ddev, 1)
            yield 1

        self.runloop(script)
        self.w.destroy()

    def test_hiapicker (self):
        #self.hiaview.bindstore.nlayers = 2
        self.hiaview.vislayers = [ True, False ]
        self._build_sample_binds1(self.hiaview.bindstore)
        picker = hialayout.HiaPicker(self.hiaview, self.layouts0)
        picker.ui.sel_layer.set_names(['base', '1'])
        self.w.add(picker)

        def script ():
            self.w.show()
            yield 1
            picker.ui.sel_device.ui.dropbox.set_active(1)
            self.assertEqual(self.hiaview.device, "keypad")
            probe = picker.ui.sel_bind.get_child_at(0,2)
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


if __name__ == '__main__':
    unittest.main()

