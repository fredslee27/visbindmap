import unittest
import time

import vismapping
import hidlayout
import kbd_desc
import gobject
import gtk


class TestCmdpack(unittest.TestCase):
    def setUp (self):
        gtk.threads_init()

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

    def dumptree (self, treemdl):
        def visit (treemdl, treepath, treeiter, user_data):
            indent = "  " * (len(treepath)-1)
            rowdata = treemdl[treepath]
            print("{}{!r}".format(indent, tuple(rowdata)))
        treemdl.foreach(visit, None)

    def test_sql0 (self):
        cmdpack = vismapping.CommandSource.builtin()
        self.assertTrue(len(cmdpack) > 0)

        #print(len(cmdpack))
        #self.dumptree(cmdpack)

    def test_sql1 (self):
        cmdpack = vismapping.CommandSource.sqlite3("cmdset/KerbalSpaceProgram.sqlite3")
        self.assertEqual(cmdpack.packname, "Kerbal Space Program")

        #print(len(cmdpack))
        #self.dumptree(cmdpack)




if __name__ == '__main__':
    unittest.main()

