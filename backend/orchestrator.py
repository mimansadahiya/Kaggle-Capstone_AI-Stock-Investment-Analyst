import asyncio
import json
from typing import AsyncGenerator
try:
    from backend.agents.company_overview import get_company_overview
    from backend.agents.macro_outlook import get_macro_outlook
    from backend.agents.industry_analysis import get_industry_analysis
except ModuleNotFoundError:
    from agents.company_overview import get_company_overview
    from agents.macro_outlook import get_macro_outlook
    from agents.industry_analysis import get_industry_analysis

async def run_analysis(ticker_or_name: str) -> AsyncGenerator[dict, None]:
    """
    Coordinates and executes Agent 1, Agent 2, and Agent 3 in parallel.
    Yields real-time progress logs and final reports as they complete.
    """
    yield {
        "type": "log", 
        "agent": "System", 
        "message": f"Starting multi-agent investment research for '{ticker_or_name}'..."
    }
    await asyncio.sleep(0.5)

    # Status queue to collect log events from background tasks
    log_queue = asyncio.Queue()

    # Define tasks with logging
    async def run_agent_1():
        await log_queue.put({
            "type": "log", 
            "agent": "Agent 1", 
            "message": "Initializing Company Overview Analysis. Fetching latest corporate data..."
        })
        await asyncio.sleep(0.8)
        await log_queue.put({
            "type": "log", 
            "agent": "Agent 1", 
            "message": "Running Google Search grounding for business model, segments, and growth strategy..."
        })
        
        result = await get_company_overview(ticker_or_name)
        
        await log_queue.put({
            "type": "log", 
            "agent": "Agent 1", 
            "message": "Company Overview Analysis completed. Formatting report..."
        })
        return result

    async def run_agent_2():
        await log_queue.put({
            "type": "log", 
            "agent": "Agent 2", 
            "message": "Initializing Macroeconomic Outlook Analysis. Checking current interest rate trends..."
        })
        await asyncio.sleep(1.2)
        await log_queue.put({
            "type": "log", 
            "agent": "Agent 2", 
            "message": "Running Google Search grounding for industry growth trends, fiscal policy, and inflation data..."
        })
        
        result = await get_macro_outlook(ticker_or_name)
        
        await log_queue.put({
            "type": "log", 
            "agent": "Agent 2", 
            "message": "Macroeconomic Analysis completed. Formatting report..."
        })
        return result

    async def run_agent_3():
        await log_queue.put({
            "type": "log", 
            "agent": "Agent 3", 
            "message": "Initializing Industry & Market Analysis. Checking sector metrics..."
        })
        await asyncio.sleep(1.6)
        await log_queue.put({
            "type": "log", 
            "agent": "Agent 3", 
            "message": "Running Google Search grounding for market size, CAGR projections, trends, and challenges..."
        })
        
        result = await get_industry_analysis(ticker_or_name)
        
        await log_queue.put({
            "type": "log", 
            "agent": "Agent 3", 
            "message": "Industry & Market Analysis completed. Formatting report..."
        })
        return result

    # Start all three agent tasks in the background
    task1 = asyncio.create_task(run_agent_1())
    task2 = asyncio.create_task(run_agent_2())
    task3 = asyncio.create_task(run_agent_3())

    # Keep yielding logs while the tasks are running
    while not (task1.done() and task2.done() and task3.done()):
        # Process any pending logs in the queue
        while not log_queue.empty():
            log_item = await log_queue.get()
            yield log_item
            log_queue.task_done()
        await asyncio.sleep(0.2)

    # Clear out any remaining logs in the queue
    while not log_queue.empty():
        log_item = await log_queue.get()
        yield log_item
        log_queue.task_done()

    # Fetch results
    try:
        report1 = await task1
        yield {
            "type": "report",
            "agent": "Agent 1",
            "message": report1
        }
    except Exception as e:
        yield {
            "type": "log",
            "agent": "System",
            "message": f"Error retrieving Agent 1 report: {str(e)}"
        }

    try:
        report2 = await task2
        yield {
            "type": "report",
            "agent": "Agent 2",
            "message": report2
        }
    except Exception as e:
        yield {
            "type": "log",
            "agent": "System",
            "message": f"Error retrieving Agent 2 report: {str(e)}"
        }

    try:
        report3 = await task3
        yield {
            "type": "report",
            "agent": "Agent 3",
            "message": report3
        }
    except Exception as e:
        yield {
            "type": "log",
            "agent": "System",
            "message": f"Error retrieving Agent 3 report: {str(e)}"
        }

    yield {
        "type": "log",
        "agent": "System",
        "message": "Stock analysis complete! Reports are fully rendered below."
    }
