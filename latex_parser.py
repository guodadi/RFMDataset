"""Backward-compatible entry point for the RFMDataset LaTeX parser."""

from rfmdataset.latex_parser import main, parse_header, parse_tex

__all__ = ["main", "parse_header", "parse_tex"]


if __name__ == "__main__":
    main()
