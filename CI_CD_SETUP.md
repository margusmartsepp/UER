# CI/CD Setup Guide for npm Publishing

This guide explains how to set up automated npm publishing using GitHub Actions with OpenID Connect (OIDC) trusted publishing.

## Overview

**Trusted Publishing** uses OpenID Connect (OIDC) to establish a secure trust relationship between your GitHub repository and npm, eliminating the need to store long-lived npm tokens as GitHub secrets.

## Prerequisites

- GitHub repository: `margusmartsepp/UER`
- npm account with 2FA enabled
- Package name: `uer-mcp`

## Step 1: Configure npm Trusted Publisher

1. **Go to npm package settings**:
   - Visit: https://www.npmjs.com/package/uer-mcp/access
   - Or: npm website → Your Packages → `uer-mcp` → Settings → Publishing Access

2. **Add Trusted Publisher**:
   - Click "Add Trusted Publisher"
   - Select **"GitHub Actions"**
   - Fill in the form:
     - **Organization or user**: `margusmartsepp`
     - **Repository**: `UER`
     - **Workflow filename**: `publish.yml`
     - **Environment name**: (leave empty or use `production`)
   - Click "Set up connection"

3. **Verify**:
   - You should see the trusted publisher listed
   - Status should show as "Active"

## Step 2: GitHub Actions Workflow

The workflow file `.github/workflows/publish.yml` is already created with:

### Triggers

1. **On Release** (Recommended):
   ```yaml
   on:
     release:
       types: [created]
   ```
   - Automatically publishes when you create a GitHub release
   - Best for production releases

2. **Manual Trigger**:
   ```yaml
   workflow_dispatch:
   ```
   - Allows manual publishing from GitHub Actions tab
   - Useful for testing or emergency releases

### Workflow Steps

1. **Checkout code** - Gets your repository code
2. **Setup Node.js** - Installs Node.js 20
3. **Setup Python** - Installs Python 3.11 (required for build)
4. **Install uv** - Installs uv package manager
5. **Build package** - Runs `npm run build`
6. **Run tests** - Runs `npm test`
7. **Publish to npm** - Publishes with provenance

### Important Features

- **`--provenance`**: Adds cryptographic proof of where the package was built
- **`--access public`**: Required for unscoped packages (like `uer-mcp`)
- **`id-token: write`**: Required for OIDC authentication

## Step 3: Publishing Workflow

### Option A: Publish via GitHub Release (Recommended)

1. **Update version in package.json**:
   ```bash
   # Edit package.json, change version to 1.0.2
   git add package.json
   git commit -m "chore: bump version to 1.0.2"
   git push
   ```

2. **Create a GitHub Release**:
   - Go to: https://github.com/margusmartsepp/UER/releases/new
   - Tag version: `v1.0.2`
   - Release title: `v1.0.2`
   - Description: List changes (e.g., "Added logo, enhanced metadata")
   - Click "Publish release"

3. **Automatic Publishing**:
   - GitHub Actions will automatically trigger
   - Watch progress: https://github.com/margusmartsepp/UER/actions
   - Package will be published to npm within 2-3 minutes

### Option B: Manual Publish

1. **Go to Actions tab**:
   - https://github.com/margusmartsepp/UER/actions

2. **Select "Publish to npm" workflow**:
   - Click "Run workflow"
   - Select branch (usually `master` or `main`)
   - Click "Run workflow"

3. **Monitor**:
   - Watch the workflow run
   - Check for any errors
   - Verify package on npm

## Step 4: Verify Publication

After publishing, verify:

1. **Check npm**:
   - Visit: https://www.npmjs.com/package/uer-mcp
   - Verify version number updated
   - Check that files are included (README, logo, etc.)

2. **Test installation**:
   ```bash
   npx uer-mcp@latest
   ```

3. **Check provenance**:
   - On npm package page, look for "Provenance" badge
   - Shows the package was built on GitHub Actions

## Troubleshooting

### Error: "Unable to authenticate"

**Cause**: OIDC trust not configured correctly on npm.

**Solution**:
1. Verify trusted publisher settings on npm
2. Ensure workflow filename matches exactly: `publish.yml`
3. Check that `id-token: write` permission is set

### Error: "Build failed"

**Cause**: Python or build dependencies missing.

**Solution**:
1. Check that Python 3.11+ is installed in workflow
2. Verify `uv` installation step succeeded
3. Check build logs for specific errors

### Error: "Tests failed"

**Cause**: Package structure validation failed.

**Solution**:
1. Run `npm test` locally first
2. Ensure all required files exist
3. Check `scripts/test_package.js` for specific failures

### Error: "Version already exists"

**Cause**: Trying to publish a version that's already on npm.

**Solution**:
1. Bump version in `package.json`
2. Commit and push changes
3. Create new release with new version tag

## Security Best Practices

1. **Use OIDC (Trusted Publishing)**:
   - ✅ No long-lived tokens stored in GitHub
   - ✅ Automatic token rotation
   - ✅ Scoped to specific repository and workflow

2. **Enable Provenance**:
   - ✅ Cryptographic proof of build origin
   - ✅ Increases trust for package consumers
   - ✅ Shows "Provenance" badge on npm

3. **Protect main branch**:
   - Settings → Branches → Add rule
   - Require pull request reviews
   - Require status checks to pass

4. **Use GitHub Environments** (Optional):
   - Settings → Environments → New environment
   - Name: `production`
   - Add required reviewers
   - Update workflow to use environment

## Version Management

### Semantic Versioning

Follow semver (https://semver.org/):

- **Major** (1.0.0 → 2.0.0): Breaking changes
- **Minor** (1.0.0 → 1.1.0): New features, backward compatible
- **Patch** (1.0.0 → 1.0.1): Bug fixes, backward compatible

### Recommended Workflow

1. **Development**:
   ```bash
   # Make changes
   git add .
   git commit -m "feat: add new feature"
   ```

2. **Version Bump**:
   ```bash
   # Update package.json version
   # e.g., 1.0.1 → 1.0.2
   git add package.json
   git commit -m "chore: bump version to 1.0.2"
   git push
   ```

3. **Create Release**:
   - Go to GitHub Releases
   - Create new release with tag `v1.0.2`
   - Automatic publish to npm

## Alternative: npm version command

You can also use npm's built-in version command:

```bash
# Patch version (1.0.1 → 1.0.2)
npm version patch -m "chore: bump version to %s"

# Minor version (1.0.1 → 1.1.0)
npm version minor -m "chore: bump version to %s"

# Major version (1.0.1 → 2.0.0)
npm version major -m "chore: bump version to %s"

# Push tags
git push --follow-tags
```

Then create a GitHub release for the new tag.

## Monitoring

### GitHub Actions

- View all workflow runs: https://github.com/margusmartsepp/UER/actions
- Get email notifications for failures
- Check logs for detailed error messages

### npm

- Package page: https://www.npmjs.com/package/uer-mcp
- Download stats: https://www.npmjs.com/package/uer-mcp/stats
- Version history: Shows all published versions

## Next Steps

1. ✅ Create `.github/workflows/publish.yml` (Done)
2. ⏳ Configure npm trusted publisher
3. ⏳ Test with manual workflow dispatch
4. ⏳ Create first GitHub release (v1.0.1)
5. ⏳ Verify automatic publishing works
6. ⏳ Document process in team wiki

## Resources

- [npm Trusted Publishing](https://docs.npmjs.com/generating-provenance-statements)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [Semantic Versioning](https://semver.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
