from typing import Optional

from langchain_core.tools import tool
import subprocess


@tool
def git_status(repo_path: str = ".") -> str:
    """Get git status of a repository."""
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "status"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except Exception as e:
        return f"Error getting git status: {str(e)}"


@tool
def git_log(
    repo_path: str = ".", 
    max_count: int = 10,
    since: Optional[str] = None,
    until: Optional[str] = None,
    author: Optional[str] = None,
    grep: Optional[str] = None
) -> str:
    """Get git log history with optional filters.
    
    Args:
        repo_path: Path to git repository (default: current directory)
        max_count: Maximum number of commits to show (default: 10)
        since: Show commits more recent than date (e.g., "7 days ago", "2024-01-01")
        until: Show commits older than date (e.g., "yesterday", "2024-03-01")
        author: Filter commits by author name
        grep: Search for text in commit messages
    
    Examples:
        git_log(max_count=20)  # Last 20 commits
        git_log(since="7 days ago")  # Commits from last 7 days
        git_log(since="2024-03-01", until="2024-03-31")  # Commits in March 2024
        git_log(author="John", since="7 days ago")  # John's commits from last week
        git_log(grep="bug fix", max_count=5)  # Last 5 commits mentioning "bug fix"
    """
    try:
        cmd = ["git", "-C", repo_path, "log"]
        
        # Add max count
        if max_count:
            cmd.extend([f"-{max_count}"])
        
        # Add time range filters
        if since:
            cmd.extend(["--since", since])
        if until:
            cmd.extend(["--until", until])
        
        # Add author filter
        if author:
            cmd.extend(["--author", author])
        
        # Add grep filter
        if grep:
            cmd.extend(["--grep", grep])
        
        # Format output
        cmd.extend([
            "--pretty=format:%h | %ad | %an | %s",
            "--date=short",
            "--decorate"
        ])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        
        if not result.stdout:
            return "No commits found matching the criteria"
        
        return result.stdout
        
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except subprocess.CalledProcessError as e:
        return f"Error getting git log: {e.stderr}"
    except Exception as e:
        return f"Error getting git log: {str(e)}"


@tool
def git_show(
    repo_path: str = ".",
    commit_hash: Optional[str] = None,
    stat_only: bool = True
) -> str:
    """Show detailed information about a specific commit.
    
    Args:
        repo_path: Path to git repository (default: current directory)
        commit_hash: The commit hash to show (if None, shows the latest commit)
        stat_only: If True, only show file statistics (--stat); if False, show full diff
    
    Returns:
        Detailed commit information including changes
    
    Examples:
        git_show(commit_hash="a1b2c3d")  # Show full diff of specific commit
        git_show(commit_hash="HEAD~1", stat_only=True)  # Show stats of previous commit
        git_show()  # Show latest commit with stats
    """
    try:
        cmd = ["git", "-C", repo_path, "show"]
        
        # Add commit hash if provided
        if commit_hash:
            cmd.append(commit_hash)
        
        # Add stat flag
        if stat_only:
            cmd.append("--stat")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=15
        )
        
        if not result.stdout:
            return "No commit information found"
        
        return result.stdout
        
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except subprocess.CalledProcessError as e:
        return f"Error getting commit details: {e.stderr}"
    except Exception as e:
        return f"Error getting commit details: {str(e)}"


@tool
def git_diff(repo_path: str = ".", file_path: Optional[str] = None, staged: bool = False) -> str:
    """Get git diff.
    
    Args:
        repo_path: Path to git repository
        file_path: Optional specific file to show diff for
        staged: If True, show staged changes only
    
    Returns:
        Diff output
    """
    try:
        cmd = ["git", "-C", repo_path, "diff"]
        if staged:
            cmd.append("--staged")
        if file_path:
            cmd.append(file_path)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        return result.stdout if result.stdout else "No changes"
    except Exception as e:
        return f"Error getting diff: {str(e)}"


@tool
def git_branch(repo_path: str = ".") -> str:
    """Show current branch and list branches."""
    try:
        # Get current branch
        current = subprocess.run(
            ["git", "-C", repo_path, "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        
        # List all branches
        branches = subprocess.run(
            ["git", "-C", repo_path, "branch", "-a"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        
        return f"Current branch: {current.stdout.strip()}\n\nAll branches:\n{branches.stdout}"
    except Exception as e:
        return f"Error getting branch info: {str(e)}"