# vim: set ai et ts=4 sw=4 :
import unittest
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib
import time

import skel
import hialayout


class TestSkel (skel.TestSkel):
    def setUp (self):
        return

    def test_bindstore (self):
        class box:
            a = 0
            a2 = 0
            v = None
        b = hialayout.BindStore()
        b.ngroups = 4
        self.assertEqual(len(b.groups), 4)
        def on_bind_changed (widget, hiasym, newtitle, newcode):
            box.a = True
            box.v = (newtitle, newcode)
        b.connect("bind-changed", on_bind_changed)

        def script():
            v = hialayout.BindValue("nop", "nop")
            s = repr(v)
            self.assertEqual(s, "BindValue(cmdtitle='nop', cmdcode='nop')")
            # set whole entry.
            b.set_bind(0, 0, 'K_a', 'wait'),
            yield 0.1
            # set entry field.
            b.groups[0][0]['K_a'].cmdcode = 'wait 2'
            self.assertEqual(box.v, ("wait", "wait 2"))
            yield 0.1
            l2 = hialayout.BindLayer(lambda k: None)
            l2['K_b'] = 'wait 0x66'
            b.groups[0].nlayers = 2
            b.groups[0][1] = l2
            self.assertEqual(box.v, ("wait 0x66", "wait 0x66"))

        self.runloop(script)
        self.assertNotEqual(box.a, 0)

    @staticmethod
    def main ():
        if __name__ == "__main__":
            unittest.main()



if __name__ == '__main__':
    unittest.main()

