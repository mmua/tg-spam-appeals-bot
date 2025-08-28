#!/usr/bin/env python3
"""Healthcheck script for the Appeals Bot."""

import os
import sys
import psutil


def check_bot_process() -> bool:
    """Check if the bot process is actually running."""
    try:
        # Look for python process running appeals_bot.main
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python':
                    cmdline = proc.info['cmdline']
                    if cmdline and len(cmdline) >= 2:
                        # Check if it's running our bot module
                        if 'appeals_bot.main' in ' '.join(cmdline):
                            print(f"✅ Bot process found (PID: {proc.info['pid']})")
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print("❌ Bot process not found")
        return False
        
    except Exception as e:
        print(f"❌ Process check failed: {e}")
        return False


def main() -> None:
    """Main healthcheck function."""
    try:
        is_healthy = check_bot_process()
        sys.exit(0 if is_healthy else 1)
    except Exception as e:
        print(f"❌ Healthcheck error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
