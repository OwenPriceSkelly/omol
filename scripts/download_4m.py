# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx",
#     "rich",
# ]
# ///
"""
Download and extract the OMol25 4M ASE-DB split from HuggingFace.

Usage:
    uv run scripts/download_4m.py [--dest path/to/data/]

Default destination: data/train_4M/ (gitignored)
"""

import argparse
import tarfile
from pathlib import Path

import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

URL = "https://dl.fbaipublicfiles.com/opencatalystproject/data/omol/250514/train_4M.tar.gz"
DEFAULT_DEST = Path(__file__).parent.parent / "data"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DEST,
        help=f"Directory to extract into (default: {DEFAULT_DEST})",
    )
    p.add_argument(
        "--keep-tar",
        action="store_true",
        help="Keep the .tar.gz after extraction",
    )
    return p.parse_args()


def download(url: str, dest_file: Path) -> None:
    dest_file.parent.mkdir(parents=True, exist_ok=True)

    with Progress(
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        with httpx.stream("GET", url, follow_redirects=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            task = progress.add_task("Downloading train_4M.tar.gz", total=total or None)

            with dest_file.open("wb") as f:
                for chunk in r.iter_bytes(chunk_size=1024 * 1024):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))


def extract(tar_file: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"Extracting to {dest_dir} ...")
    with tarfile.open(tar_file, "r:gz") as tf:
        tf.extractall(dest_dir)
    print("Done.")


def main():
    args = parse_args()

    tar_file = args.dest / "train_4M.tar.gz"
    extract_dir = args.dest

    if (extract_dir / "train_4M").exists():
        print(f"train_4M/ already exists at {extract_dir / 'train_4M'}, nothing to do.")
        return

    if not tar_file.exists():
        print(f"Downloading to {tar_file}")
        download(URL, tar_file)
    else:
        print(f"Found existing {tar_file}, skipping download.")

    extract(tar_file, extract_dir)

    if not args.keep_tar:
        tar_file.unlink()
        print(f"Removed {tar_file}")

    print(f"\nDataset ready at: {extract_dir / 'train_4M'}")
    print(f"Run exploration with:")
    print(f"  uv run scripts/explore_ase_db.py --src {extract_dir / 'train_4M'}")


if __name__ == "__main__":
    main()
