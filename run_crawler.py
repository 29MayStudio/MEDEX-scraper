import logging
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def subprocess_cmd(command):
    logging.info(f"Running command: {command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    logging.info(proc_stdout)

# Since we only use the single Medicine crawler, we run med_crawl,
# followed by the mapper command to connect scraped generics to medicines.
subprocess_cmd('python manage.py med_crawl')
subprocess_cmd('python manage.py med_generic_mapper')
