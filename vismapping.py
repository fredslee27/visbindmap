#!/usr/bin/env python
# vim: set expandtab tabstop=4 :

import gtk, gobject
import sys, os, os.path
import sqlite3

import pprint
import pickle
import ast, parser

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
        self.cmdpack = None     # entire CommandPack.
        self.uri_bindstore = None  # path to last saved/loaded BindStore
        self.uri_cmdpack = None    # path to last saved/loaded CommandPack
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
        #self.cmdpack = CommandPack()
        self.uri_bindstore = None
        self.uri_cmdpack = None
        #self.undostack = AppUndo()
        self.ui_snapshot = None

    def snapshot (self, destfileobj):
        """Write session to persistent storage; usable as Save."""
        enc = {
            "bindstore": self.bindstore,
            "cmdpack": self.cmdpack,
            "uri_bindstore": self.uri_bindstore,
            "uri_cmdpack": self.uri_cmdpack,
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
        return inst

    def resume (self, srcfileobj):
        """Restore session from persistent storage; usable as Load."""
        enc = ast.literal_eval(srcfileobj.read())

        self.bindstore = self.reinstantiate(enc['bindstore'])
        self.cmdpack = self.reinstantiate(enc['cmdpack'])
        self.uri_bindstore = self.reinstantiate(enc['uri_bindstore'])
        self.uri_cmdpack = self.reinstantiate(enc['uri_cmdpack'])
        self.undostack = self.reinstantiate(enc['undostack'])
        self.ui_snapshot = self.reinstantiate(enc['ui_snapshot'])
        return

    def export_bindstore (self):
        """Save just BindStore in an interchange format."""
        return

    def import_bindstore (self):
        """Load BindStore from an interchange format."""
        return




## Checkpointable app data.
#class AppData (object):
#    def __init__ (self):
#        self.filename = None
#        self.active = None  # active bind layer.
#        self.binds = []  # List of dicts, bindings per layer.
#
#    def get_active (self):
#        return self.active
#    def set_active (self, val):
#        self.active = val
#
#    def get_filename (self):
#        return self.filename
#    def set_filename (self, val):
#        self.filename = val
#
#    def load (self):
#        pass
#    def save (self):
#        pass


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
    """GUI data model for list of commands available for binding."""
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


class CommandSource:  # old-style.
    """Container for command pack sources."""

#    class CmdSourceBase (object):  # new-style.
#        """Base class for command pack resource."""
#        def __init__ (self, uri, packname=None):
#            self.uri = uri
#            self.packname = "__base__"
#            self.cmdpack = None
#
#        def get_command_pack (self):
#            if self.cmdpack is None:
#                self.cmdpack = self.build_command_pack()
#            return self.cmdpack
#        command_pack = property(get_command_pack)
#
#        def build_command_pack (self):
#            raise NotImplementedError("{}.build_command_pack() not overridden.".format(self.__class__.__name__))

    @staticmethod
    def builtin ():
        """Hard-coded builtin command pack."""
        MODES = [ "Menu", "Game" ]
        COMMANDS = [
            # Layer: [ tuples... ]
            ("Shifter", [ ("^1",), ("^2",), ("^3",), ("^4",), ("^5",) ] ),
            ("Menu", [
                # Tuples (command_codename, displayed_name, hint)
                ("Pause", None, None),
                ("Minimize", None, None),
                ]),
            ("Game", [
                ("Up",), ("Down",), ("Left",), ("Right",),
                ("Jump",), ("Action",),
                ]),
            ]
        cmdpack = hidlayout.CommandPackStore("(builtin)")
        cmdid, grpid = 1, 0
        for grp in COMMANDS:
            grpname, grpdata = grp
            cmdpack.begin_group(grpname)
            for cmdentry in grpdata:
                cmd, lbl, hint = None, None, None
                try:
                    cmd = cmdentry[0]
                    lbl = cmdentry[1]
                    hint = cmdentry[2]
                except IndexError:
                    lbl = cmd
                if lbl is None:
                    lbl = cmd
                #row = (cmdid, grpid, grpname, cmd, lbl, hint)
                row = (cmdid, cmd, lbl, hint)
                cmdpack.append(row)
                cmdid += 1
            cmdpack.end_group()
            grpid += 1
        return cmdpack

    @staticmethod
    def sqlite3 (dbname):
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()

        # Get pack name.
        packname = os.path.basename(dbname)
        try:
            rows = cursor.execute('''SELECT packname FROM packname LIMIT 1;''')
            row = rows.fetchone()
            packname = row[0]
        except sqlite3.OperationalError:
            pass
        cmdpack = hidlayout.CommandPackStore(packname)

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
        rows = cursor.execute(stmt)
        for row in rows:
            cmdid, lyr, grp, cmd, lbl, hint = row
            if lbl is None:
                lbl = cmd
            datum = (cmdid, cmd, lbl, hint)
            # Find group, attach to group.
            grpiter = grploc.get(grp, None)
            cmdpack.append(grpiter, datum)

        return cmdpack

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


class CommandsFallback (Commands):
    """Minimalist hardcoded/builtin command set in case cmds.sqlite3 fails to read."""
    MODES = [ "Menu", "Game" ]
    COMMANDS = [
        # Layer: [ tuples... ]
        ("Shifter", [ ("^1",), ("^2",), ("^3",), ("^4",), ("^5",) ] ),
        ("Menu", [
            # Tuples (command_codename, displayed_name, hint)
            ("Pause", None, None),
            ("Minimize", None, None),
            ]),
        ("Game", [
            ("Up",), ("Down",), ("Left",), ("Right",),
            ("Jump",), ("Action",),
            ]),
        ]
    def __init__ (self, _=None):
        self.dbname = None
        self.packname = "(builtin)"
        cmdid, grpid = 1, 0
        self.commands = []
        for grp in self.COMMANDS:
            grpname, grpdata = grp
            for cmdentry in grpdata:
                cmd, lbl, hint = None, None, None
                try:
                    cmd = cmdentry[0]
                    lbl = cmdentry[1]
                    hint = cmdentry[2]
                except IndexError:
                    lbl = cmd
                row = (cmdid, grpid, grpname, cmd, lbl, hint)
                self.commands.append(row)
                cmdid += 1
            grpid += 1

    def get_name (self): return self.packname
    def set_name (self, val): self.packname = val
    def get_modes (self): return self.MODES
    def get_groups (self): return [ x[0] for x in self.COMMANDS ]
    groups = property(get_groups)
    def get_by_id (self, val):
        if val is None: return ( None, 0x1f, "", "", "", "" )

        result = [ x for x in self.commands if x[0] == val ][0]
        if result:
            if not result[4]:
                result = result[:4] + (result[3],) + result[5:]
            return result
        else:
            return None

    def get_count (self): return len(self.commands)

    def find (self, cmdname):
        if cmdname is None: return None

        try:
            return [ x for x in self.commands if x[3] == cmdname ][0]
        except IndexError:
            return -1

    def __iter__ (self):
        for row in self.commands:
            yield row
        raise StopIteration()



#class VisCmds (gtk.VBox):
#    """Visual presentation of commands: a tree of group and the commands."""
#    def __init__ (self, cmdstore=None):
#        gtk.VBox.__init__(self)
#
#        if not cmdstore:
#            cmdstore = CmdStore()
#        self.cmdstore = cmdstore
#
#        self.entry = gtk.TreeView(self.cmdstore)
#        self.cell0 = gtk.CellRendererText()
#        self.col0 = gtk.TreeViewColumn("command", self.cell0, text=2)
#        self.entry.append_column(self.col0)
##        self.add(gtk.Label("VisCmds"))
#
#        self.entrywin = gtk.ScrolledWindow()
#        self.entrywin.add(self.entry)
#        self.add(self.entrywin)
#        self.set_size_request(160, 100)
#
#        self.setup_dnd()
#
#    def get_cmdstore (self):
#        return self.cmdstore
#    def set_cmdstore (self, cmdstore):
#        self.cmdstore = cmdstore
#        self.entry.set_model(self.cmdstore)
#
#    def setup_dnd (self):
#        """Set up drag-and-drop."""
#        # DnD Source.
#        dnd_targets = [
#          (str(DndOpcodes.BIND), gtk.TARGET_SAME_APP, DndOpcodes.BIND),
#        ]
#        dnd_actions = gtk.gdk.ACTION_COPY
#        self.entry.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, dnd_targets, dnd_actions)
#        self.entry.connect("drag-data-get", self.on_drag_data_get)
#
#        # DnD Destination.
#        dnd_targets = [
#          (str(DndOpcodes.UNBIND), gtk.TARGET_SAME_APP, DndOpcodes.UNBIND),
#        ]
#        dnd_actions = gtk.gdk.ACTION_COPY
#        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, dnd_targets, dnd_actions)
#        self.connect("drag-data-received", self.on_drag_data_received)
#
#    def on_drag_data_received (self, w, ctx, x, y, seldata, info, time, *args):
#        logger.debug("cmdset drag-data-received %r" % info)
#        if info == DndOpcodes.UNBIND:
#            ctx.finish(True, False, time)
#            return True
#        return False
#
#    def on_drag_data_get (self, w, ctx, seldata, info, time, *args):
#        logger.debug("cmdset drag-data-get: %d" % info)
#        srcw = ctx.get_source_widget()
#        treesel = srcw.get_selection()
#        (treemdl, treeiter) = treesel.get_selected()
#        if info == DndOpcodes.BIND:
#            # Commands dragging.
#            logger.debug("info is %d => Commands dragging" % info)
#            if treemdl.iter_has_child(treeiter):
#                # non-terminal item; fail.
#                sel.set_text("", 0)
#                return False
#            # Get the command to bind.
#            val = treemdl.get_value(treeiter, 1)
#            seldata.set(seldata.target, 8, str(val))
#            chk = seldata.data
#            logger.debug("set seldata.data to %r, %r" % (val, chk))
#            return True


# Graphically lay out bindings meanings.
#class VisBind (gtk.VBox):
#    """Graphical layout of bindings; "central pane" of main window.
#Consists of:
# * layout selector
# * layer selector
#( group selector? )
# * the keytops
#"""
#
#    def reset (self):
#        pass
#
#
#    def __init__ (self, models=None):
#        gtk.VBox.__init__(self)
#
#        self.models = models
#
#        self.uibuild()
#
#        self.set_layout("SteamController")
#
#        self.reset()
#
#    def uibuild (self):
#        self.moderow = self.InpSelectMode()
#        self.pack_start(self.moderow)
#
#        self.shiftrow = self.InpSelectLevel()
#        self.pack_start(self.shiftrow)
#
#        # grid/tablular layout of inpbind+bindcmd
#        #inpdescr = self.models.bindstore.inpdescr
#        #self.hidl = hidlayout.HidLayoutWidget(self.models.dispstate)
#        #self.hidl.connect('key-selected', self.on_key_selected)
#        #self.hidl.connect('layout-changed', self.on_layout_changed)
#        self.hidl = hidlayout.BindableLayoutWidget(None)
#
#        self.pack_start(self.hidl, expand=False, fill=False)
#
#    def on_key_selected (self, w, ksym, *args):
#        #binding = self.models.bindstore.inpdescr.get_bind(ksym)
#        #binding = self.models.dispstate.get_bind(ksym)
#        logger.debug("key-selected: %s => %r" % (ksym, binding))
#
#    def get_layout (self):
#        idx = self.hidl.ui.sel_layout.get_active()
#        retval = self.hidl.mdl_layout[idx][0]
#        return retval
#    def set_layout (self, layoutname):
#        sel = self.hidl.ui.sel_layout
#        mdl = self.hidl.mdl_layout
#        idx = -1
#        for rownum in range(len(mdl)):
#            if mdl[rownum][0] == layoutname:
#                idx = rownum
#        if idx > -1:
#            sel.set_active(idx)
#
#    def on_layout_changed (self, w, layoutname, *args):
#        # Record chagne.
#        self.models.bindstore.active_layout = layoutname
#
#    def InpSelectMode (self):
#        """Generate GUI Widget for selecting mode (layer)."""
#        moderow = gtk.HBox()
#        modebtns = gtk.HButtonBox()
#
#        moderow.lbl = gtk.Label("MODE:")
#        moderow.btns = []
#        # "Select Layer" radio buttons.
#        modestore = self.models.modestore
#
#        def rebuild_buttons (modestore):
#            if moderow.btns:
#                for btn in moderow.btns:
#                    modebtns.remove(btn)
#            moderow.btns = []  # private data.
#            for modeid in range(len(modestore)):
#                grp = moderow.btns and moderow.btns[0] or None    # is group member or is group leader.
#                lbl = modestore[modeid][1]  # List row, second column => name.
#                btn = gtk.RadioButton(grp, lbl)  # create element.
#                btn.layernum = modeid  # private data
#                btn.connect('toggled', self.on_mode_toggle)  # react
#                modebtns.add(btn)  # GUI
#                moderow.btns.append(btn)  # internal storage.
#            moderow.show_all()
#            return
#        def on_data_changed (m, *args):
#            rebuild_buttons(m)
#            
#        rebuild_buttons(modestore)
#        moderow.pack_start(modebtns, expand=False)
#        # Rebuilds all buttons on any change.  This is very expensive.
#        modestore.connect('row-changed', on_data_changed)
#        modestore.connect('row-deleted', on_data_changed)
#        modestore.connect('row-inserted', on_data_changed)
#
#        #return moderow
#        modebox = gtk.Frame("MODE")
#        modebox.add(moderow)
#        return modebox
#
#    def InpSelectLevel (self):
#        """Generate GUI Widget for selecting level (shifted)."""
#        shiftbox = gtk.Frame("LEVEL")
#        shiftrow = gtk.HBox()
#        shiftbtns = gtk.HButtonBox()
#        MAX_SHIFTER = 3
#        btns = []
#        #shiftrow.lbl = gtk.Label("LEVEL")
#        #shiftrow.pack_start(shiftrow.lbl, expand=False)
#        for lvlnum in xrange(0, 8):
#            sh = []
#            for b in xrange(0, 8):
#                if (lvlnum & (1 << b)):
#                    sh.append("^%s" % (b+1))
#            if sh:
#                lbl = "%d " % lvlnum + ("(" + " + ".join(sh) + ")")
#            else:
#                lbl = "base"
#            grp = btns and btns[0] or None
#            btn = gtk.RadioButton(grp, lbl)
#            btn.levelnum = lvlnum
#            btn.connect('toggled', self.on_shifter_toggle)  # react
#            btns.append(btn)
#            shiftbtns.add(btn)
#        shiftrow.btns = btns
#        shiftrow.pack_start(shiftbtns, expand=True)
#        #return shiftrow
#        shiftbox.add(shiftrow)
#        return shiftbox
#
#    def on_mode_toggle (self, w, *args):
#        """Load bindings for mode."""
#        if w.get_active():
#          self.emit("mode-changed", w.layernum)
#        return
#
#    def on_shifter_toggle (self, w, *args):
#        """Load bindings for shift level."""
#        if not w.get_active():
#          # turning off.
#          return
#        if w.get_active():
#          # turning on.
#          self.emit("level-changed", w.levelnum)
#        return
#
#    def bind_cmd (self, ksym, cmdinfo):
#        logger.debug("bind");
#        pass
#
#    def unbind_cmd (self, ksym):
#        logger.debug("unbind");
#        pass
#
#gobject.type_register(VisBind)
#gobject.signal_new("mode-changed", VisBind, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,))
#gobject.signal_new("level-changed", VisBind, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,))
#

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

#        self.cmdcol = VisCmds(self.models.cmdstore)
#
#        self.bindrow = gtk.VBox()
#        self.bindpad = VisBind(self.models)
#        self.bindrow.pack_start(self.bindpad)
#        self.padpane.pack_start(self.bindrow)

        # TODO: from outside.
        #placeholder = hidlayout.CommandPackView.make_model()
        placeholder = CommandSource.builtin()

        self.cmdcol = hidlayout.CommandPackView(placeholder)
        self.bindrow = gtk.VBox()
        #self.bindview = hidlayout.BindableLayoutWidget(hidlayout.implicit_layouts,"PS3",self.models.bindstore.bindstore)
        self.bindview = hidlayout.BindableLayoutWidget(hidlayout.implicit_layouts, "PS3", self.session.bindstore)
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
        self.cmdsrc = None
        self.modenum = 0
        self.levelnum = 0

        #self.models = VisMapperModels()
        #self.models.cmdstore = CmdStore(self.cmdsrc)
        #self.models.bindstore = Store(8)
        #self.models.modestore = ModeStore(self.cmdsrc)
        #self.models.dispstate = hidlayout.InpDisplayState(self.models.bindstore.inpdescr)
        #self.models.accelgroup = gtk.AccelGroup()

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
        cmdname = self.cmdsrc and self.cmdsrc.get_name() or None
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
        if self.session.uri_cmdpack:
            cmdsrc = None
            try:
                cmdsrc = CommandSource.sqlite3(self.session.uri_cmdpack)
            except sqlite3.OperationalError:
                pass
            if cmdsrc:
                self.cmdsrc = cmdsrc
                self.ui.cmdcol.set_model(self.cmdsrc)

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


