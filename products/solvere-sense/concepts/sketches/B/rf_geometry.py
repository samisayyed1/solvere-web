"""Concept B RF geometry arithmetic (G1 sketch, L1 analysis only).

Every input comes from params/params.toml; nothing here is a design value.
Run: python3 concepts/sketches/B/rf_geometry.py
"""
import math

C = 299_792_458.0            # m/s (params sensor.wavelength_free_space basis)
F = 60.0e9                   # sensor.freq_centre (MDS p.12)
GAP_STEP = 2.5               # radome.antenna_gap_step, mm (MDS p.12 item 4)
KEEPOUT = 60.0               # radome.keepout_half_angle, deg
MOD_L, MOD_W = 31.5, 25.0    # sensor.radar_module_length/width, mm (MDS p.3)
WALL = {"FDM": 1.2, "SLA (unsupported)": 1.0, "MJF (PN)": 2.5}  # mfg.fdm.min_wall; sla.toml; mfg.mjf.wall_min_pn
MDS_ER = {"PC": 2.9, "ABS low": 2.0, "ABS high": 3.5, "PMMA": 2.6, "PE": 2.3, "PBT high": 4.0}  # MDS p.11-12

half_lambda = C / (2 * F) * 1e3
print(f"lambda/2 free space = {half_lambda:.4f} mm (MDS rounds to 2.5 mm)")

print("\nRadome thickness T = N * lambda/2 / sqrt(er)  [mm]")
for name, er in MDS_ER.items():
    print(f"  {name:9s} er={er:4.1f}: " + ", ".join(f"N={n}: {n*half_lambda/math.sqrt(er):.2f}" for n in (1, 2, 3)))

print("\nLargest er for which T(N) >= process minimum wall")
for proc, w in WALL.items():
    print(f"  {proc:18s} min {w} mm: " + ", ".join(f"N={n}: er<={(n*half_lambda/w)**2:.2f}" for n in (1, 2, 3)))

a = math.hypot(MOD_L, MOD_W) / 2  # conservative: antenna anywhere inside the module outline
print(f"\nConservative antenna half-aperture (module half-diagonal) a = {a:.2f} mm")
for n in (1, 2, 3):
    d = n * GAP_STEP
    r = a + d * math.tan(math.radians(KEEPOUT))
    print(f"  d = {d:.1f} mm (N={n}): keep-out radius at radome inner face = {r:.2f} mm, dia {2*r:.1f} mm")

print(f"\nSlant path through a flat radome at the cone edge = T / cos({KEEPOUT:.0f} deg) (straight-line, no refraction) "
      f"= {1/math.cos(math.radians(KEEPOUT)):.2f} x T")
