import streamlit as st
import pandas as pd

st.set_page_config(page_title="QUIOSCO EL TÍO", layout="wide")

SHEET_ID = "1XsqX-ChVzkSkKni8zg54zo6dA7JnxCy6aYN6DeZIZM"

@st.cache_data(ttl=5)
def cargar_inventario(sheet_id):
    # Probar lectura de la exportación global
    url_base = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    # Intentar cargar pestañas conocidas
    pestañas = ["Comestibles", "Gaseosas_Aguas", "Cervezas_Vinos", "Golosinas", "Limpieza"]
    dfs = []
    
    for p in pestañas:
        try:
            url_pestaña = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={p}"
            df_temp = pd.read_csv(url_pestaña)
            df_temp.columns = df_temp.columns.astype(str).str.strip().str.upper()
            if "PRODUCTO" in df_temp.columns:
                dfs.append(df_temp)
        except Exception:
            continue
            
    # Si la lectura individual falla por los nombres, descargar la vista general
    if not dfs:
        try:
            df_gen = pd.read_csv(url_base)
            df_gen.columns = df_gen.columns.astype(str).str.strip().str.upper()
            if "PRODUCTO" in df_gen.columns:
                dfs.append(df_gen)
        except Exception as e:
            st.error(f"Error accediendo a la planilla: {e}")
            return pd.DataFrame()

    if not dfs:
        st.error("No se detectaron datos válidos en la planilla.")
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    if "CODIGO" in df.columns:
        df["CODIGO"] = df["CODIGO"].fillna("").astype(str).str.strip()
    else:
        df["CODIGO"] = ""

    if "PRODUCTO" in df.columns:
        df["PRODUCTO"] = df["PRODUCTO"].fillna("").astype(str).str.strip()
        df = df[df["PRODUCTO"] != ""]
    else:
        df["PRODUCTO"] = "Sin Nombre"

    if "PRECIO_VENTA" in df.columns:
        df["PRECIO_VENTA"] = pd.to_numeric(
            df["PRECIO_VENTA"].astype(str).str.replace("$", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
            errors="coerce"
        ).fillna(0)
    else:
        df["PRECIO_VENTA"] = 0.0

    return df

inventario = cargar_inventario(SHEET_ID)

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
            c2.write(f"${fila['PRECIO_VENTA']:,.2f}")
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
            c3.write(f"${subtotal:,.2f}")
            
            if c4.button("❌", key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()
                
        st.markdown(f"## **TOTAL: ${total:,.2f}**")
        
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("Vaciar / Nueva Venta", type="secondary"):
            st.session_state.carrito = []
            st.rerun()
            
        if c_btn2.button("Cobrar", type="primary"):
            st.success(f"¡Venta realizada por ${total:,.2f}!")
            st.session_state.carrito = []
    else:
        st.info("El carrito está vacío.")
