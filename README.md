# VisMapper

GUI to help visually layout bindings for a game on a particular input device, with an emphasis on drag-and-drop rearrangement.


## Input device layout description

TODO: not have the descriptor be so obtuse to modify.

Input device descriptions are currently hard-coded into kbd\_desc.py.
The format is as obtuse and the hard-coding.
The plan is to have the description stored in a more sensible format, perhaps JSON or a sqlite3 db/file.

## Command Pack

The commands available for binding to input elements are stored in sqlite3 files.
These command packs are loaded separately from input bind arrangements.
The canonical location for these command packs are under cmdset/.
The default loaded on startup is ./cmds.sqlite3, with a fallback to a hard-coded builtin database if loading that file fails.

## Planar clusters

The Steam Controller combined with the Steam Client is able to adjust the behaviors of 2-dimensional-oriented input elements, for example the touchpads, to behave a cluster of other input elements.

