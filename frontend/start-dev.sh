#!/bin/bash
export PATH="/usr/local/bin:$PATH"
cd "$(dirname "$0")"
npx vite --host 0.0.0.0 --port "${PORT:-5173}"
