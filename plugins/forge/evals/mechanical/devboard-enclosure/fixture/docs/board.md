# Dev board to enclose

Coordinate system for every CAD file in this project: origin at the centre of the board's bottom face, +X towards the end opposite the USB-C port, +Z up. Units mm.

- PCB 51.0 x 21.0 x 1.6 mm, bottom face at z = 0.
- USB-C receptacle on the top face at the -X end, centred in Y: 7.35 (X) x 8.94 (Y) x 3.16 (Z) mm; its mouth sits 0.5 mm beyond the board edge, at x = -26.0.
- Other components: all inside x -18.0..25.5, y -9.5..9.5, at most 2.5 mm above the board top.
- The board rests on standoffs that touch only its bottom face.
- A mating USB-C plug's overmold is 12.4 (Y) x 6.5 (Z) mm and 20 mm long, centred on the receptacle.

`cad/fixtures/board.py` (board keep-out) and `cad/fixtures/usbc_plug.py` (plug keep-out) model these volumes. Don't edit them.
