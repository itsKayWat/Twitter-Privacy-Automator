import subprocess
import sys

def install_requirements():
    requirements = [
        'selenium',
        'webdriver_manager',
    ]
    
    print("Installing required packages...")
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}")
            return False
    
    print("\nAll requirements installed successfully!")
    return True

if __name__ == "__main__":
    install_requirements()