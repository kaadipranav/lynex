#!/bin/bash
# =============================================================================
# ClickHouse Deployment Script for DigitalOcean
# =============================================================================
# This script provisions a DigitalOcean droplet, installs ClickHouse,
# runs the schema, and configures firewall rules.
#
# Prerequisites:
#   - doctl CLI installed and authenticated
#   - SSH key added to DigitalOcean account
#
# Usage:
#   chmod +x infra/deploy-clickhouse.sh
#   ./infra/deploy-clickhouse.sh
#
# Estimated Cost: $6/mo (Basic Droplet)
# =============================================================================

set -e

# Configuration
DROPLET_NAME="watchllm-clickhouse"
REGION="nyc1"
SIZE="s-1vcpu-1gb"  # $6/mo - 1 vCPU, 1GB RAM, 25GB SSD
IMAGE="ubuntu-22-04-x64"
SSH_KEY_NAME="default"  # Change this to your SSH key name in DO

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  WatchLLM - ClickHouse Deployment Script${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo -e "${RED}Error: doctl CLI not found. Install it first:${NC}"
    echo "  brew install doctl  # macOS"
    echo "  snap install doctl  # Ubuntu"
    echo "  choco install doctl # Windows"
    exit 1
fi

# Check if authenticated
if ! doctl account get &> /dev/null; then
    echo -e "${RED}Error: doctl not authenticated. Run:${NC}"
    echo "  doctl auth init"
    exit 1
fi

echo -e "${YELLOW}Step 1: Getting SSH key ID...${NC}"
SSH_KEY_ID=$(doctl compute ssh-key list --format ID,Name --no-header | grep "$SSH_KEY_NAME" | awk '{print $1}' | head -1)
if [ -z "$SSH_KEY_ID" ]; then
    echo -e "${RED}Error: SSH key '$SSH_KEY_NAME' not found. Add one first:${NC}"
    echo "  doctl compute ssh-key import $SSH_KEY_NAME --public-key-file ~/.ssh/id_rsa.pub"
    exit 1
fi
echo "  Found SSH key ID: $SSH_KEY_ID"

echo ""
echo -e "${YELLOW}Step 2: Creating droplet...${NC}"
echo "  Name: $DROPLET_NAME"
echo "  Region: $REGION"
echo "  Size: $SIZE ($6/mo)"

# Check if droplet already exists
EXISTING=$(doctl compute droplet list --format Name --no-header | grep -w "$DROPLET_NAME" || true)
if [ -n "$EXISTING" ]; then
    echo -e "${YELLOW}  Droplet '$DROPLET_NAME' already exists. Skipping creation.${NC}"
    DROPLET_IP=$(doctl compute droplet list --format Name,PublicIPv4 --no-header | grep -w "$DROPLET_NAME" | awk '{print $2}')
else
    # Create droplet
    doctl compute droplet create "$DROPLET_NAME" \
        --region "$REGION" \
        --size "$SIZE" \
        --image "$IMAGE" \
        --ssh-keys "$SSH_KEY_ID" \
        --enable-monitoring \
        --wait

    # Wait for droplet to be ready
    echo "  Waiting for droplet to boot..."
    sleep 30

    DROPLET_IP=$(doctl compute droplet list --format Name,PublicIPv4 --no-header | grep -w "$DROPLET_NAME" | awk '{print $2}')
fi

echo -e "${GREEN}  Droplet IP: $DROPLET_IP${NC}"

echo ""
echo -e "${YELLOW}Step 3: Installing ClickHouse...${NC}"

# Create installation script
INSTALL_SCRIPT=$(cat <<'EOF'
#!/bin/bash
set -e

# Install ClickHouse
apt-get update
apt-get install -y apt-transport-https ca-certificates dirmngr gnupg

# Add ClickHouse GPG key and repo
GNUPGHOME=$(mktemp -d)
GNUPGHOME="$GNUPGHOME" gpg --no-default-keyring --keyring /usr/share/keyrings/clickhouse-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 8919F6BD2B48D754
rm -rf "$GNUPGHOME"
chmod +r /usr/share/keyrings/clickhouse-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg] https://packages.clickhouse.com/deb stable main" | tee /etc/apt/sources.list.d/clickhouse.list
apt-get update

# Install ClickHouse (non-interactive)
DEBIAN_FRONTEND=noninteractive apt-get install -y clickhouse-server clickhouse-client

# Generate random password
CH_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
echo "$CH_PASSWORD" > /root/.clickhouse_password

# Configure ClickHouse to listen on all interfaces
cat > /etc/clickhouse-server/config.d/listen.xml <<XMLEOF
<?xml version="1.0"?>
<clickhouse>
    <listen_host>0.0.0.0</listen_host>
</clickhouse>
XMLEOF

# Configure authentication
cat > /etc/clickhouse-server/users.d/default-password.xml <<XMLEOF
<?xml version="1.0"?>
<clickhouse>
    <users>
        <default>
            <password>$CH_PASSWORD</password>
            <networks>
                <ip>::/0</ip>
            </networks>
        </default>
    </users>
</clickhouse>
XMLEOF

# Start ClickHouse
systemctl enable clickhouse-server
systemctl restart clickhouse-server

# Wait for ClickHouse to start
sleep 5

echo "ClickHouse installed successfully!"
echo "Password saved to /root/.clickhouse_password"
EOF
)

# Copy and run installation script
echo "$INSTALL_SCRIPT" | ssh -o StrictHostKeyChecking=no root@"$DROPLET_IP" "cat > /tmp/install_clickhouse.sh && chmod +x /tmp/install_clickhouse.sh && /tmp/install_clickhouse.sh"

echo ""
echo -e "${YELLOW}Step 4: Running schema.sql...${NC}"

# Copy schema file
scp -o StrictHostKeyChecking=no infra/clickhouse/schema.sql root@"$DROPLET_IP":/tmp/schema.sql

# Get password and run schema
CH_PASSWORD=$(ssh -o StrictHostKeyChecking=no root@"$DROPLET_IP" "cat /root/.clickhouse_password")
ssh -o StrictHostKeyChecking=no root@"$DROPLET_IP" "clickhouse-client --password '$CH_PASSWORD' --multiquery < /tmp/schema.sql"

echo ""
echo -e "${YELLOW}Step 5: Configuring firewall...${NC}"

# Create firewall if it doesn't exist
FIREWALL_NAME="watchllm-clickhouse-fw"
EXISTING_FW=$(doctl compute firewall list --format Name --no-header | grep -w "$FIREWALL_NAME" || true)

if [ -z "$EXISTING_FW" ]; then
    # Get App Platform outbound IPs (varies by region)
    # For NYC, common ranges are documented at:
    # https://docs.digitalocean.com/products/app-platform/how-to/manage-firewall/
    
    doctl compute firewall create \
        --name "$FIREWALL_NAME" \
        --droplet-ids "$(doctl compute droplet list --format ID,Name --no-header | grep -w "$DROPLET_NAME" | awk '{print $1}')" \
        --inbound-rules "protocol:tcp,ports:22,address:0.0.0.0/0 protocol:tcp,ports:9000,address:0.0.0.0/0 protocol:tcp,ports:8123,address:0.0.0.0/0" \
        --outbound-rules "protocol:tcp,ports:all,address:0.0.0.0/0 protocol:udp,ports:all,address:0.0.0.0/0"
    
    echo -e "${YELLOW}  Note: Firewall created with open access. For production, restrict to App Platform IPs.${NC}"
else
    echo "  Firewall '$FIREWALL_NAME' already exists."
fi

echo ""
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  ClickHouse Deployment Complete!${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""
echo -e "  ${YELLOW}Connection Details:${NC}"
echo "  Host: $DROPLET_IP"
echo "  Port: 9000 (native) / 8123 (HTTP)"
echo "  User: default"
echo "  Password: $CH_PASSWORD"
echo "  Database: default"
echo ""
echo -e "  ${YELLOW}Connection String:${NC}"
echo "  clickhouse://$DROPLET_IP:9000/default?user=default&password=$CH_PASSWORD"
echo ""
echo -e "  ${YELLOW}Environment Variables for .env:${NC}"
echo "  CLICKHOUSE_HOST=$DROPLET_IP"
echo "  CLICKHOUSE_PORT=9000"
echo "  CLICKHOUSE_USER=default"
echo "  CLICKHOUSE_PASSWORD=$CH_PASSWORD"
echo "  CLICKHOUSE_DATABASE=default"
echo ""
echo -e "  ${YELLOW}Test Connection:${NC}"
echo "  clickhouse-client --host $DROPLET_IP --password $CH_PASSWORD -q 'SELECT version()'"
echo ""
echo -e "${GREEN}Monthly Cost: \$6/mo${NC}"
echo ""
