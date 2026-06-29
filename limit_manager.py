import os
import json
from pymongo import MongoClient
from langchain_core.callbacks import BaseCallbackHandler

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "research_agent_db")
LIMIT = 50

# Fallback local file path
LOCAL_FILE = os.path.join(os.path.dirname(__file__), "api_usage.json")

def get_mongo_collection():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[MONGO_DB_NAME]
        return db["usage_limits"]
    except Exception:
        return None

def get_usage():
    # Try MongoDB first
    col = get_mongo_collection()
    if col is not None:
        try:
            doc = col.find_one({"_id": "usage_stats"})
            if doc:
                return {
                    "searches": doc.get("searches", 0),
                    "api_calls": doc.get("api_calls", 0)
                }
            else:
                # Initialize MongoDB document
                col.insert_one({"_id": "usage_stats", "searches": 0, "api_calls": 0})
                return {"searches": 0, "api_calls": 0}
        except Exception:
            pass # fallback to local file

    # Local file fallback
    if os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, "r") as f:
                data = json.load(f)
                return {
                    "searches": data.get("searches", 0),
                    "api_calls": data.get("api_calls", 0)
                }
        except Exception:
            pass

    return {"searches": 0, "api_calls": 0}

def update_usage(searches_delta=0, api_calls_delta=0):
    current = get_usage()
    new_searches = current["searches"] + searches_delta
    new_api_calls = current["api_calls"] + api_calls_delta

    # Update MongoDB
    col = get_mongo_collection()
    if col is not None:
        try:
            col.update_one(
                {"_id": "usage_stats"},
                {"$set": {"searches": new_searches, "api_calls": new_api_calls}},
                upsert=True
            )
        except Exception:
            pass

    # Always write to local file as secondary backup/local state
    try:
        with open(LOCAL_FILE, "w") as f:
            json.dump({"searches": new_searches, "api_calls": new_api_calls}, f)
    except Exception:
        pass

class GeminiLimitReachedException(Exception):
    pass

def check_limit():
    usage = get_usage()
    if usage["searches"] >= LIMIT:
        raise GeminiLimitReachedException(f"Search limit of {LIMIT} searches has been reached. No further searches allowed.")
    if usage["api_calls"] >= LIMIT:
        raise GeminiLimitReachedException(f"Gemini API call limit of {LIMIT} calls has been reached. No further API calls allowed.")

def increment_search():
    check_limit()
    update_usage(searches_delta=1)

def increment_api_call():
    check_limit()
    update_usage(api_calls_delta=1)

class GeminiUsageCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        increment_api_call()
