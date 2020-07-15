(function(f){if(typeof exports==="object"&&typeof module!=="undefined"){module.exports=f()}else if(typeof define==="function"&&define.amd){define([],f)}else{var g;if(typeof window!=="undefined"){g=window}else if(typeof global!=="undefined"){g=global}else if(typeof self!=="undefined"){g=self}else{g=this}g.geojsonvt = f()}})(function(){var define,module,exports;return (function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
'use strict';

module.exports = clip;

var createFeature = require('./feature');

/* clip features between two axis-parallel lines:
 *     |        |
 *  ___|___     |     /
 * /   |   \____|____/
 *     |        |
 */

function clip(features, scale, k1, k2, axis, intersect, minAll, maxAll) {

    k1 /= scale;
    k2 /= scale;

    if (minAll >= k1 && maxAll <= k2) return features; // trivial accept
    else if (minAll > k2 || maxAll < k1) return null; // trivial reject

    var clipped = [];

    for (var i = 0; i < features.length; i++) {

        var feature = features[i],
            geometry = feature.geometry,
            type = feature.type,
            min, max;

        min = feature.min[axis];
        max = feature.max[axis];

        if (min >= k1 && max <= k2) { // trivial accept
            clipped.push(feature);
            continue;
        } else if (min > k2 || max < k1) continue; // trivial reject

        var slices = type === 1 ?
                clipPoints(geometry, k1, k2, axis) :
                clipGeometry(geometry, k1, k2, axis, intersect, type === 3);

        if (slices.length) {
            // if a feature got clipped, it will likely get clipped on the next zoom level as well,
            // so there's no need to recalculate bboxes
            clipped.push(createFeature(feature.tags, type, slices, feature.id));
        }
    }

    return clipped.length ? clipped : null;
}

function clipPoints(geometry, k1, k2, axis) {
    var slice = [];

    for (var i = 0; i < geometry.length; i++) {
        var a = geometry[i],
            ak = a[axis];

        if (ak >= k1 && ak <= k2) slice.push(a);
    }
    return slice;
}

function clipGeometry(geometry, k1, k2, axis, intersect, closed) {

    var slices = [];

    for (var i = 0; i < geometry.length; i++) {

        var ak = 0,
            bk = 0,
            b = null,
            points = geometry[i],
            area = points.area,
            dist = points.dist,
            outer = points.outer,
            len = points.length,
            a, j, last;

        var slice = [];

        for (j = 0; j < len - 1; j++) {
            a = b || points[j];
            b = points[j + 1];
            ak = bk || a[axis];
            bk = b[axis];

            if (ak < k1) {

                if ((bk > k2)) { // ---|-----|-->
                    slice.push(intersect(a, b, k1), intersect(a, b, k2));
                    if (!closed) slice = newSlice(slices, slice, area, dist, outer);

                } else if (bk >= k1) slice.push(intersect(a, b, k1)); // ---|-->  |

            } else if (ak > k2) {

                if ((bk < k1)) { // <--|-----|---
                    slice.push(intersect(a, b, k2), intersect(a, b, k1));
                    if (!closed) slice = newSlice(slices, slice, area, dist, outer);

                } else if (bk <= k2) slice.push(intersect(a, b, k2)); // |  <--|---

            } else {

                slice.push(a);

                if (bk < k1) { // <--|---  |
                    slice.push(intersect(a, b, k1));
                    if (!closed) slice = newSlice(slices, slice, area, dist, outer);

                } else if (bk > k2) { // |  ---|-->
                    slice.push(intersect(a, b, k2));
                    if (!closed) slice = newSlice(slices, slice, area, dist, outer);
                }
                // | --> |
            }
        }

        // add the last point
        a = points[len - 1];
        ak = a[axis];
        if (ak >= k1 && ak <= k2) slice.push(a);

        // close the polygon if its endpoints are not the same after clipping

        last = slice[slice.length - 1];
        if (closed && last && (slice[0][0] !== last[0] || slice[0][1] !== last[1])) slice.push(slice[0]);

        // add the final slice
        newSlice(slices, slice, area, dist, outer);
    }

    return slices;
}

function newSlice(slices, slice, area, dist, outer) {
    if (slice.length) {
        // we don't recalculate the area/length of the unclipped geometry because the case where it goes
        // below the visibility threshold as a result of clipping is rare, so we avoid doing unnecessary work
        slice.area = area;
        slice.dist = dist;
        if (outer !== undefined) slice.outer = outer;

        slices.push(slice);
    }
    return [];
}

},{"./feature":3}],2:[function(require,module,exports){
'use strict';

module.exports = convert;

var simplify = require('./simplify');
var createFeature = require('./feature');

// converts GeoJSON feature into an intermediate projected JSON vector format with simplification data

function convert(data, tolerance) {
    var features = [];

    if (data.type === 'FeatureCollection') {
        for (var i = 0; i < data.features.length; i++) {
            convertFeature(features, data.features[i], tolerance);
        }
    } else if (data.type === 'Feature') {
        convertFeature(features, data, tolerance);

    } else {
        // single geometry or a geometry collection
        convertFeature(features, {geometry: data}, tolerance);
    }
    return features;
}

function convertFeature(features, feature, tolerance) {
    if (feature.geometry === null) {
        // ignore features with null geometry
        return;
    }

    var geom = feature.geometry,
        type = geom.type,
        coords = geom.coordinates,
        tags = feature.properties,
        id = feature.id,
        i, j, rings, projectedRing;

    if (type === 'Point') {
        features.push(createFeature(tags, 1, [projectPoint(coords)], id));

    } else if (type === 'MultiPoint') {
        features.push(createFeature(tags, 1, project(coords), id));

    } else if (type === 'LineString') {
        features.push(createFeature(tags, 2, [project(coords, tolerance)], id));

    } else if (type === 'MultiLineString' || type === 'Polygon') {
        rings = [];
        for (i = 0; i < coords.length; i++) {
            projectedRing = project(coords[i], tolerance);
            if (type === 'Polygon') projectedRing.outer = (i === 0);
            rings.push(projectedRing);
        }
        features.push(createFeature(tags, type === 'Polygon' ? 3 : 2, rings, id));

    } else if (type === 'MultiPolygon') {
        rings = [];
        for (i = 0; i < coords.length; i++) {
            for (j = 0; j < coords[i].length; j++) {
                projectedRing = project(coords[i][j], tolerance);
                projectedRing.outer = (j === 0);
                rings.push(projectedRing);
            }
        }
        features.push(createFeature(tags, 3, rings, id));

    } else if (type === 'GeometryCollection') {
        for (i = 0; i < geom.geometries.length; i++) {
            convertFeature(features, {
                geometry: geom.geometries[i],
                properties: tags
            }, tolerance);
        }

    } else {
        throw new Error('Input data is not a valid GeoJSON object.');
    }
}

function project(lonlats, tolerance) {
    var projected = [];
    for (var i = 0; i < lonlats.length; i++) {
        projected.push(projectPoint(lonlats[i]));
    }
    if (tolerance) {
        simplify(projected, tolerance);
        calcSize(projected);
    }
    return projected;
}

function projectPoint(p) {
    var sin = Math.sin(p[1] * Math.PI / 180),
        x = (p[0] / 360 + 0.5),
        y = (0.5 - 0.25 * Math.log((1 + sin) / (1 - sin)) / Math.PI);

    y = y < 0 ? 0 :
        y > 1 ? 1 : y;

    return [x, y, 0];
}

// calculate area and length of the poly
function calcSize(points) {
    var area = 0,
        dist = 0;

    for (var i = 0, a, b; i < points.length - 1; i++) {
        a = b || points[i];
        b = points[i + 1];

        area += a[0] * b[1] - b[0] * a[1];

        // use Manhattan distance instead of Euclidian one to avoid expensive square root computation
        dist += Math.abs(b[0] - a[0]) + Math.abs(b[1] - a[1]);
    }
    points.area = Math.abs(area / 2);
    points.dist = dist;
}

},{"./feature":3,"./simplify":5}],3:[function(require,module,exports){
'use strict';

module.exports = createFeature;

function createFeature(tags, type, geom, id) {
    var feature = {
        id: id || null,
        type: type,
        geometry: geom,
        tags: tags || null,
        min: [Infinity, Infinity], // initial bbox values
        max: [-Infinity, -Infinity]
    };
    calcBBox(feature);
    return feature;
}

// calculate the feature bounding box for faster clipping later
function calcBBox(feature) {
    var geometry = feature.geometry,
        min = feature.min,
        max = feature.max;

    if (feature.type === 1) {
        calcRingBBox(min, max, geometry);
    } else {
        for (var i = 0; i < geometry.length; i++) {
            calcRingBBox(min, max, geometry[i]);
        }
    }

    return feature;
}

function calcRingBBox(min, max, points) {
    for (var i = 0, p; i < points.length; i++) {
        p = points[i];
        min[0] = Math.min(p[0], min[0]);
        max[0] = Math.max(p[0], max[0]);
        min[1] = Math.min(p[1], min[1]);
        max[1] = Math.max(p[1], max[1]);
    }
}

},{}],4:[function(require,module,exports){
'use strict';

module.exports = geojsonvt;

var convert = require('./convert'),     // GeoJSON conversion and preprocessing
    transform = require('./transform'), // coordinate transformation
    clip = require('./clip'),           // stripe clipping algorithm
    wrap = require('./wrap'),           // date line processing
    createTile = require('./tile');     // final simplified tile generation


function geojsonvt(data, options) {
    return new GeoJSONVT(data, options);
}

function GeoJSONVT(data, options) {
    options = this.options = extend(Object.create(this.options), options);

    var debug = options.debug;

    var z2 = 1 << options.maxZoom, // 2^z
        features = convert(data, options.tolerance / (z2 * options.extent));

    this.tiles = {};
    this.tileCoords = [];

    if (debug) {
        this.stats = {};
        this.total = 0;
    }

    features = wrap(features, options.buffer / options.extent, intersectX);

    // start slicing from the top tile down
    if (features.length) this.splitTile(features, 0, 0, 0);
}

GeoJSONVT.prototype.options = {
    maxZoom: 14,            // max zoom to preserve detail on
    indexMaxZoom: 5,        // max zoom in the tile index
    indexMaxPoints: 100000, // max number of points per tile in the tile index
    solidChildren: false,   // whether to tile solid square tiles further
    tolerance: 3,           // simplification tolerance (higher means simpler)
    extent: 4096,           // tile extent
    buffer: 64,             // tile buffer on each side
    debug: 0                // logging level (0, 1 or 2)
};

GeoJSONVT.prototype.splitTile = function (features, z, x, y, cz, cx, cy) {

    var stack = [features, z, x, y],
        options = this.options,
        debug = options.debug,
        solid = null;

    // avoid recursion by using a processing queue
    while (stack.length) {
        y = stack.pop();
        x = stack.pop();
        z = stack.pop();
        features = stack.pop();

        var z2 = 1 << z,
            id = toID(z, x, y),
            tile = this.tiles[id],
            tileTolerance = z === options.maxZoom ? 0 : options.tolerance / (z2 * options.extent);

        if (!tile) {

            tile = this.tiles[id] = createTile(features, z2, x, y, tileTolerance, z === options.maxZoom);
            this.tileCoords.push({z: z, x: x, y: y});

            if (debug) {
                var key = 'z' + z;
                this.stats[key] = (this.stats[key] || 0) + 1;
                this.total++;
            }
        }

        // save reference to original geometry in tile so that we can drill down later if we stop now
        tile.source = features;

        // if it's the first-pass tiling
        if (!cz) {
            // stop tiling if we reached max zoom, or if the tile is too simple
            if (z === options.indexMaxZoom || tile.numPoints <= options.indexMaxPoints) continue;

        // if a drilldown to a specific tile
        } else {
            // stop tiling if we reached base zoom or our target tile zoom
            if (z === options.maxZoom || z === cz) continue;

            // stop tiling if it's not an ancestor of the target tile
            var m = 1 << (cz - z);
            if (x !== Math.floor(cx / m) || y !== Math.floor(cy / m)) continue;
        }

        // stop tiling if the tile is solid clipped square
        if (!options.solidChildren && isClippedSquare(tile, options.extent, options.buffer)) {
            if (cz) solid = z; // and remember the zoom if we're drilling down
            continue;
        }

        // if we slice further down, no need to keep source geometry
        tile.source = null;

        // values we'll use for clipping
        var k1 = 0.5 * options.buffer / options.extent,
            k2 = 0.5 - k1,
            k3 = 0.5 + k1,
            k4 = 1 + k1,
            tl, bl, tr, br, left, right;

        tl = bl = tr = br = null;

        left  = clip(features, z2, x - k1, x + k3, 0, intersectX, tile.min[0], tile.max[0]);
        right = clip(features, z2, x + k2, x + k4, 0, intersectX, tile.min[0], tile.max[0]);

        if (left) {
            tl = clip(left, z2, y - k1, y + k3, 1, intersectY, tile.min[1], tile.max[1]);
            bl = clip(left, z2, y + k2, y + k4, 1, intersectY, tile.min[1], tile.max[1]);
        }

        if (right) {
            tr = clip(right, z2, y - k1, y + k3, 1, intersectY, tile.min[1], tile.max[1]);
            br = clip(right, z2, y + k2, y + k4, 1, intersectY, tile.min[1], tile.max[1]);
        }

        if (features.length) {
            stack.push(tl || [], z + 1, x * 2,     y * 2);
            stack.push(bl || [], z + 1, x * 2,     y * 2 + 1);
            stack.push(tr || [], z + 1, x * 2 + 1, y * 2);
            stack.push(br || [], z + 1, x * 2 + 1, y * 2 + 1);
        }
    }

    return solid;
};

GeoJSONVT.prototype.getTile = function (z, x, y) {
    var options = this.options,
        extent = options.extent,
        debug = options.debug;

    var z2 = 1 << z;
    x = ((x % z2) + z2) % z2; // wrap tile x coordinate

    var id = toID(z, x, y);
    if (this.tiles[id]) return transform.tile(this.tiles[id], extent);

    var z0 = z,
        x0 = x,
        y0 = y,
        parent;

    while (!parent && z0 > 0) {
        z0--;
        x0 = Math.floor(x0 / 2);
        y0 = Math.floor(y0 / 2);
        parent = this.tiles[toID(z0, x0, y0)];
    }

    if (!parent || !parent.source) return null;

    // it parent tile is a solid clipped square, return it instead since it's identical
    if (isClippedSquare(parent, extent, options.buffer)) return transform.tile(parent, extent);

    var solid = this.splitTile(parent.source, z0, x0, y0, z, x, y);

    // one of the parent tiles was a solid clipped square
    if (solid !== null) {
        var m = 1 << (z - solid);
        id = toID(solid, Math.floor(x / m), Math.floor(y / m));
    }

    return this.tiles[id] ? transform.tile(this.tiles[id], extent) : null;
};

function toID(z, x, y) {
    return (((1 << z) * y + x) * 32) + z;
}

function intersectX(a, b, x) {
    return [x, (x - a[0]) * (b[1] - a[1]) / (b[0] - a[0]) + a[1], 1];
}
function intersectY(a, b, y) {
    return [(y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) + a[0], y, 1];
}

function extend(dest, src) {
    for (var i in src) dest[i] = src[i];
    return dest;
}

// checks whether a tile is a whole-area fill after clipping; if it is, there's no sense slicing it further
function isClippedSquare(tile, extent, buffer) {

    var features = tile.source;
    if (features.length !== 1) return false;

    var feature = features[0];
    if (feature.type !== 3 || feature.geometry.length > 1) return false;

    var len = feature.geometry[0].length;
    if (len !== 5) return false;

    for (var i = 0; i < len; i++) {
        var p = transform.point(feature.geometry[0][i], extent, tile.z2, tile.x, tile.y);
        if ((p[0] !== -buffer && p[0] !== extent + buffer) ||
            (p[1] !== -buffer && p[1] !== extent + buffer)) return false;
    }

    return true;
}

},{"./clip":1,"./convert":2,"./tile":6,"./transform":7,"./wrap":8}],5:[function(require,module,exports){
'use strict';

module.exports = simplify;

// calculate simplification data using optimized Douglas-Peucker algorithm

function simplify(points, tolerance) {

    var sqTolerance = tolerance * tolerance,
        len = points.length,
        first = 0,
        last = len - 1,
        stack = [],
        i, maxSqDist, sqDist, index;

    // always retain the endpoints (1 is the max value)
    points[first][2] = 1;
    points[last][2] = 1;

    // avoid recursion by using a stack
    while (last) {

        maxSqDist = 0;

        for (i = first + 1; i < last; i++) {
            sqDist = getSqSegDist(points[i], points[first], points[last]);

            if (sqDist > maxSqDist) {
                index = i;
                maxSqDist = sqDist;
            }
        }

        if (maxSqDist > sqTolerance) {
            points[index][2] = maxSqDist; // save the point importance in squared pixels as a z coordinate
            stack.push(first);
            stack.push(index);
            first = index;

        } else {
            last = stack.pop();
            first = stack.pop();
        }
    }
}

// square distance from a point to a segment
function getSqSegDist(p, a, b) {

    var x = a[0], y = a[1],
        bx = b[0], by = b[1],
        px = p[0], py = p[1],
        dx = bx - x,
        dy = by - y;

    if (dx !== 0 || dy !== 0) {

        var t = ((px - x) * dx + (py - y) * dy) / (dx * dx + dy * dy);

        if (t > 1) {
            x = bx;
            y = by;

        } else if (t > 0) {
            x += dx * t;
            y += dy * t;
        }
    }

    dx = px - x;
    dy = py - y;

    return dx * dx + dy * dy;
}

},{}],6:[function(require,module,exports){
'use strict';

module.exports = createTile;

function createTile(features, z2, tx, ty, tolerance, noSimplify) {
    var tile = {
        features: [],
        numPoints: 0,
        numSimplified: 0,
        numFeatures: 0,
        source: null,
        x: tx,
        y: ty,
        z2: z2,
        transformed: false,
        min: [2, 1],
        max: [-1, 0]
    };
    for (var i = 0; i < features.length; i++) {
        tile.numFeatures++;
        addFeature(tile, features[i], tolerance, noSimplify);

        var min = features[i].min,
            max = features[i].max;

        if (min[0] < tile.min[0]) tile.min[0] = min[0];
        if (min[1] < tile.min[1]) tile.min[1] = min[1];
        if (max[0] > tile.max[0]) tile.max[0] = max[0];
        if (max[1] > tile.max[1]) tile.max[1] = max[1];
    }
    return tile;
}

function addFeature(tile, feature, tolerance, noSimplify) {

    var geom = feature.geometry,
        type = feature.type,
        simplified = [],
        sqTolerance = tolerance * tolerance,
        i, j, ring, p;

    if (type === 1) {
        for (i = 0; i < geom.length; i++) {
            simplified.push(geom[i]);
            tile.numPoints++;
            tile.numSimplified++;
        }

    } else {

        // simplify and transform projected coordinates for tile geometry
        for (i = 0; i < geom.length; i++) {
            ring = geom[i];

            // filter out tiny polylines & polygons
            if (!noSimplify && ((type === 2 && ring.dist < tolerance) ||
                                (type === 3 && ring.area < sqTolerance))) {
                tile.numPoints += ring.length;
                continue;
            }

            var simplifiedRing = [];

            for (j = 0; j < ring.length; j++) {
                p = ring[j];
                // keep points with importance > tolerance
                if (noSimplify || p[2] > sqTolerance) {
                    simplifiedRing.push(p);
                    tile.numSimplified++;
                }
                tile.numPoints++;
            }

            if (type === 3) rewind(simplifiedRing, ring.outer);

            simplified.push(simplifiedRing);
        }
    }

    if (simplified.length) {
        var tileFeature = {
            geometry: simplified,
            type: type,
            tags: feature.tags || null
        };
        if (feature.id !== null) {
            tileFeature.id = feature.id;
        }
        tile.features.push(tileFeature);
    }
}

function rewind(ring, clockwise) {
    var area = signedArea(ring);
    if (area < 0 === clockwise) ring.reverse();
}

function signedArea(ring) {
    var sum = 0;
    for (var i = 0, len = ring.length, j = len - 1, p1, p2; i < len; j = i++) {
        p1 = ring[i];
        p2 = ring[j];
        sum += (p2[0] - p1[0]) * (p1[1] + p2[1]);
    }
    return sum;
}

},{}],7:[function(require,module,exports){
'use strict';

exports.tile = transformTile;
exports.point = transformPoint;

// Transforms the coordinates of each feature in the given tile from
// mercator-projected space into (extent x extent) tile space.
function transformTile(tile, extent) {
    if (tile.transformed) return tile;

    var z2 = tile.z2,
        tx = tile.x,
        ty = tile.y,
        i, j, k;

    for (i = 0; i < tile.features.length; i++) {
        var feature = tile.features[i],
            geom = feature.geometry,
            type = feature.type;

        if (type === 1) {
            for (j = 0; j < geom.length; j++) geom[j] = transformPoint(geom[j], extent, z2, tx, ty);

        } else {
            for (j = 0; j < geom.length; j++) {
                var ring = geom[j];
                for (k = 0; k < ring.length; k++) ring[k] = transformPoint(ring[k], extent, z2, tx, ty);
            }
        }
    }

    tile.transformed = true;

    return tile;
}

function transformPoint(p, extent, z2, tx, ty) {
    var x = Math.round(extent * (p[0] * z2 - tx)),
        y = Math.round(extent * (p[1] * z2 - ty));
    return [x, y];
}

},{}],8:[function(require,module,exports){
'use strict';

var clip = require('./clip');
var createFeature = require('./feature');

module.exports = wrap;

function wrap(features, buffer, intersectX) {
    var merged = features,
        left  = clip(features, 1, -1 - buffer, buffer,     0, intersectX, -1, 2), // left world copy
        right = clip(features, 1,  1 - buffer, 2 + buffer, 0, intersectX, -1, 2); // right world copy

    if (left || right) {
        merged = clip(features, 1, -buffer, 1 + buffer, 0, intersectX, -1, 2) || []; // center world copy

        if (left) merged = shiftFeatureCoords(left, 1).concat(merged); // merge left into center
        if (right) merged = merged.concat(shiftFeatureCoords(right, -1)); // merge right into center
    }

    return merged;
}

function shiftFeatureCoords(features, offset) {
    var newFeatures = [];

    for (var i = 0; i < features.length; i++) {
        var feature = features[i],
            type = feature.type;

        var newGeometry;

        if (type === 1) {
            newGeometry = shiftCoords(feature.geometry, offset);
        } else {
            newGeometry = [];
            for (var j = 0; j < feature.geometry.length; j++) {
                newGeometry.push(shiftCoords(feature.geometry[j], offset));
            }
        }

        newFeatures.push(createFeature(feature.tags, type, newGeometry, feature.id));
    }

    return newFeatures;
}

function shiftCoords(points, offset) {
    var newPoints = [];
    newPoints.area = points.area;
    newPoints.dist = points.dist;

    for (var i = 0; i < points.length; i++) {
        newPoints.push([points[i][0] + offset, points[i][1], points[i][2]]);
    }
    return newPoints;
}

},{"./clip":1,"./feature":3}]},{},[4])(4)
});
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm5vZGVfbW9kdWxlcy9icm93c2VyaWZ5L25vZGVfbW9kdWxlcy9icm93c2VyLXBhY2svX3ByZWx1ZGUuanMiLCJzcmMvY2xpcC5qcyIsInNyYy9jb252ZXJ0LmpzIiwic3JjL2ZlYXR1cmUuanMiLCJzcmMvaW5kZXguanMiLCJzcmMvc2ltcGxpZnkuanMiLCJzcmMvdGlsZS5qcyIsInNyYy90cmFuc2Zvcm0uanMiLCJzcmMvd3JhcC5qcyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQTtBQ0FBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUNySkE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUN6SEE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUMzQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQ2xQQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDMUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDMUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUN6Q0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBIiwiZmlsZSI6ImdlbmVyYXRlZC5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzQ29udGVudCI6WyIoZnVuY3Rpb24gZSh0LG4scil7ZnVuY3Rpb24gcyhvLHUpe2lmKCFuW29dKXtpZighdFtvXSl7dmFyIGE9dHlwZW9mIHJlcXVpcmU9PVwiZnVuY3Rpb25cIiYmcmVxdWlyZTtpZighdSYmYSlyZXR1cm4gYShvLCEwKTtpZihpKXJldHVybiBpKG8sITApO3ZhciBmPW5ldyBFcnJvcihcIkNhbm5vdCBmaW5kIG1vZHVsZSAnXCIrbytcIidcIik7dGhyb3cgZi5jb2RlPVwiTU9EVUxFX05PVF9GT1VORFwiLGZ9dmFyIGw9bltvXT17ZXhwb3J0czp7fX07dFtvXVswXS5jYWxsKGwuZXhwb3J0cyxmdW5jdGlvbihlKXt2YXIgbj10W29dWzFdW2VdO3JldHVybiBzKG4/bjplKX0sbCxsLmV4cG9ydHMsZSx0LG4scil9cmV0dXJuIG5bb10uZXhwb3J0c312YXIgaT10eXBlb2YgcmVxdWlyZT09XCJmdW5jdGlvblwiJiZyZXF1aXJlO2Zvcih2YXIgbz0wO288ci5sZW5ndGg7bysrKXMocltvXSk7cmV0dXJuIHN9KSIsIid1c2Ugc3RyaWN0JztcclxuXHJcbm1vZHVsZS5leHBvcnRzID0gY2xpcDtcclxuXHJcbnZhciBjcmVhdGVGZWF0dXJlID0gcmVxdWlyZSgnLi9mZWF0dXJlJyk7XHJcblxyXG4vKiBjbGlwIGZlYXR1cmVzIGJldHdlZW4gdHdvIGF4aXMtcGFyYWxsZWwgbGluZXM6XHJcbiAqICAgICB8ICAgICAgICB8XHJcbiAqICBfX198X19fICAgICB8ICAgICAvXHJcbiAqIC8gICB8ICAgXFxfX19ffF9fX18vXHJcbiAqICAgICB8ICAgICAgICB8XHJcbiAqL1xyXG5cclxuZnVuY3Rpb24gY2xpcChmZWF0dXJlcywgc2NhbGUsIGsxLCBrMiwgYXhpcywgaW50ZXJzZWN0LCBtaW5BbGwsIG1heEFsbCkge1xyXG5cclxuICAgIGsxIC89IHNjYWxlO1xyXG4gICAgazIgLz0gc2NhbGU7XHJcblxyXG4gICAgaWYgKG1pbkFsbCA+PSBrMSAmJiBtYXhBbGwgPD0gazIpIHJldHVybiBmZWF0dXJlczsgLy8gdHJpdmlhbCBhY2NlcHRcclxuICAgIGVsc2UgaWYgKG1pbkFsbCA+IGsyIHx8IG1heEFsbCA8IGsxKSByZXR1cm4gbnVsbDsgLy8gdHJpdmlhbCByZWplY3RcclxuXHJcbiAgICB2YXIgY2xpcHBlZCA9IFtdO1xyXG5cclxuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgZmVhdHVyZXMubGVuZ3RoOyBpKyspIHtcclxuXHJcbiAgICAgICAgdmFyIGZlYXR1cmUgPSBmZWF0dXJlc1tpXSxcclxuICAgICAgICAgICAgZ2VvbWV0cnkgPSBmZWF0dXJlLmdlb21ldHJ5LFxyXG4gICAgICAgICAgICB0eXBlID0gZmVhdHVyZS50eXBlLFxyXG4gICAgICAgICAgICBtaW4sIG1heDtcclxuXHJcbiAgICAgICAgbWluID0gZmVhdHVyZS5taW5bYXhpc107XHJcbiAgICAgICAgbWF4ID0gZmVhdHVyZS5tYXhbYXhpc107XHJcblxyXG4gICAgICAgIGlmIChtaW4gPj0gazEgJiYgbWF4IDw9IGsyKSB7IC8vIHRyaXZpYWwgYWNjZXB0XHJcbiAgICAgICAgICAgIGNsaXBwZWQucHVzaChmZWF0dXJlKTtcclxuICAgICAgICAgICAgY29udGludWU7XHJcbiAgICAgICAgfSBlbHNlIGlmIChtaW4gPiBrMiB8fCBtYXggPCBrMSkgY29udGludWU7IC8vIHRyaXZpYWwgcmVqZWN0XHJcblxyXG4gICAgICAgIHZhciBzbGljZXMgPSB0eXBlID09PSAxID9cclxuICAgICAgICAgICAgICAgIGNsaXBQb2ludHMoZ2VvbWV0cnksIGsxLCBrMiwgYXhpcykgOlxyXG4gICAgICAgICAgICAgICAgY2xpcEdlb21ldHJ5KGdlb21ldHJ5LCBrMSwgazIsIGF4aXMsIGludGVyc2VjdCwgdHlwZSA9PT0gMyk7XHJcblxyXG4gICAgICAgIGlmIChzbGljZXMubGVuZ3RoKSB7XHJcbiAgICAgICAgICAgIC8vIGlmIGEgZmVhdHVyZSBnb3QgY2xpcHBlZCwgaXQgd2lsbCBsaWtlbHkgZ2V0IGNsaXBwZWQgb24gdGhlIG5leHQgem9vbSBsZXZlbCBhcyB3ZWxsLFxyXG4gICAgICAgICAgICAvLyBzbyB0aGVyZSdzIG5vIG5lZWQgdG8gcmVjYWxjdWxhdGUgYmJveGVzXHJcbiAgICAgICAgICAgIGNsaXBwZWQucHVzaChjcmVhdGVGZWF0dXJlKGZlYXR1cmUudGFncywgdHlwZSwgc2xpY2VzLCBmZWF0dXJlLmlkKSk7XHJcbiAgICAgICAgfVxyXG4gICAgfVxyXG5cclxuICAgIHJldHVybiBjbGlwcGVkLmxlbmd0aCA/IGNsaXBwZWQgOiBudWxsO1xyXG59XHJcblxyXG5mdW5jdGlvbiBjbGlwUG9pbnRzKGdlb21ldHJ5LCBrMSwgazIsIGF4aXMpIHtcclxuICAgIHZhciBzbGljZSA9IFtdO1xyXG5cclxuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgZ2VvbWV0cnkubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICB2YXIgYSA9IGdlb21ldHJ5W2ldLFxyXG4gICAgICAgICAgICBhayA9IGFbYXhpc107XHJcblxyXG4gICAgICAgIGlmIChhayA+PSBrMSAmJiBhayA8PSBrMikgc2xpY2UucHVzaChhKTtcclxuICAgIH1cclxuICAgIHJldHVybiBzbGljZTtcclxufVxyXG5cclxuZnVuY3Rpb24gY2xpcEdlb21ldHJ5KGdlb21ldHJ5LCBrMSwgazIsIGF4aXMsIGludGVyc2VjdCwgY2xvc2VkKSB7XHJcblxyXG4gICAgdmFyIHNsaWNlcyA9IFtdO1xyXG5cclxuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgZ2VvbWV0cnkubGVuZ3RoOyBpKyspIHtcclxuXHJcbiAgICAgICAgdmFyIGFrID0gMCxcclxuICAgICAgICAgICAgYmsgPSAwLFxyXG4gICAgICAgICAgICBiID0gbnVsbCxcclxuICAgICAgICAgICAgcG9pbnRzID0gZ2VvbWV0cnlbaV0sXHJcbiAgICAgICAgICAgIGFyZWEgPSBwb2ludHMuYXJlYSxcclxuICAgICAgICAgICAgZGlzdCA9IHBvaW50cy5kaXN0LFxyXG4gICAgICAgICAgICBvdXRlciA9IHBvaW50cy5vdXRlcixcclxuICAgICAgICAgICAgbGVuID0gcG9pbnRzLmxlbmd0aCxcclxuICAgICAgICAgICAgYSwgaiwgbGFzdDtcclxuXHJcbiAgICAgICAgdmFyIHNsaWNlID0gW107XHJcblxyXG4gICAgICAgIGZvciAoaiA9IDA7IGogPCBsZW4gLSAxOyBqKyspIHtcclxuICAgICAgICAgICAgYSA9IGIgfHwgcG9pbnRzW2pdO1xyXG4gICAgICAgICAgICBiID0gcG9pbnRzW2ogKyAxXTtcclxuICAgICAgICAgICAgYWsgPSBiayB8fCBhW2F4aXNdO1xyXG4gICAgICAgICAgICBiayA9IGJbYXhpc107XHJcblxyXG4gICAgICAgICAgICBpZiAoYWsgPCBrMSkge1xyXG5cclxuICAgICAgICAgICAgICAgIGlmICgoYmsgPiBrMikpIHsgLy8gLS0tfC0tLS0tfC0tPlxyXG4gICAgICAgICAgICAgICAgICAgIHNsaWNlLnB1c2goaW50ZXJzZWN0KGEsIGIsIGsxKSwgaW50ZXJzZWN0KGEsIGIsIGsyKSk7XHJcbiAgICAgICAgICAgICAgICAgICAgaWYgKCFjbG9zZWQpIHNsaWNlID0gbmV3U2xpY2Uoc2xpY2VzLCBzbGljZSwgYXJlYSwgZGlzdCwgb3V0ZXIpO1xyXG5cclxuICAgICAgICAgICAgICAgIH0gZWxzZSBpZiAoYmsgPj0gazEpIHNsaWNlLnB1c2goaW50ZXJzZWN0KGEsIGIsIGsxKSk7IC8vIC0tLXwtLT4gIHxcclxuXHJcbiAgICAgICAgICAgIH0gZWxzZSBpZiAoYWsgPiBrMikge1xyXG5cclxuICAgICAgICAgICAgICAgIGlmICgoYmsgPCBrMSkpIHsgLy8gPC0tfC0tLS0tfC0tLVxyXG4gICAgICAgICAgICAgICAgICAgIHNsaWNlLnB1c2goaW50ZXJzZWN0KGEsIGIsIGsyKSwgaW50ZXJzZWN0KGEsIGIsIGsxKSk7XHJcbiAgICAgICAgICAgICAgICAgICAgaWYgKCFjbG9zZWQpIHNsaWNlID0gbmV3U2xpY2Uoc2xpY2VzLCBzbGljZSwgYXJlYSwgZGlzdCwgb3V0ZXIpO1xyXG5cclxuICAgICAgICAgICAgICAgIH0gZWxzZSBpZiAoYmsgPD0gazIpIHNsaWNlLnB1c2goaW50ZXJzZWN0KGEsIGIsIGsyKSk7IC8vIHwgIDwtLXwtLS1cclxuXHJcbiAgICAgICAgICAgIH0gZWxzZSB7XHJcblxyXG4gICAgICAgICAgICAgICAgc2xpY2UucHVzaChhKTtcclxuXHJcbiAgICAgICAgICAgICAgICBpZiAoYmsgPCBrMSkgeyAvLyA8LS18LS0tICB8XHJcbiAgICAgICAgICAgICAgICAgICAgc2xpY2UucHVzaChpbnRlcnNlY3QoYSwgYiwgazEpKTtcclxuICAgICAgICAgICAgICAgICAgICBpZiAoIWNsb3NlZCkgc2xpY2UgPSBuZXdTbGljZShzbGljZXMsIHNsaWNlLCBhcmVhLCBkaXN0LCBvdXRlcik7XHJcblxyXG4gICAgICAgICAgICAgICAgfSBlbHNlIGlmIChiayA+IGsyKSB7IC8vIHwgIC0tLXwtLT5cclxuICAgICAgICAgICAgICAgICAgICBzbGljZS5wdXNoKGludGVyc2VjdChhLCBiLCBrMikpO1xyXG4gICAgICAgICAgICAgICAgICAgIGlmICghY2xvc2VkKSBzbGljZSA9IG5ld1NsaWNlKHNsaWNlcywgc2xpY2UsIGFyZWEsIGRpc3QsIG91dGVyKTtcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIC8vIHwgLS0+IHxcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuXHJcbiAgICAgICAgLy8gYWRkIHRoZSBsYXN0IHBvaW50XHJcbiAgICAgICAgYSA9IHBvaW50c1tsZW4gLSAxXTtcclxuICAgICAgICBhayA9IGFbYXhpc107XHJcbiAgICAgICAgaWYgKGFrID49IGsxICYmIGFrIDw9IGsyKSBzbGljZS5wdXNoKGEpO1xyXG5cclxuICAgICAgICAvLyBjbG9zZSB0aGUgcG9seWdvbiBpZiBpdHMgZW5kcG9pbnRzIGFyZSBub3QgdGhlIHNhbWUgYWZ0ZXIgY2xpcHBpbmdcclxuXHJcbiAgICAgICAgbGFzdCA9IHNsaWNlW3NsaWNlLmxlbmd0aCAtIDFdO1xyXG4gICAgICAgIGlmIChjbG9zZWQgJiYgbGFzdCAmJiAoc2xpY2VbMF1bMF0gIT09IGxhc3RbMF0gfHwgc2xpY2VbMF1bMV0gIT09IGxhc3RbMV0pKSBzbGljZS5wdXNoKHNsaWNlWzBdKTtcclxuXHJcbiAgICAgICAgLy8gYWRkIHRoZSBmaW5hbCBzbGljZVxyXG4gICAgICAgIG5ld1NsaWNlKHNsaWNlcywgc2xpY2UsIGFyZWEsIGRpc3QsIG91dGVyKTtcclxuICAgIH1cclxuXHJcbiAgICByZXR1cm4gc2xpY2VzO1xyXG59XHJcblxyXG5mdW5jdGlvbiBuZXdTbGljZShzbGljZXMsIHNsaWNlLCBhcmVhLCBkaXN0LCBvdXRlcikge1xyXG4gICAgaWYgKHNsaWNlLmxlbmd0aCkge1xyXG4gICAgICAgIC8vIHdlIGRvbid0IHJlY2FsY3VsYXRlIHRoZSBhcmVhL2xlbmd0aCBvZiB0aGUgdW5jbGlwcGVkIGdlb21ldHJ5IGJlY2F1c2UgdGhlIGNhc2Ugd2hlcmUgaXQgZ29lc1xyXG4gICAgICAgIC8vIGJlbG93IHRoZSB2aXNpYmlsaXR5IHRocmVzaG9sZCBhcyBhIHJlc3VsdCBvZiBjbGlwcGluZyBpcyByYXJlLCBzbyB3ZSBhdm9pZCBkb2luZyB1bm5lY2Vzc2FyeSB3b3JrXHJcbiAgICAgICAgc2xpY2UuYXJlYSA9IGFyZWE7XHJcbiAgICAgICAgc2xpY2UuZGlzdCA9IGRpc3Q7XHJcbiAgICAgICAgaWYgKG91dGVyICE9PSB1bmRlZmluZWQpIHNsaWNlLm91dGVyID0gb3V0ZXI7XHJcblxyXG4gICAgICAgIHNsaWNlcy5wdXNoKHNsaWNlKTtcclxuICAgIH1cclxuICAgIHJldHVybiBbXTtcclxufVxyXG4iLCIndXNlIHN0cmljdCc7XHJcblxyXG5tb2R1bGUuZXhwb3J0cyA9IGNvbnZlcnQ7XHJcblxyXG52YXIgc2ltcGxpZnkgPSByZXF1aXJlKCcuL3NpbXBsaWZ5Jyk7XHJcbnZhciBjcmVhdGVGZWF0dXJlID0gcmVxdWlyZSgnLi9mZWF0dXJlJyk7XHJcblxyXG4vLyBjb252ZXJ0cyBHZW9KU09OIGZlYXR1cmUgaW50byBhbiBpbnRlcm1lZGlhdGUgcHJvamVjdGVkIEpTT04gdmVjdG9yIGZvcm1hdCB3aXRoIHNpbXBsaWZpY2F0aW9uIGRhdGFcclxuXHJcbmZ1bmN0aW9uIGNvbnZlcnQoZGF0YSwgdG9sZXJhbmNlKSB7XHJcbiAgICB2YXIgZmVhdHVyZXMgPSBbXTtcclxuXHJcbiAgICBpZiAoZGF0YS50eXBlID09PSAnRmVhdHVyZUNvbGxlY3Rpb24nKSB7XHJcbiAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCBkYXRhLmZlYXR1cmVzLmxlbmd0aDsgaSsrKSB7XHJcbiAgICAgICAgICAgIGNvbnZlcnRGZWF0dXJlKGZlYXR1cmVzLCBkYXRhLmZlYXR1cmVzW2ldLCB0b2xlcmFuY2UpO1xyXG4gICAgICAgIH1cclxuICAgIH0gZWxzZSBpZiAoZGF0YS50eXBlID09PSAnRmVhdHVyZScpIHtcclxuICAgICAgICBjb252ZXJ0RmVhdHVyZShmZWF0dXJlcywgZGF0YSwgdG9sZXJhbmNlKTtcclxuXHJcbiAgICB9IGVsc2Uge1xyXG4gICAgICAgIC8vIHNpbmdsZSBnZW9tZXRyeSBvciBhIGdlb21ldHJ5IGNvbGxlY3Rpb25cclxuICAgICAgICBjb252ZXJ0RmVhdHVyZShmZWF0dXJlcywge2dlb21ldHJ5OiBkYXRhfSwgdG9sZXJhbmNlKTtcclxuICAgIH1cclxuICAgIHJldHVybiBmZWF0dXJlcztcclxufVxyXG5cclxuZnVuY3Rpb24gY29udmVydEZlYXR1cmUoZmVhdHVyZXMsIGZlYXR1cmUsIHRvbGVyYW5jZSkge1xyXG4gICAgaWYgKGZlYXR1cmUuZ2VvbWV0cnkgPT09IG51bGwpIHtcclxuICAgICAgICAvLyBpZ25vcmUgZmVhdHVyZXMgd2l0aCBudWxsIGdlb21ldHJ5XHJcbiAgICAgICAgcmV0dXJuO1xyXG4gICAgfVxyXG5cclxuICAgIHZhciBnZW9tID0gZmVhdHVyZS5nZW9tZXRyeSxcclxuICAgICAgICB0eXBlID0gZ2VvbS50eXBlLFxyXG4gICAgICAgIGNvb3JkcyA9IGdlb20uY29vcmRpbmF0ZXMsXHJcbiAgICAgICAgdGFncyA9IGZlYXR1cmUucHJvcGVydGllcyxcclxuICAgICAgICBpZCA9IGZlYXR1cmUuaWQsXHJcbiAgICAgICAgaSwgaiwgcmluZ3MsIHByb2plY3RlZFJpbmc7XHJcblxyXG4gICAgaWYgKHR5cGUgPT09ICdQb2ludCcpIHtcclxuICAgICAgICBmZWF0dXJlcy5wdXNoKGNyZWF0ZUZlYXR1cmUodGFncywgMSwgW3Byb2plY3RQb2ludChjb29yZHMpXSwgaWQpKTtcclxuXHJcbiAgICB9IGVsc2UgaWYgKHR5cGUgPT09ICdNdWx0aVBvaW50Jykge1xyXG4gICAgICAgIGZlYXR1cmVzLnB1c2goY3JlYXRlRmVhdHVyZSh0YWdzLCAxLCBwcm9qZWN0KGNvb3JkcyksIGlkKSk7XHJcblxyXG4gICAgfSBlbHNlIGlmICh0eXBlID09PSAnTGluZVN0cmluZycpIHtcclxuICAgICAgICBmZWF0dXJlcy5wdXNoKGNyZWF0ZUZlYXR1cmUodGFncywgMiwgW3Byb2plY3QoY29vcmRzLCB0b2xlcmFuY2UpXSwgaWQpKTtcclxuXHJcbiAgICB9IGVsc2UgaWYgKHR5cGUgPT09ICdNdWx0aUxpbmVTdHJpbmcnIHx8IHR5cGUgPT09ICdQb2x5Z29uJykge1xyXG4gICAgICAgIHJpbmdzID0gW107XHJcbiAgICAgICAgZm9yIChpID0gMDsgaSA8IGNvb3Jkcy5sZW5ndGg7IGkrKykge1xyXG4gICAgICAgICAgICBwcm9qZWN0ZWRSaW5nID0gcHJvamVjdChjb29yZHNbaV0sIHRvbGVyYW5jZSk7XHJcbiAgICAgICAgICAgIGlmICh0eXBlID09PSAnUG9seWdvbicpIHByb2plY3RlZFJpbmcub3V0ZXIgPSAoaSA9PT0gMCk7XHJcbiAgICAgICAgICAgIHJpbmdzLnB1c2gocHJvamVjdGVkUmluZyk7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIGZlYXR1cmVzLnB1c2goY3JlYXRlRmVhdHVyZSh0YWdzLCB0eXBlID09PSAnUG9seWdvbicgPyAzIDogMiwgcmluZ3MsIGlkKSk7XHJcblxyXG4gICAgfSBlbHNlIGlmICh0eXBlID09PSAnTXVsdGlQb2x5Z29uJykge1xyXG4gICAgICAgIHJpbmdzID0gW107XHJcbiAgICAgICAgZm9yIChpID0gMDsgaSA8IGNvb3Jkcy5sZW5ndGg7IGkrKykge1xyXG4gICAgICAgICAgICBmb3IgKGogPSAwOyBqIDwgY29vcmRzW2ldLmxlbmd0aDsgaisrKSB7XHJcbiAgICAgICAgICAgICAgICBwcm9qZWN0ZWRSaW5nID0gcHJvamVjdChjb29yZHNbaV1bal0sIHRvbGVyYW5jZSk7XHJcbiAgICAgICAgICAgICAgICBwcm9qZWN0ZWRSaW5nLm91dGVyID0gKGogPT09IDApO1xyXG4gICAgICAgICAgICAgICAgcmluZ3MucHVzaChwcm9qZWN0ZWRSaW5nKTtcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuICAgICAgICBmZWF0dXJlcy5wdXNoKGNyZWF0ZUZlYXR1cmUodGFncywgMywgcmluZ3MsIGlkKSk7XHJcblxyXG4gICAgfSBlbHNlIGlmICh0eXBlID09PSAnR2VvbWV0cnlDb2xsZWN0aW9uJykge1xyXG4gICAgICAgIGZvciAoaSA9IDA7IGkgPCBnZW9tLmdlb21ldHJpZXMubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICAgICAgY29udmVydEZlYXR1cmUoZmVhdHVyZXMsIHtcclxuICAgICAgICAgICAgICAgIGdlb21ldHJ5OiBnZW9tLmdlb21ldHJpZXNbaV0sXHJcbiAgICAgICAgICAgICAgICBwcm9wZXJ0aWVzOiB0YWdzXHJcbiAgICAgICAgICAgIH0sIHRvbGVyYW5jZSk7XHJcbiAgICAgICAgfVxyXG5cclxuICAgIH0gZWxzZSB7XHJcbiAgICAgICAgdGhyb3cgbmV3IEVycm9yKCdJbnB1dCBkYXRhIGlzIG5vdCBhIHZhbGlkIEdlb0pTT04gb2JqZWN0LicpO1xyXG4gICAgfVxyXG59XHJcblxyXG5mdW5jdGlvbiBwcm9qZWN0KGxvbmxhdHMsIHRvbGVyYW5jZSkge1xyXG4gICAgdmFyIHByb2plY3RlZCA9IFtdO1xyXG4gICAgZm9yICh2YXIgaSA9IDA7IGkgPCBsb25sYXRzLmxlbmd0aDsgaSsrKSB7XHJcbiAgICAgICAgcHJvamVjdGVkLnB1c2gocHJvamVjdFBvaW50KGxvbmxhdHNbaV0pKTtcclxuICAgIH1cclxuICAgIGlmICh0b2xlcmFuY2UpIHtcclxuICAgICAgICBzaW1wbGlmeShwcm9qZWN0ZWQsIHRvbGVyYW5jZSk7XHJcbiAgICAgICAgY2FsY1NpemUocHJvamVjdGVkKTtcclxuICAgIH1cclxuICAgIHJldHVybiBwcm9qZWN0ZWQ7XHJcbn1cclxuXHJcbmZ1bmN0aW9uIHByb2plY3RQb2ludChwKSB7XHJcbiAgICB2YXIgc2luID0gTWF0aC5zaW4ocFsxXSAqIE1hdGguUEkgLyAxODApLFxyXG4gICAgICAgIHggPSAocFswXSAvIDM2MCArIDAuNSksXHJcbiAgICAgICAgeSA9ICgwLjUgLSAwLjI1ICogTWF0aC5sb2coKDEgKyBzaW4pIC8gKDEgLSBzaW4pKSAvIE1hdGguUEkpO1xyXG5cclxuICAgIHkgPSB5IDwgMCA/IDAgOlxyXG4gICAgICAgIHkgPiAxID8gMSA6IHk7XHJcblxyXG4gICAgcmV0dXJuIFt4LCB5LCAwXTtcclxufVxyXG5cclxuLy8gY2FsY3VsYXRlIGFyZWEgYW5kIGxlbmd0aCBvZiB0aGUgcG9seVxyXG5mdW5jdGlvbiBjYWxjU2l6ZShwb2ludHMpIHtcclxuICAgIHZhciBhcmVhID0gMCxcclxuICAgICAgICBkaXN0ID0gMDtcclxuXHJcbiAgICBmb3IgKHZhciBpID0gMCwgYSwgYjsgaSA8IHBvaW50cy5sZW5ndGggLSAxOyBpKyspIHtcclxuICAgICAgICBhID0gYiB8fCBwb2ludHNbaV07XHJcbiAgICAgICAgYiA9IHBvaW50c1tpICsgMV07XHJcblxyXG4gICAgICAgIGFyZWEgKz0gYVswXSAqIGJbMV0gLSBiWzBdICogYVsxXTtcclxuXHJcbiAgICAgICAgLy8gdXNlIE1hbmhhdHRhbiBkaXN0YW5jZSBpbnN0ZWFkIG9mIEV1Y2xpZGlhbiBvbmUgdG8gYXZvaWQgZXhwZW5zaXZlIHNxdWFyZSByb290IGNvbXB1dGF0aW9uXHJcbiAgICAgICAgZGlzdCArPSBNYXRoLmFicyhiWzBdIC0gYVswXSkgKyBNYXRoLmFicyhiWzFdIC0gYVsxXSk7XHJcbiAgICB9XHJcbiAgICBwb2ludHMuYXJlYSA9IE1hdGguYWJzKGFyZWEgLyAyKTtcclxuICAgIHBvaW50cy5kaXN0ID0gZGlzdDtcclxufVxyXG4iLCIndXNlIHN0cmljdCc7XHJcblxyXG5tb2R1bGUuZXhwb3J0cyA9IGNyZWF0ZUZlYXR1cmU7XHJcblxyXG5mdW5jdGlvbiBjcmVhdGVGZWF0dXJlKHRhZ3MsIHR5cGUsIGdlb20sIGlkKSB7XHJcbiAgICB2YXIgZmVhdHVyZSA9IHtcclxuICAgICAgICBpZDogaWQgfHwgbnVsbCxcclxuICAgICAgICB0eXBlOiB0eXBlLFxyXG4gICAgICAgIGdlb21ldHJ5OiBnZW9tLFxyXG4gICAgICAgIHRhZ3M6IHRhZ3MgfHwgbnVsbCxcclxuICAgICAgICBtaW46IFtJbmZpbml0eSwgSW5maW5pdHldLCAvLyBpbml0aWFsIGJib3ggdmFsdWVzXHJcbiAgICAgICAgbWF4OiBbLUluZmluaXR5LCAtSW5maW5pdHldXHJcbiAgICB9O1xyXG4gICAgY2FsY0JCb3goZmVhdHVyZSk7XHJcbiAgICByZXR1cm4gZmVhdHVyZTtcclxufVxyXG5cclxuLy8gY2FsY3VsYXRlIHRoZSBmZWF0dXJlIGJvdW5kaW5nIGJveCBmb3IgZmFzdGVyIGNsaXBwaW5nIGxhdGVyXHJcbmZ1bmN0aW9uIGNhbGNCQm94KGZlYXR1cmUpIHtcclxuICAgIHZhciBnZW9tZXRyeSA9IGZlYXR1cmUuZ2VvbWV0cnksXHJcbiAgICAgICAgbWluID0gZmVhdHVyZS5taW4sXHJcbiAgICAgICAgbWF4ID0gZmVhdHVyZS5tYXg7XHJcblxyXG4gICAgaWYgKGZlYXR1cmUudHlwZSA9PT0gMSkge1xyXG4gICAgICAgIGNhbGNSaW5nQkJveChtaW4sIG1heCwgZ2VvbWV0cnkpO1xyXG4gICAgfSBlbHNlIHtcclxuICAgICAgICBmb3IgKHZhciBpID0gMDsgaSA8IGdlb21ldHJ5Lmxlbmd0aDsgaSsrKSB7XHJcbiAgICAgICAgICAgIGNhbGNSaW5nQkJveChtaW4sIG1heCwgZ2VvbWV0cnlbaV0pO1xyXG4gICAgICAgIH1cclxuICAgIH1cclxuXHJcbiAgICByZXR1cm4gZmVhdHVyZTtcclxufVxyXG5cclxuZnVuY3Rpb24gY2FsY1JpbmdCQm94KG1pbiwgbWF4LCBwb2ludHMpIHtcclxuICAgIGZvciAodmFyIGkgPSAwLCBwOyBpIDwgcG9pbnRzLmxlbmd0aDsgaSsrKSB7XHJcbiAgICAgICAgcCA9IHBvaW50c1tpXTtcclxuICAgICAgICBtaW5bMF0gPSBNYXRoLm1pbihwWzBdLCBtaW5bMF0pO1xyXG4gICAgICAgIG1heFswXSA9IE1hdGgubWF4KHBbMF0sIG1heFswXSk7XHJcbiAgICAgICAgbWluWzFdID0gTWF0aC5taW4ocFsxXSwgbWluWzFdKTtcclxuICAgICAgICBtYXhbMV0gPSBNYXRoLm1heChwWzFdLCBtYXhbMV0pO1xyXG4gICAgfVxyXG59XHJcbiIsIid1c2Ugc3RyaWN0JztcclxuXHJcbm1vZHVsZS5leHBvcnRzID0gZ2VvanNvbnZ0O1xyXG5cclxudmFyIGNvbnZlcnQgPSByZXF1aXJlKCcuL2NvbnZlcnQnKSwgICAgIC8vIEdlb0pTT04gY29udmVyc2lvbiBhbmQgcHJlcHJvY2Vzc2luZ1xyXG4gICAgdHJhbnNmb3JtID0gcmVxdWlyZSgnLi90cmFuc2Zvcm0nKSwgLy8gY29vcmRpbmF0ZSB0cmFuc2Zvcm1hdGlvblxyXG4gICAgY2xpcCA9IHJlcXVpcmUoJy4vY2xpcCcpLCAgICAgICAgICAgLy8gc3RyaXBlIGNsaXBwaW5nIGFsZ29yaXRobVxyXG4gICAgd3JhcCA9IHJlcXVpcmUoJy4vd3JhcCcpLCAgICAgICAgICAgLy8gZGF0ZSBsaW5lIHByb2Nlc3NpbmdcclxuICAgIGNyZWF0ZVRpbGUgPSByZXF1aXJlKCcuL3RpbGUnKTsgICAgIC8vIGZpbmFsIHNpbXBsaWZpZWQgdGlsZSBnZW5lcmF0aW9uXHJcblxyXG5cclxuZnVuY3Rpb24gZ2VvanNvbnZ0KGRhdGEsIG9wdGlvbnMpIHtcclxuICAgIHJldHVybiBuZXcgR2VvSlNPTlZUKGRhdGEsIG9wdGlvbnMpO1xyXG59XHJcblxyXG5mdW5jdGlvbiBHZW9KU09OVlQoZGF0YSwgb3B0aW9ucykge1xyXG4gICAgb3B0aW9ucyA9IHRoaXMub3B0aW9ucyA9IGV4dGVuZChPYmplY3QuY3JlYXRlKHRoaXMub3B0aW9ucyksIG9wdGlvbnMpO1xyXG5cclxuICAgIHZhciBkZWJ1ZyA9IG9wdGlvbnMuZGVidWc7XHJcblxyXG4gICAgaWYgKGRlYnVnKSBjb25zb2xlLnRpbWUoJ3ByZXByb2Nlc3MgZGF0YScpO1xyXG5cclxuICAgIHZhciB6MiA9IDEgPDwgb3B0aW9ucy5tYXhab29tLCAvLyAyXnpcclxuICAgICAgICBmZWF0dXJlcyA9IGNvbnZlcnQoZGF0YSwgb3B0aW9ucy50b2xlcmFuY2UgLyAoejIgKiBvcHRpb25zLmV4dGVudCkpO1xyXG5cclxuICAgIHRoaXMudGlsZXMgPSB7fTtcclxuICAgIHRoaXMudGlsZUNvb3JkcyA9IFtdO1xyXG5cclxuICAgIGlmIChkZWJ1Zykge1xyXG4gICAgICAgIGNvbnNvbGUudGltZUVuZCgncHJlcHJvY2VzcyBkYXRhJyk7XHJcbiAgICAgICAgY29uc29sZS5sb2coJ2luZGV4OiBtYXhab29tOiAlZCwgbWF4UG9pbnRzOiAlZCcsIG9wdGlvbnMuaW5kZXhNYXhab29tLCBvcHRpb25zLmluZGV4TWF4UG9pbnRzKTtcclxuICAgICAgICBjb25zb2xlLnRpbWUoJ2dlbmVyYXRlIHRpbGVzJyk7XHJcbiAgICAgICAgdGhpcy5zdGF0cyA9IHt9O1xyXG4gICAgICAgIHRoaXMudG90YWwgPSAwO1xyXG4gICAgfVxyXG5cclxuICAgIGZlYXR1cmVzID0gd3JhcChmZWF0dXJlcywgb3B0aW9ucy5idWZmZXIgLyBvcHRpb25zLmV4dGVudCwgaW50ZXJzZWN0WCk7XHJcblxyXG4gICAgLy8gc3RhcnQgc2xpY2luZyBmcm9tIHRoZSB0b3AgdGlsZSBkb3duXHJcbiAgICBpZiAoZmVhdHVyZXMubGVuZ3RoKSB0aGlzLnNwbGl0VGlsZShmZWF0dXJlcywgMCwgMCwgMCk7XHJcblxyXG4gICAgaWYgKGRlYnVnKSB7XHJcbiAgICAgICAgaWYgKGZlYXR1cmVzLmxlbmd0aCkgY29uc29sZS5sb2coJ2ZlYXR1cmVzOiAlZCwgcG9pbnRzOiAlZCcsIHRoaXMudGlsZXNbMF0ubnVtRmVhdHVyZXMsIHRoaXMudGlsZXNbMF0ubnVtUG9pbnRzKTtcclxuICAgICAgICBjb25zb2xlLnRpbWVFbmQoJ2dlbmVyYXRlIHRpbGVzJyk7XHJcbiAgICAgICAgY29uc29sZS5sb2coJ3RpbGVzIGdlbmVyYXRlZDonLCB0aGlzLnRvdGFsLCBKU09OLnN0cmluZ2lmeSh0aGlzLnN0YXRzKSk7XHJcbiAgICB9XHJcbn1cclxuXHJcbkdlb0pTT05WVC5wcm90b3R5cGUub3B0aW9ucyA9IHtcclxuICAgIG1heFpvb206IDE0LCAgICAgICAgICAgIC8vIG1heCB6b29tIHRvIHByZXNlcnZlIGRldGFpbCBvblxyXG4gICAgaW5kZXhNYXhab29tOiA1LCAgICAgICAgLy8gbWF4IHpvb20gaW4gdGhlIHRpbGUgaW5kZXhcclxuICAgIGluZGV4TWF4UG9pbnRzOiAxMDAwMDAsIC8vIG1heCBudW1iZXIgb2YgcG9pbnRzIHBlciB0aWxlIGluIHRoZSB0aWxlIGluZGV4XHJcbiAgICBzb2xpZENoaWxkcmVuOiBmYWxzZSwgICAvLyB3aGV0aGVyIHRvIHRpbGUgc29saWQgc3F1YXJlIHRpbGVzIGZ1cnRoZXJcclxuICAgIHRvbGVyYW5jZTogMywgICAgICAgICAgIC8vIHNpbXBsaWZpY2F0aW9uIHRvbGVyYW5jZSAoaGlnaGVyIG1lYW5zIHNpbXBsZXIpXHJcbiAgICBleHRlbnQ6IDQwOTYsICAgICAgICAgICAvLyB0aWxlIGV4dGVudFxyXG4gICAgYnVmZmVyOiA2NCwgICAgICAgICAgICAgLy8gdGlsZSBidWZmZXIgb24gZWFjaCBzaWRlXHJcbiAgICBkZWJ1ZzogMCAgICAgICAgICAgICAgICAvLyBsb2dnaW5nIGxldmVsICgwLCAxIG9yIDIpXHJcbn07XHJcblxyXG5HZW9KU09OVlQucHJvdG90eXBlLnNwbGl0VGlsZSA9IGZ1bmN0aW9uIChmZWF0dXJlcywgeiwgeCwgeSwgY3osIGN4LCBjeSkge1xyXG5cclxuICAgIHZhciBzdGFjayA9IFtmZWF0dXJlcywgeiwgeCwgeV0sXHJcbiAgICAgICAgb3B0aW9ucyA9IHRoaXMub3B0aW9ucyxcclxuICAgICAgICBkZWJ1ZyA9IG9wdGlvbnMuZGVidWcsXHJcbiAgICAgICAgc29saWQgPSBudWxsO1xyXG5cclxuICAgIC8vIGF2b2lkIHJlY3Vyc2lvbiBieSB1c2luZyBhIHByb2Nlc3NpbmcgcXVldWVcclxuICAgIHdoaWxlIChzdGFjay5sZW5ndGgpIHtcclxuICAgICAgICB5ID0gc3RhY2sucG9wKCk7XHJcbiAgICAgICAgeCA9IHN0YWNrLnBvcCgpO1xyXG4gICAgICAgIHogPSBzdGFjay5wb3AoKTtcclxuICAgICAgICBmZWF0dXJlcyA9IHN0YWNrLnBvcCgpO1xyXG5cclxuICAgICAgICB2YXIgejIgPSAxIDw8IHosXHJcbiAgICAgICAgICAgIGlkID0gdG9JRCh6LCB4LCB5KSxcclxuICAgICAgICAgICAgdGlsZSA9IHRoaXMudGlsZXNbaWRdLFxyXG4gICAgICAgICAgICB0aWxlVG9sZXJhbmNlID0geiA9PT0gb3B0aW9ucy5tYXhab29tID8gMCA6IG9wdGlvbnMudG9sZXJhbmNlIC8gKHoyICogb3B0aW9ucy5leHRlbnQpO1xyXG5cclxuICAgICAgICBpZiAoIXRpbGUpIHtcclxuICAgICAgICAgICAgaWYgKGRlYnVnID4gMSkgY29uc29sZS50aW1lKCdjcmVhdGlvbicpO1xyXG5cclxuICAgICAgICAgICAgdGlsZSA9IHRoaXMudGlsZXNbaWRdID0gY3JlYXRlVGlsZShmZWF0dXJlcywgejIsIHgsIHksIHRpbGVUb2xlcmFuY2UsIHogPT09IG9wdGlvbnMubWF4Wm9vbSk7XHJcbiAgICAgICAgICAgIHRoaXMudGlsZUNvb3Jkcy5wdXNoKHt6OiB6LCB4OiB4LCB5OiB5fSk7XHJcblxyXG4gICAgICAgICAgICBpZiAoZGVidWcpIHtcclxuICAgICAgICAgICAgICAgIGlmIChkZWJ1ZyA+IDEpIHtcclxuICAgICAgICAgICAgICAgICAgICBjb25zb2xlLmxvZygndGlsZSB6JWQtJWQtJWQgKGZlYXR1cmVzOiAlZCwgcG9pbnRzOiAlZCwgc2ltcGxpZmllZDogJWQpJyxcclxuICAgICAgICAgICAgICAgICAgICAgICAgeiwgeCwgeSwgdGlsZS5udW1GZWF0dXJlcywgdGlsZS5udW1Qb2ludHMsIHRpbGUubnVtU2ltcGxpZmllZCk7XHJcbiAgICAgICAgICAgICAgICAgICAgY29uc29sZS50aW1lRW5kKCdjcmVhdGlvbicpO1xyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgdmFyIGtleSA9ICd6JyArIHo7XHJcbiAgICAgICAgICAgICAgICB0aGlzLnN0YXRzW2tleV0gPSAodGhpcy5zdGF0c1trZXldIHx8IDApICsgMTtcclxuICAgICAgICAgICAgICAgIHRoaXMudG90YWwrKztcclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH1cclxuXHJcbiAgICAgICAgLy8gc2F2ZSByZWZlcmVuY2UgdG8gb3JpZ2luYWwgZ2VvbWV0cnkgaW4gdGlsZSBzbyB0aGF0IHdlIGNhbiBkcmlsbCBkb3duIGxhdGVyIGlmIHdlIHN0b3Agbm93XHJcbiAgICAgICAgdGlsZS5zb3VyY2UgPSBmZWF0dXJlcztcclxuXHJcbiAgICAgICAgLy8gaWYgaXQncyB0aGUgZmlyc3QtcGFzcyB0aWxpbmdcclxuICAgICAgICBpZiAoIWN6KSB7XHJcbiAgICAgICAgICAgIC8vIHN0b3AgdGlsaW5nIGlmIHdlIHJlYWNoZWQgbWF4IHpvb20sIG9yIGlmIHRoZSB0aWxlIGlzIHRvbyBzaW1wbGVcclxuICAgICAgICAgICAgaWYgKHogPT09IG9wdGlvbnMuaW5kZXhNYXhab29tIHx8IHRpbGUubnVtUG9pbnRzIDw9IG9wdGlvbnMuaW5kZXhNYXhQb2ludHMpIGNvbnRpbnVlO1xyXG5cclxuICAgICAgICAvLyBpZiBhIGRyaWxsZG93biB0byBhIHNwZWNpZmljIHRpbGVcclxuICAgICAgICB9IGVsc2Uge1xyXG4gICAgICAgICAgICAvLyBzdG9wIHRpbGluZyBpZiB3ZSByZWFjaGVkIGJhc2Ugem9vbSBvciBvdXIgdGFyZ2V0IHRpbGUgem9vbVxyXG4gICAgICAgICAgICBpZiAoeiA9PT0gb3B0aW9ucy5tYXhab29tIHx8IHogPT09IGN6KSBjb250aW51ZTtcclxuXHJcbiAgICAgICAgICAgIC8vIHN0b3AgdGlsaW5nIGlmIGl0J3Mgbm90IGFuIGFuY2VzdG9yIG9mIHRoZSB0YXJnZXQgdGlsZVxyXG4gICAgICAgICAgICB2YXIgbSA9IDEgPDwgKGN6IC0geik7XHJcbiAgICAgICAgICAgIGlmICh4ICE9PSBNYXRoLmZsb29yKGN4IC8gbSkgfHwgeSAhPT0gTWF0aC5mbG9vcihjeSAvIG0pKSBjb250aW51ZTtcclxuICAgICAgICB9XHJcblxyXG4gICAgICAgIC8vIHN0b3AgdGlsaW5nIGlmIHRoZSB0aWxlIGlzIHNvbGlkIGNsaXBwZWQgc3F1YXJlXHJcbiAgICAgICAgaWYgKCFvcHRpb25zLnNvbGlkQ2hpbGRyZW4gJiYgaXNDbGlwcGVkU3F1YXJlKHRpbGUsIG9wdGlvbnMuZXh0ZW50LCBvcHRpb25zLmJ1ZmZlcikpIHtcclxuICAgICAgICAgICAgaWYgKGN6KSBzb2xpZCA9IHo7IC8vIGFuZCByZW1lbWJlciB0aGUgem9vbSBpZiB3ZSdyZSBkcmlsbGluZyBkb3duXHJcbiAgICAgICAgICAgIGNvbnRpbnVlO1xyXG4gICAgICAgIH1cclxuXHJcbiAgICAgICAgLy8gaWYgd2Ugc2xpY2UgZnVydGhlciBkb3duLCBubyBuZWVkIHRvIGtlZXAgc291cmNlIGdlb21ldHJ5XHJcbiAgICAgICAgdGlsZS5zb3VyY2UgPSBudWxsO1xyXG5cclxuICAgICAgICBpZiAoZGVidWcgPiAxKSBjb25zb2xlLnRpbWUoJ2NsaXBwaW5nJyk7XHJcblxyXG4gICAgICAgIC8vIHZhbHVlcyB3ZSdsbCB1c2UgZm9yIGNsaXBwaW5nXHJcbiAgICAgICAgdmFyIGsxID0gMC41ICogb3B0aW9ucy5idWZmZXIgLyBvcHRpb25zLmV4dGVudCxcclxuICAgICAgICAgICAgazIgPSAwLjUgLSBrMSxcclxuICAgICAgICAgICAgazMgPSAwLjUgKyBrMSxcclxuICAgICAgICAgICAgazQgPSAxICsgazEsXHJcbiAgICAgICAgICAgIHRsLCBibCwgdHIsIGJyLCBsZWZ0LCByaWdodDtcclxuXHJcbiAgICAgICAgdGwgPSBibCA9IHRyID0gYnIgPSBudWxsO1xyXG5cclxuICAgICAgICBsZWZ0ICA9IGNsaXAoZmVhdHVyZXMsIHoyLCB4IC0gazEsIHggKyBrMywgMCwgaW50ZXJzZWN0WCwgdGlsZS5taW5bMF0sIHRpbGUubWF4WzBdKTtcclxuICAgICAgICByaWdodCA9IGNsaXAoZmVhdHVyZXMsIHoyLCB4ICsgazIsIHggKyBrNCwgMCwgaW50ZXJzZWN0WCwgdGlsZS5taW5bMF0sIHRpbGUubWF4WzBdKTtcclxuXHJcbiAgICAgICAgaWYgKGxlZnQpIHtcclxuICAgICAgICAgICAgdGwgPSBjbGlwKGxlZnQsIHoyLCB5IC0gazEsIHkgKyBrMywgMSwgaW50ZXJzZWN0WSwgdGlsZS5taW5bMV0sIHRpbGUubWF4WzFdKTtcclxuICAgICAgICAgICAgYmwgPSBjbGlwKGxlZnQsIHoyLCB5ICsgazIsIHkgKyBrNCwgMSwgaW50ZXJzZWN0WSwgdGlsZS5taW5bMV0sIHRpbGUubWF4WzFdKTtcclxuICAgICAgICB9XHJcblxyXG4gICAgICAgIGlmIChyaWdodCkge1xyXG4gICAgICAgICAgICB0ciA9IGNsaXAocmlnaHQsIHoyLCB5IC0gazEsIHkgKyBrMywgMSwgaW50ZXJzZWN0WSwgdGlsZS5taW5bMV0sIHRpbGUubWF4WzFdKTtcclxuICAgICAgICAgICAgYnIgPSBjbGlwKHJpZ2h0LCB6MiwgeSArIGsyLCB5ICsgazQsIDEsIGludGVyc2VjdFksIHRpbGUubWluWzFdLCB0aWxlLm1heFsxXSk7XHJcbiAgICAgICAgfVxyXG5cclxuICAgICAgICBpZiAoZGVidWcgPiAxKSBjb25zb2xlLnRpbWVFbmQoJ2NsaXBwaW5nJyk7XHJcblxyXG4gICAgICAgIGlmIChmZWF0dXJlcy5sZW5ndGgpIHtcclxuICAgICAgICAgICAgc3RhY2sucHVzaCh0bCB8fCBbXSwgeiArIDEsIHggKiAyLCAgICAgeSAqIDIpO1xyXG4gICAgICAgICAgICBzdGFjay5wdXNoKGJsIHx8IFtdLCB6ICsgMSwgeCAqIDIsICAgICB5ICogMiArIDEpO1xyXG4gICAgICAgICAgICBzdGFjay5wdXNoKHRyIHx8IFtdLCB6ICsgMSwgeCAqIDIgKyAxLCB5ICogMik7XHJcbiAgICAgICAgICAgIHN0YWNrLnB1c2goYnIgfHwgW10sIHogKyAxLCB4ICogMiArIDEsIHkgKiAyICsgMSk7XHJcbiAgICAgICAgfVxyXG4gICAgfVxyXG5cclxuICAgIHJldHVybiBzb2xpZDtcclxufTtcclxuXHJcbkdlb0pTT05WVC5wcm90b3R5cGUuZ2V0VGlsZSA9IGZ1bmN0aW9uICh6LCB4LCB5KSB7XHJcbiAgICB2YXIgb3B0aW9ucyA9IHRoaXMub3B0aW9ucyxcclxuICAgICAgICBleHRlbnQgPSBvcHRpb25zLmV4dGVudCxcclxuICAgICAgICBkZWJ1ZyA9IG9wdGlvbnMuZGVidWc7XHJcblxyXG4gICAgdmFyIHoyID0gMSA8PCB6O1xyXG4gICAgeCA9ICgoeCAlIHoyKSArIHoyKSAlIHoyOyAvLyB3cmFwIHRpbGUgeCBjb29yZGluYXRlXHJcblxyXG4gICAgdmFyIGlkID0gdG9JRCh6LCB4LCB5KTtcclxuICAgIGlmICh0aGlzLnRpbGVzW2lkXSkgcmV0dXJuIHRyYW5zZm9ybS50aWxlKHRoaXMudGlsZXNbaWRdLCBleHRlbnQpO1xyXG5cclxuICAgIGlmIChkZWJ1ZyA+IDEpIGNvbnNvbGUubG9nKCdkcmlsbGluZyBkb3duIHRvIHolZC0lZC0lZCcsIHosIHgsIHkpO1xyXG5cclxuICAgIHZhciB6MCA9IHosXHJcbiAgICAgICAgeDAgPSB4LFxyXG4gICAgICAgIHkwID0geSxcclxuICAgICAgICBwYXJlbnQ7XHJcblxyXG4gICAgd2hpbGUgKCFwYXJlbnQgJiYgejAgPiAwKSB7XHJcbiAgICAgICAgejAtLTtcclxuICAgICAgICB4MCA9IE1hdGguZmxvb3IoeDAgLyAyKTtcclxuICAgICAgICB5MCA9IE1hdGguZmxvb3IoeTAgLyAyKTtcclxuICAgICAgICBwYXJlbnQgPSB0aGlzLnRpbGVzW3RvSUQoejAsIHgwLCB5MCldO1xyXG4gICAgfVxyXG5cclxuICAgIGlmICghcGFyZW50IHx8ICFwYXJlbnQuc291cmNlKSByZXR1cm4gbnVsbDtcclxuXHJcbiAgICAvLyBpZiB3ZSBmb3VuZCBhIHBhcmVudCB0aWxlIGNvbnRhaW5pbmcgdGhlIG9yaWdpbmFsIGdlb21ldHJ5LCB3ZSBjYW4gZHJpbGwgZG93biBmcm9tIGl0XHJcbiAgICBpZiAoZGVidWcgPiAxKSBjb25zb2xlLmxvZygnZm91bmQgcGFyZW50IHRpbGUgeiVkLSVkLSVkJywgejAsIHgwLCB5MCk7XHJcblxyXG4gICAgLy8gaXQgcGFyZW50IHRpbGUgaXMgYSBzb2xpZCBjbGlwcGVkIHNxdWFyZSwgcmV0dXJuIGl0IGluc3RlYWQgc2luY2UgaXQncyBpZGVudGljYWxcclxuICAgIGlmIChpc0NsaXBwZWRTcXVhcmUocGFyZW50LCBleHRlbnQsIG9wdGlvbnMuYnVmZmVyKSkgcmV0dXJuIHRyYW5zZm9ybS50aWxlKHBhcmVudCwgZXh0ZW50KTtcclxuXHJcbiAgICBpZiAoZGVidWcgPiAxKSBjb25zb2xlLnRpbWUoJ2RyaWxsaW5nIGRvd24nKTtcclxuICAgIHZhciBzb2xpZCA9IHRoaXMuc3BsaXRUaWxlKHBhcmVudC5zb3VyY2UsIHowLCB4MCwgeTAsIHosIHgsIHkpO1xyXG4gICAgaWYgKGRlYnVnID4gMSkgY29uc29sZS50aW1lRW5kKCdkcmlsbGluZyBkb3duJyk7XHJcblxyXG4gICAgLy8gb25lIG9mIHRoZSBwYXJlbnQgdGlsZXMgd2FzIGEgc29saWQgY2xpcHBlZCBzcXVhcmVcclxuICAgIGlmIChzb2xpZCAhPT0gbnVsbCkge1xyXG4gICAgICAgIHZhciBtID0gMSA8PCAoeiAtIHNvbGlkKTtcclxuICAgICAgICBpZCA9IHRvSUQoc29saWQsIE1hdGguZmxvb3IoeCAvIG0pLCBNYXRoLmZsb29yKHkgLyBtKSk7XHJcbiAgICB9XHJcblxyXG4gICAgcmV0dXJuIHRoaXMudGlsZXNbaWRdID8gdHJhbnNmb3JtLnRpbGUodGhpcy50aWxlc1tpZF0sIGV4dGVudCkgOiBudWxsO1xyXG59O1xyXG5cclxuZnVuY3Rpb24gdG9JRCh6LCB4LCB5KSB7XHJcbiAgICByZXR1cm4gKCgoMSA8PCB6KSAqIHkgKyB4KSAqIDMyKSArIHo7XHJcbn1cclxuXHJcbmZ1bmN0aW9uIGludGVyc2VjdFgoYSwgYiwgeCkge1xyXG4gICAgcmV0dXJuIFt4LCAoeCAtIGFbMF0pICogKGJbMV0gLSBhWzFdKSAvIChiWzBdIC0gYVswXSkgKyBhWzFdLCAxXTtcclxufVxyXG5mdW5jdGlvbiBpbnRlcnNlY3RZKGEsIGIsIHkpIHtcclxuICAgIHJldHVybiBbKHkgLSBhWzFdKSAqIChiWzBdIC0gYVswXSkgLyAoYlsxXSAtIGFbMV0pICsgYVswXSwgeSwgMV07XHJcbn1cclxuXHJcbmZ1bmN0aW9uIGV4dGVuZChkZXN0LCBzcmMpIHtcclxuICAgIGZvciAodmFyIGkgaW4gc3JjKSBkZXN0W2ldID0gc3JjW2ldO1xyXG4gICAgcmV0dXJuIGRlc3Q7XHJcbn1cclxuXHJcbi8vIGNoZWNrcyB3aGV0aGVyIGEgdGlsZSBpcyBhIHdob2xlLWFyZWEgZmlsbCBhZnRlciBjbGlwcGluZzsgaWYgaXQgaXMsIHRoZXJlJ3Mgbm8gc2Vuc2Ugc2xpY2luZyBpdCBmdXJ0aGVyXHJcbmZ1bmN0aW9uIGlzQ2xpcHBlZFNxdWFyZSh0aWxlLCBleHRlbnQsIGJ1ZmZlcikge1xyXG5cclxuICAgIHZhciBmZWF0dXJlcyA9IHRpbGUuc291cmNlO1xyXG4gICAgaWYgKGZlYXR1cmVzLmxlbmd0aCAhPT0gMSkgcmV0dXJuIGZhbHNlO1xyXG5cclxuICAgIHZhciBmZWF0dXJlID0gZmVhdHVyZXNbMF07XHJcbiAgICBpZiAoZmVhdHVyZS50eXBlICE9PSAzIHx8IGZlYXR1cmUuZ2VvbWV0cnkubGVuZ3RoID4gMSkgcmV0dXJuIGZhbHNlO1xyXG5cclxuICAgIHZhciBsZW4gPSBmZWF0dXJlLmdlb21ldHJ5WzBdLmxlbmd0aDtcclxuICAgIGlmIChsZW4gIT09IDUpIHJldHVybiBmYWxzZTtcclxuXHJcbiAgICBmb3IgKHZhciBpID0gMDsgaSA8IGxlbjsgaSsrKSB7XHJcbiAgICAgICAgdmFyIHAgPSB0cmFuc2Zvcm0ucG9pbnQoZmVhdHVyZS5nZW9tZXRyeVswXVtpXSwgZXh0ZW50LCB0aWxlLnoyLCB0aWxlLngsIHRpbGUueSk7XHJcbiAgICAgICAgaWYgKChwWzBdICE9PSAtYnVmZmVyICYmIHBbMF0gIT09IGV4dGVudCArIGJ1ZmZlcikgfHxcclxuICAgICAgICAgICAgKHBbMV0gIT09IC1idWZmZXIgJiYgcFsxXSAhPT0gZXh0ZW50ICsgYnVmZmVyKSkgcmV0dXJuIGZhbHNlO1xyXG4gICAgfVxyXG5cclxuICAgIHJldHVybiB0cnVlO1xyXG59XHJcbiIsIid1c2Ugc3RyaWN0JztcclxuXHJcbm1vZHVsZS5leHBvcnRzID0gc2ltcGxpZnk7XHJcblxyXG4vLyBjYWxjdWxhdGUgc2ltcGxpZmljYXRpb24gZGF0YSB1c2luZyBvcHRpbWl6ZWQgRG91Z2xhcy1QZXVja2VyIGFsZ29yaXRobVxyXG5cclxuZnVuY3Rpb24gc2ltcGxpZnkocG9pbnRzLCB0b2xlcmFuY2UpIHtcclxuXHJcbiAgICB2YXIgc3FUb2xlcmFuY2UgPSB0b2xlcmFuY2UgKiB0b2xlcmFuY2UsXHJcbiAgICAgICAgbGVuID0gcG9pbnRzLmxlbmd0aCxcclxuICAgICAgICBmaXJzdCA9IDAsXHJcbiAgICAgICAgbGFzdCA9IGxlbiAtIDEsXHJcbiAgICAgICAgc3RhY2sgPSBbXSxcclxuICAgICAgICBpLCBtYXhTcURpc3QsIHNxRGlzdCwgaW5kZXg7XHJcblxyXG4gICAgLy8gYWx3YXlzIHJldGFpbiB0aGUgZW5kcG9pbnRzICgxIGlzIHRoZSBtYXggdmFsdWUpXHJcbiAgICBwb2ludHNbZmlyc3RdWzJdID0gMTtcclxuICAgIHBvaW50c1tsYXN0XVsyXSA9IDE7XHJcblxyXG4gICAgLy8gYXZvaWQgcmVjdXJzaW9uIGJ5IHVzaW5nIGEgc3RhY2tcclxuICAgIHdoaWxlIChsYXN0KSB7XHJcblxyXG4gICAgICAgIG1heFNxRGlzdCA9IDA7XHJcblxyXG4gICAgICAgIGZvciAoaSA9IGZpcnN0ICsgMTsgaSA8IGxhc3Q7IGkrKykge1xyXG4gICAgICAgICAgICBzcURpc3QgPSBnZXRTcVNlZ0Rpc3QocG9pbnRzW2ldLCBwb2ludHNbZmlyc3RdLCBwb2ludHNbbGFzdF0pO1xyXG5cclxuICAgICAgICAgICAgaWYgKHNxRGlzdCA+IG1heFNxRGlzdCkge1xyXG4gICAgICAgICAgICAgICAgaW5kZXggPSBpO1xyXG4gICAgICAgICAgICAgICAgbWF4U3FEaXN0ID0gc3FEaXN0O1xyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG5cclxuICAgICAgICBpZiAobWF4U3FEaXN0ID4gc3FUb2xlcmFuY2UpIHtcclxuICAgICAgICAgICAgcG9pbnRzW2luZGV4XVsyXSA9IG1heFNxRGlzdDsgLy8gc2F2ZSB0aGUgcG9pbnQgaW1wb3J0YW5jZSBpbiBzcXVhcmVkIHBpeGVscyBhcyBhIHogY29vcmRpbmF0ZVxyXG4gICAgICAgICAgICBzdGFjay5wdXNoKGZpcnN0KTtcclxuICAgICAgICAgICAgc3RhY2sucHVzaChpbmRleCk7XHJcbiAgICAgICAgICAgIGZpcnN0ID0gaW5kZXg7XHJcblxyXG4gICAgICAgIH0gZWxzZSB7XHJcbiAgICAgICAgICAgIGxhc3QgPSBzdGFjay5wb3AoKTtcclxuICAgICAgICAgICAgZmlyc3QgPSBzdGFjay5wb3AoKTtcclxuICAgICAgICB9XHJcbiAgICB9XHJcbn1cclxuXHJcbi8vIHNxdWFyZSBkaXN0YW5jZSBmcm9tIGEgcG9pbnQgdG8gYSBzZWdtZW50XHJcbmZ1bmN0aW9uIGdldFNxU2VnRGlzdChwLCBhLCBiKSB7XHJcblxyXG4gICAgdmFyIHggPSBhWzBdLCB5ID0gYVsxXSxcclxuICAgICAgICBieCA9IGJbMF0sIGJ5ID0gYlsxXSxcclxuICAgICAgICBweCA9IHBbMF0sIHB5ID0gcFsxXSxcclxuICAgICAgICBkeCA9IGJ4IC0geCxcclxuICAgICAgICBkeSA9IGJ5IC0geTtcclxuXHJcbiAgICBpZiAoZHggIT09IDAgfHwgZHkgIT09IDApIHtcclxuXHJcbiAgICAgICAgdmFyIHQgPSAoKHB4IC0geCkgKiBkeCArIChweSAtIHkpICogZHkpIC8gKGR4ICogZHggKyBkeSAqIGR5KTtcclxuXHJcbiAgICAgICAgaWYgKHQgPiAxKSB7XHJcbiAgICAgICAgICAgIHggPSBieDtcclxuICAgICAgICAgICAgeSA9IGJ5O1xyXG5cclxuICAgICAgICB9IGVsc2UgaWYgKHQgPiAwKSB7XHJcbiAgICAgICAgICAgIHggKz0gZHggKiB0O1xyXG4gICAgICAgICAgICB5ICs9IGR5ICogdDtcclxuICAgICAgICB9XHJcbiAgICB9XHJcblxyXG4gICAgZHggPSBweCAtIHg7XHJcbiAgICBkeSA9IHB5IC0geTtcclxuXHJcbiAgICByZXR1cm4gZHggKiBkeCArIGR5ICogZHk7XHJcbn1cclxuIiwiJ3VzZSBzdHJpY3QnO1xyXG5cclxubW9kdWxlLmV4cG9ydHMgPSBjcmVhdGVUaWxlO1xyXG5cclxuZnVuY3Rpb24gY3JlYXRlVGlsZShmZWF0dXJlcywgejIsIHR4LCB0eSwgdG9sZXJhbmNlLCBub1NpbXBsaWZ5KSB7XHJcbiAgICB2YXIgdGlsZSA9IHtcclxuICAgICAgICBmZWF0dXJlczogW10sXHJcbiAgICAgICAgbnVtUG9pbnRzOiAwLFxyXG4gICAgICAgIG51bVNpbXBsaWZpZWQ6IDAsXHJcbiAgICAgICAgbnVtRmVhdHVyZXM6IDAsXHJcbiAgICAgICAgc291cmNlOiBudWxsLFxyXG4gICAgICAgIHg6IHR4LFxyXG4gICAgICAgIHk6IHR5LFxyXG4gICAgICAgIHoyOiB6MixcclxuICAgICAgICB0cmFuc2Zvcm1lZDogZmFsc2UsXHJcbiAgICAgICAgbWluOiBbMiwgMV0sXHJcbiAgICAgICAgbWF4OiBbLTEsIDBdXHJcbiAgICB9O1xyXG4gICAgZm9yICh2YXIgaSA9IDA7IGkgPCBmZWF0dXJlcy5sZW5ndGg7IGkrKykge1xyXG4gICAgICAgIHRpbGUubnVtRmVhdHVyZXMrKztcclxuICAgICAgICBhZGRGZWF0dXJlKHRpbGUsIGZlYXR1cmVzW2ldLCB0b2xlcmFuY2UsIG5vU2ltcGxpZnkpO1xyXG5cclxuICAgICAgICB2YXIgbWluID0gZmVhdHVyZXNbaV0ubWluLFxyXG4gICAgICAgICAgICBtYXggPSBmZWF0dXJlc1tpXS5tYXg7XHJcblxyXG4gICAgICAgIGlmIChtaW5bMF0gPCB0aWxlLm1pblswXSkgdGlsZS5taW5bMF0gPSBtaW5bMF07XHJcbiAgICAgICAgaWYgKG1pblsxXSA8IHRpbGUubWluWzFdKSB0aWxlLm1pblsxXSA9IG1pblsxXTtcclxuICAgICAgICBpZiAobWF4WzBdID4gdGlsZS5tYXhbMF0pIHRpbGUubWF4WzBdID0gbWF4WzBdO1xyXG4gICAgICAgIGlmIChtYXhbMV0gPiB0aWxlLm1heFsxXSkgdGlsZS5tYXhbMV0gPSBtYXhbMV07XHJcbiAgICB9XHJcbiAgICByZXR1cm4gdGlsZTtcclxufVxyXG5cclxuZnVuY3Rpb24gYWRkRmVhdHVyZSh0aWxlLCBmZWF0dXJlLCB0b2xlcmFuY2UsIG5vU2ltcGxpZnkpIHtcclxuXHJcbiAgICB2YXIgZ2VvbSA9IGZlYXR1cmUuZ2VvbWV0cnksXHJcbiAgICAgICAgdHlwZSA9IGZlYXR1cmUudHlwZSxcclxuICAgICAgICBzaW1wbGlmaWVkID0gW10sXHJcbiAgICAgICAgc3FUb2xlcmFuY2UgPSB0b2xlcmFuY2UgKiB0b2xlcmFuY2UsXHJcbiAgICAgICAgaSwgaiwgcmluZywgcDtcclxuXHJcbiAgICBpZiAodHlwZSA9PT0gMSkge1xyXG4gICAgICAgIGZvciAoaSA9IDA7IGkgPCBnZW9tLmxlbmd0aDsgaSsrKSB7XHJcbiAgICAgICAgICAgIHNpbXBsaWZpZWQucHVzaChnZW9tW2ldKTtcclxuICAgICAgICAgICAgdGlsZS5udW1Qb2ludHMrKztcclxuICAgICAgICAgICAgdGlsZS5udW1TaW1wbGlmaWVkKys7XHJcbiAgICAgICAgfVxyXG5cclxuICAgIH0gZWxzZSB7XHJcblxyXG4gICAgICAgIC8vIHNpbXBsaWZ5IGFuZCB0cmFuc2Zvcm0gcHJvamVjdGVkIGNvb3JkaW5hdGVzIGZvciB0aWxlIGdlb21ldHJ5XHJcbiAgICAgICAgZm9yIChpID0gMDsgaSA8IGdlb20ubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICAgICAgcmluZyA9IGdlb21baV07XHJcblxyXG4gICAgICAgICAgICAvLyBmaWx0ZXIgb3V0IHRpbnkgcG9seWxpbmVzICYgcG9seWdvbnNcclxuICAgICAgICAgICAgaWYgKCFub1NpbXBsaWZ5ICYmICgodHlwZSA9PT0gMiAmJiByaW5nLmRpc3QgPCB0b2xlcmFuY2UpIHx8XHJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgKHR5cGUgPT09IDMgJiYgcmluZy5hcmVhIDwgc3FUb2xlcmFuY2UpKSkge1xyXG4gICAgICAgICAgICAgICAgdGlsZS5udW1Qb2ludHMgKz0gcmluZy5sZW5ndGg7XHJcbiAgICAgICAgICAgICAgICBjb250aW51ZTtcclxuICAgICAgICAgICAgfVxyXG5cclxuICAgICAgICAgICAgdmFyIHNpbXBsaWZpZWRSaW5nID0gW107XHJcblxyXG4gICAgICAgICAgICBmb3IgKGogPSAwOyBqIDwgcmluZy5sZW5ndGg7IGorKykge1xyXG4gICAgICAgICAgICAgICAgcCA9IHJpbmdbal07XHJcbiAgICAgICAgICAgICAgICAvLyBrZWVwIHBvaW50cyB3aXRoIGltcG9ydGFuY2UgPiB0b2xlcmFuY2VcclxuICAgICAgICAgICAgICAgIGlmIChub1NpbXBsaWZ5IHx8IHBbMl0gPiBzcVRvbGVyYW5jZSkge1xyXG4gICAgICAgICAgICAgICAgICAgIHNpbXBsaWZpZWRSaW5nLnB1c2gocCk7XHJcbiAgICAgICAgICAgICAgICAgICAgdGlsZS5udW1TaW1wbGlmaWVkKys7XHJcbiAgICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgICAgICB0aWxlLm51bVBvaW50cysrO1xyXG4gICAgICAgICAgICB9XHJcblxyXG4gICAgICAgICAgICBpZiAodHlwZSA9PT0gMykgcmV3aW5kKHNpbXBsaWZpZWRSaW5nLCByaW5nLm91dGVyKTtcclxuXHJcbiAgICAgICAgICAgIHNpbXBsaWZpZWQucHVzaChzaW1wbGlmaWVkUmluZyk7XHJcbiAgICAgICAgfVxyXG4gICAgfVxyXG5cclxuICAgIGlmIChzaW1wbGlmaWVkLmxlbmd0aCkge1xyXG4gICAgICAgIHZhciB0aWxlRmVhdHVyZSA9IHtcclxuICAgICAgICAgICAgZ2VvbWV0cnk6IHNpbXBsaWZpZWQsXHJcbiAgICAgICAgICAgIHR5cGU6IHR5cGUsXHJcbiAgICAgICAgICAgIHRhZ3M6IGZlYXR1cmUudGFncyB8fCBudWxsXHJcbiAgICAgICAgfTtcclxuICAgICAgICBpZiAoZmVhdHVyZS5pZCAhPT0gbnVsbCkge1xyXG4gICAgICAgICAgICB0aWxlRmVhdHVyZS5pZCA9IGZlYXR1cmUuaWQ7XHJcbiAgICAgICAgfVxyXG4gICAgICAgIHRpbGUuZmVhdHVyZXMucHVzaCh0aWxlRmVhdHVyZSk7XHJcbiAgICB9XHJcbn1cclxuXHJcbmZ1bmN0aW9uIHJld2luZChyaW5nLCBjbG9ja3dpc2UpIHtcclxuICAgIHZhciBhcmVhID0gc2lnbmVkQXJlYShyaW5nKTtcclxuICAgIGlmIChhcmVhIDwgMCA9PT0gY2xvY2t3aXNlKSByaW5nLnJldmVyc2UoKTtcclxufVxyXG5cclxuZnVuY3Rpb24gc2lnbmVkQXJlYShyaW5nKSB7XHJcbiAgICB2YXIgc3VtID0gMDtcclxuICAgIGZvciAodmFyIGkgPSAwLCBsZW4gPSByaW5nLmxlbmd0aCwgaiA9IGxlbiAtIDEsIHAxLCBwMjsgaSA8IGxlbjsgaiA9IGkrKykge1xyXG4gICAgICAgIHAxID0gcmluZ1tpXTtcclxuICAgICAgICBwMiA9IHJpbmdbal07XHJcbiAgICAgICAgc3VtICs9IChwMlswXSAtIHAxWzBdKSAqIChwMVsxXSArIHAyWzFdKTtcclxuICAgIH1cclxuICAgIHJldHVybiBzdW07XHJcbn1cclxuIiwiJ3VzZSBzdHJpY3QnO1xyXG5cclxuZXhwb3J0cy50aWxlID0gdHJhbnNmb3JtVGlsZTtcclxuZXhwb3J0cy5wb2ludCA9IHRyYW5zZm9ybVBvaW50O1xyXG5cclxuLy8gVHJhbnNmb3JtcyB0aGUgY29vcmRpbmF0ZXMgb2YgZWFjaCBmZWF0dXJlIGluIHRoZSBnaXZlbiB0aWxlIGZyb21cclxuLy8gbWVyY2F0b3ItcHJvamVjdGVkIHNwYWNlIGludG8gKGV4dGVudCB4IGV4dGVudCkgdGlsZSBzcGFjZS5cclxuZnVuY3Rpb24gdHJhbnNmb3JtVGlsZSh0aWxlLCBleHRlbnQpIHtcclxuICAgIGlmICh0aWxlLnRyYW5zZm9ybWVkKSByZXR1cm4gdGlsZTtcclxuXHJcbiAgICB2YXIgejIgPSB0aWxlLnoyLFxyXG4gICAgICAgIHR4ID0gdGlsZS54LFxyXG4gICAgICAgIHR5ID0gdGlsZS55LFxyXG4gICAgICAgIGksIGosIGs7XHJcblxyXG4gICAgZm9yIChpID0gMDsgaSA8IHRpbGUuZmVhdHVyZXMubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICB2YXIgZmVhdHVyZSA9IHRpbGUuZmVhdHVyZXNbaV0sXHJcbiAgICAgICAgICAgIGdlb20gPSBmZWF0dXJlLmdlb21ldHJ5LFxyXG4gICAgICAgICAgICB0eXBlID0gZmVhdHVyZS50eXBlO1xyXG5cclxuICAgICAgICBpZiAodHlwZSA9PT0gMSkge1xyXG4gICAgICAgICAgICBmb3IgKGogPSAwOyBqIDwgZ2VvbS5sZW5ndGg7IGorKykgZ2VvbVtqXSA9IHRyYW5zZm9ybVBvaW50KGdlb21bal0sIGV4dGVudCwgejIsIHR4LCB0eSk7XHJcblxyXG4gICAgICAgIH0gZWxzZSB7XHJcbiAgICAgICAgICAgIGZvciAoaiA9IDA7IGogPCBnZW9tLmxlbmd0aDsgaisrKSB7XHJcbiAgICAgICAgICAgICAgICB2YXIgcmluZyA9IGdlb21bal07XHJcbiAgICAgICAgICAgICAgICBmb3IgKGsgPSAwOyBrIDwgcmluZy5sZW5ndGg7IGsrKykgcmluZ1trXSA9IHRyYW5zZm9ybVBvaW50KHJpbmdba10sIGV4dGVudCwgejIsIHR4LCB0eSk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcbiAgICB9XHJcblxyXG4gICAgdGlsZS50cmFuc2Zvcm1lZCA9IHRydWU7XHJcblxyXG4gICAgcmV0dXJuIHRpbGU7XHJcbn1cclxuXHJcbmZ1bmN0aW9uIHRyYW5zZm9ybVBvaW50KHAsIGV4dGVudCwgejIsIHR4LCB0eSkge1xyXG4gICAgdmFyIHggPSBNYXRoLnJvdW5kKGV4dGVudCAqIChwWzBdICogejIgLSB0eCkpLFxyXG4gICAgICAgIHkgPSBNYXRoLnJvdW5kKGV4dGVudCAqIChwWzFdICogejIgLSB0eSkpO1xyXG4gICAgcmV0dXJuIFt4LCB5XTtcclxufVxyXG4iLCIndXNlIHN0cmljdCc7XHJcblxyXG52YXIgY2xpcCA9IHJlcXVpcmUoJy4vY2xpcCcpO1xyXG52YXIgY3JlYXRlRmVhdHVyZSA9IHJlcXVpcmUoJy4vZmVhdHVyZScpO1xyXG5cclxubW9kdWxlLmV4cG9ydHMgPSB3cmFwO1xyXG5cclxuZnVuY3Rpb24gd3JhcChmZWF0dXJlcywgYnVmZmVyLCBpbnRlcnNlY3RYKSB7XHJcbiAgICB2YXIgbWVyZ2VkID0gZmVhdHVyZXMsXHJcbiAgICAgICAgbGVmdCAgPSBjbGlwKGZlYXR1cmVzLCAxLCAtMSAtIGJ1ZmZlciwgYnVmZmVyLCAgICAgMCwgaW50ZXJzZWN0WCwgLTEsIDIpLCAvLyBsZWZ0IHdvcmxkIGNvcHlcclxuICAgICAgICByaWdodCA9IGNsaXAoZmVhdHVyZXMsIDEsICAxIC0gYnVmZmVyLCAyICsgYnVmZmVyLCAwLCBpbnRlcnNlY3RYLCAtMSwgMik7IC8vIHJpZ2h0IHdvcmxkIGNvcHlcclxuXHJcbiAgICBpZiAobGVmdCB8fCByaWdodCkge1xyXG4gICAgICAgIG1lcmdlZCA9IGNsaXAoZmVhdHVyZXMsIDEsIC1idWZmZXIsIDEgKyBidWZmZXIsIDAsIGludGVyc2VjdFgsIC0xLCAyKSB8fCBbXTsgLy8gY2VudGVyIHdvcmxkIGNvcHlcclxuXHJcbiAgICAgICAgaWYgKGxlZnQpIG1lcmdlZCA9IHNoaWZ0RmVhdHVyZUNvb3JkcyhsZWZ0LCAxKS5jb25jYXQobWVyZ2VkKTsgLy8gbWVyZ2UgbGVmdCBpbnRvIGNlbnRlclxyXG4gICAgICAgIGlmIChyaWdodCkgbWVyZ2VkID0gbWVyZ2VkLmNvbmNhdChzaGlmdEZlYXR1cmVDb29yZHMocmlnaHQsIC0xKSk7IC8vIG1lcmdlIHJpZ2h0IGludG8gY2VudGVyXHJcbiAgICB9XHJcblxyXG4gICAgcmV0dXJuIG1lcmdlZDtcclxufVxyXG5cclxuZnVuY3Rpb24gc2hpZnRGZWF0dXJlQ29vcmRzKGZlYXR1cmVzLCBvZmZzZXQpIHtcclxuICAgIHZhciBuZXdGZWF0dXJlcyA9IFtdO1xyXG5cclxuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgZmVhdHVyZXMubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICB2YXIgZmVhdHVyZSA9IGZlYXR1cmVzW2ldLFxyXG4gICAgICAgICAgICB0eXBlID0gZmVhdHVyZS50eXBlO1xyXG5cclxuICAgICAgICB2YXIgbmV3R2VvbWV0cnk7XHJcblxyXG4gICAgICAgIGlmICh0eXBlID09PSAxKSB7XHJcbiAgICAgICAgICAgIG5ld0dlb21ldHJ5ID0gc2hpZnRDb29yZHMoZmVhdHVyZS5nZW9tZXRyeSwgb2Zmc2V0KTtcclxuICAgICAgICB9IGVsc2Uge1xyXG4gICAgICAgICAgICBuZXdHZW9tZXRyeSA9IFtdO1xyXG4gICAgICAgICAgICBmb3IgKHZhciBqID0gMDsgaiA8IGZlYXR1cmUuZ2VvbWV0cnkubGVuZ3RoOyBqKyspIHtcclxuICAgICAgICAgICAgICAgIG5ld0dlb21ldHJ5LnB1c2goc2hpZnRDb29yZHMoZmVhdHVyZS5nZW9tZXRyeVtqXSwgb2Zmc2V0KSk7XHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICB9XHJcblxyXG4gICAgICAgIG5ld0ZlYXR1cmVzLnB1c2goY3JlYXRlRmVhdHVyZShmZWF0dXJlLnRhZ3MsIHR5cGUsIG5ld0dlb21ldHJ5LCBmZWF0dXJlLmlkKSk7XHJcbiAgICB9XHJcblxyXG4gICAgcmV0dXJuIG5ld0ZlYXR1cmVzO1xyXG59XHJcblxyXG5mdW5jdGlvbiBzaGlmdENvb3Jkcyhwb2ludHMsIG9mZnNldCkge1xyXG4gICAgdmFyIG5ld1BvaW50cyA9IFtdO1xyXG4gICAgbmV3UG9pbnRzLmFyZWEgPSBwb2ludHMuYXJlYTtcclxuICAgIG5ld1BvaW50cy5kaXN0ID0gcG9pbnRzLmRpc3Q7XHJcblxyXG4gICAgZm9yICh2YXIgaSA9IDA7IGkgPCBwb2ludHMubGVuZ3RoOyBpKyspIHtcclxuICAgICAgICBuZXdQb2ludHMucHVzaChbcG9pbnRzW2ldWzBdICsgb2Zmc2V0LCBwb2ludHNbaV1bMV0sIHBvaW50c1tpXVsyXV0pO1xyXG4gICAgfVxyXG4gICAgcmV0dXJuIG5ld1BvaW50cztcclxufVxyXG4iXX0=
