# LAN User Session Isolation Design

## Requirements

1. **Own Session**: Each user connecting via LAN (WiFi) must have a separate session isolated from other users and the admin.
2. **Visibility**: Users need to see swarm activity across the whole surface.
3. **Clarity**: Users must be able to distinguish between tasks they triggered and tasks happening separately.
4. **Isolation**: Users cannot affect the host machine or other users' machines.

## Design

### Per-IP Session Management
- Assign a unique session ID to each user based on their IP address.
- Use this session ID to manage user sessions independently.

### User Workspace Isolation
- Create isolated workspaces for each user session.
- Ensure that users can only access their own workspace.

### Activity Tagging
- Tag activities as either **user‑triggered** or **background swarm**.
- Provide real‑time updates on the status of tasks.

### Real‑time Status
- Display **“Your tasks”** and **“Network activity”** in real‑time.
- Use web interfaces or dashboards for easy monitoring.

## Architecture

The architecture will consist of:
- **Session Manager**: Handles session creation and management per IP.
- **Workspace Isolator**: Ensures user workspaces are isolated.
- **Activity Monitor**: Tags and displays activities in real‑time.
- **Status Dashboard**: Provides real‑time status updates.

## Implementation

- Develop the Session Manager, Workspace Isolator, Activity Monitor, and Status Dashboard as separate modules.
- Integrate these modules to work seamlessly together.
- Test the system thoroughly to ensure all requirements are met.