import unittest
import time

import vismapping
import hidlayout
import kbd_desc
import gobject
import gtk

import StringIO


class TestSerialize(unittest.TestCase):
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

    def test_cmdpack (self):
#        print()
        cmdpack = vismapping.CommandSource.builtin()
        enc1 = cmdpack.encode()
#        print(repr(cmdpack))

        encdict = cmdpack.encode()
        del encdict['.class']
        cmdpack2 = hidlayout.CommandPackStore(**encdict)
#        print("\npack2\n")
#        print(repr(cmdpack2))

        self.assertEqual(repr(cmdpack), repr(cmdpack2))

    def test_bindstore (self):
        bindstore = hidlayout.BindStore(8,8)
        bindstore[0][0]['K_TEST1'] = 'test1'
        enc1 = bindstore.encode()
        #print()
        #print("bindstore  %r" % enc1)

        temp = dict(enc1)
        del temp['.class']
        bindstore2 = hidlayout.BindStore(**temp)
        enc2 = bindstore2.encode()
        #print("bindstore2 %r" % (enc2,))

        self.assertEqual(repr(enc1), repr(enc2))

    def test_appsession (self):
        session = vismapping.AppSession()
        session.cmdpack = vismapping.CommandSource.builtin()
        session.uri_bindstore = "(stdin)"
        session.uri_cmdpack = "(builtin)"
        sio = StringIO.StringIO()
        session.snapshot(sio)
        enc1 = sio.getvalue()
        #print("\n\n1: " + enc1)

        sio2 = StringIO.StringIO(enc1)
        session2 = vismapping.AppSession()
        session2.resume(sio2)
        sio2o = StringIO.StringIO()
        session2.snapshot(sio2o)
        enc2 = sio2o.getvalue()
        #print("\n\n2: " + enc2)

        self.assertEqual(repr(enc1), repr(enc2))
        self.assertIsNotNone(session2.bindstore)
        self.assertIsNotNone(session2.cmdpack)
        self.assertEqual(session2.uri_bindstore, "(stdin)")
        self.assertEqual(session2.uri_cmdpack, "(builtin)")



if __name__ == '__main__':
    unittest.main()

