#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N8N Workflow Importer
- 使用全域安裝的 n8n CLI（不再用 npx）
- 遞迴掃描 workflows/ 下所有子資料夾的 *.json
- 在匯入後更新 context/search_categories.json（若不存在則自動建立）
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

from create_categories import categorize_by_filename


CONTEXT_DIR = Path("context")
SEARCH_CATEGORIES_PATH = CONTEXT_DIR / "search_categories.json"


def ensure_context_files():
    """確保 context/ 與 search_categories.json 存在"""
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    if not SEARCH_CATEGORIES_PATH.exists():
        with open(SEARCH_CATEGORIES_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def load_categories():
    """Load the search categories file."""
    try:
        with open(SEARCH_CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_categories(data):
    """Save the search categories file."""
    ensure_context_files()
    with open(SEARCH_CATEGORIES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class WorkflowImporter:
    """Import n8n workflows with progress tracking and error handling."""

    def __init__(self, workflows_dir: str = "workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.imported_count = 0
        self.failed_count = 0
        self.errors: List[str] = []

    def validate_workflow(self, file_path: Path) -> bool:
        """Validate workflow JSON before import."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 基本格式檢查
            if not isinstance(data, dict):
                return False

            # 必要欄位（依 n8n workflow 結構）
            for field in ["nodes", "connections"]:
                if field not in data:
                    return False

            return True
        except (json.JSONDecodeError, FileNotFoundError, PermissionError):
            return False

    def import_workflow(self, file_path: Path) -> bool:
        """Import a single workflow file via n8n CLI."""
        try:
            # 先驗證 JSON
            if not self.validate_workflow(file_path):
                self.errors.append(f"Invalid JSON: {file_path.name}")
                return False

            # 呼叫全域安裝的 n8n CLI 進行匯入
            result = subprocess.run(
                ["n8n", "import:workflow", f"--input={file_path}"],
                capture_output=True,
                text=True,
                timeout=90,  # 大檔案給長一點
            )

            if result.returncode == 0:
                print(f"✅ Imported: {file_path.name}")

                # 分類並寫入 search_categories.json
                suggested_category = categorize_by_filename(file_path.name)
                all_workflows_data = load_categories()

                found = False
                for workflow_entry in all_workflows_data:
                    if workflow_entry.get("filename") == file_path.name:
                        workflow_entry["category"] = suggested_category
                        found = True
                        break

                if not found:
                    all_workflows_data.append(
                        {
                            "filename": file_path.name,
                            "category": suggested_category,
                            "name": file_path.stem,  # 先用檔名（不含副檔名）
                            "description": "",
                            "nodes": [],
                        }
                    )

                save_categories(all_workflows_data)
                print(
                    f"  Categorized '{file_path.name}' as '{suggested_category or 'Uncategorized'}'"
                )
                return True

            # 匯入失敗：記錄 stderr/stdout
            error_msg = (result.stderr or result.stdout or "").strip()
            self.errors.append(f"Import failed for {file_path.name}: {error_msg}")
            print(f"❌ Failed: {file_path.name}\n   {error_msg}")
            return False

        except subprocess.TimeoutExpired:
            self.errors.append(f"Timeout importing {file_path.name}")
            print(f"⏰ Timeout: {file_path.name}")
            return False
        except FileNotFoundError:
            # n8n CLI 未安裝或 PATH 找不到
            self.errors.append("n8n CLI not found in PATH")
            print("❌ Error: n8n CLI not found in PATH")
            return False
        except Exception as e:
            self.errors.append(f"Error importing {file_path.name}: {str(e)}")
            print(f"❌ Error: {file_path.name} - {str(e)}")
            return False

    def get_workflow_files(self) -> List[Path]:
        """Get all workflow JSON files (recursive)."""
        if not self.workflows_dir.exists():
            print(f"❌ Workflows directory not found: {self.workflows_dir}")
            return []

        # 遞迴搜尋所有子資料夾
        json_files = list(self.workflows_dir.rglob("*.json"))
        if not json_files:
            print(
                f"❌ No JSON files found in: {self.workflows_dir} (searched recursively)"
            )
            return []

        return sorted(json_files)

    def import_all(self) -> Dict[str, Any]:
        """Import all workflow files."""
        ensure_context_files()

        workflow_files = self.get_workflow_files()
        total_files = len(workflow_files)

        if total_files == 0:
            return {"success": False, "message": "No workflow files found"}

        print(f"🚀 Starting import of {total_files} workflows...")
        print("-" * 50)

        for i, file_path in enumerate(workflow_files, 1):
            print(f"[{i}/{total_files}] Processing {file_path.name}...")
            if self.import_workflow(file_path):
                self.imported_count += 1
            else:
                self.failed_count += 1

        # Summary
        print("\n" + "=" * 50)
        print("📊 Import Summary:")
        print(f"✅ Successfully imported: {self.imported_count}")
        print(f"❌ Failed imports: {self.failed_count}")
        print(f"📁 Total files: {total_files}")

        if self.errors:
            print(f"\n❌ Errors encountered:")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"   • {error}")
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more errors")

        return {
            "success": self.failed_count == 0,
            "imported": self.imported_count,
            "failed": self.failed_count,
            "total": total_files,
            "errors": self.errors,
        }


def check_n8n_available() -> bool:
    """Check if n8n CLI is available."""
    try:
        result = subprocess.run(
            ["n8n", "--version"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main():
    """Main entry point."""
    sys.stdout.reconfigure(encoding="utf-8")
    print("🔧 N8N Workflow Importer")
    print("=" * 40)

    # 檢查 n8n CLI
    if not check_n8n_available():
        print("❌ n8n CLI not found. Please install n8n first:")
        print("   npm install -g n8n")
        sys.exit(1)

    importer = WorkflowImporter()
    result = importer.import_all()

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
