import subprocess
import shutil


def install():
    print("Running post-installation script")
    source = 'yeelightble.service'
    destination = f'/etc/systemd/system/{source}'
    user_input = input("Do you want to install yeelightble as systemd service? (Yes/no): ")

    if user_input.lower() == 'yes':
        # Additional setup code
        print("Performing additional setup...")
        shutil.copyfile(source, destination)
        # Reload systemd to recognize the new service
        subprocess.call(['systemctl', 'daemon-reload'])
        # Enable and start the service
        subprocess.call(['systemctl', 'enable', 'yeelightble.service'])
        subprocess.call(['systemctl', 'status', 'yeelightble.service'])
        subprocess.call(['systemctl', 'start', 'yeelightble.service'])
