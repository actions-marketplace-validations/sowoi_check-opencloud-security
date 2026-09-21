# Tests

- `tests/fake_opencloud.py` is a real HTTP server driven by an
  `InstanceBehaviour` dataclass — use it rather than mocking `requests`, and
  derive expectations from an actual scan of it (hardcoded lists go stale).
- `tests/conftest.py` has two autouse fixtures: one strips every `COS_`
  environment variable, one stubs `time.sleep` for retry/backoff tests.
- `tests/webapp_support.py` holds web fixtures: an isolated in-process Redis
  per test and an offline resolver (`example.com` doesn't resolve).
- Name tests as sentences describing the behaviour they protect (e.g.
  `test_a_waived_check_no_longer_caps_the_rating`) with a one-line docstring
  explaining why it matters. **Assert the negative case as well as the
  positive one.**
