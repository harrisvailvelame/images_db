from __future__ import annotations

import argparse
import shutil
import subprocess
import uuid
from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "staging"
EXPORT_DIR = BASE_DIR / "images"

QUALITY = 95
MAX_WIDTH = 1920

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
RAW_EXTS = {".gif", ".mp4", ".webm", ".mp3", ".wav", ".ogg"}


def generate_token() -> str:
    """Return a short collision-resistant asset token."""
    return uuid.uuid4().hex[:12].upper()


def ensure_directories() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def process_image(file_path: Path, output_path: Path) -> None:
    """Normalize a supported image and write an optimized JPEG."""
    with Image.open(file_path) as image:
        image = image.convert("RGB")

        if image.width > MAX_WIDTH:
            ratio = MAX_WIDTH / float(image.width)
            new_height = max(1, int(image.height * ratio))
            image = image.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)

        image.save(output_path, "JPEG", quality=QUALITY, optimize=True)


def process_assets(*, consume: bool = False) -> int:
    """Process files from staging and return the number of exported assets."""
    ensure_directories()

    files_found = sorted(
        path for path in SOURCE_DIR.iterdir() if path.is_file() and not path.name.startswith(".")
    )

    if not files_found:
        print(f"No assets waiting in {SOURCE_DIR}")
        return 0

    processed = 0

    for file_path in files_found:
        extension = file_path.suffix.lower()
        token = generate_token()

        try:
            if extension in IMAGE_EXTS:
                output_path = EXPORT_DIR / f"{token}.jpg"
                process_image(file_path, output_path)
            elif extension in RAW_EXTS:
                output_path = EXPORT_DIR / f"{token}{extension}"
                shutil.copy2(file_path, output_path)
            else:
                print(f"Skipping unsupported format: {file_path.name}")
                continue

            processed += 1
            print(f"Exported {file_path.name} -> {output_path.name}")

            if consume:
                file_path.unlink()

        except (OSError, ValueError) as exc:
            print(f"Failed to process {file_path.name}: {exc}")

    return processed


def run_git(*args: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=BASE_DIR,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def git_sync(*, push: bool = False) -> bool:
    """Commit generated assets and optionally push them to origin/main."""
    try:
        run_git("add", "images")
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=BASE_DIR,
            text=True,
        )

        if diff.returncode == 0:
            print("No generated-asset changes to commit.")
            return False
        if diff.returncode not in (0, 1):
            raise subprocess.CalledProcessError(diff.returncode, diff.args)

        run_git("commit", "-m", "chore: ingest generated assets")

        if push:
            run_git("push", "origin", "main")
            print("Generated assets committed and pushed.")
        else:
            print("Generated assets committed locally. Use --push to publish them.")

        return True

    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"Git synchronization failed: {exc}")
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process and optionally publish media assets.")
    parser.add_argument(
        "--consume",
        action="store_true",
        help="Delete a source asset after it is processed successfully.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Commit generated assets and push origin/main.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Commit generated assets locally without pushing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    processed = process_assets(consume=args.consume)

    if processed and (args.commit or args.push):
        git_sync(push=args.push)

    print(f"Processed assets: {processed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
