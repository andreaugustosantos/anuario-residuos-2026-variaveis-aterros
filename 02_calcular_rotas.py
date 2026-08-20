"""
02 - Calculo das rotas pela Google Routes API.

Consulta a distância rodoviária e o tempo de deslocamento de cada par produzido pelo script 01, em condições normais de transito (routingPreference
TRAFFIC_UNAWARE, que usa velocidades tipicas da via e ignora transito em tempo real, de modo que o resultado nao depende do momento da consulta).

O progresso é gravado a cada config.SALVAR_A_CADA municípios. Se a execução for interrompida, basta rodar de novo: os municípios ja calculados são ignorados.

Entrada: saida/01_pares.csv
Saida:   saida/02_rotas.csv"""

import csv
import sys
import time

import requests

import config


CAMPOS_SAIDA = ["cod_ibge", "municipio", "uf", "distancia_km", "tempo_min", "status"]

# CONSULTA


def ler_chave():
    if not config.CHAVE_GOOGLE.exists():
        sys.exit(
            "Não encontrei o arquivo da chave em:\n  %s\n\n"
            "Crie um arquivo de texto com esse nome contendo apenas a chave da "
            "Google Routes API." % config.CHAVE_GOOGLE
        )
    chave = config.CHAVE_GOOGLE.read_text(encoding="utf-8-sig").strip()
    if not chave.startswith("AIza"):
        sys.exit("A chave em %s nao parece ser do Google." % config.CHAVE_GOOGLE)
    return chave


def ponto(lat, lon):
    return {"location": {"latLng": {"latitude": float(lat), "longitude": float(lon)}}}


def segundos(duracao):
    """A Routes API devolve a duração como texto, no formato '1234s'."""
    return float(str(duracao).rstrip("s"))


def consultar(par, chave):
    """Devolve (distancia_km, tempo_min, status)."""
    corpo = {
        "origin": ponto(par["origem_lat"], par["origem_lon"]),
        "destination": ponto(par["destino_lat"], par["destino_lon"]),
        "travelMode": "DRIVE",
        "routingPreference": config.PREFERENCIA_ROTA,
        "units": "METRIC",
    }
    cabecalho = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": chave,
        "X-Goog-FieldMask": config.CAMPOS_ROUTES,
    }

    for tentativa in range(1, 4):
        try:
            resposta = requests.post(config.URL_ROUTES, json=corpo,
                                     headers=cabecalho, timeout=30)
        except requests.RequestException as erro:
            if tentativa == 3:
                return None, None, "ERRO DE REDE: %s" % type(erro).__name__
            time.sleep(2 * tentativa)
            continue

        if resposta.status_code in (400, 401, 403):
            try:
                motivo = resposta.json()["error"]["message"]
            except (ValueError, KeyError, TypeError):
                motivo = resposta.text[:200]
            sys.exit(
                "\nO Google recusou a consulta:\n  %s\n\n"
                "Verifique se a Routes API está ativada, se a chave a inclui em "
                "API restrictions e se o faturamento esta ativo no mesmo projeto.\n"
                % motivo
            )

        if resposta.status_code != 200:
            if tentativa == 3:
                return None, None, "HTTP %s" % resposta.status_code
            time.sleep(2 * tentativa)
            continue

        rotas = resposta.json().get("routes") or []
        if not rotas:
            return None, None, "SEM ROTA RODOVIARIA"

        metros = rotas[0]["distanceMeters"]
        return (round(metros / 1000.0, 1),
                int(round(segundos(rotas[0]["duration"]) / 60.0)),
                "OK")

    return None, None, "FALHOU APOS 3 TENTATIVAS"


# CONTROLE DE QUALIDADE

def avaliar(distancia_km, linha_reta_km):
    """
    A distância rodoviária é sempre maior que a distância em linha reta.
    Valor menor indica erro; valor muito acima sugere coordenada equivocada ou
    acesso mal mapeado, e merece conferência individual.
    """
    try:
        linha_reta = float(linha_reta_km)
    except (TypeError, ValueError):
        return "OK"
    if not distancia_km or linha_reta <= 0:
        return "OK"
    razao = distancia_km / linha_reta
    if razao < config.RAZAO_MINIMA:
        return "CONFERIR: menor que a linha reta (%.2fx)" % razao
    if razao > config.RAZAO_SUSPEITA:
        return "CONFERIR: %.1fx a linha reta" % razao
    return "OK"


# PROGRAMA

def ler_pares():
    caminho = config.SAIDA / "01_pares.csv"
    if not caminho.exists():
        sys.exit("Rode antes o 01_montar_pares.py: nao encontrei %s" % caminho)
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ler_calculados():
    """Municipios com resultado definitivo em execucao anterior."""
    caminho = config.SAIDA / "02_rotas.csv"
    if not caminho.exists():
        return {}

    with open(caminho, encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))

    return {
        linha["cod_ibge"]: linha
        for linha in linhas
        if (
            linha["status"] == "OK"
            or linha["status"].startswith("CONFERIR:")
            or linha["status"] == "SEM ROTA RODOVIARIA"
        )
    }


def gravar(resultados):
    with open(config.SAIDA / "02_rotas.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_SAIDA)
        escritor.writeheader()
        escritor.writerows(resultados.values())


def main():
    chave = ler_chave()
    pares = ler_pares()
    resultados = ler_calculados()

    pendentes = [p for p in pares if p["cod_ibge"] not in resultados]
    if not pendentes:
        print("Nada pendente: os %d municipios ja foram calculados." % len(resultados))
        return
    if resultados:
        print("Retomando: %d ja calculados, %d pendentes.\n"
              % (len(resultados), len(pendentes)))
    else:
        print("%d municipios a consultar.\n" % len(pendentes))

    contagem = {"OK": 0, "conferir": 0, "sem rota": 0, "erro": 0}

    for indice, par in enumerate(pendentes, 1):
        km, minutos, status = consultar(par, chave)

        if status == "OK":
            status = avaliar(km, par["dist_linha_reta_km"])
            contagem["OK" if status == "OK" else "conferir"] += 1
            marca = "" if status == "OK" else "   <-- " + status
            print("%-28s %-3s %7.1f km %5d min%s"
                  % (par["municipio"][:28], par["uf"], km, minutos, marca))
        else:
            contagem["sem rota" if "SEM ROTA" in status else "erro"] += 1
            print("%-28s %-3s %s" % (par["municipio"][:28], par["uf"], status))

        resultados[par["cod_ibge"]] = {
            "cod_ibge": par["cod_ibge"],
            "municipio": par["municipio"],
            "uf": par["uf"],
            "distancia_km": km if km is not None else "",
            "tempo_min": minutos if minutos is not None else "",
            "status": status,
        }

        if indice % config.SALVAR_A_CADA == 0:
            gravar(resultados)
            print("   ... salvo (%d de %d)" % (indice, len(pendentes)))

        time.sleep(config.PAUSA_ENTRE_CONSULTAS)

    gravar(resultados)

    print()
    print("Consultas feitas .......... %d" % len(pendentes))
    print("Sem ressalva .............. %d" % contagem["OK"])
    print("Para conferir ............. %d" % contagem["conferir"])
    print("Sem rota rodoviaria ....... %d" % contagem["sem rota"])
    print("Erros ..................... %d" % contagem["erro"])
    print()
    print("Gravado em %s" % (config.SAIDA / "02_rotas.csv"))
    if contagem["erro"]:
        print("As linhas com erro são refeitas ao rodar o script outra vez.")


if __name__ == "__main__":
    main()
