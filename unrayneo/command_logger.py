"""
Centralized command logging functionality.
"""
from datetime import datetime
import hashlib
import subprocess
import threading
from pathlib import Path

def log_command(cmd: str, prefix: str = "cmd") -> int:
    """
    Execute command while logging to secret/command-logs directory.
    Returns command's exit code.
    """
    # Create log directory structure
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cmd_hash = hashlib.md5(cmd.encode()).hexdigest()[:8]
    log_dir = Path(f"secret/command-logs/{today}/{prefix}_{cmd_hash}_{timestamp}")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Save command input
    with open(log_dir/"command.txt", "w") as f:
        f.write(cmd)
    
    # Run command while streaming output to both console and log files
    print(f"Running: {cmd}")
    
    with open(log_dir/"stdout.txt", "w") as stdout_file, \
         open(log_dir/"stderr.txt", "w") as stderr_file:
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Stream stdout/stderr to both console and files
        def stream_output(pipe, file, prefix=""):
            for line in pipe:
                print(prefix + line, end='')
                file.write(line)
                file.flush()
        
        # Start threads for streaming
        stdout_thread = threading.Thread(
            target=stream_output,
            args=(process.stdout, stdout_file))
        stderr_thread = threading.Thread(
            target=stream_output,
            args=(process.stderr, stderr_file, "ERR: "))
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Wait for process to complete
        returncode = process.wait()
        stdout_thread.join()
        stderr_thread.join()
    
    # Save return code
    with open(log_dir/"returncode.txt", "w") as f:
        f.write(str(returncode))
        
    print(f"\nCommand logged to: {log_dir}")
    return returncode
