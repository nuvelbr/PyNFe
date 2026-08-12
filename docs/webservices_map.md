# Source Map: `webservices.py` (615 lines)

SEFAZ webservice endpoint URLs organized by document type, state, and environment.

## Sections

| Section | Lines | Variable | Purpose |
|---------|-------|----------|---------|
| Host roles (consulta vs autorizador) | 1-22 | — | Module docstring: which key family each consumer may read |
| NFC-e endpoints | 24-323 | `NFCE` | NFC-e webservice URLs and QR Code URLs by state |
| `qrcode_host` helper | 326-337 | — | Consultation-portal host prefix for `<qrCode>`/`<urlChave>` |
| NF-e endpoints | 343-514 | `NFE` | NF-e webservice URLs by state |
| NFS-e endpoints | 517-542 | `NFSE` | NFS-e URLs (Betha, Ginfes) |
| MDF-e endpoints | 545-559 | `MDFE` | MDF-e URLs (SVRS only) |
| CT-e endpoints | 561-615 | `CTE` | CT-e URLs by state |

## URL Structure

Each state/virtual environment entry contains:
- `STATUS` — Service status check endpoint
- `AUTORIZACAO` — Authorization endpoint
- `RECIBO` — Receipt query endpoint
- `CHAVE` — Access key query endpoint
- `INUTILIZACAO` — Number invalidation endpoint
- `EVENTOS` — Event reception endpoint
- `CADASTRO` — Registration query endpoint (some states)
- `HTTPS` — Production base URL prefix of the AUTHORIZER (webservices; read only by
  `ComunicacaoSefaz._get_url`)
- `HOMOLOGACAO` — Homologation base URL prefix of the AUTHORIZER
- `QR_HOST` / `QR_HOST_HOMOLOGACAO` — Base URL prefix of the CONSULTATION portal, used for
  `<qrCode>`/`<urlChave>` (read only by `qrcode_host`); falls back to `HTTPS`/`HOMOLOGACAO`
  for UFs that serve both roles from the same host
- `QR` — QR Code path (NFC-e only; `QR_HOMOLOGACAO` where the path differs per environment)
- `URL` — Consultation path (NFC-e only)

The two host families must never be shared: a UF such as GO answers webservice POSTs sent to
its consultation host with a load-balancer redirect and HTML, so the invoice never receives a
SEFAZ verdict and the failure surfaces as a transport/XML-parse error, not a rejeicao.

## State/Virtual Environment Groups

### NFC-e (`NFCE`) — Lines 24-323
| Key | Lines | Description |
|-----|-------|-------------|
| Individual states | 25-311 | RO, AC, AM, RR, PA, AP, TO, MA, PI, CE, RN, PB, PE, AL, SE, BA, MG, ES, RJ, SP, PR, SC, RS, MS, MT, GO, DF |
| `SVRS` | 312-322 | Virtual SEFAZ RS (fallback for states without own NFC-e) |

### NF-e (`NFE`) — Lines 343-514
| Key | Lines | Description |
|-----|-------|-------------|
| `AN` | 345-352 | National environment (events, distribution) |
| Individual states | 353-472 | AM, MA, PE, BA, MG, SP, PR, RS, MS, MT, GO |
| `SVAN` | 473-483 | Virtual SEFAZ AN (MA for NF-e) |
| `SVRS` | 484-494 | Virtual SEFAZ RS (most states) |
| `SVC-AN` | 495-503 | Contingency AN |
| `SVC-RS` | 504-513 | Contingency RS |

### NFS-e (`NFSE`) — Lines 517-542
| Key | Lines | Description |
|-----|-------|-------------|
| `BETHA` | 519-530 | Betha provider (HTTP WSDL) |
| `GINFES` | 531-541 | Ginfes provider (HTTPS WSDL) |

### MDF-e (`MDFE`) — Lines 545-559
Only `SVRS` (547-558) — single authorizer for all states.

### CT-e (`CTE`) — Lines 561-615
| Key | Lines | Description |
|-----|-------|-------------|
| `AN` | 562-566 | National environment (distribution) |
| Individual states | 567-602 | MT, MS, MG, PR, RS, SP |
| `SVRS` | 603-608 | Virtual SEFAZ RS |
| `SVSP` | 609-614 | Virtual SEFAZ SP (AP, PE, RR) |

## Helpers

| Function | Lines | Purpose |
|----------|-------|---------|
| `qrcode_host(uf, producao=True)` | 326-337 | Consultation-portal host prefix for `<qrCode>`/`<urlChave>`, with fallback to the webservice host |
