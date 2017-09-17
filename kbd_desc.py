#!/usr/bin/env python

KBD = {
   '(none)': [ [ ] ],

  # Tuples are: (label, height[cells], width[cells])
  'mouse': [  # list of list
    [ # row 1
      ( 1, 6, None),
      ( 1, 6, 'MOUSE4'),
      ],
    [
      ( 1, 6, 'MOUSE1'),
      ( 1, 6, 'MOUSE2'),
      ( 1, 6, 'MOUSE3'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, 'MOUSE5'),
      ],
    None,
    [
      ( 1, 6, None),
      ( 1, 6, 'up'),
      ],
    [
      ( 1, 6, 'left'),
      ( 1, 6, None),
      ( 1, 6, 'right'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, 'down'),
      ],
    ],

  'en_US (pc104)': [  # list of list
    [ # row 1
      ( 1, 6, 'ESC', 'Esc'),
      ( 1, 3, None),
      ( 1, 6, 'F1'),
      ( 1, 6, 'F2'),
      ( 1, 6, 'F3'),
      ( 1, 6, 'F4'),
      ( 1, 3, None),
      ( 1, 6, 'F5'),
      ( 1, 6, 'F6'),
      ( 1, 6, 'F7'),
      ( 1, 6, 'F8'),
      ( 1, 3, None),
      ( 1, 6, 'F9'),
      ( 1, 6, 'F10'),
      ( 1, 6, 'F11'),
      ( 1, 6, 'F12'),
      ],

    None,

    [
      ( 1, 6, 'GRAVE', '`'),
      ( 1, 6, 'PA', '1'),
      ( 1, 6, 'RE', '2'),
      ( 1, 6, 'CI', '3'),
      ( 1, 6, 'VO', '4'),
      ( 1, 6, 'MU', '5'),
      ( 1, 6, 'XA', '6'),
      ( 1, 6, 'ZE', '7'),
      ( 1, 6, 'BI', '8'),
      ( 1, 6, 'SO', '9'),
      ( 1, 6, 'NO', '0'),
      ( 1, 6, 'HYPHEN', '-'),
      ( 1, 6, 'EQUAL', '='),
      ( 1, 9, 'BS'),
      ],

    [
      ( 1, 9, 'TAB', 'Tab'),
      ( 1, 6, 'Q'),
      ( 1, 6, 'W'),
      ( 1, 6, 'E'),
      ( 1, 6, 'R'),
      ( 1, 6, 'T'),
      ( 1, 6, 'Y'),
      ( 1, 6, 'U'),
      ( 1, 6, 'I'),
      ( 1, 6, 'O'),
      ( 1, 6, 'P'),
      ( 1, 6, 'LSQB', '['),
      ( 1, 6, 'RSQB', ']'),
      ( 1, 6, 'BACKSLASH', '\\'),
      ],

    [
      ( 1, 10, 'CAPSLOCK', 'CAPS'),
      ( 1, 6, 'A'),
      ( 1, 6, 'S'),
      ( 1, 6, 'D'),
      ( 1, 6, 'F'),
      ( 1, 6, 'G'),
      ( 1, 6, 'H'),
      ( 1, 6, 'J'),
      ( 1, 6, 'K'),
      ( 1, 6, 'L'),
      ( 1, 6, 'SEMI', ';'),
      ( 1, 6, 'QUOT', '\''),
      ( 1, 11, 'ENTER', 'Enter'),
      ],

    [
      ( 1, 12, 'LSHIFT', 'SHIFT'),
      ( 1, 6, 'Z'),
      ( 1, 6, 'X'),
      ( 1, 6, 'C'),
      ( 1, 6, 'V'),
      ( 1, 6, 'B'),
      ( 1, 6, 'N'),
      ( 1, 6, 'M'),
      ( 1, 6, 'COMMA', ','),
      ( 1, 6, 'PERIOD', '.'),
      ( 1, 6, 'SLASH', '/'),
      ( 1, 15, 'RSHIFT', 'SHIFT'),
      ],

    [
      ( 1, 9, 'LCTRL', 'CTRL'),
      ( 1, 8, 'LLOGO', 'LOGO'),
      ( 1, 9, 'LALT', 'ALT'),
      ( 1, 27, 'SPACE', 'Space'),
      ( 1, 9, 'RALT', 'ALT'),
      ( 1, 8, 'RLOGO', 'LOGO'),
      ( 1, 8, 'MENU', 'Menu'),
      ( 1, 9, 'RCTRL', 'CTRL'),
      ],


    None,
    None,

    [
      ( 1, 6, 'INS', 'Ins'),
      ( 1, 6, 'HOME', 'Home'),
      ( 1, 6, 'PGUP', 'PgUp'),

      ( 1, 12, None),

      ( 1, 6, 'PRINT', 'PrSc'),
      ( 1, 6, 'SCROLLLOCK', 'ScLk'),
      ( 1, 6, 'PAUSE', 'Pau'),

      ( 1, 12, None),

        ( 1, 6, 'NUMLOCK', 'NL'),
        ( 1, 6, 'KP_DIVIDE', '/'),
        ( 1, 6, 'KP_MULTIPLY', '*'),
        ( 1, 6, 'KP_SUBTRACT', '-'),
      ],

    [
      ( 1, 6, 'DEL', 'Del'),
      ( 1, 6, 'END', 'End'),
      ( 1, 6, 'PGDN', 'PgDn'),

      ( 1, 42, None),

        ( 1, 6, 'KP_7', '7'),
        ( 1, 6, 'KP_8', '8'),
        ( 1, 6, 'KP_9', '9'),
        ( 2, 6, 'KP_ADD', '+'),
      ],

    [
      ( 1, 18, None),
      ( 1, 42, None),

        ( 1, 6, 'KP_4', '4'),
        ( 1, 6, 'KP_5', '5'),
        ( 1, 6, 'KP_6', '6'),
        ( 1, 6, None),
      ],

    [
      ( 1, 6, None),
      ( 1, 6, 'UP', 'Up'),
      ( 1, 6, None),

      ( 1, 42, None),

        ( 1, 6, 'KP_1', '1'),
        ( 1, 6, 'KP_2', '2'),
        ( 1, 6, 'KP_3', '3'),
        ( 2, 6, 'KP_RET', 'Ret'),
      ],

    [
      ( 1, 6, 'LEFT', 'Lt'),
      ( 1, 6, 'DOWN', 'Dn'),
      ( 1, 6, 'RIGHT', 'Rt'),

      ( 1, 42, None),

        ( 1, 12, 'KP_0', '0'),
        ( 1, 6, 'KP_SEP', '.'),
        ( 1, 6, None),
      ],

    ],


  'en_US (HHKL2)': [
    [
      ( 1, 6, 'Esc'),
      ( 1, 6, 'PA', '1'),
      ( 1, 6, 'RE', '2'),
      ( 1, 6, 'CI', '3'),
      ( 1, 6, 'VO', '4'),
      ( 1, 6, 'MU', '5'),
      ( 1, 6, 'XA', '6'),
      ( 1, 6, 'ZE', '7'),
      ( 1, 6, 'BI', '8'),
      ( 1, 6, 'SO', '9'),
      ( 1, 6, 'NO', '0'),
      ( 1, 6, '-'),
      ( 1, 6, '='),
      ( 1, 6, '\\'),
      ( 1, 6, '`'),
      ],
    [
      ( 1, 9, 'TAB', 'Tab'),
      ( 1, 6, 'Q'),
      ( 1, 6, 'W'),
      ( 1, 6, 'E'),
      ( 1, 6, 'R'),
      ( 1, 6, 'T'),
      ( 1, 6, 'Y'),
      ( 1, 6, 'U'),
      ( 1, 6, 'I'),
      ( 1, 6, 'O'),
      ( 1, 6, 'P'),
      ( 1, 6, '['),
      ( 1, 6, ']'),
      ( 1, 9, 'Del'),
      ],
    [
      ( 1, 10, 'CTRL'),
      ( 1, 6, 'A'),
      ( 1, 6, 'S'),
      ( 1, 6, 'D'),
      ( 1, 6, 'F'),
      ( 1, 6, 'G'),
      ( 1, 6, 'H'),
      ( 1, 6, 'J'),
      ( 1, 6, 'K'),
      ( 1, 6, 'L'),
      ( 1, 6, ';'),
      ( 1, 6, '\''),
      ( 1, 14, 'ENTER', 'Enter'),
      ],
    [
      ( 1, 13, 'LSHIFT', 'SHIFT'),
      ( 1, 6, 'Z'),
      ( 1, 6, 'X'),
      ( 1, 6, 'C'),
      ( 1, 6, 'V'),
      ( 1, 6, 'B'),
      ( 1, 6, 'N'),
      ( 1, 6, 'M'),
      ( 1, 6, ','),
      ( 1, 6, '.'),
      ( 1, 6, '/'),
      ( 1, 11, 'RSHIFT', 'SHIFT'),
      ( 1, 6, 'RFN', 'Fn'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, 'LFN', 'Fn'),
      ( 1, 6, 'LALT', 'ALT'),
      ( 1, 6, 'LMETA', '<>'),
      ( 1, 36, 'SPACE', 'Space'),
      ( 1, 6, 'RMETA', '<>'),
      ( 1, 6, 'RALT', 'ALT'),
      ( 1, 6, None),
      ( 1, 6, 'UP', 'Up'),
      ],
    [
      ( 1, 64, None),
      ( 1, 8, None),
      ( 1, 6, 'LEFT', 'Lt'),
      ( 1, 6, 'DOWN', 'Dn'),
      ( 1, 6, 'RIGHT', 'Rt'),
      ],
    ],



  'en_GB (pc105)': [  # list of list
    [ # row 1
      ( 1, 6, 'Esc'),
      ( 1, 3, None),
      ( 1, 1, None),
      ( 1, 6, 'F1'),
      ( 1, 6, 'F2'),
      ( 1, 6, 'F3'),
      ( 1, 6, 'F4'),
      ( 1, 3, None),
      ( 1, 6, 'F5'),
      ( 1, 6, 'F6'),
      ( 1, 6, 'F7'),
      ( 1, 6, 'F8'),
      ( 1, 3, None),
      ( 1, 6, 'F9'),
      ( 1, 6, 'F10'),
      ( 1, 6, 'F11'),
      ( 1, 6, 'F12'),
      ],

    None,

    [
      ( 1, 6, '`'),
      ( 1, 6, 'PA', '1'),
      ( 1, 6, 'RE', '2'),
      ( 1, 6, 'CI', '3'),
      ( 1, 6, 'VO', '4'),
      ( 1, 6, 'MU', '5'),
      ( 1, 6, 'XA', '6'),
      ( 1, 6, 'ZE', '7'),
      ( 1, 6, 'BI', '8'),
      ( 1, 6, 'SO', '9'),
      ( 1, 6, 'NO', '0'),
      ( 1, 6, '-'),
      ( 1, 6, '='),
      ( 1, 10, 'BS'),
      ],

    [
      ( 1, 9, 'TAB', 'Tab'),
      ( 1, 6, 'Q'),
      ( 1, 6, 'W'),
      ( 1, 6, 'E'),
      ( 1, 6, 'R'),
      ( 1, 6, 'T'),
      ( 1, 6, 'Y'),
      ( 1, 6, 'U'),
      ( 1, 6, 'I'),
      ( 1, 6, 'O'),
      ( 1, 6, 'P'),
      ( 1, 6, '['),
      ( 1, 6, ']'),
      ( 1, 1, None),
      ( 2, 6, 'ENTER', 'Enter'),
      ],

    [
      ( 1, 10, 'CAPSLOCK', 'CAPS'),
      ( 1, 6, 'A'),
      ( 1, 6, 'S'),
      ( 1, 6, 'D'),
      ( 1, 6, 'F'),
      ( 1, 6, 'G'),
      ( 1, 6, 'H'),
      ( 1, 6, 'J'),
      ( 1, 6, 'K'),
      ( 1, 6, 'L'),
      ( 1, 6, ';'),
      ( 1, 6, '\''),
      ( 1, 6, '#'),
      ],

    [
      ( 1, 6, 'LSHIFT', 'SHIFT'),
      ( 1, 6, '\\'),
      ( 1, 6, 'Z'),
      ( 1, 6, 'X'),
      ( 1, 6, 'C'),
      ( 1, 6, 'V'),
      ( 1, 6, 'B'),
      ( 1, 6, 'N'),
      ( 1, 6, 'M'),
      ( 1, 6, ','),
      ( 1, 6, '.'),
      ( 1, 6, '/'),
      ( 1, 16, 'RSHIFT', 'SHIFT'),
      ],

    [
      ( 1, 9, 'LCTRL', 'CTRL'),
      ( 1, 8, 'LLOGO', 'LOGO'),
      ( 1, 9, 'LALT', 'ALT'),
      ( 1, 28, 'SPACE', 'Space'),
      ( 1, 9, 'RALT', 'ALT'),
      ( 1, 8, 'RLOGO', 'LOGO'),
      ( 1, 8, 'MENU', 'Menu'),
      ( 1, 9, 'RCTRL', 'CTRL'),
      ],


    None,
    None,

    [
      ( 1, 6, 'INS', 'Ins'),
      ( 1, 6, 'HOME', 'Home'),
      ( 1, 6, 'PGUP', 'PgUp'),

      ( 1, 12, None),

      ( 1, 6, 'PRINT', 'PrSc'),
      ( 1, 6, 'SCROLLLOCK', 'ScLk'),
      ( 1, 6, 'PAUSE', 'Pau'),

      ( 1, 12, None),

        ( 1, 6, 'NUMLOCK', 'NL'),
        ( 1, 6, 'KP_/', '/'),
        ( 1, 6, 'KP_*', '*'),
        ( 1, 6, 'KP_-', '-'),
      ],

    [
      ( 1, 6, 'DEL', 'Del'),
      ( 1, 6, 'END', 'End'),
      ( 1, 6, 'PGDN', 'PgDn'),

      ( 1, 42, None),

        ( 1, 6, 'KP_7', '7'),
        ( 1, 6, 'KP_8', '8'),
        ( 1, 6, 'KP_9', '9'),
        ( 2, 6, 'KP_+', '+'),
      ],

    [
      ( 1, 18, None),
      ( 1, 42, None),

        ( 1, 6, 'KP_4', '4'),
        ( 1, 6, 'KP_5', '5'),
        ( 1, 6, 'KP_6', '6'),
        ( 1, 6, None),
      ],

    [
      ( 1, 6, None),
      ( 1, 6, 'UP', 'Up'),
      ( 1, 6, None),

      ( 1, 42, None),

        ( 1, 6, 'KP_1', '1'),
        ( 1, 6, 'KP_2', '2'),
        ( 1, 6, 'KP_3', '3'),
        ( 2, 6, 'KP_RET', 'Ret'),
      ],

    [
      ( 1, 6, 'LEFT', 'Lt'),
      ( 1, 6, 'DOWN', 'Dn'),
      ( 1, 6, 'RIGHT', 'Rt'),

      ( 1, 42, None),

        ( 1, 12, 'KP_0', '0'),
        ( 1, 6, 'KP_.', '.'),
        ( 1, 6, None),
      ],

    ],






  'PS3': [
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
#      ( 1, 3, None),
      ( 1, 6, 'B/8', 'L2'),
#      ( 1, 3, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'B/9', 'R2'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 3, None),
#      ( 1, 6, None),
      ( 1, 6, 'B/10', 'L1'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'B/11', 'R1'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, 'B/4', 'up'),
      ( 1, 6, None),
      ( 1, 36, None),
      ( 1, 6, 'B/12', 'T'),
      ],
    [
      ( 1, 6, 'B/7', 'left'),
      ( 1, 6, None),
      ( 1, 6, 'B/5', 'right'),
      ( 1, 6, None),
      ( 1, 6, 'B/0', 'SELECT'),
      ( 1, 6, None),
      ( 1, 6, 'B/3', 'START'),
      ( 1, 6, None),
      ( 1, 6, 'B/15', 'S'),
      ( 1, 6, None),
      ( 1, 6, 'B/13', 'O'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, 'B/6', 'down'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'B/16', 'HOME'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'B/14', 'X'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'A/1/-', 'Ly-'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'A/3/-', 'Ry-'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'A/0/-', 'Lx-'),
      ( 1, 6, 'B/1', 'L3'),
      ( 1, 6, 'A/0/+', 'Lx+'),
      ( 1, 6, None),
      ( 1, 6, 'A/2/-', 'Rx-'),
      ( 1, 6, 'B/2', 'R3'),
      ( 1, 6, 'A/2/+', 'Rx+'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'A/1/+', 'Ly+'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'A/3/+', 'Ry+'),
      ],
    ],

  'PS4': [
    [
      ( 1, 3, None),
      ( 1, 6, 'B/8', 'L2'),
      ( 1, 3, None),
      ( 1, 6, 'B/0', 'SHARE'),
      ( 1, 3, None),
      ( 1, 6, 'A/7', 'Ty'),
      ( 1, 3, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'B/3', 'OPTIONS'),
      ( 1, 3, None),
      ( 1, 6, 'B/9', 'R2'),
      ],
    [
      ( 1, 6, 'B/10', 'L1'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 3, None),
      ( 1, 6, 'B/17', 'Tz'),
      ( 1, 6, 'A/6', 'Tx'),
      ( 1, 6, None),
      ( 1, 9, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'B/11', 'R1'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, 'B/4', 'up'),
      ( 1, 6, None),
      ( 1, 12, None),
      ( 1, 6, 'GYy-'),
      ( 1, 18, None),
      ( 1, 6, 'B/12', 'T'),
      ],
    [
      ( 1, 6, 'B/7', 'left'),
      ( 1, 6, None),
      ( 1, 6, 'B/5', 'right'),
      ( 1, 6, None),
      ( 1, 6, 'GYx-'),
      ( 1, 6, None),
      ( 1, 6, 'GYx+'),
      ( 1, 6, None),
      ( 1, 6, 'B/15', 'S'),
      ( 1, 6, None),
      ( 1, 6, 'B/13', 'O'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, 'B/6', 'down'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'GYy+'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'B/14', 'X'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'A/1/-', 'Ly-'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'A/3/-', 'Ry-'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'A/0/-', 'Lx-'),
      ( 1, 6, 'B/1', 'L3'),
      ( 1, 6, 'A/0/+', 'Lx+'),
      ( 1, 6, None),
      ( 1, 6, 'A/2/-', 'Rx-'),
      ( 1, 6, 'B/2', 'R3'),
      ( 1, 6, 'A/2/+', 'Rx+'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'A/1/+', 'Ly+'),
      ( 1, 6, None),
      ( 1, 6, 'B/16', 'HOME'),
      ( 1, 6, None),
      ( 1, 6, 'A/3/+', 'Ry+'),
      ],
    ],

  'PS4/Steam': [
    [
      ( 1, 6, None),
      ( 1, 6, 'A/4', 'L2 soft'),
      ( 1, 6, None),

      ( 4, 18, 'LP#', "LP#", "cluster"),
      ( 4, 18, 'RP#', "RP#", "cluster"),

      ( 1, 6, None),
      ( 1, 6, 'A/5', 'R2 soft'),
      ],
    [
      ( 1, 6, 'B/10', 'L1'),
      ( 1, 6, 'B/8', 'L2 full'),
      ( 1, 6, 'B/0', 'SHARE'),

      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 3, None),
#      ( 1, 6, 'B/16', 'HOME'),
      ( 1, 6, None),
      ( 1, 3, None),
      ( 1, 6, None),
      ( 1, 6, None),

      ( 1, 6, 'B/3', 'OPTIONS'),
      ( 1, 6, 'B/9', 'R2 full'),
      ( 1, 6, 'B/11', 'R1'),
      ],
    [
      ( 4, 18, 'DP#', "DP#", "cluster"),
      ( 1, 18, None),
      ( 1, 18, None),
      ( 4, 18, 'B#', "B#", "cluster"),
      ],
    [
      ( 1, 60, None),
      ],
    [
      ( 1, 18, None),
      ( 1, 6, None),
      ( 1, 3, None),
      ( 5, 18, 'GY#', "GY#", "cluster"),
      ],
    [
      ( 1, 60, None),
      ],
    [
      ( 1, 9, None),
      ( 4, 18, 'L#', "L#", "cluster"),
      ( 4, 18, None),
      ( 4, 18, 'R#', "R#", "cluster"),
      ],
    [
      ( 1, 60, None),
      ],
    [
      ( 1, 60, None),
      ],
    [
      ( 1, 60, None),
      ],
# Home elided for Steam Client use.
    ],

  'XB360': [
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'LT'),
#      ( 1, 3, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'RT'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 3, None),
      ( 1, 6, 'TL'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'TR'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, 'Ly-'),
      ( 1, 6, None),
      ( 1, 36, None),
      ( 1, 6, 'Y'),
      ],
    [
      ( 1, 6, 'Lx-'),
      ( 1, 6, 'LS'),
      ( 1, 6, 'Lx+'),
      ( 1, 6, None),
      ( 1, 6, 'BACK'),
      ( 1, 6, None),
      ( 1, 6, 'START'),
      ( 1, 6, None),
      ( 1, 6, 'X'),
      ( 1, 6, None),
      ( 1, 6, 'B'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, 'Ly+'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, "GUIDE"),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'A'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'up'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'Ry-'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'left'),
      ( 1, 6, None),
      ( 1, 6, 'right'),
      ( 1, 6, None),
      ( 1, 6, 'Rx-'),
      ( 1, 6, 'RS'),
      ( 1, 6, 'Rx+'),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'down'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'Ry+'),
      ],
    ],


  'en_US (mac109)': [
    [ # row 1
      ( 1, 6, 'Esc'),
      ( 1, 1, None),
      ( 1, 6, 'F1'),
      ( 1, 6, 'F2'),
      ( 1, 6, 'F3'),
      ( 1, 6, 'F4'),
      ( 1, 6, 'F5'),
      ( 1, 6, 'F6'),
      ( 1, 6, 'F7'),
      ( 1, 6, 'F8'),
      ( 1, 6, 'F9'),
      ( 1, 6, 'F10'),
      ( 1, 6, 'F11'),
      ( 1, 6, 'F12'),
      ( 1, 1, None),
      ( 1, 6, 'Eject','EJCT'),
      ],

    [
      ( 1, 6, '`'),
      ( 1, 6, 'PA', '1'),
      ( 1, 6, 'RE', '2'),
      ( 1, 6, 'CI', '3'),
      ( 1, 6, 'VO', '4'),
      ( 1, 6, 'MU', '5'),
      ( 1, 6, 'XA', '6'),
      ( 1, 6, 'ZE', '7'),
      ( 1, 6, 'BI', '8'),
      ( 1, 6, 'SO', '9'),
      ( 1, 6, 'NO', '0'),
      ( 1, 6, '-'),
      ( 1, 6, '='),
      ( 1, 9, 'BS'),
      ],

    [
      ( 1, 9, 'TAB', 'Tab'),
      ( 1, 6, 'Q'),
      ( 1, 6, 'W'),
      ( 1, 6, 'E'),
      ( 1, 6, 'R'),
      ( 1, 6, 'T'),
      ( 1, 6, 'Y'),
      ( 1, 6, 'U'),
      ( 1, 6, 'I'),
      ( 1, 6, 'O'),
      ( 1, 6, 'P'),
      ( 1, 6, '['),
      ( 1, 6, ']'),
      ( 1, 6, '\\'),
      ],

    [
      ( 1, 10, 'CAPSLOCK', 'CAPS'),
      ( 1, 6, 'A'),
      ( 1, 6, 'S'),
      ( 1, 6, 'D'),
      ( 1, 6, 'F'),
      ( 1, 6, 'G'),
      ( 1, 6, 'H'),
      ( 1, 6, 'J'),
      ( 1, 6, 'K'),
      ( 1, 6, 'L'),
      ( 1, 6, ';'),
      ( 1, 6, '\''),
      ( 1, 11, 'ENTER', 'Enter'),
      ],

    [
      ( 1, 12, 'LSHIFT', 'SHIFT'),
      ( 1, 6, 'Z'),
      ( 1, 6, 'X'),
      ( 1, 6, 'C'),
      ( 1, 6, 'V'),
      ( 1, 6, 'B'),
      ( 1, 6, 'N'),
      ( 1, 6, 'M'),
      ( 1, 6, ','),
      ( 1, 6, '.'),
      ( 1, 6, '/'),
      ( 1, 15, 'RSHIFT', 'SHIFT'),
      ],

    [
      ( 1, 8, 'LCTRL', 'CTRL'),
      ( 1, 6, 'LALT', 'ALT'),
      ( 1, 8, 'LCMD', 'CMD'),
      ( 1, 43, 'SPACE', 'Space'),
      ( 1, 8, 'RCMD', 'CMD'),
      ( 1, 6, 'RALT', 'ALT'),
      ( 1, 8, 'RCTRL', 'CTRL'),
      ],


    None,

    [
      ( 1, 30, None),

      ( 1, 6, 'F13', 'F13'),
      ( 1, 6, 'F14', 'F14'),
      ( 1, 6, 'F15', 'F15'),

      ( 1, 12, None),
        ( 1, 6, 'F16'),
        ( 1, 6, 'F17'),
        ( 1, 6, 'F18'),
        ( 1, 6, 'F19'),
      ],
    [
      ( 1, 30, None),

      ( 1, 6, 'Fn'),
      ( 1, 6, 'HOME', 'Home'),
      ( 1, 6, 'PGUP', 'PgUp'),

      ( 1, 12, None),

        ( 1, 6, 'KP_CLEAR', 'clr'),
        ( 1, 6, 'KP_=', '='),
        ( 1, 6, 'KP_/', '/'),
        ( 1, 6, 'KP_*', '*'),
      ],

    [
      ( 1, 30, None),
      ( 1, 6, 'DEL', 'Del'),
      ( 1, 6, 'END', 'End'),
      ( 1, 6, 'PGDN', 'PgDn'),

      ( 1, 12, None),

        ( 1, 6, 'KP_7', '7'),
        ( 1, 6, 'KP_8', '8'),
        ( 1, 6, 'KP_9', '9'),
        ( 1, 6, 'KP_-', '-'),
      ],

    [
      ( 1, 30, None),
      ( 1, 18, None),

      ( 1, 12, None),
        ( 1, 6, 'KP_4', '4'),
        ( 1, 6, 'KP_5', '5'),
        ( 1, 6, 'KP_6', '6'),
        ( 1, 6, 'KP_+', '+'),
        ( 1, 6, None),
      ],

    [
      ( 1, 30, None),
      ( 1, 6, None),
      ( 1, 6, 'UP', 'Up'),
      ( 1, 6, None),

      ( 1, 12, None),
        ( 1, 6, 'KP_1', '1'),
        ( 1, 6, 'KP_2', '2'),
        ( 1, 6, 'KP_3', '3'),
        ( 2, 6, 'KP_RET', 'Ret'),
      ],

    [
      ( 1, 30, None),
      ( 1, 6, 'LEFT', 'Lt'),
      ( 1, 6, 'DOWN', 'Dn'),
      ( 1, 6, 'RIGHT', 'Rt'),

      ( 1, 12, None),

        ( 1, 12, 'KP_0', '0'),
        ( 1, 6, 'KP_.', '.'),
        ( 1, 6, None),
      ],

    ],


  'SteamController': [
    [
      ( 1, 6, None),
      ( 1, 6, 'LTz', 'LT (soft)'),
      ( 1, 6, 'LT', 'LT (full)'),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, 'RTz', 'RT (full)'),
      ( 1, 6, 'RT', 'RT (soft)'),
      ],
    [
      ( 1, 6, 'LG'),
      ( 1, 3, None),
      ( 1, 6, 'LB'),
      ( 1, 3, None),
      ( 1, 6, 'BACK'),
      ( 1, 6, 'HOME'),
      ( 1, 6, 'START'),
      ( 1, 3, None),
      ( 1, 6, 'RB'),
      ( 1, 3, None),
      ( 1, 6, 'RG'),
      ],
    [
      ( 4, 18, 'LP#', "LP#", "cluster"),
      ( 4, 18, 'GY#', "GY#", "cluster"),
      ( 4, 18, 'RP#', "RP#", "cluster"),
      ],
    [
      ( 1, 18, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 18, None),
      ],
    [
      ( 1, 18, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 18, None),
      ],
    [
      ( 1, 6, None),
      ( 1, 6, None),
      ( 1, 3, None),
      ( 1, 6, None),
      ( 1, 9, None),
      ( 1, 6, None),
      ( 1, 9, None),
      ( 1, 6, None),
      ( 1, 3, None),
      ( 1, 6, None),
      ( 1, 6, None),
      ],
    [
      ( 1, 6, None),
      ( 1, 3, None),
      ( 4, 18, 'L#', "L#", "cluster"),
      ( 4, 18, 'B#', "B#", "cluster"),
      ( 1, 3, None),
      ( 1, 6, None),
      ],
    [
      ( 1, 60, None),
      ],
    [
      ( 1, 60, None),
      ],
    [
      ( 1, 60, None),
      ],
    ],


  'en_US (mac78)': [
    [ # row 1
      ( 2, 6, 'ESC', 'Esc'),
      ( 2, 1, None),
      ( 2, 6, 'F1'),
      ( 2, 6, 'F2'),
      ( 2, 6, 'F3'),
      ( 2, 6, 'F4'),
      ( 2, 6, 'F5'),
      ( 2, 6, 'F6'),
      ( 2, 6, 'F7'),
      ( 2, 6, 'F8'),
      ( 2, 6, 'F9'),
      ( 2, 6, 'F10'),
      ( 2, 6, 'F11'),
      ( 2, 6, 'F12'),
      ( 2, 1, None),
      ( 2, 6, 'Eject', 'Ej'),
      ],
    None,

    [
      ( 2, 6, 'GRAVE', '`'),
      ( 2, 6, 'PA', '1'),
      ( 2, 6, 'RE', '2'),
      ( 2, 6, 'CI', '3'),
      ( 2, 6, 'VO', '4'),
      ( 2, 6, 'MU', '5'),
      ( 2, 6, 'XA', '6'),
      ( 2, 6, 'ZE', '7'),
      ( 2, 6, 'BI', '8'),
      ( 2, 6, 'SO', '9'),
      ( 2, 6, 'NO', '0'),
      ( 2, 6, 'HYPHEN', '-'),
      ( 2, 6, 'EQUAL', '='),
      ( 2, 9, 'BS'),
      ],
    None,

    [
      ( 2, 9, 'TAB', 'Tab'),
      ( 2, 6, 'Q'),
      ( 2, 6, 'W'),
      ( 2, 6, 'E'),
      ( 2, 6, 'R'),
      ( 2, 6, 'T'),
      ( 2, 6, 'Y'),
      ( 2, 6, 'U'),
      ( 2, 6, 'I'),
      ( 2, 6, 'O'),
      ( 2, 6, 'P'),
      ( 2, 6, 'LSQB', '['),
      ( 2, 6, 'RSQB', ']'),
      ( 2, 6, 'BACKSLASH', '\\'),
      ],
    None,

    [
      ( 2, 10, 'CAPSLOCK', 'CAPS'),
      ( 2, 6, 'A'),
      ( 2, 6, 'S'),
      ( 2, 6, 'D'),
      ( 2, 6, 'F'),
      ( 2, 6, 'G'),
      ( 2, 6, 'H'),
      ( 2, 6, 'J'),
      ( 2, 6, 'K'),
      ( 2, 6, 'L'),
      ( 2, 6, 'SEMI', ';'),
      ( 2, 6, 'QUOT', '\''),
      ( 2, 11, 'ENTER', 'Enter'),
      ],
    None,

    [
      ( 2, 12, 'LSHIFT', 'SHIFT'),
      ( 2, 6, 'Z'),
      ( 2, 6, 'X'),
      ( 2, 6, 'C'),
      ( 2, 6, 'V'),
      ( 2, 6, 'B'),
      ( 2, 6, 'N'),
      ( 2, 6, 'M'),
      ( 2, 6, 'COMMA', ','),
      ( 2, 6, 'PERIOD', '.'),
      ( 2, 6, 'SLASH', '/'),
      ( 2, 15, 'RSHIFT', 'SHIFT'),
      ],
    None,

    [
      ( 2, 5, 'Fn', 'Fn'),
      ( 2, 6, 'LCTRL', 'CTRL'),
      ( 2, 6, 'LOPT', 'OPT'),
      ( 2, 7, 'LCMD', 'CMD'),
      ( 2, 30, 'SPACE', 'Space'),
      ( 2, 8, 'RCMD', 'CMD'),
      ( 2, 6, 'ROPT', 'OPT'),
      ( 2, 6, None),
      ( 2, 6, 'Up', 'Up'),
      ],
    None,
    [
      ( 2, 68, None),
      ( 2, 6, 'Left', 'Lt'),
      ( 2, 6, 'Down', 'Dn'),
      ( 2, 6, 'Right', 'Rt'),
      ],
    None,
    ],


  }


TOP = {
  "K_ESCAPE": "esc",
  "K_F1": "F1", "K_F2": "F2", "K_F3": "F3", "K_F4": "F4",
  "K_F5": "F5", "K_F6": "F6", "K_F7": "F7", "K_F8": "F8",
  "K_F9": "F9", "K_F10": "F10", "K_F11": "F11", "K_F12": "F12",
  "K_SCROLLLOCK": "sclk", "K_PAUSE": "paus", "K_PRINT": "ptsc",

  "K_GRAVE": "`",
  "K_1": "1", "K_2": "2", "K_3": "3", "K_4": "4", "K_5": "5",
  "K_6": "6", "K_7": "7", "K_8": "8", "K_9": "9", "K_0": "0",
  "K_MINUS": "-", "K_EQUALS": "=", "K_BACKSPACE": "BS",

  "K_TAB": "tab",
  "K_Q": "Q", "K_W": "W", "K_E": "E", "K_R": "R", "K_T": "T",
  "K_Y": "Y", "K_U": "U", "K_I": "I", "K_O": "O", "K_P": "P",
  "K_LBRACKET": "[", "K_RBRACKET": "]", "K_BACKSLASH": "\\",

  "K_CAPSLOCK": "caps",
  "K_A": "A", "K_S": "S", "K_D": "D", "K_F": "F", "K_G": "G",
  "K_H": "H", "K_J": "J", "K_K": "K", "K_L": "L", "K_SEMICOLON": ";",
  "K_QUOTE": "'", "K_RETURN": "ret", "K_ENTER": "ent",

  "K_LSHIFT": "shift",
  "K_Z": "Z", "K_X": "X", "K_C": "C", "K_V": "V", "K_B": "B",
  "K_N": "N", "K_M": "M", "K_COMMA": ",", "K_PERIOD": ".", "K_SLASH": "/",
  "K_RSHIFT": "shift",

  "K_LCONTROL": "ctrl", "K_LLOGO": "logo", "K_LALT": "alt",
  "K_SPACE": "space",
  "K_RALT": "alt", "K_RLOGO": "logo", "K_RMENU": "menu", "K_RCONTROL": "ctrl",

  "K_INSERT": "ins", "K_HOME": "hom", "K_PGUP": "pgup",
  "K_DELETE": "del", "K_END": "end", "K_PGDN": "pgdn",
  "K_UP": "Up",
  "K_LEFT": "Lt", "K_DOWN": "Dn", "K_RIGHT": "Rt",

  "K_NUMLOCK": "nmlk",
  "K_KP_EQUALS": "=",
  "K_KP_SLASH": "/", "K_KP_STAR": "*", "K_KP_MINUS": "-",
  "K_KP_7": "7", "K_KP_8": "8", "K_KP_9": "9", "K_KP_PLUS": "+",
  "K_KP_4": "4", "K_KP_5": "5", "K_KP_6": "6",
  "K_KP_1": "1", "K_KP_2": "2", "K_KP_3": "3", "K_KP_ENTER": "ent",
  "K_KP_0": "0", "K_KP_SEP": ".",

  "K_LFN": "Fn", "K_RFN": "Fn",
  "K_LMETA": "<>", "K_RMETA": "<>",

  "M_1": "1", "M_2": "2", "M_3": "3", "M_4": "4", "M_5": "5",
  "M_x": "lt", "M_X": "rt", "M_y": "up", "M_Y": "down",
  }




# One-time convert kbd_desc.py to SQL statements.
def gen_sql ():
  PREAMBLE = r"""
DROP TABLE IF EXISTS inp_layouts;
DROP TABLE IF EXISTS inp_details;

CREATE TABLE inp_layouts (
  id SERIAL,
  name TEXT
);

CREATE TABLE inp_details (
  id SERIAL,
  layout INTEGER,
  label TEXT,  -- shown on keytop; NULL for empty space.
  name TEXT,   -- internal unique name; disabled (unmappable) for label==NULL
  x INTEGER,   -- nominal x position (0 = left, positive = right)
  y INTEGER,   -- nominal y position (0 = top, postiive = down)
  w INTEGER DEFAULT 1,   -- nominal width
  h INTEGER DEFAULT 1,   -- nominal height
  FOREIGN KEY (layout) REFERENCES inp_layouts(id)
);

"""

  print(PREAMBLE)

  layoutid = 1
  layoutmap = {}
  layoutlist = [None]
  for layoutname in sorted(KBD.keys()):
    layoutlist.append(layoutname)
    layoutmap[layoutname] = layoutid
    print("INSERT INTO inp_layouts VALUES (%d, '%s');" % (layoutid, layoutname))
    layoutid += 1

  print("")

  stdsymmap = {
    '`': "GRAVE",
    "-": "DASH",
    "=": "EQUALS",
    '!': "EXCL", '@': "AT", '#': "NUM", '$': "DOLLAR", '%': "PERCNT", '^': "HAT",
    '&': "AMP", '*': "AST", '(': "LPAR", ')': "RPAR", '_': "LOWBAR", '+': "PLUS",
    '[': "LSQB",
    ']': "RSQB",
    '\\': "BACKSLASH",
    '{': "LCUB", '}': "RCUB", '|': "BRVBAR",
    ';': "SEMI",
    '\'': "APOS",
    ':': "COLON", '"': "QUOT",
    ',': "COMMA",
    '.': "PERIOD",
    '/': "SOL",
    '<': "LT", '>': "GT", '?': "QUES",
    }

  def sqlescape(s):
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "''")
    return s
  
  for layoutid in xrange(1, len(layoutlist)):
    layoutkey = layoutlist[layoutid]
    layoutdetails = KBD[layoutkey]
    y = 0
    for rowid in xrange(0, len(layoutdetails)):
      layoutrow = layoutdetails[rowid]
      x = 0
      if layoutrow:
        for colid in xrange(0, len(layoutrow)):
          layoutelt = layoutrow[colid]
          (s, kw, kh) = layoutelt
          if s is None:
            lbl = kname = None
          elif '\f' in s:
            lbl, kname = s.split("\f", 1)
          else:
            lbl = kname = s
          if lbl and kname:
            print("INSERT INTO inp_details VALUES (NULL, %(layoutid)s, '%(label)s', '%(name)s', %(x)d, %(y)d, %(w)d, %(h)d);" % { 'layoutid': layoutid, 'label': sqlescape(lbl), 'name': sqlescape(kname), 'x': x, 'y': y, 'w': kw, 'h': kh })
          x += kw
      y += 1
    print("")
  
if __name__ == '__main__':
  # Generate SQL for keyboard layouts from python lists.
  gen_sql()
  # python -mkbd_desc | sqlite3 layouts.sqlite3

