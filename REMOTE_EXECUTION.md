# Remote Execution (Client + Relay)

## Overview
The relay runs on the swarm host. The client runs on a user's machine. The
relay authenticates messages with an HMAC shared secret and forwards allow-
listed commands to the client, which executes them locally and returns results.

## Install dependency
```
pip install websockets
```

## Start the relay
```
export REMOTE_RELAY_HOST=0.0.0.0
export REMOTE_RELAY_PORT=8765
export REMOTE_RELAY_SECRET=your_shared_secret
python remote_execution_relay.py
```

## Start the client (on the user machine)
```
export REMOTE_RELAY_HOST=relay-host
export REMOTE_RELAY_PORT=8765
export REMOTE_RELAY_SECRET=your_shared_secret
python remote_execution_client.py
```

## Allowed commands (client allow-list)
```
open_browser [url]
run <arg1> <arg2> ...
```

To add or restrict commands, update `ALLOWED_COMMANDS` in
`remote_execution_client.py`.

## Send commands from the swarm host (example)
```python
import asyncio
from remote_execution_relay import send_command

async def main():
    result = await send_command(
        machine_id="machine-id-from-client-log",
        command="open_browser",
        args=["https://example.com"],
    )
    print(result)

asyncio.run(main())
```

## Configuration reference
- `REMOTE_RELAY_HOST`: Relay bind host (default: 0.0.0.0)
- `REMOTE_RELAY_PORT`: Relay port (default: 8765)
- `REMOTE_RELAY_SECRET`: Shared HMAC secret (required)
- `REMOTE_RELAY_URL`: Optional client override (ws://host:port)
- `REMOTE_EXEC_MACHINE_ID`: Optional client machine id override
- `REMOTE_RELAY_RECONNECT_DELAY`: Client reconnect delay (seconds)
