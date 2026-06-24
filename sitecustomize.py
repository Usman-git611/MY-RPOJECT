import sys
from pathlib import Path


vendor_path = Path(__file__).resolve().parent / ".vendor"
if vendor_path.exists():
    sys.path.insert(0, str(vendor_path))
