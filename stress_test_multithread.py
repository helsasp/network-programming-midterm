import socket
import json
import base64
import os
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

srv_addr = ('127.0.0.1', 13337)

def execute_command(cmd_str):
    try:
        with socket.create_connection(srv_addr, timeout=300) as s:
            s.sendall(cmd_str.encode())

            resp_data = b""
            end_flag = b"\r\n\r\n"
            while True:
                part = s.recv(2**20)
                if not part:
                    break
                resp_data += part
                if end_flag in resp_data[-8:]:
                    break

            response = resp_data.decode().strip()
            return json.loads(response)
    except Exception as err:
        print(f"Connection error: {err}")
        return {"status": "ERROR", "message": str(err)}

def fetch_list():
    cmd = "LIST\r\n\r\n"
    result = execute_command(cmd)
    if result['status'] == 'OK':
        print("\nAvailable Files List:")
        for fname in result['data']:
            print(f"  • {fname}")
        print()
        return True, "Success"
    else:
        print(f"Failed LIST: {result.get('data', 'Unknown error')}")
        return False, "Failed"

def fetch_file(fname=""):
    cmd = f"GET {fname}\r\n\r\n"
    print(f"Fetching file: {fname}...")

    t_start = time.time()
    result = execute_command(cmd)
    t_end = time.time()

    print(f"Response in {t_end - t_start:.2f} seconds")

    if result['status'] == 'OK':
        out_fname = result['data_namafile']
        decoded = base64.b64decode(result['data_file'])
        with open(out_fname, 'wb') as file:
            file.write(decoded)
        print(f"Downloaded {fname} ({len(decoded)} bytes)")
        return True, "Success"
    else:
        print(f"Failed GET: {result.get('data', 'Unknown error')}")
        return False, "Failed"

def upload_file(fname=""):
    if not os.path.exists(fname):
        print(f"File {fname} not found.")
        return False, "File not found"

    with open(fname, 'rb') as f:
        content = f.read()

    b64_content = base64.b64encode(content).decode()
    cmd = f"ADD {fname} {b64_content}\r\n\r\n"

    print(f"Uploading file: {fname} ({len(content)} bytes)...")

    t_start = time.time()
    result = execute_command(cmd)
    t_end = time.time()

    print(f"Response in {t_end - t_start:.2f} seconds")

    if result['status'] == 'OK':
        print(f"Uploaded {fname}")
        return True, "Success"
    else:
        print(f"Failed ADD: {result.get('data', 'Unknown error')}")
        return False, "Failed"

def perform_task(job, fname):
    t0 = time.time()
    print(f"--> {job.upper()} started for {fname}")
    if job == "upload":
        success, msg = upload_file(fname)
    else:
        success, msg = fetch_file(fname)
    t1 = time.time()
    volume = os.path.getsize(fname) if os.path.exists(fname) else 0
    duration = t1 - t0
    return {
        "task": job,
        "filename": fname,
        "success": success,
        "time": duration,
        "throughput": volume / duration if success and duration > 0 else 0,
        "message": msg if not success else "OK"
    }

def simulate_test(task, fname, number_client_pool, number_server_pool=50):
    print(f"\nRunning {task.upper()} | File: {fname} | Clients: {number_client_pool}, Server Threads: {number_server_pool}")
    client_data = []

    t_global_start = time.time()
    with ThreadPoolExecutor(max_workers=number_client_pool) as pool:
        futures = [pool.submit(perform_task, task, fname) for _ in range(number_client_pool)]
        for f in tqdm(futures):
            client_data.append(f.result())
    t_global_end = time.time()

    total_time = sum(d['time'] for d in client_data)
    time_client = total_time / number_client_pool if number_client_pool > 0 else 0

    client_success = sum(1 for d in client_data if d['success'])
    client_fail = number_client_pool - client_success

    total_tp = sum(d['throughput'] for d in client_data if d['success'])
    throughput_client = total_tp / client_success if client_success else 0

    return {
        "task": task,
        "file": fname,
        "client_pool": "thread",
        "server_pool": number_server_pool,
        "clients": number_client_pool,
        "client_success": client_success,
        "client_fail": client_fail,
        "server_success": client_success,
        "server_fail": client_fail,
        "total_time": round(t_global_end - t_global_start, 2),
        "avg_client_time": round(time_client, 2),
        "avg_throughput": round(throughput_client, 2)
    }

def generate_files():
    size_map = {
        "10MB.bin": 10 * 1024 * 1024,
        "50MB.bin": 50 * 1024 * 1024,
        "100MB.bin": 100 * 1024 * 1024,
    }
    for fname, size in size_map.items():
        if not os.path.exists(fname):
            print(f"Creating {fname}...")
            with open(fname, 'wb') as f:
                f.write(os.urandom(size))

def save_results(results):
    csv_path = "multithread_result.csv"
    file_exists = os.path.isfile(csv_path) and os.path.getsize(csv_path) > 0
    row_start = 1
    if file_exists:
        try:
            with open(csv_path, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    last_line = lines[-1].strip()
                    if last_line:
                        try:
                            row_start = int(last_line.split(',')[0]) + 1
                        except:
                            row_start = 1
        except Exception as err:
            print(f"Warning reading CSV: {err}, starting from 1.")

    for i, d in enumerate(results):
        d["number"] = row_start + i

    with open(csv_path, 'a' if file_exists else 'w') as f:
        if not file_exists:
            f.write("number,operation,volume,number_client_pool,number_server_pool,time_client,throughput_client,client_success,client_fail,server_success,server_fail\n")
        for d in results:
            f.write(f"{d['number']},{d['task']},{d['file']},{d['clients']},{d['server_pool']},{d['avg_client_time']},{d['avg_throughput']},{d['client_success']},{d['client_fail']},{d['server_success']},{d['server_fail']}\n")

    print(f"✅ Results saved to {csv_path} (rows {results[0]['number']} to {results[-1]['number']})")

# Tambahan fungsi LIST dengan concurrency
def perform_list_test(fname, number_client_pool, number_server_pool=50):
    print(f"\nRunning LIST | File: {fname} | Clients: {number_client_pool}, Server Threads: {number_server_pool}")

    t_start = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=number_client_pool) as pool:
        futures = [pool.submit(fetch_list) for _ in range(number_client_pool)]
        for f in futures:
            results.append(f.result())
    t_end = time.time()

    success_count = sum(1 for r in results if r[0] == True)
    fail_count = number_client_pool - success_count

    total_time = t_end - t_start
    avg_time = total_time / number_client_pool if number_client_pool > 0 else 0

    throughput = 0.01  # dummy throughput

    return {
        "task": "list",
        "file": fname,
        "client_pool": "thread",
        "server_pool": number_server_pool,
        "clients": number_client_pool,
        "client_success": success_count,
        "client_fail": fail_count,
        "server_success": success_count,
        "server_fail": fail_count,
        "total_time": round(total_time, 2),
        "avg_client_time": round(avg_time, 2),
        "avg_throughput": throughput
    }

def run_list_operations_and_save():
    size_files = ["10MB.bin", "50MB.bin", "100MB.bin"]
    client_counts = [1, 5, 50]
    server_pool = 50
    results_list = []

    for fname in size_files:
        for c in client_counts:
            res = perform_list_test(fname, c, server_pool)
            results_list.append(res)

    save_results(results_list)

def main():
    generate_files()
    tasks = [
        (t, f, c)
        for t in ["download", "upload"]
        for f in ["10MB.bin", "50MB.bin", "100MB.bin"]
        for c in [1, 5, 50]
    ]

    final_results = []
    for job, fname, client_count in tasks:
        outcome = simulate_test(job, fname, client_count)
        final_results.append(outcome)

    save_results(final_results)

if __name__ == '__main__':
    main()
    run_list_operations_and_save()
