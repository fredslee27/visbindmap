
DROP TABLE IF EXISTS cmd;
DROP TABLE IF EXISTS modes;

DROP VIEW IF EXISTS packname;
CREATE VIEW packname(packname) AS SELECT 'Euro Truck Simulator 2';

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
  id INTEGER,
  name VARCHAR(32)
);


BEGIN TRANSACTION;

INSERT INTO modes VALUES
 (NULL, 'Menu'),
 (NULL, 'Game');

INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Mouse Motion', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Mouse1', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Mouse2', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Mouse3', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Throttle', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Brake/Reverse', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Steering Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Steering Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Shift Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Shift Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Shift to Neutral', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Shift Up Hint', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Shift Down Hint', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Gearbox Auto||Seq', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Start/Stop Engine', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Parking Brake', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Engine Brake', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Engine Brake Toggle', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Engine Brake Increase', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Engine Brake Decrease', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Trailer Brake', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Retarder Increase', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Retarder Decrease', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Lift/Drop Axle', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Lift/Drop Trailer Axle', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Differential Lock', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Left-Turn Indicator', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Right-Turn Indicator', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Hazard Warning', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Light Modes', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'High Beam Headlights', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Beacon', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Horn', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Air Horn', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Light Horn', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Wipers', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Cruise Control', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Cruise Control Speed Increase', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Cruise Control Speed Decrease', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Cruise Control Resume', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Dashboard Display Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Dashboard Map Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Truck', 'Dashboard Trip Info Reset', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 2, 'HUD', 'Toggle Side Mirrors', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'HUD', 'Route Advisor Modes', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'HUD', 'Truck Adjustment', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'HUD', 'Route Advisor Mouse Control', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'HUD', 'Route Advisor Navigation Page', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'HUD', 'Route Advisor Job Info Page', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'HUD', 'Route Advisor Diagnostics Page', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'HUD', 'Route Advisor Info Page', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'HUD', 'Route Advisor Next Page', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'HUD', 'Route Advisor Previous Page', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Next Camera', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Interior Camera', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Chasing Camera', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Top-Down Camera', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Roof Camera', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Lean Out Camera', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Bumper Camera', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'On-Wheel Camera', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Drive-By Camera', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Rotate Camera mouse', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Zoom Interior Camera', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Look Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Look Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Interior Look Forward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Interior Look Up Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Interior Look Up Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Interior Look Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Interior Look Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Interior Look Up Middle', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Steering Based Camera Rotation', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Camera', 'Blinker Based Camera Rotation', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Activate', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Trailer Attach/Detach', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Menu', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Quick Save', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Quick Load', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Audio Player', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Audio Player Next Fav', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Audio Player Prev Fav', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Audio Player Volume Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Audio Player Volume Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'World Map', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Garage Manager', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Other', 'Screenshot', NULL, NULL);

COMMIT TRANSACTION;
