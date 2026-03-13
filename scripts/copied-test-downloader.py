#!/usr/bin/env python3
"""
Boto3-based S3 Calculation Downloader

A simplified and more efficient downloader using AWS Python SDK with:
- Built-in transfer optimization and retry logic
- Real-time progress tracking with progress callbacks
- Better error handling with Python exceptions
- Automatic multipart downloads for large files
- Connection pooling and resource efficiency
"""

import os
import json
import time
import gzip
import shutil
import argparse
import signal
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple, Any
import logging
from dataclasses import dataclass

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError, NoCredentialsError
    from boto3.s3.transfer import TransferConfig
except ImportError:
    print("Error: boto3 is required. Install with: pip install boto3")
    exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class DownloadConfig:
    """Configuration class for the downloader."""

    max_workers: int = 5
    progress_report_frequency: int = 10  # Report progress every N downloads
    max_paths: Optional[int] = None  # Limit total downloads (None = no limit)
    paths_file: str = "4m_paths.txt"
    failures_file: str = "failures.txt"
    progress_file: str = "boto3_progress.json"
    save_frequency: int = 10  # Save progress every N downloads

    # S3 configuration
    s3_bucket: str = "opencatalysisdata"
    hot_prefix: str = "archive/hot"
    warm_prefix: str = "archive/warm"

    # boto3 Transfer configuration
    multipart_threshold: int = 64 * 1024 * 1024  # 64MB
    max_concurrency: int = 10
    multipart_chunksize: int = 8 * 1024 * 1024  # 8MB
    use_threads: bool = True
    s3_max_pool_connections: int = 50


class ProgressCallback:
    """Progress callback for individual file downloads."""

    def __init__(self, filename: str, total_size: Optional[int] = None):
        self.filename = filename
        self.total_size = total_size
        self.bytes_transferred = 0
        self.start_time = time.time()

    def __call__(self, bytes_amount: int):
        self.bytes_transferred += bytes_amount
        if self.total_size:
            percent = (self.bytes_transferred / self.total_size) * 100
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                speed = self.bytes_transferred / elapsed
                logger.debug(
                    f"{self.filename}: {percent:.1f}% ({speed/1024/1024:.1f} MB/s)"
                )


class ProgressTracker:
    """Handles progress tracking and persistence."""

    def __init__(self, progress_file: str, save_frequency: int = 10):
        self.progress_file = progress_file
        self.save_frequency = save_frequency
        self.save_counter = 0
        self.lock = threading.Lock()
        self.progress = self.load_progress()

    def load_progress(self) -> Dict:
        """Load progress from file if it exists."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r") as f:
                    progress = json.load(f)

                # Ensure all keys exist
                progress.setdefault("completed", [])
                progress.setdefault("failed", [])
                progress.setdefault("in_progress", [])
                progress.setdefault(
                    "stats",
                    {
                        "successful": len(progress.get("completed", [])),
                        "failed": len(progress.get("failed", [])),
                    },
                )

                logger.info(
                    f"Resumed from previous session: {len(progress['completed'])} completed, "
                    f"{len(progress['failed'])} failed, {len(progress['in_progress'])} were in progress."
                )

                return progress
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load progress file: {e}. Starting fresh.")

        return {
            "completed": [],
            "failed": [],
            "in_progress": [],
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "stats": {"successful": 0, "failed": 0},
        }

    def save_progress(self, force: bool = False):
        """Save current progress to file."""
        with self.lock:
            self.save_counter += 1
            if not force and (self.save_counter % self.save_frequency != 0):
                return

            self.progress["last_updated"] = datetime.now().isoformat()
            try:
                # Atomic write
                temp_file = f"{self.progress_file}.tmp"
                with open(temp_file, "w") as f:
                    json.dump(self.progress, f, indent=2)
                os.rename(temp_file, self.progress_file)
                logger.debug(f"Progress saved to {self.progress_file}")
            except IOError as e:
                logger.error(f"Failed to save progress: {e}")

    def mark_in_progress(self, calc_path: str):
        """Mark a calculation as in progress."""
        with self.lock:
            if calc_path not in self.progress["in_progress"]:
                self.progress["in_progress"].append(calc_path)

    def mark_completed(self, calc_path: str):
        """Mark a calculation as completed."""
        with self.lock:
            if calc_path not in self.progress["completed"]:
                self.progress["completed"].append(calc_path)
                self.progress["stats"]["successful"] += 1
            if calc_path in self.progress["in_progress"]:
                self.progress["in_progress"].remove(calc_path)

    def mark_failed(self, calc_path: str):
        """Mark a calculation as failed."""
        with self.lock:
            if calc_path not in self.progress["failed"]:
                self.progress["failed"].append(calc_path)
                self.progress["stats"]["failed"] += 1
            if calc_path in self.progress["in_progress"]:
                self.progress["in_progress"].remove(calc_path)

    def is_completed(self, calc_path: str) -> bool:
        """Check if a calculation is already completed."""
        with self.lock:
            return calc_path in self.progress["completed"]

    def get_stats(self) -> Dict:
        """Get current statistics."""
        with self.lock:
            return self.progress["stats"].copy()

    def get_completed_set(self) -> Set[str]:
        """Get set of completed calculations for fast lookup."""
        with self.lock:
            return set(self.progress["completed"])


class Boto3CalculationDownloader:
    """boto3-based downloader with built-in transfer optimization."""

    def __init__(self, config: DownloadConfig):
        self.config = config
        self.tracker = ProgressTracker(config.progress_file, config.save_frequency)
        self.shutdown_requested = False

        # Initialize boto3 clients
        self.setup_boto3()
        self.setup_signal_handlers()

    def setup_boto3(self):
        """Initialize boto3 S3 client and transfer config."""
        try:
            # Create a botocore config
            boto_config = Config(
                max_pool_connections=self.config.s3_max_pool_connections
            )
            # Create S3 client
            self.s3_client = boto3.client("s3", config=boto_config)

            # NOTE: We are intentionally not calling head_bucket here.
            # This is because many public buckets (like opencatalysisdata)
            # grant s3:GetObject but not s3:ListBucket permissions.
            # Calling head_bucket would require ListBucket and cause a 403 Forbidden error.
            # The first download_file call will act as the credential and connectivity test.

            # Configure transfer settings for optimal performance
            self.transfer_config = TransferConfig(
                multipart_threshold=self.config.multipart_threshold,
                max_concurrency=self.config.max_concurrency,
                multipart_chunksize=self.config.multipart_chunksize,
                use_threads=self.config.use_threads,
            )

        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            if not self.shutdown_requested:
                logger.info(
                    "Shutdown requested. Finishing active tasks before exiting..."
                )
                self.shutdown_requested = True
                # The main loop will stop submitting new tasks.
                # A second CTRL+C can force exit, but progress might be inconsistent.

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a single file from S3 using boto3.

        Args:
            s3_key: S3 key (path within bucket)
            local_path: Local path to save the file

        Returns:
            bool: True if successful, False otherwise
        """
        # Check if file already exists and has reasonable size
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            logger.debug(f"File {local_path} already exists, skipping download")
            return True

        if self.shutdown_requested:
            return False

        try:
            # Get file size for progress tracking
            try:
                response = self.s3_client.head_object(
                    Bucket=self.config.s3_bucket, Key=s3_key
                )
                file_size = response.get("ContentLength", 0)
            except ClientError:
                file_size = None

            # Create progress callback
            progress_callback = ProgressCallback(
                filename=os.path.basename(local_path), total_size=file_size
            )

            # Download with transfer manager (automatic retries, multipart, etc.)
            self.s3_client.download_file(
                Bucket=self.config.s3_bucket,
                Key=s3_key,
                Filename=local_path,
                Config=self.transfer_config,
                Callback=progress_callback,
            )

            # Verify download
            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                return True
            else:
                logger.error(f"Downloaded file {local_path} is empty or missing")
                return False

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(
                f"Failed to download s3://{self.config.s3_bucket}/{s3_key}: {error_code} - {e}"
            )
            # Clean up partial file
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except OSError:
                    pass
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error downloading s3://{self.config.s3_bucket}/{s3_key}: {e}"
            )
            return False

    def download_calculation(self, calc_path: str) -> Tuple[str, bool]:
        """
        Download all files for a single calculation.

        Args:
            calc_path: The calculation path

        Returns:
            Tuple[str, bool]: The calculation path and a boolean indicating success
        """
        # Skip if already completed
        if self.tracker.is_completed(calc_path):
            logger.debug(f"Skipping already completed: {calc_path}")
            return calc_path, True

        self.tracker.mark_in_progress(calc_path)

        # Create directory
        local_dir = Path(calc_path)
        local_dir.mkdir(parents=True, exist_ok=True)

        # Define the three files to download
        files = [
            (
                f"{self.config.hot_prefix}/{calc_path}/orca.tar.zst",
                str(local_dir / "orca.tar.zst"),
            ),
            (
                f"{self.config.warm_prefix}/{calc_path}/density_mat.npz",
                str(local_dir / "density_mat.npz"),
            ),
            (
                f"{self.config.warm_prefix}/{calc_path}/orca.gbw.zstd0",
                str(local_dir / "orca.gbw.zstd0"),
            ),
        ]

        # Download all files
        success = True
        for s3_key, local_path in files:
            if self.shutdown_requested:
                success = False
                break

            if not self.download_file(s3_key, local_path):
                success = False
                break

        # Update progress
        if success:
            self.tracker.mark_completed(calc_path)
            logger.info(f"Successfully downloaded: {calc_path}")
        else:
            self.tracker.mark_failed(calc_path)
            logger.error(f"Failed to download: {calc_path}")

            # Clean up directory if download failed
            try:
                if local_dir.exists() and local_dir.is_dir():
                    shutil.rmtree(local_dir)
            except OSError as e:
                logger.warning(
                    f"Could not clean up failed download directory {local_dir}: {e}"
                )

        # Save progress
        self.tracker.save_progress()

        return calc_path, success

    def download_path_list(self) -> List[str]:
        """Download and extract the list of calculation paths."""
        paths_file = Path(self.config.paths_file)

        # Check if paths file already exists
        if paths_file.exists():
            logger.info("Using existing paths file")
        else:
            logger.info("Downloading calculation paths list...")

            # Download compressed file using boto3
            if not self.download_file(
                f"{self.config.hot_prefix}/4m_paths.txt.gz", "4m_paths.txt.gz"
            ):
                raise Exception("Failed to download path list")

            # Decompress
            logger.info("Decompressing path list...")
            with gzip.open("4m_paths.txt.gz", "rb") as f_in:
                with open(self.config.paths_file, "wb") as f_out:
                    f_out.write(f_in.read())

        # Read paths
        with open(self.config.paths_file, "r") as f:
            paths = [line.strip() for line in f if line.strip()]

        # Apply max_paths limit if specified
        if self.config.max_paths is not None:
            paths = paths[: self.config.max_paths]
            logger.info(f"Limited to first {self.config.max_paths} paths")

        logger.info(f"Found {len(paths)} calculation paths")
        return paths

    def get_remaining_paths(self, all_paths: List[str]) -> List[str]:
        """Get list of paths that still need to be downloaded."""
        completed_set = self.tracker.get_completed_set()
        # Do not filter out 'in_progress' paths, they should be retried
        remaining = [p for p in all_paths if p not in completed_set]
        return remaining

    def write_failures_file(self):
        """Write failures file for compatibility with existing scripts."""
        with self.tracker.lock:
            failed_paths = self.tracker.progress["failed"]
            with open(self.config.failures_file, "w") as f:
                for failed_path in failed_paths:
                    f.write(f"{failed_path}\n")

    def run(self) -> Dict:
        """
        Main download process.

        Returns:
            Dict: Final statistics
        """
        try:
            # Get list of calculations
            all_paths = self.download_path_list()

            # Filter out already completed
            remaining_paths = self.get_remaining_paths(all_paths)
            total_to_download = len(remaining_paths)

            if not remaining_paths:
                logger.info("All calculations already downloaded!")
                return self.tracker.get_stats()

            stats = self.tracker.get_stats()
            logger.info(
                f"Starting download of {total_to_download} calculations "
                f"({stats['successful']} already completed, {stats['failed']} failed)"
            )

            processed_in_session = 0

            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                # Use a generator for memory efficiency
                path_generator = (p for p in remaining_paths)

                # Submit the initial batch of jobs
                futures = {
                    executor.submit(
                        self.download_calculation, next(path_generator)
                    ): next(path_generator)
                    for _ in range(min(self.config.max_workers, total_to_download))
                }

                while futures:
                    if self.shutdown_requested and len(futures) == 0:
                        break

                    # Wait for the next future to complete
                    for future in as_completed(futures):
                        # Get result and remove from futures
                        calc_path, success = future.result()
                        del futures[future]

                        processed_in_session += 1

                        # Log progress periodically
                        if (
                            processed_in_session % self.config.progress_report_frequency
                            == 0
                            or processed_in_session == total_to_download
                        ):
                            stats = self.tracker.get_stats()
                            remaining_count = total_to_download - processed_in_session
                            logger.info(
                                f"Progress: {stats['successful']} completed, {stats['failed']} failed. "
                                f"{remaining_count} remaining in session."
                            )

                        # If not shutting down, submit a new job
                        if not self.shutdown_requested:
                            try:
                                next_path = next(path_generator)
                                new_future = executor.submit(
                                    self.download_calculation, next_path
                                )
                                futures[new_future] = next_path
                            except StopIteration:
                                # No more paths to process
                                break

        finally:
            # Always save final progress and write failures file
            logger.info("Download process finished. Saving final progress...")
            self.tracker.save_progress(force=True)
            self.write_failures_file()

            stats = self.tracker.get_stats()
            logger.info(
                f"Download session complete! "
                f"Total: {stats['successful']} successful, {stats['failed']} failed"
            )
            return stats


def main():
    parser = argparse.ArgumentParser(
        description="Boto3-based OpenCatalysisData downloader"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Maximum parallel calculation downloads (default: 5)",
    )
    parser.add_argument(
        "--progress-report-frequency",
        type=int,
        default=10,
        help="Report progress every N downloads (default: 10)",
    )
    parser.add_argument(
        "--max-paths",
        type=int,
        default=None,
        help="Maximum number of paths to download (default: no limit)",
    )
    parser.add_argument(
        "--paths-file",
        default="4m_paths.txt",
        help="Local paths file (default: 4m_paths.txt)",
    )
    parser.add_argument(
        "--failures-file",
        default="failures.txt",
        help="Failures output file (default: failures.txt)",
    )
    parser.add_argument(
        "--progress-file",
        default="boto3_progress.json",
        help="Progress tracking file (default: boto3_progress.json)",
    )
    parser.add_argument(
        "--save-frequency",
        type=int,
        default=10,
        help="Save progress every N downloads (default: 10)",
    )
    parser.add_argument(
        "--multipart-threshold",
        type=int,
        default=64,
        help="Multipart threshold in MB (default: 64)",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=10,
        help="Max concurrent transfers per file (default: 10)",
    )
    parser.add_argument(
        "--s3-max-pool-connections",
        type=int,
        default=10,
        help="S3 client max connection pool size (default: 10)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Input validation
    if args.workers <= 0:
        parser.error("Number of workers must be positive")
    if args.progress_report_frequency <= 0:
        parser.error("Progress report frequency must be positive")
    if args.save_frequency <= 0:
        parser.error("Save frequency must be positive")
    if args.max_paths is not None and args.max_paths <= 0:
        parser.error("Max paths must be positive if specified")

    config = DownloadConfig(
        max_workers=args.workers,
        progress_report_frequency=args.progress_report_frequency,
        max_paths=args.max_paths,
        paths_file=args.paths_file,
        failures_file=args.failures_file,
        progress_file=args.progress_file,
        save_frequency=args.save_frequency,
        multipart_threshold=args.multipart_threshold * 1024 * 1024,  # Convert to bytes
        max_concurrency=args.max_concurrency,
        s3_max_pool_connections=args.s3_max_pool_connections,
    )

    try:
        downloader = Boto3CalculationDownloader(config)
        downloader.run()
    except KeyboardInterrupt:
        logger.info(
            "\nInterrupted by user. The script will finish active tasks and exit."
        )
    except Exception as e:
        logger.error(f"A critical error occurred: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
