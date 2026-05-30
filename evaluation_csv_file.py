import os
import io
import pandas as pd
from io import StringIO
import math
import traceback


def read_utf8_file(file_path):
    print('Reading file: ' + file_path)
    with io.open(file_path, 'r', encoding='utf8') as f:
        return f.read()


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


def string_to_pd(data):
    return pd.read_csv(StringIO(data))


def pd_to_string(df):
    sio = StringIO()
    df.to_csv(sio, index=False)
    return sio.getvalue()


def get_correct_results(df, only_one=False):
    correct = []
    for _, row in df.iterrows():
        correct.append(f"{row['Correct']}")
        if only_one:
            break
    return correct


def format_questions_and_answers(df, add_correct=False, only_one=False, language='en'):
    # Iterate through the DataFrame to format each question
    result = []
    one_based = 0
    question = 'QUESTION' if language == 'en' else 'ВЪПРОС'
    answer = 'ANSWER' if language == 'en' else 'ОТГОВОР'
    answers = 'ANSWERS' if language == 'en' else 'ОТГОВОРИ'
    for idx, row in df.iterrows():
        one_based += 1
        suffix = f"{one_based} " if not only_one else ''
        result.append(f"--- {question} {suffix}---\n")
        result.append(f"Q: {row['Question']}\n")
        result.append(f"A: {row['A']}\n")
        result.append(f"B: {row['B']}\n")
        result.append(f"C: {row['C']}\n")
        result.append(f"D: {row['D']}\n\n")
        if only_one:
            break
    if add_correct:
        if only_one or one_based == 1:
            result.append(f"--- {answer} ---\n")
        else:
            result.append(f"--- {answers} ---\n")
        result.append(', '.join(get_correct_results(df, only_one=only_one)))
    return ''.join(result) + '\n\n'


def split_dataframe(df, max_rows=1):
    """
    Split a pandas DataFrame into K DataFrames, each with at most max_rows rows.
    
    Parameters:
    df (pd.DataFrame): Input DataFrame with N rows
    max_rows (int): Maximum number of rows per split DataFrame (default: 10)
    
    Returns:
    list: List of K DataFrames
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    
    if max_rows < 1:
        raise ValueError("max_rows must be at least 1")
    
    n_rows = len(df)
    if n_rows == 0:
        return []
    
    # Calculate number of splits needed
    k = math.ceil(n_rows / max_rows)
    
    # Split DataFrame into K parts
    split_dfs = []
    for i in range(k):
        start_idx = i * max_rows
        end_idx = min((i + 1) * max_rows, n_rows)
        split_dfs.append(df.iloc[start_idx:end_idx].copy())
    
    return split_dfs


class evaluation_csv_file:

    def __init__(self, file_path):
        data = read_utf8_file(file_path)
        data = 'Question,A,B,C,D,Correct\n' + data
        df = string_to_pd(data)
        self.df = df

    def get_length(self):
        return len(self.df.index)

    def get_split_dfs(self):
        df = self.df.iloc[:,:-1]
        return split_dataframe(df)
        #return list(map(pd_to_string, dfs))

    def get_correct_results_from_self(self):
        expected_results = get_correct_results(self.df)
        return expected_results

    def compare_results(self, response):
        expected_results = list(map(lambda x: x.strip(), self.get_correct_results_from_self()))
        response = list(map(lambda x: x.strip(), response))

        total = 0
        correct = 0
        try:
            index_expected = 0
            index_response = 0
            while True:
                if index_expected >= len(expected_results) or index_response >= len(response):
                    break
                total += 1
                if expected_results[index_expected] == response[index_response]:
                    correct += 1
                    print(f"Comparing Index {index_expected}: True")
                else:
                    expected = expected_results[index_expected]
                    split_response = response[index_response].split()
                    all_other_answers = [i for i in ['A', 'B', 'C', 'D'] if not (i == expected)]
                    if (expected in split_response) and all(not(i in split_response) for i in all_other_answers):
                        print(f"Comparing Index {index_expected}: True because {expected} is in {split_response}")
                        correct += 1
                    else:
                        print(f"Comparing Index {index_expected}: False because {expected} is not the answer in {split_response}")
                index_expected += 1
                index_response += 1
        except:
            stack_trace = traceback.format_exc()
            print(f"Unable to parse results: {response}, stack_trace: {stack_trace}")
        ratio_equal = 0.0
        if total > 0:
            ratio_equal = float(correct) / float(total)
        percentage_equal = ratio_equal * 100.0
        return percentage_equal
