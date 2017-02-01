
DROP TABLE IF EXISTS cmd;
DROP TABLE IF EXISTS modes;

CREATE TABLE cmd (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
--  modemask INTEGER,  -- mask of modes; command binds to all modes specified.
  layer INTEGER,  -- layer number of command.
  grp VARCHAR(32),  -- group.
  cmd VARCHAR(32),  -- command as used by other app.
  label VARCHAR(64),  -- label to show in column UI.
  hint VARCHAR(1024)  -- hint (hovertext) for command.
  );


CREATE TABLE modes (
  id SERIAL,
  name TEXT
);



BEGIN TRANSACTION;

INSERT INTO modes VALUES (NULL, 'Game'),
  (NULL, 'Inventory'),
  (NULL, 'Crafting'),
  (NULL, 'Editor');

COMMIT TRANSACTION;


BEGIN TRANSACTION;

INSERT INTO cmd VALUES (NULL, 0, 'Shifter', '^1', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Shifter', '^2', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Shifter', '^3', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Shifter', '^4', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Shifter', '^5', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 1, 'Game', 'MoveUp', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'MoveRight', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'MoveLeft', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'MoveDown', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'CharScrn', 'Character Screen', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'TechScrn', 'Technology Screen', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'CloseWin', 'Close Window/Screen', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Mine', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Build', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'BldGhost', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'RmvCbls', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'CopyEnt', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'PasteEnt', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'SelBluprt', 'Select for Blueprint', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'CanDecon', 'Cancel Deconstruction', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'ObjGui', 'Show Object Gui', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'ShowInfo', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'NextWeap', 'Next weapon', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'ClrCursor', 'Clear selection', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'DropItem', 'Drop item on ground', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Rotate', 'Rotate Entity', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'PickUp', 'Pick up item from ground', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'ShootE', 'Shoot at Enemy', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'ShootSel', 'Shoot at Selection', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'ManVehcl', 'Enter/Exit Vehicle', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'ZoomIn', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'ZoomOut', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'TglMenu', 'Toggle Menu', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'PrdStats', 'Production Stats', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'TglWrldMap', 'Toggle World Map', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'ConfirmMsg', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'ConnTrain', 'Connect train with wagon', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'DiscoTrain', 'Disconnect last train wagon', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'PauseGame', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'BldArea+', 'Increase Terrain Build Area', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'BldArea-', 'Decrease Terrain Build Area', NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Console', 'Toggle Console', NULL);

INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'PickUp', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'StkXfer', 'Stack Transfer', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'InvXfer', 'Inventory Transfer', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'FastEXfr', 'Fast Entity Transfer', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'SetFilter', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'CursSplt', 'Cursor Split', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'StkSplt', 'Stack Split', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'InvSplt', 'Inventory Split', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'FastESplt', 'Fast Entity Split', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'Qk1', 'Quickbar1', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'Qk2', 'Quickbar2', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'Qk3', 'Quickbar3', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'Qk4', 'Quickbar4', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'Qk5', 'Quickbar5', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'Qk6', 'Quickbar6', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'Qk7', 'Quickbar7', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'Qk8', 'Quickbar8', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'Qk9', 'Quickbar9', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'Qk10', 'Quickbar10', NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Inventory', 'ChgActQk', 'Change Active Quickbar', NULL);

INSERT INTO cmd VALUES (NULL, 3, 'Crafting', 'Craft1', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Crafting', 'Craft5', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Crafting', 'CanCrft1', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Crafting', 'CanCrft2', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Crafting', 'CraftAll', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Crafting', 'CanCrftAll', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 4, 'Editor', 'Primary', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Editor', 'Secondary', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Editor', 'RmvEnt', 'Remove Entity', NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Editor', 'EditEnt', 'Edit Entity', NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Editor', 'ShAllDiff', 'Show All Difficulties', NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Editor', 'ShEasyDiff', 'Show Easy Difficulty', NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Editor', 'ShMedDiff', 'Show Medium Difficulty', NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Editor', 'ShHardDiff', 'Show Hard Difficulty', NULL);


COMMIT TRANSACTION;

