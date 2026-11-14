"""Run the graphics test suite without pytest: import every test_* module and call its test_ functions."""
import importlib.util
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class Skipped(Exception):
    """Raised in place of pytest.skip: the test could not run here and that is fine."""


# A minimal pytest stand-in so the modules can be imported without the real package.
if "pytest" not in sys.modules:
    import types
    stub = types.ModuleType("pytest")

    class _Mark:
        def __getattr__(self, _name):
            def deco(*a, **k):
                if a and callable(a[0]) and not k:
                    return a[0]
                return lambda fn: fn
            return deco

    def _skip(*a, **k):
        raise Skipped(" ".join(str(x) for x in a))

    def _importorskip(name, **k):
        raise Skipped(f"no {name} here")

    stub.mark = _Mark()
    stub.skip = _skip
    stub.importorskip = _importorskip
    stub.raises = None
    stub.fixture = lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda fn: fn))
    stub.approx = lambda v, **k: v
    sys.modules["pytest"] = stub

TESTS = ROOT / "graphics" / "tests"
passed, skipped, failed = 0, [], []
for f in sorted(TESTS.glob("test_*.py")):
    spec = importlib.util.spec_from_file_location(f.stem, f)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        failed.append((f.name, "<import>", repr(e), traceback.format_exc()))
        continue
    for name in dir(mod):
        if not name.startswith("test_"):
            continue
        fn = getattr(mod, name)
        if not callable(fn):
            continue
        try:
            fn()
            passed += 1
        except Skipped as e:
            skipped.append((f.name, name, str(e)))
        except Exception as e:
            failed.append((f.name, name, repr(e), traceback.format_exc()))

print(f"passed: {passed}   skipped: {len(skipped)}   failed: {len(failed)}")
for name, test, why in skipped:
    print(f"  SKIP {name}::{test} — {why}")
for name, test, err, tb in failed:
    print(f"\nFAIL {name}::{test}\n  {err}\n{tb}")
sys.exit(1 if failed else 0)
