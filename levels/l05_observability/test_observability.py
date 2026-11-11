import io
import json
import logging
import sys
from datetime import datetime

import pytest

from levels.l05_observability.observability import (
    JsonFormatter,
    Window,
    burn_rate,
    percentile,
    request_context,
    request_id_var,
    should_page,
)


@pytest.fixture
def capture() -> tuple[logging.Logger, io.StringIO]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("test.zoo")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    return logger, stream


def lines(stream: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_request_context_binds_and_restores() -> None:
    assert request_id_var.get() is None
    with request_context("req-1") as rid:
        assert rid == "req-1" and request_id_var.get() == "req-1"
        with request_context("req-2"):
            assert request_id_var.get() == "req-2"
        assert request_id_var.get() == "req-1", "nested contexts must restore the outer id"
    assert request_id_var.get() is None


def test_request_context_generates_an_id() -> None:
    with request_context() as rid:
        assert len(rid) == 32 and request_id_var.get() == rid


class HandlerCrash(Exception):
    pass


def test_request_context_restores_on_error() -> None:
    with pytest.raises(HandlerCrash), request_context("req-1"):
        assert request_id_var.get() == "req-1"
        raise HandlerCrash("boom")
    assert request_id_var.get() is None


def test_log_line_is_json_with_core_fields(capture: tuple[logging.Logger, io.StringIO]) -> None:
    logger, stream = capture
    with request_context("req-42"):
        logger.warning("sloth is slow: %d ms", 1200)
    [line] = lines(stream)
    assert line["message"] == "sloth is slow: 1200 ms"
    assert line["level"] == "WARNING"
    assert line["logger"] == "test.zoo"
    assert line["request_id"] == "req-42"
    assert datetime.fromisoformat(str(line["ts"])).utcoffset().total_seconds() == 0


def test_log_line_merges_fields(capture: tuple[logging.Logger, io.StringIO]) -> None:
    logger, stream = capture
    logger.info("served", extra={"fields": {"path": "/sloth", "status": 200}})
    [line] = lines(stream)
    assert line["path"] == "/sloth" and line["status"] == 200
    assert line["request_id"] is None


def test_log_line_includes_exception(capture: tuple[logging.Logger, io.StringIO]) -> None:
    logger, stream = capture
    try:
        raise ValueError("bad banana")
    except ValueError:
        logger.error("failed", exc_info=sys.exc_info())
    [line] = lines(stream)
    assert "ValueError: bad banana" in str(line["exc"])


def test_line_without_exception_has_no_exc_key(capture: tuple[logging.Logger, io.StringIO]) -> None:
    logger, stream = capture
    logger.info("ok")
    assert "exc" not in lines(stream)[0]


def test_percentile_nearest_rank() -> None:
    values = list(range(1, 101))
    assert percentile(values, 95) == 95
    assert percentile(values, 50) == 50
    assert percentile(values, 100) == 100
    assert percentile([4, 1, 3, 2], 50) == 2
    assert percentile([7], 99) == 7


def test_percentile_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        percentile([], 50)
    with pytest.raises(ValueError):
        percentile([1, 2], 0)


def test_burn_rate() -> None:
    assert burn_rate(Window(total=1000, errors=1), 0.999) == pytest.approx(1.0)
    assert burn_rate(Window(total=1000, errors=50), 0.99) == pytest.approx(5.0)
    assert burn_rate(Window(total=0, errors=0), 0.99) == 0.0


def test_should_page_needs_both_windows() -> None:
    incident = Window(total=1000, errors=300)
    calm = Window(total=10_000, errors=5)
    sustained = Window(total=10_000, errors=500)
    assert should_page(short=incident, long=sustained, slo_target=0.999)
    assert not should_page(short=incident, long=calm, slo_target=0.999), "a blip must not page"
    assert not should_page(
        short=Window(1000, 0), long=sustained, slo_target=0.999
    ), "an incident that already ended must not page"
