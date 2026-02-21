#!/bin/bash
# Installs local git hooks to enforce engineering rigor.

HOOK_DIR=".git/hooks"
PRE_PUSH_HOOK="$HOOK_DIR/pre-push"

if [ ! -d ".git" ]; then
    echo "Error: .git directory not found. Are you in the root of the repo?"
    exit 1
fi

echo "Installing pre-push hook..."

cat <<EOF > "$PRE_PUSH_HOOK"
#!/bin/bash
echo "--- Running Mandatory Pre-push Sanity Checks ---"
./scripts/core_audit/preflight_check.sh
if [ \$? -ne 0 ]; then
    echo "--- [FAIL] Pre-push checks failed. Push aborted. ---"
    exit 1
fi
echo "--- [OK] Pre-push checks passed. ---"
EOF

chmod +x "$PRE_PUSH_HOOK"
echo "Success! Pre-push hook installed at $PRE_PUSH_HOOK"
