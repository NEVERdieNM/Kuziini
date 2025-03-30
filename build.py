import PyInstaller.__main__
import os

# Create necessary directories in the output
data_dirs = ['uploads', 'excel_templates', 'exports', 'flask_session']

# Run PyInstaller - removed the icon reference
PyInstaller.__main__.run([
    'app.py',
    '--name=Kuziini',
    '--onefile',
    '--windowed',
    # Removed the problematic icon line
    '--add-data=templates:templates',
    '--add-data=static:static',
    '--hidden-import=openpyxl',
    '--hidden-import=pandas',
    '--hidden-import=flask_session'
])

# After building, create necessary directories in the dist folder
dist_path = os.path.join('dist', 'Kuziini')
if not os.path.exists(dist_path):
    dist_path = os.path.join('dist')

for directory in data_dirs:
    dir_path = os.path.join(dist_path, directory)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        # Create .gitkeep file
        with open(os.path.join(dir_path, '.gitkeep'), 'w') as f:
            pass

print("Build completed. Application packaged in the 'dist' directory.")