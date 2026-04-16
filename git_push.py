#!/usr/bin/env python
"""Direct git push using subprocess (no GitPython)"""

import os
import subprocess
import sys
from pathlib import Path

def run_git_command(cmd, cwd=None):
    """Run a git command and return output"""
    git_exe = r'C:\Program Files\Git\bin\git.exe'
    full_cmd = [git_exe] + cmd
    try:
        result = subprocess.run(full_cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def setup_and_push():
    """Initialize git repository and push to GitHub using git CLI"""
    
    repo_path = Path(__file__).parent
    print(f"\n📁 Working directory: {repo_path}")
    
    # Check if .git already exists
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        print(f"Initializing new git repository...")
        code, out, err = run_git_command(["init"], cwd=str(repo_path))
        if code == 0:
            print(f"✓ Git repository initialized")
        else:
            print(f"❌ Failed to initialize: {err}")
            return False
    else:
        print(f"✓ Git repository already exists")
    
    # Configure git user if not already set
    print("Configuring git user...")
    run_git_command(["config", "user.name", "Snehasis"], cwd=str(repo_path))
    run_git_command(["config", "user.email", "snehasis@example.com"], cwd=str(repo_path))
    print("✓ Git user configured")
    
    # Add remote
    github_url = "https://github.com/snehasissheat/submission"
    print(f"\nConfiguring remote...")
    
    # Try to remove existing remote first
    run_git_command(["remote", "remove", "origin"], cwd=str(repo_path))
    
    # Add new remote
    code, out, err = run_git_command(["remote", "add", "origin", github_url], cwd=str(repo_path))
    if code == 0 or "already exists" in err:
        print(f"✓ Remote configured: {github_url}")
    else:
        print(f"⚠ Remote configuration: {err}")
    
    # Add all files
    print(f"\nAdding files...")
    code, out, err = run_git_command(["add", "-A"], cwd=str(repo_path))
    if code == 0:
        print(f"✓ All files staged for commit")
    else:
        print(f"⚠ Warning adding files: {err}")
    
    # Check if there are changes to commit
    code, out, err = run_git_command(["status", "--porcelain"], cwd=str(repo_path))
    if out or code == 0:
        print(f"\nCommitting changes...")
        code, out, err = run_git_command(
            ["commit", "-m", "Production-ready submission with critical bug fixes and documentation"],
            cwd=str(repo_path)
        )
        if code == 0:
            print(f"✓ Changes committed")
        else:
            print(f"⚠ Commit info: {err}")
    else:
        print(f"✓ No new changes to commit")
    
    # Push to GitHub
    print(f"\nPushing to GitHub...")
    code, out, err = run_git_command(["push", "-u", "origin", "master", "-f"], cwd=str(repo_path))
    
    if code == 0:
        print(f"✓ Successfully pushed to {github_url}")
        print(f"\n✅ All done! Your submission is now on GitHub.")
        print(f"   Repository: {github_url}")
        return True
    else:
        # Try main branch if master failed
        print(f"⚠ Master push note: {err}")
        print(f"\nTrying 'main' branch...")
        code, out, err = run_git_command(["push", "-u", "origin", "main", "-f"], cwd=str(repo_path))
        
        if code == 0:
            print(f"✓ Successfully pushed to {github_url} (main branch)")
            print(f"\n✅ All done! Your submission is now on GitHub.")
            print(f"   Repository: {github_url}")
            return True
        else:
            print(f"❌ Push failed: {err}")
            print(f"\nTroubleshooting:")
            print(f"  1. Make sure you have push access to the repository")
            print(f"  2. Check your GitHub credentials/SSH keys")
            print(f"  3. Repository URL: {github_url}")
            print(f"  4. Error details: {err}")
            return False

if __name__ == "__main__":
    try:
        success = setup_and_push()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
