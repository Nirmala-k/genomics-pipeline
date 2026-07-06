#!/usr/bin/env python3
"""
run_all.py — plain-Python orchestrator (no Modal, no Flask).

Chains every stage by calling its function directly, in-process, on
whatever machine you run this on (your GPU box / NVIDIA Launchable
container). Each stage still writes to DATA_MOUNT (see config.py) exactly
like the Modal version did — just without volume.commit(), since there's
no Modal Volume anymore; it's a normal filesystem.

Usage:
    python run_all.py --sample-id KHAHPGXSTD2 \
        --fastq-r1 /data/fastq/KHAHPGXSTD2_R1.fastq.gz \
        --fastq-r2 /data/fastq/KHAHPGXSTD2_R2.fastq.gz

Run check_functions.py first to confirm every stage/binary is available.
"""
import argparse

from stages.download_references import download_references
from stages.install_opencravat import install_opencravat_modules
from stages.adapter_trim import adapter_trim
from stages.fq2bam import fq2bam
from stages.call_variants import call_variants
from stages.normalize import normalize
from stages.annotate_multi import annotate_multi
from stages.merge_annotations import merge_annotations
from stages.custom_annotators import custom_annotators
from stages.fallback_fill import fallback_fill
from stages.dedupe_columns import dedupe_columns

from config import DATA_MOUNT


def parse_args():
    p = argparse.ArgumentParser(description="FASTQ -> annotated-variants pipeline (plain python)")
    p.add_argument("--sample-id", default="KHAHPGXSTD2")
    p.add_argument("--fastq-r1", default=f"{DATA_MOUNT}/fastq/KHAHPGXSTD2_R1.fastq.gz")
    p.add_argument("--fastq-r2", default=f"{DATA_MOUNT}/fastq/KHAHPGXSTD2_R2.fastq.gz")
    p.add_argument("--ref-fasta", default=f"{DATA_MOUNT}/refs/GRCh38.fa")
    p.add_argument("--known-sites", default=f"{DATA_MOUNT}/refs/dbsnp.vcf.gz")
    p.add_argument("--dbnsfp-path", default="")
    p.add_argument("--bcftools-annot-vcfs", default="", help="comma-separated")
    p.add_argument("--clinpred", default="")
    p.add_argument("--cscape", default="")
    p.add_argument("--denovo-db", default="")
    p.add_argument("--funseq2", default="")
    p.add_argument("--mistic", default="")
    p.add_argument("--skip-download", action="store_true",
                    help="skip stage 0/0.5 if refs + OC modules already prepared")
    return p.parse_args()


def main():
    args = parse_args()

    if not args.skip_download:
        print("[0/9] Checking/downloading reference genome + annotation databases")
        download_references()

        print("[0.5/9] Checking/installing OpenCRAVAT annotator modules")
        install_opencravat_modules()
    else:
        print("[0-0.5/9] Skipped (--skip-download)")

    print(f"[1/9] Trimming adapters for {args.sample_id}")
    trimmed_r1, trimmed_r2 = adapter_trim(args.sample_id, args.fastq_r1, args.fastq_r2)

    print("[2/9] Aligning (pbrun fq2bam, GPU)")
    bam = fq2bam(args.sample_id, trimmed_r1, trimmed_r2, args.ref_fasta, args.known_sites)

    print("[3/9] Calling variants (pbrun deepvariant, GPU)")
    vcf = call_variants(args.sample_id, bam, args.ref_fasta)

    print("[4/9] Normalizing VCF")
    norm_vcf = normalize(args.sample_id, vcf, args.ref_fasta)

    print("[5/9] Annotating (OpenCRAVAT + bcftools + VEP/dbNSFP)")
    annot_vcfs = [v for v in args.bcftools_annot_vcfs.split(",") if v]
    oc_tsv, vep_vcf = annotate_multi(
        args.sample_id, norm_vcf, args.ref_fasta, args.dbnsfp_path or None, annot_vcfs
    )

    print("[6/9] Merging OpenCRAVAT + VEP/bcftools annotations")
    merged_tsv = merge_annotations(args.sample_id, oc_tsv, vep_vcf)

    print("[7/9] Custom annotators (ClinPred/CScape/denovo-db/FunSeq2/MISTIC, any supplied)")
    enriched_tsv = custom_annotators(
        args.sample_id, merged_tsv,
        args.clinpred or None, args.cscape or None, args.denovo_db or None,
        args.funseq2 or None, args.mistic or None,
    )

    print("[8/9] Per-annotator fallback fill (API + dbNSFP)")
    filled_tsv = fallback_fill(args.sample_id, enriched_tsv)

    print("[9/9] Deduping exact + semantic overlapping columns")
    final_tsv = dedupe_columns(args.sample_id, filled_tsv)

    print(f"\nDONE. Final annotated table: {final_tsv}")


if __name__ == "__main__":
    main()
