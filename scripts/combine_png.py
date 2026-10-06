import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import ConnectionPatch, Rectangle

# Load the full graph and the zoomed-in crop images
img_full = mpimg.imread('escorpio.png')
img_zoom = mpimg.imread('orion.png')

# Create the main figure
fig, ax = plt.subplots(figsize=(8, 6))

# Display the full graph and capture the extent coordinates
# This ensures we know the true pixel/coordinate boundaries for drawing the box
h, w, _ = img_full.shape
ax.imshow(img_full)
ax.axis('off')  # Hide axis ticks if they are already baked into the PNG

# ---- CHANGE 1: Define where the zoom source is located on the full image ----
# Adjust these coordinates to match the exact location of the target area inside 'escorpio.png'
# Coordinates format: (x_start, y_start, width, height)
zoom_box_x = 200
zoom_box_y = 150
zoom_box_w = 100
zoom_box_h = 100

# Draw a dashed bounding box over the main image source area
rect = Rectangle((zoom_box_x, zoom_box_y), zoom_box_w, zoom_box_h, 
                 linewidth=1.5, edgecolor='black', facecolor='none', linestyle='--')
ax.add_patch(rect)


# Create an inset axes [left, bottom, width, height] in relative figure fractions
ax_inset = fig.add_axes([0.55, 0.55, 0.35, 0.35])

# Display the zoomed-in portion inside the inset
ax_inset.imshow(img_zoom)

# ---- CHANGE 2: Remove axis numbers/ticks from the inset ----
ax_inset.set_xticks([])
ax_inset.set_yticks([])
ax_inset.set_title('Zoomed Detail', fontsize=10)

# Add a distinctive border around the inset panel
for spine in ax_inset.spines.values():
    spine.set_color('black')
    spine.set_linewidth(2)


# ---- CHANGE 3: Create the zoom-in effect with dashed connector lines ----
# We connect the vertices of the source box (ax) to the corners of the inset box (ax_inset)
# Corner mapping coordinates: (0,0)=bottom-left, (1,0)=bottom-right, (0,1)=top-left, (1,1)=top-right

# Top-Left Connector
con1 = ConnectionPatch(xyA=(zoom_box_x, zoom_box_y), coordsA=ax.transData,
                       xyB=(0, 1), coordsB=ax_inset.transAxes,
                       linestyle="--", color="black", linewidth=1)
fig.add_artist(con1)

# Bottom-Right Connector
con2 = ConnectionPatch(xyA=(zoom_box_x + zoom_box_w, zoom_box_y + zoom_box_h), coordsA=ax.transData,
                       xyB=(1, 0), coordsB=ax_inset.transAxes,
                       linestyle="--", color="black", linewidth=1)
fig.add_artist(con2)

# Optional: Add the other two corners if your geometry needs all 4 corners connected
# Top-Right Connector
con3 = ConnectionPatch(xyA=(zoom_box_x + zoom_box_w, zoom_box_y), coordsA=ax.transData,
                       xyB=(1, 1), coordsB=ax_inset.transAxes,
                       linestyle="--", color="black", linewidth=1)
fig.add_artist(con3)

# Bottom-Left Connector
con4 = ConnectionPatch(xyA=(zoom_box_x, zoom_box_y + zoom_box_h), coordsA=ax.transData,
                       xyB=(0, 0), coordsB=ax_inset.transAxes,
                       linestyle="--", color="black", linewidth=1)
fig.add_artist(con4)


plt.savefig('combined_zoom_graph.png', bbox_inches='tight', dpi=600)
plt.show()
