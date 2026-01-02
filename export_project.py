import os
import zipfile

def zip_project(output_filename):
    # Files/Dirs to exclude
    EXCLUDE_DIRS = {'__pycache__', 'venv', 'env', '.git', '.idea', '.vscode', 'instance', 'logs'}
    EXCLUDE_FILES = {'quantum_v2.db', 'firebase_credentials.json', output_filename, '.DS_Store'}
    
    # Get current directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(root_dir):
                # Modify dirs in-place to skip excluded directories
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                
                for file in files:
                    if file in EXCLUDE_FILES:
                        continue
                    if file.endswith('.pyc') or file.endswith('.log') or file.endswith('.zip'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, root_dir)
                    
                    print(f"Adding {arcname}")
                    zipf.write(file_path, arcname)
        print(f"Successfully created {output_filename}")
    except Exception as e:
        print(f"Error creating zip: {e}")

if __name__ == "__main__":
    print("Starting export...")
    zip_project('QuantumCore_Export_v2.zip')
    print("Export complete.")
