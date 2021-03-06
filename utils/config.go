	package utils

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image/color"
	"io"
	"io/ioutil"
	"log"
	"math"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"
	"github.com/CloudyKit/jet"
	goeval "github.com/edisonguo/govaluate"
)

var EtcDir = "."
var DataDir = "."

const ReservedMemorySize = 1.5 * 1024 * 1024 * 1024

type ServiceConfig struct {
	OWSHostname       string `json:"ows_hostname"`
	NameSpace         string
	MASAddress        string   `json:"mas_address"`
	WorkerNodes       []string `json:"worker_nodes"`
	OWSClusterNodes   []string `json:"ows_cluster_nodes"`
	TempDir           string   `json:"temp_dir"`
	MaxGrpcBufferSize int      `json:"max_grpc_buffer_size"`
}

// CacheLevel contains the source files of one layer as well as the
// max and min resolutions it represents.  Its fields encode the path
// to the collection and the maximum and minimum resolution that can
// be served.  This enables the definition of different versions of
// the same dataset with different resolutions to speedup response
// times.
type CacheLevel struct {
	Path   string  `json:"path"`
	MinRes float64 `json:"min_res"`
	MaxRes float64 `json:"max_res"`
}

type Mask struct {
	ID         string   `json:"id"`
	Value      string   `json:"value"`
	DataSource string   `json:"data_source"`
	Inclusive  bool     `json:"inclusive"`
	BitTests   []string `json:"bit_tests"`
}

type Palette struct {
	Interpolate bool         `json:"interpolate"`
	Colours     []color.RGBA `json:"colours"`
}

type BandExpressions struct {
	ExprText    []string
	Expressions []*goeval.EvaluableExpression
	VarList     []string
	ExprNames   []string
	ExprVarRef  [][]string
}

// Layer contains all the details that a layer needs
// to be published and rendered
type Layer struct {
	OWSHostname string `json:"ows_hostname"`
	NameSpace   string
	Name        string `json:"name"`
	Title       string `json:"title"`
	Abstract    string `json:"abstract"`
	MetadataURL string `json:"metadata_url"`
	DataURL     string `json:"data_url"`
	//CacheLevels  []CacheLevel `json:"cache_levels"`
	DataSource               string `json:"data_source"`
	StartISODate             string `json:"start_isodate"`
	EndISODate               string `json:"end_isodate"`
	EffectiveStartDate       string
	EffectiveEndDate         string
	TimestampToken           string
	StepDays                 int      `json:"step_days"`
	StepHours                int      `json:"step_hours"`
	StepMinutes              int      `json:"step_minutes"`
	Accum                    bool     `json:"accum"`
	TimeGen                  string   `json:"time_generator"`
	ResFilter                *int     `json:"resolution_filter"`
	Dates                    []string `json:"dates"`
	RGBProducts              []string `json:"rgb_products"`
	RGBExpressions           *BandExpressions
	Mask                     *Mask    `json:"mask"`
	OffsetValue              float64  `json:"offset_value"`
	ClipValue                float64  `json:"clip_value"`
	ScaleValue               float64  `json:"scale_value"`
	Palette                  *Palette `json:"palette"`
	LegendPath               string   `json:"legend_path"`
	LegendHeight             int      `json:"legend_height"`
	LegendWidth              int      `json:"legend_width"`
	Styles                   []Layer  `json:"styles"`
	ZoomLimit                float64  `json:"zoom_limit"`
	MaxGrpcRecvMsgSize       int      `json:"max_grpc_recv_msg_size"`
	WmsPolygonSegments       int      `json:"wms_polygon_segments"`
	WcsPolygonSegments       int      `json:"wcs_polygon_segments"`
	WmsTimeout               int      `json:"wms_timeout"`
	WcsTimeout               int      `json:"wcs_timeout"`
	GrpcWmsConcPerNode       int      `json:"grpc_wms_conc_per_node"`
	GrpcWcsConcPerNode       int      `json:"grpc_wcs_conc_per_node"`
	WmsPolygonShardConcLimit int      `json:"wms_polygon_shard_conc_limit"`
	WcsPolygonShardConcLimit int      `json:"wcs_polygon_shard_conc_limit"`
	BandStrides              int      `json:"band_strides"`
	WmsMaxWidth              int      `json:"wms_max_width"`
	WmsMaxHeight             int      `json:"wms_max_height"`
	WcsMaxWidth              int      `json:"wcs_max_width"`
	WcsMaxHeight             int      `json:"wcs_max_height"`
	WcsMaxTileWidth          int      `json:"wcs_max_tile_width"`
	WcsMaxTileHeight         int      `json:"wcs_max_tile_height"`
	FeatureInfoMaxDataLinks  int      `json:"feature_info_max_data_links"`
	FeatureInfoDataLinkUrl   string   `json:"feature_info_data_link_url"`
	FeatureInfoBands         []string `json:"feature_info_bands"`
	FeatureInfoExpressions   *BandExpressions
	NoDataLegendPath         string `json:"nodata_legend_path"`
}

// Process contains all the details that a WPS needs
// to be published and processed
type Process struct {
	DataSources []Layer    `json:"data_sources"`
	Identifier  string     `json:"identifier"`
	Title       string     `json:"title"`
	Abstract    string     `json:"abstract"`
	MaxArea     float64    `json:"max_area"`
	LiteralData []LitData  `json:"literal_data"`
	ComplexData []CompData `json:"complex_data"`
	IdentityTol float64    `json:"identity_tol"`
	DpTol       float64    `json:"dp_tol"`
	Approx      *bool      `json:"approx,omitempty"`
}

// LitData contains the description of a variable used to compute a
// WPS operation
type LitData struct {
	Identifier    string   `json:"identifier"`
	Title         string   `json:"title"`
	Abstract      string   `json:"abstract"`
	DataType      string   `json:"data_type"`
	DataTypeRef   string   `json:"data_type_ref"`
	AllowedValues []string `json:"allowed_values"`
	MinOccurs     int      `json:"min_occurs"`
}

// CompData contains the description of a variable used to compute a
// WPS operation
type CompData struct {
	Identifier string `json:"identifier"`
	Title      string `json:"title"`
	Abstract   string `json:"abstract"`
	MimeType   string `json:"mime_type"`
	Encoding   string `json:"encoding"`
	Schema     string `json:"schema"`
	MinOccurs  int    `json:"min_occurs"`
}

// Config is the struct representing the configuration
// of a WMS server. It contains information about the
// file index API as well as the list of WMS layers that
// can be served.
type Config struct {
	ServiceConfig ServiceConfig `json:"service_config"`
	Layers        []Layer       `json:"layers"`
	Processes     []Process     `json:"processes"`
}

// ISOFormat is the string used to format Go ISO times
const ISOFormat = "2006-01-02T15:04:05.000Z"

func GenerateDatesAux(start, end time.Time, stepMins time.Duration) []string {
	dates := []string{}
	for !start.After(end) {
		dates = append(dates, start.Format(ISOFormat))
		start = time.Date(start.Year()+1, 1, 1, 0, 0, 0, 0, time.UTC)
	}
	return dates
}

// GenerateDatesMCD43A4 function is used to generate the list of ISO
// dates from its especification in the Config.Layer struct.
func GenerateDatesMCD43A4(start, end time.Time, stepMins time.Duration) []string {
	dates := []string{}
	if int64(stepMins) <= 0 {
		return dates
	}
	year := start.Year()
	for !start.After(end) {
		for start.Year() == year && !start.After(end) {
			dates = append(dates, start.Format(ISOFormat))
			start = start.Add(stepMins)
		}
		if start.After(end) {
			break
		}
		year = start.Year()
		start = time.Date(year, 1, 1, 0, 0, 0, 0, time.UTC)
	}
	return dates
}

func GenerateDatesGeoglam(start, end time.Time, stepMins time.Duration) []string {
	dates := []string{}
	if int64(stepMins) <= 0 {
		return dates
	}
	year := start.Year()
	for !start.After(end) {
		for start.Year() == year && !start.After(end) {
			dates = append(dates, start.Format(ISOFormat))
			nextDate := start.AddDate(0, 0, 4)
			if start.Month() == nextDate.Month() {
				start = start.Add(stepMins)
			} else {
				start = nextDate
			}

		}
		if start.After(end) {
			break
		}
		year = start.Year()
		start = time.Date(year, 1, 1, 0, 0, 0, 0, time.UTC)
	}
	return dates
}

func GenerateDatesChirps20(start, end time.Time, stepMins time.Duration) []string {
	dates := []string{}
	for !start.After(end) {
		dates = append(dates, time.Date(start.Year(), start.Month(), 1, 0, 0, 0, 0, time.UTC).Format(ISOFormat))
		dates = append(dates, time.Date(start.Year(), start.Month(), 11, 0, 0, 0, 0, time.UTC).Format(ISOFormat))
		dates = append(dates, time.Date(start.Year(), start.Month(), 21, 0, 0, 0, 0, time.UTC).Format(ISOFormat))
		start = start.AddDate(0, 1, 0)
	}
	return dates
}

func GenerateMonthlyDates(start, end time.Time, stepMins time.Duration) []string {
	dates := []string{}
	for !start.After(end) {
		dates = append(dates, time.Date(start.Year(), start.Month(), start.Day(), 0, 0, 0, 0, time.UTC).Format(ISOFormat))
		start = start.AddDate(0, 1, 0)
	}
	return dates
}

func GenerateYearlyDates(start, end time.Time, stepMins time.Duration) []string {
	dates := []string{}
	for !start.After(end) {
		dates = append(dates, time.Date(start.Year(), start.Month(), start.Day(), 0, 0, 0, 0, time.UTC).Format(ISOFormat))
		start = start.AddDate(1, 0, 0)
	}
	return dates
}

func GenerateDatesRegular(start, end time.Time, stepMins time.Duration) []string {
	dates := []string{}
	if int64(stepMins) <= 0 {
		return dates
	}
	for !start.After(end) {
		dates = append(dates, start.Format(ISOFormat))
		start = start.Add(stepMins)
	}
	return dates
}

func GenerateDatesMas(start, end string, masAddress string, collection string, namespaces []string, stepMins time.Duration, token string, verbose bool) ([]string, string) {
	emptyDates := []string{}

	start = strings.TrimSpace(start)
	if len(start) > 0 {
		_, err := time.Parse(ISOFormat, start)
		if err != nil {
			log.Printf("start date parsing error: %v", err)
			return emptyDates, token
		}
	}

	end = strings.TrimSpace(end)
	if len(end) > 0 {
		_, err := time.Parse(ISOFormat, end)
		if err != nil {
			log.Printf("end date parsing error: %v", err)
			return emptyDates, token
		}
	}

	ns := strings.Join(namespaces, ",")
	url := strings.Replace(fmt.Sprintf("http://%s%s?timestamps&time=%s&until=%s&namespace=%s&token=%s", masAddress, collection, start, end, ns, token), " ", "%20", -1)
	if verbose {
		log.Printf("config querying MAS for timestamps: %v", url)
	}

	resp, err := http.Get(url)
	if err != nil {
		log.Printf("MAS http error: %v,%v", url, err)
		return emptyDates, token
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Printf("MAS http error: %v,%v", url, err)
		return emptyDates, token
	}

	type MasTimestamps struct {
		Error      string   `json:"error"`
		Timestamps []string `json:"timestamps"`
		Token      string   `json:"token"`
	}

	var timestamps MasTimestamps
	err = json.Unmarshal(body, &timestamps)
	if err != nil {
		log.Printf("MAS json response error: %v", err)
		return emptyDates, token
	}

	if len(timestamps.Error) > 0 {
		log.Printf("MAS returned error: %v", timestamps.Error)
		return emptyDates, token
	}

	if timestamps.Token == token {
		return emptyDates, token
	}

	if verbose {
		log.Printf("MAS returned %v timestamps", len(timestamps.Timestamps))
	}

	if int64(stepMins) > 0 && len(timestamps.Timestamps) > 0 {
		startDate, err := time.Parse(ISOFormat, timestamps.Timestamps[0])
		if err != nil {
			log.Printf("Error parsing MAS returned start date: %v", err)
			return emptyDates, token
		}
		endDate, err := time.Parse(ISOFormat, timestamps.Timestamps[len(timestamps.Timestamps)-1])
		if err != nil {
			log.Printf("Error parsing MAS returned end date: %v", err)
			return emptyDates, token
		}

		refDates := []time.Time{}
		for !startDate.After(endDate) {
			refDates = append(refDates, startDate)
			startDate = startDate.Add(stepMins)
		}
		refDates = append(refDates, endDate)

		aggregatedTimestamps := make([]string, len(refDates))

		iBgn := 0
		for iRef, refTs := range refDates {
			ts0 := time.Time{}
			for it := iBgn; it < len(timestamps.Timestamps); it++ {
				tsStr := timestamps.Timestamps[it]
				ts, err := time.Parse(ISOFormat, tsStr)
				if err != nil {
					log.Printf("Error parsing MAS returned date: %v", err)
					return emptyDates, token
				}

				refDiff := int64(refTs.Sub(ts))
				if refDiff == 0 {
					aggregatedTimestamps[iRef] = tsStr
					iBgn = it + 1
					break
				}

				if refDiff < 0 {
					if it > iBgn {
						refDiff0 := refTs.Sub(ts0)
						if math.Abs(float64(refDiff)) >= math.Abs(float64(refDiff0)) {
							tsStr = timestamps.Timestamps[it-1]
							iBgn = it
						}
					}
					aggregatedTimestamps[iRef] = tsStr
					break
				}

				ts0 = ts
			}
		}

		if verbose {
			log.Printf("Aggregated timestamps: %v, steps: %v", len(aggregatedTimestamps), stepMins)
		}
		return aggregatedTimestamps, timestamps.Token
	}

	return timestamps.Timestamps, timestamps.Token
}

func GenerateDates(name string, start, end time.Time, stepMins time.Duration) []string {
	dateGen := make(map[string]func(time.Time, time.Time, time.Duration) []string)
	dateGen["aux"] = GenerateDatesAux
	dateGen["mcd43"] = GenerateDatesMCD43A4
	dateGen["geoglam"] = GenerateDatesGeoglam
	dateGen["chirps20"] = GenerateDatesChirps20
	dateGen["regular"] = GenerateDatesRegular
	dateGen["monthly"] = GenerateMonthlyDates
	dateGen["yearly"] = GenerateYearlyDates

	if _, ok := dateGen[name]; !ok {
		return []string{}
	}

	return dateGen[name](start, end, stepMins)
}

func LoadAllConfigFiles(rootDir string, verbose bool) (map[string]*Config, error) {
	configMap := make(map[string]*Config)
	err := filepath.Walk(rootDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && info.Name() == "config.json" {
			absPath, _ := filepath.Abs(path)
			relPath, _ := filepath.Rel(rootDir, filepath.Dir(path))
			log.Printf("Loading config file: %s under namespace: %s\n", absPath, relPath)
			config := &Config{}
			e := config.LoadConfigFile(absPath, verbose)
			if e != nil {
				return e
			}
			configMap[relPath] = config

			for i := range config.Layers {
				ns := relPath
				if relPath == "." {
					ns = ""
				}
				config.Layers[i].NameSpace = ns
				for j := range config.Layers[i].Styles {
					config.Layers[i].Styles[j].OWSHostname = config.Layers[i].OWSHostname
					config.Layers[i].Styles[j].NameSpace = config.Layers[i].NameSpace
					if len(config.Layers[i].Styles[j].DataSource) == 0 {
						config.Layers[i].Styles[j].DataSource = config.Layers[i].DataSource
					}
					if config.Layers[i].Styles[j].LegendWidth <= 0 {
						config.Layers[i].Styles[j].LegendWidth = DefaultLegendWidth
					}
					if config.Layers[i].Styles[j].LegendHeight <= 0 {
						config.Layers[i].Styles[j].LegendHeight = DefaultLegendHeight
					}

					bandExpr, err := ParseBandExpressions(config.Layers[i].Styles[j].RGBProducts)
					if err != nil {
						return fmt.Errorf("Layer %v, style %v, RGBExpression parsing error: %v", config.Layers[i].Name, config.Layers[i].Styles[j].Name, err)
					}
					config.Layers[i].Styles[j].RGBExpressions = bandExpr

					if len(config.Layers[i].Styles[j].FeatureInfoBands) > 0 {
						featureInfoExpr, err := ParseBandExpressions(config.Layers[i].Styles[j].FeatureInfoBands)
						if err != nil {
							return fmt.Errorf("Layer %v, style %v, FeatureInfoExpression parsing error: %v", config.Layers[i].Name, config.Layers[i].Styles[j].Name, err)
						}
						config.Layers[i].Styles[j].FeatureInfoExpressions = featureInfoExpr
					}
				}
			}
		}
		return nil
	})

	if err == nil && len(configMap) == 0 {
		err = fmt.Errorf("No config file found")
	}

	return configMap, err
}

// Unmarshal is wrapper around json.Unmarshal that returns user-friendly
// errors when there are syntax errors.
// https://github.com/hashicorp/packer/blob/master/common/json/unmarshal.go
func Unmarshal(data []byte, i interface{}) error {
	err := json.Unmarshal(data, i)
	if err != nil {
		syntaxErr, ok := err.(*json.SyntaxError)
		if !ok {
			return err
		}

		// We have a syntax error. Extract out the line number and friends.
		// https://groups.google.com/forum/#!topic/golang-nuts/fizimmXtVfc
		newline := []byte{'\x0a'}

		// Calculate the start/end position of the line where the error is
		start := bytes.LastIndex(data[:syntaxErr.Offset], newline) + 1
		end := len(data)
		if idx := bytes.Index(data[start:], newline); idx >= 0 {
			end = start + idx
		}

		// Count the line number we're on plus the offset in the line
		line := bytes.Count(data[:start], newline) + 1
		pos := int(syntaxErr.Offset) - start - 1

		err = fmt.Errorf("Error in line %d, char %d: %s\n%s",
			line, pos, syntaxErr, data[start:end])
		return err
	}

	return nil
}

const DefaultRecvMsgSize = 10 * 1024 * 1024

const DefaultWmsPolygonSegments = 2
const DefaultWcsPolygonSegments = 10

const DefaultWmsTimeout = 20
const DefaultWcsTimeout = 30

const DefaultGrpcWmsConcPerNode = 16
const DefaultGrpcWcsConcPerNode = 16

const DefaultWmsPolygonShardConcLimit = 2
const DefaultWcsPolygonShardConcLimit = 2

const DefaultWmsMaxWidth = 512
const DefaultWmsMaxHeight = 512
const DefaultWcsMaxWidth = 50000
const DefaultWcsMaxHeight = 30000
const DefaultWcsMaxTileWidth = 1024
const DefaultWcsMaxTileHeight = 1024

const DefaultLegendWidth = 160
const DefaultLegendHeight = 320

// GetLayerDates loads dates for the ith layer
func (config *Config) GetLayerDates(iLayer int, verbose bool) {
	layer := config.Layers[iLayer]
	step := time.Minute * time.Duration(60*24*layer.StepDays+60*layer.StepHours+layer.StepMinutes)

	if strings.TrimSpace(strings.ToLower(layer.TimeGen)) == "mas" {
		timestamps, token := GenerateDatesMas(layer.StartISODate, layer.EndISODate, config.ServiceConfig.MASAddress, layer.DataSource, layer.RGBExpressions.VarList, step, layer.TimestampToken, verbose)
		if len(timestamps) > 0 && len(token) > 0 {
			config.Layers[iLayer].Dates = timestamps
			config.Layers[iLayer].TimestampToken = token
		} else if len(timestamps) == 0 && len(token) > 0 {
			if verbose {
				log.Printf("Cached %d timestamps", len(config.Layers[iLayer].Dates))
			}
			config.Layers[iLayer].TimestampToken = token
			return
		} else {
			log.Printf("Failed to get MAS timestamps")
			return
		}
	} else {
		startDate := layer.StartISODate
		endDate := layer.EndISODate

		useMasTimestamps := false
		if strings.TrimSpace(strings.ToLower(startDate)) == "mas" {
			useMasTimestamps = true
			startDate = ""
		}

		if strings.TrimSpace(strings.ToLower(endDate)) == "mas" {
			useMasTimestamps = true
			endDate = ""
		} else if strings.TrimSpace(strings.ToLower(endDate)) == "now" {
			endDate = time.Now().UTC().Format(ISOFormat)
		}

		if useMasTimestamps {
			masTimestamps, token := GenerateDatesMas(startDate, endDate, config.ServiceConfig.MASAddress, layer.DataSource, layer.RGBExpressions.VarList, 0, layer.TimestampToken, verbose)
			if len(token) == 0 {
				log.Printf("Failed to get MAS timestamps")
				return
			} else if len(masTimestamps) == 0 && len(token) > 0 {
				if verbose {
					log.Printf("Cached %d timestamps", len(config.Layers[iLayer].Dates))
				}
				config.Layers[iLayer].TimestampToken = token
				return
			}
			config.Layers[iLayer].TimestampToken = token

			if len(startDate) == 0 {
				startDate = masTimestamps[0]
			}

			if len(endDate) == 0 {
				endDate = masTimestamps[len(masTimestamps)-1]
			}
		}

		start, errStart := time.Parse(ISOFormat, startDate)
		if errStart != nil {
			log.Printf("start date parsing error: %v", errStart)
			return
		}

		end, errEnd := time.Parse(ISOFormat, endDate)
		if errEnd != nil {
			log.Printf("end date parsing error: %v", errEnd)
			return
		}

		if useMasTimestamps && step > 0 {
			// We normalise the timestamps by truncating them up to the required precision.
			// The truncation process essentially rounds down the datetime to the
			// nearest precision from the left. This implies that we should not
			// do such a normalisation to the end datetime. Or we might miss
			// out some data points due to lower time resolution on the upper time
			// end point.
			// This behaviour is also consistent with the manual timestep generator
			// which offers open-ended upper time end point.
			if layer.StepDays > 0 {
				start = start.Truncate(24 * 60 * time.Minute)
			} else if layer.StepHours > 0 {
				start = start.Truncate(60 * time.Minute)
			} else if layer.StepMinutes > 0 {
				start = start.Truncate(time.Minute)
			}

			if verbose {
				log.Printf("Normalised MAS start date: %v", start.Format(ISOFormat))
			}
		}

		if start == end {
			config.Layers[iLayer].Dates = append(config.Layers[iLayer].Dates, start.Format(ISOFormat))
		} else {
			config.Layers[iLayer].Dates = GenerateDates(layer.TimeGen, start, end, step)
		}
	}

	nDates := len(config.Layers[iLayer].Dates)
	if nDates > 0 {
		config.Layers[iLayer].EffectiveStartDate = config.Layers[iLayer].Dates[0]
		config.Layers[iLayer].EffectiveEndDate = config.Layers[iLayer].Dates[nDates-1]
	}
}

func ParseBandExpressions(bands []string) (*BandExpressions, error) {
	bandExpr := &BandExpressions{ExprText: bands}
	varFound := make(map[string]bool)
	hasExprAll := false
	for ib, bandRaw := range bands {
		parts := strings.Split(bandRaw, "=")
		if len(parts) == 0 {
			return nil, fmt.Errorf("invalid expression: %v", bandRaw)
		}
		for ip, p := range parts {
			parts[ip] = strings.TrimSpace(p)
			if len(parts[ip]) == 0 {
				return nil, fmt.Errorf("invalid expression: %v", bandRaw)
			}
		}
		var band string
		if len(parts) == 1 {
			band = parts[0]
		} else if len(parts) == 2 {
			band = parts[1]
		} else {
			return nil, fmt.Errorf("invalid expression: %v", bandRaw)
		}

		expr, err := goeval.NewEvaluableExpression(band)
		if err != nil {
			return nil, err
		}
		bandExpr.Expressions = append(bandExpr.Expressions, expr)

		bandExpr.ExprVarRef = append(bandExpr.ExprVarRef, []string{})
		bandVarFound := make(map[string]bool)
		for _, token := range expr.Tokens() {
			if token.Kind == goeval.VARIABLE {
				varName, ok := token.Value.(string)
				if !ok {
					return nil, fmt.Errorf("variable token '%v' failed to cast string for band '%v'", token.Value, band)
				}

				if _, found := varFound[varName]; !found {
					varFound[varName] = true
					bandExpr.VarList = append(bandExpr.VarList, varName)
				}

				if _, found := bandVarFound[varName]; !found {
					bandVarFound[varName] = true
					bandExpr.ExprVarRef[ib] = append(bandExpr.ExprVarRef[ib], varName)
				}

			} else {
				hasExprAll = true
			}
		}

		if len(parts) == 1 {
			bandExpr.ExprNames = append(bandExpr.ExprNames, band)
		} else if len(parts) == 2 {
			bandExpr.ExprNames = append(bandExpr.ExprNames, parts[0])
		}
	}

	if !hasExprAll {
		bandExpr.Expressions = nil
	}
	return bandExpr, nil
}

// LoadConfigFileTemplate parses the config as a Jet
// template and escapes any GSKY here docs (i.e. $gdoc$)
// into valid one-line JSON strings.
func LoadConfigFileTemplate(configFile string) ([]byte, error) {
	path := filepath.Dir(configFile)
	view := jet.NewSet(jet.SafeWriter(func(w io.Writer, b []byte) {
		w.Write(b)
	}), path, "/")
	template, err := view.GetTemplate(configFile)
	if err != nil {
		return nil, err
	}
	var resBuf bytes.Buffer
	vars := make(jet.VarMap)
	if err = template.Execute(&resBuf, vars, nil); err != nil {
		return nil, err
	}

	gdocSym := `$gdoc$`

	// JSON escape rules: https://www.freeformatter.com/json-escape.html
	escapeRules := func(str string) string {
		tokens := []string{"\b", "\f", "\n", "\r", "\t", `"`}
		repl := []string{`\b`, `\f`, `\n`, `\r`, `\t`, `\"`}

		str = strings.Replace(str, `\`, `\\`, -1)
		for it, t := range tokens {
			str = strings.Replace(str, t, repl[it], -1)
		}
		str = `"` + str + `"`
		return str
	}

	rawStr := resBuf.String()
	nHereDocs := strings.Count(rawStr, gdocSym)
	if nHereDocs == 0 {
		return []byte(rawStr), nil
	}

	if nHereDocs%2 != 0 {
		return nil, fmt.Errorf("gdocs are not properly closed")
	}

	strParts := strings.Split(rawStr, gdocSym)

	var escapedStr string
	for ip, part := range strParts {
		if ip%2 == 0 {
			escapedStr += part
		} else {
			escapedStr += escapeRules(part)
		}
	}

	return []byte(escapedStr), nil
}

// LoadConfigFile marshalls the config.json document returning an
// instance of a Config variable containing all the values
func (config *Config) LoadConfigFile(configFile string, verbose bool) error {
	*config = Config{}
	cfg, err := LoadConfigFileTemplate(configFile)
	if verbose {
		log.Printf("%v: %v", configFile, string(cfg))
	}

	if err != nil {
		return fmt.Errorf("Error while reading config file: %s. Error: %v", configFile, err)
	}

	err = Unmarshal(cfg, config)
	if err != nil {
		return fmt.Errorf("Error at JSON parsing config document: %v", err)
	}
	
	if len(config.ServiceConfig.TempDir) > 0 {
		log.Printf("Creating temp directory: %v", config.ServiceConfig.TempDir)
		err := os.MkdirAll(config.ServiceConfig.TempDir, os.ModePerm)
		if err != nil {
			return fmt.Errorf("error creating temp directory: %v", err)
		}
	}

	if config.ServiceConfig.MaxGrpcBufferSize > 0 && config.ServiceConfig.MaxGrpcBufferSize < 10 {
		config.ServiceConfig.MaxGrpcBufferSize = 0
		log.Printf("%v: MaxGrpcBufferSize is set to less than 10MB, reset to unlimited", configFile)
	}

	config.ServiceConfig.MaxGrpcBufferSize = config.ServiceConfig.MaxGrpcBufferSize * 1024 * 1024
	for i, layer := range config.Layers {
		bandExpr, err := ParseBandExpressions(layer.RGBProducts)
		if err != nil {
			return fmt.Errorf("Layer %v RGBExpression parsing error: %v", layer.Name, err)
		}
		config.Layers[i].RGBExpressions = bandExpr

		featureInfoExpr, err := ParseBandExpressions(layer.FeatureInfoBands)
		if err != nil {
			return fmt.Errorf("Layer %v FeatureInfoExpression parsing error: %v", layer.Name, err)
		}
		config.Layers[i].FeatureInfoExpressions = featureInfoExpr

		config.GetLayerDates(i, verbose)

		config.Layers[i].OWSHostname = config.ServiceConfig.OWSHostname

		if config.Layers[i].MaxGrpcRecvMsgSize <= DefaultRecvMsgSize {
			config.Layers[i].MaxGrpcRecvMsgSize = DefaultRecvMsgSize
		}

		if config.Layers[i].WmsPolygonSegments <= DefaultWmsPolygonSegments {
			config.Layers[i].WmsPolygonSegments = DefaultWmsPolygonSegments
		}

		if config.Layers[i].WcsPolygonSegments <= DefaultWcsPolygonSegments {
			config.Layers[i].WcsPolygonSegments = DefaultWcsPolygonSegments
		}

		if config.Layers[i].WmsTimeout <= 0 {
			config.Layers[i].WmsTimeout = DefaultWmsTimeout
		}

		if config.Layers[i].WcsTimeout <= 0 {
			config.Layers[i].WcsTimeout = DefaultWcsTimeout
		}

		if config.Layers[i].GrpcWmsConcPerNode <= 0 {
			config.Layers[i].GrpcWmsConcPerNode = DefaultGrpcWmsConcPerNode
		}

		if config.Layers[i].GrpcWcsConcPerNode <= 0 {
			config.Layers[i].GrpcWcsConcPerNode = DefaultGrpcWcsConcPerNode
		}

		if config.Layers[i].WmsPolygonShardConcLimit <= 0 {
			config.Layers[i].WmsPolygonShardConcLimit = DefaultWmsPolygonShardConcLimit
		}

		if config.Layers[i].WcsPolygonShardConcLimit <= 0 {
			config.Layers[i].WcsPolygonShardConcLimit = DefaultWcsPolygonShardConcLimit
		}

		if layer.Palette != nil && layer.Palette.Colours != nil && len(layer.Palette.Colours) < 3 {
			return fmt.Errorf("The colour palette must contain at least 2 colours.")
		}

		if config.Layers[i].WmsMaxWidth <= 0 {
			config.Layers[i].WmsMaxWidth = DefaultWmsMaxWidth
		}

		if config.Layers[i].WmsMaxHeight <= 0 {
			config.Layers[i].WmsMaxHeight = DefaultWmsMaxHeight
		}

		if config.Layers[i].WcsMaxWidth <= 0 {
			config.Layers[i].WcsMaxWidth = DefaultWcsMaxWidth
		}

		if config.Layers[i].WcsMaxHeight <= 0 {
			config.Layers[i].WcsMaxHeight = DefaultWcsMaxHeight
		}

		if config.Layers[i].WcsMaxTileWidth <= 0 {
			config.Layers[i].WcsMaxTileWidth = DefaultWcsMaxTileWidth
		}

		if config.Layers[i].WcsMaxTileHeight <= 0 {
			config.Layers[i].WcsMaxTileHeight = DefaultWcsMaxTileHeight
		}
	}

	for i, proc := range config.Processes {
		if proc.IdentityTol <= 0 {
			config.Processes[i].IdentityTol = -1.0
		}

		if proc.DpTol <= 0 {
			config.Processes[i].DpTol = -1.0
		}

		if proc.Approx == nil {
			approx := true
			config.Processes[i].Approx = &approx
		}

		for ids, ds := range proc.DataSources {
			bandExpr, err := ParseBandExpressions(ds.RGBProducts)
			if err != nil {
				return fmt.Errorf("Process %v, data source %v, RGBExpression parsing error: %v", proc.Identifier, ids, err)
			}
			config.Processes[i].DataSources[ids].RGBExpressions = bandExpr
		}

	}
	return nil
}

func DumpConfig(configs map[string]*Config) (string, error) {
	configJson, err := json.MarshalIndent(configs, "", "    ")
	if err != nil {
		return "", err
	}

	return string(configJson), nil
}

func WatchConfig(infoLog, errLog *log.Logger, configMap *map[string]*Config, verbose bool) {
	// Catch SIGHUP to automatically reload cache
	sighup := make(chan os.Signal, 1)
//out, err := json.Marshal(sighup)
//if err != nil {
//	panic (err)
//}
//p(string(out))
	signal.Notify(sighup, syscall.SIGHUP)
	go func() {
		for {
			select {
			case <-sighup:
				infoLog.Println("Caught SIGHUP, reloading config...")
				confMap, err := LoadAllConfigFiles(EtcDir, verbose)
				if err != nil {
					errLog.Printf("Error in loading config files: %v\n", err)
					return
				}

				for k := range *configMap {
					delete(*configMap, k)
				}

				for k := range confMap {
					(*configMap)[k] = confMap[k]
				}
			}
		}
	}()
}
