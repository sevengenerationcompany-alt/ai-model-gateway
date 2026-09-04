# ai-model-gateway
Zentrale API-Gateway zur automatischen Integration aller kostenlosen KI-Modelle mit Claude

## Installation

```bash
pip install -r requirements.txt
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Projektintegration

```bash
python integration_helper.py /pfad/zum/projekt
```

Dabei werden im Zielprojekt folgende Dateien erzeugt:

- `.env.gateway`
- `ai_gateway/gateway.py`
- `ai_gateway/config.json`
- `ai_gateway/requirements.txt`
- `ai_gateway_wrapper.py`
