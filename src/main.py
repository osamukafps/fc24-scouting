import pandas as pd
import streamlit as st

# Carregar dados do CSV
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, '../data/fc_24_all_players.csv')

fc_24_players = pd.read_csv(file_path, low_memory=False)


# Montar Atributos Agrupados
def calcular_atributos_agrupados(dataframe):
    fc_24_players['pace'] = round((fc_24_players['acceleration'] + fc_24_players['sprint_speed']) / 2).astype(int)

    fc_24_players['shooting'] = round((fc_24_players['positioning'] + fc_24_players['finishing'] +
                                       fc_24_players['shot_power'] + fc_24_players['long_shots'] +
                                       fc_24_players['volleys'] + fc_24_players['penalties']) / 6).astype(int)

    fc_24_players['passing'] = round((fc_24_players['vision'] + fc_24_players['crossing'] +
                                      fc_24_players['fk_accuracy'] + fc_24_players['short_passing'] +
                                      fc_24_players['long_passing'] + fc_24_players['curve']) / 6).astype(int)

    fc_24_players['dribbling'] = round((fc_24_players['agility'] + fc_24_players['balance'] +
                                        fc_24_players['reactions'] + fc_24_players['ball_control'] +
                                        fc_24_players['dribbling'] + fc_24_players['composure']) / 6).astype(int)

    fc_24_players['defending'] = round((fc_24_players['interceptions'] + fc_24_players['heading_accuracy'] +
                                        fc_24_players['defensive_awareness'] + fc_24_players['standing_tackle'] +
                                        fc_24_players['sliding_tackle']) / 5).astype(int)

    fc_24_players['physicality'] = round((fc_24_players['jumping'] + fc_24_players['stamina'] +
                                          fc_24_players['strength'] + fc_24_players['aggression']) / 4).astype(int)


calcular_atributos_agrupados(fc_24_players)

media_geral_time = 75
media_idade = 25

###############################################################
st.title("Scouting de Jogadores")

valor_disponivel = st.number_input("Valor Disponível (€)", min_value=0, format="%d", step=1000)
posicoes_jogadores = st.text_input("Posições (separadas por vírgula)", 'CAM, CM').split(',')
idade_min = st.number_input("Idade Mínima", min_value=0, value=18)
idade_max = st.number_input("Idade Máxima", min_value=0, value=40)
overall_min = st.number_input("Overall Mínimo", min_value=0, value=70)
overall_max = st.number_input("Overall Máximo", min_value=0, value=99)
potencial_min = st.number_input("Potencial Mínimo", min_value=0, value=70)

###############################################################

# Filtrar jogadores com base nos critérios
jogadores_filtrados = fc_24_players[
    (fc_24_players['overall_rating'].between(overall_min, overall_max)) &
    (fc_24_players['age'].between(idade_min, idade_max)) &
    (fc_24_players['potential'] >= potencial_min) &
    (fc_24_players['value'] <= valor_disponivel)
    ]


# Filtrar por posição desejada
def filtrar_por_posicao(positions, posicoes):
    if isinstance(positions, str):
        positions = eval(positions)  # Converte a string para uma lista
    # Verifica se alguma posição desejada está presente nas posições do jogador
    return any(posicao in positions for posicao in posicoes)


jogadores_filtrados = jogadores_filtrados[
    jogadores_filtrados['positions'].apply(lambda x: filtrar_por_posicao(x, posicoes_jogadores))
]

# Configuração dos pesos por posição do Jogador
pesos_por_posicao = {
    ('ST', 'CF', 'LW', 'RW'): {
        'potencial': 0.2,
        'overall': 0.2,
        'valor': 0.1,
        'ritmo': 0.2,
        'finalizacao': 0.15,
        'passe': 0.1,
        'drible': 0.15,
        'defesa': 0.05,
        'fisico': 0.1
    },
    ('CAM', 'RM', 'LM', 'CM', 'CDM'): {
        'potencial': 0.2,
        'overall': 0.2,
        'valor': 0.1,
        'ritmo': 0.2,
        'finalizacao': 0.05,
        'passe': 0.15,
        'drible': 0.1,
        'defesa': 0.05,
        'fisico': 0.05
    },
    ('CB', 'RB', 'LB', 'RWB', 'LWB'): {
        'potencial': 0.2,
        'overall': 0.2,
        'valor': 0.1,
        'ritmo': 0.1,
        'finalizacao': 0.04,
        'passe': 0.05,
        'drible': 0.01,
        'defesa': 0.2,
        'fisico': 0.1
    }
}


def obter_pesos(posicoes, pesos_por_posicao):
    for posicoes, pesos in pesos_por_posicao.items():
        if any(posicao in posicoes for posicao in posicoes):
            return pesos
    return {}


# Função de cálculo de custo-benefício
def calcular_custo_beneficio(row):
    pesos = obter_pesos(posicoes_jogadores, pesos_por_posicao)
    print(f"pesos: {pesos}")
    if not pesos:
        return 0

    potencial = row['potential']
    overall = row['overall_rating']
    valor = row['value'] / 1_000_000
    ritmo = row['pace']
    finalizacao = row['shooting']
    passe = row['passing']
    drible = row['dribbling']
    defesa = row['defending']
    fisico = row['physicality']

    custo_beneficio = (
            (pesos.get('potencial', 0) * potencial) +
            (pesos.get('overall', 0) * overall) +
            (pesos.get('valor', 0) * valor) +
            (pesos.get('ritmo', 0) * ritmo) +
            (pesos.get('finalizacao', 0) * finalizacao) +
            (pesos.get('passe', 0) * passe) +
            (pesos.get('drible', 0) * drible) +
            (pesos.get('defesa', 0) * defesa) +
            (pesos.get('fisico', 0) * fisico)
    )
    return custo_beneficio


# Calcular custo-benefício para jogadores filtrados
jogadores_filtrados['custo_beneficio'] = jogadores_filtrados.apply(calcular_custo_beneficio, axis=1)

# Ordenar jogadores com base no custo-benefício
jogadores_recomendados = (jogadores_filtrados.sort_values(by='custo_beneficio', ascending=False))


def formatar_valor(valor):
    if valor >= 1_000_000:
        return f"€{valor / 1_000_000:.1f}M"
    elif valor >= 1_000:
        return f"€{valor / 1_000:.1f}K"
    else:
        return f"€{valor:.0f}"


def formatar_salario(valor):
    return formatar_valor(valor)


# Formatação de Valor de mercado e Salário
jogadores_recomendados['value'] = jogadores_recomendados['value'].apply(formatar_valor)
jogadores_recomendados['wage'] = jogadores_recomendados['wage'].apply(formatar_salario)

# Formatação da Exibição
jogadores_recomendados['positions'] = jogadores_recomendados['positions'].apply(
    lambda x: eval(x) if isinstance(x, str) else x)
jogadores_recomendados = jogadores_recomendados.explode('positions')

# Exibir as colunas desejadas incluindo 'positions'
print(jogadores_recomendados[['name', 'age', 'overall_rating', 'potential', 'value', 'wage',
                              'positions', 'custo_beneficio', 'club_name', 'club_league_name',
                              'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physicality']])

st.dataframe(jogadores_recomendados[['name', 'age', 'overall_rating', 'potential', 'value', 'wage',
                                     'positions', 'custo_beneficio', 'club_name', 'club_league_name',
                                     'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physicality']])
