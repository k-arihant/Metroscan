"""
Visual Layout and Association Debug Visualizer.
Renders annotated debug images showing:
- Detected Label boxes (Blue)
- Detected Value boxes (Green)
- Detected Dot-Matrix regions (Yellow/Amber)
- Directed connection arrows from Label to Value (Cyan/Orange)
- Dotted/red connectors for uncertain associations (needs_recheck)
- Row and Column bounding regions
"""
from pathlib import Path
from typing import Optional, Dict, Any, List
import cv2
import numpy as np

import config
from src.extraction.layout_association import LayoutStructure


def draw_layout_debug_image(
    image: np.ndarray,
    layout: LayoutStructure,
    image_name: str = "debug_label",
    output_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Render visual debugging annotations on a copy of the input image and save to disk.
    """
    if image is None or image.size == 0:
        return None

    vis = image.copy()
    h_img, w_img = vis.shape[:2]

    # Overlay colors (BGR format)
    COLOR_LABEL = (255, 120, 0)      # Blue/Azure
    COLOR_VALUE = (0, 200, 50)       # Green
    COLOR_ARROW_VERIFIED = (255, 200, 0)  # Cyan/Sky
    COLOR_ARROW_RECHECK = (0, 0, 240)    # Red/Warning
    COLOR_COL_DIVIDER = (180, 180, 180)  # Gray
    COLOR_ROW_BAND = (240, 240, 240)

    # 1. Draw Column Dividers if columns detected
    if layout.columns and len(layout.columns) >= 2:
        lbl_col = layout.columns[0]
        val_col = layout.columns[1]
        # Midpoint divider between columns
        div_x = int((lbl_col["x_range"][1] + val_col["x_range"][0]) / 2.0)
        cv2.line(vis, (div_x, 0), (div_x, h_img), COLOR_COL_DIVIDER, 1, cv2.LINE_AA)
        cv2.putText(vis, "LABEL COL", (max(10, div_x - 120), 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 120, 120), 1, cv2.LINE_AA)
        cv2.putText(vis, "VALUE COL", (min(w_img - 130, div_x + 15), 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 120, 120), 1, cv2.LINE_AA)

    # 2. Draw Rows and Label/Value bounding boxes
    for r in layout.rows:
        # Subtle horizontal row guide line
        cy = int(r.center_y)
        cv2.line(vis, (0, cy), (w_img, cy), (230, 230, 230), 1, cv2.LINE_4)

        if r.label:
            l_box = r.label.bbox
            lx1, ly1 = int(l_box.x_min), int(l_box.y_min)
            lx2, ly2 = int(l_box.x_max), int(l_box.y_max)
            cv2.rectangle(vis, (lx1, ly1), (lx2, ly2), COLOR_LABEL, 2)
            # Label tag
            cv2.putText(
                vis,
                f"L:{r.label.field_name}",
                (lx1, max(15, ly1 - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                COLOR_LABEL,
                1,
                cv2.LINE_AA,
            )

        for v in r.values:
            v_box = v.bbox
            vx1, vy1 = int(v_box.x_min), int(v_box.y_min)
            vx2, vy2 = int(v_box.x_max), int(v_box.y_max)
            cv2.rectangle(vis, (vx1, vy1), (vx2, vy2), COLOR_VALUE, 2)

    # 3. Draw Label -> Value Association Arrows
    for pair in layout.assigned_pairs:
        l_bbox = pair.get("label_bbox", {})
        v_bbox = pair.get("value_bbox", {})
        if not l_bbox or not v_bbox:
            continue

        pt_start = (int(l_bbox["x_max"]), int((l_bbox["y_min"] + l_bbox["y_max"]) / 2.0))
        pt_end = (int(v_bbox["x_min"]), int((v_bbox["y_min"] + v_bbox["y_max"]) / 2.0))

        status = pair.get("status", "verified")
        arrow_color = COLOR_ARROW_VERIFIED if status == "verified" else COLOR_ARROW_RECHECK
        score = pair.get("score", 0.0)

        # Draw arrowed line
        cv2.arrowedLine(vis, pt_start, pt_end, arrow_color, 2, tipLength=0.08)

        # Draw score badge at midpoint
        mid_x = int((pt_start[0] + pt_end[0]) / 2.0)
        mid_y = int((pt_start[1] + pt_end[1]) / 2.0) - 6
        badge_text = f"score:{score:.0f}"
        cv2.putText(
            vis,
            badge_text,
            (mid_x, mid_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            arrow_color,
            1,
            cv2.LINE_AA,
        )

    # 4. Save annotated image
    out_dir = output_dir or config.DEBUG_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{Path(image_name).stem}_layout_debug.png"
    cv2.imwrite(str(out_path), vis)
    return out_path
