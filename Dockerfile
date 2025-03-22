FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /comfyui_project

# Install system dependencies, Rust, and upgrade pip
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    curl \
    build-essential \
    pkg-config \
    libssl-dev \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y --no-modify-path \
    && ln -s $HOME/.cargo/bin/* /usr/local/bin/ \
    && pip3 install --no-cache-dir --upgrade pip setuptools wheel \
    && rm -rf /var/lib/apt/lists/*

# Copy your custom requirements.txt
COPY requirements.txt .

# Install PyTorch with CUDA 12.4 support
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install Python packages (Rust now available)
RUN pip install --no-cache-dir --upgrade -r requirements.txt -i https://pypi.org/simple

# Clone ComfyUI and ComfyUI-Manager
RUN git clone https://github.com/comfyanonymous/ComfyUI.git ComfyUI && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git ComfyUI/custom_nodes/comfyui-manager

COPY extra_model_paths.yaml ComfyUI/

# Clone additional custom nodes
RUN git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git ComfyUI/custom_nodes/ComfyUI_IPAdapter_plus && \
    git clone https://github.com/kijai/ComfyUI-KJNodes.git ComfyUI/custom_nodes/ComfyUI-KJNodes && \
    git clone https://github.com/cubiq/ComfyUI_essentials.git ComfyUI/custom_nodes/ComfyUI_essentials && \
    git clone https://github.com/kijai/ComfyUI-Florence2.git ComfyUI/custom_nodes/ComfyUI-Florence2 && \
    git clone https://github.com/neverbiasu/ComfyUI-SAM2.git ComfyUI/custom_nodes/ComfyUI-SAM2 && \
    git clone https://github.com/chflame163/ComfyUI_LayerStyle.git ComfyUI/custom_nodes/ComfyUI_LayerStyle && \
    git clone https://github.com/chflame163/ComfyUI_LayerStyle_Advance.git ComfyUI/custom_nodes/ComfyUI_LayerStyle_Advance && \
    git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git ComfyUI/custom_nodes/comfyui_controlnet_aux && \
    git clone https://github.com/PowerHouseMan/ComfyUI-AdvancedLivePortrait.git ComfyUI/custom_nodes/ComfyUI-AdvancedLivePortrait && \
    git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git ComfyUI/custom_nodes/ComfyUI-Impact-Pack && \
    git clone https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git ComfyUI/custom_nodes/ComfyUI-Impact-Subpack && \
    git clone https://github.com/ltdrdata/ComfyUI-Inspire-Pack.git ComfyUI/custom_nodes/ComfyUI-Inspire-Pack && \
    git clone https://github.com/welltop-cn/ComfyUI-TeaCache.git ComfyUI/custom_nodes/ComfyUI-TeaCache

# Add NVIDIA environment variables for GPU support (from original)
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

# Expose port 8189
EXPOSE 8189

# Run ComfyUI on port 8189 with full startup options (adapted from original)
CMD ["python3", "ComfyUI/main.py", "--listen", "0.0.0.0", "--port", "8189", "--preview-method", "auto"]