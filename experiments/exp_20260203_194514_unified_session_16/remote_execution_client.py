import socket
import ssl
import json
import uuid
import os
import pathlib

class RemoteExecutionClient:
    """
    Client that runs on the end‑user's machine.
    - Uses TLS (via ssl.wrap_socket) for confidentiality and integrity.
    - Sends a JSON payload containing:
        * machine_id   – a stable identifier (MAC address or generated UUID)
        * token        – a pre‑shared secret for this machine
        * command      – the raw command string the user wants executed
    - Waits for a JSON response from the relay server.
    """

    def __init__(self, server_host: str, server_port: int, token: str, cert_path: str = None):
        self.server_addr = (server_host, server_port)
        self.token = token
        self.machine_id = self._get_machine_id()
        self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if cert_path:
            self.context.load_verify_locations(cafile=cert_path)
        else:
            # In a LAN setting we may accept self‑signed certs; disable hostname check.
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_NONE

        # Underlying TCP socket wrapped in TLS
        raw_sock = socket.create_connection(self.server_addr)
        self.sock = self.context.wrap_socket(raw_sock, server_hostname=server_host)

    @staticmethod
    def _get_machine_id() -> str:
        """
        Returns a stable identifier for the machine.
        Preference order:
        1. MAC address of the first non‑loopback interface.
        2. Persisted UUID stored in ~/.remote_exec_id (generated on first run).
        """
        # Try MAC address
        try:
            import netifaces
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                mac = addrs.get(netifaces.AF_LINK)
                if mac and mac[0].get('addr') and not mac[0]['addr'].startswith('00:00:00:00:00:00'):
                    return mac[0]['addr']
        except Exception:
            pass

        # Fallback to persisted UUID
        home = pathlib.Path.home()
        id_file = home / ".remote_exec_id"
        if not id_file.exists():
            id_file.write_text(str(uuid.uuid4()))
        return id_file.read_text().strip()

    def execute(self, command: str, timeout: float = 10.0) -> dict:
        """
        Sends a command to the relay server and returns the parsed JSON response.
        """
        payload = {
            "machine_id": self.machine_id,
            "token": self.token,
            "command": command
        }
        data = json.dumps(payload).encode("utf-8")
        # Prefix length for simple framing
        self.sock.sendall(len(data).to_bytes(4, "big") + data)

        # Receive length prefix first
        length_bytes = self._recvall(4, timeout)
        if not length_bytes:
            raise TimeoutError("No response length received")
        resp_len = int.from_bytes(length_bytes, "big")
        resp_bytes = self._recvall(resp_len, timeout)
        if not resp_bytes:
            raise TimeoutError("Incomplete response received")
        return json.loads(resp_bytes.decode("utf-8"))

    def _recvall(self, n: int, timeout: float) -> bytes:
        """
        Helper to receive exactly n bytes or return None on timeout.
        """
        self.sock.settimeout(timeout)
        chunks = []
        received = 0
        while received < n:
            try:
                chunk = self.sock.recv(min(n - received, 4096))
                if not chunk:
                    return None
                chunks.append(chunk)
                received += len(chunk)
            except socket.timeout:
                return None
        return b"".join(chunks)

    def close(self):
        self.sock.close()


if __name__ == "__main__":
    # Example usage – token would be provisioned out‑of‑band.
    TOKEN = os.getenv("REMOTE_EXEC_TOKEN", "CHANGE_ME")
    client = RemoteExecutionClient("127.0.0.1", 8443, TOKEN)
    try:
        response = client.execute("open -a Safari")  # macOS example
        print("Server response:", response)
    finally:
        client.close()