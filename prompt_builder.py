"""
prompt_builder.py — Single source of truth for brand context assembly.

All AI modules call build_brand_context() or build_social_context() instead
of assembling brand data independently. Handles voice cluster filtering,
calibration status injection, and graceful degradation notices.

Pure functions only (stdlib: json, re). No Streamlit, no Anthropic.
"""
from __future__ import annotations

import json
import re


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VOICE_CLUSTER_NAMES = [
    "Corporate Affairs",
    "Crisis & Response",
    "Internal Leadership",
    "Thought Leadership",
    "Brand Marketing",
]

# Maps content types (from app.py selectboxes) to primary voice cluster
CONTENT_TYPE_TO_CLUSTER = {
    "Internal Email": "Internal Leadership",
    "Press Release": "Corporate Affairs",
    "Blog Post": "Brand Marketing",
    "Executive Memo": "Internal Leadership",
    "Crisis Statement": "Crisis & Response",
    "Speech / Script": "Thought Leadership",
    "Social Campaign": "Brand Marketing",
}

# Message house fields for completeness counting
_MH_FIELDS = [
    "mh_brand_promise",
    "mh_pillars_json",
    "mh_founder_positioning",
    "mh_pov",
    "mh_boilerplate",
    "mh_offlimits",
    "mh_preapproval_claims",
    "mh_tone_constraints",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean_dna(text: str) -> str:
    """Strip [VISUAL_REF:] base64 image lines from DNA blobs."""
    if not text:
        return ""
    return "\n".join(
        line for line in text.split("\n")
        if not line.startswith("[VISUAL_REF:")
    )


def _count_mh_fields(inputs: dict) -> tuple:
    """Return (filled, total) count of message house fields."""
    total = len(_MH_FIELDS)
    filled = 0
    for key in _MH_FIELDS:
        val = inputs.get(key, "")
        if isinstance(val, str) and val.strip():
            filled += 1
    return filled, total


# ---------------------------------------------------------------------------
# Voice cluster parsing
# ---------------------------------------------------------------------------

def parse_voice_clusters(voice_dna: str) -> dict:
    """
    Parse voice_dna blob into {cluster_name: [sample_texts]}.

    Splits on '----------------' delimiter, extracts cluster name from
    [ASSET: CLUSTER: {NAME} | ...] headers. Returns only clusters that
    have at least one sample.
    """
    if not voice_dna:
        return {}

    clusters = {}
    chunks = re.split(r"-{10,}", voice_dna)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Extract cluster name from header
        match = re.search(
            r"\[ASSET:\s*CLUSTER:\s*([^|]+)\s*\|",
            chunk,
            re.IGNORECASE,
        )
        if not match:
            continue

        cluster_name = match.group(1).strip()

        # Normalize to canonical names (title-case match)
        canonical = None
        for cname in VOICE_CLUSTER_NAMES:
            if cname.upper() == cluster_name.upper():
                canonical = cname
                break
        if not canonical:
            canonical = cluster_name

        # Clean sample text (strip base64 refs)
        sample_text = _clean_dna(chunk)

        if canonical not in clusters:
            clusters[canonical] = []
        clusters[canonical].append(sample_text)

    return clusters


def get_cluster_status(voice_dna: str) -> dict:
    """
    Return calibration status per cluster.

    Returns: {"Corporate Affairs": {"count": 3, "status": "FORTIFIED"}, ...}
    Status: count >= 3 = FORTIFIED, count >= 1 = UNSTABLE, count == 0 = EMPTY
    """
    result = {}
    voice_upper = (voice_dna or "").upper()

    for cname in VOICE_CLUSTER_NAMES:
        count = voice_upper.count(f"CLUSTER: {cname.upper()}")
        if count >= 3:
            status = "FORTIFIED"
        elif count >= 1:
            status = "UNSTABLE"
        else:
            status = "EMPTY"
        result[cname] = {"count": count, "status": status}

    return result


# ---------------------------------------------------------------------------
# Message House builder (moved from app.py — verbatim logic)
# ---------------------------------------------------------------------------

def build_mh_context(inputs: dict) -> str:
    """
    Build the MESSAGE HOUSE block for AI prompts.
    Only includes populated fields. Returns empty string if no MH data.
    """
    mh_parts = []

    brand_promise = inputs.get("mh_brand_promise", "").strip()
    if brand_promise:
        mh_parts.append(f"BRAND PROMISE:\n{brand_promise}")

    pillars_json = inputs.get("mh_pillars_json", "")
    if pillars_json:
        try:
            pillars = json.loads(pillars_json)
            pillar_lines = []
            for i, p in enumerate(pillars, 1):
                name = p.get("name", "").strip()
                if not name:
                    continue
                pillar_lines.append(f"PILLAR {i}: {name}")
                if p.get("tagline", "").strip():
                    pillar_lines.append(f"  Tagline: {p['tagline'].strip()}")
                if p.get("headline_claim", "").strip():
                    pillar_lines.append(f"  Claim: {p['headline_claim'].strip()}")
                pps = [
                    p.get(f"proof_{j}", "").strip()
                    for j in range(1, 4)
                    if p.get(f"proof_{j}", "").strip()
                ]
                if pps:
                    pillar_lines.append("  Proof Points:")
                    for pp in pps:
                        pillar_lines.append(f"  - {pp}")
            if pillar_lines:
                mh_parts.append("MESSAGE PILLARS:\n" + "\n".join(pillar_lines))
        except (json.JSONDecodeError, TypeError):
            pass

    for field_key, label in [
        ("mh_founder_positioning", "FOUNDER POSITIONING"),
        ("mh_pov", "POV STATEMENT"),
        ("mh_boilerplate", "BOILERPLATE"),
    ]:
        val = inputs.get(field_key, "").strip()
        if val:
            mh_parts.append(f"{label}: {val}")

    guardrail_parts = []
    for field_key, label in [
        ("mh_offlimits", "Off-limits"),
        ("mh_preapproval_claims", "Pre-approval required"),
        ("mh_tone_constraints", "Tone constraints"),
    ]:
        val = inputs.get(field_key, "").strip()
        if val:
            guardrail_parts.append(f"{label}: {val}")
    if guardrail_parts:
        mh_parts.append("MESSAGING GUARDRAILS:\n" + "\n".join(guardrail_parts))

    if not mh_parts:
        return ""

    return (
        "\n=== MESSAGE HOUSE (AUTHORITATIVE DOCUMENT) ===\n\n"
        + "\n\n".join(mh_parts)
        + "\n\n=== END MESSAGE HOUSE ===\n"
    )


# ---------------------------------------------------------------------------
# Calibration & degradation block builder
# ---------------------------------------------------------------------------

def _build_completeness_block(
    inputs: dict,
    cluster_filter: str | None,
    cluster_statuses: dict,
) -> str:
    """Build the DATA COMPLETENESS section with degradation notices."""
    lines = ["\n=== DATA COMPLETENESS ==="]

    # Voice cluster status
    cluster_lines = []
    for cname in VOICE_CLUSTER_NAMES:
        cs = cluster_statuses.get(cname, {"count": 0, "status": "EMPTY"})
        cluster_lines.append(f"  {cname}: {cs['status']} ({cs['count']} samples)")
    lines.append("Voice Clusters:")
    lines.extend(cluster_lines)

    # Message house completeness
    filled, total = _count_mh_fields(inputs)
    lines.append(f"Message House: {filled}/{total} fields populated")

    # Degradation notices
    notices = []
    voice_dna = inputs.get("voice_dna", "").strip()
    if not voice_dna:
        notices.append(
            "No voice samples calibrated. Output follows brand strategy "
            "and tone keywords only."
        )
    elif cluster_filter:
        cs = cluster_statuses.get(cluster_filter, {"count": 0, "status": "EMPTY"})
        if cs["status"] == "EMPTY":
            notices.append(
                f"No samples for {cluster_filter}. Using all available "
                "voice samples as general reference."
            )
        elif cs["status"] == "UNSTABLE":
            notices.append(
                f"Only {cs['count']} sample(s) for {cluster_filter}. "
                "Output stability may be limited."
            )

    if filled == 0:
        notices.append(
            "No message house configured. Pillar alignment and proof point "
            "checks unavailable."
        )
    if not inputs.get("wiz_guardrails", "").strip():
        notices.append(
            "No guardrails defined. Cannot enforce forbidden language rules."
        )
    if not inputs.get("wiz_tone", "").strip():
        notices.append(
            "No tone keywords defined. Voice matching relies on DNA samples only."
        )

    if notices:
        lines.append("Notices:")
        for notice in notices:
            lines.append(f"  - {notice}")

    lines.append("=== END DATA COMPLETENESS ===")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def build_brand_context(
    brand_data: dict,
    include_voice_samples: bool = True,
    cluster_filter: str | None = None,
) -> str:
    """
    Build the complete brand context string for AI module prompts.

    Args:
        brand_data: The profile_data dict (must have 'inputs' key).
        include_voice_samples: Whether to include voice_dna samples.
        cluster_filter: If set, only include voice samples from this cluster.
            Falls back to all samples if the specified cluster has no data.

    Returns:
        Formatted brand context string ready for injection into prompts.
    """
    inputs = brand_data.get("inputs", {})
    sections = []

    # --- Brand identity ---
    name = inputs.get("wiz_name", "").strip()
    header = f"=== BRAND PROFILE: {name} ===" if name else "=== BRAND PROFILE ==="
    sections.append(header)

    identity_lines = []
    archetype = inputs.get("wiz_archetype", "").strip()
    if archetype:
        identity_lines.append(f"ARCHETYPE: {archetype}")
    tone = inputs.get("wiz_tone", "").strip()
    if tone:
        identity_lines.append(f"TONE KEYWORDS: {tone}")
    if identity_lines:
        sections.append("\n".join(identity_lines))

    # --- Strategy ---
    strategy_lines = []
    mission = inputs.get("wiz_mission", "").strip()
    if mission:
        strategy_lines.append(f"Mission: {mission}")
    values = inputs.get("wiz_values", "").strip()
    if values:
        strategy_lines.append(f"Core Values: {values}")
    if strategy_lines:
        sections.append("STRATEGY:\n" + "\n".join(strategy_lines))

    # --- Brand guardrails ---
    guardrails = inputs.get("wiz_guardrails", "").strip()
    if guardrails:
        sections.append(f"BRAND GUARDRAILS:\n{guardrails}")

    # --- Message house ---
    mh_block = build_mh_context(inputs)
    if mh_block:
        sections.append(mh_block)

    # --- Voice samples ---
    if include_voice_samples:
        voice_dna = inputs.get("voice_dna", "").strip()
        if voice_dna:
            cluster_statuses = get_cluster_status(voice_dna)
            voice_section = _build_voice_section(
                voice_dna, cluster_filter, cluster_statuses
            )
            if voice_section:
                sections.append(voice_section)

    # --- Data completeness ---
    voice_dna_raw = inputs.get("voice_dna", "").strip()
    cluster_statuses = get_cluster_status(voice_dna_raw)
    completeness = _build_completeness_block(inputs, cluster_filter, cluster_statuses)
    sections.append(completeness)

    sections.append("=== END BRAND PROFILE ===")

    return "\n\n".join(sections)


def _build_voice_section(
    voice_dna: str,
    cluster_filter: str | None,
    cluster_statuses: dict,
) -> str:
    """Build the voice samples section with optional cluster filtering."""
    if not voice_dna:
        return ""

    if cluster_filter:
        cs = cluster_statuses.get(cluster_filter, {"count": 0, "status": "EMPTY"})
        if cs["count"] > 0:
            # Filter to just this cluster's samples
            clusters = parse_voice_clusters(voice_dna)
            samples = clusters.get(cluster_filter, [])
            if samples:
                header = (
                    f"=== VOICE REFERENCE SAMPLES ({cluster_filter} cluster) ==="
                )
                body = "\n\n---\n\n".join(samples)
                footer = "=== END VOICE SAMPLES ==="
                return f"{header}\n\n{body}\n\n{footer}"

        # Cluster is empty — fall back to all available samples
        cleaned = _clean_dna(voice_dna)
        if cleaned.strip():
            header = (
                "=== VOICE REFERENCE SAMPLES (all available clusters) ===\n"
                f"NOTE: No samples available for {cluster_filter}. "
                "Including all voice samples for general reference."
            )
            footer = "=== END VOICE SAMPLES ==="
            return f"{header}\n\n{cleaned}\n\n{footer}"

        return ""

    # No filter — include everything (cleaned)
    cleaned = _clean_dna(voice_dna)
    if cleaned.strip():
        header = "=== VOICE REFERENCE SAMPLES ==="
        footer = "=== END VOICE SAMPLES ==="
        return f"{header}\n\n{cleaned}\n\n{footer}"

    return ""


def build_social_context(brand_data: dict) -> str:
    """
    Build brand context for the Social Assistant.

    Uses social_dna as primary DNA (instead of voice_dna), plus includes
    Brand Marketing voice cluster samples for tone alignment.
    """
    inputs = brand_data.get("inputs", {})
    sections = []

    # --- Brand identity ---
    name = inputs.get("wiz_name", "").strip()
    header = f"=== BRAND PROFILE: {name} ===" if name else "=== BRAND PROFILE ==="
    sections.append(header)

    identity_lines = []
    archetype = inputs.get("wiz_archetype", "").strip()
    if archetype:
        identity_lines.append(f"ARCHETYPE: {archetype}")
    tone = inputs.get("wiz_tone", "").strip()
    if tone:
        identity_lines.append(f"TONE KEYWORDS: {tone}")
    if identity_lines:
        sections.append("\n".join(identity_lines))

    # --- Strategy ---
    strategy_lines = []
    mission = inputs.get("wiz_mission", "").strip()
    if mission:
        strategy_lines.append(f"Mission: {mission}")
    values = inputs.get("wiz_values", "").strip()
    if values:
        strategy_lines.append(f"Core Values: {values}")
    if strategy_lines:
        sections.append("STRATEGY:\n" + "\n".join(strategy_lines))

    # --- Brand guardrails ---
    guardrails = inputs.get("wiz_guardrails", "").strip()
    if guardrails:
        sections.append(f"BRAND GUARDRAILS:\n{guardrails}")

    # --- Message house ---
    mh_block = build_mh_context(inputs)
    if mh_block:
        sections.append(mh_block)

    # --- Social DNA (primary for social module) ---
    social_dna = _clean_dna(inputs.get("social_dna", ""))
    if social_dna.strip():
        sections.append(
            "=== SOCIAL MEDIA DNA (SUCCESSFUL PATTERNS) ===\n\n"
            + social_dna
            + "\n\n=== END SOCIAL MEDIA DNA ==="
        )

    # --- Brand Marketing voice samples (secondary tone reference) ---
    voice_dna = inputs.get("voice_dna", "").strip()
    if voice_dna:
        clusters = parse_voice_clusters(voice_dna)
        bm_samples = clusters.get("Brand Marketing", [])
        if bm_samples:
            sections.append(
                "=== BRAND VOICE REFERENCE (Brand Marketing cluster) ===\n\n"
                + "\n\n---\n\n".join(bm_samples)
                + "\n\n=== END BRAND VOICE REFERENCE ==="
            )

    # --- Data completeness ---
    cluster_statuses = get_cluster_status(voice_dna)
    # Social-specific notices
    completeness_lines = ["\n=== DATA COMPLETENESS ==="]

    # Social data status
    social_raw = inputs.get("social_dna", "")
    s_count = social_raw.upper().count("[ASSET:") if social_raw else 0
    if s_count >= 3:
        completeness_lines.append(f"Social Samples: FORTIFIED ({s_count} samples)")
    elif s_count >= 1:
        completeness_lines.append(f"Social Samples: UNSTABLE ({s_count} sample(s))")
    else:
        completeness_lines.append("Social Samples: EMPTY (0 samples)")

    # Voice cluster status
    completeness_lines.append("Voice Clusters:")
    for cname in VOICE_CLUSTER_NAMES:
        cs = cluster_statuses.get(cname, {"count": 0, "status": "EMPTY"})
        completeness_lines.append(
            f"  {cname}: {cs['status']} ({cs['count']} samples)"
        )

    # MH completeness
    filled, total = _count_mh_fields(inputs)
    completeness_lines.append(f"Message House: {filled}/{total} fields populated")

    # Social-specific degradation notices
    notices = []
    if s_count == 0:
        notices.append(
            "No social media samples uploaded. Output based on general "
            "brand voice, not social-specific patterns."
        )
    if not voice_dna:
        notices.append(
            "No voice samples calibrated. Tone alignment relies on "
            "tone keywords only."
        )
    if filled == 0:
        notices.append(
            "No message house configured. Pillar alignment unavailable."
        )
    if not inputs.get("wiz_guardrails", "").strip():
        notices.append(
            "No guardrails defined. Cannot enforce forbidden language rules."
        )

    if notices:
        completeness_lines.append("Notices:")
        for notice in notices:
            completeness_lines.append(f"  - {notice}")

    completeness_lines.append("=== END DATA COMPLETENESS ===")
    sections.append("\n".join(completeness_lines))

    sections.append("=== END BRAND PROFILE ===")

    return "\n\n".join(sections)
