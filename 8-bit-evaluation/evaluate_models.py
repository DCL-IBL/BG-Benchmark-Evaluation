import os
import torch
import time
import gc
import tempfile
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from transformers import Kosmos2_5Config, AutoModel
from transformers import Kosmos2_5ForConditionalGeneration, AutoTokenizer

from huggingface_hub import snapshot_download
import evaluation_csv_file
import traceback
import sys



def get_subject_areas(directory):
    """
    Reads file names from the specified directory and returns a list of subject areas
    by removing the '_test.csv' suffix from each file name.
    
    Args:
        directory (str): Path to the directory containing the files
        
    Returns:
        list: List of subject area names without the '_test.csv' suffix
    """
    try:
        # Get list of files in the directory
        files = os.listdir(directory)
        
        # Filter files ending with '_test.csv' and remove the suffix
        subject_areas = [file[:-9] for file in files if file.endswith('_test.csv')]
        
        return sorted(subject_areas)  # Return sorted list for consistency
    except FileNotFoundError:
        print(f"Directory '{directory}' not found")
        return []
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

def generate_prompt(dev_csv_df, test_csv_df, language):
    if language == 'en':
        prompt = "You will receive a question with four answers. " + \
                "Only one of the answers (A, B, C, D) is correct. " + \
                "Chose the correct answer by its label, e.g., A. "\
                "Don't include anything else in your response.\n"
        prompt += "Example:\n" + evaluation_csv_file.format_questions_and_answers(dev_csv_df, add_correct=True, only_one=True, language=language)
        prompt += "The question is:\n" + evaluation_csv_file.format_questions_and_answers(test_csv_df, add_correct=False, only_one=True, language=language)
    else:
        prompt = "Ще получиш въпрос с четири отговора. " + \
                "Само един от отговорите (A, B, C, D) е верен. " + \
                "Посочи верния отговор чрез буквата преди него, например A. "\
                "Не включвай нищо друго в отговора.\n"
        prompt += "Пример:\n" + evaluation_csv_file.format_questions_and_answers(dev_csv_df, add_correct=True, only_one=True, language=language)
        prompt += "Въпросът е:\n" + evaluation_csv_file.format_questions_and_answers(test_csv_df, add_correct=False, only_one=True, language=language)
    return prompt


def generate_response(area, model, tokenizer, parent_directory, language):
    # val - don't use
    # dev - for training and prompt
    # test - for running this test
    dev_csv = evaluation_csv_file.evaluation_csv_file(parent_directory + '/dev/' + area + '_dev.csv')
    test_csv = evaluation_csv_file.evaluation_csv_file(parent_directory + '/test/' + area + '_test.csv')
    dfs = test_csv.get_split_dfs()

    start_time = time.time()
    response = []

    print(f"Model device: {model.device}")  # Prints the device of the model (e.g., 'cuda:0' or 'cpu')

    for df in dfs:
        prompt = generate_prompt(dev_csv.df, df, language)
        print('Prompt: ' + prompt)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        # Add print statements to confirm the device
        print(f"Input tensors device: {inputs['input_ids'].device}")  # Prints the device of the input tensors

        # Generate response
        result = ''
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=20,
                do_sample=True,            # sampling for variety
                temperature=0.7,           # randomness control
                top_p=0.9,                 # nucleus sampling
                pad_token_id=tokenizer.eos_token_id
            )
            result = tokenizer.decode(outputs[0][len(inputs["input_ids"][0]):], skip_special_tokens=True)
            print(f"Model's response result: {result}")
        response.append(result)
    end_time = time.time()
        
    return start_time, end_time, list(map(lambda x: x.strip(), response)), test_csv


def evaluate_model(model_id, dest_dir, parent_directory, areas, language):
    """
    Download, load, evaluate, and report on a single model.
    """

    gc.collect()
    torch.cuda.empty_cache()
    gc.collect()
    torch.cuda.empty_cache()
    gc.collect()
    torch.cuda.empty_cache()
    gc.collect()
    torch.cuda.empty_cache()
    gc.collect()

    print(f"\n=== Evaluating {model_id} ===")
    
    # Download to temp dir (ignores default HF cache)
    print("Downloading model...")
    local_dir = snapshot_download(
        repo_id=model_id,
        local_dir=dest_dir,
        local_dir_use_symlinks=False,  # Ensures full copy for cleanup
        resume_download=True  # Fresh download each time
    )
    
    # Load tokenizer and model (optimized for A100 CUDA)
    print("Loading model...")
    quantization_config = BitsAndBytesConfig(
        load_in_8bit=True,
        bnb_8bit_quant_type="nf4",
        bnb_8bit_compute_dtype=torch.bfloat16,
        bnb_8bit_use_double_quant=True
    )

    model = None

    tokenizer = AutoTokenizer.from_pretrained(local_dir,
        use_fast=True,  # Use fast tokenizer for better performance
        trust_remote_code=True  # Allow custom code for non-standard models (if needed)
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token  # Fix for some models

    model = AutoModelForCausalLM.from_pretrained(
        local_dir,
        quantization_config=quantization_config,
        torch_dtype=torch.bfloat16, # For stability
        device_map="auto",          # Auto-offload to GPU via accelerate
        low_cpu_mem_usage=True,
        trust_remote_code=True  # Allow custom code for non-standard models
    )

    for area in areas:
        start_time, end_time, response, csv_file = generate_response(area, model, tokenizer, parent_directory, language)
        prefix_for_file_path = parent_directory + '/outputs/' + model_id + '/' + area
        evaluation_csv_file.write_utf8_file(prefix_for_file_path + '_response.txt', f"{response}")
        percentage_equal = csv_file.compare_results(response)
        compared = f"Correct: {csv_file.get_correct_results_from_self()}, Response: {response}"
        evaluation_csv_file.write_utf8_file(prefix_for_file_path + '_compared.txt', compared)
        evaluation_csv_file.write_utf8_file(prefix_for_file_path + '_percent.txt', str(percentage_equal))

        generation_time = end_time - start_time
        vram_gb = torch.cuda.memory_allocated() / (1024 ** 3)  # Current VRAM usage in GB
    
        print(f"Response: {response}")
        print(f"Generation time: {generation_time:.2f} seconds")
        print(f"Peak VRAM usage: {vram_gb:.2f} GB")
    
    # Cleanup GPU memory
    del model, tokenizer
    gc.collect()
    torch.cuda.empty_cache()
    gc.collect()
    torch.cuda.empty_cache()
    gc.collect()
    torch.cuda.empty_cache()
    gc.collect()
    torch.cuda.empty_cache()
    gc.collect()
    
    print("Evaluation complete. Cleaning up...")
    return generation_time, vram_gb

# Main automation loop
if __name__ == "__main__":
    parent_directory = '/home/ubuntu/dimiterg/MMLU-en'

    areas = get_subject_areas(parent_directory + '/test/')

    # List of model IDs to evaluate (add/remove as needed; all from HF)
    model_ids = ['']
    assert len(model_ids) == 1
    if len(sys.argv) >= 2:
        model_ids[0] = sys.argv[1]

    results = []
    for model_id in model_ids:
        try:
            dest_dir = '/home/ubuntu/dimiterg/models/' + model_id
            os.makedirs(dest_dir, exist_ok=True)
            time_taken, vram_used = evaluate_model(model_id, dest_dir, parent_directory, areas, 'en')
            results.append({
                "model_id": model_id,
                "time_s": time_taken,
                "vram_gb": vram_used,
                "model_dir_size_gb": sum(os.path.getsize(os.path.join(dest_dir, f)) for f in os.listdir(dest_dir) if os.path.isfile(os.path.join(dest_dir, f))) / (1024 ** 3) if os.path.exists(dest_dir) else 0
            })
        except Exception as e:
            stack_trace = traceback.format_exc()
            print(f"Error with {model_id}: {e}")
            print(f"Stack trace: {stack_trace}")
            results.append({"model_id": model_id, "error": str(e)})
    
    # Summary table
    print("\n=== Summary ===")
    print("| Model ID | Time (s) | VRAM (GB) | Notes |")
    print("|----------|----------|-----------|-------|")
    for res in results:
        notes = "Success" if "error" not in res else f"Error: {res['error']}"
        print(f"| {res['model_id']} | {res.get('time_s', 0.0):.2f} | {res.get('vram_gb', 0.0):.2f} | {notes} |")
