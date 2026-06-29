import json
import os
from datetime import datetime
from pymongo import MongoClient
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

# Initialize MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "research_agent_db")

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = mongo_client[MONGO_DB_NAME]
    research_collection = db["research_results"]
except Exception as e:
    print(f"Warning: Could not connect to MongoDB: {e}")
    research_collection = None


def run_research_pipeline_stream(topic: str):
    state = {}
    
    def emit(event_type: str, agent: str = None, data: dict = None):
        payload = {"type": event_type}
        if agent:
            payload["agent"] = agent
        if data:
            payload["data"] = data
        return f"data: {json.dumps(payload)}\n\n"

    try:
        from limit_manager import increment_search
        increment_search()
        
        # Step 1: Search Agent
        yield emit("agent_start", "search", {"log": "Search agent is working..."})
        search_agent = build_search_agent()
        search_result = search_agent.invoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
        })
        tool_outputs = [m.content for m in search_result['messages'] if m.type == 'tool']
        state["search_results"] = "\n\n".join(tool_outputs) if tool_outputs else search_result['messages'][-1].content
        yield emit("agent_complete", "search", {"log": "Search complete", "output": state["search_results"]})

        # Step 2: Reader Agent
        yield emit("agent_start", "reader", {"log": "Reader agent is scraping top resources..."})
        reader_agent = build_reader_agent()
        reader_result = reader_agent.invoke({
            "messages": [("user",
                f"Based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:800]}"
            )]
        })
        tool_outputs = [m.content for m in reader_result['messages'] if m.type == 'tool']
        state['scraped_content'] = "\n\n".join(tool_outputs) if tool_outputs else reader_result['messages'][-1].content
        yield emit("agent_complete", "reader", {"log": "Scraping complete", "output": state["scraped_content"]})

        # Step 3: Writer Chain
        yield emit("agent_start", "writer", {"log": "Writer is drafting the report..."})
        research_combined = (
            f"SEARCH RESULTS : \n {state['search_results']} \n\n"
            f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
        )
        state["report"] = writer_chain.invoke({
            "topic": topic,
            "research": research_combined
        })
        yield emit("agent_complete", "writer", {"log": "Report drafted", "output": state["report"]})

        # Step 4: Critic Chain
        yield emit("agent_start", "critic", {"log": "Critic is reviewing the report..."})
        state["feedback"] = critic_chain.invoke({
            "report": state['report']
        })
        
        # Extract score roughly if possible to show in log
        yield emit("agent_complete", "critic", {"log": "Review complete", "output": state["feedback"]})

        # Save to MongoDB
        if research_collection is not None:
            try:
                doc = {
                    "topic": topic,
                    "search_results": state.get("search_results", ""),
                    "scraped_content": state.get("scraped_content", ""),
                    "report": state.get("report", ""),
                    "feedback": state.get("feedback", ""),
                    "created_at": datetime.utcnow()
                }
                research_collection.insert_one(doc)
                yield emit("db_save", data={"log": "Result saved to database successfully"})
            except Exception as e:
                yield emit("db_error", data={"log": f"Failed to save to database: {e}"})

        # Final Result
        yield emit("final_result", data=state)
        
    except Exception as e:
        yield emit("error", data={"message": str(e)})


def run_research_pipeline(topic: str) -> dict:
    from limit_manager import increment_search
    increment_search()
    
    state = {}
    print("\n"+" ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)
    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages" : [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    tool_outputs = [m.content for m in search_result['messages'] if m.type == 'tool']
    state["search_results"] = "\n\n".join(tool_outputs) if tool_outputs else search_result['messages'][-1].content
    print("\n search result ",state['search_results'])

    print("\n"+" ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)
    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}"
        )]
    })
    tool_outputs = [m.content for m in reader_result['messages'] if m.type == 'tool']
    state['scraped_content'] = "\n\n".join(tool_outputs) if tool_outputs else reader_result['messages'][-1].content
    print("\nscraped content: \n", state['scraped_content'])

    print("\n"+" ="*50)
    print("step 3 - Writer is drafting the report ...")
    print("="*50)
    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )
    state["report"] = writer_chain.invoke({
        "topic" : topic,
        "research" : research_combined
    })
    print("\n Final Report\n",state['report'])

    print("\n"+" ="*50)
    print("step 4 - critic is reviewing the report ")
    print("="*50)
    state["feedback"] = critic_chain.invoke({
        "report":state['report']
    })
    print("\n critic report \n", state['feedback'])

    if research_collection is not None:
        try:
            print("\n"+" ="*50)
            print("step 5 - saving to MongoDB ")
            print("="*50)
            doc = {
                "topic": topic,
                "search_results": state.get("search_results", ""),
                "scraped_content": state.get("scraped_content", ""),
                "report": state.get("report", ""),
                "feedback": state.get("feedback", ""),
                "created_at": datetime.utcnow()
            }
            research_collection.insert_one(doc)
            print("Successfully saved to MongoDB")
        except Exception as e:
            print(f"Failed to save to MongoDB: {e}")

    return state

if __name__ == "__main__":
    topic = input("\n Enter a research topic : ")
    run_research_pipeline(topic)
