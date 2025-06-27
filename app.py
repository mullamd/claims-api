from fastapi import FastAPI, HTTPException, Query
import psycopg2
import os

app = FastAPI()

# Function to get Redshift connection
def get_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ["REDSHIFT_HOST"],
            port=int(os.environ.get("REDSHIFT_PORT", "5439")),
            database=os.environ.get("REDSHIFT_DB", "dev"),
            user=os.environ["REDSHIFT_USER"],
            password=os.environ["REDSHIFT_PASSWORD"]
        )
        return conn
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Missing environment variable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@app.get("/")
def root():
    return {"message": "Claims API is working!"}


@app.get("/claims")
def get_all_claims():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT claim_id, customer_id, claim_amount, location, claim_type, status, risk_level 
            FROM insurance_ai.ai_claim_explanations;
        """)
        rows = cur.fetchall()
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()


@app.get("/claims/risky")
def get_risky_claims():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM insurance_ai.ai_claim_explanations 
            WHERE high_claim_flag = 1 OR suspicious_claim_score >= 2;
        """)
        rows = cur.fetchall()
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()


@app.get("/claims/suspicious")
def get_suspicious_claims():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM insurance_ai.ai_claim_explanations WHERE risk_level = 'Suspicious';
        """)
        rows = cur.fetchall()
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()


@app.get("/claims/search")
def search_claims(location: str = Query(None), status: str = Query(None)):
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = "SELECT * FROM insurance_ai.ai_claim_explanations WHERE 1=1"
        params = []
        if location:
            query += " AND location = %s"
            params.append(location)
        if status:
            query += " AND status = %s"
            params.append(status)
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()


# THIS ROUTE COMES LAST to prevent conflicts
@app.get("/claims/{claim_id}")
def get_claim_by_id(claim_id: int):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM insurance_ai.ai_claim_explanations WHERE claim_id = %s;
        """, (claim_id,))
        row = cur.fetchone()
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()
