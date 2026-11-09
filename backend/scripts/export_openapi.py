from __future__ import annotations

import argparse
import json

from mediateca.api.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta el contrato OpenAPI de la API")
    parser.add_argument("output", nargs="?", default="-")
    args = parser.parse_args()

    payload = json.dumps(app.openapi(), ensure_ascii=False, indent=2)
    if args.output == "-":
        print(payload)
    else:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(payload)


if __name__ == "__main__":
    main()
