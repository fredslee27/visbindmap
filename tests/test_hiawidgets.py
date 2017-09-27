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
        self.w = Gtk.Window(title="TestHiaWidget")
        return

    @staticmethod
    def main ():
        if __name__ == "__main__":
            unittest.main()

    def test_hiatop (self):
        hiatop = hialayout.HiaTop(self.hiaview, self.bindstore, "K_ESC")
        self.w.add(hiatop)
        self.bindstore.nlayers = 4
        self.hiaview.vislayers = [ True, True, True, True ]

        def script ():
            self.w.show_all()
            yield 1
            self.bindstore.set_bind(0,0,'K_ESC','crash-0')
            v = hiatop.binddisp[0].cmdtitle
            self.assertEqual(v, "crash-0")
            yield 1

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
        retval.append(None, ("KP_0", "0", "key",  0, 4, 1, 1))
        retval.append(None, ("KP_DECIMAL", ".", "key",  2, 4, 1, 1))
        return retval

    def _build_sample_binds1 (self, bindstore):
        bindstore.clear()
        bindstore.set_bind(0, 0, 'KP_8', 'Up')
        bindstore.set_bind(0, 0, 'KP_4', 'Left')
        bindstore.set_bind(0, 0, 'KP_6', 'Right')
        bindstore.set_bind(0, 0, 'KP_2', 'Down')
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
            yield 5

        self.runloop(script)
        self.w.destroy()


if __name__ == '__main__':
    unittest.main()

