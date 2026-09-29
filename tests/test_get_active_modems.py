import get_active_modems


def test_no_update_html_or_bs4():
    assert not hasattr(get_active_modems, "update_html")
    assert not hasattr(get_active_modems, "BeautifulSoup")


def test_no_count_vms_duplicate_filter():
    assert not hasattr(get_active_modems, "count_vms")


def test_client_is_created_with_a_read_timeout_that_fits_the_full_account(monkeypatch):
    captured = {}
    monkeypatch.setattr(get_active_modems.KitVendingClient, "from_env", classmethod(lambda cls, **kwargs: captured.update(kwargs)))

    get_active_modems.create_client()

    assert captured["timeout"] == get_active_modems.API_TIMEOUT
    assert captured["timeout"][1] >= 600
