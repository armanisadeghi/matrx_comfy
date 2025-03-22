Here's a full, **project-specific** `README.md` file based on your Dockerfile, detailing everything a user would need to understand, build, and run the repository correctly:

---

```md
# ComfyUI Custom Dockerized Environment

This repository provides a complete, GPU-accelerated Docker environment for running **ComfyUI** along with a curated set of powerful community plugins and custom nodes.

It is built on `nvidia/cuda:12.4.0-runtime-ubuntu22.04` and designed for users with NVIDIA GPUs and CUDA 12.4-compatible drivers.

---

## 🚀 Features

- ✅ **CUDA 12.4** GPU support
- 🛠️ **Rust toolchain** for compiling Python packages with native extensions
- 📦 Pre-installed ComfyUI and ComfyUI-Manager
- 🧩 Includes over a dozen custom ComfyUI nodes (IP Adapter Plus, KJNodes, Florence2, etc.)
- 🔥 PyTorch with CUDA support
- 🔐 Minimal and clean image with only required packages installed

---

## 📁 Repository Structure

```
.
├── Dockerfile
├── requirements.txt
├── extra_model_paths.yaml
└── README.md
```

---

## 🧱 Prerequisites

- **Docker** with NVIDIA Container Toolkit installed
- **NVIDIA GPU** with drivers that support CUDA 12.4+
- Internet connection (for downloading repos and Python packages)

---

## 🏗️ Building the Docker Image

Run the following command in the root of the project directory:

```bash
docker build -t comfyui-gpu .
```

---

## ▶️ Running the Container

```bash
docker run --rm -it \
  --gpus all \
  -p 8189:8189 \
  comfyui-gpu
```

This will:

- Expose the ComfyUI interface at `http://localhost:8189`
- Run with full CUDA GPU acceleration
- Automatically load all included custom nodes

---

## 🧩 Included Custom Nodes

The following nodes are cloned into `ComfyUI/custom_nodes/` during build:

- [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
- [ComfyUI_IPAdapter_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus)
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)
- [ComfyUI_essentials](https://github.com/cubiq/ComfyUI_essentials)
- [ComfyUI-Florence2](https://github.com/kijai/ComfyUI-Florence2)
- [ComfyUI-SAM2](https://github.com/neverbiasu/ComfyUI-SAM2)
- [ComfyUI_LayerStyle](https://github.com/chflame163/ComfyUI_LayerStyle)
- [ComfyUI_LayerStyle_Advance](https://github.com/chflame163/ComfyUI_LayerStyle_Advance)
- [comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux)
- [ComfyUI-AdvancedLivePortrait](https://github.com/PowerHouseMan/ComfyUI-AdvancedLivePortrait)
- [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
- [ComfyUI-Impact-Subpack](https://github.com/ltdrdata/ComfyUI-Impact-Subpack)
- [ComfyUI-Inspire-Pack](https://github.com/ltdrdata/ComfyUI-Inspire-Pack)
- [ComfyUI-TeaCache](https://github.com/welltop-cn/ComfyUI-TeaCache)

---

## 🔧 Configuration

The file `extra_model_paths.yaml` is copied into the `ComfyUI/` directory. This can be used to define additional paths for models (e.g., checkpoints, embeddings).

Edit this file to configure your own model paths if needed.

---

## 🧪 Testing GPU Support

To verify that CUDA is working inside the container:

```bash
docker run --rm --gpus all comfyui-gpu nvidia-smi
```

You should see your GPU information printed.

---

## 📝 Notes

- Python packages are installed using `requirements.txt` after upgrading `pip`, `setuptools`, and `wheel`.
- PyTorch is installed directly from the official CUDA 12.4 wheel index.
- Rust is installed globally to support Python packages that require compilation.
- All temporary files and APT caches are cleaned during build for a smaller image.

---

## 📞 Support

If you run into issues or need to customize the build further (e.g., mounting volumes, saving outputs, extending with more custom nodes), feel free to open an issue or fork this setup.

---

## 🧼 Cleanup

To remove the built image:

```bash
docker rmi comfyui-gpu
```

To stop the container if running in detached mode:

```bash
docker ps
docker stop <container_id>
```

---

## 📜 License

This project does not include ComfyUI or any plugins themselves, only instructions and Docker configuration for installation. Please refer to each plugin's repository for license and usage terms.

---

```

Let me know if you'd like this adapted to support **volume mounting**, **persistent models directory**, **offline builds**, or **compose-based workflow**.
