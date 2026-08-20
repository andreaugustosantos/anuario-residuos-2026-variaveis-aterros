"""
03 - Triagem para auditoria.

Os dados do SINISA são declarados pelos próprios municípios, sem conferência do sistema, o que exige verificação antes da publicação. Este script prepara essa
verificação em três grupos:

1 - Auditar: registros selecionados por sinais de inconsistência ou por critérios adicionais de controle. Conferidos individualmente.
2 - Amostra: sorteio aleatório entre os registros sem indício, para estimar a frequência de divergências nesse grupo. O sorteio usa
    semente fixa (config.SEMENTE) sobre a lista ordenada por codigo IBGE.
3 - Sem indicio: registros não selecionados para conferência.

Cada linha traz três endereços do Google Maps: a rota como foi calculada, a coordenada declarada isolada (revela pino sobre água ou fora de qualquer
instalação) e a busca da unidade pelo nome.

Entrada: saida/01_pares.csv e saida/02_rotas.csv
Saida:   saida/03_auditoria.csv"""

import csv
import random
import sys
from collections import Counter
from urllib.parse import quote

import config


CAMPOS_SAIDA = [
    "prioridade", "motivo_do_sinal", "cod_ibge", "municipio", "uf", "volume",
    "nome_unidade", "tipo_unidade", "municipio_da_unidade", "fluxo",
    "origem", "destino", "dist_linha_reta_km", "distancia_km", "tempo_min",
    "link_rota", "link_ver_o_ponto", "link_buscar_pelo_nome",
    "RESULTADO", "DIST_AUDITADA_KM", "TEMPO_AUDITADO_MIN", "COORD_CORRIGIDA",
    "OBSERVACAO",
]

CAPITAIS = {
    "1100205", "1200401", "1302603", "1400100", "1501402", "1600303", "1721000",
    "2111300", "2211001", "2304400", "2408102", "2507507", "2611606", "2704302",
    "2800308", "2927408", "3106200", "3205309", "3304557", "3550308", "4106902",
    "4205407", "4314902", "5002704", "5103403", "5208707", "5300108",
}

# SINAIS

def sinais(par, rota, unidades_compartilhadas):
    """Critérios que selecionam o registro para conferencia individual."""
    achados = []
    try:
        linha_reta = float(par["dist_linha_reta_km"])
    except (TypeError, ValueError):
        linha_reta = None
    km = float(rota["distancia_km"]) if rota["distancia_km"] else None
    minutos = float(rota["tempo_min"]) if rota["tempo_min"] else None

    if km is None:
        achados.append("sem valor calculado")
    else:
        razao = km / linha_reta if linha_reta else None
        if razao and razao < config.RAZAO_MINIMA:
            achados.append("rodoviaria menor que a linha reta")
        if razao and razao > config.RAZAO_SUSPEITA:
            achados.append("rodoviaria acima de %gx a linha reta" % config.RAZAO_SUSPEITA)
        if minutos and km / (minutos / 60.0) < config.VELOCIDADE_MINIMA_KMH:
            achados.append("velocidade implicita implausivel")

    if linha_reta is not None and linha_reta < config.DISTANCIA_SUSPEITA_KM:
        achados.append("unidade a menos de %g km da sede" % config.DISTANCIA_SUSPEITA_KM)
    if par["cod_ibge"] in CAPITAIS:
        achados.append("capital")
    if unidades_compartilhadas[par["codigo_unidade"]] >= config.MUNICIPIOS_POR_UNIDADE_PARA_SINALIZAR:
        achados.append("aterro usado por %d municipios"
                       % unidades_compartilhadas[par["codigo_unidade"]])
    return achados

# LINKS

def link_rota(origem, destino):
    return ("https://www.google.com/maps/dir/?api=1&origin=%s&destination=%s"
            "&travelmode=driving" % (quote(origem), quote(destino)))


def link_ponto(destino):
    return "https://www.google.com/maps/search/?api=1&query=%s" % quote(destino)


def link_busca(nome_unidade, municipio_da_unidade, uf):
    return ("https://www.google.com/maps/search/?api=1&query=%s"
            % quote("%s, %s, %s" % (nome_unidade, municipio_da_unidade, uf)))


# PROGRAMA

def ler(nome):
    caminho = config.SAIDA / nome
    if not caminho.exists():
        sys.exit("Nao encontrei %s. Rode antes os scripts anteriores." % caminho)
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    pares = ler("01_pares.csv")
    rotas = {r["cod_ibge"]: r for r in ler("02_rotas.csv")}

    faltando = [p["cod_ibge"] for p in pares if p["cod_ibge"] not in rotas]
    if faltando:
        sys.exit("O 02_calcular_rotas.py ainda nao terminou: faltam %d municipios."
                 % len(faltando))

    unidades_compartilhadas = Counter(p["codigo_unidade"] for p in pares)

    linhas, sem_indicio = [], []
    for par in pares:
        rota = rotas[par["cod_ibge"]]
        origem = "%s,%s" % (par["origem_lat"], par["origem_lon"])
        destino = "%s,%s" % (par["destino_lat"], par["destino_lon"])
        achados = sinais(par, rota, unidades_compartilhadas)

        linha = {
            "prioridade": "1 - Auditar" if achados else "3 - Sem indicio",
            "motivo_do_sinal": " + ".join(achados),
            "cod_ibge": par["cod_ibge"],
            "municipio": par["municipio"],
            "uf": par["uf"],
            "volume": par["volume"],
            "nome_unidade": par["nome_unidade"],
            "tipo_unidade": par["tipo_unidade"],
            "municipio_da_unidade": par["municipio_da_unidade"],
            "fluxo": par["fluxo"],
            "origem": origem,
            "destino": destino,
            "dist_linha_reta_km": par["dist_linha_reta_km"],
            "distancia_km": rota["distancia_km"],
            "tempo_min": rota["tempo_min"],
            "link_rota": link_rota(origem, destino),
            "link_ver_o_ponto": link_ponto(destino),
            "link_buscar_pelo_nome": link_busca(par["nome_unidade"],
                                                par["municipio_da_unidade"],
                                                par["uf"]),
            "RESULTADO": "",
            "DIST_AUDITADA_KM": "",
            "TEMPO_AUDITADO_MIN": "",
            "COORD_CORRIGIDA": "",
            "OBSERVACAO": "",
        }
        linhas.append(linha)
        if not achados:
            sem_indicio.append(linha)

    sem_indicio.sort(key=lambda linha: linha["cod_ibge"])
    tamanho = min(config.TAMANHO_AMOSTRA, len(sem_indicio))
    for linha in random.Random(config.SEMENTE).sample(sem_indicio, tamanho):
        linha["prioridade"] = "2 - Amostra aleatoria"
        linha["motivo_do_sinal"] = ("sorteado para estimar a frequencia de divergencias "
                            "no grupo sem indicio")

    linhas.sort(key=lambda linha: (linha["prioridade"], linha["cod_ibge"]))

    with open(config.SAIDA / "03_auditoria.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_SAIDA)
        escritor.writeheader()
        escritor.writerows(linhas)

    contagem = Counter(linha["prioridade"] for linha in linhas)
    for prioridade in sorted(contagem):
        print("%-24s %d" % (prioridade, contagem[prioridade]))
    print()
    conferir = contagem["1 - Auditar"] + contagem["2 - Amostra aleatoria"]
    if linhas:
        print("A conferir: %d de %d registros (%.1f%%)"
              % (conferir, len(linhas), 100 * conferir / len(linhas)))
    else:
        print("Nenhum registro para conferir: o 01_pares.csv esta vazio.")
    print()
    print("Gravado em %s" % (config.SAIDA / "03_auditoria.csv"))
    print("Preencha as colunas em maiusculas das prioridades 1 e 2 e rode o 04_consolidar.py.")


if __name__ == "__main__":
    main()
