import asyncio
import logging
import random
import sys

from automation_server_client import AutomationServer, Workqueue, WorkItemError, WorkItemStatus


async def process_run():
    logger = logging.getLogger(__name__)

    # Read mode from CLI args
    mode = "random"
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    logger.info(f"Running incident test with mode: {mode}")

    if mode == "exception":
        raise RuntimeError("Simulated exception failure")

    elif mode == "exit":
        logger.error("Simulated hard exit")
        sys.exit(1)

    elif mode == "soft":
        raise WorkItemError("Simulated business error")

    elif mode == "random":
        choice = random.choice(["exception", "exit", "soft"])
        logger.info(f"Randomly selected: {choice}")
        if choice == "exception":
            raise RuntimeError("Random exception failure")
        elif choice == "exit":
            sys.exit(1)
        else:
            raise WorkItemError("Random soft failure")

    else:
        logger.info("Success case (no failure)")


async def process_workqueue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    for item in workqueue:
        with item:
            try:
                await process_run()
            except WorkItemError as e:
                logger.error(f"Soft error: {e}")
                item.fail(str(e))
            except Exception as e:
                logger.exception(f"Hard failure: {e}")
                raise


if __name__ == "__main__":
    ats = AutomationServer.from_environment()
    workqueue = ats.workqueue()

    # Queue mode (unchanged template behavior)
    if "--queue" in sys.argv:
        workqueue.clear_workqueue(WorkItemStatus.NEW)
        exit(0)

    # Process mode (manual / trigger execution)
    if "--process" in sys.argv:
        asyncio.run(process_run())
        exit(0)

    # Default: workqueue processing
    asyncio.run(process_workqueue(workqueue))
