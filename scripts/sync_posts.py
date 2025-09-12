#!/usr/bin/env python3
"""
Enhanced sync script for Obsidian to Zola blog posts.
Handles YAML to TOML conversion with proper structure and change detection.
"""

import argparse
import subprocess
from pathlib import Path
from typing import Any

import frontmatter
import toml


def parse_yaml_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and return metadata and content separately."""
    try:
        post = frontmatter.loads(content)
        return dict(post.metadata), post.content
    except Exception as e:
        print(f"ERROR: Error parsing frontmatter: {e}")
        return {}, content


def convert_yaml_to_zola_toml(metadata: dict[str, Any]) -> str:
    """Convert YAML metadata to Zola TOML format with proper structure."""
    # Separate fields into different sections
    main_fields: dict[str, Any] = {}
    taxonomies: dict[str, Any] = {}
    extra: dict[str, Any] = {}

    # Fields that go in the main section
    main_section_fields = {"title", "description", "date", "updated", "draft"}

    # Fields that go in taxonomies
    taxonomy_fields = {"categories", "tags"}

    # Fields that go in extra
    extra_fields = {
        "lang",
        "toc",
        "copy",
        "featured",
        "comment",
        "reaction",
        "math",
        "mermaid",
        "outdate_alert",
        "outdate_alert_days",
    }

    # Categorize fields using modern Python patterns
    for key, value in metadata.items():
        match key:
            case k if k in main_section_fields:
                main_fields[k] = value
            case k if k in taxonomy_fields:
                taxonomies[k] = value
            case k if k in extra_fields:
                extra[k] = value
            case _:
                # Unknown fields go to main section
                main_fields[key] = value

    # Build TOML sections
    toml_sections: list[str] = []

    # Helper function to format TOML values
    def format_toml_value(value: Any) -> str:
        """Format a value for TOML output."""
        match value:
            case str(s):
                return f'"{s}"'
            case bool(b):
                return str(b).lower()
            case int() | float():
                return str(value)
            case _ if hasattr(value, "isoformat"):  # datetime objects
                return f'"{value.isoformat()}"'
            case _:
                return f'"{str(value)}"'

    # Main section
    if main_fields:
        for key, value in main_fields.items():
            toml_sections.append(f"{key} = {format_toml_value(value)}")

    # Taxonomies section
    if taxonomies:
        toml_sections.append("\n[taxonomies]")
        for key, value in taxonomies.items():
            try:
                match value:
                    case list(items):
                        # Format list as TOML array
                        formatted_items = [f'"{item}"' for item in items]
                        toml_sections.append(f"{key} = [{', '.join(formatted_items)}]")
                    case _:
                        toml_sections.append(f"{key} = {toml.dumps(value).strip()}")
            except Exception as e:
                print(f"ERROR: Error in taxonomies section for {key}: {e}")
                raise

    # Extra section
    if extra:
        toml_sections.append("\n[extra]")
        for key, value in extra.items():
            toml_sections.append(f"{key} = {format_toml_value(value)}")

    return "\n".join(toml_sections)


def check_git_changes(dest_dir: Path) -> bool:
    """Check if there are any uncommitted changes in the git repository."""
    try:
        # Check if there are any changes to commit (including untracked files)
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=dest_dir.parent,
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_remote_changes(dest_dir: Path) -> bool:
    """Check if there are changes to pull from remote."""
    try:
        # Fetch latest changes from remote
        subprocess.run(["git", "fetch"], check=True, cwd=dest_dir.parent)

        # Check if local branch is behind remote
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..@{u}"],
            cwd=dest_dir.parent,
            capture_output=True,
            text=True,
            check=True,
        )
        return int(result.stdout.strip()) > 0
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return False


def git_commit_and_push(
    dest_dir: Path, message: str = "Update blog posts from Obsidian"
) -> bool:
    """Commit and push changes to git repository."""
    try:
        # Check if there are any local changes
        has_local_changes = check_git_changes(dest_dir)

        if not has_local_changes:
            print("INFO: No local changes to commit.")

            # Check if there are remote changes to pull
            if check_remote_changes(dest_dir):
                print("INFO: Pulling latest changes from remote...")
                subprocess.run(["git", "pull"], check=True, cwd=dest_dir.parent)
                print("SUCCESS: Successfully pulled latest changes from remote.")
            else:
                print("INFO: Repository is up to date with remote.")
            return True

        # Check if there are only untracked files (no actual changes to commit)
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=dest_dir.parent,
                capture_output=True,
                text=True,
                check=True,
            )
            lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
            untracked_only = all(line.startswith("??") for line in lines)

            if untracked_only:
                print("INFO: Only untracked files found, nothing to commit.")
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Add all changes
        subprocess.run(["git", "add", "."], check=True, cwd=dest_dir.parent)

        # Commit changes
        subprocess.run(
            ["git", "commit", "-m", message], check=True, cwd=dest_dir.parent
        )

        # Push changes
        subprocess.run(["git", "push"], check=True, cwd=dest_dir.parent)

        print(f"SUCCESS: Git commit and push successful: {message}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Git operation failed: {e}")
        return False
    except FileNotFoundError:
        print("ERROR: Git not found. Please ensure git is installed and in PATH.")
        return False
    except Exception as e:
        print(f"ERROR: Git operation error: {e}")
        return False


def sync_obsidian_to_zola(
    source_dir: str, dest_dir: str, commit_and_push: bool = False
) -> None:
    """Sync posts from Obsidian to Zola with change detection."""
    print("INFO: Starting sync from Obsidian to Zola...")
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)

    if not source_path.exists():
        print(f"ERROR: Source directory not found at {source_dir}")
        return

    if not dest_path.exists():
        dest_path.mkdir(parents=True, exist_ok=True)
        print(f"INFO: Created destination directory at {dest_dir}")

    processed_files = 0
    updated_files = 0
    skipped_files = 0
    deleted_files = 0

    # Get list of source files
    source_files = list(source_path.glob("*.md"))
    source_filenames = {f.name for f in source_files}

    # Get list of existing destination files
    existing_dest_files = list(dest_path.glob("*.md"))
    existing_dest_filenames = {f.name for f in existing_dest_files}

    # Find files that need to be deleted (exist in dest but not in source)
    # Exclude special Zola files like _index.md
    special_zola_files = {"_index.md", "index.md"}
    files_to_delete = (existing_dest_filenames - source_filenames) - special_zola_files

    # Safety check: only delete files if we have source files to compare against
    # This prevents accidental deletion when source directory is empty or wrong
    if source_files and files_to_delete:
        print(f"INFO: Found {len(files_to_delete)} file(s) to potentially delete...")

        # Delete files that no longer exist in source
        for filename in files_to_delete:
            file_to_delete = dest_path / filename
            try:
                file_to_delete.unlink()
                print(f"INFO: Deleted '{filename}' (no longer in source)")
                deleted_files += 1
            except Exception as e:
                print(f"ERROR: Could not delete file {filename}. Reason: {e}")
    elif not source_files:
        print(
            "WARNING: No source files found - skipping deletion to prevent accidental data loss"
        )

    for md_file in source_files:
        try:
            # Read the source file
            source_content = md_file.read_text(encoding="utf-8")

            # Parse YAML frontmatter
            metadata, content = parse_yaml_frontmatter(source_content)

            # Skip files without metadata
            if not metadata:
                print(f"INFO: Skipping '{md_file.name}': No front matter found.")
                skipped_files += 1
                continue

            # Convert to Zola TOML format
            toml_front_matter = convert_yaml_to_zola_toml(metadata)
            final_content = f"+++\n{toml_front_matter}\n+++\n\n{content}"

            # Define destination file path
            dest_file_path = dest_path / md_file.name

            # Check if file has changed by comparing the final processed content
            if dest_file_path.exists():
                existing_content = dest_file_path.read_text(encoding="utf-8")
                if existing_content == final_content:
                    print(f"INFO: Skipping '{md_file.name}': No changes detected.")
                    skipped_files += 1
                    continue
            else:
                print(f"INFO: New file detected: '{md_file.name}'")

            # Write the processed file
            dest_file_path.write_text(final_content, encoding="utf-8")
            print(f"SUCCESS: Updated '{md_file.name}' -> '{dest_file_path.name}'")
            processed_files += 1
            updated_files += 1

        except (OSError, UnicodeDecodeError) as e:
            print(f"ERROR: Could not read file {md_file.name}. Reason: {e}")
        except Exception as e:
            print(f"ERROR: Could not process file {md_file.name}. Reason: {e}")

    print(f"\nSync Summary:")
    print(f"   • Processed: {processed_files} files")
    print(f"   • Updated: {updated_files} files")
    print(f"   • Deleted: {deleted_files} files")
    print(f"   • Skipped: {skipped_files} files")

    # Git commit and push if requested
    if commit_and_push:
        print(f"\nINFO: Checking git status and syncing with remote...")
        if updated_files > 0 or deleted_files > 0:
            changes = []
            if updated_files > 0:
                changes.append(f"update {updated_files} file(s)")
            if deleted_files > 0:
                changes.append(f"delete {deleted_files} file(s)")

            git_commit_and_push(
                dest_path, f"add(script): {', '.join(changes)} from Obsidian"
            )
        else:
            # Check if there are any changes to commit (including the files we just processed)
            has_changes = check_git_changes(dest_path)
            if has_changes:
                git_commit_and_push(
                    dest_path, "chore(script): sync with remote repository"
                )
            else:
                print("INFO: No changes to commit.")
                # Still check for remote changes
                if check_remote_changes(dest_path):
                    print("INFO: Pulling latest changes from remote...")
                    subprocess.run(["git", "pull"], check=True, cwd=dest_path.parent)
                    print("SUCCESS: Successfully pulled latest changes from remote.")
                else:
                    print("INFO: Repository is up to date with remote.")


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Sync Obsidian blog posts to Zola website"
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Commit and push changes to git repository",
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        required=True,
        help="Source directory path (Obsidian vault containing blog posts)",
    )
    parser.add_argument(
        "--dest-dir",
        type=str,
        required=True,
        help="Destination directory path (Zola content/posts directory)",
    )

    args = parser.parse_args()

    sync_obsidian_to_zola(
        source_dir=args.source_dir, dest_dir=args.dest_dir, commit_and_push=args.commit
    )


if __name__ == "__main__":
    main()
