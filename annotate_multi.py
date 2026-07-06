import os

from config import ANNOT_OUT_DIR, VEP_CACHE_DIR
from stages.install_opencravat import configure_oc_home
from utils import mkdirs, run


def annotate_multi(sample_id: str, vcf_path: str, ref_fasta: str,
                    dbnsfp_path: str | None, bcftools_annot_vcfs: list[str]) -> tuple[str, str]:
    mkdirs(ANNOT_OUT_DIR, f"{ANNOT_OUT_DIR}/opencravat")
    configure_oc_home()

    run([
        "oc", "run", vcf_path, "-l", "hg38",
        "-a", "aloft", "alphamissense", "cadd", "cadd_exome", "civic", "clinvar",
        "dann", "dbsnp", "gnomad3", "gwas_catalog", "interpro", "pharmgkb",
        "polyphen2", "provean", "regulomedb", "revel", "sift", "spliceai", "conservation",
        "-t", "text", "-d", f"{ANNOT_OUT_DIR}/opencravat", "-n", sample_id,
    ])

    current_vcf = vcf_path
    for annot_vcf in bcftools_annot_vcfs:
        step_out = f"{ANNOT_OUT_DIR}/{os.path.basename(annot_vcf).replace('.vcf.gz', '')}.annotated.vcf.gz"
        run(["bcftools", "annotate", "-a", annot_vcf, "-c", "INFO",
             "-Oz", "-o", step_out, current_vcf])
        run(["tabix", "-p", "vcf", step_out])
        current_vcf = step_out

    vep_out = f"{ANNOT_OUT_DIR}/{sample_id}.vep.vcf.gz"
    vep_cmd = [
        "vep", "--input_file", current_vcf, "--output_file", vep_out,
        "--vcf", "--compress_output", "bgzip",
        "--cache", "--dir_cache", VEP_CACHE_DIR,
        "--fasta", ref_fasta, "--force_overwrite",
    ]
    if dbnsfp_path and os.path.exists(dbnsfp_path):
        vep_cmd += [
            "--plugin",
            f"dbNSFP,{dbnsfp_path},ClinPred_pred,CScape_score,PrimateAI_score,SiPhy_29way_logOdds",
        ]
    else:
        print("[annotate_multi] dbNSFP not supplied/found — running VEP without the dbNSFP plugin.")
    run(vep_cmd)

    return f"{ANNOT_OUT_DIR}/opencravat/{sample_id}.variant.tsv", vep_out


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("usage: python annotate_multi.py <sample_id> <vcf_path> <ref_fasta> [dbnsfp_path] [annot_vcf1,annot_vcf2,...]")
        raise SystemExit(1)
    sample_id, vcf_path, ref_fasta = sys.argv[1:4]
    dbnsfp_path = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
    annot_vcfs = sys.argv[5].split(",") if len(sys.argv) > 5 and sys.argv[5] else []
    print(annotate_multi(sample_id, vcf_path, ref_fasta, dbnsfp_path, annot_vcfs))
