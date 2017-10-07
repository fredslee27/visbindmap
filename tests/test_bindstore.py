# vim: set ai et ts=4 sw=4 :
import unittest
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib
import time

import skel
import hialayout


class TestBindStore (skel.TestSkel):
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
            box.s = hiasym
        b.connect("bind-changed", on_bind_changed)

        def script():
            v = hialayout.BindValue("nop", "nop")
            s = repr(v)
            self.assertEqual(s, "BindValue(cmdtitle='nop', cmdcode='nop')")
            # set whole entry.
            b.set_bind(0, 0, 'K_a', 'wait'),
            yield 0.1

            # set entry field.
            box.v = None
            self.assertEqual(box.v, None)
            b.groups[0][0]['K_a'].cmdcode = 'wait 2'
            yield 0.1
            self.assertEqual(box.v, ("wait", "wait 2"))

            # set row.
            box.v = None
            l2 = hialayout.BindLayer(lambda k: None)
            l2['K_b'] = 'wait 0x66'
            b.groups[0].nlayers = 2
            b.groups[0][1] = l2
            yield 0.1
            self.assertEqual(box.v, ("wait 0x66", "wait 0x66"))

            # straight assignment
            box.v = None
            b.groups[0][0]['K_b'] = "wait b"
            yield 0.1
            self.assertEqual(box.v, ("wait b", "wait b"))
            self.assertEqual(box.s, "K_b")

            # via set_bind
            box.v = None
            b.set_bind(0, 0, 'K_b', 'wait bb')
            yield 0.1
            self.assertEqual(box.v, ("wait bb", "wait bb"))
            self.assertEqual(box.s, "K_b")
            self.assertEqual(b.groups[0][0]['K_b'][0], 'wait bb')

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

    def test_bindtreestore (self):
        b = hialayout.BindTreeStore()
        b.put_bind(0,0,"K_ESC","Quit","quit")
        b.put_bind(0,0,"K_SHIFT","nop","nop")
        b.put_bind(0,0,"K_RETURN","Activate","activate")
        #s = b.serialize_tree(b)
        s = b.snapshot()
        #print(s)
        groups = s['bindstore']
        self.assertTrue(isinstance(groups,list))
        self.assertTrue(isinstance(groups[0],tuple))  # group
        layers = groups[0][5]
        self.assertTrue(isinstance(layers[0],tuple))  # layer
        binds = layers[0][5]
        bindmap = layers[0][4]
        allsyms = [ x[2] for x in binds ]
        self.assertEqual(len(allsyms), 3)

        b2 = hialayout.BindTreeStore()
        b2.restore(s)
        bv = b2.get_bind(0,0,'K_ESC')
        self.assertTrue(bv.cmdtitle, 'Quit')

        grpmdl = b.groups
        groupnames = [ x[2] for x in grpmdl ]
        self.assertIn('GLOBAL', groupnames)

        lyrmdl = b.layers
        layernames = [ x[2] for x in lyrmdl ]
        self.assertIn('base', layernames)

        b.add_layershifter()
        self.assertEqual(b.nlayers,2)
        b.add_layershifter()
        self.assertEqual(b.nlayers,4)
        b.add_layershifter()
        self.assertEqual(b.nlayers,8)
        layernames = [ x[2] for x in lyrmdl ]
        layercodes = [ x[3] for x in lyrmdl ]
        #print(layernames)
        self.assertEqual(len(layernames), 8)
        self.assertEqual(layernames[0], "base")
        self.assertEqual(layernames[7], "7 (^1 + ^2 + ^3)")
        self.assertEqual(layernames[4], "4 (^3)")
        self.assertEqual(layercodes, [ None, "^1", "^2", None, "^3", None, None, None ] )

    @staticmethod
    def main ():
        if __name__ == "__main__":
            unittest.main()



if __name__ == '__main__':
    unittest.main()

