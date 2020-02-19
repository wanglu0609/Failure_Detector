# Failure_Detector

## Running Failure Detector
To run the script, run "python3.6 runner.py".
To leave gracefully, run Ctrl+D (or kill -3)
To crash, run Ctrl+C (or just kill)
To see the latest membership list, node ID, or directly detected failures, see /src/shared/member_log.txt

## Running dgrep to Debug

To run our code:
cd ./src
python3.6 dgrep.py "-d skip -n -E <your_pattern_here>"
To run the unit test
cd ./tests
python3.6 run_tests.py
The keyword "__VM_ID__" will be replaced with the ID of each VM a server is running on before the command is sent to that server.
Aggregate results will appear in ./dgrep_results.txt.
Per-vm results will appear in /srv/shared/.
Error messages will be printed to the console. Error messages from servers will be printed, but shouldn't stop results from being produced (unless every single server has failed).
