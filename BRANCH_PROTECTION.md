# Branch Protection Configuration

# This file documents the required branch protection rules for the main branch

# Configure these settings in GitHub repository settings > Branches

## Main Branch Protection Rules

### Required Status Checks

- ✅ Enable "Require status checks to pass before merging"
- ✅ Enable "Require branches to be up to date before merging"
- ✅ Required status checks:
  - `All Checks Passed ✅`
  - `Validate Code`
  - `Test Suite (Python 3.9)`
  - `Test Suite (Python 3.10)`
  - `Test Suite (Python 3.11)`
  - `Test Suite (Python 3.12)`
  - `Security & Quality`
  - `Integration Tests`

### Pull Request Requirements

- ✅ Enable "Require a pull request before merging"
- ✅ Enable "Require review from CODEOWNERS" (optional)
- ✅ Enable "Dismiss stale PR approvals when new commits are pushed"
- ✅ Enable "Require review from code owners"

### Additional Restrictions

- ✅ Enable "Restrict pushes that create files larger than 100 MB"
- ✅ Enable "Require linear history" (optional, for cleaner git history)
- ✅ Enable "Include administrators" (applies rules to admins too)

### Auto-merge Settings (Optional)

- ✅ Enable "Allow auto-merge"
- ✅ Enable "Automatically delete head branches"

## GitHub CLI Commands to Set Up Branch Protection

```bash
# Install GitHub CLI if not already installed
# brew install gh

# Login to GitHub
gh auth login

# Set up branch protection for main branch
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["All Checks Passed ✅","Validate Code","Test Suite (Python 3.9)","Test Suite (Python 3.10)","Test Suite (Python 3.11)","Test Suite (Python 3.12)","Security & Quality","Integration Tests"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null

# Or use the simplified command:
gh api repos/gercamjr/f1-scuderia-picker-discord-bot/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["All Checks Passed ✅"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":0,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

## Manual Setup via GitHub Web Interface

1. Go to repository Settings
2. Click "Branches" in sidebar
3. Click "Add rule" for main branch
4. Configure:
   - Branch name pattern: `main`
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Select all CI/CD job names as required status checks
   - ✅ Include administrators
   - ✅ Allow force pushes: ❌ (disabled)
   - ✅ Allow deletions: ❌ (disabled)

## Verification

Once configured, the protection will:

- ❌ Block direct pushes to main branch
- ❌ Block merges if any CI/CD job fails
- ❌ Block merges if branch is behind main
- ✅ Allow merges only after all checks pass
- ✅ Require pull request workflow

## Status Check Names (from CI/CD pipeline)

The following jobs must ALL pass for merge to proceed:

- `validate` → "Validate Code"
- `test` → "Test Suite (Python X.X)"
- `security` → "Security & Quality"
- `integration` → "Integration Tests"
- `all-checks` → "All Checks Passed ✅" (final gate)

## Testing Branch Protection

```bash
# Create a feature branch
git checkout -b feature/test-protection

# Make a change that breaks tests
echo "invalid_syntax(" >> bot.py

# Commit and push
git add . && git commit -m "Test: intentionally break syntax"
git push origin feature/test-protection

# Create PR - should show failing checks
gh pr create --title "Test PR" --body "Testing branch protection"

# CI/CD will fail and block merge ❌

# Fix the issue
git checkout bot.py
git commit -m "Fix: restore valid syntax"
git push

# CI/CD will now pass and allow merge ✅
```
