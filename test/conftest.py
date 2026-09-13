import sys
from pathlib import Path

# test/support を test/pr2, test/pr3 の各テストから import できるようにする。
sys.path.insert(0, str(Path(__file__).resolve().parent / "support"))
