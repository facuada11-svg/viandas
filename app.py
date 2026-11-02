# app.py — Alimentación y Rutina de Niños (cuestionario de viandas)
# Ejecutar:  streamlit run app.py
# Requisitos: streamlit pandas numpy plotly
#
# Estructura esperada:
#   tu-proyecto/
#   ├── app.py
#   └── data/
#       └── form-1__cuestionario-viandas-y-rutina.csv

import re

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ============================================================
# CONSTANTES
# ============================================================
COLORES = ["#4CAF50", "#FF9800", "#2196F3", "#E91E63",
           "#9C27B0", "#00BCD4", "#FFC107", "#795548"]

# Total de estudiantes del curso (uno de ellos no quiso responder el cuestionario)
TOTAL_CURSO = 12


# ============================================================
# CARGA Y LIMPIEZA DE DATOS
# ============================================================
@st.cache_data(show_spinner=False)
def cargar_datos(ruta_csv: str) -> pd.DataFrame:
    """Carga el CSV del cuestionario y normaliza las columnas."""
    data = pd.read_csv(ruta_csv, encoding="utf-8-sig")

    renombres = {
        "ec5_uuid": "uuid",
        "created_at": "fecha_creacion",
        "uploaded_at": "fecha_subida",
        "title": "titulo",
        "1_Cmo_te_gusta_que_t": "nombre",
        "2_Cuntos_aos_tens": "edad",
        "3_A_qu_grado_vas": "grado",
        "4_Coms_carne": "come_carne",
        "5_Por_qu_no_coms_car": "razon_no_carne",
        "6_Coms_vegetales": "come_vegetales",
        "7_Por_qu_no_coms_veg": "razon_no_vegetales",
        "8_Sabs_si_tens_celia": "celiaquia",
        "9_Sabs_si_tens_diabe": "diabetes",
        "10_Coms_la_vianda_qu": "come_vianda",
        "11_Por_qu_otra_razn_": "razon_no_vianda",
        "12_Qu_bebs_durante_e": "bebida",
        "13_Qu_te_gustara_que": "comida_deseada",
        "14_Cuando_coms_en_el": "ambiente_tranquilo",
        "15_Cuando_coms_en_el": "come_todo",
        "16_Si_no_termins_de_": "razon_no_termina",
        "17_Sabs_en_qu_moment": "momento_merienda",
        "18_Coms_la_merienda_": "come_merienda",
        "19_La_hora_de_la_mer": "merienda_ayuda_hora",
        "20_Tens_hambre_despu": "hambre_despues",
        "21_Cuntas_veces_coms": "cantidad_comidas",
        "22_Cules_son_esas_co": "cuales_comidas",
    }
    data = data.rename(columns=renombres)

    # Anonimización: se eliminan las columnas que identifican a los niños
    data = data.drop(
        columns=[c for c in ["nombre", "uuid", "titulo"] if c in data.columns]
    )

    # Limpieza de texto
    for col in data.select_dtypes(include="object").columns:
        data[col] = (
            data[col]
            .astype(str)
            .str.replace('"', "", regex=False)
            .str.strip()
            .replace({"nan": np.nan, "": np.nan, "-": np.nan})
        )

    if "edad" in data.columns:
        data["edad"] = pd.to_numeric(data["edad"], errors="coerce")

    for c in ["fecha_creacion", "fecha_subida"]:
        if c in data.columns:
            data[c] = pd.to_datetime(data[c], errors="coerce", utc=True)

    # Guardamos el texto original de la respuesta sobre la vianda: cuando
    # contestan "No, porque no me gusta." el motivo viene dentro de la respuesta.
    if "come_vianda" in data.columns:
        data["come_vianda_detalle"] = data["come_vianda"]

    def normaliza_si_no(x):
        if pd.isna(x):
            return np.nan
        x = str(x).strip().lower()
        if x.startswith("sí") or x.startswith("si"):
            return "Sí"
        if x.startswith("no"):
            return "No"
        return x.capitalize()

    for col in ["come_carne", "come_vegetales", "come_vianda",
                "merienda_ayuda_hora", "come_merienda", "hambre_despues",
                "celiaquia", "diabetes"]:
        if col in data.columns:
            data[col] = data[col].apply(normaliza_si_no)

    return data


# ============================================================
# FUNCIONES AUXILIARES DE GRÁFICOS
# ============================================================
def conteo(serie: pd.Series, nombre: str) -> pd.DataFrame:
    """Cuenta respuestas y les saca el punto final ("Agua." -> "Agua")."""
    s = serie.dropna().astype(str).str.strip().str.rstrip(".")
    s = s[s != ""]
    vc = s.value_counts().reset_index()
    vc.columns = [nombre, "Cantidad"]
    return vc


def torta(serie: pd.Series, key: str) -> None:
    vc = conteo(serie, "Respuesta")
    if vc.empty:
        st.info("Sin respuestas registradas.")
        return
    fig = px.pie(vc, names="Respuesta", values="Cantidad",
                 color_discrete_sequence=COLORES, hole=0.45)
    fig.update_traces(textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True, key=key)


def barras(serie: pd.Series, etiqueta: str, key: str,
           horizontal: bool = False) -> None:
    vc = conteo(serie, etiqueta)
    if vc.empty:
        st.info("Sin respuestas registradas.")
        return
    if horizontal:
        fig = px.bar(vc, x="Cantidad", y=etiqueta, orientation="h",
                     color=etiqueta, color_discrete_sequence=COLORES,
                     text="Cantidad")
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
    else:
        fig = px.bar(vc, x=etiqueta, y="Cantidad",
                     color=etiqueta, color_discrete_sequence=COLORES,
                     text="Cantidad")
        fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=key)


def lista_textos(serie: pd.Series) -> None:
    """Muestra respuestas de texto libre como una lista."""
    valores = serie.dropna().astype(str).str.strip()
    valores = valores[valores != ""]
    if valores.empty:
        st.info("Sin respuestas registradas.")
        return
    for v in valores:
        st.markdown(f"- {v}")


def lista_conteo(items: list) -> None:
    """Lista con viñetas; agrega (n) cuando algo se repite. Para pocos datos."""
    s = pd.Series(items, dtype="object").dropna()
    if s.empty:
        st.caption("Sin respuestas.")
        return
    for nombre, n in s.value_counts().items():
        st.markdown(f"- {nombre}" + (f" ({n})" if n > 1 else ""))


def motivo_no_vianda(fila) -> object:
    """Motivo principal (una categoría) por el que un estudiante no come la vianda."""
    if fila.get("come_vianda") != "No":
        return np.nan
    partes = []
    detalle = fila.get("come_vianda_detalle")
    if pd.notna(detalle):
        partes.append(
            re.sub(r"^\s*no\s*[,.:;-]*\s*", "", str(detalle), flags=re.IGNORECASE)
        )
    otra = fila.get("razon_no_vianda")
    if pd.notna(otra):
        partes.append(str(otra))
    texto = " ".join(partes).strip().rstrip(".")
    return agrupar_razon_vianda(texto) if texto else "Sin motivo indicado"


def grafico_hambre_segun(data: pd.DataFrame, columna: str, key: str,
                         orden: list = None) -> None:
    """Porcentaje de hambre después del colegio dentro de cada grupo de `columna`."""
    base = data[[columna, "hambre_despues"]].dropna().copy()
    if base.empty:
        st.info("Sin respuestas registradas.")
        return

    base["Grupo"] = base[columna].astype(str).str.strip().str.rstrip(".")
    base["Hambre"] = base["hambre_despues"].astype(str).str.rstrip(".")

    conteo = base.groupby(["Grupo", "Hambre"]).size().reset_index(name="n")
    conteo["total"] = conteo.groupby("Grupo")["n"].transform("sum")
    conteo["Porcentaje"] = conteo["n"] / conteo["total"] * 100
    conteo["Etiqueta"] = (
        conteo["Grupo"] + " (n=" + conteo["total"].astype(str) + ")"
    )
    conteo["Texto"] = conteo["Porcentaje"].round().astype(int).astype(str) + "%"

    etiquetas = dict(zip(conteo["Grupo"], conteo["Etiqueta"]))
    if orden:
        grupos = [g for g in orden if g in etiquetas]
        grupos += [g for g in etiquetas if g not in grupos]
    else:
        totales = conteo.groupby("Grupo")["total"].first()
        grupos = totales.sort_values(ascending=False).index.tolist()
    orden_etiquetas = [etiquetas[g] for g in grupos]

    fig = px.bar(
        conteo, x="Porcentaje", y="Etiqueta", color="Hambre",
        orientation="h", text="Texto",
        color_discrete_map={"Sí": "#E91E63", "A veces": "#FF9800", "No": "#4CAF50"},
        category_orders={
            "Etiqueta": orden_etiquetas,
            "Hambre": ["Sí", "A veces", "No"],
        },
    )
    fig.update_layout(
        barmode="stack",
        xaxis=dict(range=[0, 100], title="% de estudiantes de cada grupo"),
        yaxis_title=None,
        legend_title_text="¿Tiene hambre?",
        legend=dict(orientation="h", y=-0.35),
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True, key=key)


def grafico_cruce_hambre(data: pd.DataFrame) -> None:
    """Cruza vianda y merienda con el hambre después del colegio.

    Muestra, dentro de cada grupo, qué porcentaje tiene hambre (Sí / A veces / No).
    """
    base = data[["come_vianda", "come_merienda", "hambre_despues"]].dropna().copy()
    if base.empty:
        st.info("Sin respuestas registradas.")
        return

    def grupo(fila) -> str:
        vianda = fila["come_vianda"] == "Sí"
        merienda = fila["come_merienda"] == "Sí"
        if vianda and merienda:
            return "Come la vianda y la merienda"
        if vianda:
            return "Come la vianda, pero no la merienda"
        if merienda:
            return "No come la vianda, pero sí la merienda"
        return "No come ni la vianda ni la merienda"

    orden_grupos = [
        "Come la vianda y la merienda",
        "Come la vianda, pero no la merienda",
        "No come la vianda, pero sí la merienda",
        "No come ni la vianda ni la merienda",
    ]

    base["Grupo"] = base.apply(grupo, axis=1)
    base["Hambre"] = base["hambre_despues"].astype(str).str.rstrip(".")

    conteo = base.groupby(["Grupo", "Hambre"]).size().reset_index(name="n")
    conteo["total"] = conteo.groupby("Grupo")["n"].transform("sum")
    conteo["Porcentaje"] = conteo["n"] / conteo["total"] * 100
    conteo["Etiqueta"] = (
        conteo["Grupo"] + " (n=" + conteo["total"].astype(str) + ")"
    )
    conteo["Texto"] = conteo["Porcentaje"].round().astype(int).astype(str) + "%"

    etiquetas = dict(zip(conteo["Grupo"], conteo["Etiqueta"]))
    orden_etiquetas = [etiquetas[g] for g in orden_grupos if g in etiquetas]

    fig = px.bar(
        conteo, x="Porcentaje", y="Etiqueta", color="Hambre",
        orientation="h", text="Texto",
        color_discrete_map={"Sí": "#E91E63", "A veces": "#FF9800", "No": "#4CAF50"},
        category_orders={
            "Etiqueta": orden_etiquetas,
            "Hambre": ["Sí", "A veces", "No"],
        },
    )
    fig.update_layout(
        barmode="stack",
        xaxis=dict(range=[0, 100], title="% de estudiantes de cada grupo"),
        yaxis_title=None,
        legend_title_text="¿Tiene hambre después del colegio?",
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True, key="cruce_hambre")

    g = conteo[conteo["Grupo"] == "Come la vianda y la merienda"]
    if not g.empty:
        total_g = int(g["total"].iloc[0])
        hambre_si = int(g.loc[g["Hambre"] == "Sí", "n"].sum())
        hambre_a_veces = int(g.loc[g["Hambre"] == "A veces", "n"].sum())
        st.markdown(
            f"De los **{total_g}** estudiantes que comen la vianda y la merienda, "
            f"**{hambre_si / total_g * 100:.0f}%** dice tener hambre después del colegio "
            f"y **{hambre_a_veces / total_g * 100:.0f}%** dice que a veces."
        )
    st.caption(
        "\"Come la merienda\" = la come apenas la sirven. Los porcentajes son "
        "dentro de cada grupo; con pocos estudiantes (n) cambian mucho con una "
        "sola respuesta."
    )


# Comidas del día: se buscan por raíz de la palabra para juntar variantes
# ("Desayuno", "desayuna", "Desayuno (a veces xq se duerme)", etc.)
COMIDAS_DIA = {
    "Desayuno": r"desay",
    "Almuerzo": r"almu",
    "Merienda": r"merie",
    "Cena": r"\bcen",
}


def clasificar_comidas(texto: str) -> list:
    """Devuelve qué comidas del día menciona una respuesta (sin repetir)."""
    t = str(texto).lower()
    encontradas = [nombre for nombre, patron in COMIDAS_DIA.items()
                   if re.search(patron, t)]
    return encontradas


def agrupar_razon_no_termina(texto: str) -> str:
    """Junta respuestas parecidas sobre por qué no termina de comer."""
    t = str(texto).lower().strip().rstrip(".")
    if "recuerd" in t or "no sé" in t:
        return "No recuerda"
    if "llen" in t:
        return "Se llena"
    if "distra" in t or "jug" in t:
        return "Se distrae jugando"
    if "gust" in t:
        return "No le gusta la comida"
    t = re.sub(r"^porque\s+", "", t)
    return t.capitalize()


def agrupar_razon_vianda(texto: str) -> str:
    """Junta respuestas parecidas sobre por qué no come la vianda del colegio."""
    t = str(texto).lower().strip().rstrip(".")
    if "gust" in t:
        return "No le gusta"
    if "casa" in t:
        return "Come o trae comida de su casa"
    if "combi" in t:
        return "A veces no llega por la combi"
    if "quiere" in t:
        return "No quiere"
    if "otra raz" in t:
        return "Otra razón"
    return t.capitalize()


# Verduras que se buscan en las respuestas de "¿Por qué no come vegetales?"
VERDURAS = {
    "Papa": r"\bpapas?\b",
    "Batata": r"\bbatatas?\b",
    "Lechuga": r"\blechugas?\b",
    "Zanahoria": r"\bzanahorias?\b",
    "Morrón": r"\bmorr[oó]n(es)?\b",
    "Zapallo": r"\bzapallos?\b",
    "Zapallito": r"\bzapallitos?\b",
    "Calabaza": r"\bcalabazas?\b",
    "Tomate": r"\btomates?\b",
    "Cebolla": r"\bcebollas?\b",
    "Brócoli": r"\bbr[oó]colis?\b",
    "Espinaca": r"\bespinacas?\b",
    "Acelga": r"\bacelgas?\b",
    "Choclo": r"\bchoclos?\b",
    "Remolacha": r"\bremolachas?\b",
    "Pepino": r"\bpepinos?\b",
    "Berenjena": r"\bberenjenas?\b",
    "Coliflor": r"\bcoliflor(es)?\b",
    "Repollo": r"\brepollos?\b",
    "Arvejas": r"\barvejas?\b",
}


def analizar_verduras(texto: str):
    """Devuelve (verduras que sí come, verduras que no come) de una respuesta.

    Se asume que una verdura mencionada es una que NO come (la pregunta es
    "¿por qué no come?"), salvo que la respuesta diga "solo come ...".
    """
    t = str(texto).lower()
    encontradas = [n for n, patron in VERDURAS.items() if re.search(patron, t)]
    if re.search(r"\bs[oó]lo come|\bsolamente come", t):
        return encontradas, []
    return [], encontradas


def clasificar_tipo_razon(texto: str) -> str:
    """Un solo tipo de razón por respuesta (para el gráfico de torta)."""
    t = str(texto).lower()
    si, no = analizar_verduras(t)
    if si:
        return "Come solo algunas verduras"
    if re.search(r"sabor|textura|se ve|aspecto|olor", t):
        return "No le gusta el sabor, la textura o el aspecto"
    if re.search(r"prefiere|prefiero|come (un )?poco|poquito", t):
        return "Prefiere otra comida o come poco"
    if no:
        return "No come ciertas verduras"
    return "Otra razón"


def clasificar_otras_razones(texto: str) -> list:
    """Agrupa las razones que no son una lista de verduras."""
    t = str(texto).lower().strip()
    categorias = []
    if re.search(r"sabor|textura|se ve|aspecto|olor", t):
        categorias.append("No le gusta el sabor, la textura o el aspecto")
    if re.search(r"prefiere|prefiero", t):
        categorias.append("Prefiere otra comida")
    if re.search(r"come (un )?poco|poquito", t):
        categorias.append("Come poco")
    si, no = analizar_verduras(t)
    if not categorias and not si and not no:
        categorias.append(t.rstrip(".").capitalize())
    return categorias


# ============================================================
# APP
# ============================================================
def main() -> None:
    # --------------------------------------------------------
    # Configuración de página
    # --------------------------------------------------------
    st.set_page_config(
        page_title="Alimentación y Rutina de Niños",
        page_icon="🍎",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # --------------------------------------------------------
    # Carga del CSV
    # --------------------------------------------------------
    ruta_csv = Path(__file__).parent / "data" / "form-1__cuestionario-viandas-y-rutina.csv"

    if not ruta_csv.exists():
        st.error(
            f"No se encontró el archivo:\n\n`{ruta_csv}`\n\n"
            "Creá una carpeta `data/` al lado de `app.py` y colocá ahí el CSV "
            "con el nombre `form-1__cuestionario-viandas-y-rutina.csv`."
        )
        st.stop()

    df = cargar_datos(str(ruta_csv))

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------
    st.title("🍎 Alimentación y Rutina de Niños")
    st.markdown(
        "Análisis exploratorio del **cuestionario de viandas y rutina** "
        "respondido por estudiantes de 4to grado."
    )
    st.divider()

    # --------------------------------------------------------
    # Sidebar — filtros (solo edad: todos son del mismo grado)
    # --------------------------------------------------------
    st.sidebar.header("🔎 Filtros")

    edades = sorted(df["edad"].dropna().unique().tolist())
    if len(edades) > 1:
        rango_edad = st.sidebar.slider(
            "¿Cuántos años tiene?",
            int(min(edades)), int(max(edades)),
            (int(min(edades)), int(max(edades))),
        )
    elif len(edades) == 1:
        rango_edad = (int(edades[0]), int(edades[0]))
        st.sidebar.caption(f"Todos los estudiantes tienen {int(edades[0])} años.")
    else:
        rango_edad = (0, 100)

    df_f = df[
        df["edad"].between(rango_edad[0], rango_edad[1], inclusive="both")
    ].copy()

    st.sidebar.caption(f"Registros filtrados: **{len(df_f)}** de {len(df)}")

    # --------------------------------------------------------
    # Rutinas en números (lo central de la investigación)
    # --------------------------------------------------------
    total = len(df_f)
    sin_filtros = total == len(df)

    def pct(mascara: pd.Series) -> float:
        return float(mascara.mean() * 100) if total else 0.0

    pct_merienda_apenas = pct(df_f["come_merienda"].eq("Sí"))
    pct_hora_ayuda = pct(df_f["merienda_ayuda_hora"].eq("Sí"))
    pct_hambre = pct(df_f["hambre_despues"].eq("Sí"))
    pct_termina = pct(df_f["come_todo"].str.startswith("Siempre", na=False))

    st.subheader("Rutinas en números")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Come la merienda apenas la sirven",
        f"{pct_merienda_apenas:.0f}%",
    )
    c2.metric(
        "La merienda le marca la hora de salida",
        f"{pct_hora_ayuda:.0f}%",
        help="¿La hora de la merienda le ayuda a saber cuánto falta para irse a casa?",
    )
    c3.metric(
        "Tiene hambre después del colegio",
        f"{pct_hambre:.0f}%",
    )
    c4.metric(
        "Siempre termina la comida",
        f"{pct_termina:.0f}%",
        help="Cuando come en el colegio, ¿come todo lo que le sirven? (respuesta: siempre)",
    )

    # --------------------------------------------------------
    # Edades de los participantes
    # --------------------------------------------------------
    st.subheader("Edades de los participantes")
    col_edad, col_resumen = st.columns([1, 2])

    with col_edad:
        edades_vc = (
            df_f["edad"].dropna().astype(int)
            .value_counts().sort_index().reset_index()
        )
        edades_vc.columns = ["Edad", "Cantidad"]
        edades_vc["Edad"] = edades_vc["Edad"].astype(str) + " años"
        fig = px.bar(edades_vc, x="Edad", y="Cantidad", text="Cantidad",
                     color_discrete_sequence=["#2196F3"])
        fig.update_layout(height=250, xaxis_title=None,
                          yaxis=dict(visible=False),
                          margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True, key="edades")

    with col_resumen:
        if total and pd.notna(df_f["edad"].min()):
            grados_txt = ", ".join(sorted(df_f["grado"].dropna().unique()))
            if sin_filtros:
                quienes = (
                    f"**{total}** de los **{TOTAL_CURSO}** estudiantes "
                    f"de **{grados_txt}** respondieron"
                )
            else:
                quienes = f"**{total}** estudiantes de **{grados_txt}**"
            st.markdown(
                f"{quienes}, "
                f"de **{int(df_f['edad'].min())}** a **{int(df_f['edad'].max())}** años."
            )

    st.divider()

    # --------------------------------------------------------
    # Tabs
    # --------------------------------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "🥩 Alimentación y salud",
            "🍱 La vianda del colegio",
            "🥪 Merienda y rutina",
            "🍽️ ¿Tiene hambre después del colegio?",
            "📋 Datos crudos",
        ]
    )

    # ---------------- TAB 1 — ALIMENTACIÓN Y SALUD ----------------
    with tab1:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("¿Come carne?")
            torta(df_f["come_carne"], "torta_carne")

        with col_b:
            st.subheader("¿Come vegetales?")
            torta(df_f["come_vegetales"], "torta_vegetales")

        # Si todos comen carne, la pregunta es solo sobre vegetales
        if df_f["come_carne"].eq("Sí").all():
            st.subheader("¿Por qué no come vegetales?")
        else:
            st.subheader("¿Por qué no come carne / vegetales?")
        razones = pd.concat([
            df_f["razon_no_carne"].dropna(),
            df_f["razon_no_vegetales"].dropna(),
        ])
        if not razones.empty:
            verduras_si, verduras_no = [], []
            for texto in razones:
                si, no = analizar_verduras(texto)
                verduras_si += si
                verduras_no += no

            tipos = razones.apply(clasificar_tipo_razon)

            col_v1, col_v2 = st.columns(2)

            with col_v1:
                st.markdown("**Tipo de razón**")
                vc_tipos = conteo(tipos, "Razón")
                fig = px.pie(vc_tipos, names="Razón", values="Cantidad",
                             color_discrete_sequence=COLORES, hole=0.45)
                fig.update_traces(textinfo="value+percent")
                fig.update_layout(legend=dict(orientation="h", y=-0.1))
                st.plotly_chart(fig, use_container_width=True, key="torta_tipo_razon")

            with col_v2:
                st.markdown("**Verduras que mencionan**")
                filas = (
                    [{"Verdura": v, "Condición": "La come"} for v in verduras_si]
                    + [{"Verdura": v, "Condición": "No la come"} for v in verduras_no]
                )
                if filas:
                    vv = (
                        pd.DataFrame(filas)
                        .groupby(["Verdura", "Condición"]).size()
                        .reset_index(name="Cantidad")
                    )
                    fig = px.bar(
                        vv, x="Cantidad", y="Verdura", color="Condición",
                        orientation="h", text="Cantidad",
                        color_discrete_map={"La come": "#4CAF50",
                                            "No la come": "#E91E63"},
                    )
                    fig.update_yaxes(categoryorder="total ascending")
                    fig.update_xaxes(dtick=1)
                    fig.update_layout(legend_title_text="")
                    st.plotly_chart(fig, use_container_width=True,
                                    key="barras_verduras")
                else:
                    st.info("Ninguna respuesta nombra verduras.")

            st.caption(
                f"Respuestas escritas por {len(razones)} estudiantes, "
                "agrupadas por palabras clave."
            )
        elif (df_f["come_carne"].eq("Sí").all()
              and df_f["come_vegetales"].eq("Sí").all()):
            st.success("Todos los estudiantes comen carne y vegetales.")
        else:
            st.info("No hay razones registradas.")

        st.subheader("¿Sabe si tiene celiaquía o diabetes?")
        n_celiaquia = int(df_f["celiaquia"].eq("Sí").sum())
        n_diabetes = int(df_f["diabetes"].eq("Sí").sum())

        col_c1, col_c2 = st.columns(2)
        col_c1.metric("Celiaquía", f"{n_celiaquia} de {total}")
        col_c2.metric("Diabetes", f"{n_diabetes} de {total}")

        if n_celiaquia == 0 and n_diabetes == 0:
            st.success("Ningún estudiante declaró tener celiaquía ni diabetes.")

    # ---------------- TAB 2 — LA VIANDA DEL COLEGIO ----------------
    with tab2:
        st.header("🍱 La vianda del colegio")

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("¿Come la vianda que le da el colegio?")
            torta(df_f["come_vianda"], "torta_vianda")

        with col_b:
            st.subheader("¿Por qué no come la vianda del colegio?")
            detalle = df_f.loc[
                df_f["come_vianda"].eq("No"), "come_vianda_detalle"
            ].dropna()
            detalle = (
                detalle
                .str.replace(r"^\s*no\s*[,.:;-]*\s*", "", case=False, regex=True)
                .str.strip()
            )
            razones_vianda = pd.concat([
                detalle,
                df_f["razon_no_vianda"].dropna(),
            ]).str.strip().str.rstrip(".")
            razones_vianda = (
                razones_vianda[razones_vianda != ""].apply(agrupar_razon_vianda)
            )

            if not razones_vianda.empty:
                barras(razones_vianda, "Razón", "barras_razones_vianda",
                       horizontal=True)
            elif df_f["come_vianda"].eq("Sí").all():
                st.success("Todos los estudiantes comen la vianda del colegio.")
            else:
                st.info("No hay razones registradas.")

        col_c, col_d = st.columns(2)

        with col_c:
            st.subheader("¿Qué bebe durante el almuerzo, la merienda y el recreo?")
            barras(df_f["bebida"], "Bebida", "barras_bebida")

        with col_d:
            st.subheader("¿Qué le gustaría que se incluya en las viandas?")
            comidas = (
                df_f["comida_deseada"]
                .dropna()
                .str.split(",")
                .explode()
                .str.strip()
            )
            barras(comidas, "Comida", "barras_comida_deseada")

        col_e, col_f = st.columns(2)

        with col_e:
            st.subheader("Cuando come en el colegio, ¿come todo lo que le sirven?")
            barras(df_f["come_todo"], "Respuesta", "barras_come_todo")

        with col_f:
            st.subheader("¿Qué porcentaje de estudiantes termina la comida?")
            torta(df_f["come_todo"], "torta_come_todo")

        col_g, col_h = st.columns(2)

        with col_g:
            st.subheader("Cuando come en el colegio, ¿el ambiente le permite comer en tranquilidad?")
            torta(df_f["ambiente_tranquilo"], "torta_ambiente")

        with col_h:
            st.subheader("Si no termina de comer, ¿por qué cree que sea?")
            razones_no_termina = (
                df_f["razon_no_termina"].dropna().apply(agrupar_razon_no_termina)
            )
            barras(razones_no_termina, "Razón", "barras_razon_no_termina",
                   horizontal=True)

    # ---------------- TAB 3 — MERIENDA Y RUTINA ----------------
    with tab3:
        st.header("🥪 La merienda")

        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.subheader("¿Sabe en qué momento del día sirven la merienda?")
            barras(df_f["momento_merienda"], "Momento", "barras_momento_merienda")

        with col_m2:
            st.subheader("¿Come la merienda apenas la sirven?")
            torta(df_f["come_merienda"], "torta_come_merienda")

        st.divider()
        st.header("🕐 Rutina diaria")

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.subheader("¿Cuántas veces come al día?")
            barras(df_f["cantidad_comidas"], "Veces por día", "barras_cantidad_comidas")

        with col_r2:
            st.subheader("¿Cuáles son esas comidas?")
            comidas_dia = (
                df_f["cuales_comidas"]
                .dropna()
                .apply(clasificar_comidas)
                .explode()
            )
            barras(comidas_dia, "Comida", "barras_cuales_comidas")
            st.caption("Cantidad de estudiantes que mencionan cada comida.")

        st.subheader("¿La hora de la merienda le ayuda a saber cuánto falta para irse a casa?")
        col_r3, _ = st.columns(2)
        with col_r3:
            torta(df_f["merienda_ayuda_hora"], "torta_merienda_hora")

    # ---------------- TAB 4 — ¿TIENE HAMBRE DESPUÉS DEL COLEGIO? ----------------
    with tab4:
        hambre_txt = df_f["hambre_despues"].dropna().astype(str).str.rstrip(".")
        n_hambre_si = int(hambre_txt.eq("Sí").sum())
        n_hambre_av = int(hambre_txt.eq("A veces").sum())
        n_hambre_no = int(hambre_txt.eq("No").sum())

        col_p, col_n = st.columns(2)

        with col_p:
            st.subheader("¿Tiene hambre después del colegio?")
            torta(df_f["hambre_despues"], "torta_hambre")

        with col_n:
            st.subheader("En números")
            n1, n2, n3 = st.columns(3)
            n1.metric("Sí", f"{n_hambre_si} de {total}")
            n2.metric("A veces", f"{n_hambre_av} de {total}")
            n3.metric("No", f"{n_hambre_no} de {total}")

        st.divider()

        st.subheader("¿Tienen hambre después del colegio los que comen la vianda y la merienda?")
        grafico_cruce_hambre(df_f)

        st.divider()

        st.subheader("¿Quiénes tienen hambre y por qué?")
        st.caption(
            "Cada barra muestra qué porcentaje de ese grupo tiene hambre. Con pocos "
            "estudiantes por grupo (n), los porcentajes son orientativos."
        )

        df_h = df_f.copy()
        df_h["edad_txt"] = df_h["edad"].apply(
            lambda x: f"{int(x)} años" if pd.notna(x) else np.nan
        )
        if len(df_h):
            df_h["motivo_vianda"] = df_h.apply(motivo_no_vianda, axis=1)
        else:
            df_h["motivo_vianda"] = np.nan
        orden_edades = sorted(
            df_h["edad_txt"].dropna().unique(), key=lambda s: int(s.split()[0])
        )

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            st.markdown("**Según si termina la comida del colegio**")
            grafico_hambre_segun(df_h, "come_todo", "hambre_segun_come_todo")
        with col_h2:
            st.markdown("**Según cuántas veces come al día**")
            grafico_hambre_segun(df_h, "cantidad_comidas", "hambre_segun_cantidad")

        col_h3, col_h4 = st.columns(2)
        with col_h3:
            st.markdown("**Según la edad**")
            grafico_hambre_segun(df_h, "edad_txt", "hambre_segun_edad",
                                 orden=orden_edades)
        with col_h4:
            st.markdown("**Según por qué no come la vianda** (solo quienes no la comen)")
            grafico_hambre_segun(df_h, "motivo_vianda", "hambre_segun_motivo")

    # ---------------- TAB 5 — DATOS CRUDOS ----------------
    with tab5:
        st.subheader("📋 Dataset completo (filtrado)")
        st.dataframe(df_f, use_container_width=True, height=500)

        csv = df_f.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar CSV filtrado",
            data=csv,
            file_name="viandas_filtrado.csv",
            mime="text/csv",
        )

        st.subheader("Estadísticas descriptivas")
        st.dataframe(df_f.describe(include="all").transpose(),
                     use_container_width=True)

    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------
    st.divider()
    st.caption("Desarrollado con Streamlit · Pandas · NumPy · Plotly")


# ============================================================
# PUNTO DE ENTRADA
# ============================================================
main()
