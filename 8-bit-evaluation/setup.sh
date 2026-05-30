#!/bin/bash

python3 -m ensurepip --default-pip
python3 -m pip install --upgrade pip

mkdir -p ~/dimiterg
pushd ~/dimiterg

chmod +x ~/dimiterg/screen.sh
chmod +x ~/dimiterg/screen_resume.sh

cd ~/dimiterg
unzip ~/dimiterg/MMLU-bg.zip

cd ~/dimiterg
unzip ~/dimiterg/MMLU-en.zip

cd ~/dimiterg

apt-get install -y meson
pip install --upgrade meson
pip install --upgrade meson-python
pip install --upgrade transformers
pip install -r ~/dimiterg/requirements_no_versions.txt
pip install transformers bitsandbytes requests accelerate protobuf sentencepiece \
            peft datasets dropbox

pip install --upgrade huggingface_hub
curl -LsSf https://hf.co/cli/install.sh | bash

/home/ubuntu/.local/bin/hf auth login
