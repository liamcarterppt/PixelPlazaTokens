from app import app
import os
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # Start the web application on port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
