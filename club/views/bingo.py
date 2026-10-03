from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from club.decorators import member_required
from club.services.bingo import GRID_SIZE, complete_lines, existing_grid, generate_grid, is_open, square_labels
from club.services.events import attendees, visible_events


@member_required
@require_GET
def event_bingo(request, pk):
    """My « Bingo des rencontres » grid for an event: always MY grid (request.member), never an id from the URL."""
    me = request.member
    event = get_object_or_404(visible_events(me), pk=pk)
    if not event.has_bingo:
        raise Http404
    registered = attendees(event).filter(pk=me.pk).exists()  # who is expected tonight (substitutes included)
    is_over = not is_open(event)
    squares = []
    if registered:
        # Opening the page builds the grid once (idempotent, nothing a visitor can choose). After the event, read-only.
        squares = existing_grid(event, me) if is_over else generate_grid(event, me)
    complete = complete_lines(squares)
    winning_positions = {position for line in complete for position in line}
    found = sum(1 for square in squares if square.found_id is not None)
    context = {
        "event": event,
        "registered": registered,
        "is_over": is_over,
        "cells": [
            {"square": square, "label": label, "found": square.found, "in_line": square.position in winning_positions}
            for square, label in zip(squares, square_labels(squares))
        ],
        "found": found,
        "total": GRID_SIZE,
        "has_line": bool(complete),
        "full_card": found == GRID_SIZE,
    }
    return render(request, "club/event_bingo.html", context)
