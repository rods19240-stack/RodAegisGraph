from flask import Flask, render_template, redirect, url_for
from neo4j import GraphDatabase
import folium
import random
import os

app = Flask(__name__)

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# 🏠 HOME
@app.route("/")
def home():
    with driver.session(database="fraud") as session:
        result = session.run("""
        MATCH (c:Cliente)
        RETURN c.nombre AS nombre, c.riesgo AS riesgo, c.sospechoso AS sospechoso
        ORDER BY c.riesgo DESC
        """)
        clientes = [dict(r) for r in result]
        print("SI ESTA CARGANDO EL NUEVO CODIGO")

    return render_template("index.html", clientes=clientes)


# 🔘 DETECTAR FRAUDE
@app.route("/detectar")
def detectar():
    with driver.session(database="fraud") as session:

        # 🔄 Reiniciar
        session.run("""
        MATCH (c:Cliente)
        SET c.riesgo = 0.1
        REMOVE c.sospechoso
        """)

        # 🔥 Dispositivo compartido
        session.run("""
        MATCH (c1:Cliente)-[:USA]->(d:Dispositivo)<-[:USA]-(c2:Cliente)
        WHERE c1 <> c2
        SET c1.riesgo = c1.riesgo + 0.5,
            c2.riesgo = c2.riesgo + 0.5
        """)

        # 🌍 Ubicaciones múltiples
        session.run("""
        MATCH (c:Cliente)-[:USA]->(d:Dispositivo)-[:UBICADO_EN]->(u:Ubicacion)
        WITH c, collect(u.pais) AS paises
        WHERE size(paises) > 1
        SET c.riesgo = c.riesgo + 0.7
        """)

        # 🔴 Marcar sospechosos
        session.run("""
        MATCH (c:Cliente)
        WHERE c.riesgo > 0.5
        SET c.sospechoso = true
        """)

    return redirect(url_for("home"))


# 🔄 REINICIAR
@app.route("/reiniciar")
def reiniciar():
    with driver.session(database="fraud") as session:
        session.run("""
        MATCH (c:Cliente)
        SET c.riesgo = 0.1
        REMOVE c.sospechoso
        """)
    return redirect(url_for("home"))


# 🌍 MAPA
@app.route("/mapa")
def mapa():
    with driver.session(database="fraud") as session:
        result = session.run("""
        MATCH (c:Cliente)-[:USA]->(d:Dispositivo)-[:UBICADO_EN]->(u:Ubicacion)
        RETURN c.nombre AS nombre, u.ciudad AS ciudad, u.lat AS lat, u.lon AS lon
        """)

        mapa = folium.Map(location=[20, 0], zoom_start=2)

        for r in result:
            if r["lat"] and r["lon"]:
                folium.Marker(
                    location=[r["lat"], r["lon"]],
                    popup=f"{r['nombre']} - {r['ciudad']}"
                ).add_to(mapa)

        ruta = "templates/mapa.html"
        mapa.save(ruta)

        # 🔘 Botón volver
        with open(ruta, "a", encoding="utf-8") as f:
            f.write("""
            <div style="position: fixed; bottom: 20px; left: 20px; z-index:9999;">
                <a href="/">
                    <button style="padding:10px; font-size:16px;">⬅ Volver</button>
                </a>
            </div>
            """)

    return render_template("mapa.html")

@app.route("/simular")
def simular():
    with driver.session(database="fraud") as session:

        monto = random.randint(30000, 100000)  # 💥 más alto = más sospechoso

        # 💸 Crear transacción
        session.run(f"""
        MATCH (c1:Cuenta {{id:101}})
        MATCH (c2:Cuenta {{id:102}})
        CREATE (t:Transaccion {{monto:{monto}}})
        CREATE (c1)-[:ENVIA]->(t)
        CREATE (t)-[:A]->(c2)
        """)

        # 🔄 Reiniciar riesgo
        session.run("""
        MATCH (c:Cliente)
        SET c.riesgo = 0.1
        REMOVE c.sospechoso
        """)

        # 🔥 Dispositivo compartido
        session.run("""
        MATCH (c1:Cliente)-[:USA]->(d:Dispositivo)<-[:USA]-(c2:Cliente)
        WHERE c1 <> c2
        SET c1.riesgo = c1.riesgo + 0.5,
            c2.riesgo = c2.riesgo + 0.5
        """)

        # 🌍 Ubicaciones múltiples
        session.run("""
        MATCH (c:Cliente)-[:USA]->(d:Dispositivo)-[:UBICADO_EN]->(u:Ubicacion)
        WITH c, collect(u.pais) AS paises
        WHERE size(paises) > 1
        SET c.riesgo = c.riesgo + 0.7
        """)

        # 💸 NUEVO: riesgo por monto alto
        session.run("""
        MATCH (c:Cliente)-[:TIENE]->(cu:Cuenta)-[:ENVIA]->(t:Transaccion)
        WHERE t.monto > 10000
        SET c.riesgo = c.riesgo + 0.4
        """)

        # 🔴 Marcar sospechosos
        session.run("""
        MATCH (c:Cliente)
        WHERE c.riesgo > 0.5
        SET c.sospechoso = true
        """)

    return redirect(url_for("home"))

# 🚀 RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)