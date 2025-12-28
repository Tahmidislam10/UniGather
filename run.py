import sys
import os

# Force project root onto Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Backend.App import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
