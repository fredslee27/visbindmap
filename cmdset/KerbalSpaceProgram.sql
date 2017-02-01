
DROP TABLE IF EXISTS cmd;

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
 (NULL, 'Flight'),
 (NULL, 'Rover'),
 (NULL, 'Map'),
 (NULL, 'Kerbal'),
 (NULL, 'Construction');

INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Pitch Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Pitch Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Yaw Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Yaw Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Roll Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Roll Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Translate Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Translate Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Translate Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Translate Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Translate Forward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Translate Backward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Throttle Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Throttle Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Launch/Stage', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', 'Switch Xlt/Rot', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '+Pitch Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '-Pitch Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '+Roll Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '-Roll Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '+Yaw Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '-Yaw Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '+Translate Left/Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '-Translate Left/Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '+Translate Up/Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '-Translate Up/Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '+Translate Forward/Back', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '-Translate Up/Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '+Throttle Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '-Throttle Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '+ThrottleIncr Axis', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, 'Flight', '-ThrottleIncr Axis', NULL, NULL);


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


INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Move Forward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Move Back', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Move Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Move Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Turn Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Turn Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Jump', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Run', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Use/Grab', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Board', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Toggle Movement Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Orient to View', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, 'Kerbals', 'Toggle Lights', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', 'Toggle EVA Pack', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', 'EVA Forward', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', 'EVA Back', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', 'EVA Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', 'EVA Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', 'EVA Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', 'EVA Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '+Translate Forward/Back', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '-Translate Forward/Back', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '+Translate Left/Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '-Translate Left/Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '+Translate Up/Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '-Translate Up/Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '+Translate Pitch', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '-Translate Pitch', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '+Translate Yaw', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '-Translate Yaw', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '+Translate Roll', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, 'Kerbals', '-Translate Roll', NULL, NULL);


INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Orbital Map View', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Increase Time Warp', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Decrease Time Warp', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Stop Time Warp', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Focus Next Vessel', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Focus Prev Vessel', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Take Screenshot', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Pause', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Quicksave', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Quickload', NULL, NULL);

INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Camera Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Camera Next', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Camera Reset', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Zoom In', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Zoom Out', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'View Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'View Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'View Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'View Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Toggle Mouselook', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Scroll View Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Scroll View Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Part Pitch Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Part Pitch Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Yaw Part Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Yaw Part Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Roll Part Left', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Roll Part Right', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Reset Part Rotation', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Place Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Offset Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Rotate Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Root Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Toggle Local/Absolute', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Toggle Angle Snap', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Toggle Symmetry', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Cycle Symmetry Mode', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Search All Parts', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Scroll Modifier for Zoom', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Show/Hide Flight UI', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Scroll Icons Up', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Scroll Icons Down', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Show/Hide Vessel Labels', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Show/Hide Flight Log', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Show/Hide Flight Forces', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Show/Hide Temp. Gauges', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Show/Hide Temp Overlay', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', 'Show/Hide Navball', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', '+Camera Horizontal', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', '-Camera Horizontal', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', '+Camera Vertical', NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, 'Game', '-Camera Vertical', NULL, NULL);

COMMIT TRANSACTION;

