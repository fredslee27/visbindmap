
DROP TABLE IF EXISTS cmd;
DROP TABLE IF EXISTS modes;
DROP VIEW IF EXISTS packname;
DROP TABLE IF EXISTS packname;

CREATE VIEW packname AS SELECT "Guns Of Icarus Online" packname;

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

INSERT INTO modes VALUES
  (NULL, "Gun"),
  (NULL, "Helm"),
  (NULL, "Player"),
  (NULL, "Signal"),
  (NULL, "Spectator");


INSERT INTO cmd VALUES (NULL, 0, "Global", "ChatRegion", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "ChatTeam", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "ChatCrew", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "ChatParty", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "ChatClan", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "ChatCa", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "Debug", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "PushToTalk", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "CaptainPushToTalk", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "PartyPushToTalk", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "OrderNormal", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "OrderOffense", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "OrderDefense", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "PracticeDestroyShips", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "LookUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "LookDown", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "LookLeft", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "LookRight", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "ThirdPerson", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "SignalMode", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 0, "Global", "CaptainTarget", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 2, "Gun", "DismountGun", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Gun", "Reload", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Gun", "PrimaryFire", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Gun", "SecondaryFire", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Gun", "PracticeAim", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Gun", "PracticeTargetNear", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Gun", "PracticeTargetMid", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 2, "Gun", "PracticeTargetFar", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 3, "Helm", "DismountHelm", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Helm", "Ascend", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Helm", "HelmLeft", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Helm", "Descend", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Helm", "HelmRight", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Helm", "ThrottleUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Helm", "ThrottleDown", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Helm", "ScopeZoomIn", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Helm", "ScopeZoomOut", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Helm", "CargoHook", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 3, "Helm", "UseHelmEquipment", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 1, "Player", "PracticeAI", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "PracticeDamage", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "PracticeFire", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "PracticeShips", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "PracticeMovingShips", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "PracticeAttackShips", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "PracticeEditGun", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Use", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Jump", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Stamina", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Up", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Left", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Down", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Right", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "UseEquipment", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "UseEquipmentAlt", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Skill1", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Skill2", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Skill3", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Skill4", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "SpecialAbility", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "NextSkill", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "PreviousSkill", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "ScoreLog", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "Map", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 1, "Player", "TaskList", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 4, "Signal", "SignalUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Signal", "SignalLeft", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Signal", "SignalDown", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Signal", "SignalRight", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Signal", "SignalForward", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 4, "Signal", "SignalBackward", NULL, NULL);

INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraForward", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraLeft", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraBackward", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraRight", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraDown", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraSpeedUp", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraSpeedDown", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraTarget1", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraTarget2", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraTarget3", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraTarget4", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraTarget5", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraTarget6", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraTarget7", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraTarget8", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraFree", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "CameraDutch", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "ShowHealth", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "ShowChat", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "ShowDetails", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "ShowMatchDetails", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "PrevCrew", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "NextCrew", NULL, NULL);
INSERT INTO cmd VALUES (NULL, 5, "Spectator", "RamCam", NULL, NULL);

COMMIT TRANSACTION;

