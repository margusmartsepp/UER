# Publishing Guide for uer-mcp

## Prerequisites

1. **npm account**: Create one at https://www.npmjs.com/signup
2. **Enable 2FA**: Required for publishing packages
   - Go to https://www.npmjs.com/settings/[your-username]/twofa
   - Enable two-factor authentication (use authenticator app)
   - **Important**: Choose "Authorization and Publishing" mode (not just "Authorization")
3. **npm login**: Run `npm login` and enter your credentials
4. **Package name availability**: Check if `uer-mcp` is available (or choose different name)

## Pre-Publishing Checklist

- [ ] All tests pass: `npm test`
- [ ] Build succeeds: `npm run build`
- [ ] Package structure verified: `node scripts/test_package.js`
- [ ] README is up to date
- [ ] Version number is correct in `package.json`
- [ ] License file exists

## Publishing Steps

### 1. Test Locally

```bash
# Build and pack the package
npm pack

# This creates uer-mcp-1.0.0.tgz

# Test installation from local tarball
npm install -g ./uer-mcp-1.0.0.tgz

# Test the command
uer-mcp --help
```

### 2. Test with npx (Local)

```bash
# Test npx with local tarball
npx ./uer-mcp-1.0.0.tgz
```

### 3. Publish to npm

```bash
# Login to npm (first time only)
npm login

# Publish the package
npm publish

# Note: No --access public needed for unscoped packages
```

### 4. Test Published Package

```bash
# Test installation from npm
npx uer-mcp@latest

# Or install globally
npm install -g uer-mcp
uer-mcp
```

### 5. Configure Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "uer": {
      "command": "npx",
      "args": ["uer-mcp@latest"],
      "env": {
        "GEMINI_API_KEY": "your-key-here"
      }
    }
  }
}
```

## Version Management

### Updating Versions

```bash
# Patch version (1.0.0 -> 1.0.1)
npm version patch

# Minor version (1.0.0 -> 1.1.0)
npm version minor

# Major version (1.0.0 -> 2.0.0)
npm version major

# Then publish
npm publish
```

### Version Tags

```bash
# Publish as beta
npm publish --tag beta

# Users can install with:
npx uer-mcp@beta
```

## Troubleshooting

### Package Name Already Taken

If `uer-mcp` is taken, try:
- `@margusmartsepp/uer-mcp`
- `uer-mcp-server`
- `universal-expert-registry`

Update `package.json` name field accordingly.

### Publishing Fails

**Error: 403 Two-factor authentication required**

If you get this error:
```
npm error 403 Two-factor authentication or granular access token with bypass 2fa enabled is required to publish packages.
```

Solution:
1. Go to https://www.npmjs.com/settings/[your-username]/twofa
2. Enable 2FA with an authenticator app (Google Authenticator, Authy, etc.)
3. **Important**: Select "Authorization and Publishing" mode
4. Run `npm publish` again and enter the 2FA code when prompted

**Other Publishing Issues**

```bash
# Check if you're logged in
npm whoami

# Check package name availability
npm view uer-mcp

# Verify package.json is valid
npm pack --dry-run
```

### Build Issues

```bash
# Clean and rebuild
rm -rf python/
npm run build
npm test
```

## Post-Publishing

1. **Update README badges**: Add npm version badge
2. **Create GitHub release**: Tag the version
3. **Update documentation**: Ensure all docs reference correct package name
4. **Announce**: Share on relevant channels

## npm Badge

Add to README.md:

```markdown
[![npm version](https://badge.fury.io/js/uer-mcp.svg)](https://www.npmjs.com/package/uer-mcp)
[![npm downloads](https://img.shields.io/npm/dm/uer-mcp.svg)](https://www.npmjs.com/package/uer-mcp)
```

## Unpublishing (Emergency Only)

```bash
# Unpublish specific version (within 72 hours)
npm unpublish uer-mcp@1.0.0

# Deprecate instead (preferred)
npm deprecate uer-mcp@1.0.0 "Please upgrade to 1.0.1"
```

## Continuous Integration

Consider setting up GitHub Actions for automated publishing:

```yaml
# .github/workflows/publish.yml
name: Publish to npm
on:
  release:
    types: [created]
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
          registry-url: 'https://registry.npmjs.org'
      - run: npm ci
      - run: npm test
      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```
