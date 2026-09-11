"""
LEGACY / DUPLICATE SCRIPT
-------------------------
This root-level script has been superseded by the structured debug utility:
    python debug/select_region.py <image_path>
"""
import cv2

# Load image
image = cv2.imread("images/t4.jpeg")

# Let user select a region with the mouse
roi = cv2.selectROI(
    "Select Region",
    image,
    fromCenter=False,
    showCrosshair=True
)

x, y, w, h = roi

# Close selection window
cv2.destroyAllWindows()

# Crop selected region
cropped = image[y:y+h, x:x+w]

# Resize
cropped = cv2.resize(
    cropped,
    None,
    fx=3,
    fy=3,
    interpolation=cv2.INTER_CUBIC
)

# Save
cv2.imwrite("images/selected_region.jpg", cropped)

print("Selected region saved!")