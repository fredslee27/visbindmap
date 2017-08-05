import unittest
import time

import hidlayout
import kbd_desc
import gobject
import gtk


class TestBindDisplay (unittest.TestCase):
    def setUp (self):
        gtk.threads_init()
        self.bdstore = hidlayout.BindDisplayStore(1)

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
        print(repr(self.bdstore))
        return

    def test_1 (self):
        #self.bdstore.append(None, ("K_TEST1", "hello", "world", None, None, None, None, None, None) )
        #self.bdstore.append(None, ("K_TEST1", "hello", "world", "lorem" "ipsum", "dolor", "sit", "amet", "."))
        #self.bdstore.append(None, (hidlayout.BindInfo("K_TEST1",0), hidlayout.BindInfo("hello",0)))
        self.bdstore.append(None,  ("K_TEST1",0, "test1",0) )
        print(repr(self.bdstore))
        self.bdstore['K_TEST2'] = ('test2',)
        print(repr(self.bdstore))
        self.bdstore['K_TEST2'] = ('test02',)
        self.bdstore['K_TEST3'] = None
        self.bdstore['K_TEST4'] = 'test004'
        print(repr(self.bdstore))
        return



if __name__ == '__main__':
    unittest.main()

