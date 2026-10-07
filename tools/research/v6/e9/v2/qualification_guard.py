"""Pytest execution guard for explicitly audited synthetic qualification only."""
from __future__ import annotations

import os
import random
import secrets

import pytest


def forbidden(*args, **kwargs):
    raise AssertionError("synthetic qualification attempted prohibited entropy or match execution")


@pytest.fixture(autouse=True)
def prohibit_experiment_producers(monkeypatch):
    from battle_engine.match_service import NativeMatchService
    from battle_engine.process_runtime import ProcessMatchController

    from tools.research.v6.e9 import analysis
    monkeypatch.setattr(os, "urandom", forbidden)
    # random.SystemRandom (and so secrets.choice) binds os.urandom at import time.
    monkeypatch.setattr(random, "_urandom", forbidden)
    monkeypatch.setattr(secrets, "token_bytes", forbidden)
    monkeypatch.setattr(secrets, "randbits", forbidden)
    monkeypatch.setattr(secrets, "randbelow", forbidden)
    monkeypatch.setattr(NativeMatchService, "run", forbidden)
    monkeypatch.setattr(ProcessMatchController, "run", forbidden)
    monkeypatch.setattr(analysis, "uncertainty", forbidden)
    monkeypatch.setattr(analysis, "registered_uncertainty", forbidden)
