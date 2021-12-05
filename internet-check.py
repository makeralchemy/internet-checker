import argparse
import os
import requests
import time

import journal

_ITERATION_WAIT_TIME = 5 * 60          # five minutes between tests
_SITE_TO_TEST = "https://google.com"   # default pagge to retrieve

RC_SUCCESS = 0  # successfully retrieved the HTML page
RC_TIMEOUT = 1  # could not retrieve the page within a reasonable time
RC_ERROR   = 2  # some kind of error occurred

# check internet connectivity by requesting a HTML page
# use a timeout value to prevent the function from hanging
# return a code indicating the status of the request and a 
# string containing additional information for errors and timeouts  
def internet_check(test_site=_SITE_TO_TEST, time_out_seconds=1):
    try:
        r = requests.get(test_site, timeout=time_out_seconds)
    except requests.exceptions.Timeout:
        return RC_TIMEOUT, "Request timed out after {} seconds".format(time_out_seconds)
    except Exception as err:
        return RC_ERROR, err
    else:
        return RC_SUCCESS, "HTTP return code={}".format(r.status_code)

# log results from the internet check
def log_results(log, rc, msg, summary_message):
    if rc == RC_SUCCESS:
        log.information("HTTP request successful")
        log.information(msg)
    elif rc == RC_ERROR:
        log.error("HTTP request failed")
        log.error(msg)
    elif rc == RC_TIMEOUT:
        log.warning("Timeout occurred")
        log.warning(msg)
    else:
        log.error("Unexpected return code")
        log.error("RC = {}".format(rc))
    if len(summary_message) > 0:
        log.information(summary_message)

# processing if invoked from the command line
def main():
    program_name = os.path.basename(__file__)

    # setup command parser
    parser = argparse.ArgumentParser(description="check internet connection by retrieving a web page")
    parser.add_argument("-s"
                       ,"--site"
                       ,type=str
                       ,default=_SITE_TO_TEST
                       ,help="web site to use for test"
                       )
    parser.add_argument("-t"
                       ,"--timeout"
                       ,type=int
                       ,default=1
                       ,help="time out in seconds"
                       )
    parser.add_argument("-x"
                       ,"--suppress_normal_messages"
                       ,action='store_true'
                       ,help="do not display informational messages"
                       )
    parser.add_argument("-i"
                       ,"--iterate"
                       ,action='store_true'
                       ,help="do interative checking"
                       )
    parser.add_argument("-w"
                       ,"--wait_time"
                       ,type=int
                       ,default=5     # 5 minute wait between iterations
                       ,help="minutes between iterations"
                       )
    parser.add_argument("-l"
                       ,"--logfile"
                       ,default="internet-check.log"
                       ,help="log file for messages"
                       )
    parser.add_argument("-d"
                       ,"--debug"
                       ,action='store_true'
                       ,help="display debugging messages"
                       )
    args = parser.parse_args()

    # setup journal
    if args.suppress_normal_messages:
        my_journal = journal.Journal("command"
                            ,args.logfile
                            ,program_name
                            ,log_information=False
                            )
    else:
        my_journal = journal.Journal("command", args.logfile, program_name)

    # first time check of internet connectivity
    itest_retcode, itest_dmsg  = internet_check(args.site, time_out_seconds=args.timeout)
    log_results(my_journal, itest_retcode, itest_dmsg, "")

    # when --iterate has been specified, loop forever checking internet
    # connectivity every --wait_time minutes.
    if args.iterate:
        # keep track of successes, errors, timeouts, and how many times
        # the checks have been made
        error_count   = 0
        success_count = 0
        timeout_count = 0
        iteration     = 0
        try:
            while True:
                iteration += 1
                time.sleep(args.wait_time * 60) # delay between iterations
                itest_retcode, itest_dmsg = internet_check(args.site, time_out_seconds=args.timeout)
                if itest_retcode == RC_SUCCESS:
                    success_count += 1
                if itest_retcode == RC_ERROR:
                    error_count += 1
                if itest_retcode == RC_TIMEOUT:
                   timeout_count += 1
                summary_msg = "Successes: {} Timeouts: {} Errors: {}".format(success_count, timeout_count, error_count)
                log_results(my_journal, itest_retcode, itest_dmsg, summary_msg)
                # in debug mode, periodically display the iteration count
                # this is helpful when -s is specified as there may be no
                # output messages for long periods of time.
                if args.debug:
                    if iteration % 10 == 0:
                        my_journal.debug("Iteration {}".format(iteration))
        except KeyboardInterrupt:
            print("\r")

# invoked via the command line
if __name__ == '__main__':
    main()
