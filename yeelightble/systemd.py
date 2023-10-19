import subprocess
import shutil
import os

service_file = './yeelightble.service'

# Copy the service file to the systemd directory
destination = '/etc/systemd/system/yeelightble.service'
shutil.copyfile(service_file, destination)

# Reload systemd to recognize the new service
subprocess.call(['systemctl', 'daemon-reload'])

# Enable and start the service
subprocess.call(['systemctl', 'enable', 'yeelightble.service'])
subprocess.call(['systemctl', 'status', 'yeelightble.service'])
subprocess.call(['systemctl', 'start', 'yeelightble.service'])
