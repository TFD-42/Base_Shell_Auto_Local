# Security Considerations

## Secrets & Sensitive Data
- This tool does **not** contain any hardcoded credentials, API keys, or tokens.
- The optional `conf.txt` stores only the user‑supplied IP and port.  
  **Never commit `conf.txt` to version control.** It is already present in `.gitignore`.
- All generated payloads are ephemeral; compiled executables should be handled securely.

## Operational Security (OPSEC)
- Reverse shells are inherently visible to network defenders.  
  Use **encrypted channels** whenever possible (SSL, SSH tunnels).
- Combine the tool with a **tunnel** to hide your listener’s true location:
  - **Tor** – Route listener traffic through the Tor network (`torsocks nc -lvnp 4444`).
  - **Proxychains** – Force payload connections through a proxy chain.
  - **Cloudflare Tunnel** / **ngrok** – Expose a local listener with a public HTTPS endpoint.
  - **SSH Reverse Tunnels** – Pivot through an intermediate host.

## Tunneling Examples
### Using Tor
```bash
torsocks nc -lvnp 4444
