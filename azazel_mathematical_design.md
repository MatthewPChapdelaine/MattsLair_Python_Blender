# Azazel Architecture: Mathematical Design

This document records the equations and counts implemented by `build_azazel_architecture.py`. The interpretive character context is in [character_context_mapping.md](./character_context_mapping.md); Blender setup and Unity import guidance are in [azazel_architecture_documentation.md](./azazel_architecture_documentation.md).

## 1. Tower Coordinates

The design has one central tower and five perimeter towers. Let $R=\texttt{RING\_RADIUS}$ and let $i$ index the perimeter towers from 1 through 5:

$$
P_0=(0,0,0),
\qquad
P_i=\left(R\cos\theta_i,\ R\sin\theta_i,\ 0\right),
$$

$$
\theta_i=18^\circ+72^\circ(i-1),\qquad i\in\{1,2,3,4,5\}.
$$

The five angular positions are $18^\circ$, $90^\circ$, $162^\circ$, $234^\circ$, and $306^\circ$. All towers start at ground level. For causeway construction, the script raises a copy of each tower's $X,Y$ coordinate to height $H=\texttt{BRIDGE\_ELEVATION}$:

$$
Q_i=(P_{i,x},P_{i,y},H), \qquad 0\le i\le5.
$$

`Q_0` is the elevated center endpoint; it does not move the central tower itself.

### Default perimeter coordinates

For $R=20$ m and $H=3$ m:

| Tower | Angle | Ground position $P_i$ (m) | Causeway point $Q_i$ (m) |
| :--- | ---: | :--- | :--- |
| `Tower_00_Ashen_Citadel` | — | $(0,0,0)$ | $(0,0,3)$ |
| `Tower_01_Watcher_018deg` | $18^\circ$ | $(19.02,6.18,0)$ | $(19.02,6.18,3)$ |
| `Tower_02_Watcher_090deg` | $90^\circ$ | $(0,20,0)$ | $(0,20,3)$ |
| `Tower_03_Watcher_162deg` | $162^\circ$ | $(-19.02,6.18,0)$ | $(-19.02,6.18,3)$ |
| `Tower_04_Watcher_234deg` | $234^\circ$ | $(-11.76,-16.18,0)$ | $(-11.76,-16.18,3)$ |
| `Tower_05_Watcher_306deg` | $306^\circ$ | $(11.76,-16.18,0)$ | $(11.76,-16.18,3)$ |

Coordinates are calculated using floating-point trigonometry; displayed values are rounded to two decimal places.

## 2. Causeway Graph

The causeways form a sparse, connected graph with six vertices:

$$
V=\{0,1,2,3,4,5\}.
$$

Its edge set contains five spokes from the citadel and four consecutive perimeter links:

$$
E=
\{(0,i)\mid 1\le i\le5\}
\cup
\{(i,i+1)\mid 1\le i\le4\}.
$$

Therefore:

$$
|V|=6,\qquad |E|=5+4=9.
$$

The perimeter edge $(5,1)$ is intentionally omitted. The central tower has degree 5; perimeter towers 1 and 5 have degree 2; towers 2, 3, and 4 have degree 3. The graph remains connected because every perimeter tower is linked to the central citadel.

## 3. Causeway Transforms

For each connection $(i,j)\in E$, the endpoint difference, length, midpoint, and direction are:

$$
\Delta_{ij}=Q_j-Q_i,\qquad
L_{ij}=\|\Delta_{ij}\|_2,\qquad
M_{ij}=\frac{Q_i+Q_j}{2},\qquad
\hat{d}_{ij}=\frac{\Delta_{ij}}{L_{ij}}.
$$

The causeway is centered at $M_{ij}$ and its local $+Z$ axis is aligned to $\hat{d}_{ij}$. The one-meter centered causeway mesh has unit radius in $X,Y$ and unit depth along $Z$. Its object scale is:

$$
\left(\frac{W}{2},\ \frac{W}{2},\ L_{ij}\right),
\qquad W=\texttt{CAUSEWAY\_WIDTH}.
$$

The first two scale components turn the unit mesh's two-meter diameter into the configured width $W$; the last stretches its one-meter depth to the endpoint distance.

Because each causeway endpoint has the same height $H$, default edge lengths have simple forms:

* **Spokes:** $L=R$.
* **Perimeter links:** adjacent towers differ by $72^\circ$, so the chord length is
  $$
  L=2R\sin(36^\circ).
  $$
  For the default $R=20$ m this is approximately $23.51$ m.
* **Missing closure:** the omitted perimeter chord would have the same length, but is not instantiated.

## 4. Tower Transforms and Mesh Counts

The shared spire mesh has local $Z$ coordinates from 0 to 1, base radius 1, and top radius 0.58. A tower at base position $P_i$ with horizontal radius $r$ and height $h$ transforms a local point $(x,y,z)$ to:

$$
(P_{i,x}+rx,\ P_{i,y}+ry,\ hz).
$$

The citadel uses $(r,h)=(\texttt{CORE\_RADIUS},\texttt{CORE\_HEIGHT})$; each watcher uses $(r,h)=(\texttt{WATCHTOWER\_RADIUS},\texttt{WATCHTOWER\_HEIGHT})$. Thus tower geometry rises from its ground position without moving the base.

For an $n$-sided prism with triangulated caps, the approximate triangle count is:

$$
T(n)=2n+2(n-2)=4n-4.
$$

The default 8-sided spire has $T(8)=28$ triangles; the 4-sided causeway has $T(4)=12$. With six spires and nine causeways:

$$
6\cdot28+9\cdot12=276\text{ triangles}.
$$

This estimate assumes the FBX/Unity path triangulates the cap polygons. The scene contains 15 mesh objects sharing two mesh datablocks, plus five Empty hierarchy objects.

## 5. Parameter Constraints and Intent

`RING_RADIUS`, both tower radii and heights, and `CAUSEWAY_WIDTH` must be finite and positive. `BRIDGE_ELEVATION` must be finite and nonnegative. `SPIRE_SIDES` and `CAUSEWAY_SIDES` must be integers of at least 3. These bounds prevent degenerate geometry and zero-length edges.

The sparse graph and omitted perimeter chord are deliberate mathematical choices for the open silhouette. They are artistic design decisions, not mathematical or historical properties attributed to Azazel.
