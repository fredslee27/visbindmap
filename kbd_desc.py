#!/usr/bin/env python

KBD = {
  # Tuples are: (label, height[cells], width[cells])
  'mouse': [  # list of list
    [ # row 1
      (None, 1, 6),
      ('MOUSE4', 1, 6),
      ],
    [
      ('MOUSE1', 1, 6),
      ('MOUSE2', 1, 6),
      ('MOUSE3', 1, 6),
      ],
    [
      (None, 1, 6),
      ('MOUSE5', 1, 6),
      ],
    None,
    [
      (None, 1, 6),
      ('up', 1, 6),
      ],
    [
      ('left', 1, 6),
      (None, 1, 6),
      ('right', 1, 6),
      ],
    [
      (None, 1, 6),
      ('down', 1, 6),
      ],
    ],

  'en_US (pc104)': [  # list of list
    [ # row 1
      ('Esc', 1, 6),
      (None, 1, 3),
      ('F1', 1, 6),
      ('F2', 1, 6),
      ('F3', 1, 6),
      ('F4', 1, 6),
      (None, 1, 3),
      ('F5', 1, 6),
      ('F6', 1, 6),
      ('F7', 1, 6),
      ('F8', 1, 6),
      (None, 1, 3),
      ('F9', 1, 6),
      ('F10', 1, 6),
      ('F11', 1, 6),
      ('F12', 1, 6),
      ],

    None,

    [
      ('`', 1, 6),
      ('1\fPA', 1, 6),
      ('2\fRE', 1, 6),
      ('3\fCI', 1, 6),
      ('4\fVO', 1, 6),
      ('5\fMU', 1, 6),
      ('6\fXA', 1, 6),
      ('7\fZE', 1, 6),
      ('8\fBI', 1, 6),
      ('9\fSO', 1, 6),
      ('0\fNO', 1, 6),
      ('-', 1, 6),
      ('=', 1, 6),
      ('BS', 1, 9),
      ],

    [
      ('Tab\fTAB', 1, 9),
      ('Q', 1, 6),
      ('W', 1, 6),
      ('E', 1, 6),
      ('R', 1, 6),
      ('T', 1, 6),
      ('Y', 1, 6),
      ('U', 1, 6),
      ('I', 1, 6),
      ('O', 1, 6),
      ('P', 1, 6),
      ('[', 1, 6),
      (']', 1, 6),
      ('\\', 1, 6),
      ],

    [
      ('CAPS\fCAPSLOCK', 1, 10),
      ('A', 1, 6),
      ('S', 1, 6),
      ('D', 1, 6),
      ('F', 1, 6),
      ('G', 1, 6),
      ('H', 1, 6),
      ('J', 1, 6),
      ('K', 1, 6),
      ('L', 1, 6),
      (';', 1, 6),
      ('\'', 1, 6),
      ('Enter\fENTER', 1, 11),
      ],

    [
      ('SHIFT\fLSHIFT', 1, 12),
      ('Z', 1, 6),
      ('X', 1, 6),
      ('C', 1, 6),
      ('V', 1, 6),
      ('B', 1, 6),
      ('N', 1, 6),
      ('M', 1, 6),
      (',', 1, 6),
      ('.', 1, 6),
      ('/', 1, 6),
      ('SHIFT\fRSHIFT', 1, 15),
      ],

    [
      ('CTRL\fLCTRL', 1, 9),
      ('LOGO\fLLOGO', 1, 8),
      ('ALT\fLALT', 1, 9),
      ('Space\fSPACE', 1, 27),
      ('ALT\fRALT', 1, 9),
      ('LOGO\fRLOGO', 1, 8),
      ('Menu\fMENU', 1, 8),
      ('CTRL\fRCTRL', 1, 9),
      ],


    None,
    None,

    [
      ('Ins\fINS', 1, 6),
      ('Home\fHOME', 1, 6),
      ('PgUp\fPGUP', 1, 6),

      (None, 1, 12),

      ('PrSc\fPRINT', 1, 6),
      ('ScLk\fSCROLLLOCK', 1, 6),
      ('Pau\fPAUSE', 1, 6),

      (None, 1, 12),

        ('NL\fNUMLOCK', 1, 6),
        ('/\fKP_/', 1, 6),
        ('*\fKP_*', 1, 6),
        ('-\fKP_-', 1, 6),
      ],

    [
      ('Del\fDEL', 1, 6),
      ('End\fEND', 1, 6),
      ('PgDn\fPGDN', 1, 6),

      (None, 1, 42),

        ('7\fKP_7', 1, 6),
        ('8\fKP_8', 1, 6),
        ('9\fKP_9', 1, 6),
        ('+\fKP_+', 2, 6),
      ],

    [
      (None, 1, 18),
      (None, 1, 42),

        ('4\fKP_4', 1, 6),
        ('5\fKP_5', 1, 6),
        ('6\fKP_6', 1, 6),
        (None, 1, 6),
      ],

    [
      (None, 1, 6),
      ('Up\fUP', 1, 6),
      (None, 1, 6),

      (None, 1, 42),

        ('1\fKP_1', 1, 6),
        ('2\fKP_2', 1, 6),
        ('3\fKP_3', 1, 6),
        ('Ret\fKP_RET', 2, 6),
      ],

    [
      ('Lt\fLEFT', 1, 6),
      ('Dn\fDOWN', 1, 6),
      ('Rt\fRIGHT', 1, 6),

      (None, 1, 42),

        ('0\fKP_0', 1, 12),
        ('.\fKP_.', 1, 6),
        (None, 1, 6),
      ],

    ],


  'en_US (HHKL2)': [
    [
      ('Esc', 1, 6),
      ('1\fPA', 1, 6),
      ('2\rRE', 1, 6),
      ('3\fCI', 1, 6),
      ('4\fVO', 1, 6),
      ('5\fMU', 1, 6),
      ('6\fXA', 1, 6),
      ('7\fZE', 1, 6),
      ('8\fBI', 1, 6),
      ('9\fSO', 1, 6),
      ('0\fNO', 1, 6),
      ('-', 1, 6),
      ('=', 1, 6),
      ('\\', 1, 6),
      ('`', 1, 6),
      ],
    [
      ('Tab\fTAB', 1, 9),
      ('Q', 1, 6),
      ('W', 1, 6),
      ('E', 1, 6),
      ('R', 1, 6),
      ('T', 1, 6),
      ('Y', 1, 6),
      ('U', 1, 6),
      ('I', 1, 6),
      ('O', 1, 6),
      ('P', 1, 6),
      ('[', 1, 6),
      (']', 1, 6),
      ('Del', 1, 9),
      ],
    [
      ('CTRL', 1, 10),
      ('A', 1, 6),
      ('S', 1, 6),
      ('D', 1, 6),
      ('F', 1, 6),
      ('G', 1, 6),
      ('H', 1, 6),
      ('J', 1, 6),
      ('K', 1, 6),
      ('L', 1, 6),
      (';', 1, 6),
      ('\'', 1, 6),
      ('Enter\fENTER', 1, 14),
      ],
    [
      ('SHIFT\fLSHIFT', 1, 13),
      ('Z', 1, 6),
      ('X', 1, 6),
      ('C', 1, 6),
      ('V', 1, 6),
      ('B', 1, 6),
      ('N', 1, 6),
      ('M', 1, 6),
      (',', 1, 6),
      ('.', 1, 6),
      ('/', 1, 6),
      ('SHIFT\fRSHIFT', 1, 11),
      ('Fn\fRFN', 1, 6),
      ],
    [
      (None, 1, 6),
      ('Fn\fLFN', 1, 6),
      ('ALT\fLALT', 1, 6),
      ('<>\fLMETA', 1, 6),
      ('Space\fSPACE', 1, 36),
      ('<>\fRMETA', 1, 6),
      ('ALT\fRALT', 1, 6),
      (None, 1, 6),
      ('Up\fUP', 1, 6),
      ],
    [
      (None, 1, 64),
      (None, 1, 8),
      ('Lt\fLEFT', 1, 6),
      ('Dn\fDOWN', 1, 6),
      ('Rt\fRIGHT', 1, 6),
      ],
    ],



  'en_GB (pc105)': [  # list of list
    [ # row 1
      ('Esc', 1, 6),
      (None, 1, 3),
      (None, 1, 1),
      ('F1', 1, 6),
      ('F2', 1, 6),
      ('F3', 1, 6),
      ('F4', 1, 6),
      (None, 1, 3),
      ('F5', 1, 6),
      ('F6', 1, 6),
      ('F7', 1, 6),
      ('F8', 1, 6),
      (None, 1, 3),
      ('F9', 1, 6),
      ('F10', 1, 6),
      ('F11', 1, 6),
      ('F12', 1, 6),
      ],

    None,

    [
      ('`', 1, 6),
      ('1\fPA', 1, 6),
      ('2\fRE', 1, 6),
      ('3\fCI', 1, 6),
      ('4\fVO', 1, 6),
      ('5\fMU', 1, 6),
      ('6\fXA', 1, 6),
      ('7\fZE', 1, 6),
      ('8\fBI', 1, 6),
      ('9\fSO', 1, 6),
      ('0\fNO', 1, 6),
      ('-', 1, 6),
      ('=', 1, 6),
      ('BS', 1, 10),
      ],

    [
      ('Tab\fTAB', 1, 9),
      ('Q', 1, 6),
      ('W', 1, 6),
      ('E', 1, 6),
      ('R', 1, 6),
      ('T', 1, 6),
      ('Y', 1, 6),
      ('U', 1, 6),
      ('I', 1, 6),
      ('O', 1, 6),
      ('P', 1, 6),
      ('[', 1, 6),
      (']', 1, 6),
      (None, 1, 1),
      ('Enter\fENTER', 2, 6),
      ],

    [
      ('CAPS\fCAPSLOCK', 1, 10),
      ('A', 1, 6),
      ('S', 1, 6),
      ('D', 1, 6),
      ('F', 1, 6),
      ('G', 1, 6),
      ('H', 1, 6),
      ('J', 1, 6),
      ('K', 1, 6),
      ('L', 1, 6),
      (';', 1, 6),
      ('\'', 1, 6),
      ('#', 1, 6),
      ],

    [
      ('SHIFT\fLSHIFT', 1, 6),
      ('\\', 1, 6),
      ('Z', 1, 6),
      ('X', 1, 6),
      ('C', 1, 6),
      ('V', 1, 6),
      ('B', 1, 6),
      ('N', 1, 6),
      ('M', 1, 6),
      (',', 1, 6),
      ('.', 1, 6),
      ('/', 1, 6),
      ('SHIFT\fRSHIFT', 1, 16),
      ],

    [
      ('CTRL\fLCTRL', 1, 9),
      ('LOGO\fLLOGO', 1, 8),
      ('ALT\fLALT', 1, 9),
      ('Space\fSPACE', 1, 28),
      ('ALT\fRALT', 1, 9),
      ('LOGO\fRLOGO', 1, 8),
      ('Menu\fMENU', 1, 8),
      ('CTRL\fRCTRL', 1, 9),
      ],


    None,
    None,

    [
      ('Ins\fINS', 1, 6),
      ('Home\fHOME', 1, 6),
      ('PgUp\fPGUP', 1, 6),

      (None, 1, 12),

      ('PrSc\fPRINT', 1, 6),
      ('ScLk\fSCROLLLOCK', 1, 6),
      ('Pau\fPAUSE', 1, 6),

      (None, 1, 12),

        ('NL\fNUMLOCK', 1, 6),
        ('/\fKP_/', 1, 6),
        ('*\fKP_*', 1, 6),
        ('-\fKP_-', 1, 6),
      ],

    [
      ('Del\fDEL', 1, 6),
      ('End\fEND', 1, 6),
      ('PgDn\fPGDN', 1, 6),

      (None, 1, 42),

        ('7\fKP_7', 1, 6),
        ('8\fKP_8', 1, 6),
        ('9\fKP_9', 1, 6),
        ('+\fKP_+', 2, 6),
      ],

    [
      (None, 1, 18),
      (None, 1, 42),

        ('4\fKP_4', 1, 6),
        ('5\fKP_5', 1, 6),
        ('6\fKP_6', 1, 6),
        (None, 1, 6),
      ],

    [
      (None, 1, 6),
      ('Up\fUP', 1, 6),
      (None, 1, 6),

      (None, 1, 42),

        ('1\fKP_1', 1, 6),
        ('2\fKP_2', 1, 6),
        ('3\fKP_3', 1, 6),
        ('Ret\fKP_RET', 2, 6),
      ],

    [
      ('Lt\fLEFT', 1, 6),
      ('Dn\fDOWN', 1, 6),
      ('Rt\fRIGHT', 1, 6),

      (None, 1, 42),

        ('0\fKP_0', 1, 12),
        ('.\fKP_.', 1, 6),
        (None, 1, 6),
      ],

    ],






  'PS3': [
    [
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
#      (None, 1, 3),
      ('L2\fB/8', 1, 6),
#      (None, 1, 3),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('R2\fB/9', 1, 6),
      ],
    [
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 3),
#      (None, 1, 6),
      ('L1\fB/10', 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('R1\fB/11', 1, 6),
      ],
    [
      (None, 1, 6),
      ('up\fB/4', 1, 6),
      (None, 1, 6),
      (None, 1, 36),
      ('T\fB/12', 1, 6),
      ],
    [
      ('left\fB/7', 1, 6),
      (None, 1, 6),
      ('right\fB/5', 1, 6),
      (None, 1, 6),
      ('SELECT\fB/0', 1, 6),
      (None, 1, 6),
      ('START\fB/3', 1, 6),
      (None, 1, 6),
      ('S\fB/15', 1, 6),
      (None, 1, 6),
      ('O\fB/13', 1, 6),
      ],
    [
      (None, 1, 6),
      ('down\fB/6', 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ("HOME\fB/16", 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('X\fB/14', 1, 6),
      ],
    [
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('Ly-\fA/1/-', 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('Ry-\fA/3/-', 1, 6),
      ],
    [
      (None, 1, 6),
      (None, 1, 6),
      ('Lx-\fA/0/-', 1, 6),
      ('L3\fB/1', 1, 6),
      ('Lx+\fA/0/+', 1, 6),
      (None, 1, 6),
      ('Rx-\fA/2/-', 1, 6),
      ('R3\fB/2', 1, 6),
      ('Rx+\fA/2/+', 1, 6),
      ],
    [
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('Ly+\fA/1/+', 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('Ry+\fA/3/+', 1, 6),
      ],
    ],

  'XB360': [
    [
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('LT', 1, 6),
#      (None, 1, 3),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('RT', 1, 6),
      ],
    [
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 3),
      ('TL', 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('TR', 1, 6),
      ],
    [
      (None, 1, 6),
      ('Ly-', 1, 6),
      (None, 1, 6),
      (None, 1, 36),
      ('Y', 1, 6),
      ],
    [
      ('Lx-', 1, 6),
      ('LS', 1, 6),
      ('Lx+', 1, 6),
      (None, 1, 6),
      ('BACK', 1, 6),
      (None, 1, 6),
      ('START', 1, 6),
      (None, 1, 6),
      ('X', 1, 6),
      (None, 1, 6),
      ('B', 1, 6),
      ],
    [
      (None, 1, 6),
      ('Ly+', 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ("GUIDE", 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('A', 1, 6),
      ],
    [
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('up', 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('Ry-', 1, 6),
      ],
    [
      (None, 1, 6),
      (None, 1, 6),
      ('left', 1, 6),
      (None, 1, 6),
      ('right', 1, 6),
      (None, 1, 6),
      ('Rx-', 1, 6),
      ('RS', 1, 6),
      ('Rx+', 1, 6),
      ],
    [
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('down', 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      (None, 1, 6),
      ('Ry+', 1, 6),
      ],
    ],


  'en_US (mac104)': [
    [ # row 1
      ('Esc', 1, 6),
      (None, 1, 3),
      ('F1', 1, 6),
      ('F2', 1, 6),
      ('F3', 1, 6),
      ('F4', 1, 6),
      (None, 1, 3),
      ('F5', 1, 6),
      ('F6', 1, 6),
      ('F7', 1, 6),
      ('F8', 1, 6),
      (None, 1, 3),
      ('F9', 1, 6),
      ('F10', 1, 6),
      ('F11', 1, 6),
      ('F12', 1, 6),
      ],

    None,

    [
      ('`', 1, 6),
      ('1\fPA', 1, 6),
      ('2\fRE', 1, 6),
      ('3\fCI', 1, 6),
      ('4\fVO', 1, 6),
      ('5\fMU', 1, 6),
      ('6\fXA', 1, 6),
      ('7\fZE', 1, 6),
      ('8\fBI', 1, 6),
      ('9\fSO', 1, 6),
      ('0\fNO', 1, 6),
      ('-', 1, 6),
      ('=', 1, 6),
      ('BS', 1, 9),
      ],

    [
      ('Tab\fTAB', 1, 9),
      ('Q', 1, 6),
      ('W', 1, 6),
      ('E', 1, 6),
      ('R', 1, 6),
      ('T', 1, 6),
      ('Y', 1, 6),
      ('U', 1, 6),
      ('I', 1, 6),
      ('O', 1, 6),
      ('P', 1, 6),
      ('[', 1, 6),
      (']', 1, 6),
      ('\\', 1, 6),
      ],

    [
      ('CAPS\fCAPSLOCK', 1, 10),
      ('A', 1, 6),
      ('S', 1, 6),
      ('D', 1, 6),
      ('F', 1, 6),
      ('G', 1, 6),
      ('H', 1, 6),
      ('J', 1, 6),
      ('K', 1, 6),
      ('L', 1, 6),
      (';', 1, 6),
      ('\'', 1, 6),
      ('Enter\fENTER', 1, 11),
      ],

    [
      ('SHIFT\fLSHIFT', 1, 12),
      ('Z', 1, 6),
      ('X', 1, 6),
      ('C', 1, 6),
      ('V', 1, 6),
      ('B', 1, 6),
      ('N', 1, 6),
      ('M', 1, 6),
      (',', 1, 6),
      ('.', 1, 6),
      ('/', 1, 6),
      ('SHIFT\fRSHIFT', 1, 15),
      ],

    [
      ('CTRL\fLCTRL', 1, 8),
      ('ALT\fLALT', 1, 6),
      ('CMD\fLCMD', 1, 8),
      ('Space\fSPACE', 1, 43),
      ('CMD\fRCMD', 1, 8),
      ('ALT\fRALT', 1, 6),
      ('CTRL\fRCTRL', 1, 8),
      ],


    None,
    None,

    [
      ('Ins\fINS', 1, 6),
      ('Home\fHOME', 1, 6),
      ('PgUp\fPGUP', 1, 6),

      (None, 1, 12),

      ('F13\fF13', 1, 6),
      ('F14\fF14', 1, 6),
      ('F15\fF15', 1, 6),

      (None, 1, 12),

        ('clr\fKP_CLEAR', 1, 6),
        ('=\fKP_=', 1, 6),
        ('/\fKP_/', 1, 6),
        ('*\fKP_*', 1, 6),
      ],

    [
      ('Del\fDEL', 1, 6),
      ('End\fEND', 1, 6),
      ('PgDn\fPGDN', 1, 6),

      (None, 1, 42),

        ('7\fKP_7', 1, 6),
        ('8\fKP_8', 1, 6),
        ('9\fKP_9', 1, 6),
        ('-\fKP_-', 1, 6),
      ],

    [
      (None, 1, 18),
      (None, 1, 42),

        ('4\fKP_4', 1, 6),
        ('5\fKP_5', 1, 6),
        ('6\fKP_6', 1, 6),
        ('+\fKP_+', 1, 6),
        (None, 1, 6),
      ],

    [
      (None, 1, 6),
      ('Up\fUP', 1, 6),
      (None, 1, 6),

      (None, 1, 42),

        ('1\fKP_1', 1, 6),
        ('2\fKP_2', 1, 6),
        ('3\fKP_3', 1, 6),
        ('Ret\fKP_RET', 2, 6),
      ],

    [
      ('Lt\fLEFT', 1, 6),
      ('Dn\fDOWN', 1, 6),
      ('Rt\fRIGHT', 1, 6),

      (None, 1, 42),

        ('0\fKP_0', 1, 12),
        ('.\fKP_.', 1, 6),
        (None, 1, 6),
      ],

    ],

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
  gen_sql()
  # python -mkbd_desc | sqlite3 layouts.sqlite3

