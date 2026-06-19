# EDIT VALUES BELOW TO CONFIGURE THE BOT
_MAX_BEST_OF:int = 9
_REQUEST_TIMEOUT:float = 120.0


# FUNCTION IMPLEMENTATIONS
def get_max_best_of() -> int:
    return _MAX_BEST_OF

def get_match_request_timeout() -> float:
    return _REQUEST_TIMEOUT