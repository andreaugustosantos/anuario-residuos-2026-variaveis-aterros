"""
04 - Consolidacao da serie final.

Combina o cálculo automático com o resultado da auditoria e produz as duas variáveis na forma em que entram na matriz do Anuário.

Regra de precedência, por registro:
  1. RESULTADO = "Coordenada errada" com valor auditado  -> vale a medição manual, porque a rota automática chegou ao ponto errado;
  2. RESULTADO = "Coordenada invalida", ou errada sem instalação localizada -> registro em branco;
  3. demais casos -> vale o valor calculado pela Routes API;
  4. sem valor calculado e sem auditoria -> registro em branco.

Dado ausente e sempre célula vazia, nunca zero: zero afirmaria que a unidade fica na propria sede do município.

Entrada: saida/01_pares.csv, saida/02_rotas.csv e
         saida/03_auditoria.csv com as colunas em maiusculas preenchidas
         para os registros selecionados.
Saida:   saida/04_final.csv e saida/04_sem_dado.csv"""

import csv
import sys
from collections import Counter

import config


CAMPOS_FINAL = [
    "cod_ibge", "municipio", "uf", "volume",
    "E3_DIST_ATERRO_KM", "E3_TEMPO_ATERRO_MIN",
    "procedencia", "nivel_de_verificacao",
    "nome_unidade", "tipo_unidade", "municipio_da_unidade", "fluxo",
    "origem", "destino", "dist_linha_reta_km",
]

CAMPOS_SEM_DADO = ["cod_ibge", "municipio", "uf", "volume", "motivo",
                   "codigo_unidade", "nome_unidade", "tipo_unidade",
                   "municipio_da_unidade"]

DESCARTE = "Coordenada invalida"
CORRECAO = "Coordenada errada"
CONFIRMACAO = "Coordenada confirmada"

RESULTADOS_VALIDOS = {
    CONFIRMACAO,
    CORRECAO,
    DESCARTE,
}


def ler(nome):
    caminho = config.SAIDA / nome
    if not caminho.exists():
        sys.exit("Nao encontrei %s. Rode antes os scripts anteriores." % caminho)
    with open(caminho, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def numero(valor):
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def resolver(par, rota, auditoria):
    """Devolve (distancia_km, tempo_min, procedencia)."""
    resultado = (auditoria or {}).get("RESULTADO", "").strip()
    if resultado and resultado not in RESULTADOS_VALIDOS:
        sys.exit(
            'RESULTADO invalido para %s: "%s".'
            % (par["municipio"], resultado)
    )
    km_auditado = numero((auditoria or {}).get("DIST_AUDITADA_KM"))
    min_auditado = numero((auditoria or {}).get("TEMPO_AUDITADO_MIN"))
    km_calculado = numero(rota["distancia_km"])
    min_calculado = numero(rota["tempo_min"])

    if resultado == DESCARTE:
        return None, None, "Em branco - coordenada do SINISA invalida"

    if resultado == CORRECAO:
        if km_auditado is not None and min_auditado is not None:
            return (km_auditado, int(min_auditado),
                    "Auditoria manual - coordenada do SINISA incorreta")
        return None, None, "Em branco - coordenada incorreta e instalacao nao localizada"

    if km_calculado is not None and min_calculado is not None:
        return km_calculado, int(min_calculado), "Google Routes API"

    if km_auditado is not None and min_auditado is not None:
        return km_auditado, int(min_auditado), "Auditoria manual - sem rota pela API"

    return None, None, "Em branco - sem rota rodoviaria"


def verificacao(auditoria):
    if auditoria and auditoria.get("RESULTADO", "").strip():
        return "Auditada individualmente"
    return "Nao auditada - sem indicio de inconsistencia"


def main():
    pares = ler("01_pares.csv")
    rotas = {r["cod_ibge"]: r for r in ler("02_rotas.csv")}
    auditorias = {a["cod_ibge"]: a for a in ler("03_auditoria.csv")}

    pendentes = [
        a for a in auditorias.values()
        if a["prioridade"].startswith(("1", "2"))
        and not a["RESULTADO"].strip()
    ]

    if pendentes:
        sys.exit(
            "A auditoria ainda nao terminou: %d registros selecionados "
            "estao sem RESULTADO." % len(pendentes)
        )

    linhas, procedencias = [], Counter()
    for par in pares:
        rota = rotas.get(par["cod_ibge"])
        if rota is None:
            sys.exit("O 02_calcular_rotas.py ainda nao terminou: falta %s."
                     % par["municipio"])

        auditoria = auditorias.get(par["cod_ibge"])
        km, minutos, procedencia = resolver(par, rota, auditoria)
        procedencias[procedencia] += 1

        linhas.append({
            "cod_ibge": par["cod_ibge"],
            "municipio": par["municipio"],
            "uf": par["uf"],
            "volume": par["volume"],
            "E3_DIST_ATERRO_KM": km if km is not None else "",
            "E3_TEMPO_ATERRO_MIN": minutos if minutos is not None else "",
            "procedencia": procedencia,
            "nivel_de_verificacao": verificacao(auditoria),
            "nome_unidade": par["nome_unidade"],
            "tipo_unidade": par["tipo_unidade"],
            "municipio_da_unidade": par["municipio_da_unidade"],
            "fluxo": par["fluxo"],
            "origem": "%s, %s" % (par["origem_lat"], par["origem_lon"]),
            "destino": "%s, %s" % (par["destino_lat"], par["destino_lon"]),
            "dist_linha_reta_km": par["dist_linha_reta_km"],
        })

    with open(config.SAIDA / "04_final.csv", "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_FINAL)
        escritor.writeheader()
        escritor.writerows(linhas)

    excluidos = ler("01_excluidos.csv")
    with open(config.SAIDA / "04_sem_dado.csv", "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_SEM_DADO, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(excluidos)

    com_valor = sum(1 for linha in linhas if linha["E3_DIST_ATERRO_KM"] != "")
    total = len(linhas) + len(excluidos)

    print("PROCEDENCIA DO VALOR")
    for procedencia, quantidade in procedencias.most_common():
        print("  %5d  %s" % (quantidade, procedencia))
    print()
    print("Com valor ............. %d" % com_valor)
    print("Em branco ............. %d" % (len(linhas) - com_valor + len(excluidos)))
    print("Cobertura ............. %d de %d municipios (%.1f%%)"
          % (com_valor, total, 100 * com_valor / total))
    print()
    print("Gravado em %s" % config.SAIDA)


if __name__ == "__main__":
    main()
