# Core Debug Tools for Blender

The features can be found in the following menus:

- `Topbar > Help > Debug`
- `Node Editor > Node > Debug`

This extension bundles a viewer for dot graph files which is based on [d3-graphviz](https://github.com/magjac/d3-graphviz). The only dependency is a browser that supports WebAssembly.

## Build Instructions

The Python code does not require any build steps.

However, the extension also contains an HTML viewer which needs to be build in the `viewer` directory.

- `cd viewer`
- `npm install`
- `npm run build`
