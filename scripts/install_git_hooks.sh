#!/bin/bash
# Install git hooks for this repository
# Usage: ./scripts/install_git_hooks.sh

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Installing git hooks..."
echo ""

# Pre-push hook
if [ ! -f "$HOOKS_DIR/pre-push" ]; then
  cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
# Pre-push hook: Remind user to run verification before pushing

REPO_ROOT="$(git rev-parse --show-toplevel)"
VERIFY_SCRIPT="$REPO_ROOT/scripts/verify_pr_readiness.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Pre-push: Run verification before pushing?"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Script: $VERIFY_SCRIPT"
echo ""
echo "This checks manifest, documents, and Python linting."
echo "Run verification? (y/n) [default: y]"
echo ""
read -r response
response="${response:-y}"
if [[ "$response" != "y" ]]; then
  echo "Push cancelled. Run verification and try again:"
  echo "  $VERIFY_SCRIPT"
  exit 1
fi
exit 0
EOF
  chmod +x "$HOOKS_DIR/pre-push"
  echo "✓ Installed pre-push hook"
else
  echo "✓ pre-push hook already exists"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Git hooks installation complete!"
echo ""
echo "Hooks installed:"
echo "  - pre-push: Prompts to run verification before push"
echo ""
echo "To disable a hook temporarily:"
echo "  git push --no-verify"
echo ""
echo "To uninstall all hooks:"
echo "  rm -f .git/hooks/pre-push"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
