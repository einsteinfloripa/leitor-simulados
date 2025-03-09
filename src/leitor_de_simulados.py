import argparse

# Must be imported before any other module
from utils.log import LoggingSystem
from gui.app import WindowApplication


def main(log_level: str):
    LoggingSystem.initilize(log_level=log_level)
    app = WindowApplication()
    app.mainloop()
    LoggingSystem.shutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Leitor de Simulados")
        
    parser.add_argument(
        "--loglevel",
        choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    args = parser.parse_args()
    main(log_level=args.loglevel)