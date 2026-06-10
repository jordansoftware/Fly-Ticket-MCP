# Fly Ticket MCP

A **Model Context Protocol (MCP)** server that enables Claude Desktop to search for the cheapest flights in real‑time using the Amadeus Flight Offers Search API.

## Features

- Exposes a single MCP tool: `rechercher_vols_economiques`
- Accepts origin, destination, departure date, and optional return date (IATA codes, `YYYY‑MM‑DD`)
- Handles Amadeus OAuth2 client‑credentials flow automatically
- Returns a compact, readable JSON summary of the cheapest flight offers (price, number of stops, duration, segment details)
- Proper error handling (missing credentials, API errors, no results)
- Ready to run with `stdio` transport for Claude Desktop

## 📦 Installation

1. Clone the repository (or copy the files):

```bash
git clone https://github.com/<your‑username>/fly-ticket-mcp.git
cd fly-ticket-mcp
```

2. Install the required Python dependencies:

```bash
pip install "mcp[cli]" httpx
```

## 🛠️ Usage

### 1. Set up Amadeus credentials

Create a free developer account at [Amadeus for Developers](https://developers.amadeus.com/) and obtain your **Client ID** and **Client Secret** (use the *test* environment).

### 2. Configure Claude Desktop

Add the following entry to your `claude_desktop_config.json` (location varies by OS):

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "flight-search": {
      "command": "python",
      "args": [
        "C:/full/path/to/fly-ticket-mcp/flight_mcp_server.py"
      ],
      "env": {
        "AMADEUS_CLIENT_ID": "your_amadeus_client_id",
        "AMADEUS_CLIENT_SECRET": "your_amadeus_client_secret"
      }
    }
  }
}
```

Replace `C:/full/path/to/fly-ticket-mcp/flight_mcp_server.py` with the **absolute** path to `flight_mcp_server.py` on your machine.

### 3. Restart Claude Desktop

After saving the configuration, quit and relaunch Claude Desktop. The MCP server will start automatically.

### 4. Ask Claude to search for flights

Example prompts you can use:

```
Recherche les vols les moins chers de PAR à TYO le 2026-06-15, retour le 2026-06-22.
```

```
Quel est le vol le moins cher de NYC à LON demain ?
```

Claude will invoke the `rechercher_vols_economiques` tool, retrieve a token from Amadeus, query the Flight Offers Search API, and return a friendly summary.

## 📂 Project Structure

```
fly-ticket-mcp/
│
├─ flight_mcp_server.py   # Main MCP server implementation
├─ README.md              # This file
└─ (optional) .gitignore
```

## 🔐 Environment Variables

| Variable               | Description                              | Required |
|------------------------|------------------------------------------|----------|
| `AMADEUS_CLIENT_ID`    | Amadeus API Client ID                    | ✅ |
| `AMADEUS_CLIENT_SECRET`| Amadeus API Client Secret                | ✅ |

Never commit these values to a public repository. Use the `env` section in Claude Desktop config or a `.env` file if you run the server manually.

## 🐳 Running Manually (for testing)

You can also run the server directly from a terminal:

```bash
export AMADEUS_CLIENT_ID=your_id
export AMADEUS_CLIENT_SECRET=your_secret
python flight_mcp_server.py
```

The server will listen on `stdout/stdin` for MCP messages.

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Amadeus for Developers](https://developers.amadeus.com/) for providing the Flight Offers Search API.
- The [Model Context Protocol](https://modelcontextprotocol.io/) team for the `mcp` Python SDK.

--- 

Happy hunting for the best flight deals! ✈️