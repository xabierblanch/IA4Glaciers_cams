from datetime import datetime
import RPi.GPIO as GPIO

def _print(message):
    current_time = datetime.now()
    formatted_time = current_time.strftime("[%d/%m/%Y - %H:%M:%S]")
    print(f"{formatted_time} :: {message}")

def select_function(now):
    if now.minute in (0,1,2,3,4,5):
        maintenance_mode = False
        _print(f"Maintance mode = False -> {num_of_pics} images will be captured")
    else:
        maintenance_mode = True
        _print(f"Maintance mode = True -> no images will be captured")
        _print(f"Maintance mode - Remember to shutdown the system after the maintance")
    return maintenance_mode

def shutdown():
    try:
        _print("Shutdown command recieved")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.OUT)
        GPIO.output(4, GPIO.LOW)
        _print("GPIO Shutdown executed successfully")
    except Exception as e:
        _print(f"ERROR: executing GPIO commands: {e}")
    finally:
        GPIO.cleanup()
        
if __name__ == "__main__":
    now = datetime.now()
    maintenance_mode = select_function(now)
    if not maintenance_mode:
        shutdown()