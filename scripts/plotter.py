#!/usr/bin/env python3
import argparse
import re
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from matplotlib.patches import ConnectionPatch, Polygon


NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"


def read_pp3(path):
    """Read the chart center, dimensions, and scale from a PP3 source file."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Could not find PP3 file: {path}")

    text = path.read_text(encoding="utf-8")

    # PP3 defaults, used only when a setting is omitted from the source file.
    defaults = {
        "center_rectascension": 5.8,
        "center_declination": 0.0,
        "box_width": 15.0,
        "box_height": 15.0,
        "grad_per_cm": 4.0,
    }

    settings = {}
    for name, default in defaults.items():
        match = re.search(
            rf"^\s*set\s+{re.escape(name)}\s+({NUMBER})",
            text,
            flags=re.MULTILINE,
        )
        settings[name] = float(match.group(1)) if match else default

    if settings["box_width"] <= 0 or settings["box_height"] <= 0:
        raise ValueError(f"{path}: box dimensions must be positive.")
    if settings["grad_per_cm"] <= 0:
        raise ValueError(f"{path}: grad_per_cm must be positive.")

    return settings


def image_pixel_to_sky(px, py, image_width, image_height, chart, ra_direction):
    """Convert a pixel in a PP3 image to RA/Dec using its chart settings."""
    # Angular coordinates in the chart plane, in degrees.
    x_image_deg = (px / image_width - 0.5) * chart["box_width"] * chart["grad_per_cm"]
    y_north_deg = (0.5 - py / image_height) * chart["box_height"] * chart["grad_per_cm"]

    # PP3's chart x-axis usually runs opposite to increasing RA.
    x_east = np.deg2rad(ra_direction * x_image_deg)
    y_north = np.deg2rad(y_north_deg)
    rho = np.hypot(x_east, y_north)

    ra0 = np.deg2rad(chart["center_rectascension"] * 15.0)  # PP3 RA is in hours
    dec0 = np.deg2rad(chart["center_declination"])

    if rho < 1e-12:
        return ra0, dec0

    c = rho
    dec = np.arcsin(
        np.cos(c) * np.sin(dec0)
        + (y_north * np.sin(c) * np.cos(dec0) / rho)
    )
    ra = ra0 + np.arctan2(
        x_east * np.sin(c),
        rho * np.cos(dec0) * np.cos(c)
        - y_north * np.sin(dec0) * np.sin(c),
    )
    return ra, dec


def sky_to_image_pixel(ra, dec, image_width, image_height, chart, ra_direction):
    """Project RA/Dec into a pixel location on another PP3 chart."""
    ra0 = np.deg2rad(chart["center_rectascension"] * 15.0)
    dec0 = np.deg2rad(chart["center_declination"])

    delta_ra = (ra - ra0 + np.pi) % (2 * np.pi) - np.pi
    cos_c = (
        np.sin(dec0) * np.sin(dec)
        + np.cos(dec0) * np.cos(dec) * np.cos(delta_ra)
    )
    c = np.arccos(np.clip(cos_c, -1.0, 1.0))

    if c < 1e-12:
        x_east = 0.0
        y_north = 0.0
    else:
        k = c / np.sin(c)
        x_east = k * np.cos(dec) * np.sin(delta_ra)
        y_north = k * (
            np.cos(dec0) * np.sin(dec)
            - np.sin(dec0) * np.cos(dec) * np.cos(delta_ra)
        )

    x_image_deg = ra_direction * np.rad2deg(x_east)
    y_north_deg = np.rad2deg(y_north)

    px = (
        0.5 + x_image_deg / (chart["box_width"] * chart["grad_per_cm"])
    ) * image_width
    py = (
        0.5 - y_north_deg / (chart["box_height"] * chart["grad_per_cm"])
    ) * image_height
    return px, py


def zoom_border_on_main(main_image, zoom_image, main_chart, zoom_chart, ra_direction):
    """Project the zoom image's four corners onto the main image."""
    zoom_height, zoom_width = zoom_image.shape[:2]
    main_height, main_width = main_image.shape[:2]

    # Image-edge corners, ordered clockwise from top-left.
    zoom_corners = [
        (0, 0),
        (zoom_width, 0),
        (zoom_width, zoom_height),
        (0, zoom_height),
    ]

    main_points = []
    for px, py in zoom_corners:
        ra, dec = image_pixel_to_sky(
            px, py, zoom_width, zoom_height, zoom_chart, ra_direction
        )
        main_px, main_py = sky_to_image_pixel(
            ra, dec, main_width, main_height, main_chart, ra_direction
        )
        main_points.append((main_px, main_py))

    return main_points


def generate_zoom_plot(
    main_img_path,
    zoom_img_path,
    output_path,
    main_pp3_path,
    zoom_pp3_path,
    inset_layout,
    ra_direction,
    dpi,
):
    main_image = mpimg.imread(main_img_path)
    zoom_image = mpimg.imread(zoom_img_path)
    main_chart = read_pp3(main_pp3_path)
    zoom_chart = read_pp3(zoom_pp3_path)

    main_height, main_width = main_image.shape[:2]

    main_ratio = main_chart["box_width"] / main_chart["box_height"]
    image_ratio = main_width / main_height
    if abs(main_ratio - image_ratio) / main_ratio > 0.02:
        warnings.warn(
            "The main PNG's aspect ratio differs from its PP3 chart dimensions. "
            "The image may include margins, be cropped, or be stretched; the "
            "calculated outline may not align correctly."
        )

    points = zoom_border_on_main(
        main_image, zoom_image, main_chart, zoom_chart, ra_direction
    )

    fig, ax = plt.subplots(figsize=(5.9, 5.9))
    ax.imshow(main_image)
    ax.axis("off")

    outline = Polygon(
        points,
        closed=True,
        fill=False,
        edgecolor="black",
        linewidth=0.8,
        linestyle="--",
    )
    ax.add_patch(outline)

    ax_inset = fig.add_axes(inset_layout)
    ax_inset.imshow(zoom_image)
    ax_inset.set_xticks([])
    ax_inset.set_yticks([])
    #ax_inset.set_title("Zoomed Detail", fontsize=10)

    for spine in ax_inset.spines.values():
        spine.set_color("black")
        spine.set_linewidth(1.0)

    # Connect the zoom frame's top-left and bottom-right corners to the inset.
    for main_point, inset_point in (
        (points[0], (0, 1)),
        (points[2], (1, 0)),
    ):
        connector = ConnectionPatch(
            xyA=main_point,
            coordsA=ax.transData,
            xyB=inset_point,
            coordsB=ax_inset.transAxes,
            linestyle="--",
            color="black",
            linewidth=0.6,
        )
        fig.add_artist(connector)

    plt.savefig(output_path, bbox_inches="tight", dpi=dpi)
    plt.close(fig)
    print(f"Saved composite plot to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a composite PP3 chart with an automatically positioned zoom outline."
    )
    parser.add_argument("--main-img", default="escorpio.png")
    parser.add_argument("--zoom-img", default="orion.png")
    parser.add_argument("--output", default="combined_zoom_graph.png")

    # By default, sidecar .pp3 files use the image names with a .pp3 extension.
    parser.add_argument(
        "--main-pp3",
        help="Main chart's PP3 source file. Defaults to the main image name with .pp3 extension.",
    )
    parser.add_argument(
        "--zoom-pp3",
        help="Zoom chart's PP3 source file. Defaults to the zoom image name with .pp3 extension.",
    )

    parser.add_argument(
        "--inset-layout",
        type=float,
        nargs=4,
        default=[0.6, 0.6, 0.35, 0.35],
        metavar=("LEFT", "BOTTOM", "WIDTH", "HEIGHT"),
    )
    parser.add_argument(
        "--ra-direction",
        type=int,
        choices=(-1, 1),
        default=-1,
        help="Use -1 for the usual sky-chart orientation; use 1 if the outline is mirrored.",
    )
    parser.add_argument("--dpi", type=int, default=600)
    args = parser.parse_args()

    main_img = Path(args.main_img)
    zoom_img = Path(args.zoom_img)

    main_pp3 = Path(args.main_pp3) if args.main_pp3 else main_img.with_suffix(".pp3")
    zoom_pp3 = Path(args.zoom_pp3) if args.zoom_pp3 else zoom_img.with_suffix(".pp3")

    generate_zoom_plot(
        main_img_path=main_img,
        zoom_img_path=zoom_img,
        output_path=args.output,
        main_pp3_path=main_pp3,
        zoom_pp3_path=zoom_pp3,
        inset_layout=args.inset_layout,
        ra_direction=args.ra_direction,
        dpi=args.dpi,
    )