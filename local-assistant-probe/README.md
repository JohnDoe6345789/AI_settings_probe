# local-assistant-probe

A small stdlib-only Python tool that probes a local OpenAI-compatible endpoint
(e.g., Open WebUI) and prints a Continue `config.yaml` snippet.

## Run

### Using Command-Line Arguments
```bash
python -m local_assistant_probe.probe --host localhost --port 3000 --api-key sk-... --model-hint llama3 --debug
```

### Using Environment Variables (Recommended)
```bash
# Copy the example file and edit it
cp .env.example .env
# Edit .env with your settings (at minimum, set PROBE_API_KEY)

# Run with .env configuration
python -m local_assistant_probe.probe
```

See [ENV_SETUP.md](ENV_SETUP.md) for detailed environment variable configuration.

## Tests

```bash
python -m unittest -q
```
