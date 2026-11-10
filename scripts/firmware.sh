#!/usr/bin/env bash
# Builds the ZMK firmware locally: firmware/flatwell.uf2 (with ZMK Studio).
# First run downloads ZMK, Zephyr and the ARM toolchain into tools/ (a few GB).
# Needs: brew install cmake ninja dtc uv gh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/tools"
ZMK="$TOOLS/zmk"
VENV="$TOOLS/venv"
SDK_DIR="$TOOLS/zephyr-sdk"
BUILD="$TOOLS/build/flatwell"
mkdir -p "$TOOLS"

if [[ ! -d "$VENV" ]]; then
  uv venv --python 3.12 "$VENV"
  uv pip install --python "$VENV/bin/python" west
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

if [[ ! -d "$ZMK/.git" ]]; then
  git clone --depth 1 https://github.com/zmkfirmware/zmk.git "$ZMK"
fi
if [[ ! -d "$ZMK/.west" ]]; then
  (cd "$ZMK" && west init -l app)
fi
if [[ ! -d "$ZMK/zephyr/.git" ]]; then
  (cd "$ZMK" && west update --narrow -o=--depth=1)
  uv pip install --python "$VENV/bin/python" -r "$ZMK/zephyr/scripts/requirements-base.txt"
  uv pip install --python "$VENV/bin/python" protobuf grpcio-tools  # ZMK Studio's nanopb generator
fi
SDK_VERSION="$(cat "$ZMK/zephyr/SDK_VERSION")"
SDK="$SDK_DIR/zephyr-sdk-$SDK_VERSION"
if [[ ! -d "$SDK/arm-zephyr-eabi" ]]; then
  ARCH="macos-$(uname -m | sed 's/arm64/aarch64/')"
  mkdir -p "$SDK_DIR"
  gh release download "v$SDK_VERSION" --repo zephyrproject-rtos/sdk-ng --dir "$SDK_DIR" --clobber \
    --pattern "zephyr-sdk-${SDK_VERSION}_${ARCH}_minimal.tar.xz" \
    --pattern "toolchain_${ARCH}_arm-zephyr-eabi.tar.xz"
  tar -xf "$SDK_DIR/zephyr-sdk-${SDK_VERSION}_${ARCH}_minimal.tar.xz" -C "$SDK_DIR"
  tar -xf "$SDK_DIR/toolchain_${ARCH}_arm-zephyr-eabi.tar.xz" -C "$SDK"
  rm "$SDK_DIR"/*.tar.xz
fi

export ZEPHYR_TOOLCHAIN_VARIANT=zephyr ZEPHYR_SDK_INSTALL_DIR="$SDK"
(cd "$ZMK" && west zephyr-export > /dev/null)
(cd "$ZMK/app" && west build -p auto -d "$BUILD" -b nice_nano//zmk -S studio-rpc-usb-uart -- \
  -DSHIELD=flatwell -DZMK_CONFIG="$ROOT/firmware/config" -DZMK_EXTRA_MODULES="$ROOT/firmware")

cp "$BUILD/zephyr/zmk.uf2" "$ROOT/firmware/flatwell.uf2"
echo "✓ firmware/flatwell.uf2"
