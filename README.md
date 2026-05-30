# MMLU-BG-Evaluation

## Objective of the IfGPT project

The project aims to develop a freely accessible infrastructure for the selection and pre-processing of large datasets for Bulgarian as well as tailored data for particular industries and fine-tuning suitable freely available large language models for specific purposes.

## MMLU-BG Evaluation



## MMLU-BG Evaluation Instructions

Install on a **Thundercompute** instance as follows:
- Obtain MMLU-en.zip and MMLU-bg.zip and place them in the current directory of the script.
- [Optional] For automatic uploading to Google Drive, generate a client secret for your Google Cloud client. Your Google account must authorize your client for access to your google drive. Replace client_secret.json with your own.
- Copy the whole directory to your Thundercompute home directory, call it dimiterg (the name is currently hardcoded)
- chmod +x ~/dimiterg/setup.sh
- Run this script: ~/dimiterg/setup.sh , it will also ask you for your huggingface token
- cd ~/dimiterg
- Put your model ID(s) (from huggingface) into iterate_models.py - see 'INSAIT-Institute/BgGPT-Gemma-2-9B-IT-v1.0' and add/replace accordingly.
- [Optional] Put your Thundercompute API token in iterate_models.py. This is used to delete your instance once done (because instances can currently only be deleted, not stopped), in order to save on rent. If you don't automatically upload to Google Drive, then don't delete the instance until you've had the chance to download your results.
- python iterate_models.py.
- The instance should be deleted automatically when the calculation is done.
- stdout.txt and percent.txt per area will be generated in ~/MMLU-{language}/outputs/Model/ID/. stdout.txt can then be parsed using results_parser.py. Check that file to see what paths to change.

Thundercompute: https://www.thundercompute.com/

## MMLU-BG Dataset

MMLU-BG is a dataset in Bulgarian for testing and evaluating the performance of large language models. 

MMLU-BG is available here: https://github.com/DCL-IBL/MMLU-BG-Dataset/

MMLU-BG dataset is based on the original MMLU dataset (Hendrix et al., 2021), taking into account the experience from developing newer and extended versions of the dataset such as MMLU-Pro (Wang et al., 2024) and MMLU-ProX (Xuan et al., 2025), as well as the experience in developing multilingual versions of the dataset (Singh et al., 2024). 

In this regard, procedural steps for selecting thematic domains and improving data quality have been introduced in the procedures of compiling the dataset. Further, the correction of the dataset proposed in MMLU-Redux (Gema et al., 2024) are also implemented.

The origuinal MMLU dataset contains a total of over 15,000 questions for 57 domains.

__________________________________________

This work is part of the project **Infrastructure for Fine-tuning Pre-trained Large Language Models**, Grant Agreement No. ПВУ – 55 from 12.12.2024 /BG-RRP-2.017-0030-C01/.

https://ifgpt.dcl.bas.bg/en/
