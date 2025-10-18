"""
Debug script to analyze DD Content Browser UI hierarchy and spacing
Run this from Maya Script Editor after opening the browser
"""

try:
    from PySide6 import QtWidgets, QtCore
except:
    from PySide2 import QtWidgets, QtCore

def analyze_widget_hierarchy(widget, indent=0):
    """Recursively print widget hierarchy with spacing info"""
    spacing = "  " * indent
    class_name = widget.__class__.__name__
    obj_name = widget.objectName() or "(no name)"
    
    # Get size info
    size_info = f"{widget.width()}x{widget.height()}"
    
    # Get margin/spacing info if it's a layout
    layout_info = ""
    if isinstance(widget, QtWidgets.QWidget):
        layout = widget.layout()
        if layout:
            margins = layout.contentsMargins()
            spacing_val = layout.spacing()
            layout_info = f" [margins:{margins.left()},{margins.top()},{margins.right()},{margins.bottom()} spacing:{spacing_val}]"
    elif isinstance(widget, (QtWidgets.QHBoxLayout, QtWidgets.QVBoxLayout, QtWidgets.QGridLayout)):
        margins = widget.contentsMargins()
        spacing_val = widget.spacing()
        layout_info = f" [margins:{margins.left()},{margins.top()},{margins.right()},{margins.bottom()} spacing:{spacing_val}]"
    
    print(f"{spacing}{class_name} '{obj_name}' ({size_info}){layout_info}")
    
    # Process children
    for child in widget.children():
        if isinstance(child, QtWidgets.QWidget):
            analyze_widget_hierarchy(child, indent + 1)

# Find the DD Content Browser window
app = QtWidgets.QApplication.instance()
for widget in app.topLevelWidgets():
    if "DD Content Browser" in widget.windowTitle():
        print("=== DD Content Browser UI Hierarchy ===\n")
        analyze_widget_hierarchy(widget)
        
        # Also check main_layout specifically
        central = widget.centralWidget()
        if central:
            layout = central.layout()
            if layout:
                print("\n=== Main Layout Details ===")
                print(f"Type: {layout.__class__.__name__}")
                margins = layout.contentsMargins()
                print(f"Margins: left={margins.left()}, top={margins.top()}, right={margins.right()}, bottom={margins.bottom()}")
                print(f"Spacing: {layout.spacing()}")
                print(f"Item count: {layout.count()}")
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item.widget():
                        print(f"  Item {i}: {item.widget().__class__.__name__}")
                    elif item.layout():
                        print(f"  Item {i}: {item.layout().__class__.__name__}")
        break
else:
    print("DD Content Browser window not found!")
