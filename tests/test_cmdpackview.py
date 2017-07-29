import unittest
import time

import hidlayout
import kbd_desc
import gobject
import gtk


class TestCommandPack(unittest.TestCase):
    def setUp (self):
        gtk.threads_init()
        self.bindstore = hidlayout.BindStore(8,8)
        self.w = gtk.Window()
        self.w.set_title(self.__class__.__name__)
        self.w.resize(640, 480)
        class dragsim:
            # Simulated drag-and-drop state information.
            pass
        self.dragsim = dragsim
        self.sample_models = [
          self.make_model0(),
          ]


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

    def make_model0 (self):
        mdl = hidlayout.CommandPackView.make_model()
        grpsys = mdl.append(None, (0, "", "System", None))
        mdl.append(grpsys, (1001, "Reset", "Reset", None))
        mdl.append(grpsys, (1002, "Pause", "Pause", None))
        mdl.append(grpsys, (1003, "Shutdown", "Shutdown", None))
        grpgame = mdl.append(None, (0, "", "Game", None))
        mdl.append(grpgame, (1, "Up", "Up", None))
        mdl.append(grpgame, (2, "Down", "Down", None))
        mdl.append(grpgame, (3, "Left", "Left", None))
        mdl.append(grpgame, (4, "Right", "Right", None))
        mdl.append(grpgame, (5, "Jump", "Jump", None))
        mdl.append(grpgame, (6, "Action", "Action", None))
        mdl.append(grpgame, (7, "Select", "Select", None))
        mdl.append(grpgame, (8, "Start", "Start", None))
        return mdl


    def test_view0 (self):
        layout = gtk.VBox()
        self.w.add(layout)

        self.mdl = self.sample_models[0]
        v = hidlayout.CommandPackView(self.mdl)
        layout.add(v)

        #w.show_all()
        self.w.show()
        layout.show()
        v.show()

        def script ():
            yield 4
            return

        self.runloop(script, 1)
        #time.sleep(4)
        self.w.hide()

    def test_viewdrag0 (self):
        layout = gtk.VBox()
        self.w.add(layout)

        self.mdl = self.sample_models[0]
        v = hidlayout.CommandPackView(self.mdl)
        layout.add(v)

        #w.show_all()
        self.w.show()
        layout.show()
        v.show()

        def script ():
            yield .1

            xw = v.ui.treeview.window
            geom = xw.get_geometry()
            print("geom = %r" % (geom,))

            yield 1

            treesel = v.ui.treeview.get_selection()
            treesel.select_path((0,))
            tx, ty = v.ui.treeview.tree_to_widget_coords(12, 8)
            print("tx, ty = %r, %r" % (tx, ty))

            yield 1

            dragsrc = v.ui.treeview.window
            dnd_targets = [ (str(hidlayout.DndOpcodes.BIND), gtk.TARGET_SAME_APP, hidlayout.DndOpcodes.BIND), ]
            dnd_actions = gtk.gdk.ACTION_COPY
#            dragctx = dragsrc.drag_begin(targets=dnd_targets, actions=dnd_actions, button=gtk.gdk.BUTTON1_MASK)
            dragctx = gtk.gdk.Window.drag_begin(dragsrc, [ int(hidlayout.DndOpcodes.BIND) ])


            dragdst = dragsrc
            #v.ui.treeview.drag_motion(dragctx, dragsrc, gtk.gdk.DRAG_PROTO_LOCAL, x, y, gtk.gdk.ACTION_COPY, gtk.gdk.ACTION_COPY, 0)
            x, y = tx, ty
#            res = dragctx.drag_motion(dragdst, gtk.gdk.DRAG_PROTO_LOCAL, x, y, gtk.gdk.ACTION_COPY, gtk.gdk.ACTION_COPY, 0)

            #geom = dragsrc.get_geometry()
            geom = v.ui.treeview.size_request()
            print("geom = %r" % (geom,))
            ev = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
            ev.x = float(x)
            ev.y = float(y)
            ev.button = 1
            #v.ui.treeview.emit('button-press-event', ev)
            ev.put()
            dragctx = v.ui.treeview.drag_begin(dnd_targets, gtk.gdk.ACTION_COPY, gtk.gdk.BUTTON1_MASK, gtk.gdk.Event(gtk.gdk.BUTTON_PRESS))
            yield 4
            return

        self.runloop(script, 1)
        #time.sleep(4)
        self.w.hide()




if __name__ == '__main__':
    unittest.main()

