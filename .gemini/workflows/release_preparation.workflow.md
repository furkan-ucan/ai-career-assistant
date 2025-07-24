# META
# Name: Release Preparation
# Description: Yeni bir sürüm için changelog oluşturur, proje versiyonunu artırır ve bir Pull Request şablonu hazırlar.
# Category: DevOps & Operations
# Duration: ~6 minutes
# Input: Version number (e.g., v1.2.0) and commit range (e.g., v1.1.0..HEAD)
# Output: Release artifacts (CHANGELOG.md, updated version file, PR description).

# WORKFLOW STEPS

## Step 1: Generate Changelog from Git History
# Prompt: prompts/system/create_shell_script.prompt.md
# Input: "Create a script that runs 'git log --pretty=format:%s {{commit_range}}' to get commit messages for the release."
# Output: git_log_script
# Purpose: Sürüme dahil olan commit mesajlarını çekmek.

---

## Step 2: Format Changelog
# Prompt: prompts/documentation/create_documentation.prompt.md
# Input: {{git_log_output}} + "Format this list of commit messages into a user-friendly CHANGELOG.md file, categorizing changes into Features, Fixes, and Chores."
# Output: changelog_content
# Purpose: Commit loglarını okunaklı bir changelog'a dönüştürmek.

---

## Step 3: Bump Project Version
# Prompt: prompts/system/create_shell_script.prompt.md
# Input: "Create a script to find and replace the version string in pyproject.toml (or package.json) with '{{version_number}}'."
# Output: version_bump_script
# Purpose: Proje versiyonunu güncellemek.

---

## Step 4: Create Pull Request Description
# Prompt: prompts/git/create_pr_description.prompt.md
# Input: {{changelog_content}} + "Create a Pull Request description for a new release. The body should contain the changelog."
# Output: pr_description
# Purpose: Sürüm için standart bir PR açıklaması oluşturmak.
