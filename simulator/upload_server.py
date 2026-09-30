"""Upload Simulator — demonstrates web upload interception.

A simple local HTTP server that accepts file uploads. The SentinelX agent
monitors the designated drop folder. If the risk engine scores the file
as high risk, the agent enforces a BLOCK and deletes the uploaded file
before it is persisted.
"""

import argparse
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DROP_DIR = Path("C:/tmp/sentinelx_upload_test").resolve()


class UploadHandler(BaseHTTPRequestHandler):
    """Handles HTTP POST requests for file uploads."""

    def do_POST(self):
        """Process file upload."""
        if not DROP_DIR.exists():
            DROP_DIR.mkdir(parents=True, exist_ok=True)

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self.send_error(400, "Empty payload")
            return

        # Simple filename extraction from headers (not robust for prod, fine for demo)
        filename = self.headers.get("X-File-Name", "upload.dat")
        target_path = DROP_DIR / filename

        # Read the payload
        file_data = self.rfile.read(content_length)

        # Write to drop directory
        try:
            with open(target_path, "wb") as f:
                f.write(file_data)

            logger.info("Received upload: %s (%d bytes)", target_path, content_length)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "success", "message": "File uploaded successfully"}')

        except Exception as exc:
            logger.error("Failed to write upload: %s", exc)
            self.send_error(500, f"Server error: {exc}")


def main():
    global DROP_DIR
    parser = argparse.ArgumentParser(description="SentinelX Upload Simulator")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument(
        "--drop-dir",
        type=str,
        default=str(DROP_DIR),
        help="Directory where uploaded files are saved",
    )
    args = parser.parse_args()

    DROP_DIR = Path(args.drop_dir).resolve()
    DROP_DIR.mkdir(parents=True, exist_ok=True)

    server = HTTPServer(("localhost", args.port), UploadHandler)
    logger.info("Upload simulator listening on port %d", args.port)
    logger.info("Drop directory: %s", DROP_DIR)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
