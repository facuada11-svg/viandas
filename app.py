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
    # Métricas principales (lo más importante del estudio)
    # --------------------------------------------------------
    total = len(df_f)
    sin_filtros = total == len(df)

    def pct(mascara: pd.Series) -> float:
        return float(mascara.mean() * 100) if total else 0.0

    pct_no_vianda = pct(df_f["come_vianda"].eq("No"))
    pct_carne_pollo = pct(
        df_f["comida_deseada"].str.contains("carne|pollo", case=False, na=False)
    )
    pct_hambre = pct(df_f["hambre_despues"].eq("Sí"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Respondieron",
        f"{total} de {TOTAL_CURSO}" if sin_filtros else f"{total}",
    )
    c2.metric("No come la vianda del colegio", f"{pct_no_vianda:.0f}%")
    c3.metric("Quiere carne o pollo en la vianda", f"{pct_carne_pollo:.0f}%")
    c4.metric("Tiene hambre después del colegio", f"{pct_hambre:.0f}%")

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
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🥩 Alimentación y salud",
            "🍱 La vianda del colegio",
            "🕐 Merienda y rutina diaria",
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

        st.subheader("¿Por qué no come carne / vegetales?")
        razones = pd.concat([
            df_f["razon_no_carne"].dropna(),
            df_f["razon_no_vegetales"].dropna(),
        ])
        if not razones.empty:
            barras(razones, "Razón", "barras_razones_carne_veg", horizontal=True)
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
            razones_vianda = razones_vianda[razones_vianda != ""].str.capitalize()

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
            st.subheader("Cuando come en el colegio, ¿el ambiente le permite comer en tranquilidad?")
            torta(df_f["ambiente_tranquilo"], "torta_ambiente")

        st.subheader("Si no termina de comer, ¿por qué cree que sea?")
        lista_textos(df_f["razon_no_termina"])

    # ---------------- TAB 3 — MERIENDA Y RUTINA DIARIA ----------------
    with tab3:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("¿Sabe en qué momento del día sirven la merienda?")
            barras(df_f["momento_merienda"], "Momento", "barras_momento_merienda")

        with col_b:
            st.subheader("¿Come la merienda apenas la sirven?")
            torta(df_f["come_merienda"], "torta_come_merienda")

        col_c, col_d = st.columns(2)

        with col_c:
            st.subheader("¿La hora de la merienda le ayuda a saber cuánto falta para irse a casa?")
            torta(df_f["merienda_ayuda_hora"], "torta_merienda_hora")

        with col_d:
            st.subheader("¿Tiene hambre después del colegio?")
            torta(df_f["hambre_despues"], "torta_hambre")

        col_e, col_f = st.columns(2)

        with col_e:
            st.subheader("¿Cuántas veces come al día?")
            barras(df_f["cantidad_comidas"], "Veces por día", "barras_cantidad_comidas")

        with col_f:
            st.subheader("¿Cuáles son esas comidas?")
            comidas_dia = (
                df_f["cuales_comidas"]
                .dropna()
                .str.replace(r"\.$", "", regex=True)
                .str.split(r"\s*,\s*|\s+y\s+", regex=True)
                .explode()
                .str.strip()
                .str.capitalize()
            )
            barras(comidas_dia, "Comida", "barras_cuales_comidas")

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
