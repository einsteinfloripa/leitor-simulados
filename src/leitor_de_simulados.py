from utils.filehandler import FileHandler
from gui.App import WindowApplication



# TODO: LOGGING

# FILE HANDLER
FileHandler.set_path( "MODELS_PATH", './models' )

def main():
    app = WindowApplication()
    app.mainloop()

if __name__ == "__main__":
    main()