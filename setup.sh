#!/bin/bash
mkdir -p ~/dimiterg
pushd ~/dimiterg

chmod +x ~/dimiterg/screen.sh
chmod +x ~/dimiterg/screen_resume.sh
mkdir -p ~/dimiterg/MMLU-bg

cd ~/dimiterg/MMLU-bg
unzip ~/dimiterg/MMLU-bg.zip

cd ~/dimiterg
unzip ~/dimiterg/MMLU-en.zip

cd ~/dimiterg
sudo apt install -y meson
pip install --upgrade meson
pip install --upgrade meson-python
pip install -r ~/dimiterg/requirements_no_versions.txt
pip install --upgrade transformers

huggingface-cli login
