"""Check the provenance and structure of the small image-trait pilot.

Run from any directory: python3 ML/image_traits/validate.py
This does not validate the visual annotations or approve images for training.
"""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "ML/image_traits/pilot_observations.json"
VOCABULARY = {
    "head_profile": {"elongated_rounded", "broad_wedge"},
    "body_build": {"slender"},
    "hood_display": {"spread"},
    "hood_marking": {"pale_hood_mark"},
    "body_pattern": {"diamond_like"},
    "tail_pattern": {"alternating_dark_light_bands"},
    "iris_color": {"green"},
    "posture": {"raised"},
}
COLORS = {"dark", "brown", "pale", "olive", "gray", "green"}


def main():
    dataset = json.loads(DATA.read_text())
    seen_images, seen_observations = set(), set()
    errors = []
    for row in dataset["records"]:
        image_id = row["image_id"]
        try:
            assert image_id not in seen_images, "duplicate image"
            seen_images.add(image_id)
            observation = (row["species_label"], row["observation_id"])
            assert observation not in seen_observations, "duplicate observation for species"
            seen_observations.add(observation)
            manifest = ROOT / row["source_manifest"]
            source = next(item for item in json.loads(manifest.read_text()) if item["image_id"] == image_id)
            for output_key, source_key in (
                ("species_label", "provider_species_name"),
                ("observation_id", "observation_id"),
                ("sha256", "sha256"),
                ("source_page", "source_page"),
                ("photo_page", "photo_page"),
                ("photo_license", "photo_license"),
                ("license_version", "license_version"),
                ("attribution", "attribution"),
                ("source_review_status", "review_status"),
            ):
                assert row[output_key] == source.get(source_key), f"source mismatch: {output_key}"
            assert row["source_rendering_training_excluded"] == bool(source.get("rendering_training_excluded", False)), "exclusion mismatch"
            assert row["pilot_training_eligible"] is False, "pilot must remain reference-only"
            assert source["review_status"] in {"accepted", "unreviewed"}, "rejected source image"
            image_path = ROOT / row["local_image_path"]
            assert image_path.resolve() == (manifest.parent / source["local_path"]).resolve(), "image path mismatch"
            assert hashlib.sha256(image_path.read_bytes()).hexdigest() == row["sha256"], "image hash mismatch"
            features = row["features"]
            assert set(features) == set(VOCABULARY) | {"body_color"}, "unexpected trait fields"
            for key, allowed in VOCABULARY.items():
                assert features[key] is None or features[key] in allowed, f"invalid {key}"
            colors = features["body_color"]
            assert colors is None or (isinstance(colors, list) and colors and set(colors) <= COLORS), "invalid colors"
        except (AssertionError, KeyError, OSError, StopIteration, TypeError, json.JSONDecodeError) as exc:
            errors.append(f"{image_id}: {exc}")
    if errors:
        raise SystemExit("Validation failed:\n" + "\n".join(errors))
    print(f"Validated {len(seen_images)} images from {len(seen_observations)} observations across "
          f"{len({row['species_label'] for row in dataset['records']})} species labels.")
    print("Checks provenance and structure only; visual accuracy and training eligibility remain unverified.")


if __name__ == "__main__":
    main()
