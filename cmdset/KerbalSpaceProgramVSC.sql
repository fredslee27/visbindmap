-- Kerbal Space Program (Valve Steam Controller)

DROP TABLE IF EXISTS cmd;
DROP TABLE IF EXISTS modes;

DROP VIEW IF EXISTS packname;
CREATE VIEW packname(packname) AS SELECT 'Kerbal Space Program VSC';

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
 (NULL, 'Flight'),
 (NULL, 'Docking'),
 (NULL, 'Editor'),
 (NULL, 'Map');

INSERT INTO cmd VALUES (NULL, 0, 'Shifters', '^1', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Shifters', '^2', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Shifters', '^3', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Return', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Escape', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Backspace', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Delete', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Tab', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'ScrWhl Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'ScrWhl Dn', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'LMB', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'MMB', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'RMB', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Menu', 'Mouse Motion', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Pitch Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Pitch Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Yaw Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Yaw Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Roll Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Roll Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Translate Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Translate Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Translate Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Translate Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Translate Forward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Translate Backward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Throttle Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Throttle Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Launch/Stage', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight', 'Switch Xlt/Rot', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '+Pitch Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '-Pitch Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '+Roll Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '-Roll Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '+Yaw Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '-Yaw Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '+Translate Left/Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '-Translate Left/Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '+Translate Up/Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '-Translate Up/Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '+Translate Forward/Back', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '-Translate Up/Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '+Throttle Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '-Throttle Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '+ThrottleIncr Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Flight/analog', '-ThrottleIncr Axis', NULL, NULL);
INSERT INTO cmd VALUES
  (NULL, 1, 'Flight/consolized', 'Toggle Precision Controls', NULL, NULL),
  (NULL, 1, 'Flight/consolized', 'Trim Pitch+', NULL, NULL),
  (NULL, 1, 'Flight/consolized', 'Trim Pitch-', NULL, NULL),
  (NULL, 1, 'Flight/consolized', 'Trim Yaw+', NULL, NULL),
  (NULL, 1, 'Flight/consolized', 'Trim Yaw-', NULL, NULL),
  (NULL, 1, 'Flight/consolized', 'Trim Roll+', NULL, NULL),
  (NULL, 1, 'Flight/consolized', 'Trim Roll-', NULL, NULL),
  (NULL, 1, 'Flight/consolized', 'Staging Mode', NULL, NULL),
  (NULL, 1, 'Flight/consolized', 'Docking Mode', NULL, NULL),
  (NULL, 1, 'Flight/consolized', 'Toggle Stg<->Dck', NULL, NULL),
  (NULL, 1, 'Flight/consolized', 'Lock Launch Stage', NULL, NULL);


INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Landing Gear', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Brakes', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'SAS Hold', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'SAS Toggle', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'RCS Toggle', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Throttle CutOff', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Full Throttle', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Precision Controls Toggle', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Lights', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Emergency Abort', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Custom Action 1', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Custom Action 2', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Custom Action 3', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Custom Action 4', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Custom Action 5', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Custom Action 6', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Custom Action 7', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Custom Action 8', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Custom Action 9', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Custom Action 10', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Steer Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Steer Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Drive Forward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', 'Drive Backward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', '+Steering Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', '-Steering Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', '+Throttle Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Vessel', '-Throttle Axis', NULL, NULL);


INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Move Forward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Move Back', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Move Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Move Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Turn Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Turn Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Jump', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Run', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Use/Grab', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Board', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Toggle Movement Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Orient to View', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Toggle Lights', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'Toggle EVA Pack', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'EVA Forward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'EVA Back', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'EVA Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'EVA Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'EVA Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', 'EVA Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '+Translate Forward/Back', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '-Translate Forward/Back', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '+Translate Left/Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '-Translate Left/Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '+Translate Up/Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '-Translate Up/Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '+Translate Pitch', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '-Translate Pitch', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '+Translate Yaw', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '-Translate Yaw', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '+Translate Roll', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Kerbals', '-Translate Roll', NULL, NULL);


INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Orbital Map View', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Increase Time Warp', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Decrease Time Warp', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Stop Time Warp', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Focus Next Vessel', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Focus Prev Vessel', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Take Screenshot', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Pause', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Quicksave', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Quickload', NULL, NULL);


INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', 'Camera Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', 'Camera Next', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', 'Camera Reset', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', 'Zoom In', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', 'Zoom Out', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', 'View Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', 'View Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', 'View Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', 'View Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', 'Toggle Mouselook', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', '+Camera Horizontal', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', '-Camera Horizontal', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', '+Camera Vertical', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Camera', '-Camera Vertical', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 1, 'Game', 'Show/Hide Navball', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Misc', 'Show/Hide Flight UI', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Misc', 'Show/Hide Vessel Labels', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Misc', 'Show/Hide Flight Log', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Misc', 'Show/Hide Flight Forces', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Misc', 'Show/Hide Temp. Gauges', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, 'Game/Misc', 'Show/Hide Temp Overlay', NULL, NULL);
INSERT INTO cmd VALUES
  (NULL, 1, 'Game/consolized', 'Cycle Focus', NULL, NULL),
  (NULL, 1, 'Game/consolized', 'ModKey', NULL, NULL),
  (NULL, 1, 'Game/consolized', 'ModifierConsole', NULL, NULL),
  (NULL, 1, 'Game/consolized', 'Toggle Motion Sensor', NULL, NULL),
  (NULL, 1, 'Game/consolized', 'RadialMenu', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Scroll View Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Scroll View Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Part Pitch Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Part Pitch Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Yaw Part Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Yaw Part Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Roll Part Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Roll Part Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Reset Part Rotation', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Place Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Offset Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Rotate Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Root Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Toggle Local/Absolute', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Toggle Angle Snap', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Toggle Symmetry', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Cycle Symmetry Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Search All Parts', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Scroll Modifier for Zoom', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Scroll Icons Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Construction', 'Scroll Icons Down', NULL, NULL);
INSERT INTO cmd VALUES
  (NULL, 4, 'Construction/consolized', 'Precision Mode', NULL, NULL),
  (NULL, 4, 'Construction/consolized', 'Clone Part', NULL, NULL),
  (NULL, 4, 'Construction/consolized', 'Delete Part', NULL, NULL),
  (NULL, 4, 'Construction/consolized', 'Undo', NULL, NULL),
  (NULL, 4, 'Construction/consolized', 'Redo', NULL, NULL);


COMMIT TRANSACTION;

