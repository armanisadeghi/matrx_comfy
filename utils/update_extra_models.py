#!/usr/bin/env python3

import subprocess
import os
import sys
import yaml
from colorama import init, Fore, Back, Style
import shutil

init()
CLEAR = "clear" if os.name == "posix" else "cls"

BASE_DIR = "/root/matrx_comfy"
SCRIPT_PATH = os.path.join(BASE_DIR, "utils/update_extra_models.py")
CONFIG_PATH = os.path.join(BASE_DIR, "extra_model_paths.yaml")
DOCKERFILE_PATH = BASE_DIR
DEFAULT_CONTAINER_NAME = "matrx-comfy"
DOCKER_PORT = "8189"
VOLUME_MAP_FILE = os.path.join(BASE_DIR, "volume_mappings.yaml")
DOCKER_FLAGS_FILE = os.path.join(BASE_DIR, "docker_flags.yaml")
WORKFLOWS_DIR = "/matrx_comfy/ComfyUI/user/default/workflows"
DOCKER_IMAGE_TAG = "matrx-comfy:latest"

def run_command(command, return_output=False):
    try:
        process = subprocess.run(command, shell=True, check=True, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(Fore.GREEN + process.stdout + Style.RESET_ALL)
        if process.stderr:
            print(Fore.YELLOW + process.stderr + Style.RESET_ALL)
        return process.stdout if return_output else True
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Error running command '{command}': {e}" + Style.RESET_ALL)
        print(Fore.RED + f"Stderr: {e.stderr}" + Style.RESET_ALL)
        return None if return_output else False

def build_docker_image(verbose=False):
    build_cmd = f"docker build -t {DOCKER_IMAGE_TAG} {DOCKERFILE_PATH}"
    print(Fore.CYAN + f"Building Docker image '{DOCKER_IMAGE_TAG}'..." + Style.RESET_ALL)
    if verbose:
        print(Fore.CYAN + "Verbose output enabled. Streaming build logs..." + Style.RESET_ALL)
        process = subprocess.Popen(build_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        while process.poll() is None:
            line = process.stdout.readline()
            if line:
                print(Fore.WHITE + line.strip() + Style.RESET_ALL)
        # Capture any remaining output
        for line in process.stdout:
            print(Fore.WHITE + line.strip() + Style.RESET_ALL)
        if process.returncode != 0:
            print(Fore.RED + "Build failed. Check logs above for details." + Style.RESET_ALL)
            return False
        print(Fore.GREEN + "Build completed successfully." + Style.RESET_ALL)
        return True
    else:
        return run_command(build_cmd)

def get_running_containers(image_tag=None):
    cmd = "docker ps -a --format '{{.Names}} {{.Image}}'" if image_tag else "docker ps --format '{{.Names}}'"
    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
        containers = []
        for line in output.splitlines():
            if image_tag:
                name, image = line.strip().split(maxsplit=1)
                if image == image_tag:
                    containers.append(name)
            else:
                containers.append(line.strip())
        return containers
    except subprocess.CalledProcessError:
        return []

def select_container():
    containers = get_running_containers()
    if not containers:
        print(Fore.YELLOW + "No running containers found. Using default name." + Style.RESET_ALL)
        return DEFAULT_CONTAINER_NAME
    
    print(Fore.CYAN + "\nAvailable running containers:" + Style.RESET_ALL)
    for i, container in enumerate(containers, 1):
        print(f"{i}. {Fore.WHITE}{container}{Style.RESET_ALL}")
    print(f"Default: {Fore.WHITE}{DEFAULT_CONTAINER_NAME}{Style.RESET_ALL}")
    
    while True:
        choice = input(Fore.CYAN + "Select container number (or press Enter for default): " + Style.RESET_ALL)
        if not choice:
            return DEFAULT_CONTAINER_NAME
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(containers):
                return containers[idx]
            print(Fore.RED + "Invalid selection. Try again." + Style.RESET_ALL)
        except ValueError:
            print(Fore.RED + "Please enter a number or press Enter." + Style.RESET_ALL)

def load_volume_mappings():
    if not os.path.exists(VOLUME_MAP_FILE):
        return {}
    with open(VOLUME_MAP_FILE, 'r') as f:
        return yaml.safe_load(f) or {}

def save_volume_mappings(mappings):
    with open(VOLUME_MAP_FILE, 'w') as f:
        yaml.safe_dump(mappings, f)

def load_docker_flags():
    if not os.path.exists(DOCKER_FLAGS_FILE):
        return {"default": ["--gpus all", f"-p {DOCKER_PORT}:8189"]}
    with open(DOCKER_FLAGS_FILE, 'r') as f:
        return yaml.safe_load(f) or {"default": ["--gpus all", f"-p {DOCKER_PORT}:8189"]}

def save_docker_flags(flags):
    with open(DOCKER_FLAGS_FILE, 'w') as f:
        yaml.safe_dump(flags, f)

def map_directory(container_name):
    print(Fore.CYAN + "Mapping a new directory..." + Style.RESET_ALL)
    local_path = input(Fore.CYAN + "Enter local path: " + Style.RESET_ALL)
    dest_path = input(Fore.CYAN + "Enter destination path in container: " + Style.RESET_ALL)
    
    if not os.path.exists(local_path):
        print(Fore.RED + f"Local path {local_path} does not exist." + Style.RESET_ALL)
        return
    
    mappings = load_volume_mappings()
    if container_name not in mappings:
        mappings[container_name] = []
    mappings[container_name].append({"local": local_path, "dest": dest_path})
    save_volume_mappings(mappings)
    print(Fore.GREEN + f"Mapped {local_path} to {dest_path} for {container_name}. Restart container to apply." + Style.RESET_ALL)

def list_mapped_directories(container_name):
    mappings = load_volume_mappings()
    if container_name not in mappings or not mappings[container_name]:
        print(Fore.YELLOW + f"No directories mapped for {container_name}" + Style.RESET_ALL)
        return
    print(Fore.MAGENTA + f"\nMapped directories for {container_name}:" + Style.RESET_ALL)
    for i, mapping in enumerate(mappings[container_name], 1):
        print(Fore.WHITE + f"{i}. {mapping['local']} -> {mapping['dest']}" + Style.RESET_ALL)

def remove_mapped_directory(container_name):
    mappings = load_volume_mappings()
    if container_name not in mappings or not mappings[container_name]:
        print(Fore.YELLOW + f"No directories mapped for {container_name}" + Style.RESET_ALL)
        return
    
    list_mapped_directories(container_name)
    choice = input(Fore.CYAN + "Enter number of mapping to remove (or Enter to cancel): " + Style.RESET_ALL)
    if not choice:
        return
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(mappings[container_name]):
            removed = mappings[container_name].pop(idx)
            save_volume_mappings(mappings)
            print(Fore.GREEN + f"Removed mapping: {removed['local']} -> {removed['dest']}. Restart container to apply." + Style.RESET_ALL)
        else:
            print(Fore.RED + "Invalid selection." + Style.RESET_ALL)
    except ValueError:
        print(Fore.RED + "Please enter a number." + Style.RESET_ALL)

def traverse_directory(container_name):
    mappings = load_volume_mappings().get(container_name, [])
    if not mappings:
        print(Fore.YELLOW + f"No directories mapped for {container_name}" + Style.RESET_ALL)
        return
    
    print(Fore.MAGENTA + f"\nDirectory structure for {container_name} mappings:" + Style.RESET_ALL)
    for mapping in mappings:
        local_path = mapping['local']
        dest_path = mapping['dest']
        print(Fore.WHITE + f"{local_path} -> {dest_path}" + Style.RESET_ALL)
        if os.path.isdir(local_path):
            for item in os.listdir(local_path):
                item_path = os.path.join(local_path, item)
                print(Fore.WHITE + f"  ├── {item}" + Style.RESET_ALL)
                if os.path.isdir(item_path):
                    for subitem in os.listdir(item_path):
                        print(Fore.WHITE + f"  │   └── {subitem}" + Style.RESET_ALL)
        print()

def run_pip_command(container_name):
    print(Fore.CYAN + f"Running pip command in {container_name}..." + Style.RESET_ALL)
    pip_cmd = input(Fore.CYAN + "Enter pip command (e.g., install numpy): " + Style.RESET_ALL)
    full_cmd = f"docker exec {container_name} pip3 {pip_cmd}"
    output = run_command(full_cmd, return_output=True)
    if output:
        print(Fore.GREEN + f"Pip command output:\n{output}" + Style.RESET_ALL)

def copy_workflows(container_name):
    print(Fore.CYAN + "Copying workflows to container..." + Style.RESET_ALL)
    source_dir = input(Fore.CYAN + "Enter local directory with workflows: " + Style.RESET_ALL)
    if not os.path.isdir(source_dir):
        print(Fore.RED + f"{source_dir} is not a valid directory." + Style.RESET_ALL)
        return
    cmd = f"docker cp {source_dir}/. {container_name}:{WORKFLOWS_DIR}"
    run_command(cmd)
    print(Fore.GREEN + f"Copied contents of {source_dir} to {WORKFLOWS_DIR} in {container_name}" + Style.RESET_ALL)

def view_config_contents(source, is_local=True):
    path = CONFIG_PATH if is_local else f"{source}:/matrx_comfy/ComfyUI/extra_model_paths.yaml"
    if is_local and not os.path.exists(path):
        print(Fore.RED + f"{path} not found." + Style.RESET_ALL)
        return None
    try:
        if is_local:
            with open(path, 'r') as f:
                content = yaml.safe_load(f)
        else:
            cmd = f"docker cp {path} - | tar -xO"
            content = yaml.safe_load(subprocess.check_output(cmd, shell=True))
        print(Fore.MAGENTA + f"\nContents of {'local' if is_local else 'container'} extra_model_paths.yaml:" + Style.RESET_ALL)
        print(Fore.WHITE + yaml.dump(content, default_flow_style=False) + Style.RESET_ALL)
        return content
    except Exception as e:
        print(Fore.RED + f"Error reading config: {e}" + Style.RESET_ALL)
        return None

def build_docker():
    print(Fore.CYAN + Back.BLACK + "Building Docker image..." + Style.RESET_ALL)
    verbose = input(Fore.CYAN + "Show verbose build output? (y/n, default n): " + Style.RESET_ALL).lower() == 'y'
    build_docker_image(verbose=verbose)

def copy_config_to_container(container_name):
    print(Fore.CYAN + f"Copying local extra_model_paths.yaml into {container_name}..." + Style.RESET_ALL)
    if not os.path.exists(CONFIG_PATH):
        print(Fore.RED + f"Error: {CONFIG_PATH} not found. Please create it first." + Style.RESET_ALL)
        return
    old_content = view_config_contents(container_name, is_local=False)
    copy_cmd = f"docker cp {CONFIG_PATH} {container_name}:/matrx_comfy/ComfyUI/extra_model_paths.yaml"
    run_command(copy_cmd)
    new_content = view_config_contents(container_name, is_local=False)
    if old_content and new_content:
        print(Fore.YELLOW + "Previous content:" + Style.RESET_ALL)
        print(Fore.YELLOW + yaml.dump(old_content, default_flow_style=False) + Style.RESET_ALL)
        print(Fore.GREEN + "New content:" + Style.RESET_ALL)
        print(Fore.GREEN + yaml.dump(new_content, default_flow_style=False) + Style.RESET_ALL)
    print(Fore.GREEN + f"Replaced {container_name}'s extra_model_paths.yaml with {CONFIG_PATH}" + Style.RESET_ALL)

def update_local_config(container_name):
    print(Fore.CYAN + f"Updating local extra_model_paths.yaml from {container_name}..." + Style.RESET_ALL)
    old_content = view_config_contents(None, is_local=True)
    copy_cmd = f"docker cp {container_name}:/matrx_comfy/ComfyUI/extra_model_paths.yaml {CONFIG_PATH}"
    run_command(copy_cmd)
    new_content = view_config_contents(None, is_local=True)
    if old_content and new_content:
        print(Fore.YELLOW + "Previous local content:" + Style.RESET_ALL)
        print(Fore.YELLOW + yaml.dump(old_content, default_flow_style=False) + Style.RESET_ALL)
        print(Fore.GREEN + "New local content:" + Style.RESET_ALL)
        print(Fore.GREEN + yaml.dump(new_content, default_flow_style=False) + Style.RESET_ALL)
    print(Fore.GREEN + f"Updated {CONFIG_PATH} from {container_name}" + Style.RESET_ALL)

def run_container(container_name):
    print(Fore.CYAN + f"Starting Docker container {container_name}..." + Style.RESET_ALL)
    if not os.path.exists(CONFIG_PATH):
        print(Fore.RED + f"Error: Please create {CONFIG_PATH} first" + Style.RESET_ALL)
        return
    
    if not run_command(f"docker image inspect {DOCKER_IMAGE_TAG} >/dev/null 2>&1"):
        print(Fore.RED + f"Image '{DOCKER_IMAGE_TAG}' not found. Please build it first (option 1 or 13)." + Style.RESET_ALL)
        return
    
    mappings = load_volume_mappings().get(container_name, [])
    volume_args = " ".join(f"-v {m['local']}:{m['dest']}" for m in mappings)
    flags = load_docker_flags().get(container_name, load_docker_flags()["default"])
    flag_args = " ".join(flags)
    
    print(Fore.CYAN + f"Removing existing container {container_name} if it exists..." + Style.RESET_ALL)
    run_command(f"docker rm -f {container_name} 2>/dev/null")
    
    run_cmd = (
        f"docker run -d {flag_args} "
        f"-v {CONFIG_PATH}:/matrx_comfy/ComfyUI/extra_model_paths.yaml "
        f"{volume_args} "
        f"--name {container_name} {DOCKER_IMAGE_TAG}"
    )
    print(Fore.CYAN + f"Running command: {run_cmd}" + Style.RESET_ALL)
    if run_command(run_cmd):
        print(Fore.GREEN + Back.BLUE + f"Container running at http://localhost:{DOCKER_PORT}" + Style.RESET_ALL)
    else:
        print(Fore.RED + "Failed to start container. Check error above." + Style.RESET_ALL)

def build_and_run_docker(container_name):
    print(Fore.CYAN + Back.BLACK + f"Building and Running Docker image '{DOCKER_IMAGE_TAG}'..." + Style.RESET_ALL)
    
    # Check for existing containers using this image
    existing_containers = get_running_containers(DOCKER_IMAGE_TAG)
    if existing_containers:
        print(Fore.YELLOW + f"\nFound existing containers using '{DOCKER_IMAGE_TAG}':" + Style.RESET_ALL)
        for i, cont in enumerate(existing_containers, 1):
            print(f"{i}. {Fore.WHITE}{cont}{Style.RESET_ALL}")
        choice = input(Fore.CYAN + "Replace all existing containers? (y/n): " + Style.RESET_ALL).lower()
        if choice != 'y':
            print(Fore.YELLOW + "Build and run cancelled." + Style.RESET_ALL)
            return
    
    # Build the image with verbose option
    verbose = input(Fore.CYAN + "Show verbose build output? (y/n, default n): " + Style.RESET_ALL).lower() == 'y'
    if not build_docker_image(verbose=verbose):
        print(Fore.RED + "Failed to build Docker image. Aborting." + Style.RESET_ALL)
        return
    
    # Stop and remove existing containers if any
    if existing_containers:
        print(Fore.CYAN + "Stopping and removing existing containers..." + Style.RESET_ALL)
        for cont in existing_containers:
            run_command(f"docker stop {cont}")
            run_command(f"docker rm {cont}")
    
    # Run the new container
    run_container(container_name)

def main():
    os.system(CLEAR)
    print(Fore.MAGENTA + Back.WHITE + " Welcome to Matrx ComfyUI Docker Manager! " + Style.RESET_ALL)
    
    container_name = select_container()
    print(Fore.GREEN + Back.BLACK + f" Using container: {container_name} " + Style.RESET_ALL)
    
    # Initialize default flags if not set
    flags = load_docker_flags()
    if container_name not in flags and container_name == DEFAULT_CONTAINER_NAME:
        flags[container_name] = ["--gpus all", f"-p {DOCKER_PORT}:8189"]
        save_docker_flags(flags)
    
    while True:
        print(Fore.CYAN + "\nWhat would you like to do?" + Style.RESET_ALL)
        print(Fore.WHITE + "1. Build Docker image" + Style.RESET_ALL)
        print(Fore.WHITE + "2. Run/Update container" + Style.RESET_ALL)
        print(Fore.WHITE + "3. Copy local config to container" + Style.RESET_ALL)
        print(Fore.WHITE + "4. Update local config from container" + Style.RESET_ALL)
        print(Fore.WHITE + "5. View local config contents" + Style.RESET_ALL)
        print(Fore.WHITE + "6. View container config contents" + Style.RESET_ALL)
        print(Fore.WHITE + "7. Map a directory" + Style.RESET_ALL)
        print(Fore.WHITE + "8. List mapped directories" + Style.RESET_ALL)
        print(Fore.WHITE + "9. Run pip command in container" + Style.RESET_ALL)
        print(Fore.WHITE + "10. Remove a mapped directory" + Style.RESET_ALL)
        print(Fore.WHITE + "11. Traverse mapped directories" + Style.RESET_ALL)
        print(Fore.WHITE + "12. Copy workflows to container" + Style.RESET_ALL)
        print(Fore.WHITE + "13. Build and Run Docker image" + Style.RESET_ALL)
        print(Fore.WHITE + "14. Exit" + Style.RESET_ALL)
        
        choice = input(Fore.CYAN + "Enter your choice (1-14): " + Style.RESET_ALL)
        
        if choice == "1":
            build_docker()
        elif choice == "2":
            run_container(container_name)
        elif choice == "3":
            copy_config_to_container(container_name)
        elif choice == "4":
            update_local_config(container_name)
        elif choice == "5":
            view_config_contents(None, is_local=True)
        elif choice == "6":
            view_config_contents(container_name, is_local=False)
        elif choice == "7":
            map_directory(container_name)
        elif choice == "8":
            list_mapped_directories(container_name)
        elif choice == "9":
            run_pip_command(container_name)
        elif choice == "10":
            remove_mapped_directory(container_name)
        elif choice == "11":
            traverse_directory(container_name)
        elif choice == "12":
            copy_workflows(container_name)
        elif choice == "13":
            build_and_run_docker(container_name)
        elif choice == "14":
            print(Fore.MAGENTA + Back.WHITE + " Goodbye! " + Style.RESET_ALL)
            break
        else:
            print(Fore.RED + "Invalid choice, please try again" + Style.RESET_ALL)

if __name__ == "__main__":
    main()