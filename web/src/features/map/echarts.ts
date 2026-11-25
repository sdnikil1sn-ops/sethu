// ECharts with only what the map needs (tree-shaken, bundled with the app, its own chunk: no CDN).
import { MapChart } from "echarts/charts";
import { TooltipComponent, VisualMapComponent } from "echarts/components";
import { init, registerMap, use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

use([MapChart, TooltipComponent, VisualMapComponent, CanvasRenderer]);

export { init, registerMap };
