from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "123456789"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def probar_conexion():
    with driver.session(database="fraud") as session:
        result = session.run("RETURN 'Conexion exitosa Rod 😎' AS mensaje")
        for r in result:
            print(r["mensaje"])

def insertar_datos():
    with driver.session(database="fraud") as session:
        session.run("""
        // CLIENTES
        MERGE (c1:Cliente {nombre:"Juan"})
        ON CREATE SET c1.riesgo = 0.1

        MERGE (c2:Cliente {nombre:"Ana"})
        ON CREATE SET c2.riesgo = 0.2

        MERGE (c3:Cliente {nombre:"Luis"})
        ON CREATE SET c3.riesgo = 0.9

        // CUENTAS
        MERGE (cu1:Cuenta {id:101})
        MERGE (cu2:Cuenta {id:102})
        MERGE (cu3:Cuenta {id:103})

        MERGE (c1)-[:TIENE]->(cu1)
        MERGE (c2)-[:TIENE]->(cu2)
        MERGE (c3)-[:TIENE]->(cu3)

        // DISPOSITIVOS
        MERGE (d1:Dispositivo {ip:"192.168.1.1"})
        MERGE (d2:Dispositivo {ip:"192.168.1.1"})

        MERGE (c1)-[:USA]->(d1)
        MERGE (c2)-[:USA]->(d2)

        // UBICACIONES 🌍
        MERGE (u1:Ubicacion {ciudad:"CDMX", pais:"Mexico", lat:19.4326, lon:-99.1332})
        MERGE (u2:Ubicacion {ciudad:"Moscu", pais:"Rusia", lat:55.7558, lon:37.6173})

        MERGE (d1)-[:UBICADO_EN]->(u1)
        MERGE (d2)-[:UBICADO_EN]->(u2)

        // TRANSACCIONES
        MERGE (t1:Transaccion {id:1})
        ON CREATE SET t1.monto = 10000

        MERGE (t2:Transaccion {id:2})
        ON CREATE SET t2.monto = 12000

        MERGE (cu1)-[:ENVIA]->(t1)
        MERGE (t1)-[:A]->(cu2)

        MERGE (cu2)-[:ENVIA]->(t2)
        MERGE (t2)-[:A]->(cu3)
        """)

def reiniciar_riesgo():
    with driver.session(database="fraud") as session:
        session.run("""
        MATCH (c:Cliente)
        SET c.riesgo = 0.1
        REMOVE c.sospechoso
        """)

def detectar_fraude():
    with driver.session(database="fraud") as session:
        session.run("""
        MATCH (c1:Cliente)-[:USA]->(d:Dispositivo)<-[:USA]-(c2:Cliente)
        WHERE c1 <> c2
        SET c1.riesgo = c1.riesgo + 0.5,
            c2.riesgo = c2.riesgo + 0.5
        """)

def detectar_ubicaciones_sospechosas():
    with driver.session(database="fraud") as session:
        session.run("""
        MATCH (c:Cliente)-[:USA]->(d:Dispositivo)-[:UBICADO_EN]->(u:Ubicacion)
        WITH c, collect(u.pais) AS paises
        WHERE size(paises) > 1
        SET c.riesgo = c.riesgo + 0.7
        """)

def detectar_ciclos():
    with driver.session(database="fraud") as session:
        result = session.run("""
        MATCH path = (c:Cuenta)-[:ENVIA*2..5]->(c)
        RETURN path
        """)

        print("\n💸 Posible lavado de dinero (ciclos):\n")
        for _ in result:
            print("Ciclo detectado")

def mostrar_sospechosos():
    with driver.session(database="fraud") as session:
        result = session.run("""
        MATCH (c:Cliente)
        WHERE c.riesgo > 0.5
        RETURN c.nombre AS nombre, c.riesgo AS riesgo
        """)

        print("\n⚠️ Clientes sospechosos:\n")
        for r in result:
            print(f"{r['nombre']} → riesgo: {r['riesgo']}")

def marcar_sospechosos():
    with driver.session(database="fraud") as session:
        session.run("""
        MATCH (c:Cliente)
        WHERE c.riesgo > 0.5
        SET c.sospechoso = true
        """)

# 🔥 MAIN FINAL PRO
if __name__ == "__main__":
    probar_conexion()
    insertar_datos()
    reiniciar_riesgo()
    detectar_fraude()
    detectar_ubicaciones_sospechosas()  # 👈 NUEVO NIVEL PRO
    detectar_ciclos()
    mostrar_sospechosos()
    marcar_sospechosos()
    driver.close()