import qr_page


def test_render_qr_page_embeds_svg_code_and_frontend_url():
    html = qr_page.render_qr_page("data:image/svg+xml;base64,AAA", "code123", "http://example.com/")

    assert "data:image/svg+xml;base64,AAA" in html
    assert 'const code = "code123";' in html
    assert 'const frontendUrl = "http://example.com/";' in html
    assert "/api/pair/${code}/status" in html


def test_render_qr_page_redirects_to_frontend_on_completed():
    html = qr_page.render_qr_page("data:x", "code123", "http://example.com/")

    assert 'data.status === "completed"' in html
    assert "window.location.href = frontendUrl" in html


def test_render_qr_page_reloads_on_expired_or_not_found():
    html = qr_page.render_qr_page("data:x", "code123", "http://example.com/")

    assert 'data.status === "expired"' in html
    assert 'data.status === "not_found"' in html
    assert "window.location.reload()" in html


def test_render_pair_error_page_for_expired():
    html = qr_page.render_pair_error_page("expired")

    assert "expirou" in html
    assert '<a href="/login/qr">' in html


def test_render_pair_error_page_for_not_found():
    html = qr_page.render_pair_error_page("not_found")

    assert "não é válido" in html


def test_render_pair_error_page_for_unknown_status_has_generic_message():
    html = qr_page.render_pair_error_page("weird_status")

    assert "Não foi possível continuar" in html
