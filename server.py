import json, math, os, re, urllib.request
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

APP_DIR = Path(__file__).resolve().parent
BASE = os.getenv("SPARK_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
MODEL_OVERRIDE = os.getenv("SPARK_MODEL", "auto")
API_KEY = os.getenv("SPARK_API_KEY", "")
TIMEOUT = float(os.getenv("SPARK_TIMEOUT", "120"))
NOBELS = json.loads((APP_DIR / "data" / "nobel.json").read_text())
NOBEL_BY_ID = {n["id"]: n for n in NOBELS}

app = FastAPI(title="Paper Science-Technology Landscape", version="0.3.0")

class PaperIn(BaseModel):
    title: str = ""
    abstract: str


def request_json(url: str, payload: dict | None = None, method: str = "GET"):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


def discover_models():
    try:
        j = request_json(BASE + "/models")
        return [x.get("id", "") for x in j.get("data", []) if x.get("id")]
    except Exception:
        return []


def model_score(name: str):
    s = name.lower(); score = 0.0
    nums = re.findall(r"(\d+(?:\.\d+)?)\s*b\b", s)
    if nums: score += max(float(x) for x in nums) * 12
    for word, points in [("instruct",120),("reason",110),("thinking",100),("qwen",35),("nemotron",30),("llama",20),("mistral",20)]:
        if word in s: score += points
    if any(x in s for x in ["embed", "rerank", "whisper", "asr"]): score -= 2000
    if any(x in s for x in ["vl", "vision"]): score -= 15
    return score


def select_model(models: list[str]):
    if MODEL_OVERRIDE != "auto": return MODEL_OVERRIDE
    return max(models, key=model_score) if models else None


def nobel_reference_text():
    rows=[]
    for n in NOBELS:
        rows.append(f'{n["id"]} | {n["year"]} {n["category"]} | {n["title"]} | keywords: {", ".join(n.get("keywords", []))}')
    return "\n".join(rows)

SYSTEM_PROMPT = '''You are a senior scientific and technology-assessment analyst. Classify a research paper using ONLY its title and abstract plus the supplied Nobel reference catalogue. Do not assume the paper is correct. Do not use outside facts. Return JSON only.

Axes:
- fundamentalScienceScore (0-100): 0 = strongly application/engineering-oriented; 100 = primarily fundamental mechanisms, laws, theory, or basic scientific understanding. Descriptive, not a quality score.
- technologyMaturityScore (0-100): demonstrated technological maturity supported by the abstract. "Could", "may", "potential" do NOT justify high maturity. High values need implemented systems, hardware, prototypes, real-world deployment, clinical/industrial validation, strong operational benchmarks, manufacturing, or field evidence.
- technologyPotentialScore (0-100): plausible future technological potential, separate from demonstrated maturity.
- confidence (0-1): confidence that the abstract contains enough evidence to position the paper.

Infer primaryArea from: Physics, Chemistry, Medicine, Biology, Materials, Computer Science, Artificial Intelligence, Robotics, Mathematics, Energy, Earth & Climate, Space, Engineering, Other. Add up to 3 secondaryAreas.

Nobel proximity:
From the supplied Nobel catalogue, choose up to 5 Nobel entries that are conceptually closest to the paper. This is thematic/intellectual affinity, NOT prestige and NOT a claim that the paper is Nobel-level. Assign each conceptualScore 0-100 and a one-sentence rationale grounded in the abstract and Nobel catalogue. Use ONLY Nobel IDs from the catalogue.

Return exactly:
{
 "title":"...",
 "primaryArea":"...",
 "secondaryAreas":["..."],
 "fundamentalScienceScore":0,
 "technologyMaturityScore":0,
 "technologyPotentialScore":0,
 "confidence":0.0,
 "summary":"one concise sentence",
 "rationale":"2-4 concise sentences explaining X and Y, distinguishing demonstrated evidence from future claims",
 "signals":["up to 6 short evidence signals"],
 "nobelAffinity":[{"id":"physics-2024","conceptualScore":0,"rationale":"..."}]
}
Use integer scores. Never output markdown fences.'''


def extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    try: return json.loads(text)
    except Exception:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a: return json.loads(text[a:b+1])
        raise


def clamp(v, a=0, b=100):
    try: return max(a, min(b, int(round(float(v)))))
    except Exception: return 50


def map_distance(p, n):
    dx = float(p["fundamentalScienceScore"]) - float(n["fundamentalScienceScore"])
    dy = float(p["technologyMaturityScore"]) - float(n["technologyImpactScore"])
    return math.sqrt(dx*dx + dy*dy)


def enrich_nobel_affinity(out: dict, raw_affinity: list | None):
    conceptual = {}
    rationale = {}
    for item in raw_affinity or []:
        nid = str(item.get("id", ""))
        if nid in NOBEL_BY_ID:
            conceptual[nid] = clamp(item.get("conceptualScore", 0))
            rationale[nid] = str(item.get("rationale", ""))[:500]
    rows=[]
    for n in NOBELS:
        dist = map_distance(out, n)
        position_score = max(0.0, 100.0 - dist / math.sqrt(2))
        c = conceptual.get(n["id"], 0)
        # Hybrid emphasizes intellectual affinity while preserving geometric agreement.
        hybrid = 0.65*c + 0.35*position_score
        rows.append({
            "id": n["id"], "year": n["year"], "category": n["category"], "title": n["title"],
            "laureates": n.get("laureates", []), "conceptualScore": c,
            "positionScore": round(position_score, 1), "hybridScore": round(hybrid, 1),
            "mapDistance": round(dist, 1), "rationale": rationale.get(n["id"], "")
        })
    # If model supplied no conceptual ranking, generate a lexical fallback so UI still works.
    if not conceptual:
        text = " ".join([out.get("title", ""), out.get("summary", ""), out.get("primaryArea", ""), *out.get("secondaryAreas", []), *out.get("signals", [])]).lower()
        toks=set(re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", text))
        for r in rows:
            n=NOBEL_BY_ID[r["id"]]
            nt=set(re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", (n["title"]+" "+" ".join(n.get("keywords",[]))).lower()))
            overlap=len(toks & nt)
            r["conceptualScore"] = min(90, overlap*22)
            r["hybridScore"] = round(0.65*r["conceptualScore"] + 0.35*r["positionScore"],1)
            if overlap: r["rationale"]="Keyword-level thematic overlap (fallback estimate)."
    return sorted(rows, key=lambda x: x["hybridScore"], reverse=True)[:8]


def normalize(j: dict, title: str, model: str, mode: str):
    out = {
      "title": j.get("title") or title or "Untitled paper",
      "primaryArea": j.get("primaryArea", "Other"),
      "secondaryAreas": (j.get("secondaryAreas") or [])[:3],
      "fundamentalScienceScore": clamp(j.get("fundamentalScienceScore", 50)),
      "technologyMaturityScore": clamp(j.get("technologyMaturityScore", 30)),
      "technologyPotentialScore": clamp(j.get("technologyPotentialScore", 50)),
      "confidence": max(0, min(1, float(j.get("confidence", 0.5)))),
      "summary": str(j.get("summary", ""))[:600],
      "rationale": str(j.get("rationale", ""))[:1800],
      "signals": [str(x)[:140] for x in (j.get("signals") or [])[:6]],
      "model": model, "mode": mode
    }
    out["nobelProximity"] = enrich_nobel_affinity(out, j.get("nobelAffinity") or [])
    return out


def heuristic(p: PaperIn):
    t=(p.title+" "+p.abstract).lower()
    areas=[("Artificial Intelligence",["neural","machine learning","llm","transformer","artificial intelligence","deep learning"]),("Robotics",["robot","manipulation","navigation","grasp","autonomous"]),("Medicine",["patient","clinical","disease","diagnos","therapy","medical"]),("Biology",["protein","gene","cell","genome","biological"]),("Physics",["quantum","particle","physics","wave","relativity"]),("Chemistry",["chemical","molecule","catal","synthesis"]),("Materials",["material","alloy","polymer","semiconductor"]),("Energy",["battery","solar","energy","fusion"]),("Mathematics",["theorem","proof","equation","mathematical"])]
    area="Computer Science" if any(k in t for k in ["algorithm","software","computation"]) else "Other"
    for a,ks in areas:
        if any(k in t for k in ks): area=a; break
    fundamental=72 if any(k in t for k in ["theory","theorem","mechanism","fundamental","proof","derive"]) else 48
    if any(k in t for k in ["prototype","robot","device","system","hardware","implementation"]): fundamental-=18
    maturity=18
    if any(k in t for k in ["benchmark","experiment","implemented","prototype","hardware","device"]): maturity=46
    if any(k in t for k in ["real-world","deployed","clinical trial","industrial","manufactur","field test"]): maturity=72
    potential=70 if any(k in t for k in ["potential","could","may enable","promising","application"]) else max(45,maturity+10)
    j={"title":p.title or "Untitled paper","primaryArea":area,"secondaryAreas":[],"fundamentalScienceScore":fundamental,"technologyMaturityScore":maturity,"technologyPotentialScore":potential,"confidence":0.35,"summary":"Demo-mode estimate based on keyword signals in the abstract.","rationale":"The Spark LLM endpoint was not reachable, so this point uses a simple local heuristic for UI testing only.","signals":["DEMO HEURISTIC"]}
    return normalize(j,p.title,"local-heuristic","demo")

@app.get("/api/health")
def health():
    ms=discover_models(); sel=select_model(ms)
    return {"ok":True,"spark_connected":bool(sel),"selected_model":sel,"model_count":len(ms),"base_url":BASE}

@app.get("/api/models")
def models():
    ms=discover_models(); sel=select_model(ms)
    return {"models":ms,"selected":sel or "local-heuristic","mode":"live" if sel else "demo","base_url":BASE}

@app.get("/api/nobels")
def nobels(): return NOBELS

@app.post("/api/analyze")
def analyze(p: PaperIn):
    if len(p.abstract.strip()) < 80: raise HTTPException(400,"Abstract is too short.")
    ms=discover_models(); model=select_model(ms)
    if not model: return heuristic(p)
    user = f"TITLE:\n{p.title}\n\nABSTRACT:\n{p.abstract}\n\nNOBEL REFERENCE CATALOGUE:\n{nobel_reference_text()}"
    payload={"model":model,"messages":[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":user}],"temperature":0.1,"max_tokens":1600}
    try:
        raw=request_json(BASE+"/chat/completions",payload,"POST")
        text=raw["choices"][0]["message"].get("content","")
        return normalize(extract_json(text),p.title,model,"live")
    except Exception as e:
        out=heuristic(p); out["rationale"]="Spark model call failed; demo heuristic used instead. "+out["rationale"]; out["error"]=str(e)[:400]; return out

app.mount("/",StaticFiles(directory=APP_DIR,html=True),name="static")
