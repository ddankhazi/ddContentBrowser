"""
One-time config migration script for DD Content Browser
Moves config from user home to script directory
Run this once after updating to v2.3.1+
"""

import json
import shutil
from pathlib import Path

# Old location (user home)
OLD_CONFIG = Path.home() / ".dd_content_browser_config.json"

# New location (script folder)
NEW_CONFIG = Path(__file__).parent / "config.json"

def migrate_config():
    """Migrate config from old location to new location"""
    
    print("=" * 60)
    print("DD Content Browser - Config Migration Tool")
    print("=" * 60)
    
    # Check if old config exists
    if not OLD_CONFIG.exists():
        print(f"✅ No old config found at: {OLD_CONFIG}")
        print("   Nothing to migrate. Using defaults.")
        return
    
    # Check if new config already exists
    if NEW_CONFIG.exists():
        print(f"⚠️  New config already exists at: {NEW_CONFIG}")
        response = input("   Overwrite with old config? (y/n): ")
        if response.lower() != 'y':
            print("   Skipping migration.")
            return
    
    try:
        # Load old config
        print(f"\n📂 Loading old config from: {OLD_CONFIG}")
        with open(OLD_CONFIG, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        
        # Backup old config
        backup_path = OLD_CONFIG.parent / f"{OLD_CONFIG.stem}_backup{OLD_CONFIG.suffix}"
        shutil.copy2(OLD_CONFIG, backup_path)
        print(f"💾 Backup created at: {backup_path}")
        
        # Save to new location
        print(f"\n📝 Saving to new location: {NEW_CONFIG}")
        with open(NEW_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(old_data, f, indent=2, ensure_ascii=False)
        
        print("\n✅ Migration complete!")
        print(f"\n📊 Migrated data:")
        print(f"   - Recent paths: {len(old_data.get('recent_paths', []))}")
        print(f"   - Favorites: {len(old_data.get('favorites', []))}")
        print(f"   - Thumbnail size: {old_data.get('thumbnail_size', 128)}")
        print(f"   - Window geometry: {'Saved' if old_data.get('window_geometry') else 'Default'}")
        
        print(f"\n📌 Next steps:")
        print(f"   1. Old config is backed up at: {backup_path}")
        print(f"   2. You can safely delete: {OLD_CONFIG}")
        print(f"   3. New config location: {NEW_CONFIG}")
        print(f"   4. Restart DD Content Browser to use new config")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("   Please report this error.")

if __name__ == "__main__":
    migrate_config()
    input("\nPress Enter to close...")
