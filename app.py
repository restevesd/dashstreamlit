import streamlit as st
import pandas as pd
import matplotli.pyplot as plt
import seaborn as sns

# ---------------------------------
# CONFIGURACIÓN
# ---------------------------------
st.set_page_config(page_title="Tablero LigaPro", layout="wide")
st.markdown("<h1 style='text-align: center;'>📊 Tablero Analítico - LigaPro Ecuador (2020)</h1>", unsafe_allow_html=True)

# ---------------------------------
# CARGA DE DATOS (MISMA RUTA QUE app.py)
# ---------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("ligapro2020.csv", sep=";")

df = load_data()

# ---------------------------------
# TIPOS NUMÉRICOS
# ---------------------------------
for c in ["edadjugador", "pesojugador", "alturajugador"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# ---------------------------------
# FILTROS SOLICITADOS
# - eliminar rol DT
# - eliminar jugadores con altura < 80 cm
# ---------------------------------
if "roljugador" in df.columns:
    df["roljugador"] = df["roljugador"].astype(str).str.strip()
    df = df[df["roljugador"].str.upper() != "DT"]

if "alturajugador" in df.columns:
    df = df[df["alturajugador"].notna() & (df["alturajugador"] >= 80)]

# ---------------------------------
# IMC (calcularlo)
# IMC = peso(kg) / (altura(m))^2
# altura en cm -> m = cm/100
# ---------------------------------
if {"pesojugador", "alturajugador"}.issubset(df.columns):
    df["imc"] = df["pesojugador"] / ((df["alturajugador"] / 100) ** 2)

# Helpers
def es_nacional(pais: str) -> bool:
    if pd.isna(pais):
        return False
    p = str(pais).strip().lower()
    return p in ["ecuador", "ecuatoriano", "ecuatoriana", "ecu"]

# =========================================================
# FILA KPIs: k1–k4
# =========================================================
st.markdown("### 🧭 Indicadores (KPIs)")

k1, k2, k3, k4 = st.columns(4)

# k1-k3: edades
if "edadjugador" in df.columns:
    edades = df["edadjugador"].dropna()
    edad_prom = float(edades.mean()) if len(edades) else None
    edad_min = float(edades.min()) if len(edades) else None
    edad_max = float(edades.max()) if len(edades) else None
else:
    edad_prom = edad_min = edad_max = None

with k1:
    st.metric("k1 • Edad promedio", "—" if edad_prom is None else f"{edad_prom:.1f} años")

with k2:
    st.metric("k2 • Edad mínima", "—" if edad_min is None else f"{edad_min:.0f} años")

with k3:
    st.metric("k3 • Edad máxima", "—" if edad_max is None else f"{edad_max:.0f} años")

# k4: IMC promedio por rol y rol con IMC más alto
with k4:
    if {"imc", "roljugador"}.issubset(df.columns):
        imc_por_rol = df.dropna(subset=["imc", "roljugador"]).groupby("roljugador")["imc"].mean()
        if len(imc_por_rol):
            rol_top = imc_por_rol.idxmax()
            imc_top = float(imc_por_rol.max())
            st.metric("k4 • Rol con IMC promedio más alto", f"{rol_top}", f"{imc_top:.2f}")
        else:
            st.metric("k4 • Rol con IMC promedio más alto", "—")
    else:
        st.metric("k4 • Rol con IMC promedio más alto", "—")

st.markdown("---")

# =========================================================
# FILA 1: (1) Barras por equipo | (2) Histograma edades
# =========================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ Jugadores por Equipo (Mayor → Menor)")
    if "nombreequipo" in df.columns:
        conteo = df["nombreequipo"].value_counts().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(conteo.index, conteo.values)
        ax.set_xlabel("Equipo")
        ax.set_ylabel("Cantidad")
        ax.set_title("Cantidad de Jugadores por Equipo")
        plt.xticks(rotation=90)
        st.pyplot(fig)
    else:
        st.error("Falta columna: 'nombreequipo'.")

with col2:
    st.subheader("2️⃣ Distribución de Edades (Histograma + Densidad)")
    if "edadjugador" in df.columns:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.histplot(df["edadjugador"].dropna(), bins=15, kde=True, ax=ax)
        ax.set_xlabel("Edad")
        ax.set_ylabel("Frecuencia")
        ax.set_title("Edades de Jugadores (con densidad)")
        st.pyplot(fig)
    else:
        st.error("Falta columna: 'edadjugador'.")

# =========================================================
# FILA 2: (3) Boxplot alturas por rol | (4) Scatter peso vs altura
# =========================================================
col3, col4 = st.columns(2)

with col3:
    st.subheader("3️⃣ Boxplot - Alturas por Rol")
    needed = {"alturajugador", "roljugador"}
    if needed.issubset(df.columns):
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.boxplot(
            data=df.dropna(subset=["alturajugador", "roljugador"]),
            x="roljugador",
            y="alturajugador",
            ax=ax
        )
        ax.set_xlabel("Rol")
        ax.set_ylabel("Altura (cm)")
        ax.set_title("Distribución de Alturas por Rol")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.error("Faltan columnas: 'alturajugador' y/o 'roljugador'.")

with col4:
    st.subheader("4️⃣ Scatter - Peso vs Altura (Color=Rol, Tamaño=Edad)")
    needed = {"pesojugador", "alturajugador", "roljugador", "edadjugador"}
    if needed.issubset(df.columns):
        d = df.dropna(subset=["pesojugador", "alturajugador", "roljugador", "edadjugador"]).copy()

        edad = d["edadjugador"]
        size = 30 + (edad - edad.min()) / (edad.max() - edad.min() + 1e-9) * 170
        d["_size"] = size

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.scatterplot(
            data=d,
            x="pesojugador",
            y="alturajugador",
            hue="roljugador",
            size="_size",
            sizes=(30, 200),
            alpha=0.7,
            ax=ax
        )
        ax.set_xlabel("Peso (kg)")
        ax.set_ylabel("Altura (cm)")
        ax.set_title("Relación Peso vs Altura (Rol y Edad)")
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0)
        st.pyplot(fig)
    else:
        st.error("Faltan columnas: 'pesojugador', 'alturajugador', 'roljugador', 'edadjugador'.")

# =========================================================
# FILA 3: (5) Barras apiladas nacionales vs extranjeros | (6) Boxplot IMC por rol
# =========================================================
col5, col6 = st.columns(2)

with col5:
    st.subheader("5️⃣ Plantillas: Nacionales vs Extranjeros (por Equipo)")
    needed = {"nombreequipo", "paisjugador"}
    if needed.issubset(df.columns):
        d = df.dropna(subset=["nombreequipo", "paisjugador"]).copy()
        d["tipo"] = d["paisjugador"].apply(lambda x: "Nacional" if es_nacional(x) else "Extranjero")

        pivot = (
            d.pivot_table(index="nombreequipo", columns="tipo", values="idJugador", aggfunc="count", fill_value=0)
            .sort_values(by=["Nacional", "Extranjero"], ascending=False)
        )

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(pivot.index, pivot.get("Nacional", 0), label="Nacional")
        ax.bar(pivot.index, pivot.get("Extranjero", 0), bottom=pivot.get("Nacional", 0), label="Extranjero")

        ax.set_xlabel("Equipo")
        ax.set_ylabel("Cantidad de jugadores")
        ax.set_title("Composición de Plantillas por Equipo")
        plt.xticks(rotation=90)
        ax.legend()
        st.pyplot(fig)
    else:
        st.error("Faltan columnas: 'nombreequipo' y/o 'paisjugador'.")

with col6:
    st.subheader("6️⃣ Distribución de IMC por Rol (Boxplot)")
    needed = {"imc", "roljugador"}
    if needed.issubset(df.columns):
        d = df.dropna(subset=["imc", "roljugador"]).copy()
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.boxplot(data=d, x="roljugador", y="imc", ax=ax)
        ax.set_xlabel("Rol")
        ax.set_ylabel("IMC")
        ax.set_title("IMC por Rol")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.error("Faltan columnas: 'imc' y/o 'roljugador'.")

# =========================================================
# FILA 4: (7) Pie top 5 nacionalidades | (8) Heatmap correlación
# =========================================================
col7, col8 = st.columns(2)

with col7:
    st.subheader("7️⃣ Top 5 Nacionalidades (Torta)")
    if "paisjugador" in df.columns:
        paises = df["paisjugador"].dropna().astype(str).str.strip()
        vc = paises.value_counts()

        top5 = vc.head(5)
        otros = vc.iloc[5:].sum()
        pie_series = top5.copy()
        pie_series["Otros"] = otros

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.pie(pie_series.values, labels=pie_series.index, autopct="%1.1f%%", startangle=90)
        ax.set_title("Proporción de Nacionalidades (Top 5 + Otros)")
        st.pyplot(fig)
    else:
        st.error("Falta columna: 'paisjugador'.")

with col8:
    st.subheader("8️⃣ Matriz de Correlación (Heatmap)")
    needed = {"edadjugador", "pesojugador", "alturajugador", "imc"}
    if needed.issubset(df.columns):
        corr_df = df[list(needed)].dropna().copy()
        corr = corr_df.corr(numeric_only=True)

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(corr, annot=True, fmt=".2f", ax=ax)
        ax.set_title("Correlación entre Variables Numéricas")
        st.pyplot(fig)
    else:
        st.error("Faltan columnas numéricas: edadjugador, pesojugador, alturajugador e imc.")
