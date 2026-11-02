"""EXPERIMENT-ONLY research code. Nothing under production paths may import this package.

The token-attractor pilot recorded a NEGATIVE result (see docs/TOKEN_ATTRACTOR_NEGATIVE_RESULT.md):
hand-authored concept expansion did not beat a plain-word baseline, and the transfer-hypothesis
layer added no useful match. Concept expansion and transfer-hypothesis matching are therefore OFF
by default and need two explicit keys (a function argument AND an environment variable).

Scope of that guarantee: it stops accidental use through the sanctioned entry points. It is a
guardrail, not a security boundary; code that reads the vocabulary directly can still build a
predicate by hand. The existing Resource Miner plain-word matcher (needs.py, intent_os.py) is the
production path and is untouched.
"""
