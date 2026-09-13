"""6.6 種別判定：12種別の重み付き採点としきい値による採用/退避。"""
from app import config


def _score_header(f):
    if f["position"] != "first":
        return 0.0
    s = 0.0
    if f["height_ratio"] <= config.HEADER_MAX_HEIGHT_RATIO:
        s += 0.4
    if f["text_blob_count"] >= 1:
        s += 0.3
    if f["image_blob_count"] >= 1 or f["icon_blob_count"] >= 1:
        s += 0.3
    return s


def _score_hero(f):
    s = 0.0
    if f["height_ratio"] >= 0.25 or f["image_blob_count"] >= 1:
        s += 0.3
    if f["heading_scale"] >= 2.0:
        s += 0.3
    if f["button_blob_count"] >= 1:
        s += 0.2
    if f["image_blob_count"] >= 1:
        s += 0.2
    return s


def _score_feature_list(f):
    if not (2 <= f["column_count"] <= 4):
        return 0.0
    if f["icon_blob_count"] < f["column_count"]:
        return 0.0
    s = 0.4
    if f["repeat_count"] == f["column_count"]:
        s += 0.3
    if f["text_blob_count"] >= f["column_count"]:
        s += 0.3
    return s


def _score_image_and_text(f):
    if f["image_position"] not in ("left", "right"):
        return 0.0
    s = 0.5
    if f["text_blob_count"] >= 1:
        s += 0.3
    if f["column_count"] <= 2:
        s += 0.2
    return s


def _score_cta(f):
    s = 0.0
    if f["height_ratio"] <= 0.15:
        s += 0.3
    if f["alignment"] == "center":
        s += 0.2
    if f["heading_scale"] >= 1.5:
        s += 0.2
    if f["button_blob_count"] == 1:
        s += 0.3
    return s


def _score_pricing(f):
    if not (2 <= f["column_count"] <= 4):
        return 0.0
    if f["button_blob_count"] < f["column_count"]:
        return 0.0
    s = 0.4
    if f["text_blob_count"] >= f["column_count"]:
        s += 0.3
    if f["repeat_count"] == f["column_count"]:
        s += 0.3
    return s


def _score_testimonial(f):
    if f["circular_image_blob_count"] < 1:
        return 0.0
    s = 0.4
    if f["repeat_count"] >= 2:
        s += 0.3
    if f["text_blob_count"] >= f["repeat_count"]:
        s += 0.3
    return s


def _score_faq(f):
    if f["column_count"] != 1:
        return 0.0
    s = 0.0
    if f["repeat_count"] >= 2:
        s += 0.3
    if f["icon_blob_count"] >= f["repeat_count"] * 0.5:
        s += 0.4
    if f["text_blob_count"] >= f["repeat_count"]:
        s += 0.3
    return s


def _score_gallery(f):
    if f["image_blob_count"] < 4:
        return 0.0
    s = 0.6
    if f["text_blob_count"] <= 2:
        s += 0.4
    return s


def _score_logo_strip(f):
    if f["image_blob_count"] < 4:
        return 0.0
    s = 0.5
    if f["height_ratio"] <= 0.10:
        s += 0.3
    if f["text_blob_count"] <= 1:
        s += 0.2
    return s


def _score_footer(f):
    if f["position"] != "last":
        return 0.0
    s = 0.0
    if f["column_count"] >= 2:
        s += 0.5
    if f["text_blob_count"] >= 2:
        s += 0.5
    return s


_SCORERS = {
    "header": _score_header,
    "hero": _score_hero,
    "feature_list": _score_feature_list,
    "image_and_text": _score_image_and_text,
    "cta": _score_cta,
    "pricing": _score_pricing,
    "testimonial": _score_testimonial,
    "faq": _score_faq,
    "gallery": _score_gallery,
    "logo_strip": _score_logo_strip,
    "footer": _score_footer,
}


def classify_band(features: dict, allowed_kinds: list) -> tuple:
    """features -> (kind, confidence, runner_up_kind, notices)"""
    notices = []
    scores = {}
    for kind, scorer in _SCORERS.items():
        scores[kind] = scorer(features) if kind in allowed_kinds else 0.0

    ranked = sorted(scores.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    top_kind, top_score = ranked[0]
    second_kind, second_score = ranked[1] if len(ranked) > 1 else (None, 0.0)

    runner_up_kind = None
    if second_score > 0.0 and (top_score - second_score) <= config.CONFIDENCE_CLOSE_DIFF:
        runner_up_kind = second_kind
        notices.append(
            {
                "notice_type": config.NOTICE_CLOSE_CONFIDENCE_RUNNER_UP,
                "detail": {"runner_up_kind": second_kind},
            }
        )

    if top_score >= config.CONFIDENCE_ADOPT_THRESHOLD:
        kind = top_kind
        confidence = top_score
    elif top_score >= config.CONFIDENCE_LOW_THRESHOLD:
        kind = top_kind
        confidence = top_score
        notices.append({"notice_type": config.NOTICE_LOW_CONFIDENCE_KIND, "detail": {"kind": kind}})
    else:
        kind = "generic_text"
        confidence = top_score
        notices.append(
            {"notice_type": config.NOTICE_GENERIC_TEXT_FALLBACK, "detail": {"best_kind": top_kind}}
        )

    return kind, confidence, runner_up_kind, notices
