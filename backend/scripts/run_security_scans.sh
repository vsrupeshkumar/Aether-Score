#!/bin/bash
# Security scanning script
# Runs bandit, safety, and other security tools

set -e

echo "🔒 Running Security Scans"
echo "=========================="

# Bandit - Python security linter
echo ""
echo "Running Bandit (Python security linter)..."
bandit -r . -f json -o bandit-report.json || true
bandit -r . -f txt || true

# Safety - Check for known vulnerabilities in dependencies
echo ""
echo "Running Safety (dependency vulnerability check)..."
safety check --json --output safety-report.json || true
safety check || true

# Check for secrets in code
echo ""
echo "Checking for potential secrets..."
if command -v gitleaks &> /dev/null; then
    gitleaks detect --source . --report-path gitleaks-report.json || true
else
    echo "gitleaks not installed, skipping secret detection"
fi

echo ""
echo "✅ Security scans complete!"
echo "Reports saved to: bandit-report.json, safety-report.json"

