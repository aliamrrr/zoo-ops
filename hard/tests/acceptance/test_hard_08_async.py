"""Ticket 08: the stuck robot crew, and the silent Owl."""

from zp_testkit import World, auth, parse_sse


def report(world: World, pen: str) -> None:
    assert (
        world.client.post(
            f"/v1/pens/{pen}/incidents", json={"kind": "dirty"}, headers=auth()
        ).status_code
        == 202
    )


def drain(world: World) -> None:
    world.client.post("/internal/worker/drain")


def dirty(world: World, pen: str) -> bool:
    return bool(world.client.get(f"/v1/pens/{pen}", headers=auth()).json()["dirty"])


def test_a_busy_crew_is_retried_after_a_delay(world: World) -> None:
    world.crew.busy["pen-lion"] = 1
    report(world, "pen-lion")
    drain(world)
    drain(world)
    assert dirty(world, "pen-lion")
    assert world.crew.dispatched == ["pen-lion"], "a failed job must wait before its retry"
    world.clock.advance(1)
    drain(world)
    assert not dirty(world, "pen-lion")


def test_poison_jobs_end_in_the_dead_letter_queue(world: World) -> None:
    world.crew.busy["pen-otter"] = -1
    report(world, "pen-otter")
    for _ in range(6):
        drain(world)
        world.clock.advance(10)
    assert world.crew.dispatched.count("pen-otter") == 3
    letters = world.client.get("/internal/dead-letters").json()
    assert len(letters) == 1
    assert letters[0]["kind"] == "clean_pen"
    assert letters[0]["attempts"] == 3
    assert "busy" in letters[0]["last_error"].lower()


def test_a_poison_job_does_not_block_the_others(world: World) -> None:
    world.crew.busy["pen-otter"] = -1
    report(world, "pen-otter")
    report(world, "pen-lion")
    drain(world)
    assert not dirty(world, "pen-lion")


def stream(world: World, question: str) -> tuple[str, list[dict[str, str]]]:
    response = world.client.get("/v1/owl/stream", params={"question": question}, headers=auth())
    assert response.status_code == 200
    return response.headers.get("content-type", ""), parse_sse(response.text)


def test_answers_stream_as_server_sent_events(world: World) -> None:
    content_type, events = stream(world, "Why do otters hold hands?")
    assert content_type.startswith("text/event-stream")
    tokens = [event for event in events if event["event"] == "token"]
    assert len(tokens) > 3
    assert (
        "".join(event["data"] for event in tokens)
        == "owl says: Sea otters hold hands while they sleep."
    )
    assert events[-1]["event"] == "done"


def test_multi_line_answers_survive_the_stream(world: World) -> None:
    world.owl.suffix = "\nThey never drift apart."
    _, events = stream(world, "Why do otters hold hands?")
    text = "".join(event["data"] for event in events if event["event"] == "token")
    assert text.endswith("sleep.\nThey never drift apart.")
