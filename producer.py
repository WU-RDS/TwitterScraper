import logging
import arrow, json, time

from os.path import isfile
from pathlib import Path
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from asyncio import Lock

from utils import hash_dict

"1) just loop from top to bottom"
"2) if change occurs (rare) then start again from top and check where left off"
"3) same procedure for prio-queue but that one comes first.. else is same..."

'''
go from top to bottom checking first prio and then normal queue, at beginning, or whenever prio file is modified
when normal queue is modified then do nothing
'''
'''
automatically write test cases for that...
has default query... but you can add extra one if need be...
'''

'''
give minimal logging output to let user know what something has been done...
'''

"needs to be resistant! i.e. if wrong json is entered it won't crash... and will just skip that line until one works... that is sensible..." \
"does it the iterator get all actually?" \
"implement manager of passwords..."


class PrioQueueHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global selected_todo
        if event.event_type == 'modified' and (
                event.src_path.split('/')[-1] == 'perma_queue.txt'
                or
                event.src_path.split('/')[-1] == 'priority_queue.txt'
        ):
            selected_todo = get_next_todo()
            print(f'new ToDo was added: {selected_todo}')


event_handler = PrioQueueHandler()
observer = Observer()
observer.schedule(event_handler, path="/Users/pi/PycharmProjects/TwitterScraper/todos", recursive=False)
observer.start()


def get_next_todo():
    '''
    this literally just provides the next thing to scrape, given the current state of the prio and non-prio queue
    :return:
    '''
    # builds lookup table for all already completed jobs
    lookup_of_finished_todos = set()
    with open('./todos/finished_jobs.txt', 'r') as f:
        for fin_l in f:
            try:
                fin_dct = json.loads(fin_l)
            except:
                continue
            lookup_of_finished_todos.add(hash_dict(fin_dct))

    def search_for_todo_in(path):
        with open(path, 'r') as f:
            for todo_l in f:
                try:
                    todo_dct = json.loads(todo_l)
                except:
                    continue
                if hash_dict(todo_dct) not in lookup_of_finished_todos:
                    return todo_dct
            else:
                # no job could be found
                return None

    # finds first TO_DO from the priortiy_queue that hasn't yet been completed
    q_type = 'priority_queue'
    next_todo = search_for_todo_in(f'./todos/{q_type}.txt')

    # only executed if no outstanding priority job
    if not next_todo:
        # finds first TO_DO from the perma_queue that hasn't yet been completed
        q_type = 'perma_queue'
        next_todo = search_for_todo_in(f'./todos/{q_type}.txt')

    return next_todo


def produce(qu):
    q, counter = qu
    global selected_todo
    selected_todo = get_next_todo()
    while True:

        while not selected_todo:
            time.sleep(2)
            # print('nothing is selected')

        logging.warning(f'NEW TODO: {selected_todo}')

        keywords = selected_todo['keywords']
        output_folder = f'{"_".join(keywords)}_{hash_dict(selected_todo)}'
        query = f'({" OR ".join(keywords)}) -has:links -is:reply -is:retweet -has:videos -has:images -has:media lang:en'
        Path(f"./data/{output_folder}").mkdir(parents=True, exist_ok=True)

        active_toto = selected_todo
        for d in arrow.Arrow.span_range('day', datetime.fromisoformat(selected_todo['start']),
                                        datetime.fromisoformat(selected_todo['end'])):

            while counter.value() > 3:
                if hash_dict(active_toto) != hash_dict(selected_todo):
                    break
                # print("sleeping")
                # print(f'{active_toto}  ==?==   {selected_todo}')
                time.sleep(2)
            if hash_dict(active_toto) != hash_dict(selected_todo):
                print("purging")
                q.clear()
                break

            s, e = d

            ## skip ever if day for to_do already scraped
            base_name = f'./data/{output_folder}/{s.format("YYYY-MM-DD")}'
            if isfile(f'{base_name}_res.jsonl'):
                # print('file already, skipping...')
                continue
            else:
                time.sleep(1)
                msg_dct = {
                    "query": query,
                    "start": str(s),
                    "end": str(e),
                    "save_as": f'{base_name}'
                }
                q.put(msg_dct)
                counter.increment()
                print(f'produced job for day: {base_name}_res.jsonl')
        else:
            with open('./todos/finished_jobs.txt', 'a') as af:
                af.write(f'{json.dumps(selected_todo)}\n')
            selected_todo = get_next_todo()

# experiment with this a lot
