from lib.log_processor import ProcessedLogEntry

# DISCLAIMER: Not sure if this is the best way to do it but it seems to work. Feel free to change it if you think there's a better way.

def osconfig_agent_filter(log_entry: ProcessedLogEntry):
    # TODO BLAIS5-3780: This can be removed once the unit tests are redone
    if not isinstance(log_entry.data, dict):
        return False

    # NOTE: I put these conditionals to satisfy the type checker
    if not isinstance(log_entry.platform, str):
        return False

    # NOTE: Not even sure if we really need to check for this but I included it just in case
    if log_entry.platform != "gce_instance":
        return False

    # NOTE: I put these conditionals to satisfy the type checker
    if not isinstance(log_entry.message, str):
        return False

    # NOTE: This text seems to be common across the OSConfigAgent logs and can be found in log_entry.message and depending on the log
    # , it can be found within log_entry.log_name and log_entry.data["description"]
    if "unexpected end of JSON input" not in log_entry.message:
        return False

    # NOTE: I put these conditionals to satisfy the type checker
    if not isinstance(log_entry.log_name, str):
        return False

    # NOTE: If the log passes through through the previous conditionals, 
    # then we can assume that at this point that it's a log with "unexpected end of JSON input" 
    # but we still don't know whether it is definitely an OSConfigAgent log 
    # NOTE: So to confirm that it is an OSConfigAgent log, 
    # we check: 
    # if the log_entry.log_name contains "OSConfigAgent" 
    # or if the log_entry.message contains "OSConfigAgent Error"  
    # NOTE: In this conditional, if take the OSConfigAgent Error log as an example and go through this.
    # We should find OSConfigAgent Error in the log_entry.message but not in log_entry.log_name 
    # (we get something else, e.g. projects/ons-blaise-v2-prod/logs/winevt.raw)
    # If so the overall statement should evaluate to False as {True and False} is False, 
    # which means we ultimately pass over all of the conditionals and return True. With how we've set up the filters, 
    # returning True from a filter function means that the log is skipped and returning False means that the log is sent.
    if (
        "OSConfigAgent Error" not in log_entry.message
        and "OSConfigAgent" not in log_entry.log_name
    ):
        return False

    return True
