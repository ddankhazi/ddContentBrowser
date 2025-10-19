"""
Test script to check available Maya import file types
Run this in Maya's Script Editor to see what file types are available
"""

try:
    import maya.cmds as cmds
    
    print("\n" + "="*60)
    print("AVAILABLE MAYA FILE TYPES:")
    print("="*60)
    
    # Query all file types
    file_types = cmds.file(query=True, type=True)
    
    for i, ft in enumerate(file_types, 1):
        print(f"{i:2d}. {ft}")
    
    print("="*60)
    print(f"Total: {len(file_types)} file types")
    print("="*60)
    
    # Check specifically for DAE and STL
    print("\nSearching for DAE/Collada types:")
    for ft in file_types:
        if 'dae' in ft.lower() or 'collada' in ft.lower():
            print(f"  -> {ft}")
    
    print("\nSearching for STL types:")
    for ft in file_types:
        if 'stl' in ft.lower():
            print(f"  -> {ft}")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nThis script must be run inside Maya!")
