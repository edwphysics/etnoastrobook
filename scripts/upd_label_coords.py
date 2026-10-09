import sys
import re
import math

def calculate_top_left_coords(pp3_filename, margin_cm=0.8):
    # Default values in case they aren't explicitly set in the file
    ra_center = None
    dec_center = None
    box_width = None
    box_height = None
    grad_per_cm = None
    text_line_found = None

    # Regex patterns to parse pp3 commands
    ra_pattern = re.compile(r'^\s*set\s+center_rectascension\s+([\d\.-]+)', re.IGNORECASE)
    dec_pattern = re.compile(r'^\s*set\s+center_declination\s+([\d\.-]+)', re.IGNORECASE)
    width_pattern = re.compile(r'^\s*set\s+box_width\s+([\d\.-]+)', re.IGNORECASE)
    height_pattern = re.compile(r'^\s*set\s+box_height\s+([\d\.-]+)', re.IGNORECASE)
    grad_pattern = re.compile(r'^\s*set\s+grad_per_cm\s+([\d\.-]+)', re.IGNORECASE)
    text_pattern = re.compile(r'^\s*text\s+(".+?")\s+at\s+[\d\.-]+\s+[\d\.-]+(.*)', re.IGNORECASE)

    with open(pp3_filename, 'r', encoding='utf-8') as f:
        for line in f:
            ra_match = ra_pattern.match(line)
            if ra_match: ra_center = float(ra_match.group(1))

            dec_match = dec_pattern.match(line)
            if dec_match: dec_center = float(dec_match.group(1))

            width_match = width_pattern.match(line)
            if width_match: box_width = float(width_match.group(1))

            height_match = height_pattern.match(line)
            if height_match: box_height = float(height_match.group(1))

            grad_match = grad_pattern.match(line)
            if grad_match: grad_per_cm = float(grad_match.group(1))

            text_match = text_pattern.match(line)
            if text_match:
                text_content = text_match.group(1)
                remainder = text_match.group(2)
                text_line_found = (text_content, remainder)

    # Check that all necessary parameters were found
    params = {'center_rectascension': ra_center, 'center_declination': dec_center, 
              'box_width': box_width, 'box_height': box_height, 'grad_per_cm': grad_per_cm}
    missing = [k for k, v in params.items() if v is None]
    if missing:
        raise ValueError(f"Could not find the following parameter(s) in {pp3_filename}: {', '.join(missing)}")

    # Calculate offsets with padding margin
    half_height_deg = (box_height / 2.0 - margin_cm) * grad_per_cm
    half_width_deg = (box_width / 2.0 - margin_cm) * grad_per_cm

    # Top Declination
    dec_top = dec_center + half_height_deg

    # Left Right Ascension
    # Note: In celestial coordinates, RA increases toward the EAST (left side of standard sky maps)
    ra_left = ra_center + (half_width_deg / (15.0 * math.cos(math.radians(dec_center))))

    # Output result
    print("\n--- Calculated Coordinates ---")
    print(f"Top-Left Target RA  : {ra_left:.4f} hours")
    print(f"Top-Left Target Dec : {dec_top:.4f} degrees\n")

    if text_line_found:
        text_str, rest = text_line_found
        updated_line = f"text {text_str} at {ra_left:.4f} {dec_top:.4f}{rest}"
        print("--- Updated pp3 Line ---")
        print(updated_line)
    else:
        print("--- Generated pp3 Line ---")
        print(f'text "\\Large\\bfseries Title" at {ra_left:.4f} {dec_top:.4f} color 0 0 0 ;')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_pp3_text.py <path_to_pp3_file>")
    else:
        calculate_top_left_coords(sys.argv[1])