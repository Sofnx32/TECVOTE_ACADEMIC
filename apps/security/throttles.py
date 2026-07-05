from rest_framework.throttling import ScopedRateThrottle


class LoginRateThrottle(ScopedRateThrottle):
    scope = "login"


class VoteCastRateThrottle(ScopedRateThrottle):
    scope = "vote_cast"


class ReceiptVerifyRateThrottle(ScopedRateThrottle):
    scope = "receipt_verify"