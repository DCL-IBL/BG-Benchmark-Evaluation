import subprocess
import os
import traceback
import sys
import requests

import upload_to_dropbox

def run_bash_command(model_id, language):
    try:
        # Construct the bash command
        python_file = 'evaluate_models_bg.py' if 'bg' == language else 'evaluate_models.py'
        model_dir = f"/home/ubuntu/dimiterg/MMLU-{language}/outputs/{model_id}"
        if os.path.exists(model_dir + "/completed.txt"):
            print(f"Skipping completed model {model_id}")
        else:
            print(f"File {model_dir + '/completed.txt'} doesn't exist")
            print(f"Running model {model_id}")
            command = "bash -c \"" + \
                    "pushd /home/ubuntu/dimiterg && " + \
                    f"mkdir -p '{model_dir}' && " + \
                    f"python {python_file} '{model_id}' >'{model_dir}/stdout.txt' 2>'{model_dir}/stderr.txt'" + \
                    "\""
            
            # Execute the command
            result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
            print("Command output:", result.stdout)
            print("Command error:", result.stderr)

            if result.returncode == 0:
                command = f"touch {model_dir}/completed.txt"
                subprocess.run(command, shell=True, check=True, text=True, capture_output=True)

        file_name = f"{language}_good_prompt_" + model_id.replace('/', '_') + ".tar"
        command = "bash -c \"" + \
                "pushd /home/ubuntu/dimiterg && " + \
                f"tar cvf \'{file_name}\' \'MMLU-{language}/outputs/{model_id}/\'\""
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print("Command output:", result.stdout)
        print("Command error:", result.stderr)

        upload_to_dropbox.upload_results('/home/ubuntu/dimiterg/' + file_name)

    except Exception as e:
        stack_trace = traceback.format_exc()
        print(f"Error with {model_id}: {e}")
        print(f"Stack trace: {stack_trace}")



def delete_instance(instance_id, token):
    url = f"https://api.thundercompute.com:8443/instances/{instance_id}/delete"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Sending delete request to {url}...")
    response = requests.post(url, headers=headers)


def main(argv):
    models = [
        'meta-llama/Llama-3.2-3B-Instruct',
        'meta-llama/Llama-3.1-8B-Instruct',
        'google/gemma-3-27b-it',
        'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B',
        'INSAIT-Institute/MamayLM-Gemma-3-12B-IT-v1.0',
        'Qwen/Qwen2.5-14B-Instruct',
        'INSAIT-Institute/BgGPT-Gemma-2-9B-IT-v1.0',
        'mistralai/Mistral-7B-Instruct-v0.3',
    ]
    for model in models:
        run_bash_command(model, language='bg')
        run_bash_command(model, language='en')

    # Issue the shutdown command
    delete_instance('0', '1fdff9c7550e53d3f90b9394514fd4fcb67409557c8623e40206d72361d5ca95')


if __name__ == "__main__":
    main(sys.argv)
