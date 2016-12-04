import os, time
from flask import Flask, Response, render_template, jsonify, session
from geojson import Point, Feature, FeatureCollection
from distReq import randomLocations, readInputLocations, getDurationMatrix, getDistanceMatrix, sendRequest# uncomment this when using in another file
from findPath import gen_time_values, harmMatrices
from mapbox import Directions


app = Flask(__name__)
app.debug = True
app.secret_key = 'correctHorseBatteryStaple'
app.config['SESSION_TYPE'] = 'filesystem'


destinationFeatureArray = []
response = [];
distMatrix = []
durMatrix = []
addreses = []
paths = []
costs = []
output = []

originFeature = []


ACCESS_KEY = os.environ.get('MAPBOX_ACCESSKEY')
service = Directions(ACCESS_KEY)
@app.route('/')
def index():
    return render_template('index.html', ACCESS_KEY=ACCESS_KEY)

@app.route('/origin')
def processOrigin():
    point = Point((-87.9073, 41.9742))
    originFeature = Feature(geometry=point ,properties={'marker-color': '#3ca0d3','marker-size': 'large','marker-symbol': 'airport'})
    feature_collection = FeatureCollection([originFeature])
    session['originFeature'] = originFeature
    return jsonify(result=feature_collection)

@app.route('/dest')
def processDestinations():
    numRiders = 5
    locationFile = "locations.txt" # stores all the lat/longs on different lines
    processedArray = randomLocations(readInputLocations(locationFile), numRiders)
    destinationFeatureArray = []
    for i in range(1, len(processedArray)):
        point = Point((processedArray[i][1],processedArray[i][0]))
        feature =  Feature(geometry=point ,properties= {'marker-color': '#228B22','marker-size': 'medium','marker-symbol': chr(96+i)})
        destinationFeatureArray.append(feature)
    session['destinationFeatureArray']= destinationFeatureArray
    feature_collection = FeatureCollection(destinationFeatureArray)
    response = sendRequest(processedArray,[])
    session['addresses'] = addresses = response["origin_addresses"] # list of length numLocations of the addresses
    session['durMatrix'] = durMatrix = getDurationMatrix(response)
    session['distMatrix'] = distMatrix = getDistanceMatrix(response)
    timeValues = gen_time_values()
    destinations = [(dest[0], dest[1], i) for i, dest in enumerate(processedArray)]
    output, paths, costs = harmMatrices(timeValues, destinations, durMatrix)
    session['paths']=paths
    return jsonify(result=feature_collection)

@app.route('/social')
def socialRoute():
    paths = session.get('paths', None)
    originFeature = session.get('originFeature', None)
    destinationFeatureArray = session.get('destinationFeatureArray', None)
    socialPath = paths[0]
    featureDict = []
    featureDict.append(originFeature);
    for i in range(1,len(socialPath)):
        featureDict.append(destinationFeatureArray[socialPath[i][2]-1])
    response2 = service.directions(featureDict, 'mapbox.driving')
    print response2
    responseJson = response2.geojson()
    # responseJson['style'] = {"style":{ "fill":"red", "stroke-width":"3", "fill-opacity":0.6}}
    # responseJson['features'][0]['properties']['fill']=  '#228B22'
    responseJson['features'][0]['properties']['title']=  'Social Optimal Path'
    responseJson['features'][0]['properties']['stroke']=  '#000080' # lime
    responseJson['features'][0]['properties']['stroke-opacity']=  '0.7'
    responseJson['features'][0]['properties']['stroke-width']=  '6'
    return jsonify(result=responseJson)


@app.route('/opt')
def optRoute():
    paths = session.get('paths', None)
    originFeature = session.get('originFeature', None)
    destinationFeatureArray = session.get('destinationFeatureArray', None)
    optPath = paths[1]
    featureDict = []
    featureDict.append(originFeature);
    for i in range(1,len(optPath)):
        featureDict.append(destinationFeatureArray[optPath[i][2]-1])
    response2 = service.directions(featureDict, 'mapbox.driving')
    # print response2
    responseJson = response2.geojson()
    responseJson['features'][0]['properties']['title']=  'Utility Optimal Path'
    responseJson['features'][0]['properties']['stroke']=  '#00FF00' # lime
    responseJson['features'][0]['properties']['stroke-opacity']=  '0.7'
    responseJson['features'][0]['properties']['stroke-width']=  '4'
    return jsonify(result=responseJson)


@app.route('/process')
def long_running_process():
      def generate():
        # time.sleep(10)
        yield 'data: Chicago O\'Hare Airport marker placed \n\n'
      return Response(generate(), mimetype='text/event-stream')

@app.route('/process2')
def long_running_process2():
      def generate2():
        yield 'data: Destination markers placed \n\n'
      return Response(generate2(), mimetype='text/event-stream')

@app.route('/process3')
def long_running_process3():
      def generate3():
        yield 'data: Social Path \n\n'
      return Response(generate3(), mimetype='text/event-stream')

@app.route('/process4')
def long_running_process4():
      def generate4():
        yield 'data: Optimal Path \n\n'
      return Response(generate4(), mimetype='text/event-stream')



if __name__ == "__main__":
    app.run()