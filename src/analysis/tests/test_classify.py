from app import config
from app.classify import classify_band


def base_features(**overrides):
    f = {
        "column_count": 1,
        "repeat_count": 1,
        "image_position": "none",
        "alignment": "left",
        "heading_scale": 1.0,
        "bg_color_hex": "#ffffff",
        "bg_luminance": 1.0,
        "accent_color_hex": None,
        "height_ratio": 0.5,
        "position": "other",
        "text_blob_count": 0,
        "max_text_blob_height": 0,
        "median_text_blob_height": 0,
        "button_blob_count": 0,
        "icon_blob_count": 0,
        "image_blob_count": 0,
        "circular_image_blob_count": 0,
    }
    f.update(overrides)
    return f


def test_header_adopted_when_first_and_thin_with_nav_text():
    features = base_features(position="first", height_ratio=0.05, text_blob_count=4, icon_blob_count=1)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    assert kind == "header"
    assert confidence >= config.CONFIDENCE_ADOPT_THRESHOLD


def test_header_not_adopted_when_not_first_even_if_shape_matches():
    features = base_features(position="other", height_ratio=0.05, text_blob_count=4, icon_blob_count=1)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=["header" if False else k for k in config.SECTION_KINDS])
    assert kind != "header"


def test_footer_not_adopted_when_not_last():
    features = base_features(position="other", text_blob_count=6, column_count=3)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    assert kind != "footer"


def test_footer_adopted_when_last_with_multi_column_links():
    features = base_features(position="last", text_blob_count=8, column_count=3)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    assert kind == "footer"


def test_gallery_adopted_for_many_images_little_text():
    features = base_features(image_blob_count=6, column_count=3, text_blob_count=0)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    assert kind == "gallery"


def test_faq_adopted_for_single_column_repeated_rows_with_icons():
    features = base_features(column_count=1, repeat_count=5, icon_blob_count=5, text_blob_count=10)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    assert kind == "faq"


def test_low_confidence_records_notice_between_0_4_and_0_6():
    # 部分的にしか特徴が一致しない曖昧な帯
    features = base_features(position="last", text_blob_count=3, column_count=1)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    if config.CONFIDENCE_LOW_THRESHOLD <= confidence < config.CONFIDENCE_ADOPT_THRESHOLD:
        assert any(n["notice_type"] == config.NOTICE_LOW_CONFIDENCE_KIND for n in notices)


def test_falls_back_to_generic_text_when_all_scores_low():
    features = base_features()  # 何の特徴も無い帯
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    assert kind == "generic_text"
    assert any(n["notice_type"] == config.NOTICE_GENERIC_TEXT_FALLBACK for n in notices)


def test_records_close_confidence_runner_up_when_top_two_within_0_05():
    features = base_features(column_count=1, repeat_count=5, icon_blob_count=5, text_blob_count=10)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    # runner_up が設定されている場合はnoticeも必ず記録されていること
    if runner_up is not None:
        assert any(n["notice_type"] == config.NOTICE_CLOSE_CONFIDENCE_RUNNER_UP for n in notices)


def test_pricing_and_feature_list_both_rejected_when_missing_required_signal():
    # 列数はあるがボタンもアイコンも無い曖昧な帯 → pricingにもfeature_listにも採用されない
    features = base_features(column_count=3, repeat_count=3, text_blob_count=3)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    assert kind not in ("pricing", "feature_list")


def test_pricing_adopted_when_each_column_has_button():
    features = base_features(column_count=3, repeat_count=3, button_blob_count=3, text_blob_count=6)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    assert kind == "pricing"


def test_feature_list_adopted_when_each_item_has_icon():
    features = base_features(column_count=3, repeat_count=3, icon_blob_count=3, text_blob_count=6)
    kind, confidence, runner_up, notices = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    assert kind == "feature_list"


def test_is_deterministic():
    features = base_features(column_count=3, repeat_count=3, button_blob_count=3, text_blob_count=6)
    r1 = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    r2 = classify_band(features, allowed_kinds=config.SECTION_KINDS)
    assert r1 == r2
