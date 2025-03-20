#!/usr/bin/env python3
import os
import sys
import time
import argparse
import json
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict
import curses
from threading import Thread, Event

@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    message: str
    task: Optional[str] = None
    error: Optional[str] = None

class LogReader:
    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = log_dir
        self.log_pattern = re.compile(
            r'\[(.*?)\: (\w+)\] (?:\[(.*?)\] )?(.+)'
        )

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """Parse a log line into structured data"""
        try:
            match = self.log_pattern.match(line.strip())
            if match:
                timestamp_str, level, task, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                return LogEntry(timestamp, level, message, task)
        except Exception as e:
            print(f"Error parsing line: {e}", file=sys.stderr)
        return None

    def read_logs(self, 
                 filenames: List[str], 
                 level_filter: Optional[str] = None,
                 task_filter: Optional[str] = None,
                 since: Optional[datetime] = None,
                 search: Optional[str] = None) -> List[LogEntry]:
        """Read and filter log entries"""
        entries = []
        
        for filename in filenames:
            try:
                filepath = os.path.join(self.log_dir, filename)
                with open(filepath, 'r') as f:
                    for line in f:
                        entry = self.parse_line(line)
                        if entry:
                            # Apply filters
                            if level_filter and entry.level != level_filter:
                                continue
                            if task_filter and entry.task != task_filter:
                                continue
                            if since and entry.timestamp < since:
                                continue
                            if search and search.lower() not in entry.message.lower():
                                continue
                            entries.append(entry)
            except Exception as e:
                print(f"Error reading {filename}: {str(e)}", file=sys.stderr)
        
        return sorted(entries, key=lambda x: x.timestamp)

class LogMonitor:
    def __init__(self, reader: LogReader):
        self.reader = reader
        self.stop_event = Event()
        self.stats = defaultdict(int)

    def update_display(self, stdscr, entries: List[LogEntry]):
        """Update the curses display with log entries"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Show stats in header
        header = f" Log Monitor | Entries: {len(entries)} | ERROR: {self.stats['ERROR']} | INFO: {self.stats['INFO']} "
        stdscr.addstr(0, 0, header.center(width, '-'))
        
        # Show entries
        current_line = 1
        for entry in entries[-height+3:]:  # Leave room for header and footer
            if current_line >= height - 1:
                break
                
            # Format entry
            timestamp = entry.timestamp.strftime('%H:%M:%S')
            level_color = curses.A_BOLD if entry.level == 'ERROR' else curses.A_NORMAL
            
            try:
                stdscr.addstr(current_line, 0, timestamp)
                stdscr.addstr(current_line, 9, f"[{entry.level}]", level_color)
                if entry.task:
                    stdscr.addstr(current_line, 18, f"[{entry.task}]")
                message = entry.message[:width-30] # Truncate if too long
                stdscr.addstr(current_line, 30, message)
                current_line += 1
            except curses.error:
                pass  # Ignore errors from writing outside window
        
        # Show footer
        footer = " Press 'q' to quit | 'c' to clear | 'f' to filter "
        stdscr.addstr(height-1, 0, footer.center(width, '-'))
        stdscr.refresh()

    def monitor(self, stdscr, filenames: List[str], interval: int = 1):
        """Monitor logs in real-time"""
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        
        while not self.stop_event.is_set():
            entries = self.reader.read_logs(filenames)
            
            # Update stats
            self.stats.clear()
            for entry in entries:
                self.stats[entry.level] += 1
            
            self.update_display(stdscr, entries)
            time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description='Read and monitor Celery logs')
    parser.add_argument('--files', nargs='+', default=['celery.log', 'celery_worker.log'],
                      help='Log files to read')
    parser.add_argument('--level', choices=['INFO', 'ERROR', 'WARNING'],
                      help='Filter by log level')
    parser.add_argument('--task', help='Filter by task name')
    parser.add_argument('--hours', type=int, help='Show logs from last N hours')
    parser.add_argument('--search', help='Search string in messages')
    parser.add_argument('--watch', action='store_true', help='Monitor logs in real-time')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    reader = LogReader()
    since = None
    if args.hours:
        since = datetime.now() - timedelta(hours=args.hours)
    
    if args.watch:
        monitor = LogMonitor(reader)
        curses.wrapper(lambda stdscr: monitor.monitor(stdscr, args.files))
    else:
        entries = reader.read_logs(
            args.files,
            level_filter=args.level,
            task_filter=args.task,
            since=since,
            search=args.search
        )
        
        if args.json:
            output = [{
                'timestamp': entry.timestamp.isoformat(),
                'level': entry.level,
                'task': entry.task,
                'message': entry.message
            } for entry in entries]
            print(json.dumps(output, indent=2))
        else:
            for entry in entries:
                task_info = f"[{entry.task}] " if entry.task else ""
                print(f"[{entry.timestamp}] [{entry.level}] {task_info}{entry.message}")

if __name__ == '__main__':
    main()