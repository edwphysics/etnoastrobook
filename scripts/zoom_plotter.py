#!/usr/bin/env python3
import argparse
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import ConnectionPatch, Rectangle

def generate_zoom_plot(img_full_path, img_zoom_path, output_path, zoom_box, inset_layout):
    """
    Combines a macro graph and a zoom inset snippet into a clean 15x15 cm figure layout.
    """
    # 1. Load the full graph and the zoomed-in crop images
    img_full = mpimg.imread(img_full_path)
    img_zoom = mpimg.imread(img_zoom_path)

    # 2. Create the main figure 15x15 cm (5.9 x 5.9 inches)
    fig, ax = plt.subplots(figsize=(5.9, 5.9))

    # Display the full graph
    ax.imshow(img_full)
    ax.axis('off')  # Hide axis ticks if they are already baked into the PNG

    # 3. Unpack your zoom target region configurations
    zoom_box_x, zoom_box_y, zoom_box_w, zoom_box_h = zoom_box

    # Draw a dashed bounding box over the main image source area
    rect = Rectangle((zoom_box_x, zoom_box_y), zoom_box_w, zoom_box_h, 
                     linewidth=0.5, edgecolor='black', facecolor='none', linestyle='--')
    ax.add_patch(rect)

    # 4. Create an inset axes [left, bottom, width, height] in relative figure fractions
    ax_inset = fig.add_axes(inset_layout)

    # Display the zoomed-in portion inside the inset
    ax_inset.imshow(img_zoom)

    # Remove axis numbers/ticks from the inset
    ax_inset.set_xticks([])
    ax_inset.set_yticks([])
    ax_inset.set_title('Zoomed Detail', fontsize=10)

    # Add a distinctive border around the inset panel
    for spine in ax_inset.spines.values():
        spine.set_color('black')
        spine.set_linewidth(1.5)

    # 5. Create the zoom-in effect with dashed connector lines
    # Top-Left Connector
    con1 = ConnectionPatch(xyA=(zoom_box_x, zoom_box_y), coordsA=ax.transData,
                           xyB=(0, 1), coordsB=ax_inset.transAxes,
                           linestyle="--", color="black", linewidth=0.5)
    fig.add_artist(con1)

    # Bottom-Right Connector
    con2 = ConnectionPatch(xyA=(zoom_box_x + zoom_box_w, zoom_box_y + zoom_box_h), coordsA=ax.transData,
                           xyB=(1, 0), coordsB=ax_inset.transAxes,
                           linestyle="--", color="black", linewidth=0.5)
    fig.add_artist(con2)

    # Save the plot with your target high resolution
    plt.savefig(output_path, bbox_inches='tight', dpi=600)
    print(f"Success! Figure exported cleanly to: {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="CLI Utility to overlay a macro graph with a zoom source box and an inset graph.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Image Input and Output parameters
    parser.add_argument('--main-img', type=str, default='escorpio.png',
                        help='Path to the full main graph background PNG.')
    parser.add_argument('--zoom-img', type=str, default='orion.png',
                        help='Path to the inner detailed zoom region PNG.')
    parser.add_argument('--output', type=str, default='combined_zoom_graph.png',
                        help='Filename/Path destination for the generated high-res figure.')

    # Zoom target tracking box: (x_start, y_start, width, height)
    parser.add_argument('--zoom-box', type=float, nargs=4, default=[800, 1800, 1000, 1000],
                        metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                        help='Four coordinates identifying the focus boundary box over the main image context.')

    # Screen fraction position viewport for the Inset frame: (left, bottom, width, height)
    parser.add_argument('--inset-layout', type=float, nargs=4, default=[0.6, 0.6, 0.35, 0.35],
                        metavar=('LEFT', 'BOTTOM', 'WIDTH', 'HEIGHT'),
                        help='Relative canvas boundary placement coordinates for rendering the secondary viewport.')

    args = parser.parse_args()

    # Trigger visualization engine pipeline
    generate_zoom_plot(
        img_full_path=args.main_img,
        img_zoom_path=args.zoom_img,
        output_path=args.output,
        zoom_box=args.zoom_box,
        inset_layout=args.inset_layout
    )
