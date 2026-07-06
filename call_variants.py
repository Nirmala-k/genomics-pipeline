from config import CALLS_DIR
from utils import mkdirs, run


def call_variants(sample_id: str, bam_path: str, ref_fasta: str) -> str:
    mkdirs(CALLS_DIR)
    out_vcf = f"{CALLS_DIR}/{sample_id}.vcf.gz"
    run(["pbrun", "deepvariant", "--ref", ref_fasta, "--in-bam", bam_path,
         "--out-variants", out_vcf, "--num-gpus", "1"])
    return out_vcf


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("usage: python call_variants.py <sample_id> <bam_path> <ref_fasta>")
        raise SystemExit(1)
    print(call_variants(sys.argv[1], sys.argv[2], sys.argv[3]))
