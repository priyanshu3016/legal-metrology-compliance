#!/usr/bin/env python3
"""
CLI Tool for Legal Metrology Packaged Commodities Compliance AI Engine.
Usage:
    Single-image mode:
        python analyze.py path/to/image.jpg [--demo]
    Multi-image mode:
        python analyze.py --front path/to/front.jpg --back path/to/back.jpg [--side path/to/side.jpg] [--demo]
"""

import sys
import json
import argparse
from analyzer import analyze_image, analyze_multi_image


def main():
    parser = argparse.ArgumentParser(
        description="Analyze packaged commodity label image(s) for mandatory Legal Metrology declarations."
    )
    parser.add_argument(
        "image_path",
        nargs="?",
        default=None,
        help="Single image path (legacy mode)"
    )
    parser.add_argument(
        "--front",
        type=str,
        default=None,
        help="Front image path (multi-image mode)"
    )
    parser.add_argument(
        "--back",
        type=str,
        default=None,
        help="Back image path (multi-image mode)"
    )
    parser.add_argument(
        "--side",
        type=str,
        default=None,
        help="Side image path (optional, multi-image mode)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        default=False,
        help="Enable demo mode for pre-verified presentation data"
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation (default: 2)"
    )

    args = parser.parse_args()

    if args.front and args.back:
        result = analyze_multi_image(
            front_image_path=args.front,
            back_image_path=args.back,
            side_image_path=args.side,
            demo_mode=args.demo
        )
    elif args.image_path:
        result = analyze_image(args.image_path, demo_mode=args.demo)
    else:
        parser.error("Provide either a positional image path, or --front and --back")

    print(json.dumps(result, indent=args.indent))

    if not result.get("success", False):
        sys.exit(1)


if __name__ == "__main__":
    main()

