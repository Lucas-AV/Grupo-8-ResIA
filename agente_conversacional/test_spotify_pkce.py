from spotify_auth.pkce import generate_code_challenge, generate_code_verifier, generate_state


def test_generate_code_verifier_is_url_safe_and_within_rfc7636_length():
    verifier = generate_code_verifier()

    assert 43 <= len(verifier) <= 128
    assert all(c.isalnum() or c in "-_" for c in verifier)


def test_generate_code_verifier_is_unique_per_call():
    assert generate_code_verifier() != generate_code_verifier()


def test_generate_code_challenge_matches_rfc7636_test_vector():
    # Vetor de teste oficial da RFC 7636, apendice B.
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"

    assert generate_code_challenge(verifier) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


def test_generate_state_is_unique_per_call():
    assert generate_state() != generate_state()
