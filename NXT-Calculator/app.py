from flask import Flask, render_template, request, jsonify
import ast
import math
import operator

app = Flask(__name__)

# -----------------------------
# Safe scientific expression engine
# -----------------------------
BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

FUNCTIONS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sqrt": math.sqrt, "log": math.log10, "ln": math.log,
    "abs": abs, "exp": math.exp, "floor": math.floor, "ceil": math.ceil,
    "radians": math.radians, "degrees": math.degrees,
    "factorial": math.factorial,
}
CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}

def safe_eval(expression):
    expression = expression.replace("^", "**").strip()
    if len(expression) > 200:
        raise ValueError("Expression is too long.")
    tree = ast.parse(expression, mode="eval")

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name) and node.id in CONSTANTS:
            return CONSTANTS[node.id]
        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
            return UNARY_OPS[type(node.op)](walk(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
            return BIN_OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id not in FUNCTIONS or node.keywords:
                raise ValueError("Function not allowed.")
            args = [walk(a) for a in node.args]
            return FUNCTIONS[node.func.id](*args)
        raise ValueError("Unsupported expression.")

    result = walk(tree)
    if not math.isfinite(result):
        raise ValueError("Result is not finite.")
    return result

def clean(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return round(value, 10) if isinstance(value, float) else value

# -----------------------------
# Engineering calculation engine
# -----------------------------
def engineering_calc(calc, d):
    n = lambda key: float(d[key])

    if calc == "ohm":
        # Any two of V, I, R -> calculate the third
        if d.get("voltage") not in ("", None) and d.get("current") not in ("", None):
            v, i = n("voltage"), n("current")
            return {"formula": "R = V / I", "answer": clean(v/i), "unit": "Ω"}
        if d.get("voltage") not in ("", None) and d.get("resistance") not in ("", None):
            v, r = n("voltage"), n("resistance")
            return {"formula": "I = V / R", "answer": clean(v/r), "unit": "A"}
        if d.get("current") not in ("", None) and d.get("resistance") not in ("", None):
            i, r = n("current"), n("resistance")
            return {"formula": "V = I × R", "answer": clean(i*r), "unit": "V"}
        raise ValueError("Enter any two of Voltage, Current, and Resistance.")

    if calc == "power":
        v, i = n("voltage"), n("current")
        return {"formula": "P = V × I", "answer": clean(v*i), "unit": "W"}

    if calc == "energy":
        p, t = n("power"), n("time")
        return {"formula": "E = P × t", "answer": clean(p*t), "unit": "J"}

    if calc == "series_resistance":
        values = [float(x) for x in d["values"].replace(",", " ").split()]
        if not values:
            raise ValueError("Enter resistor values.")
        return {"formula": "Rtotal = R1 + R2 + ...", "answer": clean(sum(values)), "unit": "Ω"}

    if calc == "parallel_resistance":
        values = [float(x) for x in d["values"].replace(",", " ").split()]
        if not values or any(x == 0 for x in values):
            raise ValueError("Enter non-zero resistor values.")
        return {"formula": "1/Rtotal = 1/R1 + 1/R2 + ...", "answer": clean(1/sum(1/x for x in values)), "unit": "Ω"}

    if calc == "voltage_divider":
        vin, r1, r2 = n("vin"), n("r1"), n("r2")
        return {"formula": "Vout = Vin × R2 / (R1 + R2)", "answer": clean(vin*r2/(r1+r2)), "unit": "V"}

    if calc == "led_resistor":
        vs, vf, current_ma = n("supply"), n("forward"), n("current_ma")
        i = current_ma / 1000
        return {"formula": "R = (Vs − Vf) / I", "answer": clean((vs-vf)/i), "unit": "Ω"}

    if calc == "rc_time":
        r, c = n("resistance"), n("capacitance")
        return {"formula": "τ = R × C", "answer": clean(r*c), "unit": "s"}

    if calc == "gain":
        vin, vout = n("vin"), n("vout")
        return {"formula": "Av = Vout / Vin", "answer": clean(vout/vin), "unit": "×"}

    if calc == "force":
        m, a = n("mass"), n("acceleration")
        return {"formula": "F = m × a", "answer": clean(m*a), "unit": "N"}

    if calc == "work":
        f, distance = n("force"), n("distance")
        angle = math.radians(n("angle"))
        return {"formula": "W = F × d × cos(θ)", "answer": clean(f*distance*math.cos(angle)), "unit": "J"}

    if calc == "power_mech":
        work, time = n("work"), n("time")
        return {"formula": "P = W / t", "answer": clean(work/time), "unit": "W"}

    if calc == "torque":
        f, r = n("force"), n("radius")
        return {"formula": "T = F × r", "answer": clean(f*r), "unit": "N·m"}

    if calc == "stress":
        force, area = n("force"), n("area")
        return {"formula": "σ = F / A", "answer": clean(force/area), "unit": "Pa"}

    if calc == "strain":
        change, original = n("change"), n("original")
        return {"formula": "ε = ΔL / L", "answer": clean(change/original), "unit": ""}

    if calc == "pressure":
        force, area = n("force"), n("area")
        return {"formula": "P = F / A", "answer": clean(force/area), "unit": "Pa"}

    if calc == "density":
        mass, volume = n("mass"), n("volume")
        return {"formula": "ρ = m / V", "answer": clean(mass/volume), "unit": "kg/m³"}

    if calc == "kinetic":
        mass, velocity = n("mass"), n("velocity")
        return {"formula": "KE = ½mv²", "answer": clean(0.5*mass*velocity**2), "unit": "J"}

    if calc == "potential":
        mass, height, g = n("mass"), n("height"), n("gravity")
        return {"formula": "PE = mgh", "answer": clean(mass*height*g), "unit": "J"}

    if calc == "efficiency":
        useful, input_power = n("useful"), n("input_power")
        return {"formula": "η = Useful / Input × 100", "answer": clean(useful/input_power*100), "unit": "%"}

    if calc == "gear_ratio":
        driver, driven = n("driver"), n("driven")
        return {"formula": "Gear ratio = Driven teeth / Driver teeth", "answer": clean(driven/driver), "unit": "ratio"}

    if calc == "rectangle_area":
        length, width = n("length"), n("width")
        return {"formula": "A = L × W", "answer": clean(length*width), "unit": "m²"}

    if calc == "triangle_area":
        base, height = n("base"), n("height")
        return {"formula": "A = ½bh", "answer": clean(0.5*base*height), "unit": "m²"}

    if calc == "circle_area":
        radius = n("radius")
        return {"formula": "A = πr²", "answer": clean(math.pi*radius**2), "unit": "m²"}

    if calc == "cylinder_volume":
        radius, height = n("radius"), n("height")
        return {"formula": "V = πr²h", "answer": clean(math.pi*radius**2*height), "unit": "m³"}

    if calc == "concrete_volume":
        length, width, height = n("length"), n("width"), n("height")
        return {"formula": "V = L × W × H", "answer": clean(length*width*height), "unit": "m³"}

    if calc == "binary_to_decimal":
        value = d["value"].strip()
        if not value or any(ch not in "01" for ch in value):
            raise ValueError("Enter a valid binary number.")
        return {"formula": "Binary → Decimal", "answer": int(value, 2), "unit": ""}

    if calc == "decimal_to_binary":
        value = int(float(d["value"]))
        if value < 0:
            raise ValueError("Enter a non-negative decimal number.")
        return {"formula": "Decimal → Binary", "answer": bin(value)[2:], "unit": ""}

    if calc == "decimal_to_hex":
        value = int(float(d["value"]))
        if value < 0:
            raise ValueError("Enter a non-negative decimal number.")
        return {"formula": "Decimal → Hexadecimal", "answer": hex(value)[2:].upper(), "unit": ""}

    if calc == "decimal_to_octal":
        value = int(float(d["value"]))
        if value < 0:
            raise ValueError("Enter a non-negative decimal number.")
        return {"formula": "Decimal → Octal", "answer": oct(value)[2:], "unit": ""}

    raise ValueError("Unknown calculator.")

# -----------------------------
# Unit conversions
# -----------------------------
CONVERSIONS = {
    "m_to_km": lambda x: x / 1000,
    "km_to_m": lambda x: x * 1000,
    "mm_to_m": lambda x: x / 1000,
    "m_to_mm": lambda x: x * 1000,
    "cm_to_m": lambda x: x / 100,
    "m_to_cm": lambda x: x * 100,
    "kg_to_g": lambda x: x * 1000,
    "g_to_kg": lambda x: x / 1000,
    "kmh_to_ms": lambda x: x / 3.6,
    "ms_to_kmh": lambda x: x * 3.6,
    "w_to_kw": lambda x: x / 1000,
    "kw_to_w": lambda x: x * 1000,
    "j_to_kj": lambda x: x / 1000,
    "kj_to_j": lambda x: x * 1000,
    "pa_to_kpa": lambda x: x / 1000,
    "kpa_to_pa": lambda x: x * 1000,
    "hz_to_khz": lambda x: x / 1000,
    "khz_to_hz": lambda x: x * 1000,
    "c_to_f": lambda x: x * 9/5 + 32,
    "f_to_c": lambda x: (x - 32) * 5/9,
    "c_to_k": lambda x: x + 273.15,
    "k_to_c": lambda x: x - 273.15,
    "n_to_kn": lambda x: x / 1000,
    "kn_to_n": lambda x: x * 1000,
}

CONVERSION_LABELS = {
    "m_to_km": "m → km", "km_to_m": "km → m", "mm_to_m": "mm → m",
    "m_to_mm": "m → mm", "cm_to_m": "cm → m", "m_to_cm": "m → cm",
    "kg_to_g": "kg → g", "g_to_kg": "g → kg", "kmh_to_ms": "km/h → m/s",
    "ms_to_kmh": "m/s → km/h", "w_to_kw": "W → kW", "kw_to_w": "kW → W",
    "j_to_kj": "J → kJ", "kj_to_j": "kJ → J", "pa_to_kpa": "Pa → kPa",
    "kpa_to_pa": "kPa → Pa", "hz_to_khz": "Hz → kHz", "khz_to_hz": "kHz → Hz",
    "c_to_f": "°C → °F", "f_to_c": "°F → °C", "c_to_k": "°C → K",
    "k_to_c": "K → °C", "n_to_kn": "N → kN", "kn_to_n": "kN → N"
}

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.post("/calculate")
def calculate():
    data = request.get_json(silent=True) or {}
    try:
        result = safe_eval(str(data.get("expression", "")))
        return jsonify({"success": True, "result": clean(result)})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

@app.post("/engineering")
def engineering():
    data = request.get_json(silent=True) or {}
    try:
        result = engineering_calc(data.get("calc"), data)
        return jsonify({"success": True, **result})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

@app.post("/convert")
def convert():
    data = request.get_json(silent=True) or {}
    try:
        key = data.get("conversion")
        value = float(data.get("value"))
        if key not in CONVERSIONS:
            raise ValueError("Unknown conversion.")
        result = clean(CONVERSIONS[key](value))
        return jsonify({"success": True, "result": result, "label": CONVERSION_LABELS[key]})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

@app.get("/formulas")
def formulas():
    return jsonify({
        "Electrical": [
            ["Ohm's Law", "V = I × R"],
            ["Electrical Power", "P = V × I"],
            ["Energy", "E = P × t"],
            ["Voltage Divider", "Vout = Vin × R2 / (R1 + R2)"]
        ],
        "Mechanical": [
            ["Force", "F = m × a"],
            ["Torque", "T = F × r"],
            ["Work", "W = F × d × cos(θ)"],
            ["Kinetic Energy", "KE = ½mv²"],
            ["Efficiency", "η = Useful / Input × 100"]
        ],
        "Civil": [
            ["Rectangle Area", "A = L × W"],
            ["Triangle Area", "A = ½bh"],
            ["Circle Area", "A = πr²"],
            ["Cylinder Volume", "V = πr²h"],
            ["Stress", "σ = F / A"]
        ],
        "Electronics": [
            ["LED Resistor", "R = (Vs − Vf) / I"],
            ["RC Time Constant", "τ = R × C"],
            ["Voltage Gain", "Av = Vout / Vin"]
        ],
        "Computer": [
            ["Binary to Decimal", "int(binary, 2)"],
            ["Decimal to Binary", "bin(decimal)"],
            ["Decimal to Hex", "hex(decimal)"],
            ["Decimal to Octal", "oct(decimal)"]
        ]
    })

if __name__ == "__main__":
    app.run(debug=True)
