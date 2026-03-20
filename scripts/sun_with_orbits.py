"""Generate an SVG with slanted elliptical orbits."""

import math


def orbit_path(cx, cy, radius, incline_deg, tilt_deg, view_dist, num_points=200):
    """Generate a perspective-projected circular orbit path.

    The orbit is a circle of given radius in 3D, viewed with perspective.
    incline_deg: tilt of orbital plane around X axis (0 = face-on, 90 = edge-on)
    tilt_deg: rotation of orbital plane around Z axis (slants the ellipse)
    view_dist: viewer distance along Z (larger = less perspective, 0 = no perspective)
    """
    incline = math.radians(incline_deg)
    tilt = math.radians(tilt_deg)
    ci, si = math.cos(incline), math.sin(incline)
    ct, st = math.cos(tilt), math.sin(tilt)
    parts = []
    for i in range(num_points + 1):
        angle = 2.0 * math.pi * i / num_points
        # Circle in XY plane
        px = radius * math.cos(angle)
        py = radius * math.sin(angle)
        # Rotate around X axis (incline — tips the plane, creates depth)
        py2 = py * ci
        pz2 = py * si
        # Rotate around Z axis (slant in screen plane)
        px3 = px * ct - py2 * st
        py3 = px * st + py2 * ct
        pz3 = pz2
        # Perspective projection (viewer at z = view_dist looking at origin)
        if view_dist > 0:
            scale = view_dist / (view_dist - pz3)
        else:
            scale = 1.0
        x = cx + px3 * scale
        y = cy + py3 * scale
        if i == 0:
            parts.append(f"M {x:.2f} {y:.2f}")
        else:
            parts.append(f"L {x:.2f} {y:.2f}")
    parts.append("Z")
    return " ".join(parts)


def generate_orbits(width=1080, height=2040, offset_x=0, offset_y=-0.25):
    # Center shifted by offset fractions (0 = center, 0.5 = edge)
    cx = width / 2 + width * offset_x
    cy = height / 2 + height * offset_y
    half = min(width, height) / 2

    # Shared orbital plane parameters
    incline = 78  # degrees — how tilted the plane is (60 = fairly oblique)
    tilt = -15  # degrees — rotation of the plane in screen space
    view_dist = half * 4  # viewer distance (larger = subtler perspective)

    # Orbit definitions: (radius as fraction of half-canvas, opacity)
    orbits = [
        (0.8, 1),
        (1.2, 1),
        (1.6, 1),
        (2.0, 1),
        (2.4, 1),
        (2.8, 1),
    ]

    orbit_elements = []
    for frac, opacity in orbits:
        radius = half * frac
        d = orbit_path(cx, cy, radius, incline, tilt, view_dist)
        orbit_elements.append(
            f'<path d="{d}" fill="none" stroke="#262626" '
            f'stroke-width="0.6" opacity="{opacity}"/>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
    )
    svg += "\n".join(orbit_elements)
    svg += "\n</svg>\n"
    return svg


if __name__ == "__main__":
    svg = generate_orbits()
    out = "sun_orbits.svg"
    with open(out, "w") as f:
        f.write(svg)
    print(f"Written to {out}")
