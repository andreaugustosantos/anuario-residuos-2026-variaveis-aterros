"""
Configuração de caminhos e parâmetros.

Este é o único arquivo que precisa ser editado para reproduzir o trabalho em outra máquina. Os demais scripts leem tudo daqui.

As bases de dados não acompanham o repositório: são públicas e devem ser baixadas na origem. Veja o README para os endereços."""

from pathlib import Path

# CAMINHOS DAS BASES

# Ajuste os três caminhos abaixo para as pastas onde você baixou as bases.

# Pasta com as planilhas do SINISA Resíduos 2023, com os nomes originais.
# Download: https://www.gov.br/cidades  (Sistema Nacional de Informações em
# Saneamento Básico, módulo Resíduos Sólidos, ano de referência 2023)
SINISA = Path(r"C:\caminho\para\SINISA_RESIDUOS_Planilhas_2023")

# Tabela de coordenadas municipais de referência, usada apenas para detectar o
# preenchimento padrão do formulário do SINISA.
# Origem: github.com/kelvins/municipios-brasileiros (derivada do IBGE)
COORDENADAS_REFERENCIA = Path(r"C:\caminho\para\coordenadas_municipais_referencia.csv")

# Pasta com o shapefile Localidades do Brasil 2022, do IBGE.
# Os cinco arquivos (.shp .dbf .shx .prj .cpg) devem estar juntos.
# Download: https://geoftp.ibge.gov.br/organizacao_do_territorio
#           /estrutura_territorial/localidades/Localidades_do_Brasil/2022/
IBGE = Path(r"C:\caminho\para\Localidades_Brasil_shp")

# Pasta onde os scripts gravam os resultados.
SAIDA = Path(__file__).parent / "saida"

# Arquivo de texto contendo apenas a chave da Google Routes API.
# Nunca deve ir para o repositório: o .gitignore já bloqueia este nome.
CHAVE_GOOGLE = Path(__file__).parent / "chave_google.txt"

# Lista dos 2.000 municípios do Anuário. Acompanha o repositório.
MUNICIPIOS = Path(__file__).parent / "dados_referencia" / "municipios_anuario_2026.csv"

# ARQUIVOS DO SINISA


MANEJO = SINISA / "SINISA_RESIDUOS_Informacoes_Formulario_Manejo_2023.xlsx"
DISPOSICAO_FINAL = SINISA / (
    "SINISA_RESIDUOS_Informacoes_Formulario_Infraestrutura_Destinacao_Final_2023.xlsx"
)
PROCESSAMENTO = SINISA / (
    "SINISA_RESIDUOS_Informacoes_Formulario_Infraestrutura_"
    "Unidades_de_Processamento_e_Tratamento_2023.xlsx"
)
TRANSBORDO = SINISA / (
    "SINISA_RESIDUOS_Informacoes_Formulario_Infraestrutura_"
    "Unidades_de_Transbordo_2023.xlsx"
)

SHAPEFILE = IBGE / "BR_localidades_2022"

# PARÂMETROS DO MÉTODO

# Nas planilhas do SINISA os dados começam na linha 14.
PRIMEIRA_LINHA = 14

# Limite usado para identificar coordenadas do SINISA coincidentes com o ponto
# municipal de referência.
LIMITE_COINCIDENCIA_KM = 0.3

# Sorteio da amostra de conferência. Número de partida fixo, para que qualquer
# pessoa refaça o sorteio e chegue aos mesmos municípios.
SEMENTE = 2026
TAMANHO_AMOSTRA = 50

# Sinais usados na triagem da conferência.
RAZAO_MINIMA = 1.0            # distância por estrada menor que a linha reta é impossível
RAZAO_SUSPEITA = 3.0          # distância por estrada muito acima da linha reta
DISTANCIA_SUSPEITA_KM = 2.0   # unidade próxima demais da sede
VELOCIDADE_MINIMA_KMH = 15.0  # velocidade média implausível para o trajeto
MUNICIPIOS_POR_UNIDADE_PARA_SINALIZAR = 8

# Google Routes API.
URL_ROUTES = "https://routes.googleapis.com/directions/v2:computeRoutes"
CAMPOS_ROUTES = "routes.distanceMeters,routes.duration"
PREFERENCIA_ROTA = "TRAFFIC_UNAWARE"   # sem trânsito em tempo real
PAUSA_ENTRE_CONSULTAS = 0.08
SALVAR_A_CADA = 25
