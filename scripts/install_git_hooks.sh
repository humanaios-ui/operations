#!/bin/bash
# Install git hooks for this repository
# Usage: ./scripts/install_git_hooks.sh

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
PRE_PUSH_HOOK="$HOOKS_DIR/pre-push"
PRE_PUSH_GATE="$REPO_ROOT/tools/pre_push_gate.py"

echo "Installing git hooks..."
echo ""

# Pre-push hook: Compose verification with existing pre_push_gate.py
if [ ! -f "$PRE_PUSH_HOOK" ]; then
  cat > "$PRE_PUSH_HOOK" << 'EOF'
#!/bin/bash
# Pre-push hook: Composed verification + behind-remote guard

REPO_ROOT="$(git rev-parse --show-toplevel)"
VERIFY_SCRIPT="$REPO_ROOT/scripts/verify_pr_readiness.sh"
PRE_PUSH_GATE="$REPO_ROOT/tools/pre_push_gate.py"

# Step 1: Run behind-remote guard (if available)
if [ -f "$PRE_PUSH_GATE" ]; then
  python3 "$PRE_PUSH_GATE" "$@" || exit 1
fi

# Step 2: Run readiness verification
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Pre-push: Running readiness verification..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if "$VERIFY_SCRIPT"; then
  echo ""
  echo "✓ Ready to push"
  exit 0
else
  echo ""
  echo "✗ Verification failed. Fix issues and try again:"
  echo "  $VERIFY_SCRIPT --verbose"
  exit 1
fi
EOF
  chmod +x "$PRE_PUSH_HOOK"
  echo "✓ Installed pre-push hook (with readiness verification)"
else
  echo "✓ pre-push hook already exists"
  echo "  (Not overwriting existing hook. To update, remove and re-run this script.)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Git hooks installation complete!"
echo ""
echo "Hooks installed:"
echo "  - pre-push: Verifies behind-remote status and PR readiness"
echo ""
echo "To disable a hook temporarily:"
echo "  git push --no-verify"
echo ""
echo "To reinstall hooks:"
echo "  rm -f .git/hooks/pre-push && ./scripts/install_git_hooks.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
