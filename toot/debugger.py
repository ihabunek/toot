from os import getenv

def initialize_debugger():
    import multiprocessing

    if multiprocessing.current_process().pid > 1:
        import debugpy

        debugpy.listen(("0.0.0.0", 9000))
        print("VSCode Debugger is ready to be attached on port 9000, press F5", flush=True)
        debugpy.wait_for_client()
        print("VSCode Debugger is now attached", flush=True)
