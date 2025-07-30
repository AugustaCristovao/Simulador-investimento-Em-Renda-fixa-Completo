
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import math

# ---------------- Funções Auxiliares ---------------- #
def obter_aliquota_ir(dias):
    if dias <= 180:
        return 0.225
    elif dias <= 360:
        return 0.20
    elif dias <= 720:
        return 0.175
    else:
        return 0.15

def calcular_rentabilidade_mensal(tipo_rentabilidade, taxa, cdi_anual, ipca_anual):
    if tipo_rentabilidade == "Prefixada":
        return (1 + taxa/100) ** (1/12) - 1
    elif tipo_rentabilidade == "Pós-fixada (% CDI)":
        cdi_mensal = (1 + cdi_anual/100) ** (1/12) - 1
        return cdi_mensal * (taxa/100)
    elif tipo_rentabilidade == "Híbrida (IPCA + %)":
        ipca_mensal = (1 + ipca_anual/100) ** (1/12) - 1
        taxa_adicional_mensal = (1 + taxa/100) ** (1/12) - 1
        return ipca_mensal + taxa_adicional_mensal

def simular_investimento(valor_inicial, aporte_mensal, prazo_dias, rentabilidade_mensal, tipo_investimento):
    prazo_meses = prazo_dias // 30
    saldos = []
    saldo_atual = valor_inicial

    for mes in range(prazo_meses + 1):
        if mes == 0:
            saldos.append(saldo_atual)
        else:
            if aporte_mensal > 0:
                saldo_atual += aporte_mensal
            saldo_atual = saldo_atual * (1 + rentabilidade_mensal)
            saldos.append(saldo_atual)

    saldo_bruto = saldos[-1]
    if tipo_investimento == "CDB":
        total_investido = valor_inicial + (aporte_mensal * prazo_meses)
        rendimento_bruto = saldo_bruto - total_investido
        aliquota_ir = obter_aliquota_ir(prazo_dias)
        ir_devido = rendimento_bruto * aliquota_ir
        saldo_liquido = saldo_bruto - ir_devido
    else:
        saldo_liquido = saldo_bruto
        ir_devido = 0

    return saldos, saldo_bruto, saldo_liquido, ir_devido, prazo_meses

# ---------------- Interface Principal ---------------- #
st.title("💰 Simulador Comparativo de Renda Fixa")
st.markdown("**Compare CDB, LCI e LCA e encontre o melhor investimento para seu perfil!**")

# Sidebar
with st.sidebar:
    st.header("📚 Guia Rápido")
    st.subheader("CDB")
    st.write("• Garantido pelo FGC até R$ 250 mil\n• Tributação: IR regressivo\n• Liquidez variável")
    st.subheader("LCI")
    st.write("• Garantido pelo FGC até R$ 250 mil\n• Isento de IR\n• Carência mínima de 90 dias")
    st.subheader("LCA")
    st.write("• Garantido pelo FGC até R$ 250 mil\n• Isento de IR\n• Carência mínima de 90 dias")
    st.subheader("Tabela IR - CDB")
    st.write("• Até 180 dias: 22,5%\n• 181-360 dias: 20%\n• 361-720 dias: 17,5%\n• Acima de 720 dias: 15%")

# Parâmetros Gerais
st.header("🎯 Parâmetros de Simulação")
col1, col2, col3 = st.columns(3)

with col1:
    valor_inicial = st.number_input("Valor inicial (R$)", min_value=100.0, value=10000.0, step=100.0, format="%.2f")
    aporte_mensal = st.number_input("Aporte mensal (R$)", min_value=0.0, value=500.0, step=50.0, format="%.2f")
with col2:
    cdi_atual = st.number_input("CDI atual (% a.a.)", min_value=0.1, max_value=30.0, value=10.75, step=0.25, format="%.2f")
with col3:
    ipca_atual = st.number_input("IPCA atual (% a.a.)", min_value=0.0, max_value=20.0, value=4.5, step=0.1, format="%.1f")

st.markdown("---")

# Simulação
st.header("📊 Compare até 3 Investimentos")
investimentos = []

for i in range(3):
    with st.expander(f"💼 Investimento {i+1}", expanded=(i < 2)):
        col_inv1, col_inv2, col_inv3, col_inv4, col_inv5 = st.columns(5)

        with col_inv1:
            tipo = st.selectbox("Tipo", ["CDB", "LCI", "LCA"], key=f"tipo_{i}")
        with col_inv2:
            tipo_rent = st.selectbox("Rentabilidade", ["Prefixada", "Pós-fixada (% CDI)", "Híbrida (IPCA + %)"], key=f"rent_{i}")
        with col_inv3:
            if tipo_rent == "Prefixada":
                taxa = st.number_input("Taxa (% a.a.)", min_value=0.1, max_value=50.0, value=11.0, step=0.1, key=f"taxa_{i}")
            elif tipo_rent == "Pós-fixada (% CDI)":
                taxa = st.number_input("% do CDI", min_value=50.0, max_value=150.0, value=105.0, step=1.0, key=f"taxa_{i}")
            else:
                taxa = st.number_input("Taxa adicional (% a.a.)", min_value=0.0, max_value=20.0, value=5.0, step=0.1, key=f"taxa_{i}")
        with col_inv4:
            prazo_individual = st.number_input("Prazo (dias)", min_value=30, max_value=7200, value=720, step=30, key=f"prazo_{i}")
        with col_inv5:
            ativo = st.checkbox("Incluir", value=(i < 2), key=f"ativo_{i}")

        if ativo:
            rent_mensal = calcular_rentabilidade_mensal(tipo_rent, taxa, cdi_atual, ipca_atual)
            saldos, bruto, liquido, ir, prazo_meses_calc = simular_investimento(valor_inicial, aporte_mensal, prazo_individual, rent_mensal, tipo)

            total_investido = valor_inicial + (aporte_mensal * prazo_meses_calc)
            rent_liquida_anual = ((liquido / total_investido) ** (12/prazo_meses_calc) - 1) * 100 if prazo_meses_calc > 0 else 0

            investimentos.append({
                'nome': f"{tipo} - {tipo_rent}",
                'tipo': tipo,
                'tipo_rentabilidade': tipo_rent,
                'taxa': taxa,
                'prazo': prazo_individual,
                'saldos': saldos,
                'bruto': bruto,
                'liquido': liquido,
                'ir': ir,
                'rent_liquida_anual': rent_liquida_anual,
                'total_investido': total_investido
            })

# Resultados
if investimentos:
    st.markdown("---")
    st.header("📈 Resultados da Simulação")
    melhor = max(investimentos, key=lambda x: x['liquido'])

    # Tabela resumo
    dados_tabela = []
    for inv in investimentos:
        rendimento_liquido = inv['liquido'] - inv['total_investido']
        dados_tabela.append({
            'Investimento': inv['nome'],
            'Prazo (dias)': inv['prazo'],
            'Taxa': f"{inv['taxa']:.1f}%",
            'Total Investido': f"R$ {inv['total_investido']:,.2f}",
            'Valor Bruto': f"R$ {inv['bruto']:,.2f}",
            'IR Devido': f"R$ {inv['ir']:,.2f}",
            'Valor Líquido': f"R$ {inv['liquido']:,.2f}",
            'Rendimento Líquido': f"R$ {rendimento_liquido:,.2f}",
            'Rentabilidade Anual': f"{inv['rent_liquida_anual']:.2f}% a.a."
        })

    st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True)

    # Gráfico
    fig = go.Figure()
    for inv in investimentos:
        meses = list(range(len(inv['saldos'])))
        fig.add_trace(go.Scatter(x=meses, y=inv['saldos'], mode='lines+markers', name=f"{inv['nome']} ({inv['prazo']} dias)", line=dict(width=3)))

    fig.update_layout(title="Evolução dos Investimentos", xaxis_title="Meses", yaxis_title="Valor (R$)", hovermode='x unified', height=500)
    fig.update_layout(yaxis=dict(tickformat=",.0f"))
    st.plotly_chart(fig, use_container_width=True)

    # Melhor opção
    st.success(f"🏆 **MELHOR OPÇÃO:** {melhor['nome']} - Valor final: R$ {melhor['liquido']:.2f}")

# Informações
st.markdown("---")
st.info("⚠️ Esta é uma simulação educativa. Rentabilidades passadas não garantem resultados futuros.")
