#!/usr/bin/env python3
"""
Script to start RQ workers
"""
import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.score_worker import start_score_worker
from workers.blockchain_worker import start_blockchain_worker
from workers.batch_worker import start_batch_worker


def main():
    parser = argparse.ArgumentParser(description="Start RQ worker")
    parser.add_argument(
        "worker_type",
        choices=["score", "blockchain", "batch", "all"],
        help="Type of worker to start"
    )
    
    args = parser.parse_args()
    
    if args.worker_type == "score":
        start_score_worker()
    elif args.worker_type == "blockchain":
        start_blockchain_worker()
    elif args.worker_type == "batch":
        start_batch_worker()
    elif args.worker_type == "all":
        # Start all workers (in production, use separate processes)
        import multiprocessing
        
        processes = []
        for worker_func in [start_score_worker, start_blockchain_worker, start_batch_worker]:
            p = multiprocessing.Process(target=worker_func)
            p.start()
            processes.append(p)
        
        # Wait for all processes
        for p in processes:
            p.join()


if __name__ == "__main__":
    main()

