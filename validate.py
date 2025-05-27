import json
import internet_roadtrip_panos
import concurrent.futures

def process_item(item):
  """Processes a single item, predicting options and calculating set differences.

  Args:
    item: A dictionary containing 'pano', 'heading', 'options', and 'stop'.

  Returns:
    A tuple containing the stop name and two sets (estimated - action, action - estimated)
    or None if there is no difference between the sets.
  """
  options = internet_roadtrip_panos.predict_options(item['pano'], float(item['heading']))
  estimated = set([x['pano'] for x in options])
  action = set([x['pano'] for x in item['options']])
  if len(estimated - action) or len(action - estimated):
    return (item['stop'], estimated - action, action - estimated)
  return None

import csv


def process_data_in_parallel(data, max_workers=1):
    """Processes data in parallel using a thread pool.

    Args:
      data: A list of dictionaries, each containing data for a single item.
      max_workers: The maximum number of worker threads to use.
    """
    w = csv.writer(open("failures.csv", "w"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_item, item) for item in data]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
              stop, estimated_minus_action, action_minus_estimated = result
              w.writerow([stop, len(estimated_minus_action), len(action_minus_estimated)])
              print("Set delta: %s, %s, %s" % (stop, estimated_minus_action, action_minus_estimated))


# Example of how to call the function:
# Assuming your data is in a variable called 'data'
data = json.load(open("failed.json"))
#data = [i for i in data if i['stop'] == "231160"]
process_data_in_parallel(data)
