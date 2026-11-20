#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ${WORKERS_CI:-} == 1 ]]; then
  # Workers Builds uses Linux x86_64. Install TeX only for this build.
  tex_dir=$(mktemp -d)
  trap 'rm -rf "$tex_dir"' EXIT
  tex_release=v2025.11
  tex_archive="TinyTeX-$tex_release.tar.gz"
  tex_repository=https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/2025/tlnet-final
  curl --fail --silent --show-error --location --retry 3 --max-time 120 \
    --output "$tex_dir/$tex_archive" \
    "https://github.com/rstudio/tinytex-releases/releases/download/$tex_release/$tex_archive"
  printf '%s  %s\n' '6055bd954f8c46e425fe7ea1f32f3fbd53b3635c64bfd472bd59f8e88ca3db44' \
    "$tex_dir/$tex_archive" | sha256sum --check
  tar -xzf "$tex_dir/$tex_archive" -C "$tex_dir"
  export PATH="$tex_dir/.TinyTeX/bin/x86_64-linux:$PATH"
  # Add the scalable fonts used by microtype and the manuscript's URL package.
  tlmgr --repository "$tex_repository" update --self
  tlmgr --repository "$tex_repository" install cm-super xurl
fi

make -C ../report agentic
mkdir -p public/files
cp ../report/agentic/build/main.pdf public/files/collusion-resistance-paper.pdf
