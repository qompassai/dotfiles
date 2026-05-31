// SPDX-FileCopyrightText: See AUTHORS file
//
// SPDX-License-Identifier: GPL-3.0-or-later

import * as d3 from "d3-graphviz";

export function init(injected_dot_graph: string | null) {
  let dot_str = null;
  if (injected_dot_graph) {
    dot_str = injected_dot_graph;
  } else if (location.hash.length > 1) {
    dot_str = decodeURIComponent(location.hash.substring(1));
  } else {
    dot_str = `digraph {
      no -> input;
      input -> provided;
    }`;
  }

  const svg_div = document.getElementById("svg-div");
  const info_div = document.getElementById("info");
  const save_svg_btn = document.getElementById("save-svg-btn");

  window.addEventListener("unhandledrejection", () => {
    info_div.innerText =
      "Error generating graph, maybe it's too large or badly formatted.";
  });

  const graphviz = d3.graphviz(svg_div, {
    useWorker: false,
    zoomScaleExtent: [0.001, 100],
  });
  graphviz.renderDot(dot_str, () => {
    info_div.style.display = "none";
    save_svg_btn.style.display = "block";
  });

  save_svg_btn.addEventListener("click", () => {
    const svg_str = svg_div.innerHTML;
    const blob = new Blob([svg_str], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "graph.svg";
    document.body.append(link);
    link.click();

    URL.revokeObjectURL(url);
    link.remove();
  });
}
