#!/usr/bin/env python3
"""
Generate VTuber design images with OpenAI Images API.

Outputs 2-3 images per character:
- standing (full body)
- turnaround (front/side/back sheet)
- stream-bust (upper body for streaming, optional)
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Tuple
from urllib import error, request

import numpy as np
from PIL import Image


GENERATIONS_URL = "https://api.openai.com/v1/images/generations"
EDITS_URL = "https://api.openai.com/v1/images/edits"


CHARACTERS: List[Dict[str, str]] = [
    {
        "slug": "morino-mint",
        "name": "森乃ミント",
        "desc": (
            "gentle older-sister vibe, pale mint long wavy hair with side braids and ornate "
            "flower-and-moon hair ornaments, slightly droopy kind eyes, layered mint robe dress "
            "with chiffon sleeves, moon brooch, tea-cup earrings, tassels, ribbons, delicate "
            "gold trim, elegant and warm aura"
        ),
        "palette": "main #6ACB7A, sub #D8F7DB, shadow #3F8F63, accent #F7E89E",
    },
    {
        "slug": "wakaba-ruru",
        "name": "若葉ルル",
        "desc": (
            "energetic petite girl, light lime high side twin tails with oversized ribbons, "
            "bright round eyes, clover motif layered hoodie with cropped jacket, asymmetrical "
            "suspenders, belts, rabbit hair clips, sporty and playful personality"
        ),
        "palette": "main #8EDC6A, sub #DFF7B8, shadow #4B9D58, accent #FFD85E",
    },
    {
        "slug": "mebuki-koharu",
        "name": "芽吹こはる",
        "desc": (
            "calm healing librarian girl, milky green medium hair with inner curls, side braid "
            "and ribbon ornament, gentle half-moon eyes, layered librarian dress with bookmark "
            "ribbon, lace cuffs, capelet, brooch, book-themed accessories, soft and comforting "
            "atmosphere"
        ),
        "palette": "main #B6E89A, sub #EEFAD7, shadow #6A9F6D, accent #F1DFA2",
    },
    {
        "slug": "suiu-noa",
        "name": "翠羽ノア",
        "desc": (
            "cool elegant global vtuber, deep emerald long straight hair with wing-like "
            "streaks and feather ornaments, sharp beautiful eyes, tailored layered jacket with "
            "feather tie, metallic accessories, asymmetrical sleeve details, refined and "
            "intelligent style"
        ),
        "palette": "main #52C4A1, sub #CFF7EC, shadow #2E7D75, accent #9BE4D6",
    },
    {
        "slug": "sakaki-shida",
        "name": "榊シダ",
        "desc": (
            "cool music producer vtuber, dark green hair with side-swept bangs and one bright "
            "streak, calm expression, technical layered jacket with waveform embroidery, utility "
            "straps, audio-device accessories, detachable headphones, asymmetrical details"
        ),
        "palette": "main #4EA772, sub #D6F0E1, shadow #2F5F4A, accent #A0D7B8",
    },
]


STYLE_PRESETS: Dict[str, str] = {
    "soft_modern": (
        "high-quality Japanese anime style for modern VTuber visual design, polished "
        "professional character sheet quality, clean lineart, detailed rendering, rich but "
        "cohesive decorative design, consistent identity, no text, no logo, no watermark. "
    ),
    "anime_cel": (
        "high-end Japanese anime character design, crisp clean lineart, strong cel shading, "
        "2-to-3 tone shadows, sharp highlights on hair and fabric, high contrast and vivid but "
        "controlled saturation, professional VTuber key visual quality, no text, no logo, "
        "no watermark. "
    ),
    "anime_painterly": (
        "premium anime illustration with thick painted shading, rich gradient shadows, clear "
        "form modeling, layered highlights, polished artbook quality, strong character identity, "
        "decorative and luxurious VTuber costume detail, no text, no logo, no watermark. "
    ),
}


def _http_post_json(url: str, api_key: str, payload: dict, retries: int = 3) -> dict:
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_err = None
    for attempt in range(1, retries + 1):
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            msg = exc.read().decode("utf-8", errors="ignore")
            last_err = RuntimeError(f"HTTP {exc.code}: {msg}")
        except Exception as exc:  # noqa: BLE001
            last_err = exc

        time.sleep(min(3 * attempt, 10))

    raise RuntimeError(f"request failed after retries: {last_err}")


def _multipart_body(fields: Dict[str, str], files: List[Tuple[str, Path]]) -> Tuple[bytes, str]:
    boundary = "----openai-boundary-" + uuid.uuid4().hex
    chunks: List[bytes] = []

    for k, v in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        chunks.append(v.encode())
        chunks.append(b"\r\n")

    for field_name, path in files:
        mime, _ = mimetypes.guess_type(path.name)
        mime = mime or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{path.name}"\r\n'.encode()
        )
        chunks.append(f"Content-Type: {mime}\r\n\r\n".encode())
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def _http_post_multipart(
    url: str,
    api_key: str,
    fields: Dict[str, str],
    files: List[Tuple[str, Path]],
    retries: int = 3,
) -> dict:
    body, boundary = _multipart_body(fields, files)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    last_err = None
    for attempt in range(1, retries + 1):
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            msg = exc.read().decode("utf-8", errors="ignore")
            last_err = RuntimeError(f"HTTP {exc.code}: {msg}")
        except Exception as exc:  # noqa: BLE001
            last_err = exc

        time.sleep(min(3 * attempt, 10))

    raise RuntimeError(f"request failed after retries: {last_err}")


def _decode_image(resp: dict) -> bytes:
    if "data" not in resp or not resp["data"]:
        raise RuntimeError(f"unexpected response: {resp}")
    b64 = resp["data"][0].get("b64_json")
    if not b64:
        raise RuntimeError(f"missing image data in response: {resp}")
    return base64.b64decode(b64)


def _guess_ext(img: bytes) -> str:
    if img.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if img.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    return ".bin"


def _write_image(target_base: Path, img: bytes) -> Path:
    ext = _guess_ext(img)
    out = target_base.with_suffix(ext)
    out.write_bytes(img)
    return out


def _color_match_to_reference(ref_path: Path, target_path: Path) -> None:
    ref_img = Image.open(ref_path).convert("RGB")
    tgt_img = Image.open(target_path).convert("RGB")

    ref = np.asarray(ref_img).astype(np.float32)
    tgt = np.asarray(tgt_img).astype(np.float32)

    ref_mean = ref.reshape(-1, 3).mean(axis=0)
    ref_std = ref.reshape(-1, 3).std(axis=0) + 1e-6
    tgt_mean = tgt.reshape(-1, 3).mean(axis=0)
    tgt_std = tgt.reshape(-1, 3).std(axis=0) + 1e-6

    # Channel-wise color transfer to keep identity colors stable.
    out = (tgt - tgt_mean) * (ref_std / tgt_std) + ref_mean
    out = np.clip(out, 0, 255).astype(np.uint8)
    Image.fromarray(out, mode="RGB").save(target_path)


def generate_character(
    api_key: str,
    out_dir: Path,
    char: Dict[str, str],
    style_prefix: str,
    force: bool,
    apply_color_match: bool,
    include_bust: bool,
) -> None:
    char_dir = out_dir / char["slug"]
    char_dir.mkdir(parents=True, exist_ok=True)

    standing_existing = list(char_dir.glob("standing.*"))
    turnaround_existing = list(char_dir.glob("turnaround.*"))
    bust_existing = list(char_dir.glob("stream-bust.*"))
    is_complete = standing_existing and turnaround_existing
    if include_bust:
        is_complete = bool(is_complete and bust_existing)
    if (not force) and is_complete:
        print(f"[skip] {char['slug']} already complete", flush=True)
        return

    color_lock = (
        f"Color lock palette: {char['palette']}. "
        "Keep exact same costume and hair colors across all outputs. "
        "No hue shift, no recoloring, no dramatic exposure change. "
        "Use neutral studio lighting and consistent white balance."
    )

    standing_prompt = (
        style_prefix
        + f"Character: {char['name']}. {char['desc']}. {color_lock} "
        + "Single character, full body standing pose, front-facing, complete outfit and shoes "
        + "fully visible, strong silhouette readability, plain light background, design-reference "
        + "quality, highly detailed accessories."
    )
    standing_payload = {
        "model": "gpt-image-1",
        "prompt": standing_prompt,
        "size": "1024x1536",
        "quality": "high",
    }
    if (not force) and standing_existing:
        standing_path = standing_existing[0]
        print(f"  [reuse] {standing_path}", flush=True)
    else:
        print("  [gen] standing", flush=True)
        standing_resp = _http_post_json(GENERATIONS_URL, api_key, standing_payload)
        standing_bytes = _decode_image(standing_resp)
        standing_path = _write_image(char_dir / "standing", standing_bytes)
        print(f"  [ok] {standing_path}", flush=True)

    turnaround_prompt = (
        style_prefix
        + f"Same exact character as the reference ({char['name']}). {color_lock} "
        + "Create a clean turnaround sheet with 3 full-body views in one image: "
        + "front view, right-side view, back view. "
        + "Keep face, hairstyle, outfit, proportions, and accessories fully consistent. "
        + "White background, no text labels, preserve complex accessory placement."
    )
    turnaround_fields = {
        "model": "gpt-image-1",
        "prompt": turnaround_prompt,
        "size": "1536x1024",
        "quality": "high",
    }
    if (not force) and turnaround_existing:
        print(f"  [reuse] {turnaround_existing[0]}", flush=True)
    else:
        print("  [gen] turnaround", flush=True)
        turnaround_resp = _http_post_multipart(
            EDITS_URL, api_key, turnaround_fields, [("image[]", standing_path)]
        )
        turnaround_bytes = _decode_image(turnaround_resp)
        turnaround_path = _write_image(char_dir / "turnaround", turnaround_bytes)
        if apply_color_match:
            _color_match_to_reference(standing_path, turnaround_path)
        print(f"  [ok] {turnaround_path}", flush=True)

    if include_bust:
        bust_prompt = (
            style_prefix
            + f"Same exact character as the reference ({char['name']}). {color_lock} "
            + "Upper-body portrait for livestream thumbnail, facing viewer, "
            + "clear face and hair details, rich costume details near shoulder/chest, "
            + "clean light background close to off-white. Keep identity and outfit motifs consistent "
            + "with the reference."
        )
        bust_fields = {
            "model": "gpt-image-1",
            "prompt": bust_prompt,
            "size": "1024x1024",
            "quality": "high",
        }
        if (not force) and bust_existing:
            print(f"  [reuse] {bust_existing[0]}", flush=True)
        else:
            print("  [gen] stream-bust", flush=True)
            bust_resp = _http_post_multipart(
                EDITS_URL, api_key, bust_fields, [("image[]", standing_path)]
            )
            bust_bytes = _decode_image(bust_resp)
            bust_path = _write_image(char_dir / "stream-bust", bust_bytes)
            if apply_color_match:
                _color_match_to_reference(standing_path, bust_path)
            print(f"  [ok] {bust_path}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir",
        default="assets/illustrations-openai",
        help="Output directory",
    )
    parser.add_argument(
        "--chars",
        default="all",
        help="Comma-separated slugs to generate (default: all)",
    )
    parser.add_argument(
        "--style-preset",
        default="anime_cel",
        choices=sorted(STYLE_PRESETS.keys()),
        help="Rendering style preset",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate files even if they already exist",
    )
    parser.add_argument(
        "--no-color-match",
        action="store_true",
        help="Disable automatic color matching to standing image",
    )
    parser.add_argument(
        "--include-bust",
        action="store_true",
        help="Also generate stream-bust images (default: off)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = CHARACTERS
    if args.chars != "all":
        wanted = {x.strip() for x in args.chars.split(",") if x.strip()}
        selected = [c for c in CHARACTERS if c["slug"] in wanted]
        if not selected:
            raise SystemExit(f"no matching characters for --chars={args.chars}")

    style_prefix = STYLE_PRESETS[args.style_preset]

    failures: List[str] = []
    for char in selected:
        print(f"[generate] {char['slug']} ...", flush=True)
        try:
            generate_character(
                api_key,
                out_dir,
                char,
                style_prefix,
                args.force,
                not args.no_color_match,
                args.include_bust,
            )
            print(f"[ok] {char['slug']}", flush=True)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{char['slug']}: {exc}")
            print(f"[fail] {char['slug']}: {exc}", flush=True)

    print("\n=== summary ===", flush=True)
    if failures:
        for f in failures:
            print("-", f)
        return 1

    print("all characters generated successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
