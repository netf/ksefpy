from ksef.environments import Environment


def test_test_environment_has_correct_api_url():
    assert Environment.TEST.api_base_url == "https://api-test.ksef.mf.gov.pl/v2"


def test_demo_environment_has_correct_api_url():
    assert Environment.DEMO.api_base_url == "https://api-demo.ksef.mf.gov.pl/v2"


def test_production_environment_has_correct_api_url():
    assert Environment.PRODUCTION.api_base_url == "https://api.ksef.mf.gov.pl/v2"


def test_environment_is_frozen():
    env = Environment.TEST
    try:
        env.api_base_url = "https://changed.example.com"  # type: ignore[misc]
        assert False, "Should have raised"
    except AttributeError:
        pass


def test_test_environment_qr_url():
    assert Environment.TEST.qr_base_url == "https://qr-test.ksef.mf.gov.pl"


def test_production_qr_url():
    assert Environment.PRODUCTION.qr_base_url == "https://qr.ksef.mf.gov.pl"
