# Setup Script
# Run this in your terminal: python setup_repo.py

import os

def create_structure():
    # Define the structure based on docs/SYSTEM.md
    dirs = [
        "services/ingest-api",
        "services/processor",
        "services/ui-backend",
        "services/billing",
        "libs/sdk-python",
        "libs/sdk-js",
        "web",
        "infra",
        "tests/integration",
        "tests/e2e",
        ".github/workflows"
    ]

    files = [
        "services/ingest-api/__init__.py",
        "services/ingest-api/main.py",
        "services/ingest-api/requirements.txt",
        "services/processor/__init__.py",
        "services/ui-backend/__init__.py",
        "libs/sdk-python/__init__.py",
        "README.md",
        ".gitignore"
    ]

    # Create Directories
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Created directory: {d}")

    # Create Files
    for f in files:
        if not os.path.exists(f):
            with open(f, 'w') as file:
                file.write("")
            print(f"Created file: {f}")
        else:
            print(f"File exists: {f}")

    # Create .gitignore content
    gitignore_content = """
__pycache__/
*.pyc
.env
.venv
node_modules/
dist/
.DS_Store
"""
    with open(".gitignore", "w") as f:
        f.write(gitignore_content.strip())
    print("Updated .gitignore")

if __name__ == "__main__":
    create_structure()
