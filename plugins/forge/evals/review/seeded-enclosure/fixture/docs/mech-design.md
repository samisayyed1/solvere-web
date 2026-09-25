# SensorHub rev A -- mechanical design description

All values come from params/params.toml. Origin: base floor top surface, z up.

| Feature | Value |
|---|---|
| Base outer | 64.2 x 48.0 x 10.5 mm, wall `enclosure.base_wall` 2.0 mm, floor 2.0 mm; rim at z = 8.5 mm |
| Insert bosses | four 7 x 7 mm corner blocks, full height, each with an M3 heat-set insert (OD 4.6 mm) centred 2.5 mm from both outer edges |
| PCB slot | `base.pcb_slot_width` 60.20 mm long (PCB length direction) |
| PCB standoffs | four d 5.0 mm posts, `pcb.standoff_height` 4.0 mm tall, PCB (`pcb.thickness` 1.6 mm) on top |
| J1 USB-C | on the PCB top face at the +X edge, `j1.height` 3.26 mm tall, opening in the +X wall |
| Lid | 64.2 x 48.0 mm plate, `enclosure.lid_wall` thick; it sits on the rim, so its underside is at `lid.inner_ceiling_z` 8.5 mm when closed |
| Lid screws | four `lid.screw_hole_diameter` 3.4 mm holes, centres `lid.screw_hole_edge_offset` 2.5 mm from both edges at each corner, into M3 heat-set inserts in the base corners |
| DC cable exit | `base.cable_exit_diameter` 5.0 mm hole in the -X wall, 4.5 mm OD cable to the J3 screw terminal |
