import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess
import sys
import time

SIMPLE_TEST_PATTERNS = [
    'unique 1',
    'unique 2',
    'unique 3',
    'unique 4',
    'unique f',
    'unique g',
    'unique h',
    'unique i',
    'unique j',
    'common', 
    'double', 
    'triple',
    'quad'
]

REALISTIC_TEST_PATTERNS = [
    'Mozilla',
    'OER',
    'JlmLT1',
    '^[0-9]*[a-z]{5}'
]

LOCAL_TEST_DIR = "/srv/shared/mp1/test_logs/"
DGREP_TEST_DIR = "/srv/shared/"

GREP_CMD_FORMAT = "grep -d skip -n -E '%s' %s /dev/null"

def print_final_result(result):
    bar_str = "****"
    for _ in range(0, len(result)):
        bar_str += "*"
    print(bar_str)
    print("* %s *" % result)
    print(bar_str)

def check_test_output(local_lines):
    dgrep_lines = []
    with open("dgrep_result.txt") as dgrep_result_file:
        dgrep_lines = dgrep_result_file.readlines()
    tmp_lines = []
    for line in dgrep_lines:
        tmp_lines.append(line[line.find(':') + 1:-1])
    dgrep_lines = sorted(tmp_lines)
    tmp_lines = []
    for line in local_lines:
        if line == '':
            continue
        tmp_lines.append(line.replace('mp1/test_logs/', ''))
    local_lines = sorted(tmp_lines)
    if not (len(local_lines) == len(dgrep_lines)):
        print("** TEST FAILED: Line counts do not match. **")
        print("\tLocal line count:  %d" % len(local_lines))
        print("\tRemote line count: %d" % len(dgrep_lines))
        return False
    for i in range(0, len(local_lines)):
        if not (local_lines[i] == dgrep_lines[i]):
            print("** TEST FAILED: Line does not match. **")
            return False
    return True

def run_local_grep(pattern, file_pattern):
    file_pattern = file_pattern.replace('__VM_ID__', '*')
    file_pattern = os.path.join(LOCAL_TEST_DIR, file_pattern)
    result = subprocess.check_output(GREP_CMD_FORMAT % (pattern, file_pattern), shell=True).decode('utf-8')
    return result.split('\n')

def run_dgrep(pattern, file_pattern):
    file_pattern = os.path.join(DGREP_TEST_DIR, file_pattern)
    grep_cmd = GREP_CMD_FORMAT % (pattern, file_pattern)
    os.system('python3.6 ../src/dgrep.py "%s"' % grep_cmd)

def run_test(test_type, test_pattern, file_pattern):
    local_result = run_local_grep(test_pattern, file_pattern)
    dgrep_result = run_dgrep(test_pattern, file_pattern)
    return check_test_output(local_result)

def run_realistic_test(test_pattern):
    return run_test("realistic", test_pattern, "vm__VM_ID__.log")

def run_simple_test(test_pattern):
    return run_test("simple", test_pattern, "simple_log___VM_ID__.txt")

def run_latency_test(test_pattern):
    start_time = time.time()
    run_dgrep(test_pattern, "vm__VM_ID___60MB.log")
    return time.time() - start_time

def run_latency_tests():
    results = {}
    for pattern in REALISTIC_TEST_PATTERNS:
        this_pattern_results = []
        for i in range(0, 10):
            print("Running latency test %d for %s" % (i, pattern))
            this_pattern_results.append(run_latency_test(pattern))
        results[pattern] = this_pattern_results
    print(results)
    fig, ax = plt.subplots(1)
    positions = [i for i in range(1, len(REALISTIC_TEST_PATTERNS) + 1)]
    bars = []
    stds = []
    for k in results.keys():
        bars.append(np.mean(results[k]))
        stds.append(np.std(results[k]))
    ax.bar(positions, bars, tick_label=REALISTIC_TEST_PATTERNS, yerr=stds)
    ax.set_xlabel("Query")
    ax.set_ylabel("Latency(s)")
    fig.savefig("latency_graph.png")

def run_correctness_tests():
    simple_passing = True
    print("Running simple tests...")
    for pattern in SIMPLE_TEST_PATTERNS:
        print("\tTest pattern: %s" % pattern)
        result = run_simple_test(pattern)
        if (result == False):
            simple_passing = False
    if simple_passing:
        print("SIMPLE TESTS: All tests passed!")
    else:
        print("SIMPLE TESTS: At least one test failed!")
    realistic_passing = True
    print("Running realistic tests...")
    for pattern in REALISTIC_TEST_PATTERNS:
        print("\tTest pattern: %s" % pattern)
        result = run_realistic_test(pattern)
        if (result == False):
            realistic_passing = False
    if realistic_passing:
        print("REALISTIC TESTS: All tests passed!")
    else:
        print("REALISTIC TESTS: At least one test failed!")
    if (simple_passing and realistic_passing):
    	print_final_result("ALL TESTS PASSED")
    else:
    	print_final_result("TESTS FAILED")

if __name__ == '__main__':
    if ("--latency" in sys.argv):
        run_latency_tests()
    else:
        run_correctness_tests()
