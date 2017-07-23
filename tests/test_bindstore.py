import unittest
import time

import hidlayout
import kbd_desc
import gobject
import gtk


class TestBindstore (unittest.TestCase):
    def setUp (self):
        gtk.threads_init()
	self.bindstore = hidlayout.BindStore(8,8)

    def runloop (self, script=lambda: 0):
        """Run test script, coded as a coroutine.
Coroutine yield()s number of seconds to pause; gtk event handler runs during the script pause.
Loop ends when coroutine ends (uses return instead of yield)
"""
        for pauselen in script():
            t = time.time()
            timegate = t + pauselen
            while t <= timegate:
                while gtk.events_pending():
                    gtk.main_iteration_do(block=False)
                t = time.time()

    def test_0 (self):
        self.bindstore[0][0]['K_TEST'] = 'test_changer'
        def script ():
            return
        self.assertEqual(self.bindstore[0][0]['K_TEST'], 'test_changer')
        self.assertEqual(self.bindstore[0][0], {'K_TEST': 'test_changer'})
        return

    def test_copy (self):
        self.bindstore[0][0]['K_TEST'] = 'test_changer'
        b2 = self.bindstore.__copy__()
        self.assertEqual(b2[0][0]['K_TEST'], 'test_changer')
        b3 = self.bindstore[0][3:6]
        self.assertEqual(len(b3), 3)
        return




if __name__ == '__main__':
    unittest.main()

