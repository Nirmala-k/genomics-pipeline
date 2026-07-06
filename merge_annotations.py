import csv
import subprocess

from config import MERGED_DIR
from utils import mkdirs


def _load_opencravat(path):
    table = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            key = (row["chrom"], int(row["pos"]), row["ref"], row["alt"])
            table[key] = dict(row)
    return table


def _load_vep_info(path):
    result = subprocess.run(["bcftools", "view", "-H", path], capture_output=True, text=True, check=True)
    table = {}
    for line in result.stdout.strip().splitlines():
        fields = line.split("\t")
        chrom, pos, ref, alt, info = fields[0], int(fields[1]), fields[3], fields[4], fields[7]
        info_dict = {}
        for kv in info.split(";"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                info_dict[f"vep__{k}"] = v
            else:
                info_dict[f"vep__{kv}"] = "true"
        for a in alt.split(","):
            table[(chrom, pos, ref, a)] = info_dict
    return table


def merge_annotations(sample_id: str, opencravat_tsv: str, vep_vcf: str) -> str:
    mkdirs(MERGED_DIR)
    out_tsv = f"{MERGED_DIR}/{sample_id}.merged.tsv"

    oc_table = _load_opencravat(opencravat_tsv)
    vep_table = _load_vep_info(vep_vcf)
    all_keys = set(oc_table) | set(vep_table)
    all_columns = set()
    for t in (oc_table, vep_table):
        for row in t.values():
            all_columns.update(row.keys())
    fieldnames = ["chrom", "pos", "ref", "alt"] + sorted(all_columns - {"chrom", "pos", "ref", "alt"})

    with open(out_tsv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for key in sorted(all_keys):
            chrom, pos, ref, alt = key
            row = {"chrom": chrom, "pos": pos, "ref": ref, "alt": alt}
            row.update(oc_table.get(key, {}))
            row.update(vep_table.get(key, {}))
            writer.writerow(row)

    return out_tsv


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("usage: python merge_annotations.py <sample_id> <opencravat_tsv> <vep_vcf>")
        raise SystemExit(1)
    print(merge_annotations(sys.argv[1], sys.argv[2], sys.argv[3]))
