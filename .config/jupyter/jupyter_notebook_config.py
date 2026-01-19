# ~/.config/jupyter/jupyter_notebook_config.py
c = get_config()
c.NotebookApp.ip = '127.0.0.1'
c.NotebookApp.open_browser = False
c.NotebookApp.notebook_dir = '~/notebooks'
c.NotebookApp.allow_remote_access = True
c.NotebookApp.terminals_enabled = True

