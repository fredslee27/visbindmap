#!/usr/bin/env python
# vim: set expandtab tabstop=4 :

import gtk, gobject, glib, gio
import sys, os, os.path
import sqlite3

import pprint
import pickle
import ast, parser
import weakref

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
    SAVEKEYS = [ 'knowwhat' ]
    def __init__ (self):
        self.defaults()
        self.fetch()

    def defaults (self):
        self.knowwhat = False

    def config_path (self):
        path = os.path.join(glib.get_user_config_dir(),
                            PACKAGE,
                            "prefs")
        return path

    def fetch (self):
        """Load preferences from storage."""
        giofile = gio.File(path=self.config_path())
        try:
            contents,filelen,etag = giofile.load_contents()
        except:
            return
        enc = ast.literal_eval(contents)
        for k in self.SAVEKEYS:
            self.__dict__[k] = enc[k]
        return

    def commit (self):
        """Save preferences to storage."""
        enc = dict()
        for k in self.SAVEKEYS:
            enc[k] = self.__dict__[k]
        printable = pprint.pformat(enc, width=1024)

        oldumask = os.umask(0077)
        config_path = self.config_path()
        config_dir = os.path.dirname(config_path)
        giofile = gio.File(path=config_path)
        giodir = giofile.get_parent()
        if giodir:
            try:
                giodir.make_directory_with_parents()
            except:
                pass
        gioflags = gio.FILE_CREATE_PRIVATE | gio.FILE_CREATE_REPLACE_DESTINATION
        giostream = giofile.replace_contents(contents=printable, etag=None, make_backup=False, flags=gioflags, cancellable=None)
        os.umask(oldumask)
        return


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
        """Re-initialize states to a new session."""
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




# CommandInfo from sqlite3 file.
@hidlayout.CommandInfo.register
class CommandInfo_sqlite3 (hidlayout.CommandInfo):
    @staticmethod
    def is_acceptable (uri):
        try:
            # Check if it quacks like a string.
            uri.isalpha
            return True
        except:
            return False
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




class DlgAbout (gtk.AboutDialog):
    def __init__ (self):
        gtk.AboutDialog.__init__(self)
        self.set_name("VisMapper")
        self.set_version("0.0.1")
        self.set_copyright("Copyright 2016  PhaethonH <PhaethonH@gmail.com>")
        self.set_license("GNU General Public License 3.0 or later")


class DlgPreferences (gtk.Dialog):
    FORMDESC = [
        ("knowwhat", bool, "Suppress novice tooltips"),
        ]

    def __init__ (self, parent, prefs):
        self.prefs = prefs
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        btns = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,)
        gtk.Dialog.__init__(self, "Preferences", parent=parent, flags=flags, buttons=btns)
        self.formdata = {}
        self.setup_widget()
        self.setup_signals()
        self.reset()

    def reset (self):
        for formelt in self.FORMDESC:
            name, typ, descr = formelt
            w = self.widgets.get(name, None)
            if not w:
                continue
            if typ is bool:
                val = bool(self.prefs.__dict__.get(name, False))
                w.set_active(val)
                self.formdata[name ] = val
            else:
                pass
        return

    def setup_widget (self):
        vbox = self.vbox
        class ui: pass
        self.ui = ui
        self.widgets = dict()
        for formelt in self.FORMDESC:
            name, typ, descr = formelt
            init_val = self.prefs.__dict__.get(name, 0)
            w = None
            if typ is bool:
                w = gtk.CheckButton(descr)
                w.connect("toggled", self.on_checkbutton_toggled, name)
                w.props.has_tooltip = True
                w.knowwhat = "{}_{}".format("prefs", name)
                self.widgets[name] = w
            else:
                w = None
            if w:
                vbox.pack_start(w, False, False, 0)
        self.set_size_request(320,240)
        vbox.show_all()

    def setup_signals (self):
        pass

    def commit_prefs (self):
        for k,v in self.formdata.iteritems():
            self.prefs.__dict__[k] = v

    def on_checkbutton_toggled (self, w, name, *args):
        self.formdata[name] = w.get_active()


class VisMapperWindow (gtk.Window):
    """Main window, majority of state information."""
    BASE_TITLE = "Vismapper"

    def reset (self):
        """Reset window contents."""
        #self.bindview.reset()
        self.bindview.set_bindstore(self.session.bindstore)
        self.bindview.ui.selectors.frob_mode(0)
        self.bindview.ui.selectors.frob_layer(0)
        #self.bindview.update_bindstore()

    def __init__ (self, parent=None, menubar=None, prefs=None, session=None):
        self.app = parent

        gtk.Window.__init__(self)
        self.set_title("%s" % self.BASE_TITLE)
        self.subtitle = ""

        self.prefs = prefs
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

        # Build HidLayouts from kbd_desc.KBD
        self.all_layouts = hidlayout.HidLayouts()
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

        #self.bindview = hidlayout.BindableLayoutWidget(self.all_layouts, "PS3", mdl_modes=self.session.cmdinfo.get_modelist(), mdl_layers=mdl_layers, bindstore=self.session.bindstore)
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
        self.dlg_prefs = DlgPreferences(self, self.prefs)

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




class AppActions (gtk.ActionGroup):
    ACTIONS = [
        # Must also specify actions for submenus?
        ("file", None, "_File"),
        ("file.new", gtk.STOCK_NEW, "_New", "<Control>n"),
        ("file.open", gtk.STOCK_OPEN, "_Open", "<Control>o"),
        ("file.save", gtk.STOCK_SAVE, "_Save", "<Control>s"),
        ("file.saveas", gtk.STOCK_SAVE_AS, "Save _As", "<Control><Alt>s"),
        ("file.commandpack", None, "CommandPack"),
        ("file.quit", gtk.STOCK_QUIT, "_Quit", "<Control>backslash"),
        ("edit", None, "_Edit"),
        ("edit.copy", gtk.STOCK_COPY, "_Copy", "<Control>c"),
        ("edit.cut", gtk.STOCK_CUT, "C_ut", "<Control>x"),
        ("edit.paste", gtk.STOCK_PASTE, "_Paste", "<Control>v"),
        ("edit.prefs", gtk.STOCK_PREFERENCES, "Pr_eferences"),
        ("view", None, "_View"),
        ("view.levels1", None, "_1 level"),
        ("view.levels2", None, "_2 levels"),
        ("view.levels4", None, "_4 levels"),
        ("view.levels8", None, "_8 levels"),
        ("help", None, "_Help"),
        ("help.help", gtk.STOCK_HELP, "_Help"),
        ("help.about", gtk.STOCK_ABOUT, "_About"),
    ]

    def __init__ (self, accelgroup):
        gtk.ActionGroup.__init__(self, "vismapper")
        #self.add_actions(self.ACTIONS, None)
        for actdesc in self.ACTIONS:
            extend = (None,)*(8-len(actdesc))
            x = actdesc + extend
            name, stockid, lbl, accel = x[:4]
            actname, actlabel, actaccel = name, lbl, None
            # Prefer stock properties; use actdesc if missing.
            stock = (None,)*5
            if stockid:
                temp = gtk.stock_lookup(stockid)
                if temp:
                    stock = temp
            if stock[1]:  # No preferred label.
                actlabel = stock[1]
            if not stock[2] and not stock[3]:  # No preferred accelerator.
                actaccel = accel
            action = gtk.Action(name=name, label=actlabel, tooltip=None, stock_id=stockid)
            accelpath = "{}/{}/{}".format("<MAIN>", "vismapper", name)
            action.set_accel_group(accelgroup)
            action.set_accel_path(accelpath)
            self.add_action_with_accel(action, actaccel)
            action.connect_accelerator()
        self.set_sensitive(True)
        self.set_visible(True)

    def get (self, k, defval=None):
        val = self.get_action(k)
        return (val if val is not None else defval)

    def __getitem__ (self, k):
        return self.get_action(k)


class MainMenubar (gtk.MenuBar):
    MENUDESC = [
        ('_File', [
            "file.new",
            "file.open",
            "file.save",
            "file.saveas",
            None,
            "file.commandpack",
            None,
            "file.quit",
            ]),
        ('_Edit', [
            "edit.copy",
            "edit.cut",
            "edit.paste",
            None,
            "edit.prefs",
            ]),
        ('_View', [
            "view.levels1",
            "view.levels2",
            "view.levels4",
            "view.levels8",
            ]),
        ('_Help', [
            "help.help",
            "help.about",
            ]),
        ]

    def __init__ (self, appactions):
        gtk.MenuBar.__init__(self)
        self.appactions = appactions
        self.build_menu(self, self.MENUDESC, self.appactions)

    @staticmethod
    def build_menu (menu, menudesc, appactions):
        __function__ = MainMenubar.build_menu
        if menu is None:
            menu = gtk.Menu()
        for itemdesc in menudesc:
            menuitem = None
            if itemdesc is None:
                menuitem = gtk.SeparatorMenuItem()
            elif isinstance(itemdesc, tuple):
                if len(itemdesc) == 2:
                    name, subdesc = itemdesc
                    action = appactions.get_action(name)
                    submenu = None
                    if action:
                        submenu = action.create_menu()
                    submenu = __function__(submenu, subdesc, appactions)
                    menuitem = gtk.MenuItem(name, True)
                    menuitem.set_submenu(submenu)
                elif len(itemdesc) == 3:
                    name, accel, action = itemdesc
            else:
                actname = itemdesc
                action = appactions.get_action(actname)
                menuitem = action.create_menu_item()
                if not action:
                    raise KeyError("Could not resolve action for {!r}".format(actname))
                action.connect_proxy(menuitem)
            if menuitem:
                menu.append(menuitem)
        return menu


# Massive store of tooltip text.
AppTooltips = {
    "sel_layout": """\
Device Layout

Layout is an approximation of a human-computer input device (HID). \
The various components of the device are laid out graphically to assist in presenting what and where each bindable component is.

Each bindable component is labeled with some indicator of its physical form. \
Typically this label related to a printed key face, a "well-known name", or description of the component.

Bindings are the in-game action carried out by activating (pressing) the input component (typically key or button). \
The bindings are displayed beneath the labels. \
""",
    "sel_mode": """\
Mode selector

Under certain circumstances in a game, the same key may take on completely different meanings specific and unique to the circumstances -- a &quot;mode&quot;.  These &quot;modes&quot; demand their own set of bindings distinct from other modes (or normal gameplay).

For example, in battle, left-click may mean attack; but while shopping, left-click may mean to purchase.  Separating the concepts allows multiple, alternate, or separate bindings, e.g. Ctrl as alternate attack button, while Space as alternate purchase button.

The first mode, Global, is reserved for keys that are (usually) active in all modes.  Examples include a universal &quot;Escape&quot; game menu, in-game console, debug/troubleshooting toggles, quit-to-desktop.  Global bindings that show through to the current mode are marked up in italics (slant) font. \
""",
    "sel_layer": """\
Layer selector

Layers are overloaded meanings of a key that are activated by some other key or action, typically a shift-modifier key (e.g. Shift, Ctrl, Alt, Cmd), but in rare cases same-key manipulation such as long-press, double-tap, or triple-tap.

Higher layers are often accessed by multiple combinatinations of shift-modifier keys.

Change the number of layers visible simultaneously through the menu View. \
""",
    "btn_cluster_type_menu": """\
PlanarCluster

The Steam client can map certain control types from their two-dimensional position to customized virtual keys. \
Originally designed for the Steam Controller's touchpads, the feature has also been extended to analog sticks, PlayStation 4 controllers, and XInput (Xbox360-style) controllers. \
""",
    "cmdpackview": """\
Command Pack

Set of commands in the game (not exhaustive). \
Many commands are grouped together logically under a collapsing row, to avoid having one enormous list that is difficult to browse.

Drag commands from here to a bindable component to bind the action (be aware of currently active layer). \
Drag from key to here to erase the bind. \
Drag from key to key to swap binds.

Pre-made command packs can be opened through File &gt; CommmandPack. \
Most of these packs are in sqlite3 format. \
""",
    "prefs_knowwhat": """\
Advanced mode - hide the helper tooltips intended for novice users. \
"""
}



class VisMapperApp (object):
    """Overall application object, with app/GUI state information."""
    def __init__ (self):
        self.modenum = 0
        self.levelnum = 0

        self.prefs = AppPreferences()
        self.session = AppSession()
        self.accelgroup = gtk.AccelGroup()
        self.appactions = AppActions(self.accelgroup)

        self.build_ui()
        self.hook_tooltips()
        self.bind_actions()

        self.set_cmdsuri(DEFAULT_DBNAME + ".sqlite3")
        #self.cmds_in_place()

    def build_ui (self):
        """Setup and connect UI elements."""
        self.menubar = MainMenubar(self.appactions)
        self.ui = VisMapperWindow(self, menubar=self.menubar, prefs=self.prefs, session=self.session)
        self.ui.add_accel_group(self.accelgroup)
        #self.ui.add_accel_group(accelgroup)
        # New planar-clusters may appear on layout change.  Watch such changes and pick up the new planar-clusters for tooltips.
        self.ui.bindview.ui.selectors.connect("layout-changed", self.on_layoutmap_changed)

    def on_layoutmap_changed (self, w, val):
        self.hook_tooltips()

    def hook_tooltips (self):
        # Recursively search all children for has-tooltip widgets.
        # TODO: this misses late-creation widgets such as cluster type buttons.
        stack = []
        #witer = self.ui.get_children().__iter__()
        scanning = [ self.ui, self.ui.dlg_about, self.ui.dlg_prefs ]
        witer = scanning.__iter__()
        self.tooltipable = weakref.WeakKeyDictionary()
        while stack or witer:
            try:
                ch = witer.next()
            except StopIteration:
                if stack:
                    witer = stack[-1]
                    del stack[-1]
                else:
                    witer = None
                continue
            if ch.props.has_tooltip:
                if not ch in self.tooltipable:
                    self.tooltipable[ch] = None
            try:
                # Recurse.
                chiter = ch.get_children().__iter__()
            except:
                chiter = None
            if chiter:
                stack.append(witer)
                witer = chiter
        for tipable in self.tooltipable:
            tipable.connect("query-tooltip", self.on_query_tooltip, tipable.knowwhat)

    def on_query_tooltip (self, w, x, y, kbd, tooltip, qualifier, *args):
        if not self.prefs.knowwhat:
            txt = AppTooltips.get(qualifier, None)
            if txt:
                tooltip.set_markup(txt)
                return True
        return False

    def bind_actions (self):
        actionmap = {
            "file.new": (lambda w: self.reset(),),
            "file.open": (self.gui_open,),
            "file.save": (self.gui_save,),
            "file.saveas": (self.gui_saveas,),
            "file.commandpack": (self.gui_commandpack,),
            "file.quit": (lambda w: self.quit(),),
            "edit.prefs": (lambda w: self.ask_preferences(),),
            "view.levels1": (lambda w: self.set_vislayers(1),),
            "view.levels2": (lambda w: self.set_vislayers(2),),
            "view.levels4": (lambda w: self.set_vislayers(4),),
            "view.levels8": (lambda w: self.set_vislayers(8),),
            "help.about": (lambda w: self.display_about(),),
        }
        for actname in actionmap:
            action = self.appactions.get_action(actname)
            cb = actionmap[actname]
            action.connect("activate", *cb)
        pass

    def gui_open (self, w):
        loadname = self.ask_load_uri()
        if loadname:
            self.set_saveuri(loadname)
            self.load_in_place()
        return
    def gui_save (self, w):
        if not self.save_in_place():
            return self.gui_saveas(self, w, *args)
        return
    def gui_saveas (self, w):
        savename = self.ask_save_uri()
        if savename:
            self.set_saveuri(savename)
            self.save_in_place()
        return
    def gui_commandpack (self, w):
        srcname = self.ask_cmds_uri()
        if srcname:
            self.set_cmdsuri(srcname)
        return

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
        return self.session.uri_cmdinfo
    def set_cmdsuri (self, val):
        #self.models.bindstore.cmdsuri = val
        self.session.uri_cmdinfo = val
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
                cmdinfo = CommandInfo_sqlite3(self.session.uri_cmdinfo)
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

    def ask_preferences (self):
        dlg = self.ui.dlg_prefs
        dlg.reset()
        dlg.show()
        response = dlg.run()
        if response == gtk.RESPONSE_ACCEPT:
            dlg.commit_prefs()
            self.prefs.commit()
        dlg.hide()

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


