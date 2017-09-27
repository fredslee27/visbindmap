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

    def test_reprs (self):
        # Test repr() and serialization.
        v = hialayout.BindValue("nop", "nop")
        r = repr(v)
        self.assertEqual(r, "BindValue(cmdtitle='nop', cmdcode='nop')")
        s = v.snapshot()
        expected = {
            "__class__": hialayout.BindValue.__name__,
            "cmdtitle": "nop",
            "cmdcode": "nop" }
        self.assertEqual(s, expected)

        l = hialayout.BindLayer(lambda k: None)
        l['K_b'] = hialayout.BindValue(lambda: None, 'No-op', 'nop')
        r = repr(l)
        self.assertEqual(r, "BindLayer(values={'K_b': BindValue(cmdtitle='No-op', cmdcode='nop')})")
        s = l.snapshot()
        expected = {
            "__class__": hialayout.BindLayer.__name__,
            "dict": {
                'K_b': {
                    "__class__": hialayout.BindValue.__name__,
                    "cmdtitle": "No-op",
                    "cmdcode": "nop" 
                    },
                },
            }
        self.assertEqual(s, expected)

        g = hialayout.BindGroup(lambda l,k: None)
        expected = {
            "__class__": hialayout.BindGroup.__name__,
            "list": [
                { "__class__": hialayout.BindLayer.__name__,
                    "dict": {},
                    },
                ]
            }
        s = g.snapshot()
        self.assertEqual(s, expected)
        l = g[0]
        l['K_ESC'] = hialayout.BindValue(lambda: None, 'Quit', 'quit')
        expected = {
            "__class__": hialayout.BindGroup.__name__,
            "list": [
                { "__class__": hialayout.BindLayer.__name__,
                    "dict": {
                        'K_ESC': {
                            "__class__": hialayout.BindValue.__name__,
                            "cmdtitle": "Quit",
                            "cmdcode": "quit",
                            },
                        },
                    },
                ]
            }
        s = g.snapshot()
        self.assertEqual(s, expected)

    def test_restore (self):
        # Test restore BindStore from serialization.
        s = {
            "__class__": hialayout.BindStore.__name__,
            "groups": [
                {
                    "__class__": hialayout.BindGroup.__name__,
                    "list": [
                        {
                            "__class__": hialayout.BindLayer.__name__,
                            "dict": {
                                'K_ESC': {
                                    "__class__": hialayout.BindValue.__name__,
                                    "cmdtitle": "Immediate Quit",
                                    "cmdcode": "quit",
                                    },
                                },
                            },
                        ]
                    },
                ]
            }
        b = hialayout.BindStore()
        b.restore(s)
        v = b.get_bind(0,0,'K_ESC')
        self.assertEqual(v.cmdtitle, "Immediate Quit")

    @staticmethod
    def main ():
        if __name__ == "__main__":
            unittest.main()



if __name__ == '__main__':
    unittest.main()

