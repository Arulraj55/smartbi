import os
import glob
import base64

frontend_dir = r"c:\Users\arulj\Documents\Projects\Smartbi\frontend"
for ext in ("*.html", "*.js"):
    for filepath in glob.glob(os.path.join(frontend_dir, "**", ext), recursive=True):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_content = content.replace("fetch('/api/", "fetch('https://smartbi-backend.onrender.com/api/")
        new_content = new_content.replace('fetch(`/api/', 'fetch(`https://smartbi-backend.onrender.com/api/')
        
        if new_content != content:
            print(f"Updated {filepath}")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)

# Create a valid 1x1 transparent favicon.ico
favicon_path = os.path.join(frontend_dir, "favicon.ico")
if not os.path.exists(favicon_path):
    # base64 for a 1x1 transparent ICO
    ico_b64 = "AAABAAEAAQEAAAEAIAAwAAAAFgAAACgAAAABAAAAAgAAAAEAIAAAAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAA=="
    with open(favicon_path, "wb") as f:
        f.write(base64.b64decode(ico_b64))
    print("Created favicon.ico")
