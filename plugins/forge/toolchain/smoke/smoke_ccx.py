"""CalculiX smoke: cantilever tip deflection vs Euler-Bernoulli hand calc. Usage: smoke_ccx.py <ccx>."""
import pathlib
import re
import subprocess
import sys
import tempfile

L, B, H = 100.0, 10.0, 10.0          # mm
E, NU, F = 210000.0, 0.3, 100.0      # MPa, -, N (tip load, -z)
NX, NY, NZ = 40, 4, 4                # C3D8I elements


def main(ccx: str) -> int:
    nid = lambda i, j, k: 1 + i + (NX + 1) * (j + (NY + 1) * k)
    lines = ["*HEADING", "Forge smoke cantilever", "*NODE"]
    for k in range(NZ + 1):
        for j in range(NY + 1):
            for i in range(NX + 1):
                lines.append(f"{nid(i, j, k)}, {L * i / NX:.6f}, {B * j / NY:.6f}, {H * k / NZ:.6f}")
    lines.append("*ELEMENT, TYPE=C3D8I, ELSET=EALL")
    e = 1
    for k in range(NZ):
        for j in range(NY):
            for i in range(NX):
                n = [nid(i, j, k), nid(i + 1, j, k), nid(i + 1, j + 1, k), nid(i, j + 1, k),
                     nid(i, j, k + 1), nid(i + 1, j, k + 1), nid(i + 1, j + 1, k + 1), nid(i, j + 1, k + 1)]
                lines.append(f"{e}, " + ", ".join(map(str, n)))
                e += 1
    fix = [nid(0, j, k) for k in range(NZ + 1) for j in range(NY + 1)]
    tip = [(nid(NX, j, k), (0.5 if j in (0, NY) else 1.0) * (0.5 if k in (0, NZ) else 1.0))
           for k in range(NZ + 1) for j in range(NY + 1)]
    wsum = sum(w for _, w in tip)
    lines += ["*NSET, NSET=FIX"] + [str(n) for n in fix]
    lines += ["*NSET, NSET=TIP"] + [str(n) for n, _ in tip]
    lines += ["*MATERIAL, NAME=STEEL", "*ELASTIC", f"{E}, {NU}",
              "*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL", "*STEP", "*STATIC",
              "*BOUNDARY", "FIX, 1, 3", "*CLOAD"]
    lines += [f"{n}, 3, {-F * w / wsum:.8f}" for n, w in tip]
    lines += ["*NODE PRINT, NSET=TIP", "U", "*END STEP"]
    work = pathlib.Path(tempfile.mkdtemp(prefix="forge-smoke-ccx-"))
    (work / "cant.inp").write_text("\n".join(lines) + "\n")
    subprocess.run([ccx, "-i", "cant"], cwd=work, check=True, capture_output=True, timeout=300)
    dat = (work / "cant.dat").read_text()
    uz = [float(m.group(3)) for m in re.finditer(
        r"^\s*\d+\s+(\S+)\s+(\S+)\s+(\S+)\s*$", dat.split("displacements")[-1], re.M)]
    fea = -sum(uz) / len(uz)
    inertia = B * H ** 3 / 12.0
    hand = F * L ** 3 / (3.0 * E * inertia)
    diff = (fea - hand) / hand
    ok = abs(diff) < 0.03
    assert abs((fea - 1.2 * hand) / (1.2 * hand)) >= 0.03, "negative control: check cannot fail"
    print(f"tip deflection FEA={fea:.5f} mm hand(EB)={hand:.5f} mm diff={diff * 100:+.2f}% "
          f"(tolerance 3%, shear adds ~0.8%) work={work} -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
