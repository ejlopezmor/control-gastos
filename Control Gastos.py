"""
Control de Gastos Personal - Javier
App Streamlit con persistencia en Google Sheets
Datos en miles de pesos colombianos (COP)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import json
import os
import calendar
import math

st.set_page_config(
    page_title="Control de Gastos - Javier",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

SHEET_ID = "1ap_ceoBgDH4sLFUFaYFYovLCPDbc05CTqyPIWLcwvm8"

# ─────────────────────────────────────────────
# DATOS INICIALES
# ─────────────────────────────────────────────
PRESUPUESTO_INICIAL = {
    "Planilla Laura":         ("Gasto Fijo",     500.0),
    "Planilla Javier":        ("Gasto Fijo",     500.0),
    "Extra Cuota Casa":       ("Gasto Fijo",     800.0),
    "Celular Javier y Laura": ("Gasto Fijo",     100.0),
    "Estadía Javier":         ("Gasto Fijo",    1200.0),
    "Servicios Javier":       ("Gasto Fijo",     300.0),
    "Rep Javier":             ("Gasto Fijo",     500.0),
    "Rep Laura":              ("Gasto Fijo",     100.0),
    "Familia Javier":         ("Gasto Variable", 300.0),
    "Familia Laura":          ("Gasto Variable", 300.0),
    "Nestor":                 ("Gasto Variable",  45.0),
    "TC Nu":                  ("Gasto Variable", 1795.0),
    "Gasto Anomalo":          ("Gasto Variable",  349.0),
    "Skandia":                ("Ahorro",         2000.0),
    "Ahorro Colombia":        ("Ahorro",         3045.0),
    "Impuestos: 17 Abril":    ("Impuesto",       1915.0),
}

INGRESOS_PRESUPUESTO_INICIAL = {
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

# ─────────────────────────────────────────────
# GOOGLE SHEETS — CONEXIÓN
# ─────────────────────────────────────────────
@st.cache_resource
def get_gsheet_client():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception:
        return None

def get_or_create_sheet(client, tab_name, headers):
    try:
        sh = client.open_by_key(SHEET_ID)
        try:
            ws = sh.worksheet(tab_name)
        except Exception:
            ws = sh.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
            ws.append_row(headers)
        return ws
    except Exception:
        return None

# ─────────────────────────────────────────────
# LECTURA DESDE SHEETS
# ─────────────────────────────────────────────
def leer_transacciones(client):
    ws = get_or_create_sheet(client, "Transacciones", ["fecha","monto","descripcion","medio","categoria"])
    if ws is None:
        return TRANSACCIONES_INICIALES.copy()
    rows = ws.get_all_records()
    if not rows:
        batch = [[t["fecha"], t["monto"], t["descripcion"], t["medio"], t["categoria"]]
                 for t in TRANSACCIONES_INICIALES]
        if batch:
            ws.append_rows(batch)
        return TRANSACCIONES_INICIALES.copy()
    return [{"fecha": str(r.get("fecha","")), "monto": float(r.get("monto",0)),
             "descripcion": str(r.get("descripcion","")), "medio": str(r.get("medio","")),
             "categoria": str(r.get("categoria",""))} for r in rows]

def leer_ingresos(client):
    ws = get_or_create_sheet(client, "Ingresos", ["fecha","monto","descripcion","categoria"])
    if ws is None:
        return INGRESOS_INICIALES.copy()
    rows = ws.get_all_records()
    if not rows:
        batch = [[t["fecha"], t["monto"], t["descripcion"], t["categoria"]]
                 for t in INGRESOS_INICIALES]
        if batch:
            ws.append_rows(batch)
        return INGRESOS_INICIALES.copy()
    return [{"fecha": str(r.get("fecha","")), "monto": float(r.get("monto",0)),
             "descripcion": str(r.get("descripcion","")), "categoria": str(r.get("categoria",""))} for r in rows]

def leer_presupuesto(client):
    ws = get_or_create_sheet(client, "Presupuesto", ["categoria","tipo","planeado"])
    if ws is None:
        return {k: list(v) for k, v in PRESUPUESTO_INICIAL.items()}
    rows = ws.get_all_records()
    if not rows:
        batch = [[cat, tipo, plan] for cat, (tipo, plan) in PRESUPUESTO_INICIAL.items()]
        if batch:
            ws.append_rows(batch)
        return {k: list(v) for k, v in PRESUPUESTO_INICIAL.items()}
    result = {str(r["categoria"]): [str(r["tipo"]), float(r["planeado"])] for r in rows}
    return result if result else {k: list(v) for k, v in PRESUPUESTO_INICIAL.items()}

def leer_ingresos_presupuesto(client):
    ws = get_or_create_sheet(client, "Ingresos_Presupuesto", ["categoria","planeado"])
    if ws is None:
        return INGRESOS_PRESUPUESTO_INICIAL.copy()
    rows = ws.get_all_records()
    if not rows:
        batch = [[cat, plan] for cat, plan in INGRESOS_PRESUPUESTO_INICIAL.items()]
        if batch:
            ws.append_rows(batch)
        return INGRESOS_PRESUPUESTO_INICIAL.copy()
    result = {str(r["categoria"]): float(r["planeado"]) for r in rows}
    return result if result else INGRESOS_PRESUPUESTO_INICIAL.copy()

def leer_presupuestos_mensuales(client):
    ws = get_or_create_sheet(client, "Presupuestos_Mensuales", ["mes","categoria","tipo","planeado"])
    if ws is None:
        return {}
    rows = ws.get_all_records()
    result = {}
    for r in rows:
        mes = str(r.get("mes", ""))
        cat = str(r.get("categoria", ""))
        if mes and cat:
            if mes not in result:
                result[mes] = {}
            result[mes][cat] = [str(r.get("tipo", "")), float(r.get("planeado", 0))]
    return result

# ─────────────────────────────────────────────
# ESCRITURA EN SHEETS  (todas usan append_rows por lote)
# ─────────────────────────────────────────────
def _sanitize_val(v):
    """Convierte NaN / Inf / None a string vacío para evitar InvalidJSONError."""
    if v is None:
        return ""
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return ""
    except (TypeError, ValueError):
        pass
    return v

def _escribir_hoja(ws, headers, filas):
    """Limpia y reescribe la hoja en 2 llamadas a la API.
    Sanea NaN/Inf antes de enviar para evitar InvalidJSONError."""
    ws.clear()
    filas_limpias = [[_sanitize_val(c) for c in fila] for fila in filas]
    todas = [headers] + filas_limpias
    if todas:
        ws.append_rows(todas)

def guardar_transacciones(client, trans):
    ws = get_or_create_sheet(client, "Transacciones", ["fecha","monto","descripcion","medio","categoria"])
    if ws:
        filas = [[t["fecha"], t["monto"], t["descripcion"], t["medio"], t["categoria"]]
                 for t in trans]
        _escribir_hoja(ws, ["fecha","monto","descripcion","medio","categoria"], filas)

def guardar_ingresos(client, ingresos):
    ws = get_or_create_sheet(client, "Ingresos", ["fecha","monto","descripcion","categoria"])
    if ws:
        filas = [[t["fecha"], t["monto"], t["descripcion"], t["categoria"]] for t in ingresos]
        _escribir_hoja(ws, ["fecha","monto","descripcion","categoria"], filas)

def guardar_presupuesto(client, presupuesto):
    ws = get_or_create_sheet(client, "Presupuesto", ["categoria","tipo","planeado"])
    if ws:
        filas = [[cat, vals[0], vals[1]] for cat, vals in presupuesto.items()]
        _escribir_hoja(ws, ["categoria","tipo","planeado"], filas)

def guardar_ingresos_presupuesto(client, ing_pres):
    ws = get_or_create_sheet(client, "Ingresos_Presupuesto", ["categoria","planeado"])
    if ws:
        filas = [[cat, plan] for cat, plan in ing_pres.items()]
        _escribir_hoja(ws, ["categoria","planeado"], filas)

def guardar_presupuesto_mes(client, mes, presupuesto):
    ws = get_or_create_sheet(client, "Presupuestos_Mensuales", ["mes","categoria","tipo","planeado"])
    if ws:
        otros = [[r["mes"], r["categoria"], r["tipo"], r["planeado"]]
                 for r in ws.get_all_records()
                 if str(r.get("mes", "")) != mes]
        nuevos = [[mes, cat, vals[0], vals[1]] for cat, vals in presupuesto.items()]
        _escribir_hoja(ws, ["mes","categoria","tipo","planeado"], otros + nuevos)

def agregar_transaccion(client, t):
    ws = get_or_create_sheet(client, "Transacciones", ["fecha","monto","descripcion","medio","categoria"])
    if ws:
        ws.append_rows([[t["fecha"], t["monto"], t["descripcion"], t["medio"], t["categoria"]]])

def agregar_ingreso(client, t):
    ws = get_or_create_sheet(client, "Ingresos", ["fecha","monto","descripcion","categoria"])
    if ws:
        ws.append_rows([[t["fecha"], t["monto"], t["descripcion"], t["categoria"]]])

# ─────────────────────────────────────────────
# CARGA INICIAL
# ─────────────────────────────────────────────
client     = get_gsheet_client()
usar_sheets = client is not None

if "data" not in st.session_state:
    if usar_sheets:
        with st.spinner("Cargando datos desde Google Sheets..."):
            st.session_state.data = {
                "transacciones":          leer_transacciones(client),
                "ingresos":               leer_ingresos(client),
                "presupuesto":            leer_presupuesto(client),
                "ingresos_presupuesto":   leer_ingresos_presupuesto(client),
                "presupuestos_mensuales": leer_presupuestos_mensuales(client),
            }
    else:
        DATA_FILE = "gastos_data.json"
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                st.session_state.data = json.load(f)
            if "presupuestos_mensuales" not in st.session_state.data:
                st.session_state.data["presupuestos_mensuales"] = {}
        else:
            st.session_state.data = {
                "transacciones":          TRANSACCIONES_INICIALES.copy(),
                "ingresos":               INGRESOS_INICIALES.copy(),
                "presupuesto":            {k: list(v) for k, v in PRESUPUESTO_INICIAL.items()},
                "ingresos_presupuesto":   INGRESOS_PRESUPUESTO_INICIAL.copy(),
                "presupuestos_mensuales": {},
            }

data = st.session_state.data

# Limpieza automática: eliminar transacciones con monto 0
_trans_sin_cero = [t for t in data["transacciones"] if float(t.get("monto", 0)) != 0]
if len(_trans_sin_cero) < len(data["transacciones"]):
    data["transacciones"] = _trans_sin_cero
    if usar_sheets:
        guardar_transacciones(client, data["transacciones"])

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt_cop(v):
    return f"${v:,.0f}K"

def fmt_val(v):
    return f"${v:,.0f}"

def fmt_diff(v):
    sign = "+" if v >= 0 else ""
    return f"{sign}${v:,.0f}"

def _diff_bg(v):
    if v > 0:  return "background:#d4edda;color:#155724;"
    if v < 0:  return "background:#f8d7da;color:#721c24;"
    return "background:#ffffff;"

def _mes_activo():
    return st.session_state.get("mes_activo", date.today().strftime("%Y-%m"))

def _presupuesto_activo():
    mes = _mes_activo()
    pm  = data.get("presupuestos_mensuales", {})
    return pm[mes] if mes in pm else data["presupuesto"]

def get_df_trans_all():
    df = pd.DataFrame(data["transacciones"])
    if df.empty:
        return df
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df

def get_df_trans():
    df = get_df_trans_all()
    if df.empty:
        return df
    return df[df["fecha"].dt.strftime("%Y-%m") == _mes_activo()]

def get_df_ing():
    df = pd.DataFrame(data["ingresos"])
    if df.empty:
        return df
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df[df["fecha"].dt.strftime("%Y-%m") == _mes_activo()]

def get_resumen():
    df  = get_df_trans()
    pres = _presupuesto_activo()
    rows = []
    for cat, vals in pres.items():
        tipo, planeado = vals[0], float(vals[1])
        real = 0.0 if df.empty else float(df[df["categoria"] == cat]["monto"].sum())
        rows.append({"Tipo": tipo, "Categoría": cat, "Planeado": planeado,
                     "Real": real, "Diferencia": planeado - real,
                     "% Ejecutado": (real / planeado * 100) if planeado > 0 else 0})
    return pd.DataFrame(rows)

def dias_en_mes():
    hoy = date.today()
    return calendar.monthrange(hoy.year, hoy.month)[1]

def dias_transcurridos():
    return date.today().day

# ─────────────────────────────────────────────
# CONSTRUCTORES DE TABLAS HTML
# ─────────────────────────────────────────────
TIPO_STYLE = {
    "Gasto Fijo":     ("#fff3e0", "#f39c12"),
    "Gasto Variable": ("#f1f8e9", "#27ae60"),
    "Ahorro":         ("#e3f2fd", "#3498db"),
    "Impuesto":       ("#fce4ec", "#e74c3c"),
}

def _th(txt, align="right", extra=""):
    return f'<th style="text-align:{align};padding:8px 12px;color:#6c757d;font-weight:600;font-size:0.82em;letter-spacing:.04em;border-bottom:2px solid #dee2e6;{extra}">{txt}</th>'

def _td(txt, align="right", extra=""):
    return f'<td style="text-align:{align};padding:5px 12px;{extra}">{txt}</td>'

def build_expense_table(df_res):
    total_plan = df_res["Planeado"].sum()
    total_real = df_res["Real"].sum()
    total_diff = total_plan - total_real
    html = (
        '<table style="width:100%;border-collapse:collapse;font-size:0.86em;font-family:sans-serif;">'
        "<thead><tr>"
        + _th("", align="left", extra="min-width:100px;")
        + _th("", align="left", extra="min-width:150px;")
        + _th("Planeado")
        + _th("Real")
        + _th("Diferencia")
        + "</tr></thead><tbody>"
        + '<tr style="font-weight:700;background:#f8f9fa;">'
        + _td("Totales", align="left", extra="padding:7px 12px;color:#343a40;font-size:.9em;")
        + _td("", align="left")
        + _td(fmt_val(total_plan), extra="color:#6c757d;")
        + _td(fmt_val(total_real))
        + _td(fmt_diff(total_diff), extra=_diff_bg(total_diff))
        + "</tr>"
    )
    for tipo in ["Gasto Fijo", "Gasto Variable", "Ahorro", "Impuesto"]:
        df_t = df_res[df_res["Tipo"] == tipo]
        if df_t.empty:
            continue
        bg, border = TIPO_STYLE.get(tipo, ("#f5f5f5", "#aaa"))
        n = len(df_t)
        for i, (_, row) in enumerate(df_t.iterrows()):
            diff = row["Diferencia"]
            tipo_td = (
                f'<td rowspan="{n}" style="vertical-align:middle;text-align:center;'
                f'background:{bg};border-left:4px solid {border};border-top:1px solid #e9ecef;'
                f'font-weight:700;font-size:0.78em;padding:4px 6px;color:#495057;'
                f'min-width:75px;">{tipo}</td>'
            ) if i == 0 else ""
            html += (
                '<tr style="border-top:1px solid #f0f0f0;">'
                + tipo_td
                + _td(row["Categoría"], align="left", extra="color:#343a40;")
                + _td(fmt_val(row["Planeado"]), extra="color:#6c757d;")
                + _td(fmt_val(row["Real"]))
                + _td(fmt_diff(diff), extra=_diff_bg(diff))
                + "</tr>"
            )
    html += "</tbody></table>"
    return html

def build_income_table():
    df_ing   = get_df_ing()
    total_real = float(df_ing["monto"].sum()) if not df_ing.empty else 0.0
    total_plan = sum(data["ingresos_presupuesto"].values())
    total_diff = total_real - total_plan
    html = (
        '<table style="width:100%;border-collapse:collapse;font-size:0.86em;font-family:sans-serif;">'
        "<thead><tr>"
        + _th("", align="left", extra="min-width:200px;")
        + _th("Planeado")
        + _th("Real")
        + _th("Diferencia")
        + "</tr></thead><tbody>"
        + '<tr style="font-weight:700;background:#f8f9fa;">'
        + _td("Totales", align="left", extra="padding:7px 12px;color:#343a40;font-size:.9em;")
        + _td(fmt_val(total_plan), extra="color:#6c757d;")
        + _td(fmt_val(total_real))
        + _td(fmt_diff(total_diff), extra=_diff_bg(total_diff))
        + "</tr>"
    )
    for cat, plan in data["ingresos_presupuesto"].items():
        real = 0.0
        if not df_ing.empty:
            real = float(df_ing[df_ing["categoria"] == cat]["monto"].sum())
        diff = real - plan
        html += (
            '<tr style="border-top:1px solid #f0f0f0;">'
            + _td(cat, align="left", extra="color:#343a40;")
            + _td(fmt_val(plan), extra="color:#6c757d;")
            + _td(fmt_val(real))
            + _td(fmt_diff(diff), extra=_diff_bg(diff))
            + "</tr>"
        )
    html += "</tbody></table>"
    return html

def build_pivot_table(df=None):
    if df is None:
        df = get_df_trans()
    if df is None or df.empty:
        return "<p style='color:#888;padding:20px;'>No hay transacciones para este mes.</p>"
    grand_total = df["monto"].sum()
    html = (
        '<table style="width:100%;border-collapse:collapse;font-size:0.86em;font-family:sans-serif;">'
        "<thead><tr style='background:#f8f9fa;'>"
        + _th("Categoría", align="left", extra="min-width:160px;")
        + _th("Descripción", align="left", extra="min-width:180px;")
        + _th("Monto")
        + _th("%")
        + "</tr></thead><tbody>"
    )
    cat_totals = df.groupby("categoria")["monto"].sum().sort_values(ascending=False)
    for cat, cat_total in cat_totals.items():
        cat_pct = cat_total / grand_total * 100 if grand_total > 0 else 0
        html += (
            '<tr style="background:#eef2f7;border-top:2px solid #dee2e6;">'
            + f'<td style="padding:5px 12px;font-weight:700;color:#343a40;">{cat}</td>'
            + '<td colspan="3" style="padding:5px 12px;"></td>'
            + "</tr>"
        )
        desc_totals = df[df["categoria"] == cat].groupby("descripcion")["monto"].sum().sort_values(ascending=False)
        for desc, desc_total in desc_totals.items():
            desc_pct = desc_total / grand_total * 100 if grand_total > 0 else 0
            html += (
                '<tr style="border-top:1px solid #f3f3f3;">'
                + '<td style="padding:3px 12px;color:#adb5bd;font-size:.9em;">  —</td>'
                + _td(desc, align="left", extra="color:#495057;")
                + _td(fmt_val(desc_total))
                + _td(f"{desc_pct:.1f}%", extra="color:#6c757d;")
                + "</tr>"
            )
        html += (
            '<tr style="background:#e2e8f0;border-top:1px solid #c8d0db;">'
            + f'<td colspan="2" style="padding:4px 12px;font-weight:600;color:#495057;font-size:.85em;">{cat} Total</td>'
            + f'<td style="text-align:right;padding:4px 12px;font-weight:600;">{fmt_val(cat_total)}</td>'
            + f'<td style="text-align:right;padding:4px 12px;color:#6c757d;">{cat_pct:.1f}%</td>'
            + "</tr>"
        )
    html += (
        '<tr style="font-weight:700;border-top:2px solid #dee2e6;background:#2c3e50;color:white;">'
        + '<td colspan="2" style="padding:8px 12px;">Gran Total</td>'
        + f'<td style="text-align:right;padding:8px 12px;">{fmt_val(grand_total)}</td>'
        + '<td style="text-align:right;padding:8px 12px;">100.0%</td>'
        + "</tr>"
    )
    html += "</tbody></table>"
    return html

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/money.png", width=60)
    st.title("Control de Gastos")
    st.caption("Javier · Miles de COP")
    st.caption("☁️ Google Sheets" if usar_sheets else "⚠️ Modo local")
    st.divider()

    # Selector de mes activo
    meses_set = {t["fecha"][:7] for t in data["transacciones"]}
    meses_set.update(data.get("presupuestos_mensuales", {}).keys())
    meses_set.add(date.today().strftime("%Y-%m"))
    meses_sorted = sorted(meses_set, reverse=True)
    mes_default  = date.today().strftime("%Y-%m")
    idx_default  = meses_sorted.index(mes_default) if mes_default in meses_sorted else 0
    mes_activo_val = st.selectbox("Mes activo:", meses_sorted, index=idx_default, key="mes_activo")

    hoy        = date.today()
    total_dias = dias_en_mes()
    dia_actual = dias_transcurridos()
    st.metric("Hoy", hoy.strftime("%d %b %Y"))
    st.progress(dia_actual / total_dias, text=f"Día {dia_actual} de {total_dias}")
    st.divider()

    _df_res  = get_resumen()
    _df_ing  = get_df_ing()
    _ing_r   = _df_ing["monto"].sum() if not _df_ing.empty else 0
    _ing_p   = sum(data["ingresos_presupuesto"].values())
    _gas_r   = _df_res["Real"].sum()
    _gas_p   = _df_res["Planeado"].sum()

    st.metric("Ingresos reales", fmt_cop(_ing_r),
              delta=fmt_cop(_ing_r - _ing_p), delta_color="normal")
    st.metric("Gastos reales",   fmt_cop(_gas_r),
              delta=fmt_cop(_gas_r - _gas_p), delta_color="inverse")
    st.metric("Balance del mes", fmt_cop(_ing_r - _gas_r))

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💰 Presupuesto Mensual",
    "📋 Detalle Presupuesto",
    "📆 Gestión por Mes",
    "🔍 Transacciones",
    "📅 Línea de Tiempo",
    "➕ Nueva Transacción",
    "⚙️ Configuración",
])

# ══════════════════════════════════════════════
# TAB 1 — PRESUPUESTO MENSUAL
# ══════════════════════════════════════════════
with tab1:
    st.markdown(
        f"<h2 style='color:#e67e22;font-weight:700;margin-bottom:4px;'>Presupuesto Mensual</h2>"
        f"<p style='color:#888;margin-top:0;'>Mes activo: <strong>{_mes_activo()}</strong></p>",
        unsafe_allow_html=True,
    )

    df_res        = get_resumen()
    df_ing_df     = get_df_ing()
    ing_real      = df_ing_df["monto"].sum() if not df_ing_df.empty else 0.0
    ing_plan      = sum(data["ingresos_presupuesto"].values())
    gasto_real    = df_res["Real"].sum()
    gasto_plan    = df_res["Planeado"].sum()
    ahorro_real   = df_res[df_res["Tipo"] == "Ahorro"]["Real"].sum()
    balance_real  = ing_real - gasto_real
    balance_plan  = ing_plan - gasto_plan

    # ── Gráfica resumen: Ingresos / Gastos / Balance ──
    col_chart, col_bal = st.columns([3, 1])

    with col_chart:
        categorias_chart = ["Ingresos", "Gastos"]
        fig_res = go.Figure()
        fig_res.add_trace(go.Bar(
            name="Planeado",
            x=categorias_chart,
            y=[ing_plan, gasto_plan],
            marker_color="#b0bec5",
            text=[fmt_val(ing_plan), fmt_val(gasto_plan)],
            textposition="outside",
            textfont=dict(size=12, color="#607d8b"),
            width=0.35,
        ))
        fig_res.add_trace(go.Bar(
            name="Real",
            x=categorias_chart,
            y=[ing_real, gasto_real],
            marker_color=["#27ae60", "#e67e22"],
            text=[fmt_val(ing_real), fmt_val(gasto_real)],
            textposition="outside",
            textfont=dict(size=13, color="#333"),
            width=0.35,
        ))
        fig_res.update_layout(
            barmode="group",
            height=300,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(t=60, b=10, l=10, r=10),
            yaxis=dict(showgrid=True, gridcolor="#f0f0f0", showticklabels=False),
            xaxis=dict(showgrid=False, tickfont=dict(size=14, color="#343a40")),
        )
        st.plotly_chart(fig_res, use_container_width=True)

    with col_bal:
        bal_color = "#27ae60" if balance_real >= 0 else "#e74c3c"
        st.markdown(
            f"""
            <div style="background:#f8f9fa;border-radius:12px;padding:24px 16px;
                        text-align:center;margin-top:10px;border-left:4px solid {bal_color};">
                <div style="color:#888;font-size:0.85em;margin-bottom:6px;">Balance del mes</div>
                <div style="font-size:1.9em;font-weight:700;color:{bal_color};">
                    {fmt_val(balance_real)}
                </div>
                <hr style="border:none;border-top:1px dashed #dee2e6;margin:12px 0;">
                <div style="color:#888;font-size:0.8em;">Planeado</div>
                <div style="font-size:1.1em;font-weight:600;color:#6c757d;">{fmt_val(balance_plan)}</div>
                <hr style="border:none;border-top:1px dashed #dee2e6;margin:12px 0;">
                <div style="color:#888;font-size:0.8em;">Cajita (Ahorro)</div>
                <div style="font-size:1.1em;font-weight:600;color:#3498db;">{fmt_val(ahorro_real)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Barras de progreso: Ingresos y Gastos ──
    col_ing, col_gas = st.columns(2)
    max_i = max(ing_plan, 1)
    max_e = max(gasto_plan, 1)

    with col_ing:
        st.markdown("**Ingresos**")
        l, b = st.columns([1, 4])
        l.markdown("<span style='color:#888;font-size:.85em;'>Planeado</span>", unsafe_allow_html=True)
        b.progress(1.0, text=fmt_val(ing_plan))
        l, b = st.columns([1, 4])
        l.markdown("<span style='color:#888;font-size:.85em;'>Real</span>", unsafe_allow_html=True)
        b.progress(min(ing_real / max_i, 1.0), text=fmt_val(ing_real))

    with col_gas:
        st.markdown("**Gastos**")
        l, b = st.columns([1, 4])
        l.markdown("<span style='color:#888;font-size:.85em;'>Planeado</span>", unsafe_allow_html=True)
        b.progress(1.0, text=fmt_val(gasto_plan))
        l, b = st.columns([1, 4])
        l.markdown("<span style='color:#888;font-size:.85em;'>Real</span>", unsafe_allow_html=True)
        b.progress(min(gasto_real / max_e, 1.0), text=fmt_val(gasto_real))

    st.divider()

    # ── Gráficas por tipo: Gasto Fijo / Variable / Ahorro ──
    st.markdown("**Ejecución por tipo de gasto**")
    tipos_cols = st.columns(3)
    for i, tipo in enumerate(["Gasto Fijo", "Gasto Variable", "Ahorro"]):
        df_t   = df_res[df_res["Tipo"] == tipo]
        plan_t = df_t["Planeado"].sum()
        real_t = df_t["Real"].sum()
        bal_t  = plan_t - real_t
        pct_t  = real_t / plan_t * 100 if plan_t > 0 else 0
        bar_color = "#e74c3c" if pct_t > 100 else "#27ae60" if pct_t <= 80 else "#f39c12"
        bg, border = TIPO_STYLE.get(tipo, ("#f5f5f5", "#aaa"))

        fig_t = go.Figure()
        fig_t.add_trace(go.Bar(
            y=["Planeado", "Real"],
            x=[plan_t, real_t],
            orientation="h",
            marker_color=["#b0bec5", bar_color],
            text=[fmt_val(plan_t), fmt_val(real_t)],
            textposition="inside",
            textfont=dict(size=11, color="white"),
        ))
        fig_t.update_layout(
            height=110,
            margin=dict(t=10, b=10, l=10, r=10),
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=11)),
        )
        with tipos_cols[i]:
            st.markdown(
                f"<div style='background:{bg};border-left:4px solid {border};"
                f"border-radius:6px;padding:6px 10px;margin-bottom:4px;'>"
                f"<b style='color:#343a40;'>{tipo}</b>"
                f"<span style='float:right;color:#6c757d;font-size:.85em;'>{pct_t:.0f}%</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig_t, use_container_width=True)
            st.markdown(
                f"<div style='text-align:center;font-size:.82em;color:#6c757d;margin-top:-12px;'>"
                f"Balance: <b style='color:#27ae60' >{fmt_val(bal_t)}</b></div>",
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════
# TAB 2 — DETALLE PRESUPUESTO
# ══════════════════════════════════════════════
with tab2:
    st.markdown(
        "<h3 style='color:#2c3e50;margin-bottom:4px;'>Detalle del Presupuesto</h3>",
        unsafe_allow_html=True,
    )
    st.caption(f"Mes activo: **{_mes_activo()}**")

    df_res2 = get_resumen()

    col_gastos2, col_ing2 = st.columns(2)

    with col_gastos2:
        st.markdown(
            "<div style='background:#fff5f5;border-radius:8px;padding:8px 12px;margin-bottom:8px;"
            "border-left:4px solid #e74c3c;'>"
            "<span style='font-weight:700;color:#e74c3c;font-size:1em;'>Gastos</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(build_expense_table(df_res2), unsafe_allow_html=True)

    with col_ing2:
        st.markdown(
            "<div style='background:#f0fff4;border-radius:8px;padding:8px 12px;margin-bottom:8px;"
            "border-left:4px solid #27ae60;'>"
            "<span style='font-weight:700;color:#27ae60;font-size:1em;'>Ingresos</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(build_income_table(), unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 3 — GESTIÓN POR MES
# ══════════════════════════════════════════════
with tab3:
    st.markdown(
        "<h3 style='color:#2c3e50;margin-bottom:4px;'>Gestión de Presupuesto por Mes</h3>",
        unsafe_allow_html=True,
    )
    st.caption("Crea o edita el presupuesto para cada mes. Puedes agregar nuevas categorías y montos.")

    mes_hoy3  = date.today().strftime("%Y-%m")
    meses3_set = {t["fecha"][:7] for t in data["transacciones"]}
    meses3_set.update(data.get("presupuestos_mensuales", {}).keys())
    # Agregar próximos 3 meses
    for delta in range(3):
        m = date.today().replace(day=1)
        for _ in range(delta):
            m = (m.replace(day=28) + pd.Timedelta(days=4)).replace(day=1)
        meses3_set.add(m.strftime("%Y-%m"))
    meses3_set.add(mes_hoy3)
    meses3_sorted = sorted(meses3_set, reverse=True)

    col_sel3, col_btn3 = st.columns([2, 2])
    with col_sel3:
        mes_sel3 = st.selectbox(
            "Selecciona el mes:",
            meses3_sorted,
            index=meses3_sorted.index(mes_hoy3) if mes_hoy3 in meses3_sorted else 0,
            key="tab3_mes_sel",
        )
    with col_btn3:
        st.write("")
        copiar = st.button("📋 Copiar presupuesto del mes anterior", key="btn_copiar_mes")

    pm3 = data.get("presupuestos_mensuales", {})

    # Determinar qué base cargar
    if copiar:
        idx3 = meses3_sorted.index(mes_sel3) if mes_sel3 in meses3_sorted else 0
        mes_ant = meses3_sorted[idx3 + 1] if idx3 + 1 < len(meses3_sorted) else None
        if mes_ant and mes_ant in pm3:
            base3 = pm3[mes_ant]
            st.info(f"Copiado desde {mes_ant}. Guarda para confirmar.")
        elif mes_ant:
            base3 = data["presupuesto"]
            st.info("No hay presupuesto guardado para el mes anterior. Usando base.")
        else:
            base3 = data["presupuesto"]
    elif mes_sel3 in pm3:
        base3 = pm3[mes_sel3]
    else:
        base3 = data["presupuesto"]

    pres3_df = pd.DataFrame([
        {"Categoría": k, "Tipo": v[0], "Planeado (K COP)": float(v[1])}
        for k, v in base3.items()
    ])

    st.markdown(f"**Presupuesto para {mes_sel3}** {'(guardado)' if mes_sel3 in pm3 else '(base)'}")
    pres3_edit = st.data_editor(
        pres3_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Categoría": st.column_config.TextColumn("Categoría", width="medium"),
            "Tipo": st.column_config.SelectboxColumn(
                "Tipo", options=["Gasto Fijo", "Gasto Variable", "Ahorro", "Impuesto"]),
            "Planeado (K COP)": st.column_config.NumberColumn(
                "Planeado (K COP)", format="$%.0fK", min_value=0),
        },
        hide_index=True,
        key=f"editor_mes_{mes_sel3}",
    )

    col_s1, col_s2, _ = st.columns([2, 2, 2])
    with col_s1:
        if st.button("💾 Guardar presupuesto del mes", type="primary"):
            nuevo = {
                str(row["Categoría"]): [str(row["Tipo"]), float(row["Planeado (K COP)"])]
                for _, row in pres3_edit.iterrows()
                if str(row.get("Categoría", "")).strip()
            }
            if "presupuestos_mensuales" not in data:
                data["presupuestos_mensuales"] = {}
            data["presupuestos_mensuales"][mes_sel3] = nuevo
            if usar_sheets:
                with st.spinner("Guardando..."):
                    guardar_presupuesto_mes(client, mes_sel3, nuevo)
            st.success(f"Presupuesto guardado para {mes_sel3}")
            st.rerun()

    with col_s2:
        if st.button("✅ Activar como presupuesto base"):
            nuevo = {
                str(row["Categoría"]): [str(row["Tipo"]), float(row["Planeado (K COP)"])]
                for _, row in pres3_edit.iterrows()
                if str(row.get("Categoría", "")).strip()
            }
            data["presupuesto"] = nuevo
            if usar_sheets:
                with st.spinner("Guardando..."):
                    guardar_presupuesto(client, nuevo)
            st.success("Presupuesto base actualizado")
            st.rerun()

    # Vista previa de totales
    if not pres3_edit.empty:
        st.divider()
        st.markdown("**Resumen del presupuesto editado**")
        tipos_preview = pres3_edit.groupby("Tipo")["Planeado (K COP)"].sum().reset_index()
        tipos_preview.columns = ["Tipo", "Total Planeado"]
        tipos_preview["Total Planeado"] = tipos_preview["Total Planeado"].map(fmt_val)
        total_row = pd.DataFrame([{"Tipo": "**TOTAL**", "Total Planeado": fmt_val(pres3_edit["Planeado (K COP)"].sum())}])
        st.dataframe(pd.concat([tipos_preview, total_row], ignore_index=True),
                     use_container_width=False, hide_index=True)


# ══════════════════════════════════════════════
# TAB 4 — TRANSACCIONES
# ══════════════════════════════════════════════
with tab4:
    st.markdown(
        "<h3 style='color:#2c3e50;margin-bottom:4px;'>Transacciones</h3>",
        unsafe_allow_html=True,
    )

    df_all4 = get_df_trans_all()
    if not df_all4.empty:
        meses4 = sorted(df_all4["fecha"].dt.strftime("%Y-%m").unique(), reverse=True)
        col_f1, col_f2, col_f3 = st.columns(3)
        mes4  = col_f1.selectbox("Mes:", meses4, key="t4_mes",
                                  index=meses4.index(_mes_activo()) if _mes_activo() in meses4 else 0)
        cat4  = col_f2.selectbox("Categoría:", ["Todas"] + sorted(df_all4["categoria"].unique()), key="t4_cat")
        med4  = col_f3.selectbox("Medio:", ["Todos"] + sorted(df_all4["medio"].unique()), key="t4_med")

        df_f4 = df_all4[df_all4["fecha"].dt.strftime("%Y-%m") == mes4]
        if cat4 != "Todas":
            df_f4 = df_f4[df_f4["categoria"] == cat4]
        if med4 != "Todos":
            df_f4 = df_f4[df_f4["medio"] == med4]

        st.markdown(build_pivot_table(df_f4), unsafe_allow_html=True)
    else:
        st.info("No hay transacciones registradas.")


# ══════════════════════════════════════════════
# TAB 5 — LÍNEA DE TIEMPO
# ══════════════════════════════════════════════
with tab5:
    st.header("📅 Línea de Tiempo de Gastos")
    df5 = get_df_trans()
    if df5.empty:
        st.info("No hay transacciones para este mes.")
    else:
        # Separar gastos reales de ahorro
        ahorro_cats5 = {cat for cat, vals in _presupuesto_activo().items() if vals[0] == "Ahorro"}
        df5_gasto  = df5[~df5["categoria"].isin(ahorro_cats5)]
        df5_ahorro = df5[df5["categoria"].isin(ahorro_cats5)]

        def _agg_dia(df_sub):
            if df_sub.empty:
                return pd.DataFrame(columns=["fecha", "monto", "acumulado"])
            d = df_sub.groupby("fecha")["monto"].sum().reset_index().sort_values("fecha")
            d["acumulado"] = d["monto"].cumsum()
            return d

        df_dia_g = _agg_dia(df5_gasto)
        df_dia_a = _agg_dia(df5_ahorro)

        res5 = get_resumen()
        total_plan5_g = res5[res5["Tipo"] != "Ahorro"]["Planeado"].sum()
        total_plan5_a = res5[res5["Tipo"] == "Ahorro"]["Planeado"].sum()

        col5a, col5b = st.columns(2)

        with col5a:
            st.subheader("Movimientos por día")
            fig5a = go.Figure()
            if not df_dia_g.empty:
                fig5a.add_trace(go.Scatter(
                    x=df_dia_g["fecha"], y=df_dia_g["monto"],
                    mode="lines+markers", name="Gasto",
                    line=dict(color="#e74c3c", width=2),
                    marker=dict(size=7),
                    fill="tozeroy", fillcolor="rgba(231,76,60,0.08)",
                ))
            if not df_dia_a.empty:
                fig5a.add_trace(go.Scatter(
                    x=df_dia_a["fecha"], y=df_dia_a["monto"],
                    mode="lines+markers", name="Ahorro",
                    line=dict(color="#3498db", width=2),
                    marker=dict(size=7),
                    fill="tozeroy", fillcolor="rgba(52,152,219,0.08)",
                ))
            fig5a.update_layout(
                height=300, plot_bgcolor="white",
                yaxis_title="Miles COP", xaxis_title="",
                margin=dict(t=30, b=20),
                yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig5a, use_container_width=True)

        with col5b:
            st.subheader("Acumulado: Gasto vs Ahorro")
            hoy5     = date.today()
            quincena = date(hoy5.year, hoy5.month, 15)

            fig5b = go.Figure()
            if not df_dia_g.empty:
                fig5b.add_trace(go.Scatter(
                    x=df_dia_g["fecha"], y=df_dia_g["acumulado"],
                    mode="lines+markers", name="Gasto acumulado",
                    line=dict(color="#e74c3c", width=2),
                    marker=dict(size=6),
                    fill="tozeroy", fillcolor="rgba(231,76,60,0.06)",
                ))
            if not df_dia_a.empty:
                fig5b.add_trace(go.Scatter(
                    x=df_dia_a["fecha"], y=df_dia_a["acumulado"],
                    mode="lines+markers", name="Ahorro acumulado",
                    line=dict(color="#3498db", width=2),
                    marker=dict(size=6),
                    fill="tozeroy", fillcolor="rgba(52,152,219,0.06)",
                ))
            if total_plan5_g > 0:
                fig5b.add_hline(
                    y=total_plan5_g, line_dash="dash", line_color="#e74c3c", line_width=1.5,
                    annotation_text=f"Techo gasto: {fmt_val(total_plan5_g)}",
                    annotation_position="top right",
                    annotation_font=dict(color="#e74c3c", size=11),
                )
                fig5b.add_hline(
                    y=total_plan5_g * 0.5, line_dash="dot", line_color="#f39c12", line_width=1,
                    annotation_text="Meta quincena",
                    annotation_position="top right",
                    annotation_font=dict(color="#f39c12", size=10),
                )
            if total_plan5_a > 0:
                fig5b.add_hline(
                    y=total_plan5_a, line_dash="dash", line_color="#3498db", line_width=1.5,
                    annotation_text=f"Meta ahorro: {fmt_val(total_plan5_a)}",
                    annotation_position="bottom right",
                    annotation_font=dict(color="#3498db", size=11),
                )
            fig5b.add_shape(
                type="line",
                x0=str(quincena), x1=str(quincena),
                y0=0, y1=1, yref="paper",
                line=dict(dash="dot", color="#adb5bd", width=1),
            )
            fig5b.add_annotation(
                x=str(quincena), y=1, yref="paper",
                text="Día 15", showarrow=False,
                font=dict(color="#adb5bd", size=10),
                xanchor="left", yanchor="top",
            )
            fig5b.update_layout(
                height=300, plot_bgcolor="white",
                yaxis_title="Acumulado (K COP)", xaxis_title="",
                margin=dict(t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
            )
            st.plotly_chart(fig5b, use_container_width=True)

        st.subheader("Detalle por día")
        fecha_sel5 = st.date_input("Ver transacciones del día:", value=df5["fecha"].max().date(), key="t5_fecha")
        df_sel5 = df5[df5["fecha"].dt.date == fecha_sel5]
        if df_sel5.empty:
            st.info("Sin transacciones ese día.")
        else:
            st.dataframe(
                df_sel5[["descripcion","categoria","medio","monto"]].rename(columns={
                    "descripcion": "Descripción", "categoria": "Categoría",
                    "medio":       "Medio de Pago", "monto":    "Monto (K COP)",
                }),
                use_container_width=True, hide_index=True,
            )
            st.metric("Total del día", fmt_cop(df_sel5["monto"].sum()))


# ══════════════════════════════════════════════
# TAB 6 — NUEVA TRANSACCIÓN
# ══════════════════════════════════════════════
with tab6:
    st.header("➕ Ingresar Nueva Transacción")

    # ── Umbral para pedir confirmación ──
    UMBRAL_CONFIRMACION = 3000  # K COP

    def _es_inusual(monto):
        return monto < 0 or abs(monto) > UMBRAL_CONFIRMACION

    col_g6, col_i6 = st.columns(2)

    # ────────── NUEVO GASTO ──────────
    with col_g6:
        st.subheader("Nuevo Gasto")

        # Confirmación pendiente
        if "pending_gasto" in st.session_state:
            p = st.session_state["pending_gasto"]
            st.warning(
                f"⚠️ Vas a guardar **{fmt_val(p['monto'])}** en **{p['categoria']}**"
                f" — *{p['descripcion']}*\n\n¿El monto es correcto?"
            )
            c1, c2 = st.columns(2)
            if c1.button("✅ Sí, guardar", key="confirm_gasto", type="primary"):
                data["transacciones"].append(p)
                if usar_sheets:
                    with st.spinner("Guardando..."):
                        agregar_transaccion(client, p)
                del st.session_state["pending_gasto"]
                st.success(f"✅ Guardado: {fmt_val(p['monto'])} en {p['categoria']}")
                st.rerun()
            if c2.button("❌ Cancelar", key="cancel_gasto"):
                del st.session_state["pending_gasto"]
                st.rerun()
            st.divider()

        with st.form("form_gasto"):
            fecha_g  = st.date_input("Fecha", value=date.today(), key="fg_fecha")
            monto_g  = st.number_input("Monto (K COP)", value=0.0, step=10.0, key="fg_monto")
            desc_g   = st.text_input("Descripción", key="fg_desc")
            medio_g  = st.selectbox("Medio de pago",
                                    ["TD Nu Bank","Efectivo","TC Nu Bank","Otro"], key="fg_medio")
            cats_g   = sorted(_presupuesto_activo().keys())
            cat_g    = st.selectbox("Categoría", cats_g, key="fg_cat")
            submit_g = st.form_submit_button(
                "💾 Guardar Gasto", type="primary",
                disabled="pending_gasto" in st.session_state,
            )

        if submit_g:
            if monto_g == 0:
                st.error("⚠️ El monto no puede ser 0.")
            elif not desc_g.strip():
                st.error("⚠️ Escribe una descripción.")
            else:
                nueva = {"fecha": str(fecha_g), "monto": monto_g, "descripcion": desc_g,
                         "medio": medio_g, "categoria": cat_g}
                if _es_inusual(monto_g):
                    st.session_state["pending_gasto"] = nueva
                    st.rerun()
                else:
                    data["transacciones"].append(nueva)
                    if usar_sheets:
                        with st.spinner("Guardando..."):
                            agregar_transaccion(client, nueva)
                    st.success(f"✅ {fmt_val(monto_g)} en {cat_g}")
                    st.rerun()

    # ────────── NUEVO INGRESO ──────────
    with col_i6:
        st.subheader("Nuevo Ingreso")

        # Confirmación pendiente
        if "pending_ingreso" in st.session_state:
            p = st.session_state["pending_ingreso"]
            st.warning(
                f"⚠️ Vas a guardar **{fmt_val(p['monto'])}** en **{p['categoria']}**"
                f" — *{p['descripcion']}*\n\n¿El monto es correcto?"
            )
            c1, c2 = st.columns(2)
            if c1.button("✅ Sí, guardar", key="confirm_ingreso", type="primary"):
                data["ingresos"].append(p)
                if usar_sheets:
                    with st.spinner("Guardando..."):
                        agregar_ingreso(client, p)
                del st.session_state["pending_ingreso"]
                st.success(f"✅ Guardado: {fmt_val(p['monto'])} en {p['categoria']}")
                st.rerun()
            if c2.button("❌ Cancelar", key="cancel_ingreso"):
                del st.session_state["pending_ingreso"]
                st.rerun()
            st.divider()

        with st.form("form_ingreso"):
            fecha_i  = st.date_input("Fecha", value=date.today(), key="fi_fecha")
            monto_i  = st.number_input("Monto (K COP)", value=0.0, step=100.0, key="fi_monto")
            desc_i   = st.text_input("Descripción", key="fi_desc")
            cat_i    = st.selectbox("Categoría", sorted(data["ingresos_presupuesto"].keys()), key="fi_cat")
            submit_i = st.form_submit_button(
                "💾 Guardar Ingreso", type="primary",
                disabled="pending_ingreso" in st.session_state,
            )

        if submit_i:
            if monto_i == 0:
                st.error("⚠️ El monto no puede ser 0.")
            elif not desc_i.strip():
                st.error("⚠️ Escribe una descripción.")
            else:
                nuevo_ing = {"fecha": str(fecha_i), "monto": monto_i,
                             "descripcion": desc_i, "categoria": cat_i}
                if _es_inusual(monto_i):
                    st.session_state["pending_ingreso"] = nuevo_ing
                    st.rerun()
                else:
                    data["ingresos"].append(nuevo_ing)
                    if usar_sheets:
                        with st.spinner("Guardando..."):
                            agregar_ingreso(client, nuevo_ing)
                    st.success(f"✅ {fmt_val(monto_i)} en {cat_i}")
                    st.rerun()

    st.divider()

    col_ed6a, col_ed6b = st.columns(2)

    # ── Tabla editable de GASTOS ──
    with col_ed6a:
        st.subheader("Gastos del mes (editables)")
        df_ed6 = get_df_trans()
        if not df_ed6.empty:
            df_ed6["fecha"] = df_ed6["fecha"].dt.strftime("%Y-%m-%d")
            df_edit6 = st.data_editor(
                df_ed6, use_container_width=True, num_rows="dynamic",
                column_config={
                    "fecha":     st.column_config.TextColumn("Fecha (YYYY-MM-DD)"),
                    "monto":     st.column_config.NumberColumn("Monto (K COP)", format="$%.0fK"),
                    "categoria": st.column_config.SelectboxColumn(
                        "Categoría", options=sorted(_presupuesto_activo().keys())),
                }, hide_index=True)
            if st.button("💾 Guardar cambios en gastos", key="btn_save_gastos_edit"):
                # Limpiar NaN y filas vacías antes de guardar
                df_limpia_g = df_edit6.copy()
                df_limpia_g["monto"] = pd.to_numeric(df_limpia_g["monto"], errors="coerce").fillna(0)
                df_limpia_g = df_limpia_g.fillna("")
                data["transacciones"] = [
                    {"fecha": str(r["fecha"]), "monto": float(r["monto"]),
                     "descripcion": str(r["descripcion"]), "medio": str(r["medio"]),
                     "categoria": str(r["categoria"])}
                    for r in df_limpia_g.to_dict("records")
                    if str(r.get("fecha", "")).strip() and float(r.get("monto", 0)) != 0
                ]
                if usar_sheets:
                    with st.spinner("Guardando en Google Sheets..."):
                        guardar_transacciones(client, data["transacciones"])
                st.success("Cambios en gastos guardados.")
                st.rerun()
        else:
            st.info("No hay gastos registrados para este mes.")

    # ── Tabla editable de INGRESOS ──
    with col_ed6b:
        st.subheader("Ingresos del mes (editables)")
        df_ed6i = get_df_ing()
        if not df_ed6i.empty:
            df_ed6i = df_ed6i.copy()
            df_ed6i["fecha"] = df_ed6i["fecha"].dt.strftime("%Y-%m-%d")
            df_edit6i = st.data_editor(
                df_ed6i, use_container_width=True, num_rows="dynamic",
                column_config={
                    "fecha":     st.column_config.TextColumn("Fecha (YYYY-MM-DD)"),
                    "monto":     st.column_config.NumberColumn("Monto (K COP)", format="$%.0fK"),
                    "descripcion": st.column_config.TextColumn("Descripción"),
                    "categoria": st.column_config.SelectboxColumn(
                        "Categoría", options=sorted(data["ingresos_presupuesto"].keys())),
                }, hide_index=True)
            if st.button("💾 Guardar cambios en ingresos", key="btn_save_ingresos_edit"):
                # Reemplazar solo los ingresos del mes activo; conservar otros meses
                mes_ed = _mes_activo()
                otros_meses_i = [
                    t for t in data["ingresos"]
                    if str(t.get("fecha", ""))[:7] != mes_ed
                ]
                # Limpiar NaN y filas completamente vacías antes de guardar
                df_limpia_i = df_edit6i.copy()
                df_limpia_i["monto"] = pd.to_numeric(df_limpia_i["monto"], errors="coerce").fillna(0)
                df_limpia_i = df_limpia_i.fillna("")
                editados_i = [
                    {"fecha": str(r["fecha"]), "monto": float(r["monto"]),
                     "descripcion": str(r["descripcion"]), "categoria": str(r["categoria"])}
                    for r in df_limpia_i.to_dict("records")
                    if str(r.get("fecha", "")).strip() and float(r.get("monto", 0)) != 0
                ]
                data["ingresos"] = otros_meses_i + editados_i
                if usar_sheets:
                    with st.spinner("Guardando en Google Sheets..."):
                        guardar_ingresos(client, data["ingresos"])
                st.success("Cambios en ingresos guardados.")
                st.rerun()
        else:
            st.info("No hay ingresos registrados para este mes.")


# ══════════════════════════════════════════════
# TAB 7 — CONFIGURACIÓN
# ══════════════════════════════════════════════
with tab7:
    st.header("⚙️ Configuración")
    st.subheader("Presupuesto base")
    pres_df7  = pd.DataFrame([{"Tipo": v[0], "Categoría": k, "Planeado (K COP)": v[1]}
                               for k, v in data["presupuesto"].items()])
    pres_edit7 = st.data_editor(
        pres_df7, use_container_width=True, num_rows="dynamic",
        column_config={
            "Tipo": st.column_config.SelectboxColumn(
                "Tipo", options=["Gasto Fijo","Gasto Variable","Ahorro","Impuesto"]),
            "Planeado (K COP)": st.column_config.NumberColumn(
                "Planeado (K COP)", format="$%.0fK", min_value=0),
        }, hide_index=True)
    if st.button("💾 Guardar presupuesto base"):
        nuevo7 = {row["Categoría"]: [row["Tipo"], float(row["Planeado (K COP)"])]
                  for _, row in pres_edit7.iterrows()}
        data["presupuesto"] = nuevo7
        if usar_sheets:
            with st.spinner("Guardando..."):
                guardar_presupuesto(client, nuevo7)
        st.success("Presupuesto base actualizado.")
        st.rerun()

    st.divider()
    st.subheader("Presupuesto de Ingresos")
    ing_df7  = pd.DataFrame([{"Categoría": k, "Planeado (K COP)": v}
                              for k, v in data["ingresos_presupuesto"].items()])
    ing_edit7 = st.data_editor(
        ing_df7, use_container_width=True,
        column_config={"Planeado (K COP)": st.column_config.NumberColumn(format="$%.0fK")},
        hide_index=True)
    if st.button("💾 Guardar ingresos presupuestados"):
        nuevo_ing7 = {row["Categoría"]: float(row["Planeado (K COP)"])
                      for _, row in ing_edit7.iterrows()}
        data["ingresos_presupuesto"] = nuevo_ing7
        if usar_sheets:
            with st.spinner("Guardando..."):
                guardar_ingresos_presupuesto(client, nuevo_ing7)
        st.success("Actualizado.")
        st.rerun()

    st.divider()
    if st.button("🔄 Recargar datos desde Google Sheets"):
        st.session_state.pop("data", None)
        st.rerun()

    st.divider()
    st.subheader("⚠️ Zona peligrosa")
    if st.button("🗑️ Resetear todos los datos al estado inicial"):
        st.session_state.pop("data", None)
        if usar_sheets:
            with st.spinner("Reseteando..."):
                guardar_transacciones(client, TRANSACCIONES_INICIALES)
                guardar_ingresos(client, INGRESOS_INICIALES)
                guardar_presupuesto(client, {k: list(v) for k, v in PRESUPUESTO_INICIAL.items()})
                guardar_ingresos_presupuesto(client, INGRESOS_PRESUPUESTO_INICIAL)
        st.success("Datos reseteados.")
        st.rerun()
