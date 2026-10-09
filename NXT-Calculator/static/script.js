const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const historyList = $("#historyList");
let history = [];

function addHistory(label, answer) {
    history.unshift({label, answer});
    history = history.slice(0, 8);
    renderHistory();
}
function renderHistory() {
    if (!history.length) {
        historyList.innerHTML = '<div class="empty">No calculations yet</div>';
        return;
    }
    historyList.innerHTML = history.map(x =>
        `<div class="history-item"><span>${x.label}</span><span class="answer">${x.answer}</span></div>`
    ).join("");
}
$("#clearHistory").onclick = () => { history = []; renderHistory(); };

function updateClock() {
    const now = new Date();
    $("#date").textContent = now.toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"}).toUpperCase();
    $("#time").textContent = now.toLocaleTimeString("en-IN",{hour:"2-digit",minute:"2-digit"});
}
updateClock(); setInterval(updateClock,1000);

$("#themeBtn").onclick = () => {
    document.body.classList.toggle("light");
    $("#themeBtn").textContent = document.body.classList.contains("light") ? "☾" : "☀";
};

/* ---------------- Basic calculator ---------------- */
let basicExpr = "";
let justCalculated = false;

function basicDisplay() {
    $("#basicResult").textContent = basicExpr || "0";
}
$$("[data-basic-value]").forEach(btn => {
    btn.onclick = () => {
        if (justCalculated) { basicExpr = ""; justCalculated = false; }
        const v = btn.dataset.basicValue;
        if (v === "." && basicExpr.split(/[+\-*/]/).pop().includes(".")) return;
        basicExpr += v;
        basicDisplay();
    };
});
$$(".op[data-basic-value]").forEach(btn => {
    btn.onclick = () => {
        if (!basicExpr) return;
        const last = basicExpr.slice(-1);
        if ("+-*/".includes(last)) basicExpr = basicExpr.slice(0,-1);
        basicExpr += btn.dataset.basicValue;
        $("#basicExpression").textContent = basicExpr.replace("*","×").replace("/","÷");
    };
});
$('[data-basic="clear"]').onclick = () => { basicExpr=""; justCalculated=false; $("#basicExpression").textContent=""; basicDisplay(); };
$('[data-basic="delete"]').onclick = () => { basicExpr=basicExpr.slice(0,-1); basicDisplay(); };
$('[data-basic="sign"]').onclick = () => {
    if (!basicExpr) return;
    if (/^-?\d+(\.\d+)?$/.test(basicExpr)) basicExpr = basicExpr.startsWith("-") ? basicExpr.slice(1) : "-"+basicExpr;
    basicDisplay();
};
$('[data-basic="percent"]').onclick = async () => {
    if (!basicExpr) return;
    try {
        const r = await post("/calculate",{expression:`(${basicExpr})/100`});
        basicExpr = String(r.result); basicDisplay();
    } catch(e) { $("#basicResult").textContent=e.message; }
};
$('[data-basic="calculate"]').onclick = async () => {
    if (!basicExpr) return;
    try {
        const old = basicExpr;
        const r = await post("/calculate",{expression:basicExpr});
        $("#basicExpression").textContent = old.replaceAll("*","×").replaceAll("/","÷")+" =";
        $("#basicResult").textContent = r.result;
        addHistory(old.replaceAll("*","×").replaceAll("/","÷"), r.result);
        basicExpr = String(r.result);
        justCalculated = true;
    } catch(e) { $("#basicResult").textContent=e.message; }
};

/* ---------------- Mode switching ---------------- */
const modePanels = {
    basic:"basicPanel", scientific:"scientificPanel",
    electrical:"engineeringPanel", electronics:"engineeringPanel",
    mechanical:"engineeringPanel", civil:"engineeringPanel",
    computer:"engineeringPanel", converter:"converterPanel",
    formulas:"formulasPanel"
};
$$(".mode").forEach(btn => btn.onclick = () => {
    $$(".mode").forEach(x=>x.classList.remove("active"));
    btn.classList.add("active");
    Object.values(modePanels).forEach(id=>$("#"+id).classList.add("hidden"));
    const mode = btn.dataset.mode;
    $("#"+modePanels[mode]).classList.remove("hidden");
    if (["electrical","electronics","mechanical","civil","computer"].includes(mode)) loadEngineering(mode);
});

/* ---------------- Scientific ---------------- */
$$("[data-scientific]").forEach(btn => btn.onclick = () => {
    const input = $("#scientificInput");
    const v = btn.dataset.scientific;
    if (v === "^2") input.value += "^2";
    else input.value += v;
    input.focus();
});
$("#scientificCalculate").onclick = async () => {
    try {
        const expression = $("#scientificInput").value;
        const r = await post("/calculate",{expression});
        $("#scientificAnswer").innerHTML = `<strong>${r.result}</strong>`;
        addHistory(expression, r.result);
    } catch(e) { $("#scientificAnswer").textContent=e.message; }
};

/* ---------------- Engineering calculators ---------------- */
const configs = {
 electrical: {
   title:"Electrical", tag:"ELECTRICAL",
   items:[
    ["ohm","Ohm's Law",[["voltage","Voltage (V)"],["current","Current (A)"],["resistance","Resistance (Ω)"]]],
    ["power","Electrical Power",[["voltage","Voltage (V)"],["current","Current (A)"]]],
    ["energy","Electrical Energy",[["power","Power (W)"],["time","Time (s)"]]],
    ["series_resistance","Series Resistance",[["values","Resistors (Ω), e.g. 10, 20, 30"]]],
    ["parallel_resistance","Parallel Resistance",[["values","Resistors (Ω), e.g. 10, 20"]]],
    ["voltage_divider","Voltage Divider",[["vin","Input Voltage (V)"],["r1","R1 (Ω)"],["r2","R2 (Ω)"]]]
   ]
 },
 electronics:{
   title:"Electronics", tag:"ELECTRONICS",
   items:[
    ["led_resistor","LED Resistor",[["supply","Supply Voltage (V)"],["forward","LED Forward Voltage (V)"],["current_ma","LED Current (mA)"]]],
    ["rc_time","RC Time Constant",[["resistance","Resistance (Ω)"],["capacitance","Capacitance (F)"]]],
    ["gain","Voltage Gain",[["vin","Input Voltage (V)"],["vout","Output Voltage (V)"]]]
   ]
 },
 mechanical:{
   title:"Mechanical", tag:"MECHANICAL",
   items:[
    ["force","Force",[["mass","Mass (kg)"],["acceleration","Acceleration (m/s²)"]]],
    ["work","Work",[["force","Force (N)"],["distance","Distance (m)"],["angle","Angle (degrees)"]]],
    ["power_mech","Mechanical Power",[["work","Work (J)"],["time","Time (s)"]]],
    ["torque","Torque",[["force","Force (N)"],["radius","Radius (m)"]]],
    ["stress","Stress",[["force","Force (N)"],["area","Area (m²)"]]],
    ["strain","Strain",[["change","Change in length (m)"],["original","Original length (m)"]]],
    ["pressure","Pressure",[["force","Force (N)"],["area","Area (m²)"]]],
    ["density","Density",[["mass","Mass (kg)"],["volume","Volume (m³)"]]],
    ["kinetic","Kinetic Energy",[["mass","Mass (kg)"],["velocity","Velocity (m/s)"]]],
    ["potential","Potential Energy",[["mass","Mass (kg)"],["height","Height (m)"],["gravity","Gravity (m/s²), e.g. 9.81"]]],
    ["efficiency","Efficiency",[["useful","Useful output"],["input_power","Input"]]],
    ["gear_ratio","Gear Ratio",[["driver","Driver teeth"],["driven","Driven teeth"]]]
   ]
 },
 civil:{
   title:"Civil", tag:"CIVIL",
   items:[
    ["rectangle_area","Rectangle Area",[["length","Length (m)"],["width","Width (m)"]]],
    ["triangle_area","Triangle Area",[["base","Base (m)"],["height","Height (m)"]]],
    ["circle_area","Circle Area",[["radius","Radius (m)"]]],
    ["cylinder_volume","Cylinder Volume",[["radius","Radius (m)"],["height","Height (m)"]]],
    ["concrete_volume","Concrete Volume",[["length","Length (m)"],["width","Width (m)"],["height","Height (m)"]]],
    ["stress","Stress",[["force","Force (N)"],["area","Area (m²)"]]]
   ]
 },
 computer:{
   title:"Computer / IT", tag:"COMPUTER",
   items:[
    ["binary_to_decimal","Binary → Decimal",[["value","Binary value"]]],
    ["decimal_to_binary","Decimal → Binary",[["value","Decimal value"]]],
    ["decimal_to_hex","Decimal → Hexadecimal",[["value","Decimal value"]]],
    ["decimal_to_octal","Decimal → Octal",[["value","Decimal value"]]]
   ]
 }
};

function loadEngineering(mode) {
    const c = configs[mode];
    $("#engTitle").textContent=c.title;
    $("#engTag").textContent=c.tag;
    $("#engDescription").textContent="Choose a calculator and enter the values.";
    const select=$("#engSelect");
    select.innerHTML=c.items.map(x=>`<option value="${x[0]}">${x[1]}</option>`).join("");
    select.dataset.mode=mode;
    renderFields();
}
function renderFields() {
    const mode=$("#engSelect").dataset.mode;
    const item=configs[mode].items.find(x=>x[0]===$("#engSelect").value);
    $("#engFields").innerHTML=item[2].map(f=>`<div class="field"><label>${f[1]}</label><input id="field_${f[0]}" type="${f[0]==="values"?"text":"number"}" step="any" placeholder="Enter value"></div>`).join("");
    $("#engAnswer").textContent="Enter values and calculate.";
}
$("#engSelect").onchange=renderFields;

$("#engCalculate").onclick=async()=>{
    const mode=$("#engSelect").dataset.mode;
    const item=configs[mode].items.find(x=>x[0]===$("#engSelect").value);
    const data={calc:item[0]};
    item[2].forEach(f=>data[f[0]]=$("#field_"+f[0]).value);
    try{
        const r=await post("/engineering",data);
        $("#engAnswer").innerHTML=`<div>Formula: <b>${r.formula}</b></div><div style="margin-top:7px">Answer: <strong>${r.answer} ${r.unit}</strong></div>`;
        addHistory(item[1],`${r.answer} ${r.unit}`);
    }catch(e){$("#engAnswer").textContent=e.message;}
};

/* ---------------- Units ---------------- */
const conversions = [
 ["m_to_km","m → km"],["km_to_m","km → m"],["mm_to_m","mm → m"],["m_to_mm","m → mm"],
 ["cm_to_m","cm → m"],["m_to_cm","m → cm"],["kg_to_g","kg → g"],["g_to_kg","g → kg"],
 ["kmh_to_ms","km/h → m/s"],["ms_to_kmh","m/s → km/h"],["w_to_kw","W → kW"],["kw_to_w","kW → W"],
 ["j_to_kj","J → kJ"],["kj_to_j","kJ → J"],["pa_to_kpa","Pa → kPa"],["kpa_to_pa","kPa → Pa"],
 ["hz_to_khz","Hz → kHz"],["khz_to_hz","kHz → Hz"],["c_to_f","°C → °F"],["f_to_c","°F → °C"],
 ["c_to_k","°C → K"],["k_to_c","K → °C"],["n_to_kn","N → kN"],["kn_to_n","kN → N"]
];
$("#conversionSelect").innerHTML=conversions.map(x=>`<option value="${x[0]}">${x[1]}</option>`).join("");
$("#convertBtn").onclick=async()=>{
    try{
        const r=await post("/convert",{conversion:$("#conversionSelect").value,value:$("#conversionValue").value});
        $("#conversionAnswer").innerHTML=`<strong>${r.result}</strong> <span>${r.label.split("→")[1].trim()}</span>`;
        addHistory(r.label,$("#conversionValue").value+" → "+r.result);
    }catch(e){$("#conversionAnswer").textContent=e.message;}
};

/* ---------------- Formula library ---------------- */
async function loadFormulas(){
    const data=await fetch("/formulas").then(r=>r.json());
    $("#formulaList").innerHTML=Object.entries(data).map(([group,items])=>
        `<div><h3 style="margin:10px 0 7px;font-size:13px;color:var(--accent)">${group}</h3>${items.map(x=>`<div class="formula-card"><h3>${x[0]}</h3><p>${x[1]}</p></div>`).join("")}</div>`
    ).join("");
}
loadFormulas();

async function post(url,data){
    const response=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
    const result=await response.json();
    if(!response.ok || !result.success) throw new Error(result.error || "Calculation failed");
    return result;
}

document.addEventListener("keydown",e=>{
    if(e.key==="Enter" && !$("#scientificPanel").classList.contains("hidden")) $("#scientificCalculate").click();
    if(e.key==="Escape") $('[data-basic="clear"]').click();
});
