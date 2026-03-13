# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "fairchem-core",
# ]
#
# [tool.uv.sources]
# fairchem-core = { git = "https://github.com/facebookresearch/fairchem.git", subdirectory = "packages/fairchem-core", rev = "fairchem_core-2.0.0" }
# ///
"""
One-pass exploration of the OMol25 4M ASE-DB.

Answers:
  1. What are the data_id values for each domain, and how are they distributed?
  2. Are all optimization steps indexed, or only final geometries?
  3. What granularity makes sense for a `subsampling` tag?
  4. How available are nbo_charges across the dataset?

Usage:
    uv run scripts/explore_ase_db.py --src path/to/train_4M/

Output: prints a report to stdout and writes omol-notes/ase-db-exploration.md
"""

import argparse
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from fairchem.core.datasets import AseDBDataset


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True, help="Path to train_4M/ directory")
    p.add_argument(
        "--limit", type=int, default=None, help="Cap iterations (for quick testing)"
    )
    return p.parse_args()


def top_level_dir(source: str) -> str:
    """First path component of atoms.info['source']."""
    return source.split("/")[0]


def step_number(source: str) -> int | None:
    """Return the step number if the path contains /stepN/, else None."""
    m = re.search(r"/step(\d+)/", source)
    return int(m.group(1)) if m else None


def subsampling_tag(source: str) -> str:
    """
    Candidate subsampling tag. Strategy: use the top-level directory,
    except for omol/ paths where we use the second component (metal_organics,
    electrolytes, solvated_protein, etc.) to distinguish internal batches.
    """
    parts = source.split("/")
    if parts[0] == "omol" and len(parts) > 1:
        return f"omol/{parts[1]}"
    return parts[0]


def main():
    args = parse_args()

    dataset = AseDBDataset({"src": args.src})
    total = len(dataset)
    limit = args.limit or total
    print(f"Dataset size: {total:,}  (iterating {limit:,})")

    # Counters
    data_id_counts = Counter()
    top_dir_to_data_ids = defaultdict(set)  # top-level dir → set of data_id values seen
    subsampling_counts = Counter()
    nbo_present = 0
    nbo_absent = 0

    # Step analysis: track per-(parent_path) → set of step numbers seen
    # parent_path = source with /stepN/filename stripped
    step_parents = defaultdict(set)  # parent → {step numbers}
    has_steps_total = 0

    for idx in range(limit):
        atoms = dataset.get_atoms(idx)
        info = atoms.info
        source = info.get("source", "")
        data_id = info.get("data_id", "MISSING")

        data_id_counts[data_id] += 1
        top_dir_to_data_ids[top_level_dir(source)].add(data_id)
        subsampling_counts[subsampling_tag(source)] += 1

        # NBO availability
        nbo = info.get("nbo_charges")
        if nbo is not None and len(nbo) > 0:
            nbo_present += 1
        else:
            nbo_absent += 1

        # Step tracking
        step = step_number(source)
        if step is not None:
            has_steps_total += 1
            # Parent = everything before /stepN
            parent = re.sub(r"/step\d+/.*$", "", source)
            step_parents[parent].add(step)

        if (idx + 1) % 100_000 == 0:
            print(f"  {idx+1:,} / {limit:,} ...")

    # --- Report ---
    lines = []
    lines.append("# ASE-DB Exploration Results\n")
    lines.append(f"*{limit:,} of {total:,} entries scanned*\n")

    # 1. data_id values
    lines.append("## 1. `data_id` Values\n")
    lines.append("| data_id | count | % |\n|---|---|---|")
    for did, count in data_id_counts.most_common():
        lines.append(f"| `{did}` | {count:,} | {100*count/limit:.1f}% |")

    lines.append("\n### Top-level directory → data_id mapping\n")
    lines.append("| top-level dir | data_id(s) |\n|---|---|")
    for top_dir, dids in sorted(top_dir_to_data_ids.items()):
        lines.append(f"| `{top_dir}` | {', '.join(f'`{d}`' for d in sorted(dids))} |")

    # 2. Optimization steps
    lines.append("\n## 2. Optimization Steps\n")
    n_parents = len(step_parents)
    lines.append(f"- {has_steps_total:,} entries have a `/stepN/` path component")
    lines.append(f"- {n_parents:,} unique parent paths contain step entries")
    if n_parents > 0:
        step_set_sizes = Counter(len(v) for v in step_parents.values())
        lines.append(f"- Steps-per-parent distribution:")
        lines.append("\n| steps per parent | # parents |\n|---|---|")
        for n_steps, n_parents_with in sorted(step_set_sizes.items()):
            lines.append(f"| {n_steps} | {n_parents_with:,} |")

        # Show a few examples
        lines.append("\n**Sample parents and their step sets:**")
        for parent, steps in list(step_parents.items())[:10]:
            lines.append(f"- `{parent}`: steps {sorted(steps)}")

    # 3. Subsampling taxonomy
    lines.append("\n## 3. Subsampling Tag Candidates\n")
    lines.append("| subsampling tag | count | % |\n|---|---|---|")
    for tag, count in subsampling_counts.most_common():
        lines.append(f"| `{tag}` | {count:,} | {100*count/limit:.1f}% |")

    # 4. NBO availability
    lines.append("\n## 4. NBO Charge Availability\n")
    lines.append(f"- Present: {nbo_present:,} ({100*nbo_present/limit:.1f}%)")
    lines.append(f"- Absent:  {nbo_absent:,} ({100*nbo_absent/limit:.1f}%)")

    # NBO availability by data_id
    lines.append("\n(Run with full dataset for per-domain NBO breakdown if needed)")

    report = "\n".join(lines)
    print("\n" + report)

    out_path = Path(__file__).parent.parent / "omol-notes" / "ase-db-exploration.md"
    out_path.write_text(report)
    print(f"\nWrote report to {out_path}")


if __name__ == "__main__":
    main()
