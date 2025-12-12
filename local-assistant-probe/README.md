# local-assistant-probe

A small stdlib-only Python tool that probes a local OpenAI-compatible endpoint
(e.g., Open WebUI) and prints a Continue `config.yaml` snippet.

## Run

```bash
python -m local_assistant_probe.probe --host localhost --port 3000 --api-key sk-... --model-hint llama3 --debug
```

## Tests

```bash
python -m unittest -q
```
