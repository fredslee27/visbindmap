import unittest
# vim: set ai et ts=4 sw=4 :

import hiabinds
import gi
gi.require_version("Gtk", '3.0')
from gi.repository import Gtk

class TestHiaBinds (unittest.TestCase):
    def setUp (self):
        pass

    def sample1 (self):
        m = hiabinds.TreeAssocStore(str,int)
        m.append(None, ('a',1))
        m.append(None, ('b',2))
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

    def test_get_by_key (self):
        m = self.sample1()
        x = m['a']
        self.assertEqual(tuple(x), ('a',1))

        m = self.sample2()
        y = m[2,2]
        x = m['c','cc']
        #z = m['c','cc', 'cccc']
        self.assertEqual(tuple(y), ('cc', 33))
        self.assertEqual(tuple(x), ('cc', 33))
        self.assertRaises(KeyError, lambda: m['c','cc','ccc'])

    def test_add_by_key (self):
        m = self.sample2()
        m['d'] = 40
        self.assertEqual(tuple(m['d']), ('d', 40))
        self.assertEqual(tuple(m[3,]), ('d', 40))
        return

    def test_get_value (self):
        m = self.sample1()
        v = m.getvalue('a')
        self.assertEqual(v, (1,))
        self.assertEqual(m.getfirst('a'), 1)

if __name__ == "__main__":
    unittest.main()
