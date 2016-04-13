
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

INSERT INTO cmd VALUES (NULL, 0, "Game", "MoveUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "MoveRight", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "MoveLeft", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "MoveDown", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "CharScrn", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "TechScrn", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "CloseWin", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "Mine", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "Build", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "buildGhost", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "RmvCables", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "CopyEnt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "PasteEnt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "SelBlueprt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "CanDecnstr", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "ObjGui", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "ShowInfo", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "NextWeap", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "ClrCursor", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "DropItem", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "Rotate", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "PickUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "ShootE", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "ShootSel", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "ManVehcl", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "ZoomIn", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "ZoomOut", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "TglMenu", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "PrdStats", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "TglWrldMap", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "ConfirmMsg", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "ConnTrain", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "DiscoTrain", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "PauseGame", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "TerrainBld+", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "TerrainBld-", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Game", "Console", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 0, "Inventory", "PickUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "StkXfer", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "InvXfer", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "FastEXfr", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "SetFilter", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "CursSplt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "StkSplt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "InvSplt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "FastESplt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "Qk1", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "Qk2", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "Qk3", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "Qk4", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "Qk5", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "Qk6", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "Qk7", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "Qk8", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "Qk9", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "Qk10", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Inventory", "ChgActvQk", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 0, "Crafting", "Craft1", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Crafting", "Craft5", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Crafting", "CanCraft1", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Crafting", "CanCraft2", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Crafting", "CraftAll", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Crafting", "CanCrftAll", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 0, "Editor", "Primary", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Editor", "Secondary", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Editor", "RmvEnt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Editor", "EditEnt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Editor", "ShowAllDIff", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Editor", "ShowEasyDiff", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Editor", "ShowMedDiff", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Editor", "ShowHardDiff", NULL, NULL);


COMMIT TRANSACTION;

