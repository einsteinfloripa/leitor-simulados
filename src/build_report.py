from datetime import datetime

import argparse
import builder

from aux.filehandler import FileHandler
from pathlib import Path

from aux import log

logger = log.get_new_logger('build report')

def build_report(falied, ec):
    
    logger.debug('getting paths...')
    dir_paths : dict[str, list[Path]] = FileHandler.get_input_paths_builder()
    
    report = {}
    report['config'] = {
        'prova' : builder.PROVA,
        'continue_on_fail' : builder.CONTINUE_ON_FAIL,
        'error_correction' : ec,
        'datetime' : datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
    }
    
    logger.debug('building success reports...')
    for path in dir_paths['success']:
        logger.error(f'buiding report for {path.name}')
        name = path.name.split('.')[0]
        report.update({name : builder.build(path, status='success', ec=False)})
        logger.warning(f'{path.name} added to report')

    logger.debug('building falied reports...') 
    if falied:
        for path in dir_paths['falied']:
            logger.error(f'buiding report for {path.name}')
            name = path.name.split('.')[0]
            report.update({name : builder.build(path, status='falied', ec=ec)})
            logger.warning(f'{path.name} added to report')


    FileHandler.save_report(report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_directory', default='scanner_output', required=True)
    parser.add_argument('-o', '--output_directory', default='')
    parser.add_argument('-p', '--prova', default='PS', choices=['PS', 'SIMUENEM', 'SIMUFSC'])
    parser.add_argument(
        '-f', '--falied_to', action='store_true', default=False,
        help='run script in falied scans too'
    )
    parser.add_argument(
        '--continue_on_fail', action='store_true', default=False,
        help='dont stop if it finds a falied scan'
    )
    parser.add_argument(
        '--error_correction',
        nargs='+',
        type=str,
        choices=['cpf', 'questions'],
        help='try to correct the errors/missing detections in falied scans'
    )
    parser.add_argument(
    "--logfile",
    nargs="*",
    type=str,
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    help="log file generation with the specified level defined",
    )

    args = parser.parse_args()

    if args.error_correction is None:
        args.error_correction = []
    elif 'questions' in args.error_correction:
        raise NotImplementedError('question blocks error correction is not implemented yet')


    if args.logfile is not None:
        try:
            log.set_log_level(args.logfile)
        except ValueError:
            log.set_log_level(['INFO'])
    else: log.remove_filehandler()
    
    FileHandler.set_path('INPUT_DIR', args.input_directory)
    FileHandler.make_and_set_dir('OUTPUT_DIR', args.output_directory)


    builder.PROVA = args.prova
    builder.CONTINUE_ON_FAIL = args.continue_on_fail
    builder.load_builder()
    build_report(args.falied_to, args.error_correction)

if __name__ == '__main__':
    main()

