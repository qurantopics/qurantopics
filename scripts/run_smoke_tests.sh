#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

PORT="${PORT:-8080}"
BASE_URL="${TEST_BASE_URL:-http://localhost:${PORT}}"

echo "========================================================"
echo "  QuranTopics Smoke Test Runner"
echo "  Target URL: $BASE_URL"
echo "========================================================"

# Check if target server is responding
if ! curl -s --head "$BASE_URL" > /dev/null 2>&1; then
    echo "⚠️  Warning: Target server at $BASE_URL is not currently responding."
    echo ""
    echo "To run against a local server:"
    echo "  1. (Optional) Start Datastore / Firestore emulator:"
    echo "     npx -y firebase-tools@13 --config var/firebase/firebase.json emulators:start --only firestore"
    echo "  2. Start QuranTopics:"
    echo "     export DATASTORE_EMULATOR_HOST=localhost:8081"
    echo "     ./venv/bin/python main.py"
    echo "  3. In another terminal, rerun this script:"
    echo "     ./scripts/run_smoke_tests.sh"
    echo ""
    echo "Attempting test run anyway..."
fi

PYTHON_BIN="./venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

"$PYTHON_BIN" scripts/smoke_test.py --base-url "$BASE_URL"
