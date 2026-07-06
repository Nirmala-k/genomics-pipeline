import os

from config import OC_DATA_DIR, OC_HOME_DIR
from utils import run


def configure_oc_home() -> None:
    """Point OpenCRAVAT's config at a persistent directory instead of the
    ephemeral $HOME. Must be called with the same OC_HOME_DIR in every
    stage that invokes `oc` (annotate_multi too)."""
    os.makedirs(OC_HOME_DIR, exist_ok=True)
    os.makedirs(OC_DATA_DIR, exist_ok=True)
    os.environ["HOME"] = OC_HOME_DIR
    run(["oc", "config", "md", OC_DATA_DIR])


def install_opencravat_modules() -> None:
    configure_oc_home()

    base_marker = f"{OC_DATA_DIR}/.base_installed"
    if not os.path.exists(base_marker):
        run(["oc", "module", "install-base"])
        open(base_marker, "w").close()
    else:
        print("[skip] oc module install-base already done")

    modules = [
        "aloft", "alphamissense", "cadd", "cadd_exome", "civic", "clinvar",
        "dann", "dbsnp", "gnomad3", "gwas_catalog", "interpro", "pharmgkb",
        "polyphen2", "provean", "regulomedb", "revel", "sift", "spliceai",
        "conservation",
    ]
    to_install = [
        m for m in modules
        if not os.path.isdir(f"{OC_DATA_DIR}/modules/annotators/{m}")
    ]
    if to_install:
        print(f"[install] modules missing, installing: {to_install}")
        run(["oc", "module", "install", *to_install, "-y"])
    else:
        print("[skip] all oc modules already installed")

    print("OpenCRAVAT module install pass complete.")


if __name__ == "__main__":
    install_opencravat_modules()
