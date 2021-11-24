import logging
import arrow, json, time

from os.path import isfile
from pathlib import Path
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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


class PrioQueueHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.event_type == 'modified' and (
                event.src_path.split('/')[-1] == 'perma_queue.txt'
                or
                event.src_path.split('/')[-1] == 'priority_queue.txt'
        ):
            global todo
            todo = get_next_todo()
            print(f'new ToDo was added: {todo}')


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
            fin_dct = json.loads(fin_l)
            lookup_of_finished_todos.add(hash_dict(fin_dct))

    def search_for_todo_in(path):
        with open(path, 'r') as f:
            for todo_l in f:
                todo_dct = json.loads(todo_l)
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


todo = get_next_todo()
while True:

    while not todo:
        time.sleep(2)

    logging.warning(f'NEW TODO: {todo}')

    keywords = todo['keywords']
    output_folder = f'{"_".join(keywords)}_{hash_dict(todo)}'
    Path(f"./data/{output_folder}").mkdir(parents=True, exist_ok=True)

    current_todo = todo
    for d in arrow.Arrow.span_range('day', datetime.fromisoformat(todo['start']), datetime.fromisoformat(todo['end'])):
        if current_todo is not todo:
            break

        s, e = d

        ## skip ever if day for to_do already scraped
        base_name = f'./data/{output_folder}/{s.format("YYYY-MM-DD")}'
        if isfile(f'{base_name}_raw.json'):
            print('file already, skipping...')
            continue
        else:
            time.sleep(1)
            print(f'working on this day: {base_name}_raw.jsonl')
    else:
        with open('./todos/finished_jobs.txt', 'a') as af:
            af.write(f'{json.dumps(todo)}\n')
        todo = get_next_todo()

# experiment with this a lot
