# Auto Shell Local V2

**Reverse Shell Factory – Ultimate Generator, Enhancer & Compiler**

A comprehensive toolkit for penetration testers and red team operators.  
Generate 50+ reverse shell one‑liners, apply advanced payload enhancements,
compile Python payloads into standalone binaries, and manage everything
through a unified launcher.

---

<img width="456" height="434" alt="Capture d’écran 2026-06-15 à 23 25 22" src="https://github.com/user-attachments/assets/867afe5b-eb17-4943-968e-55c787389421" />

---

## Features

- **50+ Payloads** – Bash, Python, PowerShell, Netcat, Ncat, Socat, PHP, Ruby, Golang, Node.js, Lua, Java, Perl, Awk, C#, Telnet, OpenSSL, Rustcat, Android (Termux), and more.
- **Multi‑platform** – Linux, macOS, Windows, BSD, Android.
- **10 Payload Enhancements** – Retry logic, SSL wrapping, persistence hints, firewall bypass, stager generation, UPX compression comments, JARM randomisation, XOR obfuscation hints, executable signing hints, and multi‑stage staging.
- **Automatic Compilation** – Extract Python one‑liners and compile them into standalone executables with PyInstaller.
- **Listener Management** – Generate Netcat/Socat/Ncat/Python/PowerShell listener commands, copy to clipboard, and start in a new terminal.
- **Configuration Persistence** – Save your IP/port in `conf.txt` so you never have to retype them.
- **Interactive & Batch Modes** – Select payloads manually, use line ranges, or process entire IP lists.
- **Onion Workflows** – Chain Python generation and Bash post‑processing in a single step.
- **Clean Output** – No broken colours; production‑grade logging.

---

## Files

| File | Description |
|------|-------------|
| `revshell_factory.py` | Main payload generator & enhancer. |
| `revshell_postprocess.sh` | Post‑processor: extracts Python code, compiles, starts listener. |
| `launcher.sh` | Interactive menu & command‑line launcher for all combos. |
| `conf.txt` | (Auto‑generated) Stores last used IP/port. |

---

## Requirements

- Python 3.6+
- Bash (Linux, macOS, WSL, Cygwin)
- `jq` (only if using JSON payload files)
- `xclip` / `pbcopy` / `clip.exe` (optional, for clipboard)
- `xterm` / `gnome-terminal` / `konsole` (optional, for listener terminal)
- `pyinstaller` (auto‑installed if missing)

---

## Installation

```bash
git clone https://github.com/TFD-42/Base_Shell_Auto_Local.git -b Base_Shell_Auto_Local_v2
cd Base_Shell_Auto_Local
chmod +x revshell_postprocess.sh launcher.sh
```

---

## Usage

### 1. Launcher (recommended)

Interactive menu with 19 combinations:

```bash
./launcher.sh --ip 10.0.0.5 --port 4444
```

Without arguments, it prompts for IP/port:

```bash
./launcher.sh
```

Skip the menu and run a specific combo directly:

```bash
./launcher.sh --ip 10.0.0.5 --port 4444 --combo 6
```

### 2. Python Generator (standalone)

Generate all payloads, enhance, and compile:

```bash
python3 revshell_factory.py -i 10.0.0.5 -p 4444 --all --enhance --compile
```

Interactive selection:

```bash
python3 revshell_factory.py -i 10.0.0.5 -p 4444 --interactive
```

Batch from a file:

```bash
python3 revshell_factory.py --batch ips.txt -p 4444 --enhance --compile
```

### 3. Bash Post‑Processor (standalone)

Process a previously generated payload file:

```bash
echo "a" | ./revshell_postprocess.sh payloads.txt --compile --store-conf
```

Listen only:

```bash
./revshell_postprocess.sh --listener-only
```

---

## Examples

### Full cycle: generate → enhance → compile → listener

```bash
./launcher.sh --ip 10.0.0.5 --port 4444 --combo 19
```

This runs:

1. `revshell_factory.py` – all enhanced payloads
2. `revshell_postprocess.sh` – extracts & compiles Python payloads
3. `revshell_postprocess.sh` – prompts to start listener

### Select & compile specific payloads

```bash
python3 revshell_factory.py -i 10.0.0.5 -p 4444 --select "0,2-4,7" --output my_payloads.txt
echo "a" | ./revshell_postprocess.sh my_payloads.txt --compile --store-conf
```

All compiled executables land in `final_shell_compiled/`.

---

## Directory Structure

```
Base_Shell_Auto_Local_v2/
├── launcher.sh
├── revshell_factory.py
├── revshell_postprocess.sh
├── conf.txt                      # (auto‑created)
├── payloads.txt                  # (output)
├── enhanced_all.txt              # (output)
├── final_shell_compiled/         # compiled binaries
│   ├── payload_0
│   ├── payload_1.exe
│   └── ...
└── compiled_binaries/            # custom compile dir
```

---

## Configuration

The file `conf.txt` stores:

```ini
SAVED_IP="10.0.0.5"
SAVED_PORT="4444"
```

It is automatically loaded by both scripts. To save manually:

```bash
python3 revshell_factory.py -i 10.0.0.5 -p 4444 --store-conf
```

---

## 🔮 Future Enhancements

We are working on integrating **Ollama** for local AI‑assisted generation, capable of dynamically adapting reverse shells to the target’s context. The AI will also drive advanced obfuscation and code mutation to evade EDR systems.  
Five other innovations are underway:

- **Multi‑hop tunneling** – automatic construction of SSH, Tor, or ngrok chains,
- **Delivery module** – generation of malicious documents (Word macros, HTA, LNK),
- **C2 integration** – direct export to Metasploit, Empire, Sliver,
- **Polymorphic mutation engine** – payloads that change on every execution,
- **Behavioral analysis** – shell adaptation based on the defences encountered.

Stay tuned for the next releases!

---

# Ethical Use Policy

This toolkit is intended **exclusively** for:

- Authorised penetration testing,
- Security research,
- Educational purposes,
- Capture‑the‑Flag (CTF) competitions.

## Prohibited Use
- Unauthorised access to computer systems (Computer Fraud and Abuse Act, equivalent laws).
- Any activity that violates the policies of a network or system you do not own or have explicit permission to test.
- Use for illegal surveillance, data theft, or exploitation.

## Responsible Disclosure
If you discover a vulnerability using this tool, follow responsible disclosure practices:
- Notify the affected party promptly.
- Provide sufficient time for remediation before public disclosure.

## Professionalism
- Do not use this tool to cause harm.
- Respect privacy and data integrity at all times.
- When in doubt, obtain written consent before testing.

**If you cannot adhere to these principles, do not use this software.**

---

## License

MIT – use at your own risk. This tool is intended for authorised security testing only.

---

## Credits

Created by the [Base_Shell_Auto_Local](https://github.com/TFD-42/Base_Shell_Auto_Local) project.  
v2 rewrite by a senior red team operator. Feedback and contributions welcome.
