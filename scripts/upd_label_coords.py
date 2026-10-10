import math
import re
import sys


def calculate_top_left_coords(pp3_filename, margin_cm=None):
    settings = {}
    text_line_found = None

    number = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"

    setting_patterns = {
        "center_rectascension": re.compile(
            rf"^\s*set\s+center_rectascension\s+({number})", re.IGNORECASE
        ),
        "center_declination": re.compile(
            rf"^\s*set\s+center_declination\s+({number})", re.IGNORECASE
        ),
        "box_width": re.compile(
            rf"^\s*set\s+box_width\s+({number})", re.IGNORECASE
        ),
        "box_height": re.compile(
            rf"^\s*set\s+box_height\s+({number})", re.IGNORECASE
        ),
        "grad_per_cm": re.compile(
            rf"^\s*set\s+grad_per_cm\s+({number})", re.IGNORECASE
        ),
    }

    text_pattern = re.compile(
        rf'^\s*text\s+("(?:\\.|[^"\\])*")\s+at\s+'
        rf"{number}\s+{number}(.*)",
        re.IGNORECASE,
    )

    with open(pp3_filename, "r", encoding="utf-8") as file:
        for line in file:
            for name, pattern in setting_patterns.items():
                match = pattern.match(line)
                if match:
                    settings[name] = float(match.group(1))

            match = text_pattern.match(line)
            if match:
                text_line_found = (match.group(1), match.group(2))

    required = (
        "center_rectascension",
        "center_declination",
        "box_width",
        "box_height",
        "grad_per_cm",
    )
    missing = [name for name in required if name not in settings]
    if missing:
        raise ValueError(
            f"Could not find these settings in {pp3_filename}: "
            + ", ".join(missing)
        )

    ra_center = settings["center_rectascension"]
    dec_center = settings["center_declination"]
    box_width = settings["box_width"]
    box_height = settings["box_height"]
    grad_per_cm = settings["grad_per_cm"]

    if text_line_found:
        text_str, remainder = text_line_found
        is_huge = re.search(r"\\+Huge\b", text_str, re.IGNORECASE) is not None
    else:
        text_str = r'"\\Huge\\bfseries Title"'
        remainder = " color 0 0 0 ;"
        is_huge = True

    # Use a larger inset for Huge labels; pass a margin to override it.
    if margin_cm is None:
        margin_cm = 1.3 if is_huge else 0.8

    half_height_deg = (box_height / 2.0 - margin_cm) * grad_per_cm
    half_width_deg = (box_width / 2.0 - margin_cm) * grad_per_cm

    if half_height_deg <= 0 or half_width_deg <= 0:
        raise ValueError("The margin is too large for this chart.")

    dec_top = dec_center + half_height_deg

    cos_dec = math.cos(math.radians(dec_center))
    if abs(cos_dec) < 1e-8:
        raise ValueError("Cannot calculate the RA offset near a celestial pole.")

    ra_left = (
        ra_center
        + half_width_deg / (15.0 * cos_dec)
    ) % 24.0

    updated_line = f"text {text_str} at {ra_left:.4f} {dec_top:.4f}{remainder}"

    print(f"\nMargin used: {margin_cm:.2f} cm")
    print(f"Top-left target RA : {ra_left:.4f} hours")
    print(f"Top-left target Dec: {dec_top:.4f} degrees")
    print("\n--- Updated PP3 line ---")
    print(updated_line)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python update_pp3_text.py "
            "<path_to_pp3_file> [margin_cm]"
        )
        raise SystemExit(1)

    filename = sys.argv[1]
    margin = float(sys.argv[2]) if len(sys.argv) > 2 else None
    calculate_top_left_coords(filename, margin)