"""Minimal Matplotlib track plotter, independent of geometry and training."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M1.13]: Add an optional diagnostic view of a selected pose, footprint, rays, and checkpoint numbers for geometry inspection.

from pathlib import Path
import numpy as np


def plot_track(track, ax, checkpoints=True):
    from matplotlib.path import Path as PlotPath
    from matplotlib.patches import PathPatch
    from shapely.geometry.polygon import orient
    vertices, codes = [], []
    # Opposing ring winding preserves the infield hole in the filled road.
    road = orient(track.road, sign=1.0)
    for ring in [road.exterior, *road.interiors]:
        xy = np.asarray(ring.coords)
        vertices.extend(xy)
        codes.extend([PlotPath.MOVETO] + [PlotPath.LINETO]*(len(xy)-2) + [PlotPath.CLOSEPOLY])
    ax.add_patch(PathPatch(PlotPath(vertices, codes), facecolor='#444b55', edgecolor='#222831', lw=0.6))
    ax.plot(*track.points.T, color='#f5bf42', lw=0.65, linestyle='--', label='Reference path')
    if checkpoints:
        for gate in track.checkpoints[1:]:
            ax.plot(*np.array(gate.endpoints).T, color='#50b7c1', lw=0.65, alpha=0.8)
    start = track.checkpoints[0]
    ax.plot(*np.array(start.endpoints).T, color='#e45151', lw=2.5, label='Start / finish')
    progress = min(30, track.length_m/20)
    arrow_start = np.array(track.point_at(progress))
    arrow_end = arrow_start + np.array(track.tangent_at(progress))*max(15, track.length_m/100)
    ax.annotate('', xy=arrow_end, xytext=arrow_start,
                arrowprops={'arrowstyle': '->', 'color': '#e45151', 'lw': 1.8})
    source = track.metadata.get('source', 'unknown')
    ax.set_title(f'{track.name.capitalize()} — {track.length_m/1000:.2f} km\n'
                 f'{track.width_m:g} m synthetic road · {source}', fontsize=11)
    ax.set_aspect('equal', adjustable='box')
    ax.autoscale_view()
    ax.margins(0.08)
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.grid(alpha=0.15)
    ax.legend(loc='best', fontsize=7)


def view_tracks(tracks, output=None, show=False, checkpoints=True):
    if not tracks:
        raise ValueError('Select at least one track')
    import matplotlib
    if not show:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    columns = min(3, len(tracks))
    rows = (len(tracks) + columns - 1)//columns
    fig, axes = plt.subplots(rows, columns, figsize=(6*columns, 6*rows), squeeze=False)
    for track, ax in zip(tracks, axes.flat):
        plot_track(track, ax, checkpoints)
    for ax in list(axes.flat)[len(tracks):]:
        ax.set_visible(False)
    fig.tight_layout()
    if output:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=160)
    if show:
        plt.show()
    plt.close(fig)
