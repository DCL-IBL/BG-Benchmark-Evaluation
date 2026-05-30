import tarfile
import os
import io

def extract_model_name(segments):
    for line in segments[0]:
        if not line.strip():
            continue
        line_segments = line.split()
        assert(line_segments[0] == '===')
        assert(line_segments[1] == 'Evaluating')
        result = line_segments[2]
        assert(line_segments[3] == '===')
        return result


def split_file_into_segments(file_path):
    segments = []
    current_segment = []
    reading_file_count = 0
    reading = False
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Check if line starts with 'Reading file: /home/ubuntu/'
            if line.startswith('Reading file: /home/ubuntu/'):
                reading = True
                reading_file_count += 1
                # If this is the first 'Reading file' line of a pair, start a new segment
                if reading_file_count == 1:
                    if current_segment:  # If there's content in current_segment, save it
                        segments.append(current_segment)
                    current_segment = [line]
                else:  # Second 'Reading file' line in the pair
                    current_segment.append(line)
                    reading_file_count = 0  # Reset counter for next pair
            elif not reading and line.startswith('Saving file: /home/ubuntu/'):
                # If this is 'Saving file' line, start a new segment
                if current_segment:  # If there's content in current_segment, save it
                    segments.append(current_segment)
                current_segment = [line]
            else:
                current_segment.append(line)
        
        # Append the last segment if it exists
        if current_segment:
            segments.append(current_segment)
    
    return segments


def extract_text(file_path):
    start = 'dev/'
    end = '_dev.csv'
    if start in file_path and end in file_path:
        start_index = file_path.index(start) + len(start)
        end_index = file_path.index(end)
        return file_path[start_index:end_index]
    
    start = '/'
    end = '_response.txt'
    if start in file_path and end in file_path:
        start_index = file_path.rfind(start) + len(start)
        end_index = file_path.index(end)
        return file_path[start_index:end_index]

    return None


def extract_index_number(line):
    if line.startswith('Comparing Index '):
        # Get the part after 'Comparing Index '
        rest = line[len('Comparing Index '):]
        # Split on colon and take the first part
        number_str = rest.split(':')[0].strip()
        return int(number_str)


def extract_true_false(line, prefix):
    if line.startswith(prefix):
        # Get the part after 'Comparing Index '
        rest = line[len(prefix):]
        # Split on colon and take the first part
        bool_str = rest.strip().split()[0]
        if bool_str == 'True':
            return True
        elif bool_str == 'False':
            return False
        else:
            raise Exception(f"Unable to parse bool in line: {line}")


def filter_comparison_lines(lines):
    return [line for line in lines if line.startswith('Comparing Index ')]


def parse_output_file(file_path):
    segments = split_file_into_segments(file_path)
    model_name = extract_model_name(segments)
    segments = segments[1:]
    results_dict = dict()
    for segment in segments:
        area = extract_text(segment[0])
        if area:
            result_lines = filter_comparison_lines(segment)
            n_questions = len(result_lines)
            results = [False] * n_questions
            n_correct = 0
            for i in range(n_questions):
                line = result_lines[i]
                index = extract_index_number(line)
                assert index == i
                bool_result = extract_true_false(line, f"Comparing Index {index}:")
                results[i] = bool_result
                if bool_result:
                    n_correct += 1
            results_dict[area] = (n_questions, n_correct)
    return model_name, results_dict


def extract_stdout(tar_path, output_dir):
    """
    Extract stdout.txt from a tar file, searching in all subdirectories.
    
    Args:
        tar_path (str): Path to the tar file
        output_dir (str): Directory where stdout.txt will be extracted
        
    Returns:
        str: Path to the extracted stdout.txt file, or None if not found
    """
    with tarfile.open(tar_path, 'r:*') as tar:
        for member in tar.getmembers():
            if os.path.basename(member.name) == 'stdout.txt':
                file_path = os.path.join(output_dir, member.name)
                if not os.path.exists(file_path):
                    tar.extract(member, output_dir)
                return os.path.join(output_dir, member.name)
    return None


def process_tar_files(directory):
    """
    Walk a directory to find all .tar files, extract stdout.txt from each,
    and collect the paths of the extracted files.
    
    Args:
        directory (str): Path to the directory to search for .tar files
        
    Returns:
        list: List of paths to the extracted stdout.txt files
    """
    extracted_paths = []
    output_dir = os.path.join(directory, "extracted")
    os.makedirs(output_dir, exist_ok=True)
    
    # Walk the directory to find all .tar files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.tar'):
                tar_path = os.path.join(root, file)
                # Create a unique subdirectory for each tar file to avoid conflicts
                tar_name = os.path.splitext(file)[0]
                unique_output_dir = os.path.join(output_dir, tar_name)
                os.makedirs(unique_output_dir, exist_ok=True)
                
                # Extract stdout.txt
                extracted_path = extract_stdout(tar_path, unique_output_dir)
                if extracted_path:
                    extracted_paths.append(extracted_path)
    
    return extracted_paths


def zip_many(x, l):
    return list(zip([x] * len(l), l))


class UngroupedSubjectError(Exception):
    """Exception raised when a subject is not found in any grouping."""
    pass

class MissingSubjectError(Exception):
    """Exception raised when a grouped subject is not found in subject stats."""
    pass

def group_subject_stats(subject_stats, groupings):
    """
    Transform a dictionary of subject stats into a dictionary grouped by subject area categories.
    Raises exceptions if any subject in subject_stats is not in any grouping or if any grouped
    subject is not in subject_stats.
    
    Args:
        subject_stats (dict): Dictionary with subject areas as keys and tuples of 
                            (total_questions, correct_questions) as values.
        groupings (dict): Dictionary with group names as keys and lists of subject areas as values.
    
    Returns:
        dict: Dictionary with group names as keys and tuples of 
              (total_questions, correct_questions) as values.
    
    Raises:
        UngroupedSubjectError: If any subject in subject_stats is not found in any grouping.
        MissingSubjectError: If any subject in groupings is not found in subject_stats.
    """
    # Check for ungrouped subjects (subjects in subject_stats not in any grouping)
    all_grouped_subjects = set()
    for subjects in groupings.values():
        all_grouped_subjects.update(subjects)
    
    ungrouped_subjects = set(subject_stats.keys()) - all_grouped_subjects
    if ungrouped_subjects:
        raise UngroupedSubjectError(f"Subjects not found in any grouping: {ungrouped_subjects}")
    
    # Check for missing subjects (subjects in groupings not in subject_stats)
    missing_subjects = all_grouped_subjects - set(subject_stats.keys())
    if missing_subjects:
        raise MissingSubjectError(f"Grouped subjects not found in subject stats: {missing_subjects}")
    
    grouped_stats = {}
    for group_name, subjects in groupings.items():
        total_questions = 0
        correct_questions = 0
        for subject in subjects:
            total, correct = subject_stats[subject]
            total_questions += total
            correct_questions += correct
        grouped_stats[group_name] = (total_questions, correct_questions)
    
    return grouped_stats


GROUPINGS = {
    'STEM': [
        'abstract_algebra',
        'anatomy',
        'astronomy',
        'college_biology',
        'college_chemistry',
        'college_computer_science',
        'college_mathematics',
        'college_physics',
        'conceptual_physics',
        'elementary_mathematics',
        'high_school_biology',
        'high_school_chemistry',
        'high_school_computer_science',
        'high_school_mathematics',
        'high_school_physics',
        'high_school_statistics',
        'machine_learning',
        'medical_genetics',
        'virology',
    ],
    'Humanities': [
        'formal_logic',
        'high_school_european_history',
        'high_school_world_history',
        'high_school_geography',
        'high_school_government_and_politics',
        'high_school_us_history',
        'logical_fallacies',
        'moral_disputes',
        'moral_scenarios',
        'philosophy',
        'prehistory',
        'world_religions',
        'global_facts',
        'international_law',
        'jurisprudence',
    ],
    'Social Sciences': [
        'high_school_macroeconomics',
        'high_school_microeconomics',
        'high_school_psychology',
        'human_sexuality',
        'sociology',
        'us_foreign_policy',
    ],
    'Professional Skills': [
        'business_ethics',
        'clinical_knowledge',
        'college_medicine',
        'computer_security',
        'econometrics',
        'electrical_engineering',
        'human_aging',
        'management',
        'marketing',
        'miscellaneous',
        'nutrition',
        'professional_accounting',
        'professional_medicine',
        'professional_psychology',
        'public_relations',
        'security_studies',
    ],
}

# set(topics_from_dir) == set(map(lambda x: x + '_bg', {item for sublist in GROUPINGS.values() for item in sublist}))

def write_utf8_file(file_path, content):
    print('Saving file: ' + file_path)
    # Get the directory path from the file path
    directory = os.path.dirname(file_path)
    
    # Create directory if it doesn't exist
    if directory:
        os.makedirs(directory, exist_ok=True)
        
    # Write the file with UTF-8 encoding
    with io.open(file_path, 'w', encoding='utf8') as f:
        f.write(content)


en_files = process_tar_files('/home/person/Develop/testing_models_8bit_results_parser/tars/results_en')
bg_files = process_tar_files('/home/person/Develop/testing_models_8bit_results_parser/tars/results_bg')
print(en_files)
print(bg_files)
files = zip_many('en', en_files) + zip_many('bg', bg_files)
assert len(files) == 16
csv_lines = [
    'Model,'
    'Language,'
    'STEM Total,'
    'STEM Correct,'
    'Humanities Total,'
    'Humanities Correct,'
    'Social Sciences Total,'
    'Social Sciences Correct,'
    'Professional Skills Total,'
    'Professional Skills Correct']
for (language, file_path) in files:
    model_name, results_dict = parse_output_file(file_path)
    new_results_dict = dict()
    for results_key in results_dict.keys():
        new_results_key = results_key
        if results_key.endswith('_' + language):
            new_results_key = results_key[0:len(results_key) - (len(language) + 1)]
        new_results_dict[new_results_key] = results_dict[results_key]
    assert len(results_dict) == len(new_results_dict)
    results_dict = new_results_dict
    print(sorted(results_dict.keys()))
    assert len(results_dict) == 56
    print("================================")
    print("================================")
    print(f"Language: {language}, Model: {model_name}")
    print("================================")
    for group in GROUPINGS:
        print(f"Group {group}")
        areas = GROUPINGS[group]
        for area in areas:
            if area not in results_dict:
                print(f"area: {area} not in file: {file_path}")
            results = results_dict[area]
            print(f"{area}: {results[1]} of {results[0]}")
    grouped = group_subject_stats(results_dict, GROUPINGS)
    assert len(grouped) == 4
    assert len(GROUPINGS) == 4
    print("================================")
    for group in grouped:
        print(f"{group}: {grouped[group][1]} of {grouped[group][0]}")
    csv_lines.append(','.join([
        f"{model_name}",
        f"{language}",
        # STEM Total
        f"{grouped['STEM'][0]}",
        # STEM Correct
        f"{grouped['STEM'][1]}",
        # Humanities Total
        f"{grouped['Humanities'][0]}",
        # Humanities Correct
        f"{grouped['Humanities'][1]}",
        # Social Sciences Total
        f"{grouped['Social Sciences'][0]}",
        # Social Sciences Correct
        f"{grouped['Social Sciences'][1]}",
        # Professional Skills Total
        f"{grouped['Professional Skills'][0]}",
        # Professional Skills Correct
        f"{grouped['Professional Skills'][1]}",
    ]))
print("================================")
write_utf8_file('/var/home/person/Develop/testing_models_8bit_results_parser/results_per_category.csv', '\n'.join(csv_lines))
