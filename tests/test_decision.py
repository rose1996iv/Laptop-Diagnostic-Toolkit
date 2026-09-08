from laptop_diagnostic.core.decision import condition_indicators, purchase_decision, value_index


def test_value_and_purchase_decision_use_supplied_price():
    assert value_index(88, 84999) == 1.035
    result = purchase_decision(88, 84999, confidence=90)
    assert result["decision"] == "BUY"
    assert result["recommended_range"] is None


def test_condition_analysis_stays_cautious_when_data_is_missing():
    assert condition_indicators()["classification"] == "UNVERIFIED"
    assert condition_indicators(storage_power_on_hours=1200)["classification"] == "POSSIBLY USED"