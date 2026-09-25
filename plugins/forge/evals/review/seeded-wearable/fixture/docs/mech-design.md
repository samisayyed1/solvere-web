# PulseBand rev B -- mechanical design description

All values come from params/params.toml. Origin: centre of the battery pocket floor, z up.

| Feature | Value |
|---|---|
| Housing outer | 52.2 x 37.2 x 9.6 mm, wall `housing.wall_thickness` 1.6 mm |
| Battery pocket | `housing.battery_pocket` 41.0 x 26.0 x 6.0 mm, cell lies on the pocket floor, centred |
| PCB standoffs | `housing.pcb_boss` d 3.0 mm x 6.0 mm tall from the pocket floor, at `housing.pcb_boss_positions`; the PCB (1.0 mm) sits on top at z = 6.0 mm |
| Lid | 52.2 x 37.2 mm plate, 1.6 mm, seated on the housing rim |
| Optical window | 12 x 12 mm clear insert, frame wall `lid.window_frame_wall` |
| Tether exit | `housing.cable_exit_diameter` 3.2 mm hole in the +X end wall, 3.0 mm tether |
| Housing rim height | `housing.rim_height` 8.00 mm (floor to rim seat) |
| U5 window top | `pcb.afe_top_height` 7.70 mm above the pocket floor |
| Light-seal gasket | `gasket.compressed_thickness` 0.10 mm, on top of U5 |
