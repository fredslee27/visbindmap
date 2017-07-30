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

        def dump0 (w, ev, *args):
            #print("button-press-event: %r" % (ev,))
            print("button-press-event: %r" % {
                "type": ev.type,
                "window": ev.window,
                "send_event": ev.send_event,
                "time": ev.time,
                "x": ev.x,
                "y": ev.y,
                "axes": ev.axes,
                "state": ev.state,
                "button": ev.button,
                "device": ev.device,
                "x_root": ev.x_root,
                "y_root": ev.y_root,
            })
            return False
        def dump1 (w, ev, *args):
            print("event; %r" % (ev,))
            return False
# button-press-event: {'x_root': 694.0, 'device': <gtk.gdk.Device object at 0x7f769c4ba370 (GdkDevice at 0x172f120)>, 'send_event': 0, 'y_root': 348.0, 'button': 1, 'axes': None, 'state': <flags GDK_MOD2_MASK of type GdkModifierType>, 'window': <gtk.gdk.Window object at 0x7f769c4ba320 (GdkWindow at 0x17316c0)>, 'time': 1273610365, 'y': 10.0, 'x': 54.0, 'type': <enum GDK_BUTTON_PRESS of type GdkEventType>}
        #v.ui.treeview.connect('button-press-event', dump0)
        #v.ui.treeview.connect('event', dump1)
        #v.ui.sclwin.connect('button-press-event', dump0)
        #self.w.connect('button-press-event', dump0)
        gtk.gdk.set_show_events(True)

        def script ():
            yield .1

            xw = v.ui.treeview.window
            geom = xw.get_geometry()
            print("geom = %r" % (geom,))

            yield 1

#            v.ui.treeview.grab_focus()
            #v.ui.treeview.grab_default()
            #v.ui.treeview.set_focus_child()
#            v.ui.treeview.row_activated((0,),v.ui.treecols[0])
#            treesel = v.ui.treeview.get_selection()
#            treesel.select_path((0,))
            tx, ty = v.ui.treeview.tree_to_widget_coords(12, 8)
            print("tx, ty = %r, %r" % (tx, ty))

            yield .1

            x, y = 54, 10

            yield .1

            ev = gtk.gdk.Event(gtk.gdk.ENTER_NOTIFY)
            ev.window = v.ui.treeview.window
            ev.subwindow = v.ui.treeview.window
            print("top geom = %r" % (ev.window.get_toplevel().get_geometry(),))
            ev.x = float(x)
            ev.y = float(y)
            ev.x_root = 694.
            ev.y_root = 348.
           # ev.button = 1
            ev.mode = gtk.gdk.CROSSING_NORMAL
            ev.detail = gtk.gdk.NOTIFY_VIRTUAL
            ev.focus = True
            v.ui.treeview.emit('button-press-event', ev)
            #ev.put()
#            gtk.main_do_event(ev)
            #self.w.emit('button-press-event', ev)

            yield .1

#            #x, y = tx, ty
#            ev = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
#            #ev.window = xw
#            #ev.window = v.ui.sclwin.window
#            #ev.window = self.w.window
#            ev.window = v.ui.treeview.window
#            print("top geom = %r" % (ev.window.get_toplevel().get_geometry(),))
#            ev.x = float(x)
#            ev.y = float(y)
#            ev.x_root = 694.
#            ev.y_root = 348.
#            ev.button = 1
#            #v.ui.treeview.emit('button-press-event', ev)
#            #ev.put()
#            #gtk.main_do_event(ev)
#            v.ui.treeview.emit('button-press-event', ev)

#            yield .1
#            evf = gtk.gdk.Event(gtk.gdk.FOCUS_CHANGE)
#            evf.window = v.ui.treeview.window
#            evf.in_ = True
#            gtk.main_do_event(evf)

            yield .05

            ev2 = gtk.gdk.Event(gtk.gdk.BUTTON_RELEASE)
            #ev2.window = self.w.window
            ev2.window = v.ui.treeview.window
            print("top geom = %r" % (ev2.window.get_toplevel().get_geometry(),))
            ev2.x = float(x)
            ev2.y = float(y)
            ev2.x_root = 694.
            ev2.y_root = 348.
            ev2.button = 1
            #ev2.put()
            #gtk.main_do_event(ev2)
            v.ui.treeview.emit('button-release-event', ev2)

#            ev3 = gtk.gdk.Event(gtk.gdk.MOTION_NOTIFY)
#            ev3.window = v.ui.treeview.window
#            ev3.x = ev.x+1
#            ev3.y = ev.y
#            ev3.x_root = ev.x_root+1
#            ev3.y_root = ev.y_root
#            gtk.main_do_event(ev3)

            yield 2

            dragsrc = v.ui.treeview.window
            dnd_targets = [ (str(hidlayout.DndOpcodes.BIND), gtk.TARGET_SAME_APP, hidlayout.DndOpcodes.BIND), ]
            dnd_actions = gtk.gdk.ACTION_COPY
#            dragctx = dragsrc.drag_begin(targets=dnd_targets, actions=dnd_actions, button=gtk.gdk.BUTTON1_MASK)
            #dragctx = gtk.gdk.Window.drag_begin(dragsrc, [ int(hidlayout.DndOpcodes.BIND) ])


            dragdst = dragsrc
            #v.ui.treeview.drag_motion(dragctx, dragsrc, gtk.gdk.DRAG_PROTO_LOCAL, x, y, gtk.gdk.ACTION_COPY, gtk.gdk.ACTION_COPY, 0)
#            res = dragctx.drag_motion(dragdst, gtk.gdk.DRAG_PROTO_LOCAL, x, y, gtk.gdk.ACTION_COPY, gtk.gdk.ACTION_COPY, 0)

            #geom = dragsrc.get_geometry()
            geom = v.ui.treeview.size_request()
            print("geom = %r" % (geom,))

            yield 1

            dragctx = v.ui.treeview.drag_begin(dnd_targets, gtk.gdk.ACTION_COPY, gtk.gdk.BUTTON1_MASK, gtk.gdk.Event(gtk.gdk.BUTTON_PRESS))
            yield 2
            return

        self.runloop(script, 1)
        #time.sleep(4)
        self.w.hide()

    def test_viewdnd0 (self):
        layout = gtk.HBox()
        self.w.add(layout)

        self.mdl = self.sample_models[0]
        v = hidlayout.CommandPackView(self.mdl)

        def on_bind_assigned (w, sym, val):
            print("T: assign %s <- %s" % (sym, val))
            pass
        def on_bind_swapped (w, sym0, sym1):
            print("T: swap {} <-> {}".format(sym0, sym1))
            pass
        def on_bind_erased (w, sym):
            print("T: erase {}".format(sym))
            pass
        hia0 = hidlayout.BindableTop("TESTA", "TESTA", [ True, ], [ "" ])
        hia1 = hidlayout.BindableTop("TESTB", "TESTB", [ True, ], [ "" ])
        hia0.connect('bind-assigned', on_bind_assigned)
        hia0.connect('bind-swapped', on_bind_swapped)
        hia0.connect('bind-erased', on_bind_erased)
        hia1.connect('bind-assigned', on_bind_assigned)
        hia1.connect('bind-swapped', on_bind_swapped)
        hia1.connect('bind-erased', on_bind_erased)

        layout.add(v)
        layout.add(hia0)
        layout.add(hia1)

        #w.show_all()
        self.w.show()
        layout.show()
        v.show()
        hia0.show()
        hia1.show()

        def script ():
            yield 4
        self.runloop(script, 1)
        #time.sleep(4)
        self.w.hide()



if __name__ == '__main__':
    unittest.main()

