#!/usr/bin/env python
# vim: set expandtab tabstop=4 :

import gtk, gobject
import sys, os, os.path
import sqlite3

import pprint
import pickle
import ast, parser

import kblayout
from kblayout import Log


BASENAME="generic_game"
DEFAULT_DBNAME="cmds"


def crumb (x):
    pass

class TeeLog (object):
    """Print log messages to stderr and debug text window."""
    def __init__ (self, debugbuf, stream=sys.stderr):
        self.outstream = stream
        self.debugbuf = debugbuf
    def write (self, data):
        self.outstream.write(data)

        if self.debugbuf:
            if data == "\f":
                # Clear contents.
                self.debugbuf.delete(self.debugbuf.get_start_iter(), self.debugbuf.get_end_iter())
            else:
                self.debugbuf.insert_at_cursor(data)
    def writelines (self, data):
        self.outstream.writelines(data)
        print("@@@ writelines not implemented")
    def flush (self):
        pass
    def close (self):
        self.outstream = None
        # let gc close the file, in case it's stderr.
    def closed (self):
        return (self.outstream is not None)
log = Log(Log.debug)



def BuildMenuBar (menubardesc, menubar=None, accelgroup=None):
    """Build menu bar from a list of menu description list.
List of menu description contains elements made of tuples, each tuple is:
1. None = menu separator
2. (display:str, handler:callable) = menu item + callback ("c/b")
2a   use lambda for passing userdata : lambda *args: callback(*args, MyUserData)
3. (display:str, accel:str, handler:callable) = menu item + accelerator + c/b
3. (display:str, submenu:list) = sub-menu (nested list of menu description)
"""
    def BuildMenuItem (itemdesc, accelgroup=None):
        if itemdesc is None: return gtk.SeparatorMenuItem()  # separator
        retval = gtk.MenuItem(itemdesc[0])
        if callable(itemdesc[1]):  # leaf - regular menu item with callback.
            callback = itemdesc[1]
            retval.connect("activate", callback)
        elif hasattr(itemdesc[1], "isalpha"):  # string-like.
            accelkey = itemdesc[1]
            callback = itemdesc[2]
            retval.connect("activate", callback)
            accelsym, accelmod = gtk.accelerator_parse(accelkey)
            if accelgroup:
                retval.add_accelerator('activate', accelgroup, accelsym, accelmod, gtk.ACCEL_VISIBLE)
        elif hasattr(itemdesc[1], "__getslice__"):  # treat as submenu.
            submenu = itemdesc[1]
            retval.set_submenu(BuildMenu(submenu, accelgroup=accelgroup))
        return retval
    def BuildMenu (menudesc, menu=None, accelgroup=None):
        menu = menu or gtk.Menu()
        #map(menu.append, map(BuildMenuItem, menudesc))
        map(menu.append, map(lambda x: BuildMenuItem(x,accelgroup), menudesc))
        return menu
    if menubar is None:
        menubar = gtk.MenuBar()
    return BuildMenu(menubardesc, menubar, accelgroup)



# Checkpointable app data.
class AppData (object):
    def __init__ (self):
        self.filename = None
        self.active = None  # active bind layer.
        self.binds = []  # List of dicts, bindings per layer.

    def get_active (self):
        return self.active
    def set_active (self, val):
        self.active = val

    def get_filename (self):
        return self.filename
    def set_filename (self, val):
        self.filename = val

    def load (self):
        pass
    def save (self):
        pass


class ObjectReinstantiater(ast.NodeTransformer):
    """Traverse Abstract Syntax Tree to filter allowed object instantiation."""
    # Classes allowed to be instantiated.  Otherwise becomes None.
    REINSTANCERS = {
        "kblayout.InpDescrModel": kblayout.InpDescrModel,
        "kblayout.InpLayer": kblayout.InpLayer,
        }
    def nop (self, node):
        return ast.parse("None", mode='eval')
    def visit_Call (self, node):
        cmodule = node.func.value.id
        cclass = node.func.attr
        ckey = "%s.%s" % (cmodule, cclass)
        if ckey in self.REINSTANCERS:
            log.debug("Invoke %s.%s(**%r)" % (cmodule, cclass, kwargs))
            return node
        else:
            return ast.parse("None", mode='eval')
    def visit_Yield (self, node): return self.nop()
    def visit_Lambda (self, node): return self.nop()
    def visit_IfExp (self, node): return self.nop()


# Persistant storage.
class Store (object):
    DEFAULT_FILENAME = BASENAME + ".cfg"

    def reset (self):
        self.inpdescr = kblayout.InpDescrModel(self._numlayers)
        self.modes = []
        for x in range(self._nummodes):
            placeholder = []
            for y in range(self._numlayers):
                v = kblayout.InpLayer(y, 0, None)
                placeholder.append(v)
            self.modes.append(placeholder)
        self.inpdescr.layers = self.modes[0]

    def __init__ (self, nummodes=8, numlevels=8, backingFileName=None):
        # list of bindings, one binding per layer (typically 8 layers).
        # bindings are mapping SDL_binding => command.
        # modes are list of list-of-binding, typically 1 or 2.
        self._nummodes = nummodes
        self._numlayers = numlevels
        self.reset()
        self.fname = backingFileName
        if not backingFileName:
            self.fname = self.DEFAULT_FILENAME

    def load (self, fileobj=None):
        if fileobj is None:
            fileobj = open(self.fname, "rb")
        #fileobj = open(fname, "rb")
        #self.binddata = pickle.load(fileobj)
        #fileobj.close()
        s = fileobj.read()
        astree = ast.parse(s, mode='eval')
        transformed = ObjectReinstantiater().visit(astree)
        storedict = eval(compile(transformed, '', 'eval'))
        self.modes = storedict['modes']
        self.inpdescr.layers = self.modes[0]
        self.inpdescr.refresh()

    def save (self, fileobj=None):
        if fileobj is None:
            fileobj = open(self.fname, "wb")
            fileobj.write(self.modes)
        #fileobj = open(fname, "wb")
        #pickle.dump(self.binddata, fileobj)
        #fileobj.close()
        storedict = {
            'modes': self.modes,
            }
        pprint.pprint(storedict, fileobj, indent=2, width=132)
        fileobj.write("\n")



def build_treestore_from_commands(cmds_db, treestore=None):
    if treestore is None:
        #                       id, cmd, display, hint
        treestore = gtk.TreeStore(int, str, str, str)

    # First, the unbind item.
    treestore.append(None, (0, "", "(unbind)", ""))

    # Prepare groups; mapping of group name to TreeIter position of that header row in the TreeStore.
    groupheads = {}

    # Recursively callable for nested groups.
    def make_group (grpname):
        if '/' in grpname:
            splitpt = grpname.rindex('/')
            prefix = grpname[:splitpt]
            suffix = grpname[splitpt+1:]
            make_group(prefix)
            parentiter = groupheads[prefix]
            treeiter = treestore.append(parentiter, (0, "", suffix, ""))
            groupheads[grpname] = treeiter
        else:
            if not groupheads.has_key(grpname):
                treeiter = treestore.append(None, (0, "", grpname, ""))
                groupheads[grpname] = treeiter

    for grp in cmds_db.groups:
        make_group(grp)

    for cmdinfo in cmds_db:
        (cmdid, layer, grp, cmd, desc, hint) = cmdinfo
        grpiter = groupheads[grp]
        if not desc:
            desc = cmd
        row = (cmdid, cmd, desc, hint)
        treeiter = treestore.append(grpiter, row)


class CmdStore (gtk.TreeStore):
    def __init__ (self, cmds_db=None):
        #                            id, cmd, display, hint
        gtk.TreeStore.__init__(self,  int, str, str, str)
        self.clear()
        if cmds_db:
            self.import_commands(cmds_db)

    def clear (self):
        gtk.TreeStore.clear(self)
        # First item = 'unbind'
        self.append(None, (0, "", "(unbind)", ""))
        # Prepare groups; mapping of group name to TreeIter position of that header row in the TreeStore.
        self.groupheads = {}
        return

    def make_group (self, grpname):
        if '/' in grpname:
            splitpt = grpname.rindex('/')
            prefix = grpname[:splitpt]
            suffix = grpname[splitpt+1:]
            make_group(prefix)
            parentiter = self.groupheads[prefix]
            treeiter = self.append(parentiter, (0, "", suffix, ""))
            self.groupheads[grpname] = treeiter
        else:
            if not self.groupheads.has_key(grpname):
                treeiter = self.append(None, (0, "", grpname, ""))
                self.groupheads[grpname] = treeiter

    def import_commands (self, cmds_db):
        for grp in cmds_db.groups:
            self.make_group(grp)
        for cmdinfo in cmds_db:
            (cmdid, layer, grp, cmd, desc, hint) = cmdinfo
            grpiter = self.groupheads[grp]
            if not desc:
                desc = cmd
            row = (cmdid, cmd, desc, hint)
            treeiter = self.append(grpiter, row)
        return True


# List of binding modes.
class ModeStore (gtk.ListStore):
    def __init__ (self, cmds_db=None):
        #                            id, name
        gtk.ListStore.__init__(self, int, str)
        self.clear()
        if cmds_db:
            self.import_commands(cmds_db)

    def clear (self):
        gtk.ListStore.clear(self)
        # First/Minimum is "global".
        self.append((0, "*GLOBAL"))
        return

    def import_commands (self, cmds_db):
        modes = cmds_db.get_modes()
        n = 1
        for modename in modes:
            self.append((n, modename))
            n += 1
        return True


class Commands (object):
    """Database of game commands."""
    def __init__ (self, dbname):
        self.dbname = dbname
#        self.db = [(0, "", "", "(none)", None)]
        # Open DB.
        self.conn = sqlite3.connect(dbname)
        # Pull relevant rows.
        cursor = self.conn.cursor()
        cursor.execute('''SELECT id,layer,grp,cmd,label,hint FROM cmd;''')

    def get_modes (self):
        cursor = self.conn.cursor()
        rows = cursor.execute('''SELECT name FROM modes ORDER BY id;''')
        modenames = []
        for row in rows:
            modename = row[0];
            modenames.append(modename)
        return modenames

    def get_groups (self):
        cursor = self.conn.cursor()
        rows = cursor.execute('''SELECT grp FROM cmd GROUP BY grp ORDER BY id;''');
        grpnames = []
        for row in rows:
            grpname = row[0]
            grpnames.append(grpname)
        return grpnames

    groups = property(get_groups)

    def get_by_id (self, val):
        # TODO: look through tree model instead?
        if val is None:
            log.debug("[None]=>None...")
            return [ None, 0x1f, "", "", "", "" ]

        cursor = self.conn.cursor()
        #cursor.execute('''SELECT cmd FROM cmd WHERE id=? LIMIT 1;''', str(val))
        cursor.execute('''SELECT id,layer,grp,cmd,label,hint FROM cmd WHERE id=? LIMIT 1;''', (str(val),))
        result = cursor.fetchone()
        if result:
            if not result[4]:
                result = result[:4] + (result[3],) + result[5:]
            return result
        else:
            return None

    def get_count (self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT COUNT(*) FROM cmd;''')
        return cursor.fetchone()[0]

    def find (self, cmdname):
        if cmdname is None:
            log.debug("find(None) => None")
            return None

        cursor = self.conn.cursor()
        cursor.execute("""SELECT id FROM cmd WHERE cmd=? LIMIT 1;""", (str(cmdname),))
        retval = cursor.fetchone()
        if retval:
            return retval[0]
        else:
            return -1

    def get (self, cmdname, altval):
        idx = self.find(cmdname)
        if (idx < 0):
            return altval
        return self.get_by_id(idx)

    def __getitem__ (self, idx):
        return self.get_by_id(idx)

    def __len__ (self):
        return self.get_count()

    def __iter__ (self):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT id,layer,grp,cmd,label,hint FROM cmd;""")
        row = cursor.fetchone()
        while row:
            yield row
            row = cursor.fetchone()
        raise StopIteration()

    def build_treestore (self, store):
        return build_treestore_from_commands(self, store)
#    def build_treestore (self, store):
#        # The unbind item.
#        store.append(None, (0, "", "(unbind)", "", self))
##            treeiter = store.append(grpiter, (cmdid, cmd, desc, hint, self))
#        # Build all groups.
#        groupheads = {}
#
#        def make_group (grpname):
#            if '/' in grpname:
#                splitpt = grpname.rindex('/')
#                prefix = grpname[:splitpt]
#                suffix = grpname[splitpt+1:]
#                make_group(prefix)
#                parentiter = groupheads[prefix]
#                #treeiter = store.append(parentiter, (0, "", grp, ""))
#                treeiter = store.append(parentiter, (0, "", suffix, "", self))
#                groupheads[grpname] = treeiter
#            else:
#                if not groupheads.has_key(grpname):
#                    treeiter = store.append(None, (0, "", grp, "", self))
#                    groupheads[grpname] = treeiter
#
#        for grp in self.groups:
##            treeiter = store.append(None, (0, "", grp, ""))
##            groupheads[grp] = treeiter
#            make_group(grp)
#
#        for cmdinfo in self.__iter__():
#            (cmdid, layer, grp, cmd, desc, hint) = cmdinfo
#            grpiter = groupheads[grp]
#            if not desc:
#                desc = cmd
#            treeiter = store.append(grpiter, (cmdid, cmd, desc, hint, self))


class VisCmds (gtk.VBox):
    """Visual presentation of commands: a tree of group and the commands."""
    def __init__ (self, cmdstore=None):
        gtk.VBox.__init__(self)

        if not cmdstore:
            cmdstore = CmdStore()
        self.cmdstore = cmdstore

        self.entry = gtk.TreeView(self.cmdstore)
        self.entry.drag_source_set(gtk.gdk.BUTTON1_MASK, [ ("bind", gtk.TARGET_SAME_APP, 1), ], gtk.gdk.ACTION_LINK)
        self.entry.connect("drag-data-get", self.on_drag_data_get)
        self.cell0 = gtk.CellRendererText()
        self.col0 = gtk.TreeViewColumn("command", self.cell0, text=2)
        self.entry.append_column(self.col0)
#        self.add(gtk.Label("VisCmds"))

        #self.add(self.entry)
        self.entrywin = gtk.ScrolledWindow()
        self.entrywin.add_with_viewport(self.entry)
        self.add(self.entrywin)
        self.set_size_request(160, 100)

    def get_cmdstore (self):
        return self.cmdstore
    def set_cmdstore (self, cmdstore):
        self.cmdstore = cmdstore
        self.entry.set_model(self.cmdstore)
        # TODO: update TreeView?

    def on_drag_data_get (self, w, ctx, sel, info, time, *args):
        srcw = ctx.get_source_widget()
        treesel = srcw.get_selection()
        (treemdl, treeiter) = treesel.get_selected()
        if sel.target == "bind":
            log.debug("target is bind")

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                sel.set_text("", 0)
                return
            # Get the command to bind.
            val = treemdl.get_value(treeiter, 1)

            sel.set("STRING", 8, val)  # 8 bits per unit.
        elif sel.target == "bindid":
            log.debug("target is bindid")

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                sel.set_text("", 0)
                return
            # Get the command to bind.
            val = treemdl.get_value(treeiter, 0)

            sel.set("STRING", 8, str(val))  # 8 bits per unit.
        elif sel.target == "binduri":
            log.debug("%s drag-data-get: w = %r" % (self.__class__.__name__, w))
            # Find out target, get its inpsym, assign binding.
            # Send displayed text to target.
            log.debug("+++ target is bindref")

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                sel.set_text("", 0)
                return
            # Get the command to bind.
            num = treemdl.get_value(treeiter, 0)
            name = treemdl.get_value(treeiter, 1)
            val = "cmdbind://%s/%s" % (num, name)
            log.debug("val = %r" % val)
            sel.set("STRING", 8, str(val))  # 8 bits per unit.


# Graphically lay out bindings meanings.
class VisBind (gtk.VBox):
    """Graphical layout of bindings; "central pane" of main window.
Consists of:
 * layout selector
 * layer selector
( group selector? )
 * the keytops
"""

    def reset (self):
        pass


    def __init__ (self, store, models=None):
        gtk.VBox.__init__(self)

        self.store = store
        self.models = models
        self.cmdstore = models.cmdstore

        self.uibuild()

        self.reset()

    def uibuild (self):
        self.shiftrow = self.InpSelectLevel()
        self.pack_start(self.shiftrow)

        self.moderow = self.InpSelectMode()
        self.pack_start(self.moderow)

        # grid/tablular layout of inpbind+bindcmd
        inpdescr = self.store.inpdescr
        self.kbl = kblayout.KblayoutWidget(inpdescr)
        self.kbl.connect('key-selected', self.on_key_selected)

        self.pack_start(self.kbl, expand=False, fill=False)

    def on_key_selected (self, w, ksym, *args):
        binding = self.store.inpdescr.get_bind(0, ksym)
        log.debug("key-selected: %s => %r" % (ksym, binding))

    def on_layout_changed (self, w, layoutname, *args):
        self.relabel_keys(self.levelnum)
        self.load_bindmap(self.layernum)

    def InpSelectMode (self):
        """Generate GUI Widget for selecting mode (layer)."""
        moderow = gtk.HBox()
        modebtns = gtk.HButtonBox()

        moderow.lbl = gtk.Label("MODE:")
        moderow.btns = []
        # "Select Layer" radio buttons.
        #modes = [ "(GLOBAL)", "Game", "Inventory", "Crafting", "Editor" ]
        #modes = [ "*GLOBAL" ] + self.cmdstore.get_modes()
        modestore = self.models.modestore

        def rebuild_buttons (modestore):
            if moderow.btns:
                for btn in moderow.btns:
                    modebtns.remove(btn)
            moderow.btns = []  # private data.
            for modeid in range(len(modestore)):
                grp = moderow.btns and moderow.btns[0] or None    # is group member or is group leader.
                lbl = modestore[modeid][1]  # List row, second column => name.
                btn = gtk.RadioButton(grp, lbl)  # create element.
                btn.layernum = modeid  # private data
                btn.connect('toggled', self.on_mode_toggle)  # react
                modebtns.add(btn)  # GUI
                moderow.btns.append(btn)  # internal storage.
            moderow.show_all()
            return
        def on_data_changed (m, *args):
            rebuild_buttons(m)
            
        rebuild_buttons(modestore)
        moderow.pack_start(modebtns, expand=False)
        # Rebuilds all buttons on any change.  This is very expensive.
        modestore.connect('row-changed', on_data_changed)
        modestore.connect('row-deleted', on_data_changed)
        modestore.connect('row-inserted', on_data_changed)

        #return moderow
        modebox = gtk.Frame("MODE")
        modebox.add(moderow)
        return modebox

    def InpSelectLevel (self):
        """Generate GUI Widget for selecting level (shifted)."""
        shiftbox = gtk.Frame("LEVEL")
        shiftrow = gtk.HBox()
        shiftbtns = gtk.HButtonBox()
        MAX_SHIFTER = 3
        btns = []
        #shiftrow.lbl = gtk.Label("LEVEL")
        #shiftrow.pack_start(shiftrow.lbl, expand=False)
        for lvlnum in xrange(0, 8):
            sh = []
            for b in xrange(0, 8):
                if (lvlnum & (1 << b)):
                    sh.append("^%s" % (b+1))
            if sh:
                lbl = "%d " % lvlnum + ("(" + " + ".join(sh) + ")")
            else:
                lbl = "base"
            grp = btns and btns[0] or None
            btn = gtk.RadioButton(grp, lbl)
            btn.levelnum = lvlnum
            btn.connect('toggled', self.on_shifter_toggle)  # react
            btns.append(btn)
            shiftbtns.add(btn)
        shiftrow.btns = btns
        shiftrow.pack_start(shiftbtns, expand=True)
        #return shiftrow
        shiftbox.add(shiftrow)
        return shiftbox

    def relabel_keys (self, levelnum):
        """Repaint/Update keysyms, typically due to layout change."""
        pass

    def on_mode_toggle (self, w, *args):
        """Load bindings for mode."""
        if w.get_active():
          self.emit("mode-changed", w.layernum)
        return

    def on_shifter_toggle (self, w, *args):
        """Load bindings for shift level."""
        if not w.get_active():
          # turning off.
          return
        if w.get_active():
          # turning on.
          self.emit("level-changed", w.levelnum)
        return

    def bind_cmd (self, ksym, cmdinfo):
        log.debug("bind");
        pass

    def unbind_cmd (self, ksym):
        log.debug("unbind");
        pass

gobject.type_register(VisBind)
gobject.signal_new("mode-changed", VisBind, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,))
gobject.signal_new("level-changed", VisBind, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,))


class DlgAbout (gtk.AboutDialog):
    def __init__ (self):
        gtk.AboutDialog.__init__(self)
        self.set_name("VisMapper")
        self.set_version("0.0.1")
        self.set_copyright("Copyright 2016  PhaethonH <PhaethonH@gmail.com>")
        self.set_license("GNU General Public License 3.0 or later")


class VisMapperWindow (gtk.Window):
    """Main window, majority of state information."""
    BASE_TITLE = "Vismapper"

    def reset (self):
        """Reset window contents."""
        self.bindpad.reset()

    def __init__ (self, parent=None, store=None, menubar=None, models=None):
        self.app = parent

        gtk.Window.__init__(self)
        self.set_title("%s" % self.BASE_TITLE)
        self.subtitle = ""

        if store is None:
            self.store = self.app.store
        else:
            self.store = store

        #self.cmdstore = cmdstore
        self.models = models
        self.menubar = menubar
        self.uibuild()

    def use_filename (self, fname=None):
        """Set filename portion of window title.
Provide "" to erase filename portion."""
        if fname is None:
            # Do not change.
            return
        # Or "" to erase subtitle.
        self.subtitle = fname
        if fname:
            self.set_title("%s: %s" % (self.BASE_TITLE, self.subtitle))
        else:
            self.set_title(self.BASE_TITLE)

    def uibuild (self):
        """Build the UI: generate widgets, add children, connect signals."""
        self.panes = gtk.VBox()
        self.add(self.panes)

        self.spans = gtk.HBox()

        self.padpane = gtk.VBox()

        self.connect("delete-event", self.on_delete_event)

        self.cmdcol = VisCmds(self.models.cmdstore)

        self.bindrow = gtk.VBox()
        self.bindpad = VisBind(self.store, self.models)
        self.bindrow.pack_start(self.bindpad)
        self.padpane.pack_start(self.bindrow)

        self.spans = gtk.HPaned()
        self.spans.add(self.padpane)
        self.spans.add(self.cmdcol)

        if self.menubar is None:
            self.menubar = self.MakeMenubar()
        self.statusbar = gtk.Statusbar()
        self.panes.pack_start(self.menubar, expand=False, fill=True)
        self.panes.pack_start(self.spans, expand=False)

        if 1:
            self.uibuild_debug()

        self.panes.pack_start(self.statusbar, expand=False)
        self.dlg_about = DlgAbout()

    def uibuild_debug (self):
        """Build  UI elements for debugging."""
        self.debugrow = gtk.HBox()
        self.debugbuf = gtk.TextBuffer()
        self.debugwin = gtk.TextView(self.debugbuf)
        self.debugrow.pack_start(self.debugwin, expand=True, fill=True)
        debugpane = gtk.ScrolledWindow()
        debugpane.add_with_viewport(self.debugrow)
        #self.panes.pack_start(self.debugrow, expand=True, fill=True)
        self.panes.pack_start(debugpane, expand=True, fill=True)
        self.debugbuf.insert_at_cursor("Debug")
        self.debugbuf.insert_at_cursor(" ready:")
        self.debugbuf.insert_at_cursor("\n")
        # Overwrite global log object to take a tee stream.
        globals()['log'] = Log(Log.debug, TeeLog(self.debugbuf, sys.stderr))

    def on_delete_event (self, w, *args):
        """Closing window with the [X] button."""
        self.app.quit()

    def ask_open (self):
        """Present dialog for opening/loading file.
Returns: str - filename specified by user.
         None - operation canceled.
"""
        loadname = None
        dlg = gtk.FileChooserDialog("Open", None, action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=("Open",1, "Cancel", 0))
        response = dlg.run()
        if response == 1:
            loadname = dlg.get_filename()
#            if loadname[-4:] != ".cfg":
#                loadname = loadname + ".cfg"
        dlg.destroy()
        return loadname

    def ask_save (self):
        """Present dialog for writing/saving file
Returns: str - filename specified by user.
         None - operation canceled.
"""
        savename = None
        dlg = gtk.FileChooserDialog("Save As", None, action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=("Save",1, "Cancel",0))
        response = dlg.run()
        if response == 1:
            savename = dlg.get_filename()
            if savename[-4:] != ".cfg":
                savename = savename + ".cfg"
        dlg.destroy()
        return savename

    def ask_cmds (self):
        """Present dialog for source of commands.
Returns: str - path to sqlite3 resource/file.
         None - operation canceled
"""
        srcname = None
        dlg = gtk.FileChooserDialog("Commands Pack", None, action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=("Open",1, "Cancel", 0))
        response = dlg.run()
        if response == 1:
            srcname = dlg.get_filename()
        dlg.destroy()
        return srcname

    def display_about (self):
        """Show/run the dialog for About."""
        self.dlg_about.run()
        self.dlg_about.hide()



class MainMenubar (gtk.MenuBar):
    """MenuBar for the main window."""
    def __init__ (self, app, accelgroup=None):
        gtk.MenuBar.__init__(self)
        self.accelgroup = accelgroup
        self.app = app
        self.uibuild()

    def on_file_new (self, w, *args):
        app = self.app
        app.reset()
        return
    def on_file_open (self, w, *args):
        app = self.app
        loadname = self.app.ask_load_uri()
        if loadname:
            self.app.set_saveuri(loadname)
            self.app.load_in_place()
        return
    def on_file_save (self, w, *args):
        app = self.app
        if not app.save_in_place():
            return self.on_file_saveas(self, w, *args)
        return
    def on_file_saveas (self, w, *args):
        app = self.app
        savename = app.ask_save_uri()
        if savename:
            app.set_saveuri(savename)
            app.save_in_place()
        return
    def on_file_cmdpack (self, w, *args):
        app = self.app
        srcname = app.ask_cmds_uri()
        if srcname:
            app.set_cmdsuri(srcname)
            app.cmds_in_place()
        return
    def on_quit (self, w, *args):
        app = self.app
        app.quit()
        return
    def on_edit_copy (self, w, *args):
        app = self.app
        return
    def on_edit_cut (self, w, *args):
        app = self.app
        return
    def on_edit_paste (self, w, *args):
        app = self.app
        return
    def on_edit_options (self, w, *args):
        app = self.app
        return
    def on_debug_1 (self, w, *args):
        app = self.app
        log.debug("DEBUG 1")
        app.set_saveuri("/home/fredslee/devel/vismapping/testout.cfg")
        app.load_in_place()
        return
    def on_debug_2 (self, w, *args):
        app = self.app
        app.set_cmdsuri("/home/fredslee/devel/vismapping/cmdset/GunsOfIcarusOnline.sqlite3")
        app.cmds_in_place()
        return
    def on_debug_3 (self, w, *args):
        app = self.app
        return
    def on_help (self, w, *args):
        app = self.app
        return
    def on_about (self, w, *args):
        app = self.app
        app.display_about()
        return

    def uibuild (self):
        menu_desc = [
          ('_File', [
            ('_New', "<Control><Shift>n", self.on_file_new),
            ('_Open', "<Control>o", self.on_file_open),
            ('_Save', "<Control>s", self.on_file_save),
            ('Save _As', "<Control><Alt>s", self.on_file_saveas),
            None,
            ('_CommandPack', self.on_file_cmdpack),
            None,
            ('_Quit', "<Control>q", self.on_quit),
            ]),
          ('_Edit', [
            ('_Copy', "<Control>c", self.on_edit_copy),
            ('C_ut', "<Control>x", self.on_edit_cut),
            ('_Paste', "<Control>v", self.on_edit_paste),
            None,
            ('_Options', self.on_edit_options),
            ]),
          ('_DEBUG', [
            ('Debug _1', self.on_debug_1),
            ('Debug _2', self.on_debug_2),
            ('Debug _3', self.on_debug_3),
            ]),
          ('_Help', [
            ('_Help', self.on_help),
            None,
            ('_About', self.on_about),
            ]),
          ]
        return BuildMenuBar(menu_desc, self, self.accelgroup)



class VisMapperModels (object):
    """Collection of data models for the GUI."""
    def __init__ (self, cmdstore=None, modestore=None, bindstore=None):
        self.cmdstore = cmdstore
        self.modestore = modestore
        self.bindstore = bindstore



class VisMapperApp (object):
    """Overall application object, with app/GUI state information."""
    def __init__ (self):
        self.store = Store(8)
        #self.mdl = kblayout.InpDescrModel(1)
        #self.ui = VisMapperWindow(self, self.mdl)

        self.cmdsuri = DEFAULT_DBNAME + ".sqlite3"
        self.cmdsrc = Commands(self.cmdsuri)
        #self.cmdstore = build_treestore_from_commands(self.cmdsrc, None)
        self.cmdstore = CmdStore(self.cmdsrc)
        self.cmdset = None
        self.set_cmdsuri(DEFAULT_DBNAME + ".sqlite3")
        #self.cmds_in_place()

        self.modenum = 0
        self.levelnum = 0
        mdl = self.store.inpdescr
        self.accelgroup = gtk.AccelGroup()

        self.models = VisMapperModels()
        self.models.cmdstore = self.cmdstore
        self.models.bindstore = self.store
        self.models.modestore = ModeStore(self.cmdsrc)

        menubar = MainMenubar(self, self.accelgroup)
        self.ui = VisMapperWindow(self, self.store, menubar=menubar, models=self.models)
        self.ui.add_accel_group(self.accelgroup)
        self.saveuri = None     # Config file.
        # Commands Pack file name.
        self.uibuild()

    def uibuild (self):
        """Setup and connect UI elements."""
        kbl = self.ui.bindpad.kbl
        cmdview = self.ui.cmdcol
        kbl.connect("dnd-link", self.on_kbl_dndlink)
        visbind = self.ui.bindpad
        visbind.connect('mode-changed', self.on_kbmode_changed)
        visbind.connect('level-changed', self.on_kblevel_changed)

    def on_kbmode_changed (self, w, modenum, *args):
        """Keyboard layout mode changed; update mdl."""
#        # Save current Layers to modes[current_mode]
#        sav = self.store.inpdescr.layers
#        self.store.modes[self.modenum] = sav
#        # Load new Layers from modes[new_mode]
        # Point to new Layers.
        cur = self.store.modes[modenum]
        self.store.inpdescr.layers = cur
        # Store new mode as current.
        self.modenum = modenum
        log.debug(" ? changing to mode %d" % modenum)
        mdl = self.store.inpdescr
        # update displays by forcing level change event.
        mdl.set_layer(mdl.get_layer())
        return

    def on_kblevel_changed (self, w, levelnum, *args):
        self.levelnum = levelnum
        mdl = self.store.inpdescr
        mdl.set_layer(levelnum)
        log.debug("changing to shift level %d" % levelnum)
        return

    def on_kbl_dndlink (self, w, dstw, srcw, dnddata, *args):
        log.debug("on_kbl_dndlink: dstw=%r, srcw=%r, dnddata=%r" % (dstw, srcw, dnddata))
        inpsym = dstw.inpsym
        levelnum = self.levelnum
        bindval = dnddata
        mdl = self.store.inpdescr
        mdl.set_bind(levelnum, inpsym, bindval)
        return

#    def on_kbl_drop (self, w, ctx, x, y, t, *args):
#        w.drag_get_data(ctx, "STRING", time)
#        # Initiates drag-data transfer.
#        return True
#
#    def on_kbl_drag_data_received (self, w, ctx, x, y, sel, info, t, *args):
#        srcw = ctx.get_source_widget()
#        bindid = int(self.get_text())
#        ctx.finish(True, False, time)
#        bindval = "UNKNOWN"
#        layernum = 0  # from store?
#        #self.mdl.set_bind(layernum, w.inpsym, bindval)
#        print("Handled KbLayout drag data received")

    # Operations re: File
    def get_saveuri (self):
        return self.saveuri
    def set_saveuri (self, val):
        self.saveuri = val
        basename = os.path.basename(val)
        self.ui.use_filename(basename)
    def ask_save_uri (self):
        """Called by MenuBar upon File/SaveAs, to run the SaveAs dialog."""
        return self.ui.ask_save()
    def save_in_place (self):
        """Save to file specified by internal state 'saveuri'."""
        if self.saveuri:
            savefile = open(self.saveuri, "wb")
            self.save(savefile)
            savefile.close()
        return
    def ask_load_uri (self):
        """Called by MenuBar upon File/Open, to run the Open dialog"""
        return self.ui.ask_open()
    def load_in_place (self):
        """Load from file specified by internal state 'saveuri'."""
        if self.saveuri:
            loadfile = open(self.saveuri, "rb")
            self.load(loadfile)
            loadfile.close()
        return

    def get_cmdsuri (self):
        return self.cmdsuri
    def set_cmdsuri (self, val):
        self.cmdsuri = val
        if not self.cmdset:
            self.cmdset = Commands(self.cmdsuri)
    def ask_cmds_uri (self):
        return self.ui.ask_cmds()
    def cmds_in_place (self):
        if self.cmdsuri:
            self.cmdset = Commands(self.cmdsuri)
            self.models.cmdstore.clear()
            self.models.cmdstore.import_commands(self.cmdset)
            self.models.modestore.clear()
            self.models.modestore.import_commands(self.cmdset)
        return

    def display_about (self):
        self.ui.display_about()


    def cmds (self, srcpath):
        log.debug("LOADING CMDS: %r" % srcpath)
        return 0

    def load (self, srcfile):
        """Load configuration from file-like object."""
        log.debug("LOADING %r" % srcfile)
        self.store.load(srcfile)
        return 0

    def save (self, destfile):
        """Save configuration to file-like object."""
        self.store.save(destfile)
        log.debug("SAVING %r" % destfile)
        return 0

    def reset (self):
        self.store.reset()
        self.ui.reset()

    def quit (self):
        gtk.main_quit()

    def go (self):
        # Instanced method.
        self.ui.show_all()
        gtk.mainloop()

    @staticmethod
    def main ():
        self = VisMapperApp()
        self.go()



if __name__ == "__main__":
    VisMapperApp.main()


