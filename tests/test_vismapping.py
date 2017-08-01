import unittest
import time

import vismapping, hidlayout
import gobject
import gtk


class TestVismapping(unittest.TestCase):
    def setUp (self):
        gtk.threads_init()
        self.app = vismapping.VisMapperApp()
        self.app.ui.show_all()
        self.ui = self.app.ui
        self.bindpad = self.ui.bindpad
        self.hidl = self.bindpad.hidl


    def runloop (self, playback=[lambda: None]):
        for n in range(0, len(playback)):
            t = time.time()
            timegate = t
            invoke = playback[n]
            if callable(invoke):
                invoke()
            elif type(invoke) in ( int, float ):
                timegate = t + invoke
            else:
                pass
            while t <= timegate:
                while gtk.events_pending():
                    gtk.main_iteration_do(block=False)
                t = time.time()


    def test_gyromenulist (self):
        def find_gyro ():
#            gridch = self.app.ui.bindpad.hidl.hidview.get_children()
#            print("gridch = %r" % gridch)
#            planars = [ ch for ch in gridch if isinstance(ch, hidlayout.HidPlanar) ]
#            gyros = [ pl for pl in planars if "GY#" in pl.frame_lbl_sym.get_label() ]
#            gyro = gyros[0]
            gyro = self.app.ui.bindpad.hidl.hidview.clusters["GY#"]
            return gyro

        def gyro_to_menulist ():
            gyro = find_gyro()
            gyro.set_arranger(gyro.arrangerMenulist)

        def fill_scratch ():
            dispstate = self.app.models.dispstate
            dispstate.set_bind("GY#1", "Up")
            dispstate.set_bind("GY#2", "Down")
            dispstate.set_bind("GY#3", "Left")
            dispstate.set_bind("GY#4", "Right")

        playback=[ 0.5,
                   lambda: gyro_to_menulist(),
                   1,
                   lambda: fill_scratch(),
                   30,
                   ]

        self.runloop(playback)
        return

    def test_multilayer (self):
        def find_gyro ():
            gyro = self.app.ui.bindpad.hidl.hidview.clusters["GY#"]
            return gyro
        def gyro_to_menulist ():
            gyro = find_gyro()
            gyro.set_arranger(gyro.arrangerMenulist)
        playback = [ 0.5,
                    lambda: self.bindpad.hidl.set_vislayers(2),
                    lambda: gyro_to_menulist(),
                    30
                    ]

        self.runloop(playback)
        return



if __name__ == '__main__':
    unittest.main()



