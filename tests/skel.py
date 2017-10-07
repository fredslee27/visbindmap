# vim: set ai et ts=4 sw=4 :
import unittest
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib
import time


class TestSkel (unittest.TestCase):
    def setUp (self):
        return

    def runloop (self, script=lambda: []):
        """Run test script, coded as a coroutine.
Coroutine yield()s number of seconds to pause; gtk event handler runs during the script pause.
Loop ends when coroutine ends (uses return instead of yield)
"""
        for pauselen in script():
            t = time.time()
            timegate = t + pauselen
            while t <= timegate:
                while Gtk.events_pending():
                    #Gtk.main_iteration_do(block=False)
                    Gtk.main_iteration_do(False)
                time.sleep(0.01)
                t = time.time()

    @staticmethod
    def main ():
        if __name__ == "__main__":
            unittest.main()



if __name__ == '__main__':
    unittest.main()

