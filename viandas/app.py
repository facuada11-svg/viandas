# app.py — Alimentación y Rutina de Niños (cuestionario de viandas)
# Ejecutar:  streamlit run app.py
# Requisitos: streamlit pandas numpy plotly
#
# Estructura esperada:
#   tu-proyecto/
#   ├── app.py
#   └── data/
#       └── form-1__cuestionario-viandas-y-rutina.csv

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


# ============================================================
# CARGA Y LIMPIEZA DE DATOS
# ============================================================
@st.cache_data(show_spinner=False)
def cargar_datos(ruta_csv: str) -> pd.DataFrame:
    """Carga el CSV del cuestionario y normaliza las columnas."""
    # ← FIX: se llama `data` en vez de `df` para no tapar el `df` global
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
        "11_Por_qu_otra_razn_": "razon_otra_comida",
        "12_Qu_bebs_durante_e": "bebida",
        "13_Qu_te_gustara_que": "comida_deseada",
        "14_Cuando_coms_en_el": "come_recreo",
        "15_Cuando_coms_en_el": "come_fuera_recreo",
        "16_Si_no_termins_de_": "termina_comida",
        "17_Sabs_en_qu_moment": "razon_no_termina",
        "18_Coms_la_merienda_": "come_merienda",
        "19_La_hora_de_la_mer": "hora_merienda",
        "20_Tens_hambre_despu": "hambre_despues",
        "21_Cuntas_veces_coms": "cantidad_comidas",
        "22_Cules_son_esas_co": "cuales_comidas",
    }
    data = data.rename(columns=renombres)

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
                "come_merienda", "hambre_despues"]:
        if col in data.columns:
            data[col] = data[col].apply(normaliza_si_no)

    return data


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
    # Sidebar — filtros
    # --------------------------------------------------------
    st.sidebar.header("🔎 Filtros")

    grados = sorted(df["grado"].dropna().unique().tolist())
    grado_sel = st.sidebar.multiselect("Grado", grados, default=grados)

    edades = sorted(df["edad"].dropna().unique().tolist())
    if edades:
        rango_edad = st.sidebar.slider(
            "Edad",
            int(min(edades)), int(max(edades)),
            (int(min(edades)), int(max(edades))),
        )
    else:
        rango_edad = (0, 100)

    df_f = df[
        df["grado"].isin(grado_sel)
        & df["edad"].between(rango_edad[0], rango_edad[1], inclusive="both")
    ].copy()

    st.sidebar.caption(f"Registros filtrados: **{len(df_f)}** de {len(df)}")

    # --------------------------------------------------------
    # Métricas principales
    # --------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)

    total = len(df_f)
    edad_prom = df_f["edad"].mean()

    # ← FIX: float(...) explícito evita el union int | Any | Literal[0]
    pct_carne: float = (
        float(df_f["come_carne"].eq("Sí").mean() * 100) if total else 0.0
    )
    pct_veg: float = (
        float(df_f["come_vegetales"].eq("Sí").mean() * 100) if total else 0.0
    )

    c1.metric("Total encuestados", f"{total}")
    c2.metric("Edad promedio", f"{edad_prom:.1f}" if pd.notna(edad_prom) else "—")
    c3.metric("Come carne", f"{pct_carne:.0f}%")
    c4.metric("Come vegetales", f"{pct_veg:.0f}%")

    st.divider()

    # --------------------------------------------------------
    # Tabs
    # --------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🥩 Alimentación", "🥤 Bebidas y comidas", "🕐 Rutina", "📋 Datos crudos"]
    )

    # ---------------- TAB 1 — ALIMENTACIÓN ----------------
    with tab1:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("¿Come carne?")
            vc = df_f["come_carne"].value_counts(dropna=False).reset_index()
            vc.columns = ["Respuesta", "Cantidad"]
            fig = px.pie(vc, names="Respuesta", values="Cantidad",
                         color_discrete_sequence=COLORES, hole=0.45)
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.subheader("¿Come vegetales?")
            vc = df_f["come_vegetales"].value_counts(dropna=False).reset_index()
            vc.columns = ["Respuesta", "Cantidad"]
            fig = px.pie(vc, names="Respuesta", values="Cantidad",
                         color_discrete_sequence=COLORES, hole=0.45)
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Razones por las que NO come carne / vegetales")
        razones = pd.concat([
            df_f["razon_no_carne"].dropna().rename("Razón"),
            df_f["razon_no_vegetales"].dropna().rename("Razón"),
        ])
        if not razones.empty:
            vc = razones.value_counts().reset_index()
            vc.columns = ["Razón", "Cantidad"]
            fig = px.bar(vc, x="Cantidad", y="Razón", orientation="h",
                         color="Cantidad", color_continuous_scale="Greens",
                         text="Cantidad")
            fig.update_layout(yaxis=dict(autorange="reversed"),
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de razones registradas.")

        st.subheader("Alergias / condiciones declaradas")
        cond = pd.DataFrame({
            "Condición": ["Celíaco/a", "Diabético/a"],
            "Cantidad": [
                df_f["celiaquia"].eq("Sí").sum(),
                df_f["diabetes"].eq("Sí").sum(),
            ],
        })
        fig = px.bar(cond, x="Condición", y="Cantidad",
                     color="Condición", color_discrete_sequence=COLORES,
                     text="Cantidad")
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- TAB 2 — BEBIDAS Y COMIDAS ----------------
    with tab2:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Bebida durante las comidas")
            vc = df_f["bebida"].value_counts(dropna=False).reset_index()
            vc.columns = ["Bebida", "Cantidad"]
            fig = px.bar(vc, x="Bebida", y="Cantidad",
                         color="Bebida", color_discrete_sequence=COLORES,
                         text="Cantidad")
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.subheader("Comida que le gustaría que traigan")
            comidas = (
                df_f["comida_deseada"]
                .dropna()
                .str.split(",")
                .explode()
                .str.strip()
            )
            vc = comidas.value_counts().reset_index()
            vc.columns = ["Comida", "Cantidad"]
            fig = px.bar(vc, x="Comida", y="Cantidad",
                         color="Comida", color_discrete_sequence=COLORES,
                         text="Cantidad")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("¿Come la vianda que trae?")
        vc = df_f["come_vianda"].value_counts(dropna=False).reset_index()
        vc.columns = ["Respuesta", "Cantidad"]
        fig = px.pie(vc, names="Respuesta", values="Cantidad",
                     color_discrete_sequence=COLORES, hole=0.45)
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- TAB 3 — RUTINA ----------------
    with tab3:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("¿Come durante el recreo?")
            vc = df_f["come_recreo"].value_counts(dropna=False).reset_index()
            vc.columns = ["Respuesta", "Cantidad"]
            fig = px.pie(vc, names="Respuesta", values="Cantidad",
                         color_discrete_sequence=COLORES, hole=0.45)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.subheader("¿Tiene hambre después de la escuela?")
            vc = df_f["hambre_despues"].value_counts(dropna=False).reset_index()
            vc.columns = ["Respuesta", "Cantidad"]
            fig = px.pie(vc, names="Respuesta", values="Cantidad",
                         color_discrete_sequence=COLORES, hole=0.45)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Cantidad de comidas al día")
        vc = df_f["cantidad_comidas"].value_counts(dropna=False).reset_index()
        vc.columns = ["Cantidad", "Frecuencia"]
        fig = px.bar(vc, x="Cantidad", y="Frecuencia", color="Cantidad",
                     color_discrete_sequence=COLORES, text="Frecuencia")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("¿Termina la comida?")
        vc = df_f["termina_comida"].value_counts(dropna=False).reset_index()
        vc.columns = ["Respuesta", "Cantidad"]
        fig = px.bar(vc, x="Respuesta", y="Cantidad", color="Respuesta",
                     color_discrete_sequence=COLORES, text="Cantidad")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Distribución de edades")
        fig = px.histogram(df_f, x="edad", nbins=8,
                           color_discrete_sequence=["#2196F3"],
                           text_auto=True)
        fig.update_layout(xaxis_title="Edad", yaxis_title="Frecuencia")
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- TAB 4 — DATOS CRUDOS ----------------
    with tab4:
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
