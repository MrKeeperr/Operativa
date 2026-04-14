"""
Flask Application for Operativa Exercises
"""

from flask import Flask, render_template, jsonify
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

app = Flask(__name__)


@app.route("/")
def index():
    """Main page with links to all exercises"""
    exercises = [
        {
            "name": "Biblioteca Universitaria",
            "description": "Minimización de bibliotecarios con turnos de 8 horas",
            "url": "/biblioteca",
            "taller": "Taller 1",
        },
        {
            "name": "Problema Dual",
            "description": "Análisis del problema dual",
            "url": "/dual",
            "taller": "Taller 1",
        },
        {
            "name": "Farmatodo",
            "description": "Problema de optimización Farmatodo",
            "url": "/farmatodo",
            "taller": "Taller 2",
        },
        {
            "name": "Problema de la Mochila",
            "description": "Problema de la mochila (Knapsack)",
            "url": "/mochila",
            "taller": "Taller 2",
        },
    ]
    return render_template("index.html", exercises=exercises)


@app.route("/biblioteca")
def biblioteca():
    """Biblioteca optimization problem"""
    return render_template("biblioteca.html")


@app.route("/biblioteca/solve", methods=["POST"])
def biblioteca_solve():
    """Solve the biblioteca optimization problem"""
    from scipy.optimize import linprog

    # Problem configuration
    c = [1, 1, 1, 1, 1, 1]

    A = [
        [-1, 0, 0, 0, 0, -1],
        [-1, -1, 0, 0, 0, 0],
        [0, -1, -1, 0, 0, 0],
        [0, 0, -1, -1, 0, 0],
        [0, 0, 0, -1, -1, 0],
        [0, 0, 0, 0, -1, -1],
    ]

    b = [-3, -2, -10, -14, -8, -10]
    bounds = [(0, None) for _ in range(6)]

    # Solve
    result = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")

    if not result.success:
        return jsonify({"success": False, "error": "No se encontró solución óptima"})

    x_optimo = result.x

    # Shift names
    turnos = [
        "12:00 AM (medianoche)",
        "4:00 AM",
        "8:00 AM",
        "12:00 PM (mediodía)",
        "4:00 PM",
        "8:00 PM",
    ]

    # Distribution data
    distribucion = []
    for i, (turno, val) in enumerate(zip(turnos, x_optimo)):
        distribucion.append({"turno": turno, "bibliotecarios": int(val)})

    total = int(sum(x_optimo))

    # Constraint verification
    periodos = [
        "12:00 AM - 3:59 AM",
        "4:00 AM - 7:59 AM",
        "8:00 AM - 11:59 AM",
        "12:00 PM - 3:59 PM",
        "4:00 PM - 7:59 PM",
        "8:00 PM - 11:59 PM",
    ]
    demandas = [3, 2, 10, 14, 8, 10]

    coberturas = [
        x_optimo[0] + x_optimo[5],
        x_optimo[0] + x_optimo[1],
        x_optimo[1] + x_optimo[2],
        x_optimo[2] + x_optimo[3],
        x_optimo[3] + x_optimo[4],
        x_optimo[4] + x_optimo[5],
    ]

    verificacion = []
    for periodo, demanda, cobertura in zip(periodos, demandas, coberturas):
        verificacion.append(
            {
                "periodo": periodo,
                "cobertura": int(cobertura),
                "demanda": demanda,
                "cumple": cobertura >= demanda,
            }
        )

    # Generate charts with Plotly
    charts = generate_biblioteca_charts(x_optimo, demandas, coberturas)

    return jsonify(
        {
            "success": True,
            "distribucion": distribucion,
            "total": total,
            "verificacion": verificacion,
            "charts": charts,
        }
    )


def generate_biblioteca_charts(x_optimo, demandas, coberturas):
    """Generate charts as Plotly JSON"""

    # Chart 1: Distribution of librarians per shift
    turnos = ["12AM", "4AM", "8AM", "12PM", "4PM", "8PM"]
    valores = [int(v) for v in x_optimo]
    colores = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]

    fig1 = go.Figure(
        data=[
            go.Bar(
                x=turnos,
                y=valores,
                marker_color=colores,
                text=valores,
                textposition="outside",
                textfont=dict(size=14, color="black"),
            )
        ]
    )

    fig1.update_layout(
        title=dict(
            text="Distribución Óptima de Bibliotecarios",
            font=dict(size=18, color="#2c3e50"),
            x=0.5,
        ),
        xaxis_title="Hora de inicio del turno",
        yaxis_title="Número de bibliotecarios",
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(gridcolor="#e0e0e0", gridwidth=1),
        margin=dict(t=60, b=60, l=60, r=40),
    )

    # Chart 2: Demand vs Coverage
    periodos = ["0-4h", "4-8h", "8-12h", "12-16h", "16-20h", "20-24h"]
    coberturas_int = [int(c) for c in coberturas]

    fig2 = go.Figure()

    fig2.add_trace(
        go.Bar(
            name="Demanda",
            x=periodos,
            y=demandas,
            marker_color="#e74c3c",
            opacity=0.8,
            text=demandas,
            textposition="outside",
        )
    )

    fig2.add_trace(
        go.Bar(
            name="Cobertura",
            x=periodos,
            y=coberturas_int,
            marker_color="#2ecc71",
            opacity=0.8,
            text=coberturas_int,
            textposition="outside",
        )
    )

    fig2.update_layout(
        title=dict(
            text="Demanda vs Cobertura por Período",
            font=dict(size=18, color="#2c3e50"),
            x=0.5,
        ),
        xaxis_title="Período de 4 horas",
        yaxis_title="Número de bibliotecarios",
        barmode="group",
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(gridcolor="#e0e0e0", gridwidth=1),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(t=80, b=60, l=60, r=40),
    )

    return {
        "distribution": json.loads(fig1.to_json()),
        "comparison": json.loads(fig2.to_json()),
    }


if __name__ == "__main__":
    app.run(debug=True)
