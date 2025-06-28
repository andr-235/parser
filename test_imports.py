#!/usr/bin/env python3
"""
Simple import test for technology validation
"""


def test_imports():
    results = {}

    try:
        import fastapi

        results["fastapi"] = f"✅ {fastapi.__version__}"
    except ImportError as e:
        results["fastapi"] = f"❌ {e}"

    try:
        import uvicorn

        results["uvicorn"] = f"✅ {uvicorn.__version__}"
    except ImportError as e:
        results["uvicorn"] = f"❌ {e}"

    try:
        import pydantic

        results["pydantic"] = f"✅ {pydantic.__version__}"
    except ImportError as e:
        results["pydantic"] = f"❌ {e}"

    try:
        import starlette

        results["starlette"] = f"✅ {starlette.__version__}"
    except ImportError as e:
        results["starlette"] = f"❌ {e}"

    return results


if __name__ == "__main__":
    print("🔍 Technology Validation - Import Test")
    print("=" * 50)

    results = test_imports()

    for package, status in results.items():
        print(f"{package:<12}: {status}")

    # Summary
    success_count = sum(1 for status in results.values() if status.startswith("✅"))
    total_count = len(results)

    print("=" * 50)
    print(f"📊 Validation Summary: {success_count}/{total_count} packages validated")

    if success_count == total_count:
        print("🎉 All core packages successfully imported!")
        print("🚀 FastAPI technology stack is ready for development")
    else:
        print("⚠️  Some packages failed to import - check installation")
