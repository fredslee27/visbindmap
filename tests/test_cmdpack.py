import unittest
import time

import hialayout
import kbd_desc


class TestCmdpack(unittest.TestCase):
    def setUp (self):
        return

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

    def test_builtin (self):
        feed = hialayout.CommandPackFeed_builtin("")
        cmdpack = feed.read()

        #print(len(cmdpack))
        #self.dumptree(cmdpack)

    def test_sql1 (self):
        feed = hialayout.CommandPackFeed_sqlite3("cmdset/KerbalSpaceProgram.sqlite3")
        cmdpack = feed.read()
        self.assertEqual(cmdpack.packname, "Kerbal Space Program")

        #print(len(cmdpack))
        #self.dumptree(cmdpack)




if __name__ == '__main__':
    unittest.main()

