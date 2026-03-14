"""
Control de Gastos Personal - Javier
App Streamlit para seguimiento de presupuesto mensual
Datos en miles de pesos colombianos (COP)

Instalación:
    pip install streamlit plotly pandas openpyxl

Ejecución:
    streamlit run control_gastos.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import json
import os

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Control de Gastos - Javier",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# DATOS INICIALES (precargados desde tu Excel)
# ─────────────────────────────────────────────
PRESUPUESTO_INICIAL = {
    # Categoría: (tipo, presupuesto_planeado)
    "Planilla Laura":        ("Gasto Fijo",    500.0),
    "Planilla Javier":       ("Gasto Fijo",    500.0),
    "Extra Cuota Casa":      ("Gasto Fijo",    800.0),
    "Celular Javier y Laura":("Gasto Fijo",    100.0),
    "Estadía Javier":        ("Gasto Fijo",   1200.0),
    "Servicios Javier":      ("Gasto Fijo",    300.0),
    "Rep Javier":            ("Gasto Fijo",    500.0),
    "Rep Laura":             ("Gasto Fijo",    100.0),
    "Familia Javier":        ("Gasto Variable",300.0),
    "Familia Laura":         ("Gasto Variable",300.0),
    "Nestor":                ("Gasto Variable", 45.0),
    "TC Nu":                 ("Gasto Variable",1795.0),
    "Gasto Anomalo":         ("Gasto Variable", 349.0),
    "Skandia":               ("Ahorro",        2000.0),
    "Ahorro Colombia":       ("Ahorro",        3045.0),
    "Impuestos: 17 Abril":   ("Impuesto",      1915.0),
}

INGRESOS_PRESUPUESTO = {
    "Salario Javier":        13400.0,
    "Ingreso por prestamos":     0.0,
    "Bonos":                     0.0,
    "Otros":                     0.0,
}

TRANSACCIONES_INICIALES = [
    {"fecha": "2026-02-27", "monto": 118.0,  "descripcion": "Ope Suites",        "medio": "TD Nu Bank", "categoria": "Gasto Anomalo"},
    {"fecha": "2026-02-27", "monto": 216.0,  "descripcion": "Restaurante",        "medio": "TD Nu Bank", "categoria": "Gasto Anomalo"},
    {"fecha": "2026-02-27", "monto": 15.0,   "descripcion": "Uber",               "medio": "TD Nu Bank", "categoria": "Gasto Anomalo"},
    {"fecha": "2026-02-28", "monto": 1795.0, "descripcion": "Cuota 1 Nu",         "medio": "TD Nu Bank", "categoria": "TC Nu"},
    {"fecha": "2026-02-28", "monto": 500.0,  "descripcion": "Planillas",          "medio": "TD Nu Bank", "categoria": "Planilla Laura"},
    {"fecha": "2026-02-28", "monto": 500.0,  "descripcion": "Planillas",          "medio": "TD Nu Bank", "categoria": "Planilla Javier"},
    {"fecha": "2026-02-28", "monto": 800.0,  "descripcion": "Deudas Mes Previo",  "medio": "TD Nu Bank", "categoria": "Extra Cuota Casa"},
    {"fecha": "2026-02-28", "monto": 50.0,   "descripcion": "Celular Laura",      "medio": "TD Nu Bank", "categoria": "Celular Javier y Laura"},
    {"fecha": "2026-02-28", "monto": 1200.0, "descripcion": "Arriendo",           "medio": "TD Nu Bank", "categoria": "Estadía Javier"},
    {"fecha": "2026-02-28", "monto": 300.0,  "descripcion": "Efectivo",           "medio": "TD Nu Bank", "categoria": "Rep Javier"},
    {"fecha": "2026-02-28", "monto": -300.0, "descripcion": "Efectivo (reverso)", "medio": "Efectivo",   "categoria": "Rep Javier"},
    {"fecha": "2026-02-28", "monto": 100.0,  "descripcion": "Rep Laura",          "medio": "TD Nu Bank", "categoria": "Rep Laura"},
    {"fecha": "2026-02-28", "monto": 300.0,  "descripcion": "Familia Laura",      "medio": "TD Nu Bank", "categoria": "Familia Laura"},
    {"fecha": "2026-03-01", "monto": 13.0,   "descripcion": "Aseo Personal",      "medio": "Efectivo",   "categoria": "Rep Javier"},
    {"fecha": "2026-03-01", "monto": 11.0,   "descripcion": "Salida Sobrinos",    "medio": "Efectivo",   "categoria": "Rep Javier"},
    {"fecha": "2026-03-01", "monto": 100.0,  "descripcion": "Ayuda Sandra",       "medio": "TD Nu Bank", "categoria": "Familia Javier"},
    {"fecha": "2026-03-02", "monto": 110.0,  "descripcion": "GYM",                "medio": "Efectivo",   "categoria": "Rep Javier"},
    {"fecha": "2026-03-04", "monto": 69.0,   "descripcion": "Medicina",           "medio": "TD Nu Bank", "categoria": "Rep Javier"},
    {"fecha": "2026-03-07", "monto": 21.0,   "descripcion": "Salida Sobrinos",    "medio": "Efectivo",   "categoria": "Rep Javier"},
    {"fecha": "2026-03-07", "monto": 25.0,   "descripcion": "Peluquería",         "medio": "Efectivo",   "categoria": "Rep Javier"},
    {"fecha": "2026-03-07", "monto": 9.0,    "descripcion": "Uber",               "medio": "TD Nu Bank", "categoria": "Rep Javier"},
    {"fecha": "2026-03-08", "monto": 40.0,   "descripcion": "Laura",              "medio": "TD Nu Bank", "categoria": "Celular Javier y Laura"},
    {"fecha": "2026-03-08", "monto": 45.0,   "descripcion": "Nestor",             "medio": "TD Nu Bank", "categoria": "Nestor"},
    {"fecha": "2026-03-08", "monto": 200.0,  "descripcion": "Bolsillo Papas",     "medio": "TD Nu Bank", "categoria": "Familia Javier"},
]

INGRESOS_INICIALES = [
    {"fecha": "2026-02-27", "monto": 6798.0, "descripcion": "Salario Tostao", "categoria": "Salario Javier"},
]

DATA_FILE = "gastos_data.json"

# ─────────────────────────────────────────────
# PERSISTENCIA LOCAL (JSON)
# ─────────────────────────────────────────────
def cargar_datos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "transacciones": TRANSACCIONES_INICIALES.copy(),
        "ingresos": INGRESOS_INICIALES.copy(),
        "presupuesto": {k: list(v) for k, v in PRESUPUESTO_INICIAL.items()},
        "ingresos_presupuesto": INGRESOS_PRESUPUESTO.copy(),
    }

def guardar_datos(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = cargar_datos()

data = st.session_state.data

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt_cop(v):
    return f"${v:,.0f}K"

def get_df_trans():
    df = pd.DataFrame(data["transacciones"])
    if df.empty:
        return df
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df

def get_df_ing():
    df = pd.DataFrame(data["ingresos"])
    if df.empty:
        return df
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df

def get_resumen():
    df = get_df_trans()
    rows = []
    for cat, (tipo, planeado) in data["presupuesto"].items():
        if df.empty:
            real = 0.0
        else:
            real = df[df["categoria"] == cat]["monto"].sum()
        diff = planeado - real
        pct = (real / planeado * 100) if planeado > 0 else 0
        rows.append({
            "Tipo": tipo,
            "Categoría": cat,
            "Planeado": planeado,
            "Real": real,
            "Diferencia": diff,
            "% Ejecutado": pct,
        })
    return pd.DataFrame(rows)

def dias_en_mes():
    hoy = date.today()
    if hoy.month == 12:
        return 31
    import calendar
    return calendar.monthrange(hoy.year, hoy.month)[1]

def dias_transcurridos():
    hoy = date.today()
    return hoy.day

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/money.png", width=60)
    st.title("Control de Gastos")
    st.caption("Javier · Miles de COP")
    st.divider()

    hoy = date.today()
    total_dias = dias_en_mes()
    dia_actual = dias_transcurridos()
    pct_mes = dia_actual / total_dias

    st.metric("Hoy", hoy.strftime("%d %b %Y"))
    st.progress(pct_mes, text=f"Día {dia_actual} de {total_dias} del mes")

    st.divider()
    df_res = get_resumen()
    total_planeado = df_res["Planeado"].sum()
    total_real = df_res["Real"].sum()
    total_ing_real = get_df_ing()["monto"].sum() if not get_df_ing().empty else 0
    total_ing_plan = sum(data["ingresos_presupuesto"].values())

    st.metric("Ingresos reales", fmt_cop(total_ing_real),
              delta=fmt_cop(total_ing_real - total_ing_plan),
              delta_color="normal")
    st.metric("Gastos reales", fmt_cop(total_real),
              delta=fmt_cop(total_real - total_planeado),
              delta_color="inverse")
    balance = total_ing_real - total_real
    st.metric("Balance del mes", fmt_cop(balance),
              delta_color="normal")

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Dashboard",
    "📊 Presupuesto vs Real",
    "📅 Gastos Diarios",
    "🔮 Proyección",
    "💳 Ingresar Gasto",
    "⚙️ Datos",
])

# ══════════════════════════════════════════════
# TAB 1: DASHBOARD
# ══════════════════════════════════════════════
with tab1:
    st.header("📊 Dashboard del Mes")

    df_res = get_resumen()
    desfasadas = df_res[df_res["% Ejecutado"] > 100].sort_values("% Ejecutado", ascending=False)
    ok = df_res[(df_res["% Ejecutado"] <= 100) & (df_res["% Ejecutado"] > 0)]
    sin_movimiento = df_res[df_res["% Ejecutado"] == 0]

    # KPIs top
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Planeado", fmt_cop(df_res["Planeado"].sum()))
    col2.metric("Total Ejecutado", fmt_cop(df_res["Real"].sum()),
                delta=f"{df_res['Real'].sum() / df_res['Planeado'].sum() * 100:.0f}% del presupuesto")
    col3.metric("Categorías desfasadas", f"{len(desfasadas)}", delta_color="inverse")
    col4.metric("Ahorro ejecutado",
                fmt_cop(df_res[df_res["Tipo"] == "Ahorro"]["Real"].sum()),
                delta=fmt_cop(df_res[df_res["Tipo"] == "Ahorro"]["Real"].sum() -
                              df_res[df_res["Tipo"] == "Ahorro"]["Planeado"].sum()),
                delta_color="normal")

    st.divider()

    # Alertas
    if not desfasadas.empty:
        st.subheader("🚨 Categorías Desfasadas (superaron el presupuesto)")
        for _, row in desfasadas.iterrows():
            exceso = row["Real"] - row["Planeado"]
            st.error(
                f"**{row['Categoría']}** ({row['Tipo']}) — "
                f"Planeado: {fmt_cop(row['Planeado'])} | "
                f"Real: {fmt_cop(row['Real'])} | "
                f"Exceso: **{fmt_cop(exceso)}** ({row['% Ejecutado']:.0f}%)"
            )
    else:
        st.success("✅ Ninguna categoría supera el presupuesto todavía.")

    # Gauge por tipo
    st.subheader("Ejecución por Tipo de Gasto")
    tipos = df_res.groupby("Tipo")[["Planeado", "Real"]].sum().reset_index()

    cols = st.columns(len(tipos))
    for i, (_, row) in enumerate(tipos.iterrows()):
        pct = row["Real"] / row["Planeado"] * 100 if row["Planeado"] > 0 else 0
        color = "#e74c3c" if pct > 100 else "#f39c12" if pct > 80 else "#2ecc71"
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=pct,
            number={"suffix": "%", "font": {"size": 28}},
            delta={"reference": 100, "valueformat": ".0f", "suffix": "%"},
            title={"text": row["Tipo"], "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, 130], "tickwidth": 1},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 80],  "color": "#ecf0f1"},
                    {"range": [80, 100], "color": "#f8d7da"},
                    {"range": [100, 130], "color": "#f5c6cb"},
                ],
                "threshold": {"line": {"color": "red", "width": 3}, "value": 100},
            },
        ))
        fig.update_layout(height=220, margin=dict(t=50, b=10, l=20, r=20))
        cols[i].plotly_chart(fig, use_container_width=True)
        cols[i].caption(f"{fmt_cop(row['Real'])} / {fmt_cop(row['Planeado'])}")

# ══════════════════════════════════════════════
# TAB 2: PRESUPUESTO VS REAL
# ══════════════════════════════════════════════
with tab2:
    st.header("📊 Presupuesto vs. Real por Categoría")

    df_res = get_resumen()
    tipo_sel = st.selectbox("Filtrar por tipo:", ["Todos"] + sorted(df_res["Tipo"].unique().tolist()))

    df_plot = df_res if tipo_sel == "Todos" else df_res[df_res["Tipo"] == tipo_sel]
    df_plot = df_plot.sort_values("% Ejecutado", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_plot["Categoría"],
        x=df_plot["Planeado"],
        name="Planeado",
        orientation="h",
        marker_color="#95a5a6",
        opacity=0.6,
    ))
    fig.add_trace(go.Bar(
        y=df_plot["Categoría"],
        x=df_plot["Real"],
        name="Real",
        orientation="h",
        marker_color=[
            "#e74c3c" if r > p else "#3498db"
            for r, p in zip(df_plot["Real"], df_plot["Planeado"])
        ],
    ))
    fig.update_layout(
        barmode="overlay",
        height=max(400, len(df_plot) * 40),
        xaxis_title="Miles COP",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=10, r=10, t=40, b=40),
        plot_bgcolor="white",
    )
    fig.add_vline(x=0, line_width=1, line_color="gray")
    st.plotly_chart(fig, use_container_width=True)

    st.caption("🔴 Rojo = superó el presupuesto | 🔵 Azul = dentro del presupuesto")

    st.subheader("Tabla detallada")
    df_display = df_plot[["Tipo", "Categoría", "Planeado", "Real", "Diferencia", "% Ejecutado"]].copy()
    df_display["Planeado"] = df_display["Planeado"].map(lambda x: f"${x:,.0f}K")
    df_display["Real"] = df_display["Real"].map(lambda x: f"${x:,.0f}K")
    df_display["Diferencia"] = df_display["Diferencia"].map(lambda x: f"${x:,.0f}K")
    df_display["% Ejecutado"] = df_display["% Ejecutado"].map(lambda x: f"{x:.1f}%")
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════
# TAB 3: GASTOS DIARIOS
# ══════════════════════════════════════════════
with tab3:
    st.header("📅 Línea de Tiempo de Gastos")

    df = get_df_trans()
    if df.empty:
        st.info("No hay transacciones aún.")
    else:
        df_dia = df.groupby("fecha")["monto"].sum().reset_index()
        df_dia = df_dia.sort_values("fecha")
        df_dia["acumulado"] = df_dia["monto"].cumsum()

        # Presupuesto diario esperado (lineal)
        total_plan = get_resumen()["Planeado"].sum()
        total_dias_mes = dias_en_mes()
        df_dia["presupuesto_diario_acum"] = [
            total_plan / total_dias_mes * (i + 1)
            for i in range(len(df_dia))
        ]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Gasto diario")
            fig1 = px.bar(
                df_dia, x="fecha", y="monto",
                color_discrete_sequence=["#3498db"],
                labels={"monto": "Miles COP", "fecha": "Fecha"},
            )
            fig1.update_layout(height=300, plot_bgcolor="white",
                               margin=dict(t=20, b=20))
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("Acumulado vs. Ritmo de presupuesto")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df_dia["fecha"], y=df_dia["presupuesto_diario_acum"],
                mode="lines", name="Ritmo presupuestado",
                line=dict(color="#95a5a6", dash="dash"),
            ))
            fig2.add_trace(go.Scatter(
                x=df_dia["fecha"], y=df_dia["acumulado"],
                mode="lines+markers", name="Gasto acumulado real",
                line=dict(color="#e74c3c", width=2),
                fill="tonexty",
                fillcolor="rgba(231,76,60,0.1)",
            ))
            fig2.update_layout(height=300, plot_bgcolor="white",
                               yaxis_title="Miles COP",
                               margin=dict(t=20, b=20),
                               legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig2, use_container_width=True)

        # Detalle por día
        st.subheader("Detalle de transacciones")
        fecha_sel = st.date_input("Ver transacciones del día:",
                                  value=df["fecha"].max().date())
        df_sel = df[df["fecha"].dt.date == fecha_sel]
        if df_sel.empty:
            st.info("Sin transacciones ese día.")
        else:
            st.dataframe(
                df_sel[["descripcion", "categoria", "medio", "monto"]].rename(columns={
                    "descripcion": "Descripción",
                    "categoria": "Categoría",
                    "medio": "Medio de Pago",
                    "monto": "Monto (K COP)",
                }),
                use_container_width=True, hide_index=True
            )
            st.metric("Total del día", fmt_cop(df_sel["monto"].sum()))

# ══════════════════════════════════════════════
# TAB 4: PROYECCIÓN
# ══════════════════════════════════════════════
with tab4:
    st.header("🔮 Proyección de Cierre del Mes")

    df = get_df_trans()
    dia_hoy = dias_transcurridos()
    total_dias = dias_en_mes()
    df_res = get_resumen()

    if df.empty or dia_hoy == 0:
        st.info("Necesitas transacciones para generar proyección.")
    else:
        gasto_hasta_hoy = df["monto"].sum()
        ritmo_diario = gasto_hasta_hoy / dia_hoy
        proyeccion_fin_mes = ritmo_diario * total_dias

        total_plan_gastos = df_res["Planeado"].sum()
        total_ing_real = get_df_ing()["monto"].sum() if not get_df_ing().empty else 0
        total_ing_plan = sum(data["ingresos_presupuesto"].values())

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Proyección de gasto total",
            fmt_cop(proyeccion_fin_mes),
            delta=fmt_cop(proyeccion_fin_mes - total_plan_gastos),
            delta_color="inverse",
        )
        col2.metric(
            "Ritmo diario actual",
            fmt_cop(ritmo_diario),
            delta=f"Meta: {fmt_cop(total_plan_gastos / total_dias)}/día",
        )
        col3.metric(
            "Balance proyectado al cierre",
            fmt_cop(total_ing_plan - proyeccion_fin_mes),
        )

        # Gráfico de proyección
        fechas_pasadas = pd.date_range(
            start=df["fecha"].min(), periods=dia_hoy, freq="D"
        )
        acumulados_reales = [
            df[df["fecha"] <= f]["monto"].sum() for f in fechas_pasadas
        ]

        fechas_futuras = pd.date_range(
            start=date.today(), periods=total_dias - dia_hoy + 1, freq="D"
        )
        acumulados_proyectados = [
            gasto_hasta_hoy + ritmo_diario * i
            for i in range(len(fechas_futuras))
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fechas_pasadas, y=acumulados_reales,
            mode="lines+markers", name="Real",
            line=dict(color="#2ecc71", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=fechas_futuras, y=acumulados_proyectados,
            mode="lines", name="Proyección",
            line=dict(color="#e67e22", dash="dot", width=2),
        ))
        fig.add_hline(
            y=total_plan_gastos,
            line_dash="dash", line_color="red",
            annotation_text=f"Presupuesto total: {fmt_cop(total_plan_gastos)}",
            annotation_position="top left",
        )
        fig.update_layout(
            height=380,
            plot_bgcolor="white",
            yaxis_title="Gasto acumulado (K COP)",
            xaxis_title="Fecha",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Categorías que se proyectan a desfasarse
        st.subheader("⚠️ Categorías que se proyectan a desfasarse al fin del mes")
        alertas = []
        for _, row in df_res.iterrows():
            if row["Real"] > 0 and dia_hoy > 0:
                proy = row["Real"] / dia_hoy * total_dias
                if proy > row["Planeado"]:
                    alertas.append({
                        "Categoría": row["Categoría"],
                        "Tipo": row["Tipo"],
                        "Real actual": fmt_cop(row["Real"]),
                        "Proyección fin mes": fmt_cop(proy),
                        "Presupuesto": fmt_cop(row["Planeado"]),
                        "Exceso proyectado": fmt_cop(proy - row["Planeado"]),
                    })
        if alertas:
            st.dataframe(pd.DataFrame(alertas), use_container_width=True, hide_index=True)
        else:
            st.success("Ninguna categoría se proyecta a desfasarse al ritmo actual.")

# ══════════════════════════════════════════════
# TAB 5: INGRESAR GASTO
# ══════════════════════════════════════════════
with tab5:
    st.header("💳 Ingresar Nueva Transacción")

    col_gasto, col_ingreso = st.columns(2)

    with col_gasto:
        st.subheader("➕ Nuevo Gasto")
        with st.form("form_gasto"):
            fecha_g = st.date_input("Fecha", value=date.today(), key="fg_fecha")
            monto_g = st.number_input("Monto (K COP)", min_value=0.0, step=10.0, key="fg_monto")
            desc_g = st.text_input("Descripción", key="fg_desc")
            medio_g = st.selectbox("Medio de pago",
                ["TD Nu Bank", "Efectivo", "TC Nu Bank", "Otro"], key="fg_medio")
            cat_g = st.selectbox("Categoría",
                sorted(data["presupuesto"].keys()), key="fg_cat")
            submit_g = st.form_submit_button("💾 Guardar Gasto", type="primary")

        if submit_g:
            if monto_g > 0 and desc_g:
                data["transacciones"].append({
                    "fecha": str(fecha_g),
                    "monto": monto_g,
                    "descripcion": desc_g,
                    "medio": medio_g,
                    "categoria": cat_g,
                })
                guardar_datos(data)
                st.success(f"✅ Gasto guardado: {fmt_cop(monto_g)} en {cat_g}")
                st.rerun()
            else:
                st.error("Completa monto y descripción.")

    with col_ingreso:
        st.subheader("💰 Nuevo Ingreso")
        with st.form("form_ingreso"):
            fecha_i = st.date_input("Fecha", value=date.today(), key="fi_fecha")
            monto_i = st.number_input("Monto (K COP)", min_value=0.0, step=100.0, key="fi_monto")
            desc_i = st.text_input("Descripción", key="fi_desc")
            cat_i = st.selectbox("Categoría",
                sorted(data["ingresos_presupuesto"].keys()), key="fi_cat")
            submit_i = st.form_submit_button("💾 Guardar Ingreso", type="primary")

        if submit_i:
            if monto_i > 0 and desc_i:
                data["ingresos"].append({
                    "fecha": str(fecha_i),
                    "monto": monto_i,
                    "descripcion": desc_i,
                    "categoria": cat_i,
                })
                guardar_datos(data)
                st.success(f"✅ Ingreso guardado: {fmt_cop(monto_i)} en {cat_i}")
                st.rerun()
            else:
                st.error("Completa monto y descripción.")

    st.divider()
    st.subheader("📋 Transacciones del mes (editables)")
    df_editable = get_df_trans()
    if not df_editable.empty:
        df_editable["fecha"] = df_editable["fecha"].dt.strftime("%Y-%m-%d")
        df_edit = st.data_editor(
            df_editable,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "fecha": st.column_config.TextColumn("Fecha (YYYY-MM-DD)"),
                "monto": st.column_config.NumberColumn("Monto (K COP)", format="$%.0fK"),
                "categoria": st.column_config.SelectboxColumn(
                    "Categoría", options=sorted(data["presupuesto"].keys())
                ),
            },
            hide_index=True,
        )
        if st.button("💾 Guardar cambios en tabla"):
            data["transacciones"] = df_edit.to_dict("records")
            guardar_datos(data)
            st.success("Cambios guardados.")
            st.rerun()

# ══════════════════════════════════════════════
# TAB 6: DATOS / PRESUPUESTO
# ══════════════════════════════════════════════
with tab6:
    st.header("⚙️ Editar Presupuesto")
    st.caption("Modifica las categorías y montos planeados aquí.")

    pres_df = pd.DataFrame([
        {"Tipo": v[0], "Categoría": k, "Planeado (K COP)": v[1]}
        for k, v in data["presupuesto"].items()
    ])

    pres_edit = st.data_editor(
        pres_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Tipo": st.column_config.SelectboxColumn(
                "Tipo", options=["Gasto Fijo", "Gasto Variable", "Ahorro", "Impuesto"]
            ),
            "Planeado (K COP)": st.column_config.NumberColumn(
                "Planeado (K COP)", format="$%.0fK", min_value=0
            ),
        },
        hide_index=True,
    )

    if st.button("💾 Guardar presupuesto"):
        nuevo_pres = {}
        for _, row in pres_edit.iterrows():
            nuevo_pres[row["Categoría"]] = [row["Tipo"], float(row["Planeado (K COP)"])]
        data["presupuesto"] = nuevo_pres
        guardar_datos(data)
        st.success("Presupuesto actualizado.")
        st.rerun()

    st.divider()
    st.subheader("Presupuesto de Ingresos")
    ing_df = pd.DataFrame([
        {"Categoría": k, "Planeado (K COP)": v}
        for k, v in data["ingresos_presupuesto"].items()
    ])
    ing_edit = st.data_editor(
        ing_df, use_container_width=True,
        column_config={"Planeado (K COP)": st.column_config.NumberColumn(format="$%.0fK")},
        hide_index=True,
    )
    if st.button("💾 Guardar ingresos presupuestados"):
        data["ingresos_presupuesto"] = {
            row["Categoría"]: float(row["Planeado (K COP)"])
            for _, row in ing_edit.iterrows()
        }
        guardar_datos(data)
        st.success("Ingresos presupuestados actualizados.")
        st.rerun()

    st.divider()
    st.subheader("⚠️ Zona peligrosa")
    if st.button("🔄 Resetear todos los datos al estado inicial"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.pop("data", None)
        st.success("Datos reseteados. Recargando...")
        st.rerun()