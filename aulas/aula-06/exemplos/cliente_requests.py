"""Consulta a API da aula usando uma URL informada pelo aluno."""
import argparse
import sys

import requests


def main():
    parser = argparse.ArgumentParser(description="Cliente da API industrial")
    parser.add_argument("base_url", help="URL base da API, por exemplo http://localhost:8000")
    parser.add_argument("--tag", default="XMEAS(9)")
    parser.add_argument("--limite", type=int, choices=range(1, 201), default=5, metavar="1..200")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    try:
        with requests.Session() as sessao:
            def consultar(caminho, params=None):
                resposta = sessao.get(base + caminho, params=params, timeout=10)
                resposta.raise_for_status()
                return resposta.json()

            print("Saúde:", consultar("/health"))
            tags = consultar("/api/v1/tags")
            print("Tags cadastradas:", len(tags))
            leituras = consultar("/api/v1/historico", {"tag": args.tag, "limite": args.limite})
            for leitura in leituras:
                print(f"{leitura['tag_id']}: valor={leitura['valor']} qualidade={leitura['qualidade']} "
                      f"validade={leitura['validade']} origem={leitura['source_timestamp']} "
                      f"coleta={leitura['coleta_utc']}")
            if not leituras:
                print("Nenhuma amostra encontrada para a tag.")
    except (requests.RequestException, ValueError) as erro:
        print(f"Falha ao consultar a API: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
