
DROP TABLE IF EXISTS cmd;
DROP TABLE IF EXISTS modes;

CREATE TABLE cmd (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
--  modemask INTEGER,  -- mask of modes; command binds to all modes specified.
  layer INTEGER,  -- layer number of command.
  grp VARCHAR(32),  -- group.
  cmd VARCHAR(32),  -- command as used by other app.
  label VARCHAR(64),  -- label to show in UI.
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

INSERT INTO cmd VALUES (NULL, 0, "Shifter", "^1", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Shifter", "^2", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Shifter", "^3", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Shifter", "^4", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Shifter", "^5", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 1, "Game", "MoveUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "MoveRight", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "MoveLeft", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "MoveDown", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "CharScrn", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "TechScrn", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "CloseWin", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "Mine", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "Build", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "buildGhost", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "RmvCables", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "CopyEnt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "PasteEnt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "SelBlueprt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "CanDecnstr", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "ObjGui", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "ShowInfo", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "NextWeap", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "ClrCursor", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "DropItem", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "Rotate", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "PickUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "ShootE", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "ShootSel", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "ManVehcl", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "ZoomIn", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "ZoomOut", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "TglMenu", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "PrdStats", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "TglWrldMap", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "ConfirmMsg", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "ConnTrain", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "DiscoTrain", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "PauseGame", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "TerrainBld+", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "TerrainBld-", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Game", "Console", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 2, "Inventory", "PickUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "StkXfer", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "InvXfer", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "FastEXfr", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "SetFilter", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "CursSplt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "StkSplt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "InvSplt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "FastESplt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "Qk1", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "Qk2", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "Qk3", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "Qk4", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "Qk5", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "Qk6", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "Qk7", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "Qk8", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "Qk9", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "Qk10", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Inventory", "ChgActvQk", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 3, "Crafting", "Craft1", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Crafting", "Craft5", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Crafting", "CanCraft1", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Crafting", "CanCraft2", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Crafting", "CraftAll", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Crafting", "CanCrftAll", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 4, "Editor", "Primary", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Editor", "Secondary", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Editor", "RmvEnt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Editor", "EditEnt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Editor", "ShowAllDIff", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Editor", "ShowEasyDiff", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Editor", "ShowMedDiff", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Editor", "ShowHardDiff", NULL, NULL);


COMMIT TRANSACTION;

