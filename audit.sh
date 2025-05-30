#!/bin/bash
set -euxo pipefail

hatch fmt --check
hatch run dev:codespell .
hatch run dev:pyright .
