# Protobuf compatibility exercises

The existing `User` field numbers are unchanged. `nickname = 4` and `address = 5`
are additive fields, so an older client can still decode the message and simply
ignore those fields.

To regenerate both runtimes:

```bash
uv run python generate_proto.py
cd frontend
npm run generate:proto
```

The tests in `test_backend.py` verify serialization of the new fields and the
standard `NOT_FOUND` error for an unknown user.

## Python environment

Install and run the backend with `uv`:

```bash
uv sync
uv run python server.py
uv run python test_backend.py
uv run python client_stream_test.py
```