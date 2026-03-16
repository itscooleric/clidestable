"""CLI entry point for clidestable."""

import argparse
import logging
import sys

from . import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="clidestable",
        description="\U0001F40E clidestable — VPS-side session server for clidesdale",
    )
    parser.add_argument("-v", "--version", action="version",
                        version=f"clidestable {__version__}")

    sub = parser.add_subparsers(dest="cmd")

    serve = sub.add_parser("serve", help="Start the clidestable server")
    serve.add_argument("--port", type=int, default=7690, help="Server port (default: 7690)")
    serve.add_argument("--bind", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    serve.add_argument("--log-dir", default="/opt/stacks",
                        help="Directory for activity logs (default: /opt/stacks)")
    serve.add_argument("--stall-base-port", type=int, default=7701,
                        help="Base port for ttyd stall instances (default: 7701)")

    args = parser.parse_args()

    if not args.cmd:
        parser.print_help()
        sys.exit(0)

    if args.cmd == "serve":
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        )
        from .server import create_app
        app = create_app(log_dir=args.log_dir, base_port=args.stall_base_port)
        print(f"\U0001F40E clidestable v{__version__} — http://{args.bind}:{args.port}")
        app.run(host=args.bind, port=args.port)
