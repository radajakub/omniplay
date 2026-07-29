__all__ = ["OmniPlay"]


# Lazily expose OmniPlay so `from omniplay import OmniPlay` works (the intended entry point when using
# the package as an application) WITHOUT importing the whole graph -- app -> registry/games -> engine ->
# pyspiel, and the LLM providers -- on every `import omniplay.<submodule>`. Internal code imports
# submodules directly, so it stays decoupled and light. This is the standard PEP 562 module __getattr__.
def __getattr__(name: str) -> object:
    if name == "OmniPlay":
        from omniplay.app import OmniPlay

        return OmniPlay
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
