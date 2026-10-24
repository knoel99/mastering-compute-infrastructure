import os
import sys

# MUTANT_DIR lets mutants.py point the tests at a mutated copy of exporter.py
sys.path.insert(0, os.environ.get("MUTANT_DIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
