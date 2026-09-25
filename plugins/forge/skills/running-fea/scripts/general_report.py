"""Turn a general-path FEA study (general_fea.run_study) into forge.check/1 measurements.

Every measurement carries a margin and, where it has one, a location -- R3 "physics in the
loop": specific margins + the offending location beat a pass/fail verdict.
"""
from __future__ import annotations

from pathlib import Path

import general_fea as g
import tet10

VALIDITY = ("linear elastic isotropic material, small deflection and small strain (linear geometry), "
            "static load, single solid, no contact / preload / thermal load, nodal stresses are "
            "CalculiX-extrapolated and element-averaged")


def _conv_text(c: dict, what: str, unit: str) -> str:
    vals = ", ".join(f"{v:.5g}" for v in c["values"])
    sizes = ", ".join(f"{h:g}" for h in c["sizes_mm"])
    s = f"{what} over mesh sizes [{sizes}] mm = [{vals}] {unit}; finest-level change {c['change_pct']:.3g} % " \
        f"(tolerance {c['tol_pct']} %)"
    if c["observed_order"] is not None:
        s += f", observed order p = {c['observed_order']:.2f}"
    if c["richardson"] is not None:
        s += f", Richardson estimate {c['richardson']:.5g} {unit} (GCI {c['gci_fine_pct']:.2g} %)"
    return s


def record(chk, study: dict, case: dict, case_name: str) -> bool:
    """Record all measurements; returns True when the evidence qualifies for L2."""
    levels = study["levels"]
    fin = levels[-1].post
    evidence_ok = True

    for hc in study["hand_calcs"]:
        loc = hc["location"]
        loc_s = g.loc_str(loc) if "xyz_mm" in loc else f"area-weighted over {loc.get('face_mean_over')}"
        ok = chk.measure(
            f"hand_calc_{hc['name']}_diff_pct", round(hc["diff_pct"], 4), "%", min=-hc["tol_pct"], max=hc["tol_pct"],
            location=loc_s,
            remediation=(
                f"FEA {hc['quantity']} = {hc['fea']:.6g} {hc['unit']} vs hand calc {hc['hand']:.6g} {hc['unit']} "
                f"({hc['formula']}): {hc['diff_pct']:+.2f} % against +/-{hc['tol_pct']} %. Check that the case's "
                "geometry, supports, load and material match the hand calc's assumptions (or that the hand calc "
                "itself is right) before trusting any number from this model."),
        )
        evidence_ok &= ok
        c = hc["conv"]
        ok = chk.measure(
            f"convergence_{hc['name']}_pct_change", round(c["change_pct"], 4), "%", max=c["tol_pct"],
            remediation=(_conv_text(c, hc["quantity"], hc["unit"]) + (
                ". The value keeps GROWING with refinement at a fixed rate: treat as singular, not as a result."
                if c["diverging"] else ". Add a finer level (or a [[refine]] zone where it changes) and re-run.")),
        )
        evidence_ok &= ok

    sc = study["stress_conv"]
    peak_loc = g.loc_str(fin["peak_von_mises_loc"])
    ok = chk.measure(
        "stress_convergence_pct_change", round(sc["change_pct"], 4), "%", max=sc["tol_pct"], location=peak_loc,
        remediation=_conv_text(sc, "peak von Mises (assessed region)", "MPa")
        + ". Refine near the peak location with a [[refine]] zone, or if it sits on a re-entrant corner, "
          "point load or edge of a clamped face, model the real fillet / load patch instead.",
    )
    evidence_ok &= ok

    diverging = [hs for hs in study["hotspots"] if hs["assessed"] and hs["conv"]["diverging"]]
    sing_txt = "; ".join(
        hs["label"] + " at " + g.loc_str(hs["location"]) + ": "
        + _conv_text(hs["conv"], f"max von Mises within {hs['radius_mm']:g} mm", "MPa")
        for hs in diverging)
    ok = chk.measure(
        "stress_singularity_suspected", bool(diverging), "1", equals=False,
        location=(g.loc_str(diverging[0]["location"]) if diverging else peak_loc),
        remediation=(
            "Peak stress does not converge with refinement -- a stress singularity (re-entrant corner, point "
            "load, knife-edge support or clamped-face edge), so its value is a mesh artefact, not a stress. "
            f"{sing_txt}. Replace the idealisation (fillet radius, distributed load patch, compliant support) "
            "or, if the region is irrelevant to failure, declare a [stress].exclude zone with the reason."
            if diverging else "no diverging hot spot"),
    )
    evidence_ok &= ok

    y = study["material"]["yield"]
    sf = study["safety_factor"]
    min_sf = float(case["requirement"]["min_safety_factor"])
    chk.measure(
        "safety_factor", round(sf, 4), "1", min=min_sf, location=peak_loc,
        remediation=(f"Safety factor {sf:.3f} = yield {y:.4g} MPa / peak von Mises {fin['peak_von_mises']:.4g} MPa "
                     f"vs required {min_sf} (margin {100 * (sf / min_sf - 1):+.1f} %) at {peak_loc}. Reduce the "
                     "load, add section or a fillet at that location, or pick a higher-yield material."),
    )

    max_imb = float(case["requirement"].get("max_reaction_imbalance_pct", g.MAX_REACTION_IMBALANCE_PCT))
    imb = study["reaction_imbalance_pct"]
    ok = chk.measure(
        "reaction_balance_pct", round(imb, 6), "%", max=max_imb,
        remediation=(f"Worst reaction force/moment imbalance over all levels {imb:.3g} % > {max_imb} % "
                     f"(finest: applied {fin['applied_force_n']} N, reactions {fin['reaction_force_n']} N). "
                     "The supports or the load application are wrong; do not trust this run."),
    )
    evidence_ok &= ok

    vmax = float(case.get("validity", {}).get("max_displacement_ratio", 0.1))
    ok = chk.measure(
        "small_deflection_ratio", round(study["small_deflection_ratio"], 6), "1", max=vmax,
        location=g.loc_str(fin["max_displacement_loc"]),
        remediation=(f"Max displacement {fin['max_displacement']:.4g} mm is {study['small_deflection_ratio']:.3g} of "
                     f"the part's smallest bounding-box dimension (limit {vmax}); linear small-deflection theory "
                     "is outside its validity. A geometrically nonlinear analysis is out of this skill's scope."),
    )
    evidence_ok &= ok

    ok = chk.measure(
        "tet10_ordering_max_midside_deviation", round(study["max_midside_deviation"], 6), "1",
        max=tet10.MAX_MIDSIDE_DEVIATION,
        remediation=("A C3D10 mid-edge node does not sit on the edge CalculiX expects (gmsh->CalculiX node "
                     "permutation broken); see references/tet10-node-ordering.md."),
    )
    evidence_ok &= ok
    return evidence_ok


def notes(study: dict, case: dict) -> str:
    mat = study["material"]
    levels = study["levels"]
    fin = levels[-1].post
    parts = [f"material {mat['name']}: E={mat['E']:.6g} MPa, nu={mat['nu']}, yield={mat['yield']:.4g} MPa, "
             f"density={mat['density']:.5g} kg/m3; source: {mat['source']}.",
             f"geometry {Path(study['step']).name} sha256={study['step_sha256'][:16]}..., volume "
             f"{study['volume_mm3']:.6g} mm3, mass {study['mass_kg']:.5g} kg."]
    for hc in study["hand_calcs"]:
        parts.append(f"hand calc {hc['name']}: {hc['formula']} = {hc['hand']:.6g} {hc['unit']} [{hc['reference']}]"
                     + (f" ({hc['notes']})" if hc["notes"] else "") + f"; FEA {hc['fea']:.6g} ({hc['diff_pct']:+.2f} %).")
    parts.append("levels: " + "; ".join(
        f"h={lv.h:g}mm {lv.n_nodes} nodes/{lv.n_elements} C3D10, minSJ={lv.min_sj:.2f}, "
        f"vM_peak={lv.post['peak_von_mises']:.4g} MPa, |u|max={lv.post['max_displacement']:.4g} mm, "
        f"imbalance={lv.post['reaction_imbalance_pct']:.2g} %" for lv in levels) + ".")
    parts.append(f"max displacement {fin['max_displacement']:.5g} mm at {g.loc_str(fin['max_displacement_loc'])}; "
                 f"peak von Mises {fin['peak_von_mises']:.5g} MPa at {g.loc_str(fin['peak_von_mises_loc'])}; "
                 f"peak max-principal {fin['peak_principal']:.5g} MPa at {g.loc_str(fin['peak_principal_loc'])}.")
    ex = case.get("stress", {}).get("exclude", [])
    if ex:
        gc = study["global_stress_conv"]
        parts.append(f"stress exclusions: " + "; ".join(f"{e['distance_mm']} mm around {e['faces']} ({e['reason']})"
                                                         for e in ex)
                     + f". Unexcluded peak {fin['global_peak_von_mises']:.5g} MPa at "
                       f"{g.loc_str(fin['global_peak_von_mises_loc'])}, trend {gc['state']} "
                       f"({', '.join(f'{v:.4g}' for v in gc['values'])} MPa) -- NOT used for the safety factor.")
    for hs in study["hotspots"]:
        if hs["conv"]["diverging"]:
            parts.append(f"diverging hot spot: {hs['label']} at {g.loc_str(hs['location'])} "
                         f"({', '.join(f'{v:.4g}' for v in hs['conv']['values'])} MPa)"
                         + ("" if hs["assessed"] else " inside a declared exclusion zone") + ".")
    parts.append(f"supports: {[(b['name'], b['type'], b['faces']) for b in case['bc']]}; loads: "
                 + "; ".join(f"{ld['name']}: {ld['desc']}" for ld in levels[-1].loads) + ".")
    parts.append(f"Validity limits: {VALIDITY}. Evidence level L2 at best (simulated + hand calc + "
                 "convergence); never 'validated' without physical test data (L4).")
    return " ".join(parts)
