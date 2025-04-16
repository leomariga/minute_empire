import asyncio
import time
from datetime import datetime
from typing import Dict, List, Callable, Coroutine, Any, Optional
import heapq
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    """Task scheduler for executing game tasks at specific times"""
    
    def __init__(self):
        self.tasks = []  # priority queue based on execution time
        self.task_map = {}  # mapping from task_id to task
        self.running = False
        self.task_lock = asyncio.Lock()
    
    async def schedule_task(self, task_id: str, execution_time: datetime, 
                           callback: Callable[..., Coroutine], *args, **kwargs):
        """Schedule a task to run at a specific time"""
        execution_timestamp = execution_time.timestamp()
        task_data = (execution_timestamp, task_id, callback, args, kwargs)
        
        async with self.task_lock:
            # Add to priority queue (heap)
            heapq.heappush(self.tasks, task_data)
            # Store in map for easy access
            self.task_map[task_id] = task_data
            
        logger.info(f"Scheduled task {task_id} to run at {execution_time}")
        
        # Start the scheduler if not already running
        if not self.running:
            asyncio.create_task(self.run_scheduler())
    
    async def run_scheduler(self):
        """Main scheduler loop that executes tasks at their designated time"""
        self.running = True
        
        while True:
            try:
                # Check if we have any tasks
                if not self.tasks:
                    await asyncio.sleep(5)  # Sleep and check again if no tasks
                    continue
                
                # Get the next task without removing it
                next_task = self.tasks[0]
                execution_time, task_id, callback, args, kwargs = next_task
                
                # Calculate time to wait
                now = time.time()
                wait_time = max(0, execution_time - now)
                
                if wait_time <= 0:
                    # Task is due, remove from queue and execute
                    async with self.task_lock:
                        heapq.heappop(self.tasks)
                        self.task_map.pop(task_id, None)
                    
                    # Execute the task in the background
                    asyncio.create_task(self._execute_task(task_id, callback, args, kwargs))
                else:
                    # Wait until the next task is due (or new task is added)
                    await asyncio.sleep(min(wait_time, 5))  # Check at least every 5 seconds
            except Exception as e:
                logger.error(f"Error in task scheduler: {str(e)}")
                await asyncio.sleep(5)  # Sleep on error to avoid tight loop
    
    async def _execute_task(self, task_id, callback, args, kwargs):
        """Execute a task with error handling"""
        try:
            logger.info(f"Executing task {task_id}")
            await callback(*args, **kwargs)
            logger.info(f"Task {task_id} completed successfully")
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        if task_id not in self.task_map:
            return False
            
        async with self.task_lock:
            # We can't easily remove from heap, so we'll just mark it in the map
            # and skip it when it comes up for execution
            self.task_map.pop(task_id, None)
            
            # Rebuild the heap without the canceled task
            self.tasks = [task for task in self.tasks if task[1] != task_id]
            heapq.heapify(self.tasks)
            
        return True

    def get_pending_task_count(self) -> int:
        """Get number of pending tasks"""
        return len(self.tasks)
        
    async def get_next_execution_time(self) -> Optional[datetime]:
        """Get the timestamp of the next task to execute"""
        if not self.tasks:
            return None
            
        execution_timestamp = self.tasks[0][0]
        return datetime.fromtimestamp(execution_timestamp)

# Global instance of the task scheduler
task_scheduler = TaskScheduler() 