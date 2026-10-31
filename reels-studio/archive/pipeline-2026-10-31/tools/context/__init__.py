"""Bounded-context session tooling for the interactive Arena agent.

Keeps a session's conversation small: one compact pack instead of whole-document
reads (ctxpack.py), capped retrieval instead of file dumps (ctxgrep.py), and
bounded tool output instead of raw logs (quiet.py).

Protocol: reels-studio/CONTEXT-PROTOCOL.md
"""
