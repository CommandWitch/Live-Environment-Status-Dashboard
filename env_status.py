import time
import datetime
import logging
import psutil
import psycopg2
from psycopg2 import Error

# 1. Set up professional logging instead of just using standard print statements
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database configuration dictionary
DB_CONFIG = {
    "host": "localhost",
    "database": "local_env_db", # Ensure you create this database in Postgres first!
    "user": "postgres",
    "password": "KayakBeauty50!"
}

def init_database():
    """Creates the metrics table if it does not already exist."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS server_health (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP NOT NULL,
        cpu_usage_percent REAL NOT NULL,
        ram_usage_percent REAL NOT NULL,
        disk_free_gb REAL NOT NULL,
        status_flag VARCHAR(20) NOT NULL
    );
    """
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_table_query)
                conn.commit()
                logging.info("Database initialized successfully.")
    except Error as e:
        logging.error(f"Error initializing database: {e}")

def gather_metrics():
    """Uses psutil to extract physical machine metrics."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    # Calculate free disk space in Gigabytes
    disk_info = psutil.disk_usage('/')
    disk_free_gb = round(disk_info.free / (1024 ** 3), 2)
    
    # Simple alert logic framework
    status = "HEALTHY"
    if cpu > 85.0 or ram > 90.0:
        status = "WARNING_HIGH_LOAD"
        
    return datetime.datetime.now(), cpu, ram, disk_free_gb, status

def log_metrics_to_db(timestamp, cpu, ram, disk, status):
    """Inserts a telemetry row into the PostgreSQL instance."""
    insert_query = """
    INSERT INTO server_health (timestamp, cpu_usage_percent, ram_usage_percent, disk_free_gb, status_flag)
    VALUES (%s, %s, %s, %s, %s);
    """
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(insert_query, (timestamp, cpu, ram, disk, status))
                conn.commit()
                logging.info(f"Logged health status: {status} (CPU: {cpu}%, RAM: {ram}%)")
    except Error as e:
        logging.error(f"Failed to write metrics to database: {e}")

def main():
    init_database()
    logging.info("Starting system monitoring loop. Press Ctrl+C to exit.")
    
    try:
        while True:
            timestamp, cpu, ram, disk_free, status = gather_metrics()
            log_metrics_to_db(timestamp, cpu, ram, disk_free, status)
            
            # Wait 10 seconds before collecting the next data point
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Monitoring loop stopped by user.")

if __name__ == "__main__":
    main()
