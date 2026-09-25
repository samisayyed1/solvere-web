"""Quadratic-tetrahedron (C3D10) and quadratic-triangle (tri6) element facts, with proofs.

Everything the general FEA path assumes about node ordering lives here, so it can be tested
in one place (``plugins/forge/tests/mech2/test_running_fea_general_tet10.py``).

Node ordering (0-based local indices; see references/tet10-node-ordering.md):

    corner nodes 0..3 are identical in gmsh and CalculiX.
    mid-edge node      gmsh (type 11)      CalculiX / Abaqus C3D10
        4               edge 0-1            edge 0-1
        5               edge 1-2            edge 1-2
        6               edge 2-0            edge 2-0
        7               edge 3-0            edge 0-3
        8               edge 3-2            edge 1-3   <- differs
        9               edge 3-1            edge 2-3   <- differs

So the CalculiX connectivity is ``gmsh[GMSH_TO_CCX_TET10]`` with the last two mid-edge nodes
swapped. This was established empirically in ccx 2.23 / gmsh 4.15.2, not taken from a
secondary source: without the swap CalculiX aborts with ``*ERROR in e_c3d: nonpositive
jacobian``; with it, a constant-stress patch test reproduces the exact stress to round-off.
:func:`ordering_report` re-proves the geometry of every mesh the pipeline solves.

Standard library + numpy only.
"""
from __future__ import annotations

import numpy as np

# CalculiX C3D10 local node i is gmsh tet10 local node GMSH_TO_CCX_TET10[i].
GMSH_TO_CCX_TET10 = (0, 1, 2, 3, 4, 5, 6, 7, 9, 8)

# Mid-edge node -> (corner a, corner b) for each convention (0-based).
CCX_TET10_EDGES = {4: (0, 1), 5: (1, 2), 6: (2, 0), 7: (0, 3), 8: (1, 3), 9: (2, 3)}
GMSH_TET10_EDGES = {4: (0, 1), 5: (1, 2), 6: (2, 0), 7: (3, 0), 8: (3, 2), 9: (3, 1)}

# gmsh tri6 (type 9): corners 0..2, then mid-edge 3=(0,1), 4=(1,2), 5=(2,0).
TRI6_EDGES = {3: (0, 1), 4: (1, 2), 5: (2, 0)}

# 7-point Dunavant rule, degree 5, on the reference triangle (weights sum to 1/2).
_A1, _B1 = 0.059715871789770, 0.470142064105115
_A2, _B2 = 0.797426985353087, 0.101286507323456
_W0, _W1, _W2 = 0.225, 0.132394152788506, 0.125939180544827
TRI_QP = np.array([
    [1 / 3, 1 / 3],
    [_B1, _B1], [_A1, _B1], [_B1, _A1],
    [_B2, _B2], [_A2, _B2], [_B2, _A2],
])  # (xi, eta) with L1 = 1 - xi - eta, L2 = xi, L3 = eta
TRI_QW = 0.5 * np.array([_W0, _W1, _W1, _W1, _W2, _W2, _W2])


def tri6_shape(xi: np.ndarray, eta: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Shape functions N (q,6) and derivatives dN/dxi, dN/deta (q,6) in gmsh tri6 order."""
    l1, l2, l3 = 1.0 - xi - eta, xi, eta
    n = np.stack([l1 * (2 * l1 - 1), l2 * (2 * l2 - 1), l3 * (2 * l3 - 1),
                  4 * l1 * l2, 4 * l2 * l3, 4 * l3 * l1], axis=-1)
    # d/dxi: dl1 = -1, dl2 = 1, dl3 = 0 ; d/deta: dl1 = -1, dl2 = 0, dl3 = 1
    dxi = np.stack([-(4 * l1 - 1), 4 * l2 - 1, 0 * l3,
                    4 * (l1 - l2), 4 * l3, -4 * l3], axis=-1)
    deta = np.stack([-(4 * l1 - 1), 0 * l2, 4 * l3 - 1,
                     -4 * l2, 4 * l2, 4 * (l1 - l3)], axis=-1)
    return n, dxi, deta


_N, _DXI, _DETA = tri6_shape(TRI_QP[:, 0], TRI_QP[:, 1])


def tri6_quadrature(xyz: np.ndarray, tris: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Quadrature data for curved tri6 faces.

    ``xyz`` (n,3) node coordinates, ``tris`` (k,6) node rows in gmsh tri6 order.
    Returns (points (k,q,3), weights*|J| (k,q), unit normals (k,q,3) -- orientation as given by
    the node order, NOT necessarily outward).
    """
    x = xyz[tris]                                   # (k,6,3)
    pts = np.einsum("qa,kad->kqd", _N, x)
    t1 = np.einsum("qa,kad->kqd", _DXI, x)
    t2 = np.einsum("qa,kad->kqd", _DETA, x)
    nrm = np.cross(t1, t2)
    jac = np.linalg.norm(nrm, axis=-1)
    if np.any(jac <= 0):
        raise ValueError("degenerate tri6 surface element (zero area Jacobian)")
    return pts, jac * TRI_QW[None, :], nrm / jac[..., None]


def consistent_nodal_forces(xyz: np.ndarray, tris: np.ndarray, traction) -> np.ndarray:
    """Consistent nodal force vector for a traction field over tri6 faces.

    ``traction(points (k,q,3), normals (k,q,3)) -> (k,q,3)`` in MPa (N/mm^2); returns (n,3) N.
    Note: for a uniform traction on a flat tri6 the corner nodes get ZERO force and the three
    mid-edge nodes get A*t/3 each -- lumping equal shares onto all nodes is wrong and fails the
    constant-stress patch test.
    """
    pts, wj, nrm = tri6_quadrature(xyz, tris)
    t = traction(pts, nrm)                          # (k,q,3)
    fe = np.einsum("qa,kq,kqd->kad", _N, wj, t)     # (k,6,3)
    out = np.zeros((xyz.shape[0], 3))
    np.add.at(out, tris.reshape(-1), fe.reshape(-1, 3))
    return out


def face_integrals(xyz: np.ndarray, tris: np.ndarray, nodal: np.ndarray | None = None):
    """Area, area centroid and (optionally) the area integral of a nodal vector field."""
    pts, wj, _ = tri6_quadrature(xyz, tris)
    area = float(wj.sum())
    centroid = np.einsum("kq,kqd->d", wj, pts) / area
    if nodal is None:
        return area, centroid, None, pts, wj
    vals = np.einsum("qa,kad->kqd", _N, nodal[tris])   # field at quadrature points
    return area, centroid, vals, pts, wj


def signed_volumes(xyz: np.ndarray, tets_ccx: np.ndarray) -> np.ndarray:
    """Six times the signed volume of each element's corner tetrahedron (CalculiX needs > 0)."""
    p = xyz[tets_ccx[:, :4]]
    return np.einsum("ij,ij->i", p[:, 1] - p[:, 0], np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 0]))


def midside_deviation(xyz: np.ndarray, conn: np.ndarray, edges: dict[int, tuple[int, int]]) -> np.ndarray:
    """Per-element max |x_mid - (x_a + x_b)/2| / |x_a - x_b| over the given edge table.

    0 for straight-sided elements whose mid-edge nodes match the table; about 0.5 or more
    when a mid-edge node sits on a different edge (wrong ordering). Curved boundary edges
    give small non-zero values (the node sits on the true geometry, off the chord).
    """
    worst = np.zeros(conn.shape[0])
    for mid, (a, b) in edges.items():
        xa, xb, xm = xyz[conn[:, a]], xyz[conn[:, b]], xyz[conn[:, mid]]
        dev = np.linalg.norm(xm - 0.5 * (xa + xb), axis=1) / np.linalg.norm(xa - xb, axis=1)
        worst = np.maximum(worst, dev)
    return worst


def ordering_report(xyz: np.ndarray, tets_ccx: np.ndarray) -> dict:
    """Evidence that a connectivity array is a valid CalculiX C3D10 ordering."""
    dev = midside_deviation(xyz, tets_ccx, CCX_TET10_EDGES)
    vol6 = signed_volumes(xyz, tets_ccx)
    return {
        "n_elements": int(tets_ccx.shape[0]),
        "max_midside_deviation": float(dev.max()),
        "p99_midside_deviation": float(np.percentile(dev, 99)),
        "min_corner_volume_mm3": float(vol6.min() / 6.0),
        "n_nonpositive_volume": int((vol6 <= 0).sum()),
    }


# Deviation above this means a mid-edge node is on the wrong edge (a wrong ordering gives
# >= ~0.5). Curved-geometry mid-edge nodes sit off the chord by far less than this for any
# mesh fine enough to be worth solving.
MAX_MIDSIDE_DEVIATION = 0.25
