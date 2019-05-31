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

// Center the map on: Alice Springs
		wwd.navigator.lookAtLocation.latitude = -26; 
		wwd.navigator.lookAtLocation.longitude = 134;
		wwd.navigator.range = 4e6; // 4 million meters above the ellipsoid
// Redraw the WorldWindow.
		wwd.redraw();

        // Create and add layers to the WorldWindow.
        var layers = [
            // Imagery layers.
            {layer: new WorldWind.BMNGLayer(), enabled: false},
            {layer: new WorldWind.BMNGLandsatLayer(), enabled: false},
            {layer: new WorldWind.BingAerialLayer(null), enabled: false},
            {layer: new WorldWind.BingAerialWithLabelsLayer(null), enabled: true},
            {layer: new WorldWind.BingRoadsLayer(null), enabled: false},
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
        var serviceAddress = "https://gsky.nci.org.au/ows/dea?Service=WMS&REQUEST=GetCapabilities&VERSION=1.3.0";
//        var serviceAddress = "https://gsky.nci.org.au/ows/dea?time=2013-03-19T00:00:00.000Z&SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0";
        // Named layer displaying Average Temperature data

		var layerName1 = 	"landsat5_geomedian";
		var layerName2 = 	"landsat5_nbar_16day";
		var layerName3 = 	"landsat5_nbar_daily";
		var layerName4 = 	"landsat5_nbart_16day";
		var layerName5 = 	"landsat5_nbart_daily";
		var layerName6 = 	"landsat7_geomedian";
		var layerName7 = 	"landsat7_nbar_16day";
		var layerName8 = 	"landsat7_nbar_daily";
		var layerName9 = 	"landsat7_nbart_16day";
		var layerName10 = 	"landsat7_nbart_daily";
		var layerName11 = 	"landsat8_geomedian";
		var layerName12 = 	"landsat8_nbar_16day";
		var layerName13 = 	"landsat8_nbar_daily";
		var layerName14 = 	"landsat8_nbart_16day";
		var layerName15 = 	"landsat8_nbart_daily";
		var layerName16 = 	"sentinel2_nbart_daily";
		var layerName17 = 	"wofs";
		
		var layerTitle1 = 	"LS5 surface reflectance geomedian";
		var layerTitle2 = 	"16D LS5 surface reflectance (NBAR)";
		var layerTitle3 = 	"Daily LS5 surface reflectance (NBAR)";
		var layerTitle4 = 	"16D LS5 surface reflectance (NBART)";
		var layerTitle5 = 	"Daily LS5 surface reflectance (NBART)";
		var layerTitle6 = 	"LS7 surface reflectance geomedian";
		var layerTitle7 = 	"16D LS7 surface reflectance (NBAR)";
		var layerTitle8 = 	"Daily LS7 surface reflectance (NBAR)";
		var layerTitle9 = 	"16D LS7 surface reflectance (NBART)";
		var layerTitle10 = 	"Daily LS7 surface reflectance (NBART)";
		var layerTitle11 = 	"LS8 surface reflectance geomedian";
		var layerTitle12 = 	"16D LS8 surface reflectance (NBAR)";
		var layerTitle13 = 	"Daily LS8 surface reflectance (NBAR)";
		var layerTitle14 = 	"16D LS8 surface reflectance (NBART)";
		var layerTitle15 = 	"Daily LS8 surface reflectance (NBART)";
		var layerTitle16 = 	"Sentinel 2 Analysis Ready Data";
		var layerTitle17 = 	"Water Observation Feature Layer";

        // landsat5_nbart_16day
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
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
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

        var createLayer6 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName6);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle6;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer7 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName7);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle7;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer8 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName8);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle8;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer9 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName9);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle9;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer10 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName10);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle10;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer11 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName11);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle11;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer12 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName12);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle12;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer13 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName13);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle13;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer14 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName14);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle14;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = true;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer15 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName15);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle15;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer16 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName16);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle16;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        var createLayer17 = function (xmlDom) {
            var wms = new WorldWind.WmsCapabilities(xmlDom);
            var wmsLayerCapabilities = wms.getNamedLayer(layerName17);
            var wmsConfig = WorldWind.WmsLayer.formLayerConfiguration(wmsLayerCapabilities);
            wmsConfig.title = layerTitle17;
            var wmsLayer = new WorldWind.WmsLayer(wmsConfig);
            wmsLayer.enabled = false;
            wwd.addLayer(wmsLayer);
            layerManager.synchronizeLayerList();
        };

        // Called if an error occurs during WMS Capabilities document retrieval
        var logError = function (jqXhr, text, exception) {
            console.log("There was a failure retrieving the capabilities document: " + text + " exception: " + exception);
        };

//        $.get(serviceAddress0).done(createLayer0).fail(logError);
        $.get(serviceAddress).done(createLayer1).fail(logError);
        $.get(serviceAddress).done(createLayer2).fail(logError);
        $.get(serviceAddress).done(createLayer3).fail(logError);
        $.get(serviceAddress).done(createLayer4).fail(logError);
        $.get(serviceAddress).done(createLayer5).fail(logError);
        $.get(serviceAddress).done(createLayer6).fail(logError);
        $.get(serviceAddress).done(createLayer7).fail(logError);
        $.get(serviceAddress).done(createLayer8).fail(logError);
        $.get(serviceAddress).done(createLayer9).fail(logError);
        $.get(serviceAddress).done(createLayer10).fail(logError);
        $.get(serviceAddress).done(createLayer11).fail(logError);
        $.get(serviceAddress).done(createLayer12).fail(logError);
        $.get(serviceAddress).done(createLayer13).fail(logError);
        $.get(serviceAddress).done(createLayer14).fail(logError);
        $.get(serviceAddress).done(createLayer15).fail(logError);
        $.get(serviceAddress).done(createLayer16).fail(logError);
        $.get(serviceAddress).done(createLayer17).fail(logError);

        // Create a layer manager for controlling layer visibility.
        var layerManager = new LayerManager(wwd);
    });