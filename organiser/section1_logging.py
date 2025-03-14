import logging

def configure_logging():
    logging.basicConfig(
        filename='organise.log',
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

configure_logging()