import get_active_modems


def test_no_update_html_or_bs4():
    assert not hasattr(get_active_modems, "update_html")
    assert not hasattr(get_active_modems, "BeautifulSoup")


def test_no_count_vms_duplicate_filter():
    assert not hasattr(get_active_modems, "count_vms")
