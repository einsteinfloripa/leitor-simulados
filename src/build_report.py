import argparse
import builder

from aux.filehandler import FileHandler
from pathlib import Path

from aux import log

logger = log.get_new_logger('build report')

def build_report(falied):

    logger.debug('getting paths...')
    dir_paths : dict[str, list[Path]] = FileHandler.get_input_paths_builder()
    
    report = {}
    
    logger.debug('building success reports...')
    for path in dir_paths['success']:
        name = path.name.split('.')[0]
        report.update({name : builder.build(path, status='success')})
        logger.warning(f'{path.name} added to report')

    logger.debug('building falieds reports...') 
    if falied:
        for path in dir_paths['falied']:
            name = path.name.split('.')[0]
            report.update({name : builder.build(path, status='falied')})
            logger.warning(f'{path.name} added to report')


    FileHandler.save_report(report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_directory', default='scanner_output', required=True)
    parser.add_argument('-o', '--output', default='')
    parser.add_argument('-p', '--prova', default='PS', choices=['PS', 'SIMUENEM', 'SIMUFSC'])
    # run script in falied scans too
    parser.add_argument('-a', '--falied', action='store_true', default=False)
    parser.add_argument('--continue_on_fail', action='store_true', default=False)
    parser.add_argument(
    "--logfile",
    nargs="*",
    type=str,
    default=None,
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    help="log file path",
    )

    args = parser.parse_args()


    if args.logfile: log.set_log_level(args.logfile)
    else: log.remove_filehandler()

    FileHandler.set_path('INPUT_DIR', args.input_directory)
    FileHandler.make_and_set_dir('OUTPUT_DIR', args.output)


    builder.PROVA = args.prova
    builder.CONTINUE_ON_FAIL = args.continue_on_fail
    builder.load_builder()
    build_report(args.falied)

if __name__ == '__main__':
    main()

