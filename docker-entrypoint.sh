#!/bin/sh
set -e

echo "=========================================="
echo "  BLACK SWARM - Network Isolated Runtime"
echo "=========================================="

# Optional: apply iptables-based egress lockdown.
# This is OFF by default because it requires extra packages/capabilities and
# can be surprising in local dev environments.
if [ "${SWARM_ENABLE_IPTABLES_LOCKDOWN:-0}" = "1" ]; then
    if command -v iptables > /dev/null 2>&1; then
        if [ "$(id -u)" -ne 0 ]; then
            echo "[NETWORK] WARNING: iptables lockdown requested but not running as root; skipping"
        else
            echo "[NETWORK] Applying iptables egress lockdown..."

            # Resolve Groq API IPs (best-effort)
            GROQ_IPS=$(getent ahosts api.groq.com 2>/dev/null | awk '{print $1}' | sort -u || echo "")
            echo "[NETWORK] Groq API IPs: $GROQ_IPS"

            # Default DROP for outbound
            iptables -P OUTPUT DROP 2>/dev/null || true

            # Allow loopback
            iptables -A OUTPUT -o lo -j ACCEPT 2>/dev/null || true

            # Allow established connections
            iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true

            # Allow DNS
            iptables -A OUTPUT -p udp --dport 53 -j ACCEPT 2>/dev/null || true
            iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT 2>/dev/null || true

            # Allow internal Docker networks
            iptables -A OUTPUT -d 172.16.0.0/12 -j ACCEPT 2>/dev/null || true
            iptables -A OUTPUT -d 10.0.0.0/8 -j ACCEPT 2>/dev/null || true

            # Allow Groq API (HTTPS)
            for ip in $GROQ_IPS; do
                iptables -A OUTPUT -d "$ip" -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
                echo "[NETWORK] Allowed: $ip (Groq API)"
            done

            echo "[NETWORK] Lockdown applied (egress restricted)"
        fi
    else
        echo "[NETWORK] WARNING: iptables not available; skipping lockdown"
    fi
fi

echo "[SWARM] Starting execution..."
cd /app

# Run the command passed to the container
exec "$@"
