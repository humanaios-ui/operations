"""Repository-local governance and resource tooling.

An explicit package boundary makes `from tools.<module> import ...` resolve
against this versioned repository tree rather than an unrelated installed
third-party `tools` package during pytest collection.
"""
