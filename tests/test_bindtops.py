#!/usr/bin/env python2
# vim: set ai et ts=4 sw=4
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib
import unittest
import time

import hiabinds
import kbd_desc
#import tests_vismapper.skel
import skel


class TestBindtops (skel.TestSkel):
    def setUp (self):
        self.mdl_binddisplay = hiabinds.BindDisplayStore(2)
        self.w = Gtk.Window()

    def skel (self):
        layout = Gtk.VBox()
        self.w.add(layout)

        WIDGET = Gtk.Widget()
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

    def sample1 (self):
        m = hiabinds.TreeAssocStore(str,str,str,int,str,int)
        m.append(None, ('K_TEST1', 'TEST1', 'tset1', 0, None, 0))
        m.append(None, ('K_TEST2', 'TEST2', 'test2', 0, None, 0))
        return m

    def sample2 (self):
        m = hiabinds.TreeAssocStore(str,int)
        t = m.append(None, ('a',10))
        m.append(t, ('aa', 11))
        m.append(t, ('ab', 12))
        m.append(t, ('ac', 13))
        t = m.append(None, ('b', 20))
        m.append(t, ('bb', 22))
        t = m.append(None, ('c', 30))
        m.append(t, ('ca', 31))
        m.append(t, ('cb', 32))
        m.append(t, ('cc', 33))
        m.append(t, ('cd', 34))
        m.append(t, ('ce', 35))
        m.append(t, ('cf', 36))
        return m

    def test_bindtop (self):
        print("OK")
        self.mdl_binddipaly = self.sample1()

        layout = Gtk.VBox()
        self.w.add(layout)

        b = hiabinds.BindTop("K_TEST", self.mdl_binddisplay)
        b.show()
        #b.get_property("display-model")
        layout.pack_start(b, True, True, 0)

        #w.show_all()
        self.w.show()
        layout.show()
        b.show()

        def script ():
            yield 3

        self.runloop(script)
        #time.sleep(4)
        self.w.hide()



if __name__ == "__main__":
    unittest.main()

