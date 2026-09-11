"""
Food/Product Label Compliance OCR System - Main CLI Entrypoint.
Executes the modular OCR pipeline on single images, directories, or runs the benchmark harness.
"""
import argparse
import json
import sys
from pathlib import Path
import config
from src.pipeline import LabelCompliancePipeline, PaddleOCRPipeline
from tests.benchmark import run_benchmark


def format_cli_output(result: dict) -> None:
    """Format and display OCR result and Legal Metrology Rule 7 compliance cleanly."""
    pkg_id = result.get("package_id", "Unknown")
    img_name = result.get("image", "Unknown")
    proc = result.get("processing", {})
    status = proc.get("ocr_status", result.get("ocr_status", "N/A")).upper()

    print("\n==================================================")
    print(f"OCR RESULT: {img_name} ({pkg_id})")
    print(f"Status: {status}")
    print("==================================================")

    imgs = result.get("images", [])
    if imgs:
        img_meta = imgs[0]
        q = img_meta.get("image_quality", {})
        cal = img_meta.get("calibration", {})
        pdp = img_meta.get("principal_display_panel", {})
        w = img_meta.get("width")
        h = img_meta.get("height")
        print(f"Dimensions : {w}x{h} | Quality Score: {q.get('quality_score', 0):.2f}")
        cal_str = f"Available ({cal.get('pixels_per_mm')} px/mm)" if cal.get("available") else "Not Provided"
        print(f"Calibration: {cal_str}")
        pdp_str = f"{pdp.get('area_cm2')} cm²" if pdp.get("detected") else "Not Provided"
        print(f"PDP Area   : {pdp_str}")

    print("\n--- EXTRACTED COMPLIANCE FIELDS ---")
    ext_fields = result.get("extracted_fields", {})
    if ext_fields:
        for f_name, f_data in ext_fields.items():
            if f_data is None:
                print(f"  {f_name:22} : <Not Detected / Uncertain> [  --  ]")
            elif isinstance(f_data, list):
                val_str = ", ".join(item.get("value", "") for item in f_data if isinstance(item, dict))
                src_str = f"[src: {f_data[0].get('source_detection_id', 'N/A')}]" if f_data else ""
                print(f"  {f_name:22} : {val_str:30} {src_str}")
            elif isinstance(f_data, dict):
                val_str = str(f_data.get("value", ""))
                if "unit" in f_data and f_data["unit"]:
                    val_str += f" {f_data['unit']}"
                conf = f_data.get("confidence", 0.0)
                src_id = f_data.get("source_detection_id", "N/A")
                print(f"  {f_name:22} : {val_str:30} [{conf * 100:.0f}%] (src: {src_id})")
            else:
                print(f"  {f_name:22} : {str(f_data):30}")
    else:
        fields = result.get("fields", {})
        confs = result.get("confidence", {})
        for field, val in fields.items():
            conf = confs.get(field, 0.0)
            conf_str = f"[{conf * 100:.0f}%]" if val is not None else "[  --  ]"
            val_display = str(val) if val is not None else "<Not Detected / Uncertain>"
            print(f"  {field:22} : {val_display:30} {conf_str}")

    print("\n--- RULE 7 COMPLIANCE SUMMARY ---")
    comp = result.get("compliance_summary", {})
    r7 = comp.get("rule_7", {})
    print(f"  Status                  : {r7.get('status', 'UNABLE_TO_VERIFY')}")
    print(f"  Detections Evaluated    : {r7.get('detections_evaluated', 0)}")
    print(f"  Detections Compliant    : {r7.get('detections_compliant', 0)}")
    print(f"  Detections Non-Compliant: {r7.get('detections_non_compliant', 0)}")
    print(f"  Unable to Verify        : {r7.get('detections_unable_to_verify', 0)}")
    print("==================================================\n")


def main():
    parser = argparse.ArgumentParser(
        description="Food/Product Label Compliance OCR Pipeline"
    )
    parser.add_argument("input", nargs="?", help="Path to an image file or directory")
    parser.add_argument("--dir", help="Process all images in the specified directory")
    parser.add_argument("--save-output", default="output", help="Directory path to save JSON results (default: output)")
    parser.add_argument("--compliance", action="store_true", help="Run full Legal Metrology Rule 7 compliance analysis")
    parser.add_argument("--benchmark", action="store_true", help="Run automated accuracy benchmark suite")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of images for benchmark (default: 5)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON to stdout")
    parser.add_argument("--no-orient", action="store_true", help="Disable automatic orientation and deskewing")
    parser.add_argument("--visualize", action="store_true", help="Generate annotated visual layout debugging images in debug/")
    parser.add_argument("--calibration", type=float, help="Physical scale calibration in pixels per mm")
    parser.add_argument("--pdp-area", type=float, help="Principal Display Panel area in cm²")
    parser.add_argument("--package-id", type=str, help="Optional package ID identifier")
    parser.add_argument("--blown-moulded", action="store_true", help="Package is blown, formed, or moulded container")

    args = parser.parse_args()

    if args.visualize:
        config.DEBUG_VISUALIZATION_ENABLED = True
        config.VISUALIZE = True

    if args.benchmark:
        run_benchmark(limit=args.limit)
        return

    target_paths = []
    if args.dir:
        dir_path = Path(args.dir)
        if not dir_path.is_dir():
            print(f"Error: {dir_path} is not a valid directory.")
            sys.exit(1)
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp"]:
            target_paths.extend(sorted(dir_path.glob(ext)))
    elif args.input:
        in_path = Path(args.input)
        if in_path.is_dir():
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp"]:
                target_paths.extend(sorted(in_path.glob(ext)))
        elif in_path.is_file():
            target_paths.append(in_path)
        else:
            print(f"Error: File or directory not found: {in_path}")
            sys.exit(1)
    else:
        # Default: process sample test image
        default_img = Path("images/test.jpeg")
        if default_img.exists():
            target_paths.append(default_img)
        else:
            parser.print_help()
            sys.exit(0)

    output_dir = Path(args.save_output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # Mode A: Full Legal Metrology Compliance Pipeline (if requested)
    # -------------------------------------------------------------
    if args.compliance:
        calibration_dict = None
        if args.calibration is not None and args.calibration > 0:
            calibration_dict = {
                "pixels_per_mm": float(args.calibration),
                "source": "cli_argument",
                "confidence": 0.99,
            }

        pdp_dict = None
        if args.pdp_area is not None and args.pdp_area > 0:
            pdp_dict = {
                "area_cm2": float(args.pdp_area),
                "measurement_source": "cli_argument",
                "confidence": 0.99,
            }

        pipeline = LabelCompliancePipeline()
        total_processed = 0
        total_json = 0

        for img_path in target_paths:
            total_processed += 1
            try:
                result = pipeline.process_image(
                    str(img_path),
                    auto_orient=not args.no_orient,
                    calibration=calibration_dict,
                    pdp=pdp_dict,
                    package_id=args.package_id,
                    blown_formed_moulded=args.blown_moulded,
                )

                if args.json:
                    print(json.dumps(result, indent=2))
                else:
                    format_cli_output(result)

                out_file = output_dir / f"{img_path.stem}_ocr.json"
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                total_json += 1
                print(f"Saved result to: {out_file}")

            except Exception as e:
                print(f"Error processing {img_path}: {e}")
        return

    # -------------------------------------------------------------
    # Mode B: Standard Raw PaddleOCR Output Pipeline (Primary Default)
    # -------------------------------------------------------------
    paddle_pipeline = PaddleOCRPipeline()
    total_processed = 0
    total_json = 0
    total_detections = 0

    for img_path in target_paths:
        total_processed += 1
        print(f"\nProcessing: {img_path}")
        try:
            result_json, saved_path = paddle_pipeline.process_image(
                img_path,
                output_dir=output_dir,
                package_id=args.package_id,
            )
            det_count = len(result_json.get("detections", []))
            total_detections += det_count
            total_json += 1

            print(f"\nPaddleOCR detections: {det_count}")
            print(f"\nJSON saved:\n{saved_path}")

            if args.json:
                print(json.dumps(result_json, indent=2))

        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    if len(target_paths) > 1:
        print("\n==================================================")
        print("BATCH SUMMARY")
        print("==================================================")
        print(f"Images processed     : {total_processed}")
        print(f"JSON files generated : {total_json}")
        print(f"Total OCR detections : {total_detections}")
        print(f"Output directory     : {output_dir}")
        print("==================================================\n")


if __name__ == "__main__":
    main()