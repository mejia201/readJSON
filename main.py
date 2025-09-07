import json
import pandas as pd
import streamlit as st
import io

st.set_page_config(page_title="Procesador de DTE JSON", page_icon="📄")

def cargar_json_con_codificacion_contenido(contenido):
    try:
        return json.loads(contenido.decode('utf-8-sig'))
    except UnicodeDecodeError:
        try:
            return json.loads(contenido.decode('latin-1'))
        except Exception as e:
            st.error(f"❌ No se pudo leer JSON: {e}")
            return None
    except json.JSONDecodeError as e:
        st.error(f"❌ Error JSON: {e}")
        return None

st.title("📄 Procesador de JSON a Excel")
st.write("Sube uno o varios archivos JSON de DTE para procesarlos y exportar a Excel.")

archivos = st.file_uploader(
    "Selecciona los archivos JSON",
    type=["json"],
    accept_multiple_files=True
)

if archivos:
    filas = []
    st.info(f"📝 Procesando {len(archivos)} archivos JSON...")

    for archivo in archivos:
        if archivo.size == 0:
            st.warning(f"⚠️ Archivo vacío: {archivo.name}")
            continue

        data = cargar_json_con_codificacion_contenido(archivo.read())
        if not data:
            continue

        # Procesar datos del JSON válido
        fecha = data["identificacion"]["fecEmi"]
        if "-" in fecha:
            y, m, d = fecha.split("-")
            fecha = f"{d}/{m}/{y}"

        # numero_control = data["identificacion"]["numeroControl"]
        # dte_num = numero_control.split("-")[-1].lstrip("0")

        numero_control = data["identificacion"]["numeroControl"]

        # Tomar el último bloque después del último guion
        ultimo_bloque = numero_control.split("-")[-1]
        dte_num = str(int(ultimo_bloque[-7:]))


        nrc = data["emisor"]["nrc"]
        nombre_empresa = data["emisor"]["nombre"]
        subtotal = data["resumen"]["totalGravada"]

        iva = 0.00
        for tributo in data["resumen"].get("tributos", []):
            if tributo.get("codigo") in ["20", "IVA", "001"]:
                iva = tributo["valor"]
                break

        # total = data["resumen"]["totalPagar"]

        total = data.get("resumen", {}).get("totalPagar") \
            or data.get("resumen", {}).get("montoTotalOperacion", 0.00)

        fila = [
            fecha,
            1,
            "03",
            dte_num,
            nrc,
            nombre_empresa,
            0.00, 0.00, 0.00,
            subtotal,
            0.00, 0.00, 0.00,
            iva,
            total,
            "",
            1, 1, 2, 1, 3
        ]
        filas.append(fila)
        st.success(f"✅ Procesado: {archivo.name}")

    if filas:
        columnas = [
            "Fecha", "Fijo1", "Fijo2", "DTE", "NRC", "Nombre", "0_1", "0_2", "0_3",
            "Subtotal", "0_4", "0_5", "0_6", "IVA", "Total", "Vacio",
            "F1", "F2", "F3", "F4", "F5"
        ]
        df = pd.DataFrame(filas, columns=columnas)

        # Convertir a datetime y ordenar
        df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y")
        df = df.sort_values(by="Fecha")

        # Volver a mostrarla en formato dd/mm/yyyy:
        df["Fecha"] = df["Fecha"].dt.strftime("%d/%m/%Y")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)

        st.download_button(
            label="📥 Descargar Excel",
            data=buffer.getvalue(),
            file_name="DTEs_procesados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ No se procesaron archivos JSON válidos.")
