(function(H) {
  if (!H.exporting) {
    H.exporting = function() {};
  }

  // This will be redefined later;
  var oldExport = H.Chart.prototype.exportChart;
  H.Chart.prototype.exportChart = function() {};

  // Set the URL of the export server to a non-existant one, just to be sure.
  var defaultHighChartsOptions = H.getOptions() || {};
  if(!defaultHighChartsOptions.exporting) {
    defaultHighChartsOptions.exporting = {};
  }
  defaultHighChartsOptions.exporting.url = "http://127.0.0.1:666/";
  if(!defaultHighChartsOptions.exporting.csv) {
    defaultHighChartsOptions.exporting.csv = {};
  }
  defaultHighChartsOptions.exporting.csv.url = "http://127.0.0.1:666/";
  H.setOptions(defaultHighChartsOptions);

  var MIME_TYPES = {
    "PDF": "application/pdf",
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "SVG": "image/svg+xml",
    "CSV": "text/csv",
    "XLS": "application/vnd.ms-excel"
  };

  var MIME_TYPE_TO_EXTENSION = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpeg",
    "image/svg+xml": ".svg",
    "text/csv": ".csv",
    "application/vnd.ms-excel": ".xls"
  };

  var TRANSLATION_KEY_TO_MIME_TYPES = {
    "downloadPDF": "application/pdf",
    "downloadPNG": "image/png",
    "downloadJPEG": "image/jpeg",
    "downloadSVG": "image/svg+xml"
  };
  TRANSLATION_KEY_TO_MIME_TYPES[H.getOptions().lang.downloadCSV || 'Download CSV'] = "text/csv";
  TRANSLATION_KEY_TO_MIME_TYPES[H.getOptions().lang.downloadXLS || 'Download XLS'] = "application/vnd.ms-excel";

  // This var indicates if the browser supports HTML5 download feature
  var browserSupportDownload = false;
  var a = document.createElement('a');
  if (typeof window.btoa != "undefined" && typeof a.download != "undefined") {
    browserSupportDownload = true;
  }
  // This is for IE support of Blob
  var browserSupportBlob = window.Blob && window.navigator.msSaveOrOpenBlob;

  /**
   * Describes the MIME types that this module supports.
   * Additionnally, you can call `support(mimeType)` to check
   * that this type is available on the current platform.
   */
  H.exporting.MIME_TYPES = MIME_TYPES;

  /**
   * Little helper function that you can set to the `filename` configuration
   * option to use the chart title for the filename when downloaded.
   */
  H.exporting.USE_TITLE_FOR_FILENAME = function(options, chartOptions) {
    var title = this.title ? this.title.textStr.replace(/ /g, '-').toLowerCase() : 'chart';
    return title;
  };

  var supportStatus = {};
  var buildSupportStatus = function() {
    var hasDownloadOrBlob = browserSupportDownload || browserSupportBlob;

    supportStatus[MIME_TYPES.CSV] = hasDownloadOrBlob && (H.Chart.prototype.getCSV !== undefined);
    supportStatus[MIME_TYPES.XLS] = hasDownloadOrBlob && (H.Chart.prototype.getTable !== undefined);

    var svgSupport = (H.Chart.prototype.getSVG !== undefined);

    supportStatus[MIME_TYPES.SVG] = hasDownloadOrBlob && svgSupport && (window.btoa !== undefined);

    // Canvg uses a function named RGBColor, but it's also a not widely known standard object
    // http://www.w3.org/TR/2000/REC-DOM-Level-2-Style-20001113/css.html#CSS-RGBColor
    // Fugly, but heh.
    var rbgColorSupport = false;
    try {
      rbgColorSupport = (new RGBColor("").ok) !== undefined;
    }
    catch(e) {}
    // We also check that a canvas element can be created.
    var canvas = document.createElement('canvas');
    var canvgSupport = typeof canvg !== "undefined" && typeof RGBColor != "undefined" &&
    rbgColorSupport && canvas.getContext && canvas.getContext('2d');

    supportStatus[MIME_TYPES.PNG] = hasDownloadOrBlob && svgSupport && canvgSupport;
    // On IE, it relies on canvas.msToBlob() which always returns PNG
    supportStatus[MIME_TYPES.JPEG] = /* useless, see last param: hasDownloadOrBlob && */
        svgSupport && canvgSupport && browserSupportDownload;

    supportStatus[MIME_TYPES.PDF] = hasDownloadOrBlob && svgSupport && canvgSupport && (typeof jsPDF !== "undefined");

  };
  buildSupportStatus();

  /**
   * Checks if the supplied MIME type is available on the
   * current platform for a chart to be exported in.
   * @param mimeType {String} The MIME type.
   * @returns {boolean} <code>true</code> if the MIME type is available on the
   *    current platform.
   */
   H.exporting.supports = function(mimeType) {
    if(supportStatus[mimeType]) {
      return supportStatus[mimeType];
    }
    else {
      return false;
    }
  };


  // Remove unsupported download features from the menu
  var menuItems = H.getOptions().exporting.buttons.contextButton.menuItems,
      menuItem,
      textKey,
      text,
      mimeType,
      handlerBuilder = function(mimeType) {
        return function() {
          this.exportChartLocal({
            type: mimeType,
            csv: {
              itemDelimiter: ';'
            }
          });
        }
      };
  for(var i in menuItems) {
    menuItem = menuItems[i];
    textKey = menuItems[i].textKey;
    text = menuItems[i].text; // export-csv do not use a textKey attribute
    mimeType = TRANSLATION_KEY_TO_MIME_TYPES[textKey] || TRANSLATION_KEY_TO_MIME_TYPES[text];
    if(mimeType) {
      if(!H.exporting.supports(mimeType)) {
        // Setting enabled = false isn't enough.
        delete menuItems[i];
      }
      else {
        // Redefines click handler to use our method.
        menuItems[i].onclick = handlerBuilder(mimeType);
      }
    }
  }

  /*
   * Converts a SVG string to a canvas element
   * thanks to canvg.
   * @param svg {String} A SVG string.
   * @param width {Integer} The rasterized width.
   * @param height {Integer} The rasterized height.
   * @return {DOMNode} a canvas element.
   */
  var svgToCanvas = function(svg, width, height, callback) {
    var canvas = document.createElement('canvas');

    canvas.setAttribute('width', width);
    canvas.setAttribute('height', height);

    canvg(canvas, svg, {
      ignoreMouse: true,
			ignoreAnimation: true,
			ignoreDimensions: true,
			ignoreClear: true,
      offsetX: 0,
      offsetY: 0,
      scaleWidth: width,
      scaleHeight: height,
      renderCallback: function() { callback(canvas); }
    });

    return canvas;
  };

  /**
   * An object to simplifies the retrieval of options in
   * multiple bundles.
   * @param opts {Object} Multiple, an object containing options.
   */
  var Opt = function(opts1, opt2, dotdotdot) {
    this.bundles = arguments;
  };

  /**
   * Fetch the value associated with the specified key in the bundles.
   * First one defined is the one returned.
   * @param key {String} The key.
   * @param value {mixed} The first defined value in the bundles or
   *    <code>undefined</code> if none is found.
   */
  Opt.prototype.get = function(key) {
    for(var i = 0; i < this.bundles.length; i++) {
      if(this.bundles[i] && this.bundles[i][key] !== undefined) {
        return this.bundles[i][key];
      }
    }
    return undefined;
  };

  // Default options.
  var defaultExportOptions = {
    type: MIME_TYPES.PNG,
    scale: 2,
    filename: "chart",
    csv: {
      useLocalDecimalPoint: true
    }
  };

  var preRenderCsvXls = function (highChartsObject, options, chartOptions) {
      // Copies some values from the options, so we can set it and change those
      // through the options argument.
      var hasCSVOptions = highChartsObject.options.exporting && highChartsObject.options.exporting.csv;
      var csvOpt = new Opt((options || {}).csv, (highChartsObject.options.exporting || {}).csv, defaultExportOptions.csv);

      var oldOptions = {},
      optionsToCopy = ["dateFormat", "itemDelimiter", "lineDelimiter"],
      optionToCopy;
      for (var i in optionsToCopy) {
        optionToCopy = optionsToCopy[i];
        if (csvOpt.get(optionToCopy)) {
          if (!highChartsObject.options.exporting) {
            highChartsObject.options.exporting = {};
          }
          if (!highChartsObject.options.exporting.csv) {
            highChartsObject.options.exporting.csv = {};
          }

          oldOptions[optionToCopy] = highChartsObject.options.exporting.csv[optionToCopy];
          highChartsObject.options.exporting.csv[optionToCopy] = csvOpt.get(optionToCopy);
        }
      }

      return {
        hasCSVOptions: hasCSVOptions,
        csvOpt: csvOpt,
        useLocalDecimalPoint: csvOpt.get("useLocalDecimalPoint"),
        optionsToCopy: optionsToCopy,
        oldOptions: oldOptions
      };
    };

  var renderCsv = function(highChartsObject, context, callback) {
      var data = {
          content: undefined,
          datauri: undefined,
          blob: undefined
        };

      var csv = highChartsObject.getCSV(context.useLocalDecimalPoint);
      data.content = csv;

      callback(data);
    };

  var renderXls = function(highChartsObject, context, callback) {
      var data = {
          content: undefined,
          datauri: undefined,
          blob: undefined
        };

      var xls = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">' +
        '<head><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet>' +
        '<x:Name>Sheet</x:Name>' +
        '<x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->' +
        '<style>td{border:none;font-family: Calibri, sans-serif;} .number{mso-number-format:"0.00";}</style>' +
        '<meta name=ProgId content=Excel.Sheet>' +
        '</head><body>' +
        highChartsObject.getTable(context.useLocalDecimalPoint) +
        '</body></html>';
      data.content = xls;

      callback(data);
    };

  var postRenderCsvXls = function(highChartsObject, context) {
      if (context.hasCSVOptions) {
        for (var i in context.optionsToCopy) {
          optionToCopy = context.optionsToCopy[i];
          if (context.csvOpt.get(optionToCopy)) {
            highChartsObject.options.exporting.csv[optionToCopy] = context.oldOptions[optionToCopy];
          }
        }
      }
      else {
        delete highChartsObject.options.exporting.csv;
      }
    };

  var preRenderImage = function (highChartsObject, options, chartOptions) {
    var opt = new Opt(options, highChartsObject.options.exporting, defaultExportOptions);

    var scale = opt.get("scale"),
    sourceWidth = highChartsObject.options.width || opt.get("sourceWidth") || highChartsObject.chartWidth,
    sourceHeight = highChartsObject.options.height || opt.get("sourceHeight") || highChartsObject.chartHeight,
    destWidth = sourceWidth * scale,
    destHeight = sourceHeight * scale;

    var cChartOptions = chartOptions || highChartsObject.options.exporting && highChartsObject.options.exporting.chartOptions || {};
    if (!cChartOptions.chart) {
      cChartOptions.chart = { width: destWidth, height: destHeight };
    }
    else {
      cChartOptions.chart.width = destWidth;
      cChartOptions.chart.height = destHeight;
    }

    var svg = highChartsObject.getSVG(cChartOptions);

    return {
      svg: svg,
      destWidth: destWidth,
      destHeight: destHeight
    };
  };

  var renderSvg = function(highChartsObject, context, callback) {
      var data = {
          content: undefined,
          datauri: undefined,
          blob: undefined
        };

      data.content = context.svg;

      callback(data);
  };

  var renderPngJpeg = function(highChartsObject, context, callback) {
      var data = {
          content: undefined,
          datauri: undefined,
          blob: undefined
        };

      svgToCanvas(context.svg, context.destWidth, context.destHeight, function(canvas) {
        data.datauri = context.browserSupportDownload && canvas.toDataURL && canvas.toDataURL(context.type);
        data.blob = (context.type == MIME_TYPES.PNG) && !context.browserSupportDownload && canvas.msToBlob && canvas.msToBlob();

        callback(data);
      });
  };

  var renderPdf = function(highChartsObject, context, callback) {
      var data = {
          content: undefined,
          datauri: undefined,
          blob: undefined
        };

      svgToCanvas(context.svg, context.destWidth, context.destHeight, function(canvas) {
        var doc = new jsPDF('l', 'mm', [context.destWidth, context.destHeight]);;
        doc.addImage(canvas, 'JPEG', 0, 0, context.destWidth, context.destHeight);

        data.datauri = context.browserSupportDownload && doc.output('datauristring');
        data.blob = !context.browserSupportDownload && doc.output('blob');

        callback(data);
      });
  };


  var download = function(highChartsObject, context, data) {
    if (!data || (!data.content && !(data.datauri || data.blob))) {
      throw new Error("Something went wrong while exporting the chart");
    }

    if (context.browserSupportDownload && (data.datauri || data.content)) {
      a = document.createElement('a');
      a.href = data.datauri || ('data:' + context.type + ';base64,' + window.btoa(unescape(encodeURIComponent(data.content))));
      a.download = context.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
    else if (context.browserSupportBlob && (data.blob || data.content)) {
      blobObject = data.blob || new Blob([data.content], { type: context.type });
      window.navigator.msSaveOrOpenBlob(blobObject, context.filename);
    }
    else {
      window.open(data);
    }
  };

  /**
   * Redefines the export function of the official exporting module.
   * @param options {Object} Overload the export options defined in the chart.
   * @param chartOptions {Object} Additionnal chart options.
   */
  H.Chart.prototype.exportChartLocal = function(options, chartOptions) {
    var opt = new Opt(options, this.options.exporting, defaultExportOptions);

    var type = opt.get("type");
    if (!H.exporting.supports(type)) {
      throw new Error("Unsupported export format on this platform: " + type);
    }

    var steps = {
      rendering: {},
      download: download
    };

    steps.rendering[MIME_TYPES.CSV] = {
      preRender: preRenderCsvXls,
      render: renderCsv,
      postRender: postRenderCsvXls
    };

    steps.rendering[MIME_TYPES.XLS] = {
      preRender: preRenderCsvXls,
      render: renderXls,
      postRender: postRenderCsvXls
    };

    steps.rendering[MIME_TYPES.SVG] = {
      preRender: preRenderImage,
      render: renderSvg
    };

    steps.rendering[MIME_TYPES.PNG] = {
      preRender: preRenderImage,
      render: renderPngJpeg
    };

    steps.rendering[MIME_TYPES.JPEG] = {
      preRender: preRenderImage,
      render: renderPngJpeg
    };

    steps.rendering[MIME_TYPES.PDF] = {
      preRender: preRenderImage,
      render: renderPdf
    };

    var highChartsObject = this;

    var context;
    if(steps.rendering[type].preRender) {
      context = steps.rendering[type].preRender(highChartsObject, options, chartOptions);
    }
    else {
      context = {};
    }

    context.type = type;
    context.browserSupportDownload = browserSupportDownload;
    context.browserSupportBlob = browserSupportBlob;

    var filename = opt.get("filename");
    if(typeof filename === "function") {
      context.filename = filename.bind(this)(options, chartOptions) + MIME_TYPE_TO_EXTENSION[type];
    }
    else {
      context.filename = opt.get("filename") + MIME_TYPE_TO_EXTENSION[type];
    }

    steps.rendering[type].render(highChartsObject, context, function(data) {
      if(steps.rendering[type].postRender) {
        steps.rendering[type].postRender(highChartsObject, context);
      }

      steps.download(highChartsObject, context, data);
    });
  }

  // Forces method from export module to use the local version
  H.Chart.prototype.exportChart = H.Chart.prototype.exportChartLocal;

}(Highcharts));
