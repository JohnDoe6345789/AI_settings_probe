# Environment Variable Configuration

The Local Assistant Probe now supports configuration via environment variables in addition to command-line arguments.

## Quick Start

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your settings:**
   ```bash
   # Open in your favorite editor
   nano .env
   # or
   code .env
   ```

3. **Update the required values:**
   At minimum, you need to set:
   ```
   PROBE_API_KEY=sk-your-actual-api-key-here
   ```

4. **Run the probe:**
   ```bash
   python -m local_assistant_probe.probe
   ```

## Configuration Priority

Settings are loaded in the following order (later ones override earlier):
1. Default values in code
2. Environment variables from `.env` file
3. Command-line arguments

This means you can set defaults in `.env` and override specific values on the command line:
```bash
# Use .env for most settings, but override the port
python -m local_assistant_probe.probe --port 8080
```

## Available Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROBE_HOST` | API host address | `localhost` |
| `PROBE_PORT` | API port number | `3000` |
| `PROBE_API_KEY` | API key (required) | None |
| `PROBE_MODEL_HINT` | Model hint to search for | `llama3` |
| `PROBE_TITLE` | Configuration title | `Local Assistant` |
| `PROBE_MODEL_NAME` | Model name for output | `LLama3` |
| `PROBE_TIMEOUT` | Request timeout in seconds | `3.0` |
| `PROBE_DEBUG` | Enable debug output | `false` |

## Security Notes

- **Never commit your `.env` file** - it's already in `.gitignore`
- The `.env.example` file is safe to commit (contains no secrets)
- Keep your API keys secure and rotate them regularly

## Examples

### Development Setup
```env
PROBE_HOST=localhost
PROBE_PORT=3000
PROBE_API_KEY=sk-dev-key-12345
PROBE_MODEL_HINT=llama3
PROBE_DEBUG=true
```

### Production Setup
```env
PROBE_HOST=api.example.com
PROBE_PORT=443
PROBE_API_KEY=sk-prod-key-67890
PROBE_MODEL_HINT=gpt-4
PROBE_TITLE=Production Assistant
PROBE_DEBUG=false
```

### Minimal Setup
```env
PROBE_API_KEY=sk-your-key-here
```

## Troubleshooting

**Problem:** Script says API key is required  
**Solution:** Make sure `PROBE_API_KEY` is set in `.env` or pass `--api-key` on command line

**Problem:** Environment variables not being read  
**Solution:** Ensure your `.env` file is in the current working directory when running the script

**Problem:** Values in `.env` are being ignored  
**Solution:** Command-line arguments override `.env` values. Remove CLI args to use `.env` settings
