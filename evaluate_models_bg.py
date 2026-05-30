import os
import time
import traceback
import sys

import evaluate_models


# Main automation loop
if __name__ == "__main__":

    parent_directory = '/home/ubuntu/dimiterg/MMLU-bg'

    areas = evaluate_models.get_subject_areas(parent_directory + '/test/')

    # List of model IDs to evaluate (add/remove as needed; all from HF)
    model_ids = []
    if len(sys.argv) >= 2:
        model_ids.append(sys.argv[1])

    results = []
    for model_id in model_ids:
        try:
            dest_dir = '/home/ubuntu/dimiterg/models/' + model_id
            os.makedirs(dest_dir, exist_ok=True)
            time_taken, vram_used = evaluate_models.evaluate_model(model_id, dest_dir, parent_directory, areas, 'bg')
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