#!/usr/bin/env python
# vim: set expandtab tabstop=4 :

import gtk, gobject
import sys, os, os.path
import sqlite3

import pprint
import pickle
import ast, parser

import kblayout
from kblayout import Logger


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
logger = Logger(Logger.debug)



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
        "kblayout.InpGroup": kblayout.InpGroup,
        }
    def nop (self, node):
        return ast.parse("None", mode='eval')
    def visit_Call (self, node):
        cmodule = node.func.value.id
        cclass = node.func.attr
        ckey = "%s.%s" % (cmodule, cclass)
        if ckey in self.REINSTANCERS:
            #logger.debug("Invoke %s.%s(**%r)" % (cmodule, cclass, kwargs))
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
        try:
            self.inpdescr
        except AttributeError:
            self.inpdescr = kblayout.InpDescrModel(self._nummodes, self._numlevels)
        self.inpdescr.clear()
        self.fname = None
        self.cmdsuri = None

    def __init__ (self, nummodes=8, numlevels=8, backingFileName=None):
        # list of bindings, one binding per layer (typically 8 layers).
        # bindings are mapping SDL_binding => command.
        # modes are list of list-of-binding, typically 1 or 2.
        self._nummodes = nummodes
        self._numlevels = numlevels
        self.active_layout = None  # last selected layout (restore view on load).
        self.reset()
        self.fname = backingFileName
        if not backingFileName:
            self.fname = self.DEFAULT_FILENAME

    def load (self, fileobj=None):
        if fileobj is None:
            fileobj = open(self.fname, "rb")
        s = fileobj.read()
        astree = ast.parse(s, mode='eval')
        transformed = ObjectReinstantiater().visit(astree)
        storedict = eval(compile(transformed, '', 'eval'))
        self.inpdescr.restore(storedict.get('inpdescr',None))
        self.inpdescr.refresh()
        self.cmdsuri = storedict.get("cmdsuri", None)
        self.active_layout = storedict.get('layout', None)

    def save (self, fileobj=None):
        if fileobj is None:
            fileobj = open(self.fname, "wb")
            fileobj.write(self.modes)
        storedict = {
            'layout': self.active_layout,
            'inpdescr': self.inpdescr,
            'cmdsuri': self.cmdsuri,
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
            self.make_group(prefix)
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
        self.packname = None
#        self.db = [(0, "", "", "(none)", None)]
        # Open DB.
        self.conn = sqlite3.connect(dbname)
        # Pull relevant rows.
        cursor = self.conn.cursor()
        cursor.execute('''SELECT id,layer,grp,cmd,label,hint FROM cmd;''')

    def get_name (self):
        if self.packname is None:
            # Extract packname from table packname if it exists.
            try:
                cursor = self.conn.cursor()
                rows = cursor.execute('''SELECT packname FROM packname LIMIT 1;''')
                row = rows.fetchone()
                self.packname = row[0]
            except:
                pass
        return self.packname
    def set_name (self, val):
        self.packname = val

    def get_modes (self):
        cursor = self.conn.cursor()
        rows = cursor.execute('''SELECT name FROM modes ORDER BY id;''')
        modenames = []
        for row in rows:
            modename = row[0]
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
            logger.debug("[None]=>None...")
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
            logger.debug("find(None) => None")
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
            logger.debug("target is bind")

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                sel.set_text("", 0)
                return
            # Get the command to bind.
            val = treemdl.get_value(treeiter, 1)

            sel.set("STRING", 8, val)  # 8 bits per unit.
        elif sel.target == "bindid":
            logger.debug("target is bindid")

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                sel.set_text("", 0)
                return
            # Get the command to bind.
            val = treemdl.get_value(treeiter, 0)

            sel.set("STRING", 8, str(val))  # 8 bits per unit.
        elif sel.target == "binduri":
            logger.debug("%s drag-data-get: w = %r" % (self.__class__.__name__, w))
            # Find out target, get its inpsym, assign binding.
            # Send displayed text to target.
            logger.debug("+++ target is bindref")

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                sel.set_text("", 0)
                return
            # Get the command to bind.
            num = treemdl.get_value(treeiter, 0)
            name = treemdl.get_value(treeiter, 1)
            val = "cmdbind://%s/%s" % (num, name)
            logger.debug("val = %r" % val)
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


    def __init__ (self, models=None):
        gtk.VBox.__init__(self)

        self.models = models

        self.uibuild()

        self.set_layout("SteamController")

        self.reset()

    def uibuild (self):
        self.moderow = self.InpSelectMode()
        self.pack_start(self.moderow)

        self.shiftrow = self.InpSelectLevel()
        self.pack_start(self.shiftrow)

        # grid/tablular layout of inpbind+bindcmd
        inpdescr = self.models.bindstore.inpdescr
        self.kbl = kblayout.KblayoutWidget(inpdescr)
        self.kbl.connect('key-selected', self.on_key_selected)
        self.kbl.connect('layout-changed', self.on_layout_changed)

        self.pack_start(self.kbl, expand=False, fill=False)

    def on_key_selected (self, w, ksym, *args):
        binding = self.models.bindstore.inpdescr.get_bind(ksym)
        logger.debug("key-selected: %s => %r" % (ksym, binding))

    def get_layout (self):
        idx = self.kbl.inp_layout.get_active()
        retval = self.kbl.mdl_layout[idx][0]
        return retval
    def set_layout (self, layoutname):
        sel = self.kbl.inp_layout
        mdl = self.kbl.mdl_layout
        idx = -1
        for rownum in range(len(mdl)):
            if mdl[rownum][0] == layoutname:
                idx = rownum
        if idx > -1:
            sel.set_active(idx)

    def on_layout_changed (self, w, layoutname, *args):
        # Record chagne.
        self.models.bindstore.active_layout = layoutname

    def InpSelectMode (self):
        """Generate GUI Widget for selecting mode (layer)."""
        moderow = gtk.HBox()
        modebtns = gtk.HButtonBox()

        moderow.lbl = gtk.Label("MODE:")
        moderow.btns = []
        # "Select Layer" radio buttons.
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
        logger.debug("bind");
        pass

    def unbind_cmd (self, ksym):
        logger.debug("unbind");
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

    def __init__ (self, parent=None, menubar=None, models=None):
        self.app = parent

        gtk.Window.__init__(self)
        self.set_title("%s" % self.BASE_TITLE)
        self.subtitle = ""

        self.models = models
        self.menubar = menubar
        self.uibuild()

    def update_title (self, packname, bindname):
        wtitleparts = [ self.BASE_TITLE ]
        if packname:
            wtitleparts.extend([" ", "(", packname, ")"])
        if bindname:
            wtitleparts.extend([" : ", bindname])
        wtitle = "".join(wtitleparts)
        self.set_title(wtitle)

    def uibuild (self):
        """Build the UI: generate widgets, add children, connect signals."""
        self.panes = gtk.VBox()
        self.add(self.panes)

        self.spans = gtk.HBox()

        self.padpane = gtk.VBox()

        self.connect("delete-event", self.on_delete_event)

        self.cmdcol = VisCmds(self.models.cmdstore)

        self.bindrow = gtk.VBox()
        self.bindpad = VisBind(self.models)
        self.bindrow.pack_start(self.bindpad)
        self.padpane.pack_start(self.bindrow)

        self.spans = gtk.HPaned()
        self.spans.add(self.cmdcol)
        self.spans.add(self.padpane)

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
        globals()['logger'] = Logger(Logger.debug, TeeLog(self.debugbuf, sys.stderr))

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
        logger.debug("DEBUG 1")
        app.set_saveuri("/home/fredslee/devel/vismapping/testout.cfg")
        app.load_in_place()
        return
    def on_debug_2 (self, w, *args):
        app = self.app
        app.set_cmdsuri("/home/fredslee/devel/vismapping/cmdset/KerbalSpaceProgram.sqlite3")
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

    def on_view_levels (self, w, count, *args):
        app = self.app
        logger.debug("View levels = %d" % count)
        app.set_vislayers(count)
        pass

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
          ('_View', [
            ('_1 level', lambda w: self.on_view_levels(w, 1)),
            ('_2 levels', lambda w: self.on_view_levels(w, 2)),
            ('_4 levels', lambda w: self.on_view_levels(w, 4)),
            ('_8 levels', lambda w: self.on_view_levels(w, 8)),
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
    def __init__ (self, cmdstore=None, modestore=None, bindstore=None, accelgroup=None):
        self.cmdstore = cmdstore
        self.modestore = modestore
        self.bindstore = bindstore
        self.accelgroup = accelgroup



class VisMapperApp (object):
    """Overall application object, with app/GUI state information."""
    def __init__ (self):
        self.cmdsrc = None
        self.modenum = 0
        self.levelnum = 0

        self.models = VisMapperModels()
        self.models.cmdstore = CmdStore(self.cmdsrc)
        self.models.bindstore = Store(8)
        self.models.modestore = ModeStore(self.cmdsrc)
        self.models.accelgroup = gtk.AccelGroup()

        menubar = MainMenubar(self, self.models.accelgroup)
        self.ui = VisMapperWindow(self, menubar=menubar, models=self.models)
        self.ui.add_accel_group(self.models.accelgroup)
        # Commands Pack file name.
        self.uibuild()

        self.set_cmdsuri(DEFAULT_DBNAME + ".sqlite3")
        self.cmds_in_place()

    def uibuild (self):
        """Setup and connect UI elements."""
        kbl = self.ui.bindpad.kbl
        cmdview = self.ui.cmdcol
        kbl.connect("dnd-link", self.on_kbl_dndlink)
        visbind = self.ui.bindpad
        visbind.connect('mode-changed', self.on_kbmode_changed)
        visbind.connect('level-changed', self.on_kblevel_changed)

    def update_main_title (self):
        cmdname = self.cmdsrc and self.cmdsrc.get_name() or None
        bindname = self.models.bindstore.fname or None
        if bindname:
            basename = os.path.basename(bindname)
        else:
            basename = None
        self.ui.update_title(cmdname, basename)

    def on_kbmode_changed (self, w, modenum, *args):
        """Keyboard layout mode changed; update mdl."""
        self.modenum = modenum
        mdl = self.models.bindstore.inpdescr
        mdl.set_group(modenum)
        logger.debug(" ? changing to mode %d" % modenum)
        return

    def on_kblevel_changed (self, w, levelnum, *args):
        self.levelnum = levelnum
        mdl = self.models.bindstore.inpdescr
        mdl.set_layer(levelnum)
        logger.debug("changing to shift level %d" % levelnum)
        return

    def on_kbl_dndlink (self, w, dstw, srcw, dnddata, *args):
        logger.debug("on_kbl_dndlink: dstw=%r, srcw=%r, dnddata=%r" % (dstw, srcw, dnddata))
        inpsym = dstw.inpsym
        modenum = self.modenum
        levelnum = self.levelnum
        bindval = dnddata
        mdl = self.models.bindstore.inpdescr
        mdl.set_bind(inpsym, bindval,  group=modenum, layer=levelnum)
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
        #return self.saveuri
        return self.models.bindstore.fname
    def set_saveuri (self, val):
        self.models.bindstore.fname = val
        #basename = os.path.basename(val)
        self.update_main_title()
    def ask_save_uri (self):
        """Called by MenuBar upon File/SaveAs, to run the SaveAs dialog."""
        return self.ui.ask_save()
    def save_in_place (self):
        """Save to file specified by internal state 'saveuri'."""
        if self.get_saveuri():
            savefile = open(self.models.bindstore.fname, "wb")
            self.save(savefile)
            savefile.close()
            return True
        return False
    def ask_load_uri (self):
        """Called by MenuBar upon File/Open, to run the Open dialog"""
        return self.ui.ask_open()
    def load_in_place (self):
        """Load from file specified by internal state 'saveuri'."""
        if self.get_saveuri():
            loadfile = open(self.models.bindstore.fname, "rb")
            self.load(loadfile)
            loadfile.close()
            if self.models.bindstore.active_layout:
                self.ui.bindpad.set_layout(self.models.bindstore.active_layout)
            return True
        return False

    # Operations re: CommandPack
    def get_cmdsuri (self):
        return self.models.bindstore.cmdsuri
    def set_cmdsuri (self, val):
        self.models.bindstore.cmdsuri = val
        if not self.cmdsrc:
            self.cmdsrc = Commands(self.models.bindstore.cmdsuri)
    def ask_cmds_uri (self):
        return self.ui.ask_cmds()
    def cmds_in_place (self):
        if self.models.bindstore.cmdsuri:
            self.cmdsrc = Commands(self.models.bindstore.cmdsuri)
            self.models.cmdstore.clear()
            self.models.cmdstore.import_commands(self.cmdsrc)
            self.models.modestore.clear()
            self.models.modestore.import_commands(self.cmdsrc)
            self.update_main_title()
        return

    def get_vislayers (self):
        kbl = self.ui.bindpad.kbl
        return kbl.get_vislayers()
    def set_vislayers (self, v):
        kbl = self.ui.bindpad.kbl
        kbl.set_vislayers(v)
    def display_about (self):
        self.ui.display_about()


    def cmds (self, srcpath):
        logger.debug("LOADING CMDS: %r" % srcpath)
        return 0

    def load (self, srcfile):
        """Load configuration from file-like object."""
        logger.debug("LOADING %r" % srcfile)
        self.models.bindstore.load(srcfile)
        self.cmds_in_place()
        return 0

    def save (self, destfile):
        """Save configuration to file-like object."""
        self.models.bindstore.save(destfile)
        logger.debug("SAVING %r" % destfile)
        return 0

    def reset (self):
        self.models.bindstore.reset()
        self.ui.reset()
        self.update_main_title()

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


