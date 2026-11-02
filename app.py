# ============================================================
# PARCHE para app.py — pestaña "¿Tiene hambre después del colegio?"
# Tiene 4 pasos. Cada uno dice DÓNDE pegarlo.
# ============================================================


# ------------------------------------------------------------
# PASO 1 — ARREGLO DE EDAD (¡importante!)
# En cargar_datos(), reemplazá estas líneas:
#
#     if "edad" in data.columns:
#         data["edad"] = pd.to_numeric(data["edad"], errors="coerce")
#
# por:
#
#     if "edad" in data.columns:
#         data["edad"] = data["edad"].apply(parsear_edad)
#
# y pegá esta función ARRIBA de cargar_datos():
# ------------------------------------------------------------
EDADES_EN_LETRAS = {"ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12}


def parsear_edad(x):
    """Entiende '9', '10 años', 'Diez', '11 años' -> número."""
    if pd.isna(x):
        return np.nan
    t = str(x).lower()
    m = re.search(r"\d+", t)
    if m:
        return int(m.group())
    for palabra, n in EDADES_EN_LETRAS.items():
        if palabra in t:
            return n
    return np.nan


# ------------------------------------------------------------
# PASO 2 — BORRÁ las funciones grafico_hambre_segun() y
# grafico_cruce_hambre(), y pegá estas dos en su lugar.
# ------------------------------------------------------------
def tabla_perfil_hambre(data: pd.DataFrame) -> pd.DataFrame:
    """Una fila por estudiante (anónima), ordenada por hambre."""
    def termina(x):
        if pd.isna(x):
            return np.nan
        x = str(x).lower()
        if x.startswith("siempre"):
            return "Siempre"
        if x.startswith("a veces"):
            return "A veces"
        return "No sabe"

    t = pd.DataFrame({
        "¿Tiene hambre?": data["hambre_despues"].astype(str).str.rstrip("."),
        "Edad": data["edad"].apply(lambda x: f"{int(x)}" if pd.notna(x) else "—"),
        "Come la vianda": data["come_vianda"],
        "Merienda apenas la sirven": (data["come_merienda"].astype(str)
                                      .str.replace(".,", " /", regex=False)
                                      .str.rstrip(".")),
        "Termina la comida": data["come_todo"].apply(termina),
        "Comidas por día": (data["cantidad_comidas"].astype(str)
                            .str.replace(".,", " /", regex=False)
                            .str.rstrip(".")),
        "Bebe": data["bebida"].astype(str).str.rstrip("."),
    })
    orden = {"Sí": 0, "A veces": 1, "No": 2}
    t = t.sort_values("¿Tiene hambre?", key=lambda s: s.map(orden).fillna(3))
    t.index = [f"Estudiante {i + 1}" for i in range(len(t))]
    return t


def grafico_hambre_conteo(data: pd.DataFrame, columna: str, key: str,
                          orden: list = None) -> None:
    """Barras con CANTIDAD de estudiantes (no %), apiladas por respuesta de hambre."""
    base = data[[columna, "hambre_despues"]].dropna().copy()
    if base.empty:
        st.info("Sin respuestas registradas.")
        return

    base["Grupo"] = base[columna].astype(str).str.strip().str.rstrip(".")
    base["Hambre"] = base["hambre_despues"].astype(str).str.rstrip(".")

    cnt = base.groupby(["Grupo", "Hambre"]).size().reset_index(name="Estudiantes")
    tot = cnt.groupby("Grupo")["Estudiantes"].sum()
    cnt["Etiqueta"] = cnt["Grupo"].map(lambda g: f"{g}  ({tot[g]} en total)")

    if orden:
        grupos = [g for g in orden if g in tot.index] + \
                 [g for g in tot.index if g not in orden]
    else:
        grupos = tot.sort_values(ascending=False).index.tolist()
    etiquetas = dict(zip(cnt["Grupo"], cnt["Etiqueta"]))

    fig = px.bar(
        cnt, x="Estudiantes", y="Etiqueta", color="Hambre",
        orientation="h", text="Estudiantes",
        color_discrete_map={"Sí": "#E91E63", "A veces": "#FF9800", "No": "#4CAF50"},
        category_orders={
            "Etiqueta": [etiquetas[g] for g in grupos],
            "Hambre": ["Sí", "A veces", "No"],
        },
    )
    fig.update_layout(
        barmode="stack",
        xaxis=dict(title="Cantidad de estudiantes", dtick=1),
        yaxis_title=None,
        legend_title_text="¿Tiene hambre?",
        legend=dict(orientation="h", y=1.12),
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True, key=key)


# ------------------------------------------------------------
# PASO 3 — REEMPLAZÁ TODO el bloque "with tab4:" por este.
# (desde "# ---- TAB 4" hasta justo antes de "# ---- TAB 5")
# ------------------------------------------------------------
"""
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

        # ---- 1) Quién es quién ----
        st.subheader("¿Quiénes tienen hambre?")
        st.info(
            "El cuestionario **no pregunta por qué** tienen hambre, así que no "
            "podemos mostrar una razón. Lo que sí podemos hacer es mirar qué "
            "tienen en común quienes dicen que sí o a veces. Con tan pocos "
            "estudiantes, son **pistas para conversar**, no conclusiones."
        )
        perfil = tabla_perfil_hambre(df_f)
        colores = {"Sí": "#F8BBD0", "A veces": "#FFE0B2", "No": "#C8E6C9"}
        estilo = perfil.style.map(
            lambda v: f"background-color: {colores.get(v, '')}",
            subset=["¿Tiene hambre?"],
        )
        st.dataframe(estilo, use_container_width=True)
        st.caption("Cada fila es un estudiante (anónimo), ordenado de más a menos hambre.")

        st.divider()

        # ---- 2) Comparador ----
        st.subheader("Comparar el hambre según…")

        df_h = df_f.copy()
        df_h["edad_txt"] = df_h["edad"].apply(
            lambda x: f"{int(x)} años" if pd.notna(x) else np.nan
        )
        df_h["termina_txt"] = df_h["come_todo"].apply(
            lambda x: np.nan if pd.isna(x)
            else ("Siempre termina" if str(x).startswith("Siempre")
                  else "A veces termina" if str(x).startswith("A veces")
                  else "No sabe")
        )
        df_h["motivo_vianda"] = (
            df_h.apply(motivo_no_vianda, axis=1) if len(df_h) else np.nan
        )

        opciones = {
            "Si come la vianda del colegio": "come_vianda",
            "Por qué no come la vianda (solo quienes no la comen)": "motivo_vianda",
            "Si come la merienda apenas la sirven": "come_merienda",
            "Si termina la comida del colegio": "termina_txt",
            "Cuántas veces come al día": "cantidad_comidas",
            "Edad": "edad_txt",
        }
        eleccion = st.selectbox("Elegí qué comparar", list(opciones))
        grafico_hambre_conteo(df_h, opciones[eleccion], "hambre_comparador")
        st.caption(
            "Cada barra es un grupo; los colores muestran cuántos de ese grupo "
            "tienen hambre. El número entre paréntesis es el tamaño del grupo."
        )
"""
