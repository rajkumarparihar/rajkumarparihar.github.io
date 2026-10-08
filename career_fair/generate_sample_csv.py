"""Generate a synthetic career_fair_1000.csv for local development and tests."""

import csv
import random
import sys
from pathlib import Path

MAJORS = ["CS", "EE", "ME", "Business", "Biology", "Math", "Economics"]


def generate(path: Path, n: int = 1000, seed: int = 42) -> None:
    rng = random.Random(seed)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Student_ID", "Name", "Major", "Est_Interaction_Time_Mins"])
        for i in range(1, n + 1):
            w.writerow(
                [f"S{i:04d}", f"Student {i}", rng.choice(MAJORS), rng.choice([3, 5, 5, 7, 8, 10, 12, 15])]
            )


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "career_fair_1000.csv"
    generate(target)
    print(f"Wrote {target}")
