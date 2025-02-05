import argparse
import logging
import os

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

def main(args):
    logging.info("Program started")
    # Your main logic here
    logging.info("Program finished")

if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(description="Python Boilerplate Script")
    parser.add_argument('--option', type=str, help='An example option')
    args = parser.parse_args()
    main(args)