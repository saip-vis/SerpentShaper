# Local image review

Start the server from Terminal:

```bash
cd /Users/saipranavviswanathan/SerpentShaper
./start_image_review.sh
```

Open **http://127.0.0.1:8767**. This is separate from the venom-composition interface on port 8765. Stop the review server with Control-C in its terminal. Run one review server per collection folder.

The launcher uses an installed Python with Pillow or the available Codex bundled Python. If neither has Pillow, it prints the installation command. The server only binds to localhost; nothing is uploaded or published.

## After cloning the repository

Photo manifests and review decisions are versioned. Original photos, generated contact sheets, caches, backups, and derived exports stay local. To restore a species' images from the URLs recorded in its manifest, run this explicitly before reviewing that batch:

```bash
python3 scripts/collect_image_pilot.py download --batch pilot_007_boomslang --limit 10
```

Replace the batch name for other species. This retains existing review annotations and verifies present-file checksums before skipping downloads. Historical URLs may become unavailable; failures are recorded rather than substituted. Starting the review interface itself never downloads photos.

## Review workflow

1. Search for a species in the left sidebar and choose its folder. Empty folders show their recorded collection outcome.
2. Choose an image from the thumbnail strip, or use Previous/Next. Filter by unreviewed, accepted, rejected, flagged, or reference-only status.
3. Record species confidence, body condition, framing, viewing angle, pose, issues, and notes. Unknown is valid when a detail cannot be determined confidently.
4. Choose a decision. Saves go directly to that species' `manifest.json`; there is no separate manual JSON-edit step.

| Decision | Meaning | Rendering export |
|---|---|---|
| Accept | Reviewer confirms species, no visible injury/deformation, useful single-snake framing, and no selected image issues. | Included if other policy exclusions are absent. |
| Reject | Unsuitable image; select an issue or explain why. | Excluded. |
| Flag for review | Identity, quality, or interpretation needs another look; select an issue or add a note. | Excluded. |
| Reference only | Useful anatomy or a special view; explain the use. | Excluded. |

Existing injury/deformity exclusions cannot be cleared through ordinary acceptance. An injured reference requires an explicit uniquely-useful-anatomy confirmation and explanatory note; it remains excluded from rendering. Exact duplicate copies cannot be accepted; open their original record instead. The original user acceptance of the diamondback batch is preserved; editing one of those reviews uses the new explicit assessment fields.

These are reviewer assessments, not expert taxonomic certification or automatic injury detection. Previews and source links help inspection; they do not establish species identity.

## Fast controls and recovery

- **A** accept, **R** reject, **F** flag, **S** reference only.
- **N/P** next/previous. Shortcuts pause while an input, select, textarea, or button is focused.
- “Move to next image after saving” is enabled by default.
- **Undo last save** restores the prior review fields and refreshes the export. After a reload it is available when the opened image's last action was an interface review.
- Unsaved changes are indicated and navigation asks before discarding them.
- A stale revision is rejected instead of overwriting a later review; reload the record before retrying.

Every save/undo makes an exact pre-write manifest backup under `data/image_pilots/_review_backups/<batch>/`. Compact before/after review history is also stored in the image record. Original files and source/attribution fields are preserved.

## Previews and exports

Thumbnails are bounded to 320 pixels; main previews to 1600 pixels on the longest side. They are generated lazily under `_review_previews/`, apply EXIF orientation, and preserve the originals. The 120-megapixel original is served as a small review preview; “Open original” is explicit. Previews are for review, and should not be treated as calibrated color measurements.

Every saved decision refreshes `data/image_pilots/rendering_manifest.json`. “Export accepted” also refreshes it on demand. Rejected, flagged, reference-only, injury-excluded, and duplicate-copy records are omitted. Review all images before model training; no training is run by this interface.

The earlier static galleries and post-download notes are collection snapshots. Use this interface's live counts and manifests for current curation progress. `scripts/build_collection_index.py` can regenerate the static index when needed.

## Validation

`tests/test_image_review.py` uses temporary data to check persistence, backups, export refresh, undo, stale revisions, original-preserving previews, path boundaries, request protections, and injury/duplicate/reference policy. It needs Pillow and localhost binding permission. Browser save tests also use an isolated copy; the real species manifests are not altered during QA.
