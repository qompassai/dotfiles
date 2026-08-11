<!--  -> #################################################################
<!--  -> /qompassai/.config/dkms/notes.md
<!--  -> Qompass AI Notes
<!--  -> SPDX-License-Identifier: Apache-2.0
<!--  -> Copyright (c) 2026 Qompass AI
<!--  ->
<!--  -> Licensed under the Apache License, Version 2.0 (the "License");
<!--  -> you may not use this file except in compliance with the License.
<!--  -> You may obtain a copy of the License at:
<!--  ->   http://www.apache.org/licenses/LICENSE-2.0
<!--  ->
<!--  -> Unless required by applicable law or agreed to in writing, software
<!--  -> distributed under the License is distributed on an "AS IS" BASIS,
<!--  -> WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
<!--  -> See the License for the specific language governing permissions and
<!--  -> limitations under the License.
<!--  --> 

journalctl -k -b | grep -iE 'module|modprobe'

For Bash or Zsh:

kernel_modules="/usr/lib/modules/$(uname -r)"

comm -23 \
  <(
    sed -E \
      's/:.*//; s|.*/||; s/\.ko(\.(gz|xz|zst))?$//; s/-/_/g' \
      "$kernel_modules/modules.dep" |
      sort -u
  ) \
  <(
    lsmod |
      awk 'NR > 1 { print $1 }' |
      sort -u
  )

This produces the names of installed loadable modules that are not currently loaded.

To search the results:

comm -23 \
  <(
    sed -E \
      's/:.*//; s|.*/||; s/\.ko(\.(gz|xz|zst))?$//; s/-/_/g' \
      "/usr/lib/modules/$(uname -r)/modules.dep" |
      sort -u
  ) \
  <(
    lsmod | awk 'NR > 1 { print $1 }' | sort -u
  ) |
fzf
Inspect a module
modinfo MODULE_NAME

For example:

modinfo nvidia_drm

Test what modprobe would do without loading anything:

sudo modprobe --dry-run --verbose MODULE_NAME

Or equivalently:

sudo modprobe -n -v MODULE_NAME

Show dependencies that would be loaded:

modprobe --show-depends MODULE_NAME
List module files directly
find "/usr/lib/modules/$(uname -r)" \
  -type f \
  \( -name '*.ko' -o -name '*.ko.xz' -o -name '*.ko.zst' -o -name '*.ko.gz' \) \
  -print |
sort

Search for a specific subsystem:

find "/usr/lib/modules/$(uname -r)" \
  -type f \
  -iname '*bluetooth*'
Built-in modules

Modules compiled directly into the kernel do not appear in lsmod, because they were never dynamically loaded. List them with:

sed -E \
  's|.*/||; s/\.ko$//; s/-/_/g' \
  "/usr/lib/modules/$(uname -r)/modules.builtin" |
sort -u

You can also inspect /sys/module, which includes both currently loaded modules and many built-in modules:

ls /sys/module | sort

The distinction is:

Source	Meaning
lsmod	Currently loaded dynamic modules
/proc/modules	Kernel’s underlying loaded-module list
modules.dep	Installed loadable modules and dependencies
modules.builtin	Compiled directly into the kernel
/sys/module	Loaded modules plus exposed built-in modules
Find modules relevant to hardware

For PCI devices:

lspci -k

This shows both the active driver and potentially suitable modules:

Kernel driver in use: nvidia
Kernel modules: nouveau, nvidia_drm, nvidia

For USB devices:

usb-devices
