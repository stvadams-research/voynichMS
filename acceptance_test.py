import os
import sys
import json
from pathlib import Path
from sqlalchemy import create_engine, text
from voynich.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()

def test_acceptance():
    print("--- Starting Level 1 Acceptance Test ---")
    
    # 1. Initialize
    print("1. Initializing...")
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    
    # 2. Register Dataset
    print("2. Registering dataset...")
    result = runner.invoke(app, ["data", "register", "test_dataset", "--name", "test_ds"])
    if result.exit_code != 0:
        print(result.stdout)
    assert result.exit_code == 0
    
    # 3. Verify DB
    print("3. Verifying Database...")
    db_path = "sqlite:///data/voynich.db"
    engine = create_engine(db_path)
    
    with engine.connect() as conn:
        # Check Run
        runs = conn.execute(text("SELECT * FROM runs ORDER BY timestamp_start DESC LIMIT 1")).fetchall()
        assert len(runs) == 1
        last_run = runs[0]
        print(f"  [OK] Run found: {last_run.id}")
        print(f"  [OK] Git Commit: {last_run.git_commit}")
        print(f"  [OK] Config: {last_run.config}")
        
        # Check Pages
        pages = conn.execute(text("SELECT * FROM pages WHERE dataset_id = 'test_ds'")).fetchall()
        assert len(pages) == 3
        print(f"  [OK] Pages registered: {len(pages)}")
        for p in pages:
            print(f"    - {p.id} (checksum: {p.checksum})")
            
    # 4. Verify Manifests
    print("4. Verifying Manifests...")
    run_dir = Path("runs") / last_run.id
    manifest_path = run_dir / "manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        print(f"  [OK] Manifest loaded. Status: {manifest['status']}")
        
    print("--- Level 1 Acceptance Test PASSED ---")

if __name__ == "__main__":
    test_acceptance()
