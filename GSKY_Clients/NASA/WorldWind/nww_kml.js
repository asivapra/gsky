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
 * Illustrates how to load and display a KML file.
 */
// -----------------------------------------------------------------------------
// AVS: Code added to save the KML in user-specific file  
function CSReadCookie() 
{
	var cookies = document.cookie;
	cookies = unescape(cookies);
	return cookies;
}
function ParseCookies(cookies,id)
{
	var cookies_array = cookies.split(";");
	nc = cookies_array.length;
	for (var j=0; j < nc; j++)
	{
		var i = cookies_array[j].indexOf(id, 0);
		if (i >= 0) 
		{
				var i = cookies_array[j].indexOf('=', 0);
				var cookie_value = cookies_array[j].substring(i+1,cookies_array[j].length);
				return cookie_value;
		}
	}
	return "";
}
var nww_kml = 'data/nww/nww.kml';
var cookiename = "GSKY-NWW-GEOGLAM";
var cookies = CSReadCookie(cookiename);
var cookie_value = ParseCookies(cookies,cookiename);
if (cookie_value)
{
	nww_kml = "data/nww/nww_"+cookie_value+".kml";
}
// AVS: End of added code
// -----------------------------------------------------------------------------
requirejs(['./WorldWindShim',
        './LayerManager'],
    function (WorldWind,
              LayerManager) {

        // Tell WorldWind to log only warnings and errors.
        WorldWind.Logger.setLoggingLevel(WorldWind.Logger.LEVEL_WARNING);

        // Create the WorldWindow.
        var wwd = new WorldWind.WorldWindow("canvasOne");

        // Create and add layers to the WorldWindow.
        var layers = [
            // Imagery layers.
            {layer: new WorldWind.BMNGLayer(), enabled: true},
            {layer: new WorldWind.BingAerialWithLabelsLayer(null), enabled: true},
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
// AVS: Changed the path for the KML file. This file is dynamically created by the CGI
//alert(nww_kml);
		var kmlFilePromise = new WorldWind.KmlFile(nww_kml, [new WorldWind.KmlTreeVisibility('treeControls', wwd)]);
        kmlFilePromise.then(function (kmlFile) {
            var renderableLayer = new WorldWind.RenderableLayer("Surface Shapes");
            renderableLayer.addRenderable(kmlFile);
//console.log(renderableLayer);
            wwd.addLayer(renderableLayer);
            wwd.redraw();
        });

        // Now set up to handle highlighting.
        var highlightController = new WorldWind.HighlightController(wwd);
    });