import bpy

def run(cmd):
    import subprocess, shlex
    subprocess.run(shlex.split(cmd), check=True)

def start(cmd):
    import subprocess, shlex
    return subprocess.Popen(shlex.split(cmd))

def list_submodules(package):
    
    import pkgutil, importlib
    
    """List all submodules of a given package without importing them."""
    submodules = []
    for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
        submodules.append(importlib.import_module(name))
        if is_pkg:
            submodules.extend(list_submodules(importlib.import_module(name)))
    return submodules

def generate(**kwargs):
    import importlib
    import os
    import inspect
    import pdoc
    import pathlib

    if kwargs['target_dir'] == "":
        mod = importlib.import_module(kwargs['module_name'])
        script_dir = os.path.dirname(inspect.getfile(mod))
        path = os.path.join(script_dir, "docs")
        os.makedirs(path, exist_ok=True)
        path = pathlib.Path(path)
    else:
        path = kwargs['target_dir']
        path = pathlib.Path(path)
        #path = path.joinpath(kwargs["module_name"])

    pdoc.pdoc(kwargs['module_name'], output_directory=path)

    return path

    
def generate_and_run(**kwargs):

    import sys
    from .. import Pid
    
    path = generate(**kwargs)

    if kwargs['server']:
     
        try: 
            exe = sys.executable
            port = kwargs['port']
            cmd = f"{exe} -m http.server -d{path} {port}"
            Pid.pid = start(cmd).pid
        except OSError as e:
            print(e)

        url = f"http://localhost:{port}/index.html"
        bpy.ops.wm.url_open(url=url)

    return path

class PdocInstallOperator(bpy.types.Operator):
    """Install pdoc, if necessary"""
    bl_idname = "pdoc.install"
    bl_label = "Install pdoc"
    def execute(self, context):
        import sys
        exe = sys.executable
        cmd = f"{exe} -m pip install pdoc"
        run(cmd)
        return {"FINISHED"}
        
class KillServerOperator(bpy.types.Operator):
    """Kill the server process if one was started previously"""
    bl_idname = "pdoc.kill"
    bl_label = "Generate Documentation"
    pid : bpy.props.IntProperty(name="pid")
    def execute(self, context):
        import signal, os
        from .. import Pid

        if self.pid > -1:
            os.kill(self.pid, signal.SIGTERM)
            Pid.pid = -1
            return {"FINISHED"}
        return {"CANCELLED"}

class DocumentationOperator(bpy.types.Operator):
    """Generates Documentation with pdoc for the given module and its submodules"""
    bl_idname = "pdoc.generate"
    bl_label = "Generate Documentation"
    module_name : bpy.props.StringProperty(name="module_name")
    server: bpy.props.BoolProperty(name="server", default=False)
    port: bpy.props.IntProperty(name="port", min=0, max=65535, default=8000)
    target: bpy.props.StringProperty(name="target", default="")

    def execute(self, context):
        if self.module_name != "":
            generate_and_run(module_name=self.module_name, target_dir=self.target, server=self.server, port=self.port)
            self.report({'INFO'}, "Documentation generated")
            return {'FINISHED'}
        self.report({'ERROR'}, "Please specify a module name")
        return {'CANCELLED'}

# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register():
    bpy.utils.register_class(DocumentationOperator)
    bpy.utils.register_class(KillServerOperator)
    bpy.utils.register_class(PdocInstallOperator)

def unregister():
    bpy.utils.unregister_class(KillServerOperator)
    bpy.utils.unregister_class(DocumentationOperator)
    bpy.utils.unregister_class(PdocInstallOperator)
