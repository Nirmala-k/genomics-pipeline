# Base image: NVIDIA Clara Parabricks (provides pbrun, CUDA, GPU libs)
FROM nvcr.io/nvidia/clara/clara-parabricks:4.3.0-1

# Prevent apt from trying to open an interactive dialog (e.g. tzdata asking
# for timezone) during the build, which hangs with no terminal attached.
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# --- Python (use whatever python3 the base image ships, avoid PPAs that
# depend on reaching external keyservers, which is flaky in some build envs) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-distutils \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3 \
    && ln -sf $(command -v python3) /usr/local/bin/python \
    && rm -rf /var/lib/apt/lists/*

# --- CLI bioinformatics tools ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl unzip git ca-certificates \
    tabix samtools bwa \
    bcftools \
    default-jre perl cpanminus \
    gcc make build-essential zlib1g-dev libbz2-dev liblzma-dev \
    libcurl4-openssl-dev libssl-dev libexpat1-dev \
    autoconf automake libtool pkg-config \
    libdbi-perl libdbd-mysql-perl libarchive-zip-perl libjson-perl \
    && rm -rf /var/lib/apt/lists/*

# --- fastp (adapter trimming) ---
RUN wget -q http://opengene.org/fastp/fastp \
    && chmod a+x fastp \
    && mv fastp /usr/local/bin/

# --- VEP (Ensembl Variant Effect Predictor) ---
RUN cpanm --notest --force Bio::Perl || true \
    && git clone --depth 1 https://github.com/Ensembl/ensembl-vep.git /opt/ensembl-vep \
    && cd /opt/ensembl-vep && perl INSTALL.pl --AUTO a --NO_UPDATE \
    && ln -s /opt/ensembl-vep/vep /usr/local/bin/vep

# --- Python dependencies (OpenCRAVAT `oc` CLI + requests) ---
RUN pip install --no-cache-dir open-cravat requests

# --- Pipeline code ---
WORKDIR /app
COPY . /app

# Data volume mount point (refs, fastq, outputs live here — mounted at runtime)
ENV PIPELINE_DATA_MOUNT=/data
VOLUME ["/data"]

# Default entrypoint: run the full pipeline. Override args at `docker run` /
# Launchable job config time, e.g.:
#   docker run ... genomics-pipeline --sample-id X --fastq-r1 ... --fastq-r2 ...
# Explicit commands such as `python3 check_functions.py` also work.
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]