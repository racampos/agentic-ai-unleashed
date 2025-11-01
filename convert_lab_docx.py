#!/usr/bin/env python3
"""
Convert lab DOCX files to Markdown using Microsoft's markitdown.

Usage:
    python convert_lab_docx.py <input.docx> [output.md]

If output filename is not provided, it will be derived from input filename.
"""

import sys
import os
from pathlib import Path
from markitdown import MarkItDown


def convert_docx_to_markdown(input_path: str, output_path: str = None):
    """
    Convert a DOCX file to Markdown format.

    Args:
        input_path: Path to the input .docx file
        output_path: Optional path to the output .md file
    """
    input_file = Path(input_path)

    # Validate input file
    if not input_file.exists():
        print(f"❌ Error: Input file '{input_path}' not found")
        sys.exit(1)

    if input_file.suffix.lower() != '.docx':
        print(f"❌ Error: Input file must be a .docx file, got: {input_file.suffix}")
        sys.exit(1)

    # Determine output path
    if output_path is None:
        output_file = input_file.with_suffix('.md')
    else:
        output_file = Path(output_path)

    print(f"📄 Converting: {input_file}")
    print(f"📝 Output to: {output_file}")

    try:
        # Initialize MarkItDown converter
        md = MarkItDown()

        # Convert the document
        result = md.convert(str(input_file))

        # Write the markdown output
        output_file.write_text(result.text_content, encoding='utf-8')

        print(f"✅ Successfully converted!")
        print(f"📊 Output size: {len(result.text_content)} characters")

    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("Example:")
        print("  python convert_lab_docx.py data/labs/configure-initial-switch-settings.docx")
        print("  python convert_lab_docx.py input.docx output.md")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    convert_docx_to_markdown(input_path, output_path)


if __name__ == "__main__":
    main()
