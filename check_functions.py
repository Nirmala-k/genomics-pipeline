#!/usr/bin/env python3
"""
check_functions.py — run this FIRST, before `run_all.py`.

It does three cheap things, per stage:
  1. imports the stage module (catches syntax errors / broken imports)
  2. confirms the expected function exists with the right name
  3. checks that required system binaries (and, for fallback_fill, python
     packages) are on PATH / importable

Nothing here touches the GPU, the network, or your actual FASTQ files.
Run it locally, in your Docker image, or inside the Launchable container
before kicking off run_all.py.
"""
import importlib
import shutil
import sys

from config import STAGE_BINARIES, STAGE_PY_IMPORTS

# stage_module_name -> expected function name
STAGES = {
    "stages.download_references": "download_references",
    "stages.install_opencravat": "install_opencravat_modules",
    "stages.adapter_trim": "adapter_trim",
    "stages.fq2bam": "fq2bam",
    "stages.call_variants": "call_variants",
    "stages.normalize": "normalize",
    "stages.annotate_multi": "annotate_multi",
    "stages.merge_annotations": "merge_annotations",
    "stages.custom_annotators": "custom_annotators",
    "stages.fallback_fill": "fallback_fill",
    "stages.dedupe_columns": "dedupe_columns",
}

# key used to look up STAGE_BINARIES / STAGE_PY_IMPORTS for each module
STAGE_KEY = {
    "stages.download_references": "download_references",
    "stages.install_opencravat": "install_opencravat",
    "stages.adapter_trim": "adapter_trim",
    "stages.fq2bam": "fq2bam",
    "stages.call_variants": "call_variants",
    "stages.normalize": "normalize",
    "stages.annotate_multi": "annotate_multi",
    "stages.merge_annotations": "merge_annotations",
    "stages.custom_annotators": "custom_annotators",
    "stages.fallback_fill": "fallback_fill",
    "stages.dedupe_columns": "dedupe_columns",
}


def check_import(module_name: str, fn_name: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(module_name)
    except Exception as e:
        return False, f"IMPORT FAILED: {e}"
    if not hasattr(mod, fn_name):
        return False, f"module imported but function '{fn_name}' not found"
    if not callable(getattr(mod, fn_name)):
        return False, f"'{fn_name}' exists but is not callable"
    return True, "import + function OK"


def check_binaries(key: str) -> list[str]:
    missing = []
    for binary in STAGE_BINARIES.get(key, []):
        if shutil.which(binary) is None:
            missing.append(binary)
    return missing


def check_py_imports(key: str) -> list[str]:
    missing = []
    for pkg in STAGE_PY_IMPORTS.get(key, []):
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


def main() -> int:
    print("=" * 70)
    print("Pipeline function/environment check (no pipeline stages executed)")
    print("=" * 70)

    all_ok = True
    for module_name, fn_name in STAGES.items():
        key = STAGE_KEY[module_name]
        ok, msg = check_import(module_name, fn_name)
        missing_bins = check_binaries(key) if ok else []
        missing_pkgs = check_py_imports(key) if ok else []

        status = "OK" if ok and not missing_bins and not missing_pkgs else "FAIL"
        if status == "FAIL":
            all_ok = False

        print(f"\n[{status}] {module_name}.{fn_name}")
        print(f"    {msg}")
        if missing_bins:
            print(f"    MISSING BINARIES on PATH: {missing_bins}")
        if missing_pkgs:
            print(f"    MISSING PYTHON PACKAGES: {missing_pkgs}")

    print("\n" + "=" * 70)
    if all_ok:
        print("ALL STAGES OK — safe to run run_all.py")
    else:
        print("SOME STAGES FAILED — fix the above before running run_all.py")
        print("(binary gaps are expected on a laptop; they matter on the")
        print(" actual Launchable/GPU container where the pipeline runs)")
    print("=" * 70)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
