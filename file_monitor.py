#!/usr/bin/env python3

import time, sys, re, requests, warnings
from urllib3.exceptions import InsecureRequestWarning
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileMonitor(FileSystemEventHandler):
    def __init__(self, filename, operator, keywords):
        self.filename = filename
        self.operator = operator
        self.keywords = keywords
        self.file = open(filename, 'r')
        self.file.seek(0, 2)  # Move to end of file
    
    def on_modified(self, event):
        if event.src_path.endswith(self.filename):
            if self.operator == 'and':
                self.and_check_new_lines()

            self.or_check_new_lines()
 

    def analyze_string(self, log_string):
        keys_to_find = {'node', 'ppid', 'pid', 'exe'}
        pattern = re.compile(r'(\w+)=(?:"([^"]*)"|\\"([^"]*)\\"|([^ ]+))')
        results = {}
        
        # Iterate over all matches found in the string
        for match in pattern.finditer(log_string):
            key = match.group(1)
        
            # If this is a key we care about
            if key in keys_to_find:
                # The value will be in group 2, 3, or 4.
                # This finds the first non-None group from [g2, g3, g4].
                value = next(g for g in match.groups()[1:] if g is not None)
                results[key] = value

        # Vefify if all required keys were found
        if len(results) == len(keys_to_find):
            # All keys were found, return the dictionary
            return results
        else:
            # One or more keys were missing, return empty
            return {}

    def send_webook(self, payload):
        # --- 1. Define Request Details ---
        url = "https://192.168.122.20/eda-event-streams/api/eda/v1/external_event_stream/2c769b47-7d3c-418e-95ae-437a7b3fd677/post/"
        
        # -u jin:redhat
        auth = ('jin', 'redhat')
        
        # --- 2. Suppress SSL Warning (for -k) ---
        # The -k flag in curl disables SSL certificate checks.
        # In 'requests', this is verify=False, which will print a warning.
        # This line disables that specific warning.
        warnings.simplefilter('ignore', InsecureRequestWarning)
        
        # --- 3. Make the POST Request ---
        try:
            response = requests.post(
                url,
                json=payload,  # Handles -H "Content-Type: application/json" and -d
                auth=auth,     # Handles -u jin:redhat
                verify=False   # Handles -k (insecure)
            )
        
            # --- 4. Print the Server's Response ---
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
        
        except requests.exceptions.ConnectionError as e:
            print(f"Connection Error: Could not connect to {url}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

    def or_check_new_lines(self):
        while True:
            line = self.file.readline()
            if line:
                line_lower = line.lower()
                for keyword in self.keywords:
                    if keyword.lower() in line_lower:
                        print(f"[{keyword}] {line.strip()}")
                        print('--'*40)
                        result = self.analyze_string(line.strip())
                        if result:
                            print(f"{result}")
                            self.send_webook(result)
                        break
            else:
                break

    def and_check_new_lines(self):
        while True:
            line = self.file.readline()
            if line:
                line_lower = line.lower()
                
                # Check if ALL keywords are present in the line
                if all(keyword.lower() in line_lower for keyword in self.keywords):
                    # If all keywords were found, print the line
                    print(line.strip())
                    
            else:
                # End of file, break the loop
                break
    
    def close(self):
        self.file.close()

def monitor_with_watchdog(filename, operator, keywords):
    """
    Monitor file using watchdog library for better performance.
    Install: pip install watchdog
    """
    import os
    
    print(f"Monitoring {filename} for keywords: {keywords}")
    print("Press Ctrl+C to stop\n")
    
    event_handler = FileMonitor(filename, operator, keywords)
    #event_handler = FileMonitor(os.path.basename(filename), keywords)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(filename) or '.', recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        event_handler.close()
    
    observer.join()

if __name__ == "__main__":
    # --- Error Checking ---
    # We need at least 4 arguments:
    # 1. (sys.argv[0]) The script name (./monitor-02.py)
    # 2. (sys.argv[1]) The log file (/tmp/log)
    # 3. (sys.argv[2]) The operator (or)
    # 4. (sys.argv[3]) At least one keyword (ERROR)
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <log_file> <or|and> <keyword1> [keyword2] ...")
        print("Error: Not enough arguments provided.")
        sys.exit(1) # Exit with a non-zero status to indicate an error
    
    # --- Argument Parsing ---
    
    # The script name is sys.argv[0]
    
    # 1. First arg is a string '/tmp/log'
    log_file = sys.argv[1]
    
    # 2. Second arg is a string 'or'
    operator = sys.argv[2]
    
    # 3. The 3rd "argument" is a list of all the rest
    # We use list slicing to get everything from index 3 to the end.
    keywords = sys.argv[3:]

    monitor_with_watchdog(log_file, operator, keywords)
