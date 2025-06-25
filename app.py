from fastapi import FastAPI, HTTPException, Query
import psycopg2
import os

app = FastAPI()

# Redshift connection using environment variables
conn = psycopg2.connect(
    host=os.environ["REDSHIFT_HOST"],
    port=5439,
    database="dev",
    user=os.environ["REDSHIFT_USER"],
    password=os.environ["REDSHIFT_PASSWORD"]
)

@app.get("/")
def root():
    return {"message": "Claims API is working!"}

@app.get("/claims")
def get_all_claims():
    cur = conn.cursor()
    cur.execute("SELECT claim_id, customer_id, claim_amount, location, claim_type, status, risk_level FROM claims;")
    rows = cur.fetchall()
    cur.close()
    return [
        {
            "claim_id": r[0],
            "customer_id": r[1],
            "claim_amount": r[2],
            "location": r[3],
            "claim_type": r[4],
            "status": r[5],
            "risk_level": r[6]
        }
        for r in rows
    ]

@app.get("/claims/{claim_id}")
def get_claim_by_id(claim_id: int):
    cur = conn.cursor()
    cur.execute("SELECT * FROM claims WHERE claim_id = %s;", (claim_id,))
    row = cur.fetchone()
    cur.close()
    if row:
        return {
            "claim_id": row[0],
            "customer_id": row[1],
            "claim_amount": row[2],
            "location": row[3],
            "claim_type": row[4],
            "status": row[5],
            "is_zero_amount": row[6],
            "is_missing_location": row[7],
            "high_claim_flag": row[8],
            "duplicate_claim_flag": row[9],
            "suspicious_claim_score": row[10],
            "risk_level": row[11],
            "ai_explanation": row[12]
        }
    raise HTTPException(status_code=404, detail="Claim not found")

@app.get("/claims/risky")
def get_risky_claims():
    cur = conn.cursor()
    cur.execute("SELECT * FROM claims WHERE high_claim_flag = 1 OR suspicious_claim_score >= 2;")
    rows = cur.fetchall()
    cur.close()
    return [
        {
            "claim_id": r[0],
            "customer_id": r[1],
            "claim_amount": r[2],
            "location": r[3],
            "claim_type": r[4],
            "status": r[5],
            "risk_level": r[11],
            "suspicious_claim_score": r[10]
        }
        for r in rows
    ]

@app.get("/claims/suspicious")
def get_suspicious_claims():
    cur = conn.cursor()
    cur.execute("SELECT * FROM claims WHERE risk_level = 'Suspicious';")
    rows = cur.fetchall()
    cur.close()
    return [
        {
            "claim_id": r[0],
            "customer_id": r[1],
            "claim_amount": r[2],
            "location": r[3],
            "claim_type": r[4],
            "status": r[5],
            "risk_level": r[11],
            "suspicious_claim_score": r[10]
        }
        for r in rows
    ]

@app.get("/claims/search")
def search_claims(location: str = Query(None), status: str = Query(None)):
    cur = conn.cursor()
    query = "SELECT * FROM claims WHERE 1=1"
    params = []
    if location:
        query += " AND location = %s"
        params.append(location)
    if status:
        query += " AND status = %s"
        params.append(status)
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    return [
        {
            "claim_id": r[0],
            "customer_id": r[1],
            "claim_amount": r[2],
            "location": r[3],
            "claim_type": r[4],
            "status": r[5],
            "risk_level": r[11]
        }
        for r in rows
    ]
