# cucm-compare-reg-status
Script to compare the results from two Risport70 queries against Cisco Unified Communications Manager

### Requirements

* Tested only on Python 3.6+
* zeep

### Usage

Run from the commandline

```
python compareregstatus.py
Successfully captured current Risport status.
Press Enter to query Risport and compare to the initial result
or Ctrl+C to exit
...
```

Pressing Enter repeats the Risport query, lists any entries that may have changed and returns to the prompt to press Enter to compare again.

Sample output:

```
No difference between snapshot and most recent query detected
Press Enter to query Risport and compare to the initial result
or Ctrl+C to exit
...
cholland changed status from Registered to UnRegistered
Press Enter to query Risport and compare to the initial result
or Ctrl+C to exit
...
```


### License

MIT
