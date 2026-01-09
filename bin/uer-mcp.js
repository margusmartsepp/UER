#!/usr/bin/env node

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

function findPython() {
  try {
    // Try to find python in PATH
    const pythonCmd = process.platform === 'win32' ? 'where python' : 'which python3 || which python';
    const result = execSync(pythonCmd, { encoding: 'utf8' }).trim();
    return result.split('\n')[0]; // Take first result
  } catch {
    throw new Error('Python not found. Please install Python 3.11+ from https://www.python.org/downloads/');
  }
}

function findUv() {
  try {
    const uvCmd = process.platform === 'win32' ? 'where uv' : 'which uv';
    const result = execSync(uvCmd, { encoding: 'utf8' }).trim();
    return result.split('\n')[0];
  } catch {
    return '';
  }
}

function checkPythonVersion(pythonPath) {
  try {
    const version = execSync(`"${pythonPath}" --version`, { encoding: 'utf8' });
    const match = version.match(/Python (\d+)\.(\d+)/);
    if (match) {
      const major = parseInt(match[1]);
      const minor = parseInt(match[2]);
      if (major >= 3 && minor >= 11) {
        return true;
      }
    }
    return false;
  } catch {
    return false;
  }
}

async function main() {
  const pythonDir = path.join(__dirname, '..', 'python');
  const serverPath = path.join(pythonDir, 'src', 'uer', 'server.py');

  // Check if Python source exists
  if (!fs.existsSync(serverPath)) {
    console.error('Error: UER server files not found.');
    console.error('This package may be corrupted. Please try reinstalling:');
    console.error('  npm uninstall -g @uer/mcp');
    console.error('  npx @uer/mcp@latest');
    process.exit(1);
  }

  const python = findPython();

  if (!checkPythonVersion(python)) {
    console.error('Error: Python 3.11 or higher is required.');
    console.error('Please install Python 3.11+ from https://www.python.org/downloads/');
    process.exit(1);
  }

  const uv = findUv();

  let command, args;

  if (uv) {
    // Use uv if available (recommended)
    console.error('Starting UER MCP server with uv...');
    command = uv;
    args = ['--directory', pythonDir, 'run', 'python', '-m', 'uer.server'];
  } else {
    // Fallback to direct python
    console.error('Starting UER MCP server with python...');
    console.error('Tip: Install uv for better dependency management: https://docs.astral.sh/uv/');
    command = python;
    args = ['-m', 'uer.server'];
  }

  const child = spawn(command, args, {
    stdio: 'inherit',
    cwd: pythonDir,
    env: process.env  // Preserve user's API keys
  });

  child.on('error', (error) => {
    console.error('Failed to start UER server:', error.message);
    console.error('\nTroubleshooting:');
    console.error('1. Ensure Python 3.11+ is installed');
    console.error('2. Install uv: pip install uv');
    console.error('3. Check that API keys are set in environment');
    process.exit(1);
  });

  child.on('exit', (code) => {
    if (code !== 0 && code !== null) {
      console.error(`\nUER server exited with code ${code}`);
    }
    process.exit(code || 0);
  });

  // Handle Ctrl+C gracefully
  process.on('SIGINT', () => {
    child.kill('SIGINT');
  });

  process.on('SIGTERM', () => {
    child.kill('SIGTERM');
  });
}

main().catch((error) => {
  console.error('Fatal error:', error.message);
  process.exit(1);
});
