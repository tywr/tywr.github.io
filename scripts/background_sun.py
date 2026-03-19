"""Generate an SVG replicating the Helios sun from the amp panel GUI."""

import math
import random


class PerlinNoise:
    """Port of the C++ PerlinNoise class with seed 2025."""

    def __init__(self, seed=2025):
        self.p = list(range(256))
        rng = random.Random(seed)
        rng.shuffle(self.p)
        self.p = self.p + self.p[:]

    @staticmethod
    def _fade(t):
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    @staticmethod
    def _lerp(t, a, b):
        return a + t * (b - a)

    @staticmethod
    def _grad(hash_val, x, y, z):
        h = hash_val & 15
        u = x if h < 8 else y
        v = y if h < 4 else (x if h == 12 or h == 14 else z)
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

    def noise(self, x, y, z):
        p = self.p
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        Z = int(math.floor(z)) & 255

        x -= math.floor(x)
        y -= math.floor(y)
        z -= math.floor(z)

        u = self._fade(x)
        v = self._fade(y)
        w = self._fade(z)

        A = p[X] + Y
        AA = p[A] + Z
        AB = p[A + 1] + Z
        B = p[X + 1] + Y
        BA = p[B] + Z
        BB = p[B + 1] + Z

        return self._lerp(
            w,
            self._lerp(
                v,
                self._lerp(
                    u,
                    self._grad(p[AA], x, y, z),
                    self._grad(p[BA], x - 1, y, z),
                ),
                self._lerp(
                    u,
                    self._grad(p[AB], x, y - 1, z),
                    self._grad(p[BB], x - 1, y - 1, z),
                ),
            ),
            self._lerp(
                v,
                self._lerp(
                    u,
                    self._grad(p[AA + 1], x, y, z - 1),
                    self._grad(p[BA + 1], x - 1, y, z - 1),
                ),
                self._lerp(
                    u,
                    self._grad(p[AB + 1], x, y - 1, z - 1),
                    self._grad(p[BB + 1], x - 1, y - 1, z - 1),
                ),
            ),
        )


def create_wobbly_path(center, radius, noise_amount, noise_frequency, z_offset):
    """Port of createWobblyPath — returns list of (x, y) points."""
    perlin = PerlinNoise(seed=2025)
    num_points = 200
    points = []

    for i in range(num_points + 1):
        angle = 2.0 * math.pi * i / num_points
        noise_x = (math.cos(angle) + 1.0) * noise_frequency
        noise_y = (math.sin(angle) + 1.0) * noise_frequency
        noise_value = (perlin.noise(noise_x, noise_y, z_offset) + 1.0) / 2.0
        modulated_radius = radius * (
            1.0 - noise_amount + noise_amount * 2.0 * noise_value
        )
        x = center[0] + modulated_radius * math.cos(angle)
        y = center[1] + modulated_radius * math.sin(angle)
        points.append((x, y))

    return points


def points_to_svg_path(points, closed=True):
    """Convert points to an SVG path d attribute."""
    parts = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
    for x, y in points[1:]:
        parts.append(f"L {x:.2f} {y:.2f}")
    if closed:
        parts.append("Z")
    return " ".join(parts)


def hex_to_rgb(c):
    return ((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)


def colour_to_hex(c):
    return f"#{(c >> 16) & 0xFF:02x}{(c >> 8) & 0xFF:02x}{c & 0xFF:02x}"


def lerp_colour(c1, c2, t):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_sun_svg(width=256, height=256):
    c1 = 0x88C0D0  # sun_yellow
    c2 = 0xECEFF4
    bg2 = 0x262626

    cx, cy = width / 2, height / 2
    max_radius = min(width, height) * 0.45

    black_hole_offset_x = 0.2 * max_radius
    black_hole_offset_y = -0.2 * max_radius
    bh_cx = cx + black_hole_offset_x
    bh_cy = cy + black_hole_offset_y

    border_thickness = 2.0
    num_layers = 10
    noise_frequency = 1.0
    noise_amount = 0.3
    z_offset_step = 0.1

    elements = []

    # Clip definition for the outer circle
    inner_radius = max_radius - border_thickness * max_radius * 0.03

    # Black hole path (computed early for use in mask)
    hole_radius = inner_radius * 0.25
    hole_points = create_wobbly_path(
        (bh_cx, bh_cy),
        hole_radius,
        noise_amount * 0.5,
        noise_frequency,
        num_layers * z_offset_step,
    )
    hole_d = points_to_svg_path(hole_points)

    elements.append(f"<defs>")
    elements.append(f'  <clipPath id="sun-clip">')
    elements.append(f'    <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{inner_radius:.2f}"/>')
    elements.append(f"  </clipPath>")
    elements.append(f'  <mask id="sun-hole-mask">')
    elements.append(f'    <rect width="{width}" height="{height}" fill="white"/>')
    elements.append(f'    <path d="{hole_d}" fill="black"/>')
    elements.append(f"  </mask>")
    elements.append(f"</defs>")

    # Outer border ellipse with gradient
    grad_id = "sun-grad"
    elements.append(f"<defs>")
    elements.append(
        f'  <linearGradient id="{grad_id}" x1="{cx - max_radius}" y1="{cy}" '
        f'x2="{cx + max_radius}" y2="{cy}" gradientUnits="userSpaceOnUse">'
    )
    elements.append(f'    <stop offset="0%" stop-color="{colour_to_hex(c1)}"/>')
    elements.append(f'    <stop offset="100%" stop-color="{colour_to_hex(c2)}"/>')
    elements.append(f"  </linearGradient>")
    elements.append(f"</defs>")

    # Masked group: cuts out the black hole as transparent
    elements.append(f'<g mask="url(#sun-hole-mask)">')

    elements.append(
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{max_radius:.2f}" '
        f'fill="none" stroke="url(#{grad_id})" stroke-width="{border_thickness}"/>'
    )

    # Clipped group for sun layers
    elements.append(f'<g clip-path="url(#sun-clip)">')

    # Base fill (c1)
    elements.append(
        f'  <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{inner_radius:.2f}" '
        f'fill="{colour_to_hex(c1)}"/>'
    )

    # Wobbly noise layers
    for i in range(1, num_layers):
        proportion = 1.0 - i / num_layers
        current_radius = inner_radius * proportion
        colour = lerp_colour(c1, c2, i / (num_layers - 1))
        z_offset = i * z_offset_step
        layer_cx = cx + black_hole_offset_x * i / num_layers
        layer_cy = cy + black_hole_offset_y * i / num_layers
        points = create_wobbly_path(
            (layer_cx, layer_cy),
            current_radius,
            noise_amount,
            noise_frequency,
            z_offset,
        )
        d = points_to_svg_path(points)
        elements.append(f'  <path d="{d}" fill="{colour}"/>')

    elements.append(f"</g>")  # close clip group
    elements.append(f"</g>")  # close mask group

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
    )
    svg += "\n".join(elements)
    svg += "\n</svg>\n"
    return svg


if __name__ == "__main__":
    svg = generate_sun_svg()
    out = "helios_sun.svg"
    with open(out, "w") as f:
        f.write(svg)
    print(f"Written to {out}")
