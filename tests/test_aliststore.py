# vim: set ai et ts=4 sw=4 :
import unittest
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib
import time

import skel
import hialayout


class TestAListStore (skel.TestSkel):
    def setUp (self):
        self.w = Gtk.Window(title=str(self.__class__.__name__))
        return

    def test_aliststore (self):
        aliststore = hialayout.AListStore(str,str)

        def script ():
            aliststore.append(('foo', 'bar'))
            yield 0.1
            v = aliststore[0][1]
            self.assertEqual(v, 'bar')
            v = aliststore['foo'][1]
            yield 0.1
            self.assertEqual(v, 'bar')
            aliststore['baz'] = 'quux'
            yield 0.1
            v = aliststore['baz'][1]
            self.assertEqual(v, 'quux')

            aliststore['baz'] = 'quuux'
            yield 0.1
            v = aliststore['baz'][1]
            self.assertEqual(v, 'quuux')

            yield 1

        self.runloop(script)
        self.w.destroy()

    @staticmethod
    def main ():
        if __name__ == "__main__":
            unittest.main()



if __name__ == '__main__':
    unittest.main()

