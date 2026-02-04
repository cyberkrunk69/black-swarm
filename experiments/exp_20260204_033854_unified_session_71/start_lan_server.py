#!/usr/bin/env python3
"""
Startup script for the LANServer.
"""

from lan_server import LANServer

def main():
    server = LANServer()
    server.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nLANServer shutting down...")
        server.stop()

if __name__ == "__main__":
    main()