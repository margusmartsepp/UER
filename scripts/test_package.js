#!/usr/bin/env node
/**
 * Test script to verify the npm package is correctly built.
 */

const fs = require('fs');
const path = require('path');

function checkFile(filePath, description) {
  if (fs.existsSync(filePath)) {
    console.log(`✓ ${description}: ${filePath}`);
    return true;
  } else {
    console.error(`✗ ${description} missing: ${filePath}`);
    return false;
  }
}

function checkDirectory(dirPath, description) {
  if (fs.existsSync(dirPath) && fs.statSync(dirPath).isDirectory()) {
    console.log(`✓ ${description}: ${dirPath}`);
    return true;
  } else {
    console.error(`✗ ${description} missing: ${dirPath}`);
    return false;
  }
}

function main() {
  console.log('Testing UER MCP package structure...\n');

  const root = path.join(__dirname, '..');
  let allGood = true;

  // Check package.json
  allGood &= checkFile(path.join(root, 'package.json'), 'package.json');

  // Check bin directory
  allGood &= checkDirectory(path.join(root, 'bin'), 'bin directory');
  allGood &= checkFile(path.join(root, 'bin', 'uer-mcp.js'), 'Entry point script');

  // Check python directory
  allGood &= checkDirectory(path.join(root, 'python'), 'Python distribution');
  allGood &= checkDirectory(path.join(root, 'python', 'src'), 'Python source');
  allGood &= checkDirectory(path.join(root, 'python', 'src', 'uer'), 'UER module');
  allGood &= checkFile(path.join(root, 'python', 'src', 'uer', 'server.py'), 'Server module');
  allGood &= checkFile(path.join(root, 'python', 'pyproject.toml'), 'pyproject.toml');

  // Check build scripts
  allGood &= checkDirectory(path.join(root, 'scripts'), 'Scripts directory');
  allGood &= checkFile(path.join(root, 'scripts', 'build_python.py'), 'Build script');

  console.log('\n' + '='.repeat(50));
  if (allGood) {
    console.log('✓ All package structure checks passed!');
    process.exit(0);
  } else {
    console.error('✗ Some package structure checks failed!');
    console.error('Run: npm run build');
    process.exit(1);
  }
}

main();
