#!/usr/bin/env python
# vim: set expandtab tabstop=4 :

import gtk
import sqlite3

import pprint
import pickle

import kblayout


BASENAME="factorio"
DEFAULT_DBNAME="cmds"


def crumb (x):
    pass


def BuildMenuBar (menubardesc):
    def BuildMenuItem (itemdesc):
        if itemdesc is None: return gtk.SeparatorMenuItem()  # separator
        retval = gtk.MenuItem(itemdesc[0])
        if callable(itemdesc[1]):  # leaf
            retval.connect("activate", itemdesc[1])
        elif hasattr(itemdesc[1], "__getslice__"):  # submenu
            retval.set_submenu(BuildMenu(itemdesc[1]))
        return retval
    def BuildMenu (menudesc, menu=None):
        menu = menu or gtk.Menu()
        map(menu.append, map(BuildMenuItem, menudesc))
        return menu
    return BuildMenu(menubardesc, gtk.MenuBar())



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


# Persistant storage.
class Store (object):
    DEFAULT_FILENAME = BASENAME + ".cfg"

    def reset (self):
        self.binddata = []
        for n in range(self._numlevels):
            self.binddata.append([])
            for m in range(self._numlayers):
                self.binddata[n].append({})

    def __init__ (self, numlayers=8, numlevels=8, backingFileName=None):
        # list of bindings, one binding per layer (typically 8 layers).
        # bindings are mapping SDL_binding => command
        self._numlayers = numlayers
        self._numlevels = numlevels
        self.reset()
        self.fname = backingFileName
        if not backingFileName:
            self.fname = self.DEFAULT_FILENAME

    def load (self, fileobj=None):
        if fileobj is None:
            fileobj = open(self.fname, "rb")
        #fileobj = open(fname, "rb")
        self.binddata = pickle.load(fileobj)
        #fileobj.close()

    def save (self, fileobj=None):
        if fileobj is None:
            fileobj = open(self.fname, "wb")
        #fileobj = open(fname, "wb")
        pickle.dump(self.binddata, fileobj)
        #fileobj.close()



def build_treestore_from_commands(cmds_db, treestore=None):
    if treestore is None:
        treestore = gtk.TreeStore(int, str, str, str, object)

    # First, the unbind item.
    treestore.append(None, (0, "", "(unbind)", "", cmds_db))

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
            treeiter = treestore.append(parentiter, (0, "", suffix, "", cmds_db))
            groupheads[grpname] = treeiter
        else:
            if not groupheads.has_key(grpname):
                treeiter = treestore.append(None, (0, "", grp, "", cmds_db))
                groupheads[grpname] = treeiter

    for grp in cmds_db.groups:
        make_group(grp)

    for cmdinfo in cmds_db:
        (cmdid, layer, grp, cmd, desc, hint) = cmdinfo
        grpiter = groupheads[grp]
        if not desc:
            desc = cmd
        row = (cmdid, cmd, desc, hint, cmds_db)
        treeiter = treestore.append(grpiter, row)



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
            print("[None]=>None...")
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
            print("find(None) => None")
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
    DEFAULT_DATASOURCE = DEFAULT_DBNAME + ".sqlite3"

    def __init__ (self, datasrc=None):
        gtk.VBox.__init__(self)
        # id, cmd, display, hint

        self.cmdlist = gtk.TreeStore(int, str, str, str, object)

        if datasrc is None:
            datasrc = self.DEFAULT_DATASOURCE
        self.cmds = Commands(datasrc)
        self.cmds.build_treestore(self.cmdlist)

        self.entry = gtk.TreeView(self.cmdlist)
        self.entry.drag_source_set(gtk.gdk.BUTTON1_MASK, [ ("bind", gtk.TARGET_SAME_APP, 1), ], gtk.gdk.ACTION_LINK)
        self.entry.drag_source_set(gtk.gdk.BUTTON1_MASK, [ ("bindid", gtk.TARGET_SAME_APP, 1), ], gtk.gdk.ACTION_LINK)
        #self.entry.drag_source_set(gtk.gdk.BUTTON1_MASK, [ ("binduri", gtk.TARGET_SAME_APP, 1), ], gtk.gdk.ACTION_LINK)
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

    def on_drag_data_get (self, w, ctx, sel, info, time, *args):
        if sel.target == "bind":
            print("+++ target is bind")
            srcw = ctx.get_source_widget()
            treesel = srcw.get_selection()
            (treemdl, treeiter) = treesel.get_selected()

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                #sel.data = None
                sel.set_text("", 0)
#                ctx.drop_finish(False, 0)
                return
            # Get the command to bind.
            val = treemdl.get_value(treeiter, 1)

#            print("using val=%r" % val)
            #sel.set_text(val, len(val))
            sel.set("STRING", 8, val)  # 8 bits per unit.
        elif sel.target == "bindid":
            print("+++ target is bindid")
            srcw = ctx.get_source_widget()
            treesel = srcw.get_selection()
            (treemdl, treeiter) = treesel.get_selected()

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                #sel.data = None
                sel.set_text("", 0)
#                ctx.drop_finish(False, 0)
                return
            # Get the command to bind.
            val = treemdl.get_value(treeiter, 0)

#            print("using val=%r" % val)
            #sel.set_text(val, len(val))
            sel.set("STRING", 8, str(val))  # 8 bits per unit.
        elif sel.target == "binduri":
            print("%s drag-data-get: w = %r" % (self.__class__.__name__, w))
            # Find out target, get its inpsym, assign binding.
            # Send displayed text to target.
            print("+++ target is bindref")
            srcw = ctx.get_source_widget()
            treesel = srcw.get_selection()
            (treemdl, treeiter) = treesel.get_selected()

            if treemdl.iter_has_child(treeiter):
                # non-terminal item; fail.
                sel.set_text("", 0)
                return
            # Get the command to bind.
            num = treemdl.get_value(treeiter, 0)
            name = treemdl.get_value(treeiter, 1)
            val = "cmdbind://%s/%s" % (num, name)
            print("+++  val = %r" % val)
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


    def __init__ (self, store, cmds=None, inpdescr=None):
        gtk.VBox.__init__(self)

        self.store = store
        self.cmds = cmds
        self.inpdescr = inpdescr

        self.uibuild()

        self.reset()

    def uibuild (self):
        self.shiftrow = self.InpSelectLevel()
        self.pack_start(self.shiftrow)

        self.moderow = self.InpSelectMode()
        self.pack_start(self.moderow)

        # grid/tablular layout of inpbind+bindcmd
        self.kbl = kblayout.KblayoutWidget(self.inpdescr)
#        self.kbl.connect("key-selected", self.on_key_selected)
#        self.kbl.connect("bind-changed", self.on_bind_changed)
#        self.kbl.connect("bindid-changed", self.on_bindid_changed)
#        self.kbl.connect("layout-changed", self.on_layout_changed)

        self.pack_start(self.kbl, expand=False, fill=False)

    def on_key_selected (self, w, ksym, *args):
        print("key-selected: %s" % ksym)

    def on_layout_changed (self, w, layoutname, *args):
        self.relabel_keys(self.levelnum)
        self.load_bindmap(self.layernum)

    def on_bind_changed (self, w, keytop, *args):
        #print("VisBind.bind-changed: %r" % keytop)
        #self.bindmap[keytop.ksym] = keytop.bind
        pass

    def InpSelectMode (self):
        """Generate GUI Widget for selecting mode (layer)."""
        moderow = gtk.HBox()
        modebtns = gtk.HButtonBox()

        moderow.lbl = gtk.Label("MODE:")
        # "Select Layer" radio buttons.
        #modes = [ "(GLOBAL)", "Game", "Inventory", "Crafting", "Editor" ]
        modes = [ "*GLOBAL" ] + self.cmds.get_modes()
            
        moderow.btns = []  # private data.
        #moderow.pack_start(moderow.lbl, expand=False)
        for modeid in range(0, len(modes)):
            grp = moderow.btns and moderow.btns[0] or None    # is group leader or member.
            lbl = modes[modeid]
            btn = gtk.RadioButton(grp, lbl)  # create element.
            btn.layernum = modeid  # private data
            btn.connect('clicked', self.on_mode_toggle)  # react
            modebtns.add(btn)  # GUI
            moderow.btns.append(btn)  # internal storage.
        moderow.pack_start(modebtns, expand=False)

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
            btn.connect('clicked', self.on_shifter_toggle)  # react
            btns.append(btn)
            shiftbtns.add(btn)
        shiftrow.btns = btns
        shiftrow.pack_start(shiftbtns, expand=True)
        #return shiftrow
        shiftbox.add(shiftrow)
        return shiftbox

    def save_bindmap (self, bindmask):
        crumb("\f")
        crumb("save_bindmap -- nop")
        pass

    def load_bindmap (self, layernum):
        """Load binding map: update visual keys with bindings from given layer."""
        return

    def relabel_keys (self, levelnum):
        pass

    def on_mode_toggle (self, w, *args):
        pass

    def on_shifter_toggle (self, w, *args):
        pass

    def bind_cmd (self, ksym, cmdinfo):
        pass

    def unbind_cmd (self, ksym):
        pass


class DlgAbout (gtk.AboutDialog):
    def __init__ (self):
        gtk.AboutDialog.__init__(self)
        self.set_name("VisMapper")
        self.set_version("0.0.1")
        self.set_copyright("Copyright 2016  PhaethonH <PhaethonH@gmail.com>")
        self.set_license("GNU General Public License 3.0 or later")


class VisMapperWindow (gtk.Window):
    """Main window, majority of state information."""
    def reset (self):
        self.bindpad.reset()

    def __init__ (self, parent=None, inpdescr=None):
        self.inpdescr = inpdescr
        self.app = parent

        gtk.Window.__init__(self)
        self.set_title("Vismapper")

        self.saveuri = None

        self.store = self.app.store

        self.panes = gtk.VBox()
        self.add(self.panes)

        self.spans = gtk.HBox()

        self.padpane = gtk.VBox()

        self.connect("delete-event", self.on_quit)

        self.cmdcol = VisCmds()

        self.bindrow = gtk.VBox()
        self.bindpad = VisBind(self.store, self.cmdcol.cmds, self.inpdescr)
        self.bindrow.pack_start(self.bindpad)
        self.padpane.pack_start(self.bindrow)

        self.spans = gtk.HPaned()
        self.spans.add(self.padpane)
        self.spans.add(self.cmdcol)

        self.menubar = self.MakeMenubar()
        self.statusbar = gtk.Statusbar()
        self.panes.pack_start(self.menubar, expand=False, fill=True)
        self.panes.pack_start(self.spans, expand=False)

        if 1:
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
            def debugcrumb (x):
                if x == "\f":
                    self.debugbuf.delete(self.debugbuf.get_start_iter(), self.debugbuf.get_end_iter())
                else:
                    self.debugbuf.insert_at_cursor(x + "\n")
            globals()['crumb'] = debugcrumb

        self.panes.pack_start(self.statusbar, expand=False)

        self.dlg_about = DlgAbout()

    def MakeMenubar (self):
        menu_desc = [
          ('_File', [
            ('_New', self.on_new),
            ('_Open', self.on_open),
            ('_Save', self.on_save),
            ('Save _As', self.on_saveas),
            None,
            ('_Quit', self.on_quit),
            ]),
          ('_Edit', [
            ('_Copy', self.on_copy),
            ('C_ut', self.on_cut),
            ('_Paste', self.on_paste),
            None,
            ('_Options', self.on_options),
            ]),
          ('_Help', [
            ('_Help', self.on_help),
            None,
            ('_About', self.on_about),
            ]),
          ]

        return BuildMenuBar(menu_desc)

    def ask_open (self):
        loadname = None
        dlg = gtk.FileChooserDialog("Open", None, action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=("Open",1, "Cancel", 0))
        response = dlg.run()
        if response == 1:
            loadname = dlg.get_filename()
            if loadname[-4:] != ".cfg":
                loadname = loadname + ".cfg"
        dlg.destroy()
        return loadname

    def ask_save (self):
        savename = None
        dlg = gtk.FileChooserDialog("Save As", None, action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=("Save",1, "Cancel",0))
        response = dlg.run()
        if response == 1:
            savename = dlg.get_filename()
            if savename[-4:] != ".cfg":
                savename = savename + ".cfg"
        dlg.destroy()
        return savename

    def on_new (self, w, *args):
        self.app.reset()

    def on_open (self, w, *args):
        loadname = self.ask_open()
        if loadname:
            loadfile = open(loadname, "rb")
            self.store.load(loadfile)
            loadfile.close()
        #crumb("loaded binddata = %r" % (self.bindpad.bindlayers,))
        self.bindpad.moderow.btn_global.clicked()
        return

    def on_save (self, w, *args):
        if self.saveuri is None:
            # Dialog for filename.
            return self.on_saveas(w, *args)
        else:
            savefile = open(self.saveuri, "wb")
            self.app.save(savefile)
            savefile.close()
        return

    def on_saveas (self, w, *args):
        savename = self.ask_save()
        if savename:
            self.saveuri = savename
            savefile = open(savename, "wb")
            self.app.save(savefile)
            savefile.close()
        return

    def on_copy (self, w, *args):
        pass

    def on_cut (self, w, *args):
        pass

    def on_paste (self, w, *args):
        pass

    def on_options (self, w, *args):
        pass

    def on_help (self, w, *args):
        pass

    def on_about (self, w, *args):
        self.dlg_about.run()
        self.dlg_about.hide()

    def on_quit (self, w, *args):
        self.app.quit()




class VisMapperApp (object):
    """Overall application object."""
    def __init__ (self):
        self.store = Store(8)
        self.mdl = kblayout.InpDescrModel(1)
        self.ui = VisMapperWindow(self, self.mdl)
        self.uibuild()

    def uibuild (self):
        """Setup and connect UI elements."""
        kbl = self.ui.bindpad.kbl
        cmdview = self.ui.cmdcol
        kbl.connect("dnd-link", self.on_kbl_dndlink)
        print("- built")

    def on_kbl_dndlink (self, w, dstw, srcw, dnddata, *args):
        print("on_kbl_dndlink: dstw=%r, srcw=%r, dnddata=%r" % (dstw, srcw, dnddata))
        inpsym = dstw.inpsym
        layernum = 0
        bindval = "-NOT IMPLEMENTED-"
        self.mdl.set_bind(layernum, inpsym, bindval)
        pass

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


    def go (self):
        self.ui.show_all()
        gtk.mainloop()

    def load (self, srcfile):
        self.store.load(destfile)
        return 0

    def save (self, destfile):
        self.store.save(destfile)
        return 0

    def reset (self):
        self.store.reset()
        self.ui.reset()

    def quit (self):
        gtk.main_quit()



if __name__ == "__main__":
    #s = Store()
    #s.save()
    app = VisMapperApp()
    app.go()


