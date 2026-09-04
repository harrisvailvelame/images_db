# Asset Ingestion & Image Optimization Pipeline

A small automation pipeline for ingesting local media assets, normalizing images, assigning collision-resistant tokens and optionally synchronizing generated assets to Git.

This repository is useful as an example of **file ingestion, deterministic routing, media processing and lightweight automation**.

## Architecture

```text
staging/
   ↓
Asset classifier
   ├── image (.jpg/.jpeg/.png/.webp)
   │      ↓
   │   Pillow processing
   │   - RGB normalization
   │   - max-width resize
   │   - optimized JPEG output
   │      ↓
   │   images/<TOKEN>.jpg
   │
   ├── raw media (.gif/.mp4/.webm/.mp3/.wav/.ogg)
   │      ↓
   │   lossless copy / passthrough
   │      ↓
   │   images/<TOKEN>.<ext>
   │
   └── unsupported format → ignored

Optional Git sync → stage only generated assets → commit → push
```

## Key engineering decisions

- **Safe-by-default Git behavior:** processing does not push unless `--push` is supplied.
- **Explicit source consumption:** input files are only deleted when `--consume` is supplied.
- **Scoped Git staging:** only the generated `images/` directory is staged by the sync routine.
- **Bounded image size:** large images are resized while preserving aspect ratio.
- **Format normalization:** supported image formats are exported as optimized JPEG.
- **Idempotent directory setup:** `staging/` and `images/` are created automatically.

## Usage

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Place assets in `staging/`, then run:

```bash
python website_upload_pics.py
```

Process and remove successfully handled source files:

```bash
python website_upload_pics.py --consume
```

Process, consume and push generated assets:

```bash
python website_upload_pics.py --consume --push
```

## Continuous mode

`daemon_aura.sh` watches `staging/` with `inotifywait` and invokes the ingestion pipeline whenever a new file arrives.

Linux dependency:

```bash
sudo apt-get install inotify-tools
```

Then:

```bash
chmod +x daemon_aura.sh
./daemon_aura.sh
```

## Repository structure

```text
.
├── website_upload_pics.py     # ingestion + processing + optional Git sync
├── daemon_aura.sh             # Linux filesystem watcher
├── images/                    # generated / published assets
├── staging/                   # local ingestion queue (gitignored)
├── requirements.txt
└── .github/workflows/quality.yml
```

## Scope

This is a lightweight automation utility, not a full object-storage or CDN platform. For larger systems, the same pattern would typically evolve toward object storage, event-driven ingestion, checksums, metadata catalogs and lifecycle policies.

---

**Author:** Harrison Grant Vail  
[LinkedIn](https://www.linkedin.com/in/harrison-grant-vail) · [GitHub](https://github.com/harrisvailvelame)
