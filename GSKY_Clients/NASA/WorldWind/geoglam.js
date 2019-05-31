/*
 * Copyright 2003-2006, 2009, 2017, United States Government, as represented by the Administrator of the
 * National Aeronautics and Space Administration. All rights reserved.
 *
 * The NASAWorldWind/WebWorldWind platform is licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/**
 * Illustrates how to consume imagery from a Web Map Service (WMS).
 */
requirejs(['./WorldWindShim',
        './LayerManager'],
    function (WorldWind,
              LayerManager) {
        "use strict";

        // Tell WorldWind to log only warnings and errors.
        WorldWind.Logger.setLoggingLevel(WorldWind.Logger.LEVEL_WARNING);

        // Create the WorldWindow.
        var wwd = new WorldWind.WorldWindow("canvasOne");

// Center the map on Alice Springs:
		wwd.navigator.lookAtLocation.latitude = -26; 
		wwd.navigator.lookAtLocation.longitude = 134;
		wwd.navigator.range = 8e6; // 8 million meters above the ellipsoid
// Redraw the WorldWindow.
		wwd.redraw();

        // Create and add layers to the WorldWindow.
        var layers = [
            // Imagery layers.
            {layer: new WorldWind.BMNGLayer(), enabled: false},
            {layer: new WorldWind.BMNGLandsatLayer(), enabled: false},
            {layer: new WorldWind.BingAerialLayer(null), enabled: false},
            {layer: new WorldWind.BingAerialWithLabelsLayer(null), enabled: false},
            {layer: new WorldWind.BingRoadsLayer(null), enabled: true},
            // Add atmosphere layer on top of all base layers.
            {layer: new WorldWind.AtmosphereLayer(), enabled: true},
            // WorldWindow UI layers.
            {layer: new WorldWind.CompassLayer(), enabled: true},
            {layer: new WorldWind.CoordinatesDisplayLayer(wwd), enabled: true},
            {layer: new WorldWind.ViewControlsLayer(wwd), enabled: true}
        ];

        for (var l = 0; l < layers.length; l++) {
            layers[l].layer.enabled = layers[l].enabled;
            wwd.addLayer(layers[l].layer);
        }

/* // DO NOT DELETE
        // Web Map Service information from NASA's Near Earth Observations WMS
        var serviceAddress0 = "https://neo.sci.gsfc.nasa.gov/wms/wms?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0";
        // Named layer displaying Average Temperature data
        var layerName0 = "MOD_LSTD_CLIM_M";

        // Called asynchronously to parse and create the WMS layer
        var createLayer0 = function (xmlDom) {
            // Create a WmsCapabilities object from the XML DOM
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            // Retrieve a WmsLayerCapabilities object by the desired layer name
            var wmsLayerCapabilities = wms.getNamedLayer(layerName0);
            // Form a configuration object from the WmsLayerCapability object
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            // Modify the configuration objects title property to a more user friendly title
            wmsConfig.title = "Average Surface Temp";
            // Create the WMS Layer from the configuration object
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            // Add the layers to WorldWind and update the layer manager
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };
*/
        var serviceAddress = "https://gsky.nci.org.au/ows/geoglam?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0"; // Working
//        var serviceAddress = "http://localhost:8080/ows/geoglam?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0";
//        var serviceAddress = "http://130.56.242.15/ows/geoglam?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0";
        // Named layer displaying Average Temperature data
        var layerName1 = "modis_tot_cov_8day";
        var layerName2 = "modis_tot_cov_monthly";
        var layerName3 = "modis_fract_cov_8day";
        var layerName4 = "modis_fract_cov_monthly";
        var layerName5 = "chirps";

		var layerTitle1 = 	"Total Vegetation Cover 8-day";
		var layerTitle2 = 	"Total Vegetation Cover Monthly";
		var layerTitle3 = 	"Vegetation Fractional Cover 8-day";
		var layerTitle4 = 	"Vegetation Fractional Cover Monthly";
		var layerTitle5 = 	"Monthly Precipitation CHIRPS";

        // Called asynchronously to parse and create the WMS layer
        var createLayer1 = function (xmlDom) {
            // Create a WmsCapabilities object from the XML DOM
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            // Retrieve a WmsLayerCapabilities object by the desired layer name
            var wmsLayerCapabilities = wms.getNamedLayer(layerName1);
            // Form a configuration object from the WmsLayerCapability object
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            // Modify the configuration objects title property to a more user friendly title
            wmsConfig.title = layerTitle1;
            // Create the WMS Layer from the configuration object
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;

            // Add the layers to WorldWind and update the layer manager
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer2 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName2);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle2;
wmsConfig.time = "2018-02-18";
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = true;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer3 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName3);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle3;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer4 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName4);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle4;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer5 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName5);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle5;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        // Called if an error occurs during WMS Capabilities document retrieval
        var logError = function (jqXhr, text, exception) {
            console.log("There was a failure retrieving the capabilities document: " + text + " exception: " + exception);
        };

        $.get(serviceAddress).done(createLayer1).fail(logError);
        $.get(serviceAddress).done(createLayer2).fail(logError);
        $.get(serviceAddress).done(createLayer3).fail(logError);
        $.get(serviceAddress).done(createLayer4).fail(logError);
        $.get(serviceAddress).done(createLayer5).fail(logError);

        // Create a layer manager for controlling layer visibility.
        var layerManager = new LayerManager(wwd);       
    });