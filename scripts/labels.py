import math
import re
import shutil
import sys
from pathlib import Path


def calculate_top_left_coords(pp3_filename, margin_cm=0.8):
    path = Path(pp3_filename)
    content = path.read_text(encoding="utf-8")

    def read_setting(name):
        match = re.search(
            rf"^\s*set\s+{re.escape(name)}\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+))",
            content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if not match:
            raise ValueError(f"Missing PP3 setting: set {name} ...")
        return float(match.group(1))

    ra_center = read_setting("center_rectascension")
    dec_center = read_setting("center_declination")
    box_width = read_setting("box_width")
    box_height = read_setting("box_height")
    grad_per_cm = read_setting("grad_per_cm")

    half_width_deg = (box_width / 2.0 - margin_cm) * grad_per_cm
    half_height_deg = (box_height / 2.0 - margin_cm) * grad_per_cm

    if half_width_deg <= 0 or half_height_deg <= 0:
        raise ValueError("The margin is too large for this chart.")

    dec_top = dec_center + half_height_deg
    dec_bottom = dec_center - half_height_deg

    cos_dec = math.cos(math.radians(dec_center))
    if abs(cos_dec) < 1e-8:
        raise ValueError("Cannot calculate the RA offset near a celestial pole.")

    ra_offset = half_width_deg / (15.0 * cos_dec)
    ra_left = (ra_center + ra_offset) % 24.0
    ra_tick_start = (math.floor((ra_left % 24.0) * 2) / 2) % 24.0

    # Preserve the existing constellation label and its styling.
    title_pattern = re.compile(
        r'(?m)^\s*text\s+("(?:\\.|[^"\\])*")\s+at\s+'
        r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s+'
        r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)'
        r'(?P<rest>[^\n]*color[^\n]*;)\s*$'
    )
    title_match = title_pattern.search(content)

    if title_match:
        title_text = title_match.group(1)

        # Ensure every LaTeX command has exactly two backslashes in the PP3 file.
        title_text = re.sub(
            r"\\+([A-Za-z]+)\b",
            lambda match: chr(92) * 2 + match.group(1),
            title_text,
        )

        title_rest = title_match.group("rest").rstrip()
        title_line = (
            f"text {title_text} at {ra_left:.4f} {dec_top:.4f}"
            f"{title_rest}"
        )
    else:
        title_line = (
            'text "\\\\LARGE\\\\bfseries Title" '
            f'at {ra_left:.4f} {dec_top:.4f} color 0 0 0 ;'
        )

    # Python turns each \\\\ into two literal backslashes in the PP3 file.
    ra_marker = (
        'text "$#3{\\\\rm h}#4{\\\\rm m}$" at '
        f"{ra_tick_start:.4f} {dec_bottom:.4f} along declination\n"
        "    tics rectascension 0.5 towards S ;"
    )

    dec_marker = (
        'text "$#5^\\\\circ$" at '
        f"{ra_left:.4f} {dec_center:.4f} along declination\n"
        "    tics declination 5 towards W ;"
    )

    objects_section = f"""objects_and_labels

{ra_marker}

{dec_marker}

{title_line}
"""

    section_pattern = re.compile(
        r"(?ms)^[ \t]*objects_and_labels\b.*\Z"
    )
    match = section_pattern.search(content)

    if not match:
        raise ValueError("Could not find the objects_and_labels section.")

    updated_content = (
        content[:match.start()].rstrip()
        + "\n\n"
        + objects_section.rstrip()
        + "\n"
    )

    backup_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup_path)
    path.write_text(updated_content, encoding="utf-8")

    print(f"Updated file: {path}")
    print(f"Backup saved: {backup_path}")
    print("\n--- Updated objects_and_labels section ---")
    print(objects_section)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_pp3_text.py <path_to_pp3_file> [margin_cm]")
        raise SystemExit(1)

    filename = sys.argv[1]
    margin = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
    calculate_top_left_coords(filename, margin)