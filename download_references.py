import os
import subprocess

from config import REFS_DIR, ANNOT_DIR, VEP_CACHE_DIR
from utils import fetch, run


def download_references() -> None:
    # GRCh38.fa + prebuilt bwa/samtools index files, hosted by us on Hugging
    # Face (one-time indexing already done — avoids repeating the ~1hr
    # `bwa index` build on every fresh environment).
    HF_BASE = "https://huggingface.co/datasets/nirmala29/grch38-bwa-index/tree/main"
    ref_fa = f"{REFS_DIR}/GRCh38.fa"
    for suffix in ["", ".fai", ".bwt", ".amb", ".ann", ".pac", ".sa"]:
        fname = f"GRCh38.fa{suffix}"
        fetch(f"{HF_BASE}/{fname}", f"{REFS_DIR}/{fname}")
    if not os.path.exists(ref_fa):
        print(f"[WARNING] {ref_fa} still missing after download attempt — check the HF_BASE URL above.")

    fetch(
        "https://ftp.ncbi.nlm.nih.gov/snp/latest_release/VCF/GCF_000001405.40.gz",
        f"{REFS_DIR}/dbsnp.vcf.gz",
        post_cmd=["tabix", "-p", "vcf", f"{REFS_DIR}/dbsnp.vcf.gz"],
    )
    fetch(
        "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz",
        f"{ANNOT_DIR}/clinvar.vcf.gz",
        post_cmd=["tabix", "-p", "vcf", f"{ANNOT_DIR}/clinvar.vcf.gz"],
    )
    for chrom in ["chr21"]:
        fetch(
            f"https://storage.googleapis.com/gcp-public-data--gnomad/release/4.1/vcf/genomes/"
            f"gnomad.genomes.v4.1.sites.{chrom}.vcf.bgz",
            f"{ANNOT_DIR}/gnomad.{chrom}.vcf.bgz",
            post_cmd=["tabix", "-p", "vcf", f"{ANNOT_DIR}/gnomad.{chrom}.vcf.bgz"],
        )
    am_tsv_gz = f"{ANNOT_DIR}/alphamissense_hg38.tsv.gz"
    fetch("https://storage.googleapis.com/dm_alphamissense/AlphaMissense_hg38.tsv.gz", am_tsv_gz)
    if not os.path.exists(f"{ANNOT_DIR}/alphamissense_hg38.tsv"):
        run(["gunzip", "-k", am_tsv_gz])
    else:
        print(f"[skip] {ANNOT_DIR}/alphamissense_hg38.tsv already exists")

    vep_marker = f"{VEP_CACHE_DIR}/homo_sapiens/110_GRCh38"
    if not os.path.exists(vep_marker):
        os.makedirs(VEP_CACHE_DIR, exist_ok=True)
        vep_tar = f"{VEP_CACHE_DIR}/vep_cache.tar.gz"
        fetch(
            "https://ftp.ensembl.org/pub/release-110/variation/indexed_vep_cache/"
            "homo_sapiens_vep_110_GRCh38.tar.gz",
            vep_tar,
        )
        run(["tar", "-xzf", vep_tar, "-C", VEP_CACHE_DIR])
        os.remove(vep_tar)
    else:
        print(f"[skip] VEP cache already present at {vep_marker}")

    manual_only = ["GRCh38.fa (+ indexes)", "dbNSFP", "ClinPred", "CScape", "denovo-db", "FunSeq2", "MISTIC", "full CADD"]
    print(f"[manual] Require manual placement / click-through registration, NOT auto-downloaded: {manual_only}")
    print("Reference/DB download pass complete.")


if __name__ == "__main__":
    download_references()