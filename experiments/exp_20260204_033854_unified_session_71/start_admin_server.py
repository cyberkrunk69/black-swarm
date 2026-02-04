#!/usr/bin/env python3
"""
Startup script for the AdminServer.
"""

from lan_server import AdminServer

def main():
    server = AdminServer()
    server.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nAdminServer shutting down...")
        server.stop()

if __name__ == "__main__":
    main()