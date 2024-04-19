"""
list of tool functions
"""

import os
import re
import subprocess

TOOL_EXPLAINATION = """
- calculator: A simple calculator that performs basic arithmetic operations.
- run_python: Executes python code in an IPython kernel on the user's machine and returns the output.
"""

TOOLS = [
    {
        "name": "calculator",
        "description": "A simple calculator that performs basic arithmetic operations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '2 + 3 * 4').",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "run_python",
        "description": "Executes python code in an IPython kernel on the user's machine and returns the output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The python code to execute"},
            },
            "required": ["code"],
        },
    },
]


def calculate(expression):
    """
    Simple calculator
    """
    # Remove any non-digit or non-operator characters from the expression
    expression = re.sub(r"[^0-9+\-*/().]", "", expression)

    try:
        result = eval(expression)
        return str(result)
    except (SyntaxError, ZeroDivisionError, NameError, TypeError, OverflowError):
        return "Error: Invalid expression"


def clone_repo(repo_url):
    """
    Clone a GitHub repository to a local directory
    """
    # common file extensions to include in the knowledge file
    repo_name = repo_url.split("/")[-1].split(".")[0]
    if not os.path.exists(repo_name):
        subprocess.run(["git", "clone", repo_url, repo_name])
    return repo_name


def checkout_version(repo_dir, branch=None, tag=None, commit=None):
    """
    Check out a specific version of a repository
    """
    if branch:
        subprocess.run(["git", "-C", repo_dir, "checkout", branch], check=True)
    elif tag:
        subprocess.run(["git", "-C", repo_dir, "checkout", f"tags/{tag}"], check=True)
    elif commit:
        subprocess.run(["git", "-C", repo_dir, "checkout", commit], check=True)
    else:
        # Fetch the latest information from the remote repository
        subprocess.run(["git", "-C", repo_dir, "fetch"])
        # Get the default branch name
        default_branch = (
            subprocess.check_output(
                ["git", "-C", repo_dir, "rev-parse", "--abbrev-ref", "origin/HEAD"]
            )
            .decode()
            .strip()
            .split("/")[-1]
        )
        # Check out the default branch
        subprocess.run(["git", "-C", repo_dir, "checkout", default_branch])
        # Get the latest tag or commit hash on the default branch
        try:
            version = (
                subprocess.check_output(
                    ["git", "-C", repo_dir, "describe", "--tags", "--abbrev=0"]
                )
                .decode()
                .strip()
            )
        except subprocess.CalledProcessError:
            version = (
                subprocess.check_output(["git", "-C", repo_dir, "rev-parse", "HEAD"])
                .decode()
                .strip()
            )
    return version


def get_file_list(repo_dir):
    """
    Get a list of files in the repository with common file extensions
    """
    files_extentions = (".py", ".js", ".ts", ".cpp", ".c", ".h", ".java", ".txt", ".md")
    file_list = []
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file.endswith(files_extentions):
                file_list.append(os.path.join(root, file))
    return file_list


def generate_knowledge_file(repo_dir, file_list, version):
    """
    Generate a knowledge file with the repository structure and file contents
    """
    repo_name = os.path.basename(repo_dir)
    knowledge_file_name = f"{repo_name}_{version}.txt"
    with open(".data/" + knowledge_file_name, "w", encoding="utf-8") as knowledge_file:
        knowledge_file.write(f"Repository Structure:\n{'-' * 50}\n")
        for root, dirs, files in os.walk(repo_dir):
            level = root.replace(repo_dir, "").count(os.sep)
            indent = " " * 4 * level
            knowledge_file.write(f"{indent}{os.path.basename(root)}/\n")
            subindent = " " * 4 * (level + 1)
            for file in files:
                knowledge_file.write(f"{subindent}{file}\n")
        knowledge_file.write(f"\n\nFile Contents:\n{'-' * 50}\n")
        for file_path in file_list:
            with open(file_path, "r", encoding="utf-8") as file:
                knowledge_file.write(f"{'=' * 50}\nFile: {file_path}\n{'=' * 50}\n")
                knowledge_file.write(file.read())
                knowledge_file.write("\n\n")
    return ".data/" + knowledge_file_name


def process_repository(repo_url, branch=None, tag=None, commit=None):
    """
    Process a GitHub repository by cloning it, checking out a specific version,
    and generating a knowledge file with the repository structure and file contents.
    """
    repo_dir = clone_repo(repo_url)
    # make sure only one of branch, tag, or commit is provided
    if [branch, tag, commit].count(None) < 2:
        raise ValueError("Only one of branch, tag, or commit should be provided")
    version = checkout_version(repo_dir, branch=branch, tag=tag, commit=commit)
    file_list = get_file_list(repo_dir)
    knowledge_file_path = generate_knowledge_file(repo_dir, file_list, version)
    print(
        f"Knowledge file generated successfully: {os.path.basename(repo_dir)}_{version}.txt"
    )
    return knowledge_file_path
