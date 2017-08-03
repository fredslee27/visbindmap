#!/usr/bin/env python
# vim: set expandtab tabstop=4 :

import gtk, gobject
import sys, os, os.path
import sqlite3

import pprint
import pickle
import ast, parser

import kbd_desc  # hard-coded keyboard layouts
import hidlayout
from hidlayout import Logger
from hidlayout import DndOpcodes


PACKAGE="VisMapper"
VERSION="0.0.1"

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

logger = hidlayout.logger
#logger.level = logger.info



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


"""Application states:

BindStore:
 Central data, maps actions onto an input element for a given group and layer.
 Expected to be usable by other applications in a toolchain.
 Most notable as "Export".

Run:
 Run-time state information not expected to last beyond application termination.
 Nominally corresponds to one session, but a session can outlast a run.
 These states are embedded into the GUI widgets, but explicitly specified here for distinction.

Session:
 One user's interaction with a BindStore.
 Encompasses command pack, visual states, and Undo history.
 Intended to be checkpointable.
 Most notable as auto-save, save/load.

Preferences:
 State information that persists across sessions ("New", "Load", etc.).
 Most notable in determining initial visual state on "New".

"""


class AppPreferences (object):
    """Persists across sssions."""
    def __init__ (self):
        pass

class AppSession (object):
    """User's interaction with a particular BindStore, checkpointable.
Also the save file.
"""
    FORMAT_VERSION = 1
    def __init__ (self):
        self.bindstore = None   # BindStore.
        self.cmdinfo = None     # CommandInfo.
        self.uri_bindstore = None  # path to last saved/loaded BindStore
        self.uri_cmdinfo = None    # path to last saved/loaded CommandInfo
        self.undostack = None   # undo stack.
        self.ui_snapshot = None
        self.reset()

    def reset (self):
        """Re-initialize states to new session."""
        # TODO: determine ngroups and nlayers
        #self.bindstore.clear()
        if self.bindstore is None:
            self.bindstore = hidlayout.BindStore(8,8)
        else:
            self.bindstore.clear()
        self.initial_clustertypes()
        self.cmdinfo = hidlayout.CommandInfo.from_uri(None)
        self.uri_bindstore = None
        self.uri_cmdinfo = None
        #self.undostack = AppUndo()
        self.ui_snapshot = None

    def initial_clustertypes (self):
        self.bindstore[0][0]['LP#'] = "DirectionPad"
        self.bindstore[0][0]['RP#'] = "MousePad"
        self.bindstore[0][0]['L#'] = "Joystick"
        self.bindstore[0][0]['R#'] = "Joystick"
        self.bindstore[0][0]['B#'] = "ButtonQuad"
        self.bindstore[0][0]['DP#'] = "DirectionPad"
        self.bindstore[0][0]['GY#'] = "GyroTilt"
        return

    def snapshot (self, destfileobj):
        """Write session to persistent storage; usable as Save."""
        enc = {
            "bindstore": self.bindstore,
            "cmdinfo": self.cmdinfo,
            "uri_bindstore": self.uri_bindstore,
            "uri_cmdinfo": self.uri_cmdinfo,
            "undostack": self.undostack,
            "ui_snapshot": None,
            }
        if destfileobj:
            destfileobj.write("# {} {} ast.literal_eval\n".format(PACKAGE, self.FORMAT_VERSION))
            destfileobj.write(repr(enc))
        return enc

    @staticmethod
    def reinstantiate (object_desc):
        if object_desc is None:
            return None
        try:
            classname = object_desc['.class']
        except (KeyError, TypeError):
            return object_desc
        temp = dict(object_desc)
        del temp['.class']
        print("classname = %r" % classname)
        if classname == hidlayout.BindStore.__name__:
            inst = hidlayout.BindStore(**temp)
        elif classname == hidlayout.CommandPackStore.__name__:
            inst = hidlayout.CommandPackStore(**temp)
        else:
            for classobj in hidlayout.CommandInfo.REGISTRY:
                if classname == classobj.__name__:
                    inst = classobj(**temp)
                    break
        return inst

    def resume (self, srcfileobj):
        """Restore session from persistent storage; usable as Load."""
        enc = ast.literal_eval(srcfileobj.read())

        self.bindstore = self.reinstantiate(enc['bindstore'])
        self.cmdinfo = self.reinstantiate(enc['cmdinfo'])
        self.uri_bindstore = self.reinstantiate(enc['uri_bindstore'])
        self.uri_cmdinfo = self.reinstantiate(enc['uri_cmdinfo'])
        self.undostack = self.reinstantiate(enc['undostack'])
        self.ui_snapshot = self.reinstantiate(enc['ui_snapshot'])
        return

    def export_bindstore (self):
        """Save just BindStore in an interchange format."""
        return

    def import_bindstore (self):
        """Load BindStore from an interchange format."""
        return





class ObjectReinstantiater(ast.NodeTransformer):
    """Traverse Abstract Syntax Tree to filter allowed object instantiation."""
    # Classes allowed to be instantiated.  Otherwise becomes None.
#    REINSTANCERS = {
#        "hidlayout.InpDescrModel": hidlayout.InpDescrModel,
#        "hidlayout.InpLayer": hidlayout.InpLayer,
#        "hidlayout.InpGroup": hidlayout.InpGroup,
#        }
    def nop (self, node=None):
        return ast.parse("None", mode='eval')
    def visit_Call (self, node):
#        cmodule = node.func.value.id
#        cclass = node.func.attr
#        ckey = "%s.%s" % (cmodule, cclass)
#        if ckey in self.REINSTANCERS:
#            #logger.debug("Invoke %s.%s(**%r)" % (cmodule, cclass, kwargs))
#            return node
#        else:
#            return ast.parse("None", mode='eval')
        return ast.parse("None", mode='eval')
    def visit_Yield (self, node): return self.nop()
    def visit_Lambda (self, node): return self.nop()
    def visit_IfExp (self, node): return self.nop()


# Persistant storage.
class Store (object):
    DEFAULT_FILENAME = BASENAME + ".cfg"

    def reset (self):
        try:
            self.bindstore
        except AttributeError:
            self.bindstore = hidlayout.BindStore(self._nummodes, self._numlevels)
        self.bindstore.clear()
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
#        self.inpdescr.restore(storedict.get('inpdescr',None))
#        self.inpdescr.refresh()
        # TODO: load BindStore from file.
        self.cmdsuri = storedict.get("cmdsuri", None)
        self.active_layout = storedict.get('layout', None)

    def save (self, fileobj=None):
        if fileobj is None:
            fileobj = open(self.fname, "wb")
            fileobj.write(self.modes)
        storedict = {
            'layout': self.active_layout,
            'bindstore': self.bindstore,
            'cmdsuri': self.cmdsuri,
            }
        pprint.pprint(storedict, fileobj, indent=2, width=132)
        fileobj.write("\n")




@hidlayout.CommandInfo.register
class CommandInfo_sqlite3 (hidlayout.CommandInfo):
    def build (self):
        dbname = self._path
        self.conn = sqlite3.connect(dbname)
        cursor = self.conn.cursor()

        # Get pack name.
        packname = os.path.basename(dbname)
        try:
            rows = cursor.execute('''SELECT packname FROM packname LIMIT 1;''')
            row = rows.fetchone()
            packname = row[0]
        except sqlite3.OperationalError:
            pass
        cmdpack = hidlayout.CommandPackStore(packname)

        # Get modes.
        try:
            rows = cursor.execute('''SELECT name FROM modes ORDER BY id;''')
        except sqlite3.OperationalError:
            rows = []
        modelist = gtk.ListStore(str,str)
        modelist.append( ("Global", None) )
        for row in rows:
            modename = row[0]
            fallthrough = "Global"
            modelist.append( (modename, fallthrough) )
        self._modelist = modelist

        # Get groups.
        rows = cursor.execute('''SELECT grp FROM cmd GROUP BY grp ORDER BY id;''')
        grpnames = [ row[0] for row in rows ]

        grploc = {}
        grptree = {}
        for grpname in grpnames:
            grpiter = None
            grpnode = grptree
            parts = grpname.split('/')
            prefix = []
            for k in parts:
                prefix.append(k)
                ancestorkey = '/'.join(prefix)
                if not k in grpnode:
                    # Create ancestor.
                    grpiter = cmdpack.append(grpiter, (-1, "", k, ""))
                    grploc[ancestorkey] = grpiter
                    grpnode[k] = dict()
                else:
                    # Lookup ancestor.
                    grpiter = grploc[ancestorkey]
                # Keep drilling.
                grpnode = grpnode[k]

        # Iterate all rows.
        stmt = '''SELECT id,layer,grp,cmd,label,hint FROM cmd;'''
        try:
            rows = cursor.execute(stmt)
        except sqlite3.OperationalError:
            rows = []
        for row in rows:
            cmdid, lyr, grp, cmd, lbl, hint = row
            if lbl is None:
                lbl = cmd
            datum = (cmdid, cmd, lbl, hint)
            # Find group, attach to group.
            grpiter = grploc.get(grp, None)
            cmdpack.append(grpiter, datum)

        self._cmdpack = cmdpack
        self.packname = packname
    @staticmethod
    def is_acceptable (uri):
        try:
            # Check if it quacks like a string.
            uri.isalpha
            return True
        except:
            return False




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
        #self.bindview.reset()
        self.bindview.set_bindstore(self.session.bindstore)
        self.bindview.ui.selectors.frob_group(0)
        self.bindview.ui.selectors.frob_layer(0)
        #self.bindview.update_bindstore()

    def __init__ (self, parent=None, menubar=None, session=None):
        self.app = parent

        gtk.Window.__init__(self)
        self.set_title("%s" % self.BASE_TITLE)
        self.subtitle = ""

        #self.models = models
        self.session = session
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

        self.cmdcol = hidlayout.CommandPackView(self.session.cmdinfo.get_cmdpack())
        self.bindrow = gtk.VBox()
        #self.bindview = hidlayout.BindableLayoutWidget(hidlayout.implicit_layouts,"PS3",self.models.bindstore.bindstore)

        # Build HidLayouts from kbd_desc.KBD
        self.all_layouts = hidlayout.HidLayouts()
        #self.bindview = hidlayout.BindableLayoutWidget(hidlayout.implicit_layouts, "SteamController", self.session.bindstore)
        for k in sorted(kbd_desc.KBD.keys()):
            layout = hidlayout.HidLayoutStore(k)
            layout.build_from_rowrun(kbd_desc.KBD[k])
            self.all_layouts.append( (k,layout) )
        # Layers labels.
        mdl_layers = gtk.ListStore(int, str)
        maxshifters = 3  # TODO: calculate.
        maxlayers = (1 << maxshifters)
        for lyrnum in range(0, maxlayers):
            sh = []
            # List the shifters that are involved in activating this layer.
            for b in range(0, maxshifters):
                if (lyrnum & (1 << b)):
                    sh.append("^%s" % (b+1))
            if sh:
                lbl = "{} ({})".format(lyrnum, " + ".join(sh))
            else:
                lbl = "base"
            rowdata = (lyrnum, lbl)
            mdl_layers.append(rowdata)

        self.bindview = hidlayout.BindableLayoutWidget(self.all_layouts, "SteamController", mdl_modes=self.session.cmdinfo.get_modelist(), mdl_layers=mdl_layers, bindstore=self.session.bindstore)
        self.bindrow.pack_start(self.bindview)
        self.padpane.pack_start(self.bindrow)

        self.spans = gtk.HPaned()
        self.spans.add(self.cmdcol)
        # TODO: proportional to font.
        self.cmdcol.set_size_request(180, -1)
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
            #app.cmds_in_place()
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
        #app.load_in_place()
        return
    def on_debug_2 (self, w, *args):
        app = self.app
        app.set_cmdsuri("/home/fredslee/devel/vismapping/cmdset/KerbalSpaceProgram.sqlite3")
        #app.cmds_in_place()
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
    def __init__ (self, cmdstore=None, modestore=None, bindstore=None, dispstate=None, accelgroup=None):
        self.dispstate = dispstate
        self.cmdstore = cmdstore
        self.modestore = modestore
        self.bindstore = bindstore
        self.accelgroup = accelgroup



class VisMapperApp (object):
    """Overall application object, with app/GUI state information."""
    def __init__ (self):
        self.modenum = 0
        self.levelnum = 0

        self.session = AppSession()
        self.accelgroup = gtk.AccelGroup()

        menubar = MainMenubar(self, self.accelgroup)
        self.ui = VisMapperWindow(self, menubar=menubar, session=self.session)
        self.ui.add_accel_group(self.accelgroup)
        self.build_ui()

        self.set_cmdsuri(DEFAULT_DBNAME + ".sqlite3")
        #self.cmds_in_place()

    def build_ui (self):
        """Setup and connect UI elements."""
        #hidl = self.ui.bindview.hidl
        hidview = self.ui.bindview.ui.hidview
        cmdview = self.ui.cmdcol
        visbind = self.ui.bindview
        #visbind.connect('mode-changed', self.on_kbmode_changed)
        #visbind.connect('level-changed', self.on_kblevel_changed)

    def update_main_title (self):
        cmdname = self.session.cmdinfo.get_packname() if self.session.cmdinfo else None
        storepath = self.session.uri_bindstore or None
        if storepath:
            basename = os.path.basename(storepath)
        else:
            basename = None
        self.ui.update_title(cmdname, basename)

    def on_kbmode_changed (self, w, modenum, *args):
        """Keyboard layout mode changed; update mdl."""
        self.modenum = modenum
        #mdl = self.models.bindstore.inpdescr
        #mdl.set_group(modenum)
        #self.models.dispstate.set_group(modenum)
        logger.debug(" ? changing to mode %d" % modenum)
        return

    def on_kblevel_changed (self, w, levelnum, *args):
        self.levelnum = levelnum
        #mdl = self.models.bindstore.inpdescr
        #mdl.set_layer(levelnum)
        #self.models.dispstate.set_layer(levelnum)
        logger.debug("changing to shift level %d" % levelnum)
        return

    # Operations re: File
    def get_saveuri (self):
        #return self.saveuri
        #return self.models.bindstore.fname
        return self.session.uri_bindstore
    def set_saveuri (self, val):
        #self.models.bindstore.fname = val
        self.session.uri_bindstore = val
        #basename = os.path.basename(val)
        self.update_main_title()
    def ask_save_uri (self):
        """Called by MenuBar upon File/SaveAs, to run the SaveAs dialog."""
        return self.ui.ask_save()
    def save_in_place (self):
        """Save to file specified by internal state 'saveuri'."""
        print("saving?")
        if self.get_saveuri():
            #savefile = open(self.models.bindstore.fname, "wb")
            #savefile = open(self.session.uri_bindstore, "wb")
            fname = self.get_saveuri()
            savefile = open(fname, "wb")
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
            loadfile = open(self.session.uri_bindstore, "rb")
            self.load(loadfile)
            loadfile.close()
            # TODO: restore GUI states?
#            if self.models.bindstore.active_layout:
#                self.ui.bindview.set_layout(self.models.bindstore.active_layout)
            return True
        return False

    # Operations re: CommandPack
    def get_cmdsuri (self):
        #return self.models.bindstore.cmdsuri
        return self.session.uri_cmdpack
    def set_cmdsuri (self, val):
        #self.models.bindstore.cmdsuri = val
        self.session.uri_cmdpack = val
        self.update_cmdsuri()
    def ask_cmds_uri (self):
        return self.ui.ask_cmds()
#    def cmds_in_place (self):
#        if self.session.uri_cmdpack:
#            try:
#                self.cmdsrc = Commands(self.session.uri_cmdpack)
#            except sqlite3.OperationalError:
#                self.cmdsrc = CommandsFallback()
#            #self.models.cmdstore.clear()
#            #self.models.cmdstore.import_commands(self.cmdsrc)
#            #self.models.modestore.clear()
#            #self.models.modestore.import_commands(self.cmdsrc)
#            self.update_main_title()
#        return
    def update_cmdsuri (self):
        if self.session.uri_cmdinfo:
            cmdinfo = None
            try:
                cmdinfo = CommandInfo_sqlite3(self.session.uri_cmdpack)
            except sqlite3.OperationalError:
                pass
            if cmdinfo:
                self.session.cmdinfo = cmdinfo
                self.ui.cmdcol.set_model(self.session.cmdinfo.get_cmdpack())
                # TODO: update modes list model
                self.ui.bindview.set_modelist(self.session.cmdinfo.get_modelist())

    def get_vislayers (self):
        hidv = self.ui.bindview
        return hivl.get_nvislayers()
    def set_vislayers (self, v):
        hidv = self.ui.bindview
        hidv.set_nvislayers(v)

    def display_about (self):
        self.ui.display_about()


    def cmds (self, srcpath):
        logger.debug("LOADING CMDS: %r" % srcpath)
        return 0

    def load (self, srcfile):
        """Load configuration from file-like object."""
        logger.debug("LOADING %r" % srcfile)
        #self.models.bindstore.load(srcfile)
        #self.session.bindstore.load(srcfile)
        #self.cmds_in_place()
        self.session.resume(srcfile)
        self.ui.reset()  # TODO: appropriate?
        return 0

    def save (self, destfile):
        """Save configuration to file-like object."""
        #self.models.bindstore.save(destfile)
        #self.session.bindstore.save(destfile)
        self.session.snapshot(destfile)
        logger.debug("SAVING %r" % destfile)
        return 0

    def reset (self):
        #self.models.bindstore.reset()
        self.session.reset()
        #self.models.dispstate.cluster_defaults()
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


