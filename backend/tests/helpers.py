def assert_envelope(response, status_code=200):
    assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"
    body = response.json()
    assert "success" in body, f"Missing 'success' field: {body}"
    assert "data" in body, f"Missing 'data' field: {body}"
    assert body["success"] is True, f"Expected success=True: {body}"
    return body["data"]


def assert_envelope_list(response, status_code=200, min_count=None, max_count=None):
    data = assert_envelope(response, status_code)
    assert isinstance(data, list), f"Expected list, got {type(data)}: {data}"
    body = response.json()
    assert "meta" in body, f"Missing 'meta' field: {body}"
    if min_count is not None:
        assert len(data) >= min_count, f"Expected >= {min_count} items, got {len(data)}"
    if max_count is not None:
        assert len(data) <= max_count, f"Expected <= {max_count} items, got {len(data)}"
    return data


def assert_error(response, status_code, error_code=None):
    assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"
    body = response.json()
    assert "success" in body, f"Missing 'success' field: {body}"
    assert body["success"] is False, f"Expected success=False: {body}"
    assert "error" in body, f"Missing 'error' field: {body}"
    error = body["error"]
    assert "code" in error, f"Missing 'code' in error: {error}"
    assert "message" in error, f"Missing 'message' in error: {error}"
    if error_code:
        assert error["code"] == error_code, f"Expected error code '{error_code}', got '{error['code']}'"
    return error


def assert_paginated(response, status_code=200):
    data = assert_envelope_list(response, status_code)
    body = response.json()
    meta = body["meta"]
    assert "cursor" in meta or "total" in meta, f"Missing pagination info in meta: {meta}"
    return data, meta
