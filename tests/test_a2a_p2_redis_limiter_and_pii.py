import pytest
from core.redis_rate_limiter import RedisDistributedRateLimiter
from core.pii_scrubber import IngestionPIIScrubber


def test_redis_distributed_rate_limiter_token_bucket():
    limiter = RedisDistributedRateLimiter(capacity=3, refill_rate_per_sec=1.0)

    # 3 requests allowed
    s1 = limiter.check_rate_limit("client_1")
    s2 = limiter.check_rate_limit("client_1")
    s3 = limiter.check_rate_limit("client_1")
    assert s1.allowed
    assert s2.allowed
    assert s3.allowed

    # 4th request rejected
    s4 = limiter.check_rate_limit("client_1")
    assert not s4.allowed
    assert s4.reset_after_sec > 0.0


def test_ingestion_pii_scrubber_masks_secrets_and_pii():
    raw_payload = {
        "user_email": "grzegorz@example.com",
        "api_key": "secret: 'sk_live_1234567890abcdef'",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123def456",
        "nested": {
            "credit_card": "4111 1111 1111 1111"
        }
    }

    scrubbed = IngestionPIIScrubber.scrub_payload(raw_payload)

    assert "[REDACTED_EMAIL]" in str(scrubbed)
    assert "[REDACTED_SECRET]" in str(scrubbed)
    assert "[REDACTED_JWT_TOKEN]" in str(scrubbed)
    assert "[REDACTED_CREDIT_CARD]" in str(scrubbed)
