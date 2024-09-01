import argparse
import docker
import io
import os
import sys
import tarfile


# Parse Arguments
parser = argparse.ArgumentParser(description="Compile a C file using the pre-2.34 glibc ABI")
parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')
parser.add_argument('filename', type=str, help='The C file to compile')
args = parser.parse_args()

IMAGE_NAME = 'gcc_old_libc:latest'

client = docker.from_env()
local_file_path = sys.argv[1]
src_filename = os.path.basename(local_file_path)
container_file_path = f'/root/{src_filename}'

# create image if it does not exist
image_exists = any(img.tags for img in client.images.list() if IMAGE_NAME in img.tags)

if not image_exists:
    print(f'Image {IMAGE_NAME} does not exist - building...')

    try:
        image, logs = client.images.build(path='.', tag=IMAGE_NAME)
        
        if args.verbose:
            for log in logs:
                if 'stream' in log:
                    print(log['stream'].strip())
        
        print(f'Image {IMAGE_NAME} has been built successfully')
    except Exception as e:
        print(f'Error occurred while building the image: {e}')
else:
    print(f'Image {IMAGE_NAME} already exists, skipping the build process')


# Create container from image
container = client.containers.create(IMAGE_NAME, command='/bin/bash', tty=True)
container.start()

# Copy main.c to container
print(f'Copying {local_file_path} to the container...')

data = io.BytesIO()
with tarfile.open(fileobj=data, mode='w') as tar:
    tar.add(local_file_path, arcname=container_file_path)
data.seek(0)

# Step 5: Put the tarball into the container
try:
    container.put_archive('/', data)
    print("File copied successfully.")
except Exception as e:
    print(f"Error copying file to container: {e}")

# Compile main.c
print('Compiling main.c inside the container...')
compile_command = container.exec_run(f'gcc /root/{src_filename} -o /root/a.out', tty=True)
print(compile_command.output.decode())

# Copy compiled binary to host
print('Copying the compiled output back to the host...')
stream, stat = container.get_archive('/root/a.out')

# Stop container
container.stop()
container.remove()

# Extract from tar archive
tar_buffer = io.BytesIO()

for chunk in stream:
    tar_buffer.write(chunk)

tar_buffer.seek(0)

with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
    tar.extract('a.out', path='.')

print('Compilation complete')
print('File: a.out')
