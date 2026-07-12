"""Output buffering tests."""

import threading

from core import console


def test_capture_buffers_and_replay_emits_in_order():
    received = []
    console.subscribe(lambda text, level: received.append((text, level)))
    try:
        with console.capture() as lines:
            console.cprint("inside the buffer", level="success")
        assert received == []
        assert len(lines) == 1

        console.replay(lines)
        assert received == [("inside the buffer", "success")]
    finally:
        console._subscribers.clear()


def test_capture_is_thread_local():
    """One thread's buffer never captures another thread's output."""
    received = []
    console.subscribe(lambda text, level: received.append(text))
    barrier = threading.Barrier(2)

    def worker():
        with console.capture() as lines:
            barrier.wait()
            console.cprint("from the worker thread")
        assert lines == ["info:from the worker thread"]

    thread = threading.Thread(target=worker)
    thread.start()
    try:
        barrier.wait()
        console.cprint("from the main thread")
        thread.join()
        assert received == ["from the main thread"]
    finally:
        console._subscribers.clear()


def test_nested_capture_restores_previous_buffer():
    with console.capture() as outer:
        console.cprint("a")
        with console.capture() as inner:
            console.cprint("b")
        console.cprint("c")
    assert inner == ["info:b"]
    assert outer == ["info:a", "info:c"]


def test_level_controls_subscriber_output():
    received = []
    console.subscribe(lambda text, level: received.append((text, level)))
    try:
        with console.capture() as lines:
            console.cprint("all good", level="success")
            console.cprint("watch out", level="warning")
            console.cprint("broken", level="error")
        console.replay(lines)
        assert received == [
            ("all good", "success"),
            ("watch out", "warning"),
            ("broken", "error"),
        ]
    finally:
        console._subscribers.clear()


def test_style_does_not_affect_level_sent_to_subscribers():
    """style= overrides terminal color but subscribers still get the level."""
    received = []
    console.subscribe(lambda text, level: received.append((text, level)))
    try:
        with console.capture() as lines:
            console.cprint("etsy banner", level="header", style="green")
        console.replay(lines)
        assert received == [("etsy banner", "header")]
    finally:
        console._subscribers.clear()
