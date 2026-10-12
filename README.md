# 🍎 Alimentación y Rutina de Niños

Aplicación interactiva desarrollada con *Streamlit, **Pandas, **NumPy* y *Plotly* 
para explorar los datos del Cuestionario de Viandas y Rutina respondido por estudiantes 
de 4to grado.

## 📊 ¿Qué muestra?

- *Alimentación*: consumo de carne y vegetales, razones de rechazo, alergias declaradas.
- *Bebidas y comidas*: qué beben, qué les gustaría comer, si comen la vianda.
- *Rutina*: horarios de comida, cantidad de comidas al día, hambre después de la escuela.
- *Datos crudos*: tabla completa con filtros y descarga en CSV.

## 🛠️ Tecnologías

| Librería | Uso |
|---|---|
| Streamlit | Interfaz web interactiva |
| Pandas | Carga y limpieza de datos |
| NumPy | Operaciones numéricas |
| Plotly | Gráficos interactivos |

## 🚀 Ejecución local

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU-USUARIO/proyecto-viandas.git
cd proyecto-viandas

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Mac/Linux

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
streamlit run app.py
