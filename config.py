"""
Central configuration for the plain-Python (non-Modal) version of the
FASTQ -> annotated-variants pipeline.

Every stage module imports DATA_MOUNT from here so paths stay consistent
whether you're running locally, in a Docker container, or inside an
NVIDIA Launchable.
"""
import os

# Root data directory. Override with env var for containers / Launchable.
DATA_MOUNT = os.environ.get("PIPELINE_DATA_MOUNT", "/data")

REFS_DIR = f"{DATA_MOUNT}/refs"
ANNOT_DIR = f"{DATA_MOUNT}/annotation"
VEP_CACHE_DIR = f"{DATA_MOUNT}/vep_cache"
OC_DATA_DIR = f"{DATA_MOUNT}/opencravat_modules"
OC_HOME_DIR = f"{DATA_MOUNT}/opencravat_home"

TRIM_DIR = f"{DATA_MOUNT}/trim"
ALIGN_DIR = f"{DATA_MOUNT}/align"
CALLS_DIR = f"{DATA_MOUNT}/calls"
NORM_DIR = f"{DATA_MOUNT}/norm"
ANNOT_OUT_DIR = f"{DATA_MOUNT}/annot"
MERGED_DIR = f"{DATA_MOUNT}/merged"
CUSTOM_DIR = f"{DATA_MOUNT}/custom"
FILLED_DIR = f"{DATA_MOUNT}/filled"
FINAL_DIR = f"{DATA_MOUNT}/final"

# Binaries each stage needs on PATH. Used by check_functions.py to verify
# the environment BEFORE anything is actually run.
STAGE_BINARIES = {
    "download_references": ["wget", "tabix", "samtools", "bwa"],
    "install_opencravat": ["oc"],
    "adapter_trim": ["fastp"],
    "fq2bam": ["pbrun"],
    "call_variants": ["pbrun"],
    "normalize": ["bcftools", "tabix"],
    "annotate_multi": ["oc", "bcftools", "tabix", "vep"],
    "merge_annotations": ["bcftools"],
    "custom_annotators": ["tabix"],
    "fallback_fill": [],  # pure python + requests
    "dedupe_columns": [],  # pure python
}

# Python packages each stage needs importable.
STAGE_PY_IMPORTS = {
    "fallback_fill": ["requests"],
}
