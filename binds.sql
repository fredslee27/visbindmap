
DROP VIEW IF EXISTS packname;
DROP TABLE IF EXISTS cmd;
DROP TABLE IF EXISTS modes;

CREATE VIEW packname(packname) AS SELECT 'Generic Bindings';

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

INSERT INTO modes VALUES (NULL, 'Menu'),
  (NULL, 'Game');

COMMIT TRANSACTION;


BEGIN TRANSACTION;

INSERT INTO cmd VALUES (NULL, 0, 'Shifter', '^1', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Shifter', '^2', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Shifter', '^3', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Shifter', '^4', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Shifter', '^5', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 1, 'Menu', 'Pause', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Menu', 'Minimize', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 2, 'Game', 'Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Game', 'Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Game', 'Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Game', 'Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Game', 'RotateLeft', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Game', 'RotateRight', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Game', 'TogglePreview', NULL, NULL);

COMMIT TRANSACTION;

