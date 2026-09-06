#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -euo pipefail
export MAR="$PWD/obj-konafox-release/dist/host/bin/mar.exe"
test -s obj-konafox-release/dist/konafox/precomplete
bash tools/update-packaging/make_full_update.sh \
    "$PWD/artifacts/unsigned.complete.mar" \
    "$PWD/obj-konafox-release/dist/konafox"
