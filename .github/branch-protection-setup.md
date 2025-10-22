# Branch Protection Setup Guide

This guide explains how to set up branch protection rules for the Switchboard repository to ensure code quality and security.

## Required Branch Protection Rules

### Main/Master Branch Protection

Navigate to: **Settings → Branches → Add rule**

**Branch name pattern:** `main` (or `master`)

**Protect matching branches:** ✅ Enabled

#### Require status checks to pass before merging

**Require branches to be up to date before merging:** ✅ Enabled

**Status checks that are required:**
- `Code Quality & Security` (from CI/CD pipeline)
- `Test Suite` (from CI/CD pipeline)
- `Docker Build & Test` (from CI/CD pipeline)
- `Dependency Vulnerability Scan` (from CI/CD pipeline)
- `CodeQL Security Analysis` (from CodeQL workflow)

#### Require pull request reviews before merging

**Required number of approvals:** `1`

**Dismiss stale pull request approvals when new commits are pushed:** ✅ Enabled

**Require review from Code Owners:** ❌ Disabled

**Restrict dismissals:** ❌ Disabled

**Require approval of the most recent reviewable push:** ✅ Enabled

**Allow specified actors to bypass required pull requests:** ❌ Disabled

#### Require up to date branches before merging

✅ Enabled

#### Additional settings

**Require signed commits:** ❌ Disabled (for now)

**Require linear history:** ❌ Disabled

**Include administrators:** ✅ Enabled

**Restrict pushes that create matching branches:** ❌ Disabled

### Develop Branch Protection (Optional)

For the develop branch, you can use similar rules but with less strict requirements:

**Required number of approvals:** `0` or `1`

**Status checks:** All except production deployment checks

## Manual Setup Steps

1. Go to your repository on GitHub
2. Navigate to **Settings → Branches**
3. Click **Add rule**
4. Enter `main` (or `master`) as the branch name pattern
5. Configure the settings as described above
6. Click **Create**

## Verification

After setting up branch protection:

1. Try to push directly to the main branch - it should be blocked
2. Create a pull request - it should require the specified status checks and approvals
3. The merge button should only be available when all requirements are met

## Troubleshooting

If you encounter issues:

1. **Status checks not appearing:** Make sure the workflows are enabled and have run at least once
2. **PR reviews not required:** Check that the branch protection rule is correctly configured
3. **Can't merge:** Ensure all required status checks have passed

## Security Note

These branch protection rules help ensure that:
- All code changes are reviewed before merging
- All tests and security checks pass
- Dependencies are scanned for vulnerabilities
- Code quality standards are maintained
- The main branch remains stable and secure
