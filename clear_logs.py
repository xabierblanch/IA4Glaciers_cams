import os

def log_size(file_path):
    # Get the size of the log file in bytes
    log_file_size = os.path.getsize(file_path)

    # Convert bytes to megabytes for easier comparison
    log_file_size_mb = log_file_size / (1024 * 1024)

    # Check if the file size exceeds 1MB
    if log_file_size_mb > 1:
        # Delete the log file if it's too large
        print("Deleting log file due to exceeding 1MB size")
        os.remove(file_path)
    else:
        print(f"{file_path} size within acceptable limit: {log_file_size_mb:.2f} MB")

log_size('IA4G.log')
