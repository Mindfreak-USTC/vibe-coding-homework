from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import analyze_folder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze image quality and generate CSV, charts, and report.")
    parser.add_argument("--input", required=True, type=Path, help="Folder containing jpg/png/bmp images.")
    parser.add_argument("--output", default=Path("outputs"), type=Path, help="Output folder.")
    parser.add_argument("--min-width", default=64, type=int, help="Minimum acceptable image width.")
    parser.add_argument("--min-height", default=64, type=int, help="Minimum acceptable image height.")
    parser.add_argument("--dark-threshold", default=45.0, type=float, help="Brightness threshold for too_dark.")
    parser.add_argument("--bright-threshold", default=215.0, type=float, help="Brightness threshold for overexposed.")
    parser.add_argument("--blur-threshold", default=80.0, type=float, help="Sharpness threshold for blurry.")
    parser.add_argument("--noise-threshold", default=22.0, type=float, help="Noise threshold for high_noise.")
    parser.add_argument("--low-contrast-threshold", default=25.0, type=float, help="Contrast threshold for low_contrast.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = analyze_folder(
        args.input,
        args.output,
        min_width=args.min_width,
        min_height=args.min_height,
        dark_threshold=args.dark_threshold,
        bright_threshold=args.bright_threshold,
        blur_threshold=args.blur_threshold,
        noise_threshold=args.noise_threshold,
        low_contrast_threshold=args.low_contrast_threshold,
    )
    print(f"Total files: {summary.total_files}")
    print(f"Valid images: {summary.valid_images}")
    print(f"Skipped files: {summary.skipped_files}")
    print(f"Error files: {summary.error_files}")
    print(f"CSV: {summary.csv_path}")
    print(f"Report: {summary.report_path}")
    for chart_path in summary.chart_paths:
        print(f"Chart: {chart_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
