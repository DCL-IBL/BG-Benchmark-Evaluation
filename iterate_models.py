import subprocess
import os
import traceback
import sys
import requests

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from uploader import drive_service


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

        def upload_file(file_path, folder_id=None):
            """Upload a file to Google Drive."""
            # File metadata
            file_metadata = {
                'name': os.path.basename(file_path),
            }
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Media upload
            media = MediaFileUpload(file_path, resumable=True)
            
            # Upload the file
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            print(f"File uploaded successfully. File ID: {file.get('id')}")
        
        upload_file('/home/ubuntu/dimiterg/' + file_name, folder_id='1I7TW2oz3ucuCxRqWjvdeQsJuK33EfzlY')

    except Exception as e:
        stack_trace = traceback.format_exc()
        print(f"Error with {model_id}: {e}")
        print(f"Stack trace: {stack_trace}")


#def shutdown_instance(instance_id, token):
#    """Send POST request to Thunder Compute API to shut down the instance."""
#    url = f"https://api.thundercompute.com:8443/instances/{instance_id}/down"
#    headers = {"Authorization": f"Bearer {token}"}
#    print(f"Sending shutdown request to {url}...")
#    response = requests.post(url, headers=headers, timeout=10)
#    response.raise_for_status()  # Raises exception for 4xx/5xx errors
#    print(f"Shutdown request successful: {response.status_code} {response.text}")


def delete_instance(instance_id, token):
    url = f"https://api.thundercompute.com:8443/instances/{instance_id}/delete"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Sending delete request to {url}...")
    response = requests.post(url, headers=headers)
    response.raise_for_status()  # Raises an HTTPError for bad responses


def main(argv):
    models = [
        'INSAIT-Institute/BgGPT-Gemma-2-9B-IT-v1.0',
        ]
    for model in models:
        run_bash_command(model, language='bg')
        run_bash_command(model, language='en')

    # Issue the shutdown command
    delete_instance('0', 'INSERT_API_KEY_HERE')
    print("Shutdown command issued. VM will terminate shortly.")

if __name__ == "__main__":
    main(sys.argv)
