#!/usr/bin/env bash
# prepare.sh — One-time setup for autonomous website builder.
# Analogous to autoresearch/prepare.py.
# Usage: bash prepare.sh

set -e

echo "=== autowebsite: environment check ==="

# 1. Check Python
echo -n "Python 3...  "
python3 --version 2>/dev/null || { echo "FAIL: python3 not found"; exit 1; }

# 2. Check Node.js
echo -n "Node.js...   "
node --version 2>/dev/null || { echo "FAIL: node not found"; exit 1; }

# 3. Check Chrome
echo -n "Chrome...    "
if command -v google-chrome &>/dev/null; then
    google-chrome --version
elif command -v chromium-browser &>/dev/null; then
    chromium-browser --version
elif command -v chromium &>/dev/null; then
    chromium --version
else
    echo "FAIL: no Chrome/Chromium found"
    exit 1
fi

# 4. Check Lighthouse
echo -n "Lighthouse..."
npx lighthouse --version 2>/dev/null || { echo "FAIL: lighthouse not available via npx"; exit 1; }

# 5. Check required files
echo ""
echo "=== checking project files ==="
for f in index.html evaluate.py program.md cv-data.json; do
    if [ -f "$f" ]; then
        echo "  ✓ $f"
    else
        echo "  ✗ $f MISSING"
        exit 1
    fi
done

# 6. Check assets
echo ""
echo "=== checking assets ==="
for f in src/cht-profile.jpg src/snu-logo.png; do
    if [ -f "$f" ]; then
        echo "  ✓ $f"
    else
        echo "  ⚠ $f missing (optional)"
    fi
done

# 7. Smoke test: run evaluate.py
echo ""
echo "=== smoke test: running evaluate.py ==="
echo "(This will take ~30-60 seconds for 3 Lighthouse runs...)"
python3 evaluate.py > smoke_test.log 2>&1
if grep -q "^composite_score:" smoke_test.log; then
    echo ""
    grep "^composite_score:\|^lighthouse:\|^heuristic:\|^brief:" smoke_test.log
    echo ""
    echo "=== Ready to iterate. ==="
    rm -f smoke_test.log
else
    echo "FAIL: evaluate.py did not produce composite_score"
    echo "Last 20 lines of output:"
    tail -20 smoke_test.log
    exit 1
fi
