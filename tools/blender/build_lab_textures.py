"""Generate seamless PBR textures for Athanor Ascension inside Blender.

Runs through the Blender MCP bridge (or ``blender --background --python``).
Outputs 1024x1024 tileable albedo and normal maps to ``game/assets/textures``
and saves a .blend containing the source image datablocks.

Materials:
    floor_epoxy   dark slate-grey resin floor with fine aggregate speckle
    steel_brushed brushed 304 stainless steel with horizontal grain
"""

import os

import bpy
import numpy as np

SIZE = 1024
OUT_DIR = os.path.join(os.getcwd(), "game", "assets", "textures")
BLEND_PATH = os.path.join(os.getcwd(), "assets", "blender", "lab_textures.blend")


def periodic_value_noise(size, cells, seed):
    """Tileable value noise: lattice wraps every ``cells`` samples."""
    rng = np.random.default_rng(seed)
    lattice = rng.random((cells, cells)).astype(np.float32)
    xs = np.linspace(0, cells, size, endpoint=False, dtype=np.float32)
    ys = np.linspace(0, cells, size, endpoint=False, dtype=np.float32)
    x0 = np.floor(xs).astype(np.int32)
    y0 = np.floor(ys).astype(np.int32)
    fx = xs - x0
    fy = ys - y0
    # Smoothstep interpolation
    fx = fx * fx * (3.0 - 2.0 * fx)
    fy = fy * fy * (3.0 - 2.0 * fy)

    x1 = (x0 + 1) % cells
    y1 = (y0 + 1) % cells
    x0 %= cells
    y0 %= cells

    v00 = lattice[np.ix_(y0, x0)]
    v10 = lattice[np.ix_(y0, x1)]
    v01 = lattice[np.ix_(y1, x0)]
    v11 = lattice[np.ix_(y1, x1)]

    top = v00 * (1 - fx)[None, :] + v10 * fx[None, :]
    bottom = v01 * (1 - fx)[None, :] + v11 * fx[None, :]
    return top * (1 - fy)[:, None] + bottom * fy[:, None]


def fbm(size, base_cells, octaves, seed, persistence=0.5):
    total = np.zeros((size, size), dtype=np.float32)
    amplitude = 1.0
    norm = 0.0
    cells = base_cells
    for octave in range(octaves):
        total += amplitude * periodic_value_noise(size, cells, seed + octave * 101)
        norm += amplitude
        amplitude *= persistence
        cells *= 2
    return total / norm


def height_to_normal(height, strength=2.0):
    dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    nx = -dx * strength
    ny = -dy * strength
    nz = np.ones_like(height)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= length
    ny /= length
    nz /= length
    # Map [-1, 1] -> [0, 1]; Blender normal maps are +Y (OpenGL style).
    return np.stack([(nx * 0.5 + 0.5), (ny * 0.5 + 0.5), (nz * 0.5 + 0.5)], axis=-1)


def save_image(name, rgb, path):
    rgba = np.ones((rgb.shape[0], rgb.shape[1], 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(rgb, 0.0, 1.0)
    image = bpy.data.images.new(name, width=rgb.shape[1], height=rgb.shape[0], alpha=False)
    # Blender expects bottom-up rows and linear float pixels.
    image.pixels.foreach_set(rgba[::-1].ravel())
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()
    return image


def epoxy_floor():
    grain = fbm(SIZE, 8, 4, 7)
    speckle = fbm(SIZE, 220, 2, 19)
    aggregate = (speckle > 0.72).astype(np.float32) * 0.10
    base = np.array([0.055, 0.062, 0.070], dtype=np.float32)
    variation = (grain - 0.5)[:, :, None] * 0.045
    rgb = base[None, None, :] + variation + aggregate[:, :, None]
    # Faint 1 m seam grid, 8 tiles across the 8 m texture.
    step = SIZE // 8
    seam = np.zeros((SIZE, SIZE), dtype=np.float32)
    seam[:, ::step] = -0.012
    seam[::step, :] = -0.012
    rgb = rgb + seam[:, :, None]
    height = grain * 0.6 + speckle * 0.4
    return rgb, height_to_normal(height, strength=1.2)


def brushed_steel():
    fine = fbm(SIZE, 512, 2, 41)
    broad = fbm(SIZE, 6, 3, 53)
    # Horizontal brush grain: stretch noise along X by sampling a thin band.
    grain = np.repeat(fine[:1, :], SIZE, axis=0)
    streaks = 0.5 + (grain - 0.5) * 0.7 + (fine - 0.5) * 0.25
    value = 0.62 + (streaks - 0.5) * 0.10 + (broad - 0.5) * 0.06
    rgb = np.stack([value * 0.98, value, value * 1.02], axis=-1)
    height = streaks * 0.8 + fine * 0.2
    return rgb, height_to_normal(height, strength=3.0)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)

    for name, builder in (("floor_epoxy", epoxy_floor), ("steel_brushed", brushed_steel)):
        rgb, normal = builder()
        save_image(f"{name}_albedo", rgb, os.path.join(OUT_DIR, f"{name}_albedo.png"))
        save_image(f"{name}_normal", normal, os.path.join(OUT_DIR, f"{name}_normal.png"))
        print(f"[textures] wrote {name} albedo + normal")

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"[textures] saved {BLEND_PATH}")


main()
