# Metatron Architecture: Mathematical Design

This document describes the geometry and counts implemented by `build_metatron_architecture.py`. The character and symbolism context is in [character_context_mapping.md](./character_context_mapping.md); the main architecture guide covers Blender and Unity operation.

## 1. Geometric Model

The generator defines 13 points in Blender's $X$–$Y$ plane: one origin, six vertices on a regular hexagon of radius $R$, and six vertices on a concentric regular hexagon of radius $2R$. Elevation is controlled independently by $E=\texttt{VERTICAL\_ELEVATION}$.

For zero-based node index $k$:

$$
P_k =
\begin{cases}
\left(0,0,0\right), & k=0,\\
\left(R\cos\theta_k,\ R\sin\theta_k,\ E\right), & 1\le k\le 6,\\
\left(2R\cos\theta_k,\ 2R\sin\theta_k,\ 2E\right), & 7\le k\le 12,
\end{cases}
$$

where

$$
\theta_k =
\begin{cases}
60^\circ(k-1), & 1\le k\le 6,\\
60^\circ(k-7), & 7\le k\le 12.
\end{cases}
$$

The center remains at $Z=0$. Consequently, nonzero $E$ raises the inner ring by $E$ and the outer ring by $2E$; it does not translate the entire structure uniformly.

### Default coordinate checks

For $R=18$ m and $E=0$:

| Node | Angle | Position $(x,y,z)$ in meters |
| :--- | ---: | :--- |
| `Node_00_Origin` | — | $(0,0,0)$ |
| `Node_01_Inner_000deg` | $0^\circ$ | $(18,0,0)$ |
| `Node_02_Inner_060deg` | $60^\circ$ | $(9,15.59,0)$ |
| `Node_07_Outer_000deg` | $0^\circ$ | $(36,0,0)$ |
| `Node_08_Outer_060deg` | $60^\circ$ | $(18,31.18,0)$ |

Coordinates in the script use floating-point trigonometry, so values mathematically equal to zero can be represented by very small residuals.

## 2. Complete-Graph Connectivity

Every distinct pair of nodes is connected once. The graph is the complete graph $K_{13}$:

$$
|V|=13,\qquad
|E|=\binom{13}{2}=\frac{13\cdot12}{2}=78.
$$

The nested loops use $0\le i<j<13$. This both avoids self-links and gives deterministic names `Strut_II_to_JJ`, with the smaller index first. Every node has degree 12.

The four Blender strut groups partition the 78 edges without overlap:

| Group | Pair set | Count |
| :--- | :--- | ---: |
| `01_Radial_Spokes` | Origin to each of the 12 ring nodes | $12$ |
| `02_Inner_Hexagon_And_Star` | All pairs among inner nodes 1–6 | $\binom{6}{2}=15$ |
| `03_Outer_Hexagon_And_Star` | All pairs among outer nodes 7–12 | $\binom{6}{2}=15$ |
| `04_Cross_Lattice_Chords` | Each inner node paired with each outer node | $6\cdot6=36$ |
| **Total** |  | **$12+15+15+36=78$** |

## 3. Strut Transform Mathematics

For an edge from node $i$ to node $j$:

$$
\Delta_{ij}=P_j-P_i,\qquad
L_{ij}=\|\Delta_{ij}\|_2,\qquad
M_{ij}=\frac{P_i+P_j}{2},\qquad
\hat{d}_{ij}=\frac{\Delta_{ij}}{L_{ij}}.
$$

The strut object is placed at midpoint $M_{ij}$. Its local $+Z$ axis is rotated to $\hat{d}_{ij}$ with `direction.to_track_quat('Z', 'Y')`, then represented as an XYZ Euler rotation. The shared mesh is one meter deep, centered from local $Z=-0.5$ to $Z=+0.5$, and has unit radius in local $X$ and $Y$. The object scale is:

$$
(\texttt{STRUT\_RADIUS},\ \texttt{STRUT\_RADIUS},\ L_{ij}).
$$

Thus the strut's centerline endpoints are the two node centers. The struts intentionally extend into the hub meshes; the generator does not shorten them to the hub surfaces.

Each hub instances the same unit-radius icosphere mesh and uses uniform scale `HUB_RADIUS`. The position radius $R$ and visual hub radius are independent parameters.

## 4. Geometry and Object Counts

* **13 hub mesh objects** share one 80-triangle unit icosphere mesh.
* **78 strut mesh objects** share one `STRUT_SIDES`-sided unit prism mesh.
* At the default six strut sides, a triangulated hexagonal prism contributes approximately 20 triangles per instance; estimated total mesh geometry is $13\cdot80+78\cdot20=2{,}600$ triangles.
* Seven Empty objects provide the root, hub group, strut group, and four strut subgroups. These are hierarchy objects, not additional mesh geometry.

Triangle totals assume polygon caps are triangulated by the FBX/Unity import path. They do not include collider geometry, which is added in Unity.

## 5. Parameter Constraints

The script requires finite positive `RING_RADIUS`, `HUB_RADIUS`, and `STRUT_RADIUS`; finite `VERTICAL_ELEVATION`; and integer `STRUT_SIDES >= 3`. In particular, a positive ring radius ensures no two generated node coordinates coincide, so every edge has nonzero length and $\hat{d}_{ij}$ is defined.

The values are a procedural design model, not a claim that a historical source prescribes this coordinate system or graph.
