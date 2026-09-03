class LLMCallError(Exception):
    """Raised when a call to an LLM backend fails (network, timeout, or malformed response)."""
