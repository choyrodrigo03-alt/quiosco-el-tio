import streamlit as st
import pandas as pd

st.set_page_config(page_title="QUIOSCO EL TÍO", layout="wide")

@st.cache_data(ttl=10)
def cargar_inventario_local():
    try:
        # Asegúrate de usar el nombre correcto de tu archivo
        excel_file = pd.read_excel("inventario.xlsx", sheet_name=None)
        
        dfs = []
        for nombre_hoja, df_hoja in excel_file.items():
            # Normalizar nombres de columnas (quita espacios y convierte a mayúsculas)
            df_hoja.columns = df_hoja.columns.astype(str).str.strip().str.upper()
            
            # Reemplazar espacios por guiones bajos para soportar "PRECIO VENTA" o "PRECIO_VENTA"
            df_hoja.columns = df_hoja.columns.str.replace(" ", "_")
            
            if "PRODUCTO" in df_hoja.columns:
                dfs.append(df_hoja)
                
        if not dfs:
            st.error("No se encontraron hojas con la columna 'PRODUCTO' en el archivo Excel.")
            return pd.DataFrame()

        df = pd.concat(dfs, ignore_index=True)

        # Manejo de la columna CODIGO
        if "CODIGO" in df.columns:
            df["CODIGO"] = df["CODIGO"].fillna("").astype(str).str.strip()
        else:
            df["CODIGO"] = ""

        # Manejo de la columna PRODUCTO
        if "PRODUCTO" in df.columns:
            df["PRODUCTO"] = df["PRODUCTO"].fillna("").astype(str).str.strip()
            df = df[df["PRODUCTO"] != ""]
        else:
            df["PRODUCTO"] = "Sin Nombre"

        # Manejo y limpieza avanzada de la columna PRECIO_VENTA
        if "PRECIO_VENTA" in df.columns:
            precios_limpios = (
                df["PRECIO_VENTA"]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(" ", "", regex=False)
                .str.replace(".", "", regex=False)  # Elimina puntos de miles
                .str.replace(",", ".", regex=False) # Convierte comas decimales a puntos
                .str.strip()
            )
            df["PRECIO_VENTA"] = pd.to_numeric(precios_limpios, errors="coerce").fillna(0.0)
        else:
            df["PRECIO_VENTA"] = 0.0

        return df

    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        return pd.DataFrame()


inventario = cargar_inventario_local()

if "carrito" not in st.session_state:
    st.session_state.carrito = []

st.title("🛒 QUIOSCO EL TÍO")

col_izq, col_der = st.columns([1, 1])

with col_izq:
    st.header("Buscar Producto")
    busqueda = st.text_input("Escribe el nombre o código:", key="input_busqueda")
    
    if not inventario.empty:
        if busqueda:
            filtro = inventario[
                inventario["CODIGO"].str.lower().str.contains(busqueda.lower()) |
                inventario["PRODUCTO"].str.lower().str.contains(busqueda.lower())
            ]
        else:
            filtro = inventario

        st.caption(f"Mostrando {len(filtro)} productos")

        for i, fila in filtro.head(30).iterrows():
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"**{fila['PRODUCTO']}**")
            c2.write(f"${fila['PRECIO_VENTA']:g}")
            if c3.button("Agregar", key=f"btn_{i}_{fila['CODIGO']}"):
                encontrado = False
                for item in st.session_state.carrito:
                    if item["producto"] == fila["PRODUCTO"]:
                        item["cantidad"] += 1
                        encontrado = True
                        break
                if not encontrado:
                    st.session_state.carrito.append({
                        "codigo": fila["CODIGO"],
                        "producto": fila["PRODUCTO"],
                        "precio": fila["PRECIO_VENTA"],
                        "cantidad": 1
                    })
                st.rerun()

with col_der:
    st.header("Venta Actual")
    
    if st.session_state.carrito:
        total = 0.0
        for i, item in enumerate(st.session_state.carrito):
            subtotal = item["precio"] * item["cantidad"]
            total += subtotal
            
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.write(f"{item['producto']}")
            c2.write(f"x{item['cantidad']}")
            c3.write(f"${subtotal:g}")
            
            if c4.button("❌", key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()
                
        st.markdown(f"## **TOTAL: ${total:g}**")
        
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("Vaciar / Nueva Venta", type="secondary"):
            st.session_state.carrito = []
            st.rerun()
            
        if c_btn2.button("Cobrar", type="primary"):
            st.success(f"¡Venta realizada por ${total:g}!")
            st.session_state.carrito = []
    else:
        st.info("El carrito está vacío.")
